# CONTEXT.md — Bối cảnh, hiện trạng và định hướng khóa luận

> **Cập nhật:** 2026-08-25
> **Giai đoạn:** Chuẩn bị và phát triển khóa luận tốt nghiệp, 08/2026–12/2026
> **Đề tài theo appendix.tex:** Hệ thống AIOps tập trung đa nút với phát hiện bất thường chủ động và tự phục hồi có kiểm soát cho hạ tầng phân tán

## 1. Thông tin khóa luận

| Hạng mục | Nội dung |
|---|---|
| Tên tiếng Việt | Hệ thống AIOps tập trung đa nút với phát hiện bất thường chủ động và tự phục hồi có kiểm soát cho hạ tầng phân tán |
| Tên tiếng Anh | Centralized Multi-Node AIOps System with Proactive Anomaly Detection and Controlled Self-Healing for Distributed Infrastructure |
| Đơn vị | Trường Đại học Công nghệ Thông tin, ĐHQG TP. Hồ Chí Minh |
| Cán bộ hướng dẫn | ThS. Trần Thị Dung |
| Sinh viên | Lê Hoàng Việt (23521778), Lê Quang Tiến (23521572) |
| Thời gian | 08/2026–12/2026 |

## 2. Bài toán và phạm vi

Hạ tầng cloud hiện đại gồm nhiều node, container, dịch vụ và dependency. Monitoring dựa trên rule có thể thu thập metrics và phát cảnh báo, nhưng thường tạo ra các tín hiệu rời rạc, phụ thuộc ngưỡng tĩnh và chưa cung cấp đầy đủ ngữ cảnh để xác định nguyên nhân gốc rễ. Khóa luận phát triển hệ thống hiện tại thành một nền tảng AIOps có khả năng:

- Thu thập và tương quan alert, metrics, logs, trạng thái node/service, dependency và lịch sử incident.
- Phát hiện bất thường chủ động từ chuỗi metrics, bổ sung cho alert rule tĩnh.
- Điều phối các agent chuyên trách bằng Celery fan-out để thu thập bằng chứng đa nguồn song song; Aggregator tổng hợp kết quả, xếp hạng nguyên nhân và sinh đề xuất xử lý có cấu trúc.
- Tích lũy incident history, feedback quản trị viên và runbook đã kiểm chứng vào Vector Knowledge Base.
- Dùng RAG/LLM để giải thích kết quả Aggregator; mọi remediation phải qua policy, Human-in-the-Loop, playbook có kiểm soát và verification.
- Xử lý partial failure, timeout và kết quả mâu thuẫn của các agent mà không làm mất incident context.
- Đánh giá bằng dữ liệu thực nghiệm: MTTD, MTTR, accuracy, false positive/negative, chất lượng RCA, hiệu quả phục hồi và khả năng duy trì dịch vụ.

Phạm vi thực nghiệm là hệ thống ngân hàng mẫu chạy trên AWS EC2. Đây là workload đại diện để tạo các kịch bản lỗi, không phải hệ thống ngân hàng thương mại thực tế. Các thao tác có rủi ro phải được giới hạn trong allowlist và môi trường thử nghiệm.

## 3. Kiến trúc và hiện trạng codebase

```text
AWS Infrastructure / Multi-AZ target architecture
        |
Terraform + Ansible
        |
Monitoring & Observability: Prometheus, Alertmanager, Grafana, exporters
        |
AI control plane: FastAPI -> Redis/Celery -> Incident Orchestrator
        -> Celery fan-out: Correlation / Dependency / Metric / Log / Probe agents
        -> Aggregator: evidence merge + deterministic RCA scoring + RAG/LLM explanation
        |
Human-in-the-Loop: Telegram approval -> controlled playbook -> verification
        |
CI/CD: GitHub Actions -> GHCR -> role-based deploy -> health check/rollback
```

### 3.1. Infrastructure và configuration

**Đã có trong codebase:**

- `terraform/` tạo một VPC `10.10.0.0/16`, một public subnet lấy AZ đầu tiên, Internet Gateway, security groups, 3 EC2 và Elastic IP.
- Ba role được tách theo host: `monitor-ai-01`, `bank-web-01`, `bank-core-01`.
- `ansible/` đảm nhiệm bootstrap host, Docker, monitoring stack và release runtime.
- Security group có health/metrics access giữa các role; EC2 bật mã hóa root volume và IMDSv2 bắt buộc.

**Trạng thái:** Đã triển khai mô hình single-AZ, multi-node theo role. Chưa có Multi-AZ, private subnet, Load Balancer hoặc Auto Scaling Group.

**Mục tiêu mở rộng:** thiết kế và triển khai thực nghiệm kiến trúc 2 AZ, public/private subnet, Load Balancer, health check và Auto Scaling ở mức phù hợp chi phí. Nếu không đủ điều kiện triển khai đầy đủ, phải phân biệt rõ phần đã chạy thực tế với phần thiết kế/POC.

### 3.2. Monitoring và observability

**Đã có:** Prometheus, Alertmanager, Grafana, Node Exporter, Blackbox Exporter, cAdvisor, Redis Exporter và PostgreSQL Exporter. Nguồn tín hiệu gồm resource metrics, endpoint/service monitor và log watcher. Alert rules hiện bao phủ các lỗi CPU, memory, disk, endpoint, container, PostgreSQL và Redis; dashboard có system overview, network performance và alert monitoring.

**Giới hạn hiện tại:** alert chủ yếu dựa trên threshold tĩnh. Chưa có pipeline time window, anomaly score, nhãn chuẩn hóa cho correlation đa nguồn hoặc service dependency graph hoàn chỉnh.

### 3.3. AI Agent và alert pipeline

Các thành phần chính nằm trong `agent_src/`:

- FastAPI tại `agent_src/core/main.py` tiếp nhận Alertmanager qua `/webhook`, health/metrics, Telegram webhook và Tool Registry API.
- Redis làm broker/cache; Celery xử lý bất đồng bộ qua `process_alerts_task`, fan-out `group/chord` và scheduled verification.
- Dedup hai tầng: ingress cooldown và AI cooldown, ưu tiên Alertmanager fingerprint hoặc hash từ các label định danh.
- Các agent chuyên trách chỉ dùng công cụ read-only theo role: correlation/dependency, metric, log, probe và change/runbook.
- Aggregator hợp nhất evidence, áp dụng deterministic RCA scoring, xử lý partial failure và chỉ dùng Gemini `gemini-2.5-flash` để giải thích hoặc chuẩn hóa proposal.
- Telegram gửi incident report, nhận feedback `/feedback` và callback approval/dismissal; sau đó agent kiểm tra lại qua Prometheus.
- `core/runbook_registry.py` đã có đăng ký revision, phân loại `read_only`/`remediation`/`destructive`, tạo runbook draft, audit JSONL và publish sau phê duyệt.
- GitHub webhook có HMAC verification và auto-discovery cho thay đổi CI/toolchain.

**Trạng thái:** Core alert-to-analysis-to-notification-to-verification đã hoạt động. Celery fan-out, Aggregator, policy gateway và typed remediation executor là phần cần phát triển. `propose_remediation()` hiện chỉ sinh proposal có validation host, chưa phải engine thực thi restart/scale/rollback; vì vậy không được mô tả hệ thống hiện tại là self-healing hoàn chỉnh.

### 3.3.1. Mô hình Multi-Agent mục tiêu

```text
Incident Orchestrator
        -> Celery group/chord
           -> Correlation Agent
           -> Dependency Agent
           -> Metric/Anomaly Agent
           -> Log Agent
           -> Probe Agent
           -> Change/Runbook Agent
        -> Aggregator
           -> evidence merge + deterministic RCA scoring
           -> RAG/LLM explanation and structured proposal
        -> Policy Gateway -> Human approval
        -> Typed Ansible Executor (staging allowlist)
        -> Verification Agent -> incident memory/audit
```

Các specialist agent chạy song song và chỉ trả về kết quả có schema, evidence ID, trạng thái, thời gian thực hiện và lỗi nếu có. Aggregator là nơi duy nhất hợp nhất kết quả; không agent nào tự thực hiện thay đổi hệ thống. `control-plane-db` là nguồn dữ liệu trạng thái chính, còn ChromaDB chỉ phục vụ retrieval.

### 3.4. RAG và knowledge base

`agent_src/core/rag_engine.py` dùng ChromaDB với hai collection:

- `standard_runbooks`: Markdown runbook được chia chunk theo heading và nạp lúc khởi động.
- `incident_memory`: incident history và admin feedback đã được agent lưu lại để truy xuất cho các lần phân tích sau.

Hiện có runbook cho Docker, Nginx, PostgreSQL và Redis. Cơ chế runbook workflow đã hỗ trợ draft, liên kết runbook liên quan, phê duyệt, publish version và audit. Phần cần phát triển là mở rộng tri thức cho dependency/network/load balancer/deploy failure, đánh giá precision@k/recall và sinh runbook draft từ các incident đã được xác minh, không tự động tin tưởng dữ liệu chưa được duyệt.

### 3.5. Workload và release

- `demo-web/frontend/`: React + Nginx, mô phỏng giao diện Internet Banking.
- `demo-web/backend/`: FastAPI Payment API; `/api/health` là liveness, `/api/ready` kiểm tra cả PostgreSQL readiness.
- `demo-web/database/`: PostgreSQL init và seed scripts.
- `release/`: compose staging/production; mỗi role chạy image GHCR do CI build, không build image trên EC2.
- Staging và production đồng thời dùng cùng host nhưng tách compose/state/port: staging `18000/18080/18081`, production `8000/8080/3000`.
- `.github/workflows/` và `automation/app-release-deploy.sh` cung cấp lint, test, build, compose validation, role-based deployment, health check và rollback theo tag trước đó.

## 4. Luồng xử lý mục tiêu

```text
Metrics / logs / service checks / Alertmanager
        -> Event Normalizer -> Incident Core
        -> Celery group/chord fan-out các specialist agent song song
        -> Aggregator: merge evidence + RCA scoring + impact
        -> RAG/LLM explanation và structured remediation proposal
        -> Policy Gateway -> Human approval
        -> Typed playbook executor trên staging
        -> Verification Agent -> RESOLVED / FAILED / ESCALATED
        -> incident memory và audit log
```

Trong phiên bản hiện tại, fan-out specialist, Aggregator, anomaly detector, correlation engine và playbook execution còn là phần phát triển. Fan-out phải có timeout, retry có giới hạn và xử lý partial failure. Không dùng LLM làm quyền thực thi trực tiếp; mọi hành động thay đổi trạng thái phải đi qua policy, allowlist, timeout, audit và điều kiện dừng.

## 5. Khoảng cách cần giải quyết

| Nhóm | Hiện trạng | Kết quả khóa luận cần đạt |
|---|---|---|
| HA hạ tầng | Single-AZ, 3 EC2 cố định | Thiết kế/POC hoặc triển khai Multi-AZ + LB + ASG, có kịch bản node/AZ failure |
| Phát hiện | Threshold tĩnh | Pipeline time window và ít nhất một mô hình Isolation Forest hoặc mô hình phù hợp |
| Multi-Agent/RCA | Chưa có Celery fan-out và Aggregator; context chủ yếu từ alert, runbook và Prometheus query | Specialist agents chạy song song, Aggregator gom evidence, dependency và lịch sử incident vào incident context |
| Knowledge | 4 nhóm runbook, incident memory đã có | Làm giàu tri thức có kiểm duyệt, đánh giá retrieval, sinh draft runbook |
| Self-healing | Proposal và approval flow, chưa có typed executor hoàn chỉnh | Aggregator proposal -> policy -> human approval -> Ansible typed executor -> Verification Agent; chỉ staging |
| Đánh giá | Có latency metric cơ bản, chưa có bộ benchmark | Dataset/scenario, baseline, metrics và bảng so sánh trước/sau |
| Bảo mật/vận hành | GitHub webhook đã có HMAC; Alertmanager webhook cần hardening theo scope | Secret management, auth ingress, audit action và test failure/rollback |

## 6. Nguyên tắc phát triển

- Giữ deterministic runbook làm lớp rẻ và ổn định trước khi gọi Gemini.
- Giữ `GEMINI_MAX_REMOTE_CALLS=1` và các giới hạn quota bảo thủ trừ khi có số liệu chứng minh cần thay đổi.
- Specialist agents chỉ được gọi nhóm tool read-only phù hợp với role; Aggregator là điểm hợp nhất duy nhất.
- Fan-out có timeout tổng thể 90 giây, retry giới hạn và phải biểu diễn partial failure bằng uncertainty thay vì tự suy đoán.
- RCA scoring được tính deterministic trước; độ tin cậy do LLM tự sinh không được dùng làm tiêu chí duy nhất.
- Terraform chỉ quản lý tài nguyên cloud; Ansible quản lý host/runtime; release script là cổng deploy duy nhất.
- Không đưa ChromaDB runtime data, `.env*`, Terraform state hoặc SSH key vào repository.
- Phân biệt rõ `liveness` và `readiness`, staging và production, proposal và execution.
- Mọi kết quả thực nghiệm phải có scenario, input, expected outcome, observed outcome và timestamp; không tự tạo số liệu đánh giá.

## 7. Tài liệu và mã nguồn tham chiếu

| Đường dẫn | Vai trò |
|---|---|
| `appendix.tex` | Đề cương chính thức, mục tiêu và kế hoạch 08/2026–12/2026 |
| `README.md` | Kiến trúc, alert flow, release và verification hiện tại |
| `agent_src/README.md`, `agent_src/RAG_SYSTEM_GUIDE.md` | Nội bộ AI Agent và RAG |
| `AIops_CICD.md` | Thiết kế CI/CD, isolation và rollback |
| `AWS_INFRASTRUCTURE_DEPLOYMENT_GUIDE.md` | Provision AWS và Ansible |
| `STAGING_DEMO_RUNBOOKS.md` | Kịch bản vận hành staging hiện có |
