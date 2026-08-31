# CONTEXT_V2.md — Bối cảnh, phạm vi và kiến trúc Multi-Agent AIOps V2

> **Phiên bản:** 2.1
> **Cập nhật:** 2026-08-31
> **Giai đoạn:** Chuyển đổi từ baseline EC2 sang MVP Fintech chạy trên Amazon EKS và Amazon RDS Multi-AZ, 08/2026–12/2026
> **Trạng thái tài liệu:** Phạm vi khóa luận đã chốt; luôn phân biệt rõ thành phần đã có, bắt buộc triển khai, POC và Future Work

## 1. Thông tin khóa luận

| Hạng mục | Nội dung |
|---|---|
| Tên tiếng Việt đề xuất | Xây dựng và đánh giá hệ thống Multi-Agent AIOps hỗ trợ phát hiện bất thường, chẩn đoán xuyên tầng ứng dụng–hạ tầng và tự phục hồi có kiểm soát cho hệ thống Fintech trên AWS |
| Tên tiếng Anh đề xuất | Design and Evaluation of a Multi-Agent AIOps System for Anomaly Detection, Cross-Layer Application-to-Infrastructure Diagnosis, and Controlled Remediation in AWS Fintech Systems |
| Đơn vị | Trường Đại học Công nghệ Thông tin, ĐHQG TP. Hồ Chí Minh |
| Cán bộ hướng dẫn | ThS. Trần Thị Dung |
| Sinh viên | Lê Hoàng Việt (23521778), Lê Quang Tiến (23521572) |
| Thời gian | 08/2026–12/2026 |

## 2. Phạm vi đã chốt

| Nhóm | Thành phần |
|---|---|
| **Đã có** | EC2 single-AZ, Docker Compose, Prometheus/Alertmanager, Redis/Celery, Gemini, ChromaDB RAG, Telegram, health check và release rollback |
| **Bắt buộc trong khóa luận** | VPC public/private subnet trên hai AZ, EKS, RDS PostgreSQL Multi-AZ, GitHub OIDC, deployment identity, metrics/logs/health check, event schema, redaction, durable Incident Core, Application/Infrastructure Agents, deterministic Aggregator, HITL, một remediation staging, Verification và benchmark |
| **POC nếu còn năng lực** | Karpenter, Neo4j, PostgreSQL/pgvector mới, traces nâng cao, AMP, Network/API Gateway Agent riêng, pattern mining nâng cao, Langfuse |
| **Future Work** | AgentCore Runtime, A2A deployment, multi-region DR, production self-healing, canary/blue-green nâng cao, tự tạo PR sửa lỗi và mở rộng compliance production |

### 2.1. Mục tiêu nghiên cứu

Mục tiêu nghiên cứu là chứng minh một luồng Multi-Agent xuyên từ dịch vụ nghiệp vụ xuống hạ tầng có thể:

- Gom các tín hiệu liên quan thành một incident.
- Xác định tầng phát sinh lỗi và phạm vi ảnh hưởng nghiệp vụ.
- Trả kết luận có evidence ID, mức không chắc chắn và khả năng tái lập.
- Chỉ cho phép hành động staging qua policy, phê duyệt và verification.
- Cải thiện kết quả so với baseline bằng benchmark có ground truth.

### 2.2. Mục tiêu triển khai

MVP phải chạy thật trên AWS ở mức khóa luận:

```text
GitHub Actions + OIDC
        |
        v
VPC hai Availability Zone
        |
EKS private worker nodes ---- RDS PostgreSQL Multi-AZ
        |
Mobile Banking + scenario services + AIOps services
        |
Metrics + logs + health checks
```

Ba AZ, NAT Gateway riêng theo từng AZ và các dịch vụ managed nâng cao được giữ trong thiết kế production tham khảo, không phải điều kiện đánh trượt khóa luận.

### 2.3. Nội dung không được tuyên bố

- Không tuyên bố một nền tảng Fintech production-ready hoặc đã được chứng nhận compliance.
- Không tuyên bố HA tuyệt đối cho toàn bộ control plane.
- Không tự động thay đổi production, IAM, Security Group, database schema hoặc secret.
- Không coi số lượng agent, việc gọi LLM hay dùng nhiều dịch vụ AWS là đóng góp tự thân.

## 3. Bài toán và câu hỏi nghiên cứu

Hệ thống Fintech dùng microservices, Kubernetes, database HA và CI/CD tạo ra lượng lớn logs, metrics, health events và workflow events. Monitoring dựa trên threshold có các hạn chế:

- Alert fatigue do một lỗi gốc tạo nhiều cảnh báo downstream.
- Điều tra lâu vì evidence nằm rải rác ở Prometheus, CloudWatch, Kubernetes, RDS và GitHub Actions.
- Không nhận ra tốt các mẫu lỗi mới chưa có rule.
- Thiếu liên kết giữa commit, workflow, image, deployment, service nghiệp vụ và lỗi hạ tầng.
- Log có thể chứa PII, PCI hoặc secret, trong khi mọi quyết định cần audit.

Câu hỏi nghiên cứu:

> Việc kết hợp Application Agents, Infrastructure Agents, dependency data và deterministic Aggregator có giúp giảm cảnh báo thừa, tăng chất lượng RCA và rút ngắn điều tra sự cố xuyên App–CI/CD–EKS–RDS, đồng thời đảm bảo redaction, least privilege, HITL và auditability hay không?

## 4. Baseline repository đã kiểm tra

### 4.1. Hạ tầng hiện tại

Terraform hiện tạo:

- Một VPC `10.10.0.0/16`.
- Một public subnet ở Availability Zone đầu tiên.
- Internet Gateway và public route table.
- Ba EC2 có public IP/EIP: `monitor-ai-01`, `bank-web-01` và `bank-core-01`.
- Security Group theo role; root volume mã hóa và IMDSv2 bắt buộc.

```text
Internet
  -> public subnet / single AZ
       -> monitor-ai-01
       -> bank-web-01
       -> bank-core-01
```

Chưa có private subnet, Load Balancer, EKS hoặc RDS.

### 4.2. Runtime hiện tại

| Role | Thành phần |
|---|---|
| Monitor/AI | Prometheus, Alertmanager, Grafana, Redis broker/cache, FastAPI AI Agent, Celery worker, log watcher |
| Core | Payment API, PostgreSQL container, PostgreSQL exporter |
| Web | React/Nginx frontend |

Staging và production chạy đồng thời trên cùng EC2 nhưng tách compose, state và cổng:

| Service | Staging | Production |
|---|---:|---:|
| AI Agent | 18000 | 8000 |
| Payment API | 18080 | 8080 |
| Frontend | 18081 | 3000 |

`/api/health` là liveness của Payment API; `/api/ready` kiểm tra cả PostgreSQL.

### 4.3. Alert/AI pipeline hiện tại

```text
Prometheus/Blackbox/service monitor/log watcher
  -> Alertmanager hoặc /webhook
  -> FastAPI
  -> Redis + Celery process_alerts_task
  -> deterministic diagnosis hoặc Gemini + ChromaDB RAG
  -> Telegram
  -> delayed Prometheus verification
```

Khả năng đã có:

- Webhook enqueue bất đồng bộ.
- Dedup ingress và AI cooldown.
- Deterministic runbook cho các alert quen thuộc.
- ChromaDB collections `standard_runbooks` và `incident_memory`.
- Admin feedback và runbook draft/revision/approval.
- GitHub webhook HMAC cho auto-discovery thay đổi CI/toolchain.
- Quota Gemini bảo thủ và degraded health khi Redis lỗi.

Giới hạn quan trọng:

- `process_alerts_task` xử lý alert riêng; chưa có specialist agents hoặc Aggregator.
- Incident context chủ yếu ở Redis có TTL; chưa có durable incident state machine.
- `propose_remediation()` chỉ tạo proposal; chưa phải executor cho EKS, RDS hoặc GitHub.
- GitHub webhook chưa tải và phân tích workflow logs/artifacts như CI/CD Agent mục tiêu.
- Chưa có dependency graph xuyên nghiệp vụ–hạ tầng hoặc redaction boundary đầy đủ.

Kết quả kiểm thử baseline ngày 2026-08-29:

```text
PYTHONPATH=agent_src venv/bin/pytest -q agent_src/tests
59 passed, 8 warnings
```

Warnings gồm API deprecated trong dependency test và `datetime.utcnow()` tại log watcher; không làm test thất bại nhưng cần backlog.

### 4.4. CI/CD hiện tại

- CI lint/test/build ba images và validate Docker Compose.
- Staging deploy theo changed role.
- Production deploy theo tag `v*` hoặc manual dispatch.
- Image lưu ở GHCR.
- Deploy qua SSH tới EC2, health check và rollback bằng `automation/app-release-deploy.sh`.

Chưa có GitHub OIDC với AWS, EKS deployment hoặc canonical deployment identity.

## 5. Các dịch vụ Fintech mẫu

Mobile Banking là luồng end-to-end bắt buộc. Payment API hiện tại được tái sử dụng và mở rộng thành Transaction Service của luồng này.

| Dịch vụ | Phạm vi | Vai trò và scenario |
|---|---|---|
| **Mobile Banking** | **Bắt buộc, triển khai đầy đủ** | Đăng nhập, chuyển tiền; migration lỗi, API chậm hoặc dependency không sẵn sàng |
| Buy Now Pay Later | Scenario pack/service nhỏ | Tạo khoản vay lỗi, thanh toán timeout |
| Investment App | Scenario pack/service nhỏ | Market data chậm, đặt lệnh thất bại |
| AI Credit Scoring | Scenario pack/service nhỏ | Thiếu feature, model endpoint chậm |

Ba dịch vụ mở rộng không cần trở thành sản phẩm hoàn chỉnh hoặc có agent runtime riêng. Chúng phải tái sử dụng Incident Core, contracts, dependency model, Aggregator và evaluation harness chung.

Dependency bắt buộc phải truy được:

```text
Mobile Banking
  -> Transaction Service
      -> Kubernetes Deployment/Pod
          -> RDS PostgreSQL
      -> Load Balancer / VPC path
      -> GitHub Workflow / Image / Deployment
```

## 6. Kiến trúc MVP xuyên App–Infrastructure

```text
GitHub Actions/webhooks              EKS/RDS/application signals
             |                                  |
             +--------- Ingestion Gateway ------+
                              |
               authentication + schema validation
                              |
             redaction before operational persistence
                              |
              Event Normalizer + Incident Core
                              |
                    Shared Orchestrator
             +----------------+----------------+
             |                                 |
       Application layer                Infrastructure layer
 Mobile Banking Agent                  Kubernetes Agent
 BNPL/Investment/Credit context        RDS Agent
                                       GitHub Actions Agent
                                       Security Agent
                                       Network/API context
             \                                 /
              +-------- Dependency model ------+
                              |
                  deterministic Aggregator
                RCA + impact + uncertainty
                              |
                   RAG/LLM explanation
                              |
                 Policy + Human approval
                              |
                  typed staging action
                              |
                independent Verification
                              |
                  audit + reviewed memory
```

### 6.1. AWS bắt buộc

- VPC có public và private subnets trên **hai Availability Zone**.
- EKS chạy Mobile Banking workload trên private worker nodes và trải ít nhất hai AZ.
- RDS PostgreSQL Multi-AZ lưu dữ liệu ứng dụng.
- GitHub Actions dùng OIDC và role ngắn hạn để triển khai.
- CI/CD ghi commit SHA, workflow run, image digest, deployment và migration ID.
- Metrics, logs và health check thu thập được từ app, EKS, RDS và workflow.
- Network access tuân thủ least privilege; không expose monitoring hoặc AI API công khai như baseline.

### 6.2. Production reference và POC

- Ba AZ và NAT Gateway theo AZ là production reference.
- Managed Node Group là lựa chọn mặc định của MVP; Karpenter là POC.
- Prometheus/CloudWatch là đủ cho MVP; AMP và traces nâng cao là POC.
- Dependency model có thể dùng PostgreSQL/JSON/YAML được version hóa; Neo4j là POC.
- ChromaDB hiện tại có thể tiếp tục cho retrieval; PostgreSQL/pgvector mới là POC.
- LangGraph chạy container trên EKS là mặc định; AgentCore Runtime và A2A deployment là Future Work.
- Kagent và Langfuse là POC, không phải điều kiện nghiệm thu.

## 7. Application Agents và Infrastructure Agents

### 7.1. Application layer

Application Agent cung cấp:

- Business capability và service criticality.
- Dependency từ chức năng nghiệp vụ tới service kỹ thuật.
- Business symptom và impact.
- Runbook/expected behavior theo nghiệp vụ.

Mobile Banking Agent là bắt buộc. BNPL, Investment và Credit Scoring có thể dùng một generic Application Agent nạp scenario/dependency pack thay vì bốn runtime độc lập.

### 7.2. Infrastructure layer

| Agent | Phạm vi bắt buộc | Quyền |
|---|---|---|
| Kubernetes Agent | Pod, Deployment, event, resource, readiness | Kubernetes read-only |
| RDS Agent | Connection, migration, lock, slow query, database status | RDS/monitoring read-only |
| GitHub Actions Agent | Workflow, job, log, artifact, deployment | GitHub read-only; mutation chỉ qua policy |
| Security Agent | Redaction, sensitive-data finding, policy veto | Read-only + veto |
| Network/API context | Load Balancer, endpoint, DNS/network probe | Tool read-only trong MVP; agent riêng là POC |

### 7.3. Shared contracts

Mỗi agent response phải có:

```text
schema_version, incident_id, agent_run_id
status: COMPLETE | PARTIAL | FAILED
started_at, completed_at
evidence[], hypotheses[], affected_capabilities[]
tool_calls[], errors[]
data_classification, redaction_status
```

Orchestrator và Aggregator dùng chung cho cả hai lớp. Agent không tự kết luận RCA cuối cùng và không tự thực hiện mutation.

## 8. Incident Core, Aggregator và state

Incident Core bắt buộc:

- Nhận dữ liệu từ Alertmanager và GitHub Actions.
- Chuẩn hóa về event schema chung.
- Redact secret, PII và PCI trước operational persistence và trước LLM.
- Lưu incident, evidence, agent run, approval, verification và audit bền vững.
- Gom event trùng hoặc liên quan vào cùng incident.
- Xử lý timeout, retry giới hạn, dữ liệu thiếu và agent failure.

Luồng:

```text
Signal
  -> authenticate/validate
  -> redact
  -> normalize
  -> deduplicate/correlate
  -> incident
  -> Application + Infrastructure investigation
  -> deterministic Aggregator
  -> RAG/LLM explanation
  -> policy/approval
  -> staging action
  -> independent verification
  -> RESOLVED / VERIFICATION_FAILED / ESCALATED
```

Event trùng chuyển `DUPLICATE` và liên kết về canonical event/incident; nó không tạo incident mới. Approval phải hỗ trợ `REJECTED` và `EXPIRED`. Verification không đạt chuyển `VERIFICATION_FAILED`, không được chuyển `RESOLVED`.

Aggregator:

- Gom và loại evidence trùng.
- Phát hiện evidence mâu thuẫn hoặc quá cũ.
- Xếp hạng nguyên nhân bằng công thức deterministic đã đóng băng.
- Gắn từng claim với evidence ID.
- Nêu uncertainty và affected business capabilities.
- Tạo remediation plan theo schema cố định.

LLM chỉ viết phần giải thích dễ đọc; không sửa score, evidence hoặc policy decision.

## 9. Canonical identity xuyên CI/CD–App–Infrastructure

Mỗi deployment record phải nối được:

```text
business_capability -> application_service
-> repository -> commit_sha -> pull_request -> workflow_run/job
-> artifact/image_digest -> deployment_id
-> EKS cluster/namespace/workload/revision
-> database_migration_id
```

Thiếu chuỗi này thì hệ thống chỉ chẩn đoán từng tầng riêng lẻ, chưa đạt mục tiêu xuyên App–Infrastructure.

## 10. Security, HITL và audit

- Webhook phải có signature/auth, replay protection và schema validation.
- Operational incident/evidence/knowledge stores chỉ nhận dữ liệu đã redact.
- Nếu cần giữ raw log cho điều tra, dùng kho tách biệt, mã hóa, quyền hạn chế và retention riêng; raw log không đi vào LLM/knowledge.
- GitHub Actions dùng OIDC với trust conditions; không giữ AWS access key dài hạn.
- Tool có input/output schema, target allowlist, timeout, rate limit và audit.
- LLM không có generic shell, SSH, `kubectl`, AWS hoặc SQL mutation.
- Khóa luận chỉ chạy remediation trên staging.
- Rerun transient job hoặc restart/rollback deployment staging phải qua policy và approval theo mức rủi ro.
- Production mutation, IAM/SG change, database schema change và secret rotation bị vô hiệu trong MVP.
- Approval có plan hash, expiry, target, environment và approver identity.
- Chỉ Verification Agent/deterministic verifier được tạo `RESOLVED`.

## 11. Kịch bản và đánh giá

### 11.1. Kịch bản trung tâm bắt buộc

```text
Database migration lỗi
  -> GitHub deployment không hoàn tất
  -> Transaction Service không sẵn sàng trên EKS
  -> Mobile Banking không chuyển tiền được
```

Hệ thống phải xác định migration là root cause; API, pod readiness và giao dịch lỗi là ảnh hưởng lan truyền. Báo cáo phải có technical impact lẫn business impact.

### 11.2. Kịch bản bắt buộc bổ sung

- Pod CrashLoopBackOff hoặc OOMKilled.
- RDS failover.
- GitHub workflow failure hoặc webhook bị mất.
- Secret/PII xuất hiện trong log.
- Một agent hoặc nguồn dữ liệu bị gián đoạn.
- Verification thất bại sau action.

### 11.3. Scenario mở rộng

- BNPL: tạo khoản vay lỗi hoặc payment timeout.
- Investment: market data chậm hoặc order failure.
- AI Credit Scoring: thiếu feature hoặc model endpoint chậm.

Các scenario này chứng minh khả năng tái sử dụng nền tảng, không bắt buộc xây thêm full-stack production.

### 11.4. Hai nhóm đánh giá

| Nhóm | Câu hỏi | Ví dụ metric |
|---|---|---|
| **AWS Platform** | Workload mục tiêu có được triển khai và chịu lỗi đúng thiết kế không? | deploy success, pod/AZ continuity, RDS failover/recovery, OIDC success |
| **AIOps Quality** | Multi-Agent có điều tra tốt hơn baseline không? | alert compression, RCA top-1/top-3, impact accuracy, evidence coverage, MTTD/MTTR, safety |

Tách hai nhóm để không quy toàn bộ cải thiện AIOps cho việc thay EC2 bằng EKS/RDS.

Phương pháp so sánh:

| Mã | Phương pháp |
|---|---|
| B0 | Baseline EC2: alert riêng lẻ + runbook/Gemini + Telegram |
| B1 | Rule correlation + dependency |
| P | Application + Infrastructure Agents + deterministic Aggregator |

Trước benchmark chính chạy ba pilot runs để sửa harness, sau đó đóng băng code/config/weight/prompt. Benchmark chính chạy **tối thiểu 10 lần độc lập cho mỗi cặp scenario–method**, dùng cùng fault profile và ground truth; báo cáo median, IQR, min/max và failure count.

## 12. Tiêu chí hoàn thành khóa luận

- Ứng dụng Mobile Banking mẫu chạy được trên EKS.
- EKS workload trải ít nhất hai AZ.
- Database ứng dụng chạy trên RDS PostgreSQL Multi-AZ.
- Có ít nhất một pipeline GitHub Actions dùng OIDC.
- Có deployment identity nối commit–workflow–image–EKS–migration.
- Một sự cố migration được liên kết từ GitHub tới Kubernetes, RDS và Mobile Banking.
- Một lỗi hạ tầng được liên kết tới capability nghiệp vụ bị ảnh hưởng.
- Ít nhất một scenario BNPL, Investment hoặc Credit Scoring tái sử dụng nền tảng chung.
- Các agent trả evidence có cấu trúc và biểu diễn partial failure.
- Aggregator xác định root cause/impact bằng công thức đã đóng băng.
- Dữ liệu nhạy cảm không xuất hiện trong prompt, notification hoặc knowledge store.
- Có ít nhất một remediation staging chạy qua policy, approval và verification.
- Verification thất bại không được ghi nhận là resolved.
- Có benchmark B0, B1 và P với ground truth và số lần chạy đã quy định.
- Có dữ liệu thô đã sanitized, script tính metric, biểu đồ và mô tả giới hạn.

## 13. Khoảng cách triển khai

| Nhóm | Hiện trạng | Kết quả bắt buộc |
|---|---|---|
| AWS | EC2 single-AZ | VPC hai AZ, EKS private workload, RDS Multi-AZ |
| Fintech app | Frontend + Payment API | Mobile Banking end-to-end + scenario pack tái sử dụng |
| CI/CD | SSH deploy theo role | OIDC + immutable deployment identity |
| Observability | Metrics/alerts là chính | metrics, logs, health checks + GitHub events |
| Incident | Redis TTL, alert riêng | durable event/incident/evidence/audit và correlation |
| Multi-Agent | Chưa có specialist/Aggregator | Application layer + bốn Infrastructure Agents tối thiểu |
| Dependency | Label/runbook rời rạc | App–service–Kubernetes–RDS–network–deployment links |
| Security | HMAC GitHub và SG | redaction trước persistence/LLM, policy và HITL |
| Remediation | Proposal + EC2 release rollback | ít nhất một typed staging action + verification |
| Evaluation | Unit tests, chưa benchmark V2 | ground truth, pilot, repeated benchmark và ablation phù hợp |

## 14. Nguyên tắc phát triển

- Giữ baseline hoạt động đến khi EKS staging đạt acceptance test.
- Không hạ EKS/RDS/OIDC xuống “nếu còn thời gian”.
- Giảm độ sâu POC/Future Work trước khi cắt luồng Mobile Banking xuyên tầng.
- Chốt schema và security boundary trước khi thêm agent.
- Deterministic preprocessing, scoring và policy đứng trước LLM.
- Mọi claim có evidence; không đủ evidence thì `INCONCLUSIVE/ESCALATED`.
- Mọi mutation có typed action, policy, idempotency, audit và verification.
- Không dùng workload database làm control-plane database.
- Không ghi trước số liệu thực nghiệm.
- Không commit secret, `.env`, Terraform state, key hoặc runtime data.

## 15. Decision gates

| Quyết định | Mặc định cho khóa luận | Phân loại |
|---|---|---|
| AWS topology | VPC hai AZ, EKS Managed Node Group, RDS Multi-AZ | Bắt buộc |
| Agent orchestration | LangGraph container trên EKS | Bắt buộc |
| Foundation model | Gemini baseline; Amazon Bedrock model qua cấu hình nếu tích hợp đạt | Bedrock integration là POC, LLM vendor không quyết định đóng góp |
| Dependency storage | PostgreSQL/JSON/YAML version hóa | Bắt buộc |
| Graph database | Neo4j | POC |
| Vector store | Giữ ChromaDB adapter; pgvector mới | pgvector là POC |
| Observability | Prometheus/CloudWatch metrics, logs, health checks | Bắt buộc |
| Advanced observability | AMP, distributed traces, Langfuse | POC |
| Node autoscaling | Managed Node Group | Bắt buộc; Karpenter là POC |
| Agent deployment protocol | Internal typed contracts | Bắt buộc; AgentCore/A2A là Future Work |
| Production mutation | Disabled | Future Work sau security review |

## 16. Tài liệu tham chiếu

Tài liệu local:

| Đường dẫn | Vai trò |
|---|---|
| `README.md` | Baseline runtime, alert và release |
| `PRODUCTION_ARCHITECTURE_COMPLETE.md` | Kiến trúc EC2 hiện tại |
| `docs/PLANNING.md`, `docs/CONTEXT.md` | Format V1 |
| `docs/PLANNING_V2.md` | Kế hoạch triển khai chi tiết V2 |
| `docs/REVIEW_CONTEXT_PLANNING_V2.md` | Nhận xét dùng để chốt phạm vi V2.1 |
| `agent_src/README.md`, `agent_src/RAG_SYSTEM_GUIDE.md` | AI Agent và RAG hiện tại |
| `docs/AIops_CICD.md` | CI/CD hiện tại |

Tài liệu chính thức cần kiểm tra khi triển khai:

- [Amazon EKS VPC and subnet considerations](https://docs.aws.amazon.com/eks/latest/best-practices/subnets.html)
- [Amazon RDS Multi-AZ deployments](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html)
- [GitHub Actions OIDC with AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
- [GitHub workflow run logs](https://docs.github.com/en/actions/how-tos/monitor-workflows/use-workflow-run-logs)
