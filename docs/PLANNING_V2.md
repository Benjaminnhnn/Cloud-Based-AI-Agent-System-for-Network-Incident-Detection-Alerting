# PLANNING_V2.md — Kế hoạch nâng cấp hệ thống Multi-Agent AIOps cho Fintech

> **Phiên bản:** 2.1
> **Cập nhật:** 2026-08-31
> **Thời gian dự kiến:** 08/2026–12/2026
> **Baseline đã kiểm tra:** AWS EC2 single-AZ, Docker Compose, Prometheus/Alertmanager, FastAPI, Redis/Celery, Gemini và ChromaDB.
> **Kiến trúc MVP bắt buộc:** VPC public/private subnet trên hai Availability Zone, Amazon EKS, Amazon RDS Multi-AZ, GitHub Actions OIDC và Multi-Agent AIOps xuyên tầng App–Infrastructure.
> **Production reference:** ba Availability Zone, NAT Gateway theo AZ và các dịch vụ managed nâng cao; không phải điều kiện nghiệm thu.
> **Mục tiêu:** xây dựng và đánh giá một vòng xử lý sự cố xuyên suốt từ dịch vụ nghiệp vụ qua CI/CD tới workload AWS theo pipeline **Collect -> Redact -> Normalize -> Detect/Correlate -> Multi-Agent Investigation -> Evidence Aggregation -> Human Approval -> Controlled Staging Action -> Verification -> Auditable Learning**.

---

## Cách đọc kế hoạch này

Kế hoạch V2 bắt đầu từ hệ thống đang chạy thật trong repository, sau đó chuyển đổi theo từng lát cắt dọc:

```text
EC2 single-AZ + Docker Compose + threshold alerts
                |
                v
Đóng băng baseline và giữ luồng cảnh báo hiện tại hoạt động
                |
                v
VPC 2 AZ + EKS + RDS Multi-AZ + GitHub OIDC
                |
                v
Metrics + logs + traces + CI/CD telemetry
                |
                v
Redaction + normalization/template fingerprint + incident core
                |
                v
LangGraph Orchestrator
  -> Application Agents | Kubernetes | RDS | GitHub | Security
                |
                v
Aggregator: evidence merge + deterministic scoring + impact
                |
                v
RAG/LLM explanation -> Policy -> HITL -> Controlled action
                |
                v
Verification -> audit trail -> reviewed incident memory
                |
                v
So sánh với baseline bằng các kịch bản có ground truth
```

Vòng xử lý trung tâm của phiên bản 2:

> **Signal -> Template/Fingerprint -> Event -> Incident -> Evidence -> Diagnosis -> Decision -> Action -> Verification -> Reviewed Learning**

Các trạng thái sau phải luôn được phân biệt:

- **Hiện có:** đã được xác nhận trong code hoặc cấu hình repository.
- **Đang chuyển đổi:** có baseline để tái sử dụng nhưng chưa đạt contract V2.
- **Mục tiêu bắt buộc:** phải triển khai và kiểm thử trong phạm vi khóa luận.
- **Mở rộng:** chỉ làm sau khi lát cắt xuyên suốt bắt buộc đã ổn định.

| Câu hỏi | Phần trả lời |
|---|---|
| Hệ thống hiện tại thực sự có gì? | Mục 1, 3 |
| Kiến trúc nâng cấp thay đổi những gì? | Mục 4 |
| Multi-Agent phối hợp và bị giới hạn ra sao? | Mục 5, 8 |
| Hệ thống học trạng thái bình thường thế nào? | Mục 6, 9 |
| CI/CD được liên kết với ứng dụng và hạ tầng ra sao? | Mục 7 |
| Dữ liệu Fintech được bảo vệ thế nào? | Mục 8, 12 |
| Làm sao chứng minh giải pháp tốt hơn baseline? | Mục 13, 14 |
| Xây theo thứ tự nào? | Mục 15 |

Phạm vi được phân loại ngay từ đầu:

| Nhóm | Nội dung |
|---|---|
| **Đã có** | Baseline EC2, monitoring, Celery, Gemini/RAG, Telegram và release rollback |
| **Bắt buộc** | Mobile Banking trên EKS hai AZ, RDS Multi-AZ, OIDC, Incident Core, Application/Infrastructure Agents, Aggregator, staging remediation, Verification và benchmark |
| **POC** | Pattern mining/anomaly nâng cao, Karpenter, Neo4j, pgvector mới, AMP, traces nâng cao, Langfuse và Network Agent riêng |
| **Future Work** | AgentCore Runtime, A2A deployment, multi-region DR và production self-healing |

Nếu tiến độ bị trễ, giảm POC/Future Work trước; không cắt luồng bắt buộc từ Mobile Banking xuống EKS/RDS và ngược về business impact.

---

## 1. Định hướng tổng thể

### 1.1. Hệ thống hiện tại đã xác minh

```text
Prometheus / Blackbox / service monitor / log watcher
        -> Alertmanager hoặc webhook
        -> FastAPI /webhook
        -> Redis broker + Celery worker
        -> deterministic runbook hoặc Gemini + ChromaDB RAG
        -> Telegram
        -> delayed verification qua Prometheus
```

Hệ thống hiện tại là một AIOps alert bot chạy trên ba EC2 cùng một Availability Zone:

| Host | Vai trò | Thành phần chính |
|---|---|---|
| `monitor-ai-01` | Monitoring/AI | Prometheus, Alertmanager, Grafana, Redis, AI Agent, Celery, log watcher |
| `bank-core-01` | Core | Payment API, PostgreSQL, PostgreSQL exporter |
| `bank-web-01` | Web | React/Nginx frontend |

Các khả năng đã có:

1. Nhận Alertmanager payload tại `/webhook` và enqueue sang Celery.
2. Dedup hai tầng bằng Redis, có fallback trong bộ nhớ.
3. Chẩn đoán deterministic cho một số alert quen thuộc.
4. ChromaDB có `standard_runbooks` và `incident_memory`.
5. Gọi Gemini theo quota bảo thủ khi cần giải thích.
6. Gửi Telegram report, nhận admin feedback và verification trễ.
7. GitHub webhook có kiểm tra HMAC để phát hiện thay đổi tool/CI và tạo runbook draft.
8. GitHub Actions có CI, build image, role-based deploy, health check và rollback theo tag.
9. Staging và production tách bằng compose project, state và cổng trên cùng các EC2.

Kết quả kiểm tra baseline ngày 2026-08-29:

```text
PYTHONPATH=agent_src venv/bin/pytest -q agent_src/tests
59 passed, 8 warnings
```

Baseline chưa có:

- Amazon EKS, RDS Multi-AZ, private workload subnets hoặc topology đa AZ.
- LangGraph, Bedrock/AgentCore, MCP tool gateway hoặc A2A runtime.
- Celery `group/chord`, specialist agent thật và Aggregator.
- Thu thập workflow logs/artifacts để chẩn đoán CI/CD.
- Event schema đa nguồn, durable incident state và evidence store.
- Pattern mining để học trạng thái bình thường.
- PII/PCI redaction gateway trước LLM và knowledge stores.
- Typed remediation executor đầy đủ cho EKS, RDS hoặc GitHub Actions.

### 1.2. Hệ thống cần xây dựng

```text
GitHub webhooks/API/telemetry       EKS/RDS/CloudWatch/Prometheus/OTel
              \                                  /
               v                                v
                    Ingestion Gateway
                           |
               Security redaction boundary
                           |
             Event Normalizer + Pattern Mining
                           |
                    Incident Core
                           |
                 LangGraph Orchestrator
       +-------------------+-------------------+
       |                                       |
 Application Agents                    Infrastructure Agents
 Mobile Banking                        Kubernetes | RDS | GitHub
 BNPL/Investment/Credit context        Security | Network context
       \                                       /
        +----------- Dependency model --------+
                           |
                    Evidence Aggregator
                           |
           deterministic RCA + impact + uncertainty
                           |
             RAG/LLM explanation and proposal
                           |
             Policy Gateway + Human approval
                           |
       typed EKS/GitHub/RDS-safe action adapters
                           |
                 Verification Agent
                           |
               audit + reviewed learning
```

### 1.3. Tên đề tài đề xuất

> **Xây dựng và đánh giá hệ thống Multi-Agent AIOps hỗ trợ phát hiện bất thường, chẩn đoán xuyên tầng ứng dụng–hạ tầng và tự phục hồi có kiểm soát cho hệ thống Fintech trên AWS.**

Tên tiếng Anh đề xuất:

> **Design and Evaluation of a Multi-Agent AIOps System for Anomaly Detection, Cross-Layer Application-to-Infrastructure Diagnosis, and Controlled Remediation in AWS Fintech Systems.**

### 1.4. Câu hỏi nghiên cứu chính

> Việc kết hợp Application Agents, Infrastructure Agents, dependency data và deterministic Aggregator có giúp giảm cảnh báo thừa, rút ngắn điều tra và tăng độ chính xác RCA cho sự cố xuyên App–GitHub Actions–EKS–RDS, trong khi vẫn duy trì least privilege, Human-in-the-Loop và auditability hay không?

### 1.5. Các dịch vụ Fintech mẫu

| Dịch vụ | Phạm vi | Scenario |
|---|---|---|
| **Mobile Banking** | **Bắt buộc, end-to-end** | Đăng nhập/chuyển tiền; migration lỗi, API chậm hoặc dependency down |
| Buy Now Pay Later | Scenario pack/service nhỏ | Tạo khoản vay lỗi, payment timeout |
| Investment App | Scenario pack/service nhỏ | Market data chậm, order failure |
| AI Credit Scoring | Scenario pack/service nhỏ | Thiếu feature, model endpoint chậm |

Payment API hiện tại được tái sử dụng và mở rộng thành Transaction Service của Mobile Banking. Ba dịch vụ còn lại dùng chung nền tảng và có thể dùng generic Application Agent; không bắt buộc xây full-stack hoặc agent runtime riêng.

---

## 2. Đóng góp kỹ thuật và giới hạn tuyên bố

### 2.1. Đóng góp chính

Đóng góp không nằm ở số lượng agent hoặc việc gọi LLM. Đóng góp cần được chứng minh là một pipeline có thể tái lập:

1. Chuẩn hóa signals từ ứng dụng, CI/CD và hạ tầng thành event schema chung.
2. Redact dữ liệu nhạy cảm trước operational persistence, LLM, vector store hoặc prompt trace.
3. Liên kết business capability, application service, commit, workflow, image digest, deployment, Kubernetes workload và database migration.
4. Điều phối Application Agents và Infrastructure Agents theo cùng dependency context; mỗi agent chỉ dùng tool được cấp.
5. Dùng template fingerprint bắt buộc và đánh giá pattern mining/time-window anomaly như một POC bổ sung cho threshold.
6. Aggregator hợp nhất evidence và xếp hạng RCA theo công thức deterministic.
7. Thực thi hành động có kiểu qua policy, approval, idempotency và verification.
8. Chỉ đưa incident/pattern vào knowledge sau khi đã được xác minh hoặc duyệt.

Mô hình điểm `rca-v1` được dùng cho MVP:

```text
positive_score =
    0.15 * temporal_score
  + 0.20 * dependency_score
  + 0.15 * metric_score
  + 0.15 * log_pattern_score
  + 0.10 * trace_or_probe_score
  + 0.15 * recent_change_score
  + 0.05 * cross_domain_link_score
  + 0.05 * security_signal_score

root_cause_score = clip(
    positive_score
  - 0.20 * contradiction_score
  - 0.10 * stale_evidence_penalty,
  0.0,
  1.0
)
```

Các trọng số ban đầu là expert priors: dependency và recent change được ưu tiên vì kịch bản trung tâm cần phân biệt root cause với lỗi downstream. Nhóm chỉ được hiệu chỉnh bằng fixture và ba pilot runs; không dùng benchmark/test set để tối ưu. Sau pilot, công thức, score normalization và hash cấu hình phải được đóng băng trước tối thiểu 10 benchmark runs cho mỗi cặp scenario–method. Báo cáo phải có sensitivity/ablation để chỉ ra kết quả có phụ thuộc bất thường vào một trọng số hay không. LLM không được tự đặt hoặc sửa điểm cuối cùng.

### 2.2. Vai trò của LLM

LLM được phép:

- Tóm tắt incident và timeline.
- Giải thích evidence đã có mã tham chiếu.
- Đề xuất giả thuyết hoặc bước điều tra read-only.
- Truy xuất runbook và incident tương tự.
- Chuẩn hóa remediation proposal theo schema.

LLM không được:

- Nhận log thô chưa qua redaction.
- Tự tạo hoặc chạy shell, SQL ghi dữ liệu, `kubectl`, AWS CLI hay GitHub mutation.
- Tự đánh dấu incident là `RESOLVED`.
- Tự promote pattern thành bình thường.
- Tự thay đổi IAM, Security Group, network policy hoặc database schema.
- Dùng confidence do chính LLM sinh làm ground truth.

### 2.3. Self-evolution được hiểu thế nào

Knowledge governance có review/version/rollback là bắt buộc. Tự động đề xuất knowledge release, pattern promotion hoặc drift lifecycle là POC.

Self-evolution trong V2 không phải online training không kiểm soát. Nó gồm:

```text
Observed pattern/incident
  -> candidate memory
  -> verification + human feedback
  -> quality/security checks
  -> approved version
  -> active retrieval/pattern baseline
  -> rollback được về version trước
```

Không cập nhật model weights trong runtime. Mọi tri thức mới phải có provenance, reviewer, version và khả năng thu hồi.

### 2.4. Giới hạn tuyên bố

- Môi trường là sandbox Fintech đại diện, không phải production ngân hàng thực.
- Multi-AZ tăng tính sẵn sàng nhưng không đồng nghĩa toàn hệ thống không có single point of failure.
- Multi-Agent chỉ được đánh giá trên tập scenario đã công bố.
- Region disaster recovery, ransomware recovery và DDoS thật chỉ được tabletop hoặc mô phỏng an toàn.
- Không tuyên bố một thuật toán RCA tổng quát hoặc một hệ thống compliance đã được chứng nhận.

---

## 3. Đối chiếu repository hiện tại với V2

### 3.1. Bốn lớp hiện tại

| Lớp | Nguồn hiện tại | Trách nhiệm hiện tại | Hướng V2 |
|---|---|---|---|
| Infrastructure | `terraform/` | VPC, một public subnet, SG, ba EC2, EIP | VPC hai AZ, public/private subnet, EKS, RDS, IAM/OIDC và KMS |
| Host/runtime | `ansible/`, `release/` | Docker và Docker Compose theo role | Helm/Kustomize/GitOps; Ansible giữ cho legacy và fault injection |
| Application/AIOps | `agent_src/`, `demo-web/` | FastAPI, Celery, RAG, demo banking | containerized microservices, LangGraph agents, incident/evidence core |
| Delivery | `.github/workflows/`, `automation/` | CI, GHCR, SSH deploy, rollback | OIDC, registry, scan, rolling deploy EKS, deployment metadata |

### 3.2. Bằng chứng từ code

| Thành phần | Bằng chứng | Đánh giá |
|---|---|---|
| Webhook | `agent_src/core/main.py` | Có Alertmanager, GitHub và Telegram endpoints |
| Async processing | `agent_src/core/tasks.py` | Có Celery task; chưa có specialist fan-out/chord |
| RAG | `agent_src/core/rag_engine.py` | Có ChromaDB; pgvector là POC thay thế |
| Runbook governance | `agent_src/core/runbook_registry.py` | Có revision, draft, approval và audit JSONL |
| Diagnostics | `agent_src/tools/diag_tools.py` | Tool thử nghiệm; chưa có typed contract/least-privilege gateway đầy đủ; MCP là POC |
| Release | `automation/app-release-deploy.sh` | Có role gate, health check và rollback cho EC2 Compose |
| CI/CD | `.github/workflows/*.yml` | Có build/deploy; chưa dùng AWS OIDC và chưa deploy EKS |

### 3.3. Khoảng cách và chiến lược chuyển đổi

| Nhóm | Baseline | V2 bắt buộc | Cách chuyển |
|---|---|---|---|
| Compute | Ba EC2 cố định | EKS worker đa AZ | Containerize giữ API contract; deploy song song sandbox |
| Database | PostgreSQL container | RDS PostgreSQL Multi-AZ | Schema migration, backup/restore rehearsal, endpoint cutover |
| Queue/state | Redis/Celery và context TTL | Durable incident store + LangGraph checkpoints | Giữ Celery ingestion ở phase đầu; thêm repository có cấu trúc |
| Monitoring | Prometheus threshold | Metrics, logs, health checks và CI/CD events | Giữ Prometheus/CloudWatch; traces/AMP là POC |
| AI | Một workflow theo alert | Application layer + bốn Infrastructure Agents + Aggregator | Tách tools/contracts trước, rồi LangGraph orchestration |
| CI/CD | SSH deploy tới EC2 | OIDC và deploy EKS | Chạy dual path staging, bỏ long-lived AWS credentials |
| Knowledge | ChromaDB local | Dependency store version hóa + ChromaDB | Neo4j/pgvector là POC sau khi MVP ổn định |
| Security | SG, HMAC GitHub | redaction, KMS, Secrets Manager, audit, SoD | Security gateway đứng trước LLM và knowledge |

### 3.4. Nguyên tắc tương thích khi chuyển đổi

- Không xóa luồng EC2 hiện tại trước khi EKS staging vượt acceptance test.
- Giữ `/health`, `/api/health` và `/api/ready` để so sánh baseline.
- Giữ Alertmanager payload adapter; thêm schema V2 phía sau adapter.
- Giữ deterministic runbooks và quota LLM bảo thủ.
- Không dùng PostgreSQL workload làm incident/control-plane store.
- Không copy dữ liệu ChromaDB runtime hoặc secret vào image/repository.
- Mọi cutover phải có rollback plan và thời điểm đo baseline.

---

## 4. Kiến trúc MVP và production reference

### 4.1. VPC hai Availability Zone bắt buộc

```text
Internet
   |
Public ALB
   |
Public subnets:       AZ-a | AZ-b
Private app subnets:  EKS nodes/pods trên AZ-a | AZ-b
Private data subnets: RDS primary/standby trên hai AZ
```

Yêu cầu nghiệm thu:

- Terraform tạo public/private subnet trên hai AZ và các route/Security Group cần thiết.
- Public subnet không chạy application workload.
- EKS worker và RDS ở private subnet.
- Security Group chỉ cho phép luồng cần thiết; không mở Prometheus, Alertmanager hoặc AI API ra `0.0.0.0/0`.
- EKS API endpoint ưu tiên private; nếu POC cần public endpoint phải giới hạn CIDR và ghi audit.
- Có test workload tiếp tục phục vụ khi một pod/node target bị loại khỏi một AZ.

Thiết kế ba AZ, NAT Gateway theo từng AZ, CloudFront/WAF và đầy đủ VPC endpoints được giữ làm production reference. MVP có thể dùng topology egress tiết kiệm chi phí nhưng phải ghi rõ giới hạn; không dùng nó để tuyên bố zone independence hoàn chỉnh.

### 4.2. Amazon EKS

Thiết kế compute:

| Nhóm | Mục đích | Cách cấp phát |
|---|---|---|
| System nodes | CoreDNS, controllers, OTel, policy components | Managed Node Group ổn định, trải trên ít nhất hai AZ |
| Application nodes | Mobile Banking, Transaction Service, agent services | Managed Node Group trải trên ít nhất hai AZ |
| Sensitive jobs | Migration/security jobs | Taint/toleration trên node group hiện có; NodePool riêng chỉ khi có bằng chứng cần |

Yêu cầu workload:

- Tối thiểu hai replicas cho service quan trọng trong staging HA test.
- `topologySpreadConstraints` và pod anti-affinity để phân bố pod giữa AZ/node.
- PodDisruptionBudget, readiness/liveness/startup probes và graceful shutdown.
- Resource request/limit và HPA cho workload đại diện.
- Production pin AMI và version add-on đã kiểm thử.
- RBAC, Kubernetes service account và IAM role theo least privilege.
- NetworkPolicy tách namespace `app`, `observability`, `aiops` và `security`.

Managed Node Group là kết quả bắt buộc. Karpenter là POC sau khi workload hai AZ ổn định; nếu làm POC, controller không được chạy trên node do chính Karpenter quản lý. Không hard-code một instance type duy nhất cho production; `t3.medium` và `m5.large` chỉ là điểm bắt đầu để benchmark capacity/cost.

### 4.3. Amazon RDS Multi-AZ

Mục tiêu:

- PostgreSQL trong private data subnets.
- Multi-AZ với standby khác AZ, automated backup và point-in-time recovery.
- KMS encryption, TLS, Secrets Manager rotation và SG chỉ nhận từ workload hợp lệ.
- Enhanced Monitoring và Database/Performance Insights theo khả năng hỗ trợ.
- Export error/slow-query logs có kiểm soát; query parameter và giá trị nhạy cảm phải được mask.
- RDS Proxy là tùy chọn nếu benchmark chứng minh cần ổn định connection pool.

Phải tách:

```text
workload-db       -> dữ liệu demo Fintech
control-plane-db  -> incident, evidence, approval, audit, evaluation
vector store      -> embedding đã redact và được duyệt
```

RDS Multi-AZ là HA, không phải read scaling. Nếu cần read scaling phải thiết kế read replica hoặc lựa chọn cluster riêng và đánh giá chi phí.

### 4.4. CI/CD GitHub Actions

```text
Pull request
  -> lint/unit/integration
  -> SAST + dependency/container/IaC scan
  -> build image
  -> sign/SBOM
  -> push registry
  -> deploy staging
  -> smoke/security checks
  -> approval/environment protection
  -> rolling deployment
  -> verify/rollback
```

Yêu cầu:

- GitHub OIDC đổi token ngắn hạn lấy AWS role; không lưu access key dài hạn.
- Trust policy khóa theo organization/repository/branch/environment.
- Quyền `id-token: write` chỉ cấp cho job cần assume role.
- Staging và production dùng role khác nhau; production có environment approval.
- Image được tham chiếu bằng immutable digest trong deployment record.
- Database migration là job riêng, có pre-check, lock, backup/restore plan và không tự rollback destructive migration.
- Chuyển dần từ SSH deploy EC2 sang Kubernetes deployment; legacy path chỉ giữ trong migration.
- Canary/blue-green production nâng cao là Future Work, không phải điều kiện nghiệm thu.

### 4.5. Observability bắt buộc và POC

| Trụ cột | Nguồn | Collector/store mục tiêu | Khóa tương quan bắt buộc |
|---|---|---|---|
| Metrics | EKS data plane, app, RDS, GitHub workflows | Prometheus/CloudWatch | service, namespace, cluster, workflow_run_id |
| Logs | Pod/app, EKS audit/control plane, RDS, CloudTrail, GitHub run logs | OTel/Fluent Bit -> CloudWatch Logs | deployment_id, commit_sha, run_id; trace_id nếu có |
| Health checks | Mobile Banking, Transaction Service và dependencies | Probes/Prometheus/CloudWatch | capability, service, deployment_id |
| Traces | Microservice request và agent/tool spans | OpenTelemetry -> X-Ray/CloudWatch | trace_id, service.version, image.digest |

GitHub Actions ingestion có hai đường:

1. Webhook `workflow_run`/`workflow_job` để phát hiện gần thời gian thực.
2. Polling reconciliation để bù webhook bị mất và tải logs/artifacts qua GitHub API.

Metrics, logs và health checks là bắt buộc. AMP, distributed traces đầy đủ và OpenTelemetry workflow telemetry là POC; webhook/API vẫn là nguồn kiểm chứng cho CI/CD.

### 4.6. Knowledge layer

**Dependency model bắt buộc:**

```text
BusinessCapability -> ApplicationService -> KubernetesWorkload -> RDSDatabase
                           ^                       ^
                           |                       |
Repository -> Commit -> WorkflowRun -> Image -> Deployment
```

MVP lưu topology bằng PostgreSQL có cấu trúc hoặc JSON/YAML được version hóa. Mỗi edge có `source`, `environment`, `valid_from`, `valid_to` và `confidence`. Neo4j là POC; việc không dùng Neo4j không được làm mất khả năng truy App -> Service -> Kubernetes -> RDS/Network -> Deployment.

**Vector knowledge:**

- ChromaDB hiện tại tiếp tục phục vụ retrieval bắt buộc trong migration.
- Aurora PostgreSQL-compatible/PostgreSQL có `pgvector` là POC thay thế.
- Chỉ lưu runbook đã duyệt, incident đã verified và error pattern đã redact.
- Mỗi chunk có tenant/environment, sensitivity, source, version và reviewer.

### 4.7. Agent runtime và observability

- LangGraph container trên EKS là state machine/runtime bắt buộc; các agent giao tiếp bằng internal typed contracts.
- Gemini hiện tại có thể tiếp tục làm LLM baseline. Amazon Bedrock/model khác là POC và phải qua cùng evaluation; LLM vendor không quyết định đóng góp.
- AgentCore Runtime/Gateway và A2A deployment là Future Work.
- MCP tool contract có thể làm POC; MVP vẫn phải có schema, role, allowlist, timeout và audit tương đương.
- Celery hiện tại có thể giữ vai trò ingestion/background/reconciliation trong giai đoạn đầu; không phải nguồn trạng thái incident cuối cùng.
- Agent trace tối thiểu được lưu vào control-plane audit/metrics. Langfuse chỉ là POC và chỉ nhận dữ liệu đã redact.
- Audit record không được phụ thuộc duy nhất vào Langfuse hoặc LLM trace.
- Kubernetes Agent được triển khai custom bằng LangGraph trong MVP để kiểm soát contract và quyền. Kagent chỉ là adapter/POC tùy chọn; nếu dùng vẫn phải qua cùng tool policy, RBAC và evidence schema.

### 4.8. Presentation layer

- API và Telegram hiện tại là giao diện bắt buộc để xem incident/approval trong MVP.
- Web Dashboard, Slack, GitHub Checks và Jira draft là POC.
- Email và Teams là Future Work.
- Web Dashboard nếu làm POC chỉ hiển thị incident, timeline, evidence, agent status, approval và verification; không xây lại dashboard metrics của Grafana.
- Không hiển thị raw PII/PCI/secret trên bất kỳ kênh notification nào.

---

## 5. Kiến trúc Multi-Agent xuyên App–Infrastructure

### 5.1. Agent và quyền

| Agent | Trách nhiệm | Tool read-only chính | Mutation |
|---|---|---|---|
| Orchestrator | Phân loại, lập investigation plan, route, loop limit | incident/topology lookup | Không |
| Mobile Banking/Application Agent | Ánh xạ business symptom, capability, criticality và dependency kỹ thuật | service catalog, dependency, business runbook | Không |
| Kubernetes Agent | Pod/node/deployment/event/RBAC diagnosis | Kubernetes API, PromQL, logs, probes | Chỉ tạo proposal |
| RDS Agent | Slow query, connection, deadlock, failover, migration | RDS APIs, insights, sanitized logs | Chỉ tạo proposal |
| GitHub Actions Agent | Workflow/job/log/artifact/deploy diagnosis | GitHub API, Checks, workflow metadata | Chỉ tạo proposal |
| Security/Compliance Agent | Kiểm tra redaction, secret/PII finding, IAM/audit review | policy, CloudTrail, redaction scanners | Có quyền veto; không tự sửa |
| Network/API context | Load Balancer, endpoint, DNS/network path | read-only probes và AWS metadata | Agent riêng là POC |
| Aggregator | Merge evidence, score RCA/impact | evidence/topology store | Không |
| Verification Agent | Kiểm tra post-condition độc lập | metrics, logs, traces, status APIs | Chỉ cập nhật kết quả verification |

Mobile Banking Agent là Application Agent bắt buộc. BNPL, Investment và Credit Scoring có thể dùng cùng generic Application Agent với scenario/dependency pack; không bắt buộc có bốn runtime độc lập. Bốn Infrastructure Agents tối thiểu là Kubernetes, RDS, GitHub Actions và Security. Network/API có thể là context/tool read-only trong MVP.

### 5.2. State dùng chung

```python
class AgentState(TypedDict):
    schema_version: str
    incident_id: str
    incident_type: Literal["application", "infrastructure", "ci_cd", "security", "mixed"]
    query: str
    normalized_events: list[dict]
    entities: list[dict]
    hypotheses: list[dict]
    evidence: list[dict]
    affected_capabilities: list[dict]
    agent_runs: list[dict]
    investigation_round: int
    data_classification: str
    redaction_status: str
    diagnosis: dict | None
    remediation_plan: dict | None
    requires_human_approval: bool
    approval: dict | None
    verification: dict | None
    next_node: str
```

State production phải checkpoint vào control-plane store. Không chỉ giữ trong process memory.

### 5.3. Điều phối

Routing không chỉ dựa vào từ khóa. Nó dùng:

1. `event_type` và `source`.
2. Entity đã resolve: business capability, application service, cluster, namespace, workflow và RDS instance.
3. Dependency/change model.
4. Data classification.
5. Evidence gap.

Ví dụ deployment failure do migration:

```text
GitHub workflow fails
  -> GitHub Agent: migration step + commit + error signature
  -> RDS Agent: lock/deadlock/schema state
  -> Kubernetes Agent: rollout and pod readiness
  -> Mobile Banking Agent: transfer capability bị ảnh hưởng
  -> Security Agent: xác nhận redaction và policy
  -> Aggregator: migration failure is root cause,
                 rollout/pod/transfer errors are impact
```

### 5.4. Loop và partial failure

- Tối đa ba investigation rounds.
- Mỗi agent có deadline và tool-call budget.
- Tool retry dùng exponential backoff, giới hạn và idempotency key.
- Agent timeout trả `PARTIAL` hoặc `FAILED` có reason, không trả evidence giả.
- Nếu evidence coverage dưới ngưỡng, kết quả là `INCONCLUSIVE/ESCALATED`.
- Không route lại chính agent với cùng input và cùng evidence gap.

### 5.5. Aggregator

Aggregator là điểm duy nhất:

- Deduplicate evidence.
- Kiểm tra freshness, provenance và contradictions.
- Tính RCA score và impact.
- Gắn evidence ID vào từng claim.
- Xác định uncertainty.
- Sinh structured proposal cho policy.

LLM có thể viết phần giải thích sau khi Aggregator hoàn tất, nhưng không sửa score/evidence gốc.

---

## 6. Pattern mining và phát hiện bất thường

Phạm vi bắt buộc chỉ gồm log normalization, template/fingerprint ổn định, dedup và frequency/time-window features cần cho incident correlation. Drain/Drain3, LogPAI, Isolation Forest, drift lifecycle và automatic baseline promotion là POC; chúng không được làm chậm Incident Core và scenario Mobile Banking trung tâm.

### 6.1. Pipeline

```text
Raw telemetry
  -> security redaction
  -> parse + canonicalize
  -> bỏ timestamp/request ID/giá trị biến động
  -> template fingerprint bắt buộc
  -> Drain/Drain3 hoặc thuật toán LogPAI nếu làm POC
  -> pattern_id + parameter schema
  -> baseline theo service/environment/version/time window
  -> novelty/frequency/change score
  -> event hoặc suppression decision
```

Không bỏ qua một pattern chỉ vì “đã thấy”. Pattern bình thường nhưng tăng tần suất đột biến vẫn có thể bất thường.

### 6.2. Vòng đời pattern

```text
CANDIDATE -> OBSERVED -> REVIEWED_NORMAL
                     \-> REVIEWED_ABNORMAL
                     \-> QUARANTINED

REVIEWED_NORMAL -> DRIFTED -> CANDIDATE
```

Mỗi pattern phải có service, environment, application version, first/last seen, count, redaction status, reviewer và baseline version.

### 6.3. Training, shadow và active cho POC

1. **Training:** học baseline từ khoảng thời gian đã xác nhận không có incident lớn.
2. **Shadow:** tính anomaly nhưng không gửi action/alert tới người vận hành.
3. **Active:** chỉ tạo signal sau khi đạt threshold trên validation set.

Không tự coi toàn bộ log trong “training window” là bình thường. Cần loại maintenance, incident và dữ liệu bị nhiễm.

### 6.4. Metric anomaly POC

Nếu triển khai POC, chọn một detector time-window như Isolation Forest hoặc robust seasonal baseline. Input:

- CPU/memory/network/error/latency.
- Kubernetes restart/pending/unschedulable.
- RDS connections, DB load, deadlocks, replica/failover event.
- GitHub success rate, queue time, duration và job failure rate.

Detector là một nguồn evidence, không tự quyết định RCA.

---

## 7. Cross-domain CI/CD observability

### 7.1. Canonical deployment identity

Mọi release record phải lưu:

```text
business_capability
application_service
repository
commit_sha
pull_request
workflow_run_id
workflow_job_id
artifact_id
image_name
image_digest
deployment_id
cluster
namespace
workload
revision
database_migration_id
deployed_at
```

Đây là cầu nối giữa Application Agent, GitHub Actions Agent, Kubernetes Agent và RDS Agent; nó cho phép Aggregator phân biệt technical failure với business impact.

### 7.2. Sự kiện CI/CD

- Workflow/job queued, started, completed.
- Build/test/security scan failure.
- Artifact/image publish.
- Deployment started/completed/rolled back.
- Migration started/completed/failed.
- GitHub rate limit, webhook delivery gap và polling reconciliation.

### 7.3. Tool của GitHub Actions Agent

```text
list_workflow_runs()
get_workflow_run()
list_workflow_jobs()
download_workflow_logs()
list_or_download_artifacts()
get_commit_and_pull_request()
get_deployment_status()
create_check_summary_draft()
propose_rerun()
```

Mutation như rerun, cancel, comment hoặc Checks update phải đi qua policy riêng. Log tải xuống phải redact trước khi lưu hoặc gửi LLM.

### 7.4. Rerun policy

- Không rerun nếu failure là deterministic như compile error, failed assertion ổn định hoặc migration schema conflict.
- Chỉ đề xuất rerun cho transient failure có evidence.
- Mặc định tối đa một automatic attempt trong sandbox/staging; production mutation bị vô hiệu trong khóa luận.
- Dùng idempotency key theo workflow run/job/attempt.
- Sau rerun phải verification cả CI result và deployment state.

---

## 8. Tool calling, guardrails và HITL

### 8.1. Tool contract

MVP bắt buộc enforce contract dưới đây trong code. MCP là một adapter POC; semantics an toàn không được phụ thuộc vào việc có MCP hay không.

Mỗi tool phải khai báo:

```text
name, version, owner
purpose
input/output JSON schema
read_only hoặc mutation
allowed_agent_roles
allowed_targets
data_classification
timeout và rate limit
required_approval
idempotency semantics
audit fields
```

Không expose generic `exec`, `bash`, `ssh`, `kubectl` hoặc unrestricted SQL cho LLM.

### 8.2. Risk matrix

| Mức | Ví dụ | Hành vi |
|---|---|---|
| Read-only | Query logs/metrics/status/topology | Tự động, audit |
| Thấp | Gửi notification, tạo issue/check draft | Tự động nếu không lộ dữ liệu |
| Trung bình | Rerun job transient, restart pod staging, scale staging | Approval hoặc policy exception đã duyệt; có giới hạn |
| Cao | Production rollout/rollback, DB failover/failback, secret rotation | Bị vô hiệu trong khóa luận |
| Cấm tự động | IAM/SG broadening, destructive DB migration, xóa cluster/DB | Từ chối hoặc quy trình break-glass ngoài agent |

Scale deployment không được mặc định coi là “thấp” trong production vì có thể tăng chi phí hoặc khuếch đại lỗi.

Mọi remediation được trình diễn trong khóa luận chỉ chạy trên staging. Production, IAM, Security Group, database schema và secret mutation nằm ngoài executor allowlist.

### 8.3. Approval contract

Approval phải chứa:

- Incident, diagnosis, evidence IDs và uncertainty.
- Action ID/version, target, environment và exact parameters.
- Risk, blast radius, expected result và rollback/stop condition.
- Plan hash, expiry, requester và required approver role.
- Dữ liệu đã redact để hiển thị.

Approval hết hạn hoặc plan hash thay đổi phải bị từ chối.

### 8.4. Segregation of Duties

- Người tạo/publish production workflow không tự phê duyệt action rủi ro cao của chính workflow đó nếu policy yêu cầu tách nhiệm vụ.
- Security Agent có quyền veto nhưng không có quyền tự thực thi.
- Executor chỉ nhận action có kiểu và token ngắn hạn.
- Verification dùng credentials read-only độc lập với executor khi có thể.

### 8.5. Auditability

Audit event ghi append-only:

```text
audit_id, timestamp, actor_type, actor_id
incident_id, agent_run_id, tool_call_id
action, target, input_hash, output_hash
policy_version, decision, approval_id
model_id, prompt_template_version
redaction_policy_version
```

CloudTrail/GitHub audit logs là nguồn bổ sung. Với production reference, audit archive dùng KMS và retention/immutability policy phù hợp; Langfuse không thay thế audit store.

Operational incident, evidence, prompt trace và knowledge stores chỉ nhận dữ liệu đã redact. Nếu cần giữ raw log cho điều tra, raw log phải ở kho tách biệt, mã hóa, quyền hạn chế và không được đưa vào LLM/knowledge.

---

## 9. Knowledge và self-evolution an toàn

MVP giữ ChromaDB và bắt buộc governance cho runbook/incident memory. Tự động tạo knowledge release hoặc pattern promotion là POC; Neo4j/pgvector không phải dependency của phần này.

### 9.1. Dữ liệu được phép học

- Incident đã `VERIFIED_RESOLVED` hoặc đã được review.
- Runbook đã publish.
- Pattern được reviewer phân loại.
- GitHub failure pattern đã redact và có outcome.
- Admin feedback đã qua kiểm tra prompt injection, secret và destructive action.

### 9.2. Dữ liệu không được học tự động

- Log thô chứa PII/PCI/secret.
- LLM output chưa kiểm chứng.
- Incident chưa kết luận.
- PR comment hoặc issue từ nguồn không tin cậy.
- Action thành công chỉ theo exit code nhưng verification thất bại.

### 9.3. Versioning và rollback

Mỗi knowledge release có:

```text
knowledge_release_id
included_documents/patterns
source hashes
reviewers
redaction policy version
embedding model version
evaluation result
activated_at
previous_release_id
```

Chỉ activate khi retrieval regression và security tests đạt yêu cầu.

---

## 10. Lược đồ dữ liệu và máy trạng thái

### 10.1. Event schema V2

```json
{
  "schema_version": "2.0",
  "event_id": "evt-uuid",
  "correlation_id": "corr-uuid",
  "incident_id": null,
  "source": "github_actions",
  "event_type": "deployment_failed",
  "status": "firing",
  "observed_at": "2026-08-29T10:00:00Z",
  "received_at": "2026-08-29T10:00:03Z",
  "environment": "staging",
  "entities": {
    "business_capability": "mobile_banking_transfer",
    "application_service": "transaction-service",
    "repository": "org/repo",
    "commit_sha": "sha",
    "workflow_run_id": "123",
    "cluster": "fintech-staging",
    "namespace": "banking",
    "service": "payment-api",
    "database": "workload-db"
  },
  "signal": {
    "name": "migration_exit_code",
    "value": 1
  },
  "data_classification": "internal",
  "redaction": {
    "status": "passed",
    "policy_version": "redact-v1"
  },
  "fingerprint": "sha256:..."
}
```

Phải tách `observed_at` và `received_at`, đồng thời lưu clock-skew/ingestion delay nếu cần phân tích temporal order.

### 10.2. Evidence schema

```text
evidence_id
incident_id
agent_run_id
kind: metric | log_pattern | trace | topology | change | audit | probe
source
query_or_reference
observed_at
collected_at
value_or_summary
freshness
quality
data_classification
redaction_status
supports
contradicts
content_hash
```

### 10.3. Incident state machine

```text
RECEIVED -> REDACTING -> NORMALIZING -> DEDUPLICATING
DEDUPLICATING -> DUPLICATE (terminal, link về canonical event/incident)
DEDUPLICATING -> CORRELATING -> OPEN
OPEN -> INVESTIGATING -> AGGREGATING -> DIAGNOSED
DIAGNOSED -> PLANNED -> AWAITING_APPROVAL
AWAITING_APPROVAL -> APPROVED | REJECTED | EXPIRED
APPROVED -> EXECUTING -> VERIFYING
EXECUTING -> EXECUTION_FAILED -> ESCALATED
VERIFYING -> RESOLVED
VERIFYING -> VERIFICATION_FAILED -> ROLLING_BACK | ESCALATED
ROLLING_BACK -> VERIFYING | ESCALATED
RESOLVED -> REOPENED
```

`DUPLICATE` là kết quả xử lý event, không phải incident mới. `REJECTED` và `EXPIRED` là terminal cho remediation plan nhưng incident có thể vẫn mở. Chỉ Verification Agent hoặc deterministic verification service được tạo `RESOLVED`; verification không đạt phải tạo `VERIFICATION_FAILED`.

### 10.4. Storage

Control-plane schema tối thiểu:

```text
events, incidents, incident_events, incident_timeline
entities, entity_links, topology_versions
patterns, pattern_observations, baseline_versions
hypotheses, evidence
orchestration_runs, agent_runs, tool_calls
diagnoses, remediation_plans, policy_decisions
approvals, execution_runs, verification_runs
knowledge_releases, feedback, audit_log
workflow_runs, deployments, migrations
```

Redis chỉ dùng cache/queue/lock có TTL. Nó không phải source of truth cho incident lifecycle.

---

## 11. Kịch bản xuyên App–Infrastructure

### 11.1. CD-07: deployment lỗi do database migration

Tạo một migration staging có lỗi đã biết làm hỏng luồng chuyển tiền Mobile Banking:

```text
Database migration lỗi
  -> GitHub Actions deployment không hoàn tất
  -> Transaction Service rollout/readiness lỗi trên EKS
  -> Mobile Banking không chuyển tiền được
  -> RDS log/lock/schema cung cấp evidence nguyên nhân
```

Hệ thống phải:

1. Nhận `workflow_job`/`workflow_run` event và bù bằng polling nếu cần.
2. Redact secret/SQL values trước persistence và LLM.
3. Chuẩn hóa event với business capability, application service, commit, run, image, deployment, cluster và migration ID.
4. Gom các signals vào một mixed incident.
5. GitHub Agent xác định step và error pattern.
6. RDS Agent kiểm tra schema/migration/lock bằng read-only tool.
7. Kubernetes Agent xác định rollout/pod là downstream impact.
8. Mobile Banking Agent xác định capability `transfer_money` bị ảnh hưởng và Transaction Service là technical dependency.
9. Security Agent xác nhận redaction và không có secret leakage.
10. Aggregator xếp migration failure đứng đầu; API, pod readiness và giao dịch lỗi là downstream impact, kèm evidence IDs.
11. Đề xuất action staging an toàn: dừng rollout/rerun sau fix hoặc rollback application; không tự rollback destructive migration.
12. Policy yêu cầu approval cho mutation.
13. Verification kiểm tra workflow, deployment, pod readiness, Transaction API, schema version và luồng chuyển tiền synthetic.
14. Lưu timeline/audit và chỉ học incident sau review.

### 11.2. K8S-01: Pod CrashLoopBackOff/OOMKilled

Phải phân biệt:

- OOM do resource limit.
- App crash do configuration/secret.
- Dependency RDS không sẵn sàng.

Không restart loop vô hạn. Nếu restart không sửa root cause, chuyển `ESCALATED`.

### 11.3. RDS-01: RDS failover

Đo:

- Thời gian phát hiện event.
- Connection errors và recovery.
- Readiness của Transaction Service và availability của Mobile Banking.
- Agent có phân biệt failover với database down kéo dài không.

Không kích hoạt failover production từ agent trong phạm vi khóa luận.

### 11.4. SEC-01: secret/PII leakage trong CI log

Hệ thống phải:

- Phát hiện và redact trước LLM/vector store.
- Không đưa giá trị secret vào Telegram/Slack/Jira/GitHub Checks.
- Tạo security incident và khuyến nghị rotation.
- Không tự rotate production secret; chỉ tạo security incident và đề xuất runbook.

### 11.5. INT-01: GitHub API/webhook outage

- Webhook gap được phát hiện.
- Polling reconciliation bù event.
- Rate limit được tôn trọng.
- Incident context không bị nhân đôi.

### 11.6. Scenario pack tái sử dụng

Ít nhất một trong ba scenario sau phải chạy trên cùng Incident Core, contracts và Aggregator:

- **BNPL:** tạo khoản vay lỗi hoặc payment timeout.
- **Investment:** market data chậm hoặc order failure.
- **AI Credit Scoring:** thiếu feature hoặc model endpoint chậm.

Các scenario pack không bắt buộc có full-stack hoặc agent runtime riêng. Mục đích là chứng minh dependency/business-impact model có thể tái sử dụng ngoài Mobile Banking.

---

## 12. Bảo mật và compliance

### 12.1. Data flow boundary

```text
Untrusted logs/webhooks/docs
        |
signature/auth + schema validation
        |
PII/PCI/secret classifier and redactor
        |
sanitized event/evidence
        |
incident store / agents / LLM / knowledge
```

Raw sensitive data nếu cần lưu điều tra phải ở kho hạn chế riêng, mã hóa và retention ngắn; LLM chỉ nhận bản sanitized.

### 12.2. Threats bắt buộc kiểm thử

- Forged GitHub/Alertmanager webhook.
- Prompt injection trong log, artifact, issue hoặc runbook.
- Secret exfiltration qua tool output.
- Cross-tenant/cross-environment retrieval.
- Approval replay hoặc plan tampering.
- Excessive tool permissions.
- Poisoned “normal” pattern.
- Audit deletion hoặc sửa lịch sử.
- CI dependency/action supply-chain risk.

### 12.3. Secrets và identity

- AWS Secrets Manager cho database/API credentials.
- GitHub OIDC cho AWS authentication.
- KMS encryption cho RDS, logs, artifacts và knowledge stores.
- Kubernetes Secret chỉ là delivery mechanism; ưu tiên CSI/External Secrets khi POC được chốt.
- Không commit `.env`, Terraform state, key, token hoặc runtime vector database.

### 12.4. Compliance evidence

Mỗi scenario cần xuất:

- Ai/agent nào đã đọc dữ liệu hoặc gọi tool.
- Policy/version nào đã quyết định.
- Approval của ai và khi nào.
- Action target và immutable input hash.
- Verification result.
- Redaction count/type nhưng không chứa giá trị nhạy cảm.

---

## 13. Kiểm thử và đánh giá

### 13.1. Hai nhóm đánh giá

Không gộp tác động của việc chuyển hạ tầng với chất lượng AIOps:

| Nhóm | Scenario bắt buộc | Mục tiêu |
|---|---|---|
| **AWS Platform** | OIDC deploy, pod/node target failure trên hai AZ, RDS failover | Chứng minh MVP AWS triển khai và chịu lỗi đúng thiết kế |
| **AIOps Quality** | Mobile Banking migration, CrashLoop/OOM, webhook gap, secret leakage, agent/source outage | Đo correlation, RCA, impact, safety và graceful degradation |

Scenario performance/slow query là bổ sung nếu đủ thời gian. Multi-region DR, DDoS và ransomware chỉ tabletop/Future Work.

### 13.2. Phương pháp so sánh

| Mã | Phương pháp |
|---|---|
| B0 | Hệ thống EC2 hiện tại: alert riêng lẻ + runbook/Gemini + Telegram |
| B1 | Rule correlation + dependency, không multi-agent |
| P | Application + Infrastructure Agents + dependency model + deterministic Aggregator |

Biến thể B2 hoặc các cấu hình bỏ thành phần được dùng cho ablation, không phải baseline bắt buộc.

### 13.3. Chỉ số

**Vận hành:**

- MTTD, thời gian điều tra, MTTR.
- Alert compression ratio và số incident cần con người xử lý.
- Workflow failure recovery time.
- Fan-out/graph latency và agent completion rate.
- Tool calls, token và chi phí trên incident.

**Chẩn đoán:**

- RCA top-1/top-3.
- Cross-domain diagnosis accuracy.
- Impact accuracy.
- Evidence coverage và unsupported-claim rate.
- Calibration giữa confidence và kết quả thực.

**Phát hiện:**

- Precision, recall, F1 và false-positive rate.
- New-pattern detection latency.
- Drift detection và false-normal promotion.

**An toàn/compliance:**

- PII/secret redaction recall trên fixture.
- HITL compliance.
- Unauthorized-action rate.
- Approval replay/tamper rejection.
- False resolution rate.
- Audit completeness.

Các mục tiêu từ đặc tả như infrastructure accuracy >85%, CI/CD accuracy >80%, MTTD <2 phút, MTTR giảm ít nhất 50%, false positive <5% và PII redaction 100% là **acceptance targets cần kiểm chứng**, không phải kết quả đã đạt.

### 13.4. Ablation

```text
P-full
P-no-application-context
P-no-dependency-model
P-no-cross-domain-change-links
P-no-security-agent
P-no-log-evidence
P-no-temporal-order
P-rules-only
P-LLM-only
```

Nếu pattern mining hoặc Neo4j POC được triển khai, thêm `P-no-pattern-mining` hoặc `P-no-neo4j` như thí nghiệm phụ; không biến chúng thành điều kiện nghiệm thu.

### 13.5. Dữ liệu thực nghiệm

Mỗi run lưu:

```text
scenario_id, run_id, method, seed
injected_fault, ground_truth
start/end timestamps
raw sanitized events
expected/observed incident grouping
expected/observed RCA and impact
agent/tool traces
policy/approval/action/verification
cost and latency
software/config versions
```

Không tự tạo số liệu hoặc chỉ giữ screenshot của trường hợp tốt.

### 13.6. Giao thức chạy benchmark

1. Chốt scenario, fault profile, ground truth và metric trước khi chạy.
2. Chạy ba pilot runs để sửa harness; pilot không được đưa vào kết quả chính.
3. Đóng băng commit, image digest, infrastructure version, dependency data, `rca-v1` weights, prompt và policy.
4. Chạy tối thiểu **10 lần độc lập cho mỗi cặp scenario–method** với cùng fault profile và collection window.
5. Randomize thứ tự method khi khả thi để giảm bias do tải/thời gian.
6. Báo cáo median, IQR, min/max, failure count và raw sanitized records; không chỉ báo cáo giá trị trung bình.
7. Nếu một run bị loại, phải ghi reason và không thay bằng run thuận lợi mà không audit.

---

## 14. Tiêu chí hoàn thành lát cắt V2

- Mobile Banking và Transaction Service chạy trên EKS với workload trải ít nhất hai AZ.
- Dữ liệu ứng dụng chạy trên RDS PostgreSQL Multi-AZ.
- GitHub Actions deploy staging bằng OIDC và ghi immutable deployment identity.
- Một deployment/migration failure tạo đúng một incident xuyên Mobile Banking–GitHub–EKS–RDS.
- Báo cáo xác định migration là root cause và giao dịch/API/pod readiness là impact.
- Ít nhất một scenario BNPL, Investment hoặc Credit Scoring tái sử dụng nền tảng chung.
- Mọi claim chính có evidence ID và provenance.
- Secret/PII fixture không xuất hiện trong prompt trace, notification hoặc vector store.
- Agent timeout vẫn tạo kết quả partial có uncertainty.
- Không mutation nào vượt policy/approval.
- Rerun/restart có idempotency và loop limit.
- Verification thất bại không tạo trạng thái `RESOLVED`.
- Webhook gap được polling reconciliation bù mà không tạo incident trùng.
- Có thể replay scenario và tái tạo bảng metric.
- Baseline B0, B1 và P dùng cùng ground truth, fault profile và cửa sổ đo.
- Có ba pilot runs và tối thiểu 10 benchmark runs cho mỗi cặp scenario–method.

---

## 15. Lộ trình 12 tuần

### 15.1. Ba nhóm công việc

| Nhóm | Tuần trọng tâm | Kết quả |
|---|---|---|
| **Nền tảng AWS** | 2–5 | VPC hai AZ, OIDC, EKS, RDS Multi-AZ, Mobile Banking và observability tối thiểu |
| **AIOps xuyên tầng** | 5–10 | Event/redaction, Incident Core, dependency, agents, Aggregator, HITL và staging remediation |
| **Đánh giá** | 1, 11–12 | Baseline/ground truth, pilot, repeated benchmark, ablation, hardening và báo cáo |

Ba nhóm có artifact và metric riêng. Đánh giá AWS Platform không được trộn với đánh giá AIOps Quality.

### 15.2. Phân công nhóm hai người

| Role | Trách nhiệm |
|---|---|
| Infrastructure/Platform Engineer | VPC/EKS/RDS/IAM/OIDC, observability, deployment, fault injection, cost và HA |
| AI/AIOps Engineer | schemas, redaction, Incident Core, dependency, Application/Infrastructure Agents, Aggregator, RAG, policy và evaluation |

Cả hai review chéo security, integration, dữ liệu và luận văn.

### 15.3. Kế hoạch và Definition of Done theo tuần

| Tuần | Nhóm chính | Công việc | Definition of Done |
|---:|---|---|---|
| 1 | Đánh giá | Đóng băng baseline; chốt Mobile Banking migration scenario, ground truth, schemas và metric | Baseline test/report chạy lại được; fixture có expected incident, RCA và impact |
| 2 | AWS | Terraform VPC hai AZ, public/private subnet, IAM và GitHub OIDC | `terraform validate/plan` đạt; workflow assume đúng staging role, sai repo/branch bị từ chối |
| 3 | AWS | EKS Managed Node Group, RBAC, namespaces; deploy Mobile Banking/Transaction Service | Frontend/API healthy; replicas trải hai AZ; pod failure không làm mất toàn bộ service |
| 4 | AWS | RDS PostgreSQL Multi-AZ, Secrets Manager, migration job và backup/restore | Transaction Service dùng RDS; failover/recovery có timestamp; migration fixture tạo lỗi kiểm soát |
| 5 | AWS + AIOps | Metrics, logs, health checks và service/deployment catalog | Truy được commit/image/deployment/workload/RDS cho một release; dashboard/queries lưu version |
| 6 | AIOps | Event schema, auth/validation và redaction trước persistence/LLM | Contract tests đạt; canary PII/secret không xuất hiện trong incident store, prompt hay notification |
| 7 | AIOps | Durable Incident Core, dedup/correlation, state machine và dependency model | Event trùng thành `DUPLICATE`; timeline sống qua restart; truy được Mobile Banking -> RDS/deployment |
| 8 | AIOps | Mobile Banking/Application Agent, Kubernetes Agent và RDS Agent | Agents trả schema/evidence; xác định business impact và biểu diễn timeout/partial failure |
| 9 | AIOps | GitHub Actions Agent, Security Agent, network context và deterministic Aggregator | Migration scenario có ranked RCA, evidence IDs, contradictions, uncertainty và affected capability |
| 10 | AIOps | Policy, approval, typed staging action và Verification | Ít nhất một rerun/restart/rollback staging chạy end-to-end; forbidden target và stale approval bị chặn |
| 11 | Đánh giá | Ba pilot runs, đóng băng `rca-v1`/config; chạy B0, B1, P và safety tests | Pilot tách khỏi result; mỗi scenario–method có 10 runs được ghi nhận, gồm cả success/failure, không discard run bất lợi |
| 12 | Đánh giá | Tính metric, ablation, hardening, tài liệu và demo | Raw sanitized data, scripts, plots, limitations, IaC và reproducibility guide được bàn giao |

Mỗi tuần chỉ được đánh dấu hoàn thành khi artifact nằm trong repository hoặc evidence store, có lệnh/fixture tái chạy và được thành viên còn lại review. POC/Future Work không được dùng để bù cho Definition of Done bắt buộc.

---

## 16. Kiểm thử

### 16.1. Unit

- Event/evidence schema, redaction và fingerprint.
- Log canonicalization và template/fingerprint; novelty/drift lifecycle chỉ kiểm thử nếu POC.
- Entity resolution và topology traversal.
- RCA score, contradiction và stale penalty.
- LangGraph routing/loop limit.
- Policy, plan hash, expiry, SoD và idempotency.
- Verification post-conditions.

### 16.2. Contract

- GitHub webhook/API adapter.
- Kubernetes API/tool output; MCP adapter chỉ kiểm thử nếu POC được triển khai.
- RDS monitoring/log adapter.
- Prometheus/CloudWatch queries; trace query chỉ kiểm thử nếu POC được triển khai.
- Internal typed agent response; MCP adapter chỉ kiểm thử nếu POC, A2A bị loại khỏi MVP.
- Dependency/ChromaDB repository contracts; pgvector/Neo4j chỉ kiểm thử nếu POC được triển khai.

### 16.3. Integration

- GitHub workflow -> event -> incident.
- Deployment -> EKS/RDS evidence -> Aggregator.
- Secret in log -> redaction -> safe notification.
- Agent timeout -> partial diagnosis.
- Approval -> typed action -> verification.
- Webhook outage -> polling -> no duplicate.

### 16.4. Infrastructure

- Terraform format/validate/plan.
- Kubernetes manifest/Helm lint.
- Policy-as-code and least-privilege checks.
- Pod disruption/node termination.
- RDS failover/restore.
- Network path/route checks; VPC endpoint chỉ kiểm thử nếu được provision.

### 16.5. Security

- Webhook signature and replay.
- Prompt injection fixtures.
- Secret/PII canary tokens.
- Target allowlist escape.
- Approval replay/tamper.
- Cross-environment retrieval.
- Malicious runbook/PR comment.

---

## 17. Cấu trúc repository mục tiêu

```text
terraform/
  modules/network/
  modules/eks/
  modules/rds/
  modules/observability/
  environments/staging/
  environments/production/

k8s/
  base/
  overlays/staging/
  overlays/production/
  helm/aiops/

agent_src/
  api/
  orchestration/
  agents/
    application/
      mobile_banking/
      scenario_packs/
    kubernetes/
    rds/
    github_actions/
    security/
    network_context/
  aggregation/
  incident_core/
  patterns/
  policy/
  verification/
  tools/
  knowledge/
  schemas/

evaluation/
  scenarios/
  fixtures/
  ground_truth/
  runners/
  metrics/
  results/

docs/
  CONTEXT_V2.md
  PLANNING_V2.md
  adr/
  runbooks/
```

Không di chuyển toàn bộ code ngay ở tuần đầu. Tạo package mới theo vertical slice và giữ adapter tương thích cho API hiện tại.

---

## 18. Ưu tiên khi thiếu thời gian

### Không được cắt

- Mobile Banking/Transaction Service chạy trên EKS hai AZ.
- RDS Multi-AZ và GitHub OIDC.
- App–GitHub–EKS–RDS deployment identity và dependency model.
- Event/evidence schema và durable incident state.
- Redaction trước operational persistence, LLM và knowledge.
- Mobile Banking/Application Agent, Kubernetes, RDS, GitHub và Security Agents.
- Deterministic Aggregator.
- Kịch bản Mobile Banking migration và SEC-01.
- Policy/HITL/verification/audit.
- Ít nhất một remediation staging.
- Baseline, ground truth, repeated benchmark và replayable evaluation.

### Cắt trước

1. Jira/Teams/Email; giữ Telegram hoặc Slack và GitHub Checks draft.
2. Web dashboard nâng cao; giữ API và trace.
3. Full production deploy; giữ staging sandbox.
4. Karpenter; giữ Managed Node Group.
5. Neo4j và pgvector mới; giữ dependency store version hóa và ChromaDB adapter.
6. AMP, distributed traces và Langfuse; giữ metrics/logs/health checks và control-plane audit.
7. Network/API Gateway Agent riêng; giữ tool/context read-only.
8. AgentCore/A2A deployment; giữ LangGraph container trên EKS và typed internal contracts.
9. Canary/blue-green nâng cao; giữ rolling staging deployment và rollback.
10. DR multi-region, DDoS, ransomware execution; giữ tabletop.
11. Tự tạo PR sửa code.

---

## 19. Danh sách kiểm tra trước bảo vệ

- [ ] Baseline EC2 được mô tả đúng và có test evidence.
- [ ] Kiến trúc V2 phân biệt đã có, bắt buộc, POC và Future Work.
- [ ] Mobile Banking/Transaction Service chạy được trên EKS.
- [ ] EKS workload trải ít nhất hai AZ và có failure test.
- [ ] RDS Multi-AZ có failover/restore evidence.
- [ ] GitHub Actions dùng OIDC, không dùng AWS key dài hạn.
- [ ] Có canonical identity và dependency từ business capability tới deployment/infrastructure.
- [ ] Metrics, logs, health checks và CI/CD signals được correlation.
- [ ] Mọi operational persistence, prompt, notification và knowledge chỉ nhận dữ liệu đã redact.
- [ ] Có Application Agent/context và bốn Infrastructure Agents tối thiểu.
- [ ] Agent trả structured evidence; Aggregator là điểm kết luận duy nhất.
- [ ] RCA score deterministic và version hóa.
- [ ] Partial failure không bị che giấu.
- [ ] Mọi mutation có policy, idempotency và audit.
- [ ] Action rủi ro có approval hợp lệ.
- [ ] Verification failure không tạo false resolution.
- [ ] Có ít nhất một remediation chỉ chạy trên staging.
- [ ] Có B0/B1/P, ba pilot runs, repeated benchmark, raw data và script metrics.
- [ ] Ít nhất một scenario BNPL/Investment/Credit Scoring tái sử dụng nền tảng.
- [ ] Không commit secret, state, key hoặc runtime database.

---

## 20. Future Work

- Mở rộng MVP từ hai lên ba AZ và NAT Gateway theo AZ.
- Karpenter cho workload có capacity biến động.
- Neo4j cho graph traversal quy mô lớn và PostgreSQL/pgvector thay ChromaDB.
- AMP, distributed tracing đầy đủ và Langfuse.
- Network/API Gateway Agent độc lập.
- Amazon Bedrock AgentCore Runtime/Gateway và A2A deployment.
- Canary/blue-green production, multi-region DR và production self-healing.
- Tự tạo PR sửa lỗi và mở rộng sang nền tảng CI/CD khác.

Future Work chỉ được thực hiện sau khi Definition of Done bắt buộc hoàn tất; không được trình bày như kết quả đã triển khai.

---

## 21. Tài liệu tham chiếu và tên bắt buộc giữ

Tài liệu local:

- `README.md` và `PRODUCTION_ARCHITECTURE_COMPLETE.md`: baseline EC2.
- `docs/PLANNING.md` và `docs/CONTEXT.md`: format và kế hoạch V1.
- `docs/REVIEW_CONTEXT_PLANNING_V2.md`: nhận xét dùng để chốt phạm vi V2.1.
- `agent_src/README.md` và `agent_src/RAG_SYSTEM_GUIDE.md`: AI/RAG hiện tại.
- `docs/AIops_CICD.md`: CI/CD hiện tại.

Tài liệu chính thức cần dùng khi triển khai:

- Amazon EKS best practices về subnet và data plane.
- Amazon RDS Multi-AZ, backup và monitoring.
- GitHub Actions OIDC với AWS và workflow run logs.
- Tài liệu POC/Future Work cho Karpenter, AMP, AgentCore, A2A và observability nâng cao khi các mục này được thực hiện.

Tên code/API hiện tại như `/webhook`, `process_alerts_task`, `PostgreSQLDown`, `GEMINI_MAX_REMOTE_CALLS` và các endpoint health phải giữ trong adapter migration cho đến khi có versioning/deprecation plan rõ ràng.
