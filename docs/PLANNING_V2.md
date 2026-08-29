# PLANNING_V2.md — Kế hoạch nâng cấp hệ thống Multi-Agent AIOps cho Fintech

> **Phiên bản:** 2.0
> **Cập nhật:** 2026-08-29
> **Thời gian dự kiến:** 08/2026–12/2026
> **Baseline đã kiểm tra:** AWS EC2 single-AZ, Docker Compose, Prometheus/Alertmanager, FastAPI, Redis/Celery, Gemini và ChromaDB.
> **Kiến trúc đích:** VPC ba Availability Zone, Amazon EKS, Amazon RDS Multi-AZ, GitHub Actions, observability ba trụ cột và Multi-Agent AIOps có kiểm soát.
> **Mục tiêu:** xây dựng và đánh giá một vòng xử lý sự cố xuyên suốt từ CI/CD đến production theo pipeline **Collect -> Redact -> Normalize -> Detect/Correlate -> Multi-Agent Investigation -> Evidence Aggregation -> Human Approval -> Controlled Action -> Verification -> Auditable Learning**.

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
VPC 3 AZ + EKS + RDS Multi-AZ + GitHub OIDC
                |
                v
Metrics + logs + traces + CI/CD telemetry
                |
                v
Redaction + normalization + pattern mining + incident core
                |
                v
LangGraph Orchestrator
  -> Kubernetes | RDS | GitHub Actions | Security/Compliance Agents
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

> **Signal -> Pattern -> Event -> Incident -> Evidence -> Diagnosis -> Decision -> Action -> Verification -> Learning**

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
| CI/CD được liên kết với production ra sao? | Mục 7 |
| Dữ liệu Fintech được bảo vệ thế nào? | Mục 8, 12 |
| Làm sao chứng minh giải pháp tốt hơn baseline? | Mục 13, 14 |
| Xây theo thứ tự nào? | Mục 15 |

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

- Amazon EKS, RDS Multi-AZ, private workload subnets hoặc topology ba AZ.
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
       |                   |                   |
 Kubernetes Agent       RDS Agent      GitHub Actions Agent
       \                   |                   /
        +------------- Security Agent --------+
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

> **Xây dựng và đánh giá hệ thống Multi-Agent AIOps hỗ trợ phát hiện bất thường, chẩn đoán xuyên miền CI/CD–production và tự phục hồi có kiểm soát cho hạ tầng Fintech trên AWS.**

Tên tiếng Anh đề xuất:

> **Design and Evaluation of a Multi-Agent AIOps System for Anomaly Detection, Cross-Domain CI/CD-to-Production Diagnosis, and Controlled Remediation in AWS Fintech Infrastructure.**

### 1.4. Câu hỏi nghiên cứu chính

> Việc kết hợp học trạng thái bình thường, pattern mining, dependency knowledge và các agent chuyên trách có giúp giảm cảnh báo thừa, rút ngắn điều tra và tăng độ chính xác RCA cho sự cố xuyên suốt GitHub Actions–EKS–RDS, trong khi vẫn duy trì least privilege, Human-in-the-Loop và auditability hay không?

---

## 2. Đóng góp kỹ thuật và giới hạn tuyên bố

### 2.1. Đóng góp chính

Đóng góp không nằm ở số lượng agent hoặc việc gọi LLM. Đóng góp cần được chứng minh là một pipeline có thể tái lập:

1. Chuẩn hóa signals từ CI/CD và production thành event schema chung.
2. Redact dữ liệu nhạy cảm trước khi dữ liệu đi vào LLM, vector store hoặc prompt trace.
3. Dùng pattern mining và time window để phát hiện mẫu mới thay vì chỉ phụ thuộc threshold.
4. Liên kết commit, workflow, image digest, deployment, Kubernetes workload và database migration.
5. Điều phối các agent theo domain, mỗi agent chỉ dùng tool được cấp.
6. Aggregator hợp nhất evidence và xếp hạng RCA theo công thức deterministic.
7. Thực thi hành động có kiểu qua policy, approval, idempotency và verification.
8. Chỉ đưa incident/pattern vào knowledge sau khi đã được xác minh hoặc duyệt.

Mô hình điểm dự kiến:

```text
root_cause_score =
    w_time        * temporal_score
  + w_dependency  * dependency_score
  + w_metric      * metric_score
  + w_log         * log_pattern_score
  + w_trace       * trace_score
  + w_change      * recent_change_score
  + w_cross_domain* ci_prod_link_score
  + w_security    * security_signal_score
  - w_conflict    * contradiction_score
  - w_stale       * stale_evidence_penalty
```

Các trọng số phải được version hóa và đóng băng trước benchmark. LLM không được tự đặt điểm cuối cùng.

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
| Infrastructure | `terraform/` | VPC, một public subnet, SG, ba EC2, EIP | VPC ba AZ, public/private subnet, EKS, RDS, endpoints, KMS |
| Host/runtime | `ansible/`, `release/` | Docker và Docker Compose theo role | Helm/Kustomize/GitOps; Ansible giữ cho legacy và fault injection |
| Application/AIOps | `agent_src/`, `demo-web/` | FastAPI, Celery, RAG, demo banking | containerized microservices, LangGraph agents, incident/evidence core |
| Delivery | `.github/workflows/`, `automation/` | CI, GHCR, SSH deploy, rollback | OIDC, registry, scan, deploy EKS, canary/blue-green, telemetry |

### 3.2. Bằng chứng từ code

| Thành phần | Bằng chứng | Đánh giá |
|---|---|---|
| Webhook | `agent_src/core/main.py` | Có Alertmanager, GitHub và Telegram endpoints |
| Async processing | `agent_src/core/tasks.py` | Có Celery task; chưa có specialist fan-out/chord |
| RAG | `agent_src/core/rag_engine.py` | Có ChromaDB; chưa có pgvector |
| Runbook governance | `agent_src/core/runbook_registry.py` | Có revision, draft, approval và audit JSONL |
| Diagnostics | `agent_src/tools/diag_tools.py` | Tool thử nghiệm; chưa có MCP contract/least-privilege gateway đầy đủ |
| Release | `automation/app-release-deploy.sh` | Có role gate, health check và rollback cho EC2 Compose |
| CI/CD | `.github/workflows/*.yml` | Có build/deploy; chưa dùng AWS OIDC và chưa deploy EKS |

### 3.3. Khoảng cách và chiến lược chuyển đổi

| Nhóm | Baseline | V2 bắt buộc | Cách chuyển |
|---|---|---|---|
| Compute | Ba EC2 cố định | EKS worker đa AZ | Containerize giữ API contract; deploy song song sandbox |
| Database | PostgreSQL container | RDS PostgreSQL Multi-AZ | Schema migration, backup/restore rehearsal, endpoint cutover |
| Queue/state | Redis/Celery và context TTL | Durable incident store + LangGraph checkpoints | Giữ Celery ingestion ở phase đầu; thêm repository có cấu trúc |
| Monitoring | Prometheus threshold | Metrics, logs, traces, CI/CD telemetry | ADOT/OTel + CloudWatch/AMP |
| AI | Một workflow theo alert | Orchestrator + bốn domain agents + Aggregator | Tách tools và contracts trước, rồi graph orchestration |
| CI/CD | SSH deploy tới EC2 | OIDC và deploy EKS | Chạy dual path staging, bỏ long-lived AWS credentials |
| Knowledge | ChromaDB local | Neo4j + Aurora PostgreSQL/pgvector | Backfill có kiểm duyệt; ChromaDB giữ cho local dev tạm thời |
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

## 4. Kiến trúc hạ tầng đích

### 4.1. VPC ba Availability Zone

```text
Internet
   |
CloudFront/WAF hoặc public ALB
   |
Public subnets:  AZ-a | AZ-b | AZ-c
NAT Gateway:     AZ-a | AZ-b | AZ-c    (production reference)
   |
Private app subnets: EKS nodes/pods
Private data subnets: RDS/knowledge stores
   |
VPC endpoints: S3, ECR API/DKR, STS, CloudWatch Logs,
               X-Ray, Secrets Manager và các endpoint cần thiết
```

Yêu cầu:

- Public subnet không chạy application workload.
- EKS worker, RDS và knowledge stores ở private subnet.
- Security Group chỉ cho phép luồng cần thiết; không mở Prometheus, Alertmanager hoặc AI API ra `0.0.0.0/0`.
- EKS API endpoint ưu tiên private; nếu cần public cho POC phải giới hạn CIDR và ghi rõ.
- Production reference dùng NAT Gateway theo AZ để tránh phụ thuộc chéo AZ.
- POC tiết kiệm chi phí có thể dùng một NAT Gateway, nhưng phải ghi đó là giới hạn HA và không dùng để tuyên bố zone independence.

### 4.2. Amazon EKS

Thiết kế compute:

| Nhóm | Mục đích | Cách cấp phát |
|---|---|---|
| System nodes | CoreDNS, controllers, OTel, policy components | Managed Node Group ổn định, trải trên ít nhất hai AZ |
| Application nodes | Frontend, Payment API, agent services | Karpenter NodePool hoặc Managed Node Group |
| Sensitive jobs | Migration/security jobs | NodePool riêng với taint/toleration nếu cần |

Yêu cầu workload:

- Tối thiểu hai replicas cho service quan trọng trong staging HA test.
- `topologySpreadConstraints` và pod anti-affinity để phân bố pod giữa AZ/node.
- PodDisruptionBudget, readiness/liveness/startup probes và graceful shutdown.
- Resource request/limit, HPA; Karpenter chỉ scale node cho pending workload.
- Karpenter controller không chạy trên node do chính Karpenter quản lý.
- Production pin AMI và version add-on đã kiểm thử.
- RBAC, Kubernetes service account và IAM role theo least privilege.
- NetworkPolicy tách namespace `app`, `observability`, `aiops` và `security`.

Không hard-code một instance type duy nhất cho production. `t3.medium` và `m5.large` là điểm bắt đầu từ đặc tả, còn NodePool phải cho phép một tập instance tương thích sau benchmark capacity/cost.

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
  -> smoke/DAST
  -> approval/environment protection
  -> canary hoặc blue-green production
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

### 4.5. Observability ba trụ cột

| Trụ cột | Nguồn | Collector/store mục tiêu | Khóa tương quan bắt buộc |
|---|---|---|---|
| Metrics | EKS control/data plane, app, RDS, GitHub workflows | ADOT/Prometheus -> AMP hoặc CloudWatch | service, namespace, cluster, workflow_run_id |
| Logs | Pod/app, EKS audit/control plane, RDS, CloudTrail, GitHub run logs | OTel/Fluent Bit -> CloudWatch Logs | trace_id, deployment_id, commit_sha, run_id |
| Traces | Microservice request và agent/tool spans | OpenTelemetry -> X-Ray/CloudWatch | trace_id, service.version, image.digest |

GitHub Actions ingestion có hai đường:

1. Webhook `workflow_run`/`workflow_job` để phát hiện gần thời gian thực.
2. Polling reconciliation để bù webhook bị mất và tải logs/artifacts qua GitHub API.

OpenTelemetry spans/metrics từ workflow là bổ sung. Không phụ thuộc vào một “GitHub receiver” duy nhất nếu chưa được POC xác nhận; webhook/API vẫn là nguồn kiểm chứng.

### 4.6. Knowledge layer

**Knowledge Graph:**

```text
Repository -> Commit -> WorkflowRun -> Job
     |          |            |          |
     |          v            v          v
     +------> Image ----> Deployment -> KubernetesWorkload
                                      -> Service -> RDSDatabase
```

Neo4j lưu topology và quan hệ ảnh hưởng. Mỗi edge có `source`, `environment`, `valid_from`, `valid_to` và `confidence`.

**Vector knowledge:**

- Target: Aurora PostgreSQL-compatible hoặc PostgreSQL có `pgvector`.
- Local development có thể tiếp tục ChromaDB trong giai đoạn chuyển đổi.
- Chỉ lưu runbook đã duyệt, incident đã verified và error pattern đã redact.
- Mỗi chunk có tenant/environment, sensitivity, source, version và reviewer.

### 4.7. Agent runtime và observability

- LangGraph là state machine và điều phối luồng.
- Amazon Bedrock là nền tảng foundation model mục tiêu. `Claude 3.5 Sonnet` trong đặc tả ban đầu được xem là model ứng viên, không hard-code; model ID thực tế phải có trong region, vượt evaluation set và được ghi vào audit cho từng run.
- AgentCore Runtime/Gateway là mục tiêu triển khai cho A2A/MCP sau POC về region, network, cost và auth.
- MCP chuẩn hóa tool discovery/invocation; A2A dùng cho giao tiếp agent có contract.
- Celery hiện tại có thể giữ vai trò ingestion/background/reconciliation trong giai đoạn đầu; không phải nguồn trạng thái incident cuối cùng.
- Agent trace được gửi đến CloudWatch/AgentCore observability; Langfuse chỉ nhận dữ liệu đã redact nếu được dùng.
- Audit record không được phụ thuộc duy nhất vào Langfuse hoặc LLM trace.
- Kubernetes Agent được triển khai custom bằng LangGraph trong MVP để kiểm soát contract và quyền. Kagent chỉ là adapter/POC tùy chọn; nếu dùng vẫn phải qua cùng MCP policy, RBAC và evidence schema.

### 4.8. Presentation layer

- Web Dashboard hiển thị incident, timeline, evidence, agent status, approval và verification; không xây lại dashboard metrics của Grafana.
- Giữ Telegram hiện tại trong migration; Slack bot là target HITL nếu có workspace phù hợp.
- GitHub Checks hiển thị bản tóm tắt đã redact trên commit/PR.
- Jira ticket chỉ tự tạo ở dạng draft/incident record; mutation workflow phải theo policy.
- Email và Teams là integration mở rộng.
- Không hiển thị raw PII/PCI/secret trên bất kỳ kênh notification nào.

---

## 5. Kiến trúc Multi-Agent

### 5.1. Agent và quyền

| Agent | Trách nhiệm | Tool read-only chính | Mutation |
|---|---|---|---|
| Orchestrator | Phân loại, lập investigation plan, route, loop limit | incident/topology lookup | Không |
| Kubernetes Agent | Pod/node/deployment/event/RBAC diagnosis | Kubernetes API, PromQL, logs, probes | Chỉ tạo proposal |
| RDS Agent | Slow query, connection, deadlock, failover, migration | RDS APIs, insights, sanitized logs | Chỉ tạo proposal |
| GitHub Actions Agent | Workflow/job/log/artifact/deploy diagnosis | GitHub API, Checks, workflow metadata | Chỉ tạo proposal |
| Security/Compliance Agent | Redaction, secret/PII detection, IAM/audit review | policy, CloudTrail, redaction scanners | Có quyền veto; không tự sửa |
| Aggregator | Merge evidence, score RCA/impact | evidence/topology store | Không |
| Verification Agent | Kiểm tra post-condition độc lập | metrics, logs, traces, status APIs | Chỉ cập nhật kết quả verification |

### 5.2. State dùng chung

```python
class AgentState(TypedDict):
    schema_version: str
    incident_id: str
    incident_type: Literal["infrastructure", "ci_cd", "security", "mixed"]
    query: str
    normalized_events: list[dict]
    entities: list[dict]
    hypotheses: list[dict]
    evidence: list[dict]
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
2. Entity đã resolve: cluster, namespace, workflow, RDS instance.
3. Dependency/change graph.
4. Data classification.
5. Evidence gap.

Ví dụ deployment failure do migration:

```text
GitHub workflow fails
  -> GitHub Agent: migration step + commit + error signature
  -> RDS Agent: lock/deadlock/schema state
  -> Kubernetes Agent: rollout and pod readiness
  -> Security Agent: redact SQL values/secrets
  -> Aggregator: migration failure is root cause,
                 rollout/pod errors are impact
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

### 6.1. Pipeline

```text
Raw telemetry
  -> security redaction
  -> parse + canonicalize
  -> bỏ timestamp/request ID/giá trị biến động
  -> Drain/Drain3 hoặc thuật toán LogPAI được chọn
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

### 6.3. Training, shadow và active

1. **Training:** học baseline từ khoảng thời gian đã xác nhận không có incident lớn.
2. **Shadow:** tính anomaly nhưng không gửi action/alert tới người vận hành.
3. **Active:** chỉ tạo signal sau khi đạt threshold trên validation set.

Không tự coi toàn bộ log trong “training window” là bình thường. Cần loại maintenance, incident và dữ liệu bị nhiễm.

### 6.4. Metric anomaly

Ít nhất một detector time-window được triển khai, ví dụ Isolation Forest hoặc robust seasonal baseline. Input:

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

Đây là cầu nối giữa GitHub Actions Agent, Kubernetes Agent và RDS Agent.

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
- Mặc định tối đa một automatic attempt trong sandbox; production yêu cầu approval.
- Dùng idempotency key theo workflow run/job/attempt.
- Sau rerun phải verification cả CI result và deployment state.

---

## 8. Tool calling, guardrails và HITL

### 8.1. MCP tool contract

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
| Cao | Production rollout/rollback, DB failover/failback, secret rotation | Human approval bắt buộc, two-person rule khi áp dụng |
| Cấm tự động | IAM/SG broadening, destructive DB migration, xóa cluster/DB | Từ chối hoặc quy trình break-glass ngoài agent |

Scale deployment không được mặc định coi là “thấp” trong production vì có thể tăng chi phí hoặc khuếch đại lỗi.

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

---

## 9. Knowledge và self-evolution an toàn

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
RECEIVED -> REDACTING -> NORMALIZING -> CORRELATING -> OPEN
         -> INVESTIGATING -> AGGREGATING -> DIAGNOSED
         -> PLANNED -> AWAITING_APPROVAL -> APPROVED/REJECTED/EXPIRED
         -> EXECUTING -> VERIFYING -> RESOLVED
         -> FAILED -> ESCALATED

RESOLVED -> REOPENED
```

Chỉ Verification Agent hoặc deterministic verification service được tạo `RESOLVED`.

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

## 11. Kịch bản trung tâm

### 11.1. CD-07: deployment lỗi do database migration

Tạo một migration staging có lỗi đã biết:

```text
GitHub Actions migration job fails
        |
        +-> workflow/deployment alerts
        +-> Kubernetes rollout pending hoặc pod readiness fail
        +-> RDS log/lock/schema evidence
```

Hệ thống phải:

1. Nhận `workflow_job`/`workflow_run` event và bù bằng polling nếu cần.
2. Redact secret/SQL values trước persistence và LLM.
3. Chuẩn hóa event với commit, run, image, deployment, cluster và migration ID.
4. Gom các signals vào một mixed incident.
5. GitHub Agent xác định step và error pattern.
6. RDS Agent kiểm tra schema/migration/lock bằng read-only tool.
7. Kubernetes Agent xác định rollout/pod là downstream impact.
8. Security Agent xác nhận redaction và không có secret leakage.
9. Aggregator xếp migration failure đứng đầu, kèm evidence IDs.
10. Đề xuất action an toàn: dừng rollout/rerun sau fix hoặc rollback application; không tự rollback destructive migration.
11. Policy yêu cầu approval cho mutation.
12. Verification kiểm tra workflow, deployment, pod readiness, API và schema version.
13. Lưu timeline/audit và chỉ học incident sau review.

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
- Readiness của Payment API.
- Agent có phân biệt failover với database down kéo dài không.

Không kích hoạt failover production từ agent trong phạm vi khóa luận.

### 11.4. SEC-01: secret/PII leakage trong CI log

Hệ thống phải:

- Phát hiện và redact trước LLM/vector store.
- Không đưa giá trị secret vào Telegram/Slack/Jira/GitHub Checks.
- Tạo security incident và khuyến nghị rotation.
- Không tự rotate production secret nếu chưa có approval và runbook.

### 11.5. INT-01: GitHub API/webhook outage

- Webhook gap được phát hiện.
- Polling reconciliation bù event.
- Rate limit được tôn trọng.
- Incident context không bị nhân đôi.

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

### 13.1. Nhóm scenario

| Nhóm | Scenario bắt buộc | Mục tiêu |
|---|---|---|
| Resilience | Pod termination, node/AZ simulation, RDS failover | HA và recovery evidence |
| Performance | Peak load an toàn, slow query | phát hiện/diagnosis dưới tải |
| Security | PII/secret leakage, prompt injection, IAM anomaly fixture | redaction và policy |
| CI/CD | Build/test/deploy/migration failure, flaky test, webhook gap | cross-domain diagnosis |
| Agent | accuracy, loop limit, partial failure, HITL | agent correctness/safety |
| Integration | Prometheus/LLM/GitHub API outage | graceful degradation |
| DR | backup restore rehearsal/tabletop | giới hạn DR rõ ràng |

### 13.2. Phương pháp so sánh

| Mã | Phương pháp |
|---|---|
| B0 | Hệ thống EC2 hiện tại: alert riêng lẻ + runbook/Gemini + Telegram |
| B1 | Rule correlation + dependency, không multi-agent |
| B2 | Multi-Agent không pattern mining/knowledge graph |
| P | V2 đầy đủ: pattern + cross-domain graph + agents + deterministic Aggregator |

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
P-no-pattern-mining
P-no-knowledge-graph
P-no-cross-domain-change-links
P-no-security-agent
P-no-log-evidence
P-no-temporal-order
P-rules-only
P-LLM-only
```

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

---

## 14. Tiêu chí hoàn thành lát cắt V2

- Một deployment/migration failure tạo đúng một incident xuyên GitHub–EKS–RDS.
- Mọi claim chính có evidence ID và provenance.
- Secret/PII fixture không xuất hiện trong prompt trace, notification hoặc vector store.
- Agent timeout vẫn tạo kết quả partial có uncertainty.
- Không mutation nào vượt policy/approval.
- Rerun/restart có idempotency và loop limit.
- Verification thất bại không tạo trạng thái `RESOLVED`.
- Webhook gap được polling reconciliation bù mà không tạo incident trùng.
- Có thể replay scenario và tái tạo bảng metric.
- Baseline B0 và V2 dùng cùng ground truth và cửa sổ đo.

---

## 15. Lộ trình 12 tuần

### 15.1. Phân công nhóm hai người

| Role | Trách nhiệm |
|---|---|
| Infrastructure/Platform Engineer | VPC/EKS/RDS/IAM/OIDC, observability, deployment, fault injection, cost và HA |
| AI/AIOps Engineer | schemas, pattern mining, LangGraph, domain agents, Aggregator, RAG, policy, evaluation |

Cả hai review chéo security, integration, dữ liệu và luận văn.

### Tuần 1: Baseline và architecture decision records

- Chạy test baseline, capture alert flow và CI/CD flow.
- Chốt region, ba AZ, cost budget và POC limitations.
- Chốt event/evidence/deployment identity schemas.
- Chốt scenario, ground truth và acceptance targets.

**Bàn giao:** baseline report, architecture diagram, ADR và replay fixture.

### Tuần 2: VPC, identity và CI foundation

- Terraform VPC ba AZ, subnet, routes, endpoints và SG.
- GitHub OIDC role cho staging với trust conditions.
- CI scan, image digest và deployment metadata.

**Bàn giao:** `terraform validate/plan`, OIDC test và threat review.

### Tuần 3: EKS sandbox

- EKS, system Managed Node Group, namespaces, RBAC và controllers tối thiểu.
- Deploy frontend/Payment API bằng manifests/Helm.
- Probes, PDB và topology spread.

**Bàn giao:** pod/service HA test trên ít nhất hai AZ.

### Tuần 4: RDS Multi-AZ và migration

- RDS PostgreSQL Multi-AZ, Secrets Manager, backup và monitoring.
- Migrate demo schema/data, tách workload/control-plane.
- GitHub migration job có pre/post checks.

**Bàn giao:** restore/failover rehearsal và migration audit.

### Tuần 5: Observability ba trụ cột

- OTel/ADOT, CloudWatch logs, AMP/Prometheus và traces.
- Kubernetes/RDS/GitHub metadata correlation.
- CloudTrail và EKS audit logs.

**Bàn giao:** một request/deployment truy được từ commit tới trace/log/metric.

### Tuần 6: Security gateway và pattern mining

- PII/PCI/secret redaction.
- Log canonicalization và Drain/Drain3.
- Training/shadow baseline và pattern store.

**Bàn giao:** redaction fixtures và shadow anomaly report.

### Tuần 7: Incident Core và knowledge graph

- Durable incident state, timeline và idempotency.
- Neo4j topology cho repo/commit/workflow/image/deployment/service/RDS.
- Backfill deployment identity.

**Bàn giao:** correlation xuyên GitHub–EKS–RDS.

### Tuần 8: LangGraph và domain agents

- Orchestrator, Kubernetes Agent, RDS Agent, GitHub Actions Agent.
- MCP read-only tool contracts, deadline và budgets.
- Security Agent redaction/veto path.

**Bàn giao:** structured agent runs với partial failure.

### Tuần 9: Aggregator, RAG và agent observability

- Evidence merge, deterministic RCA scoring, impact và contradictions.
- pgvector migration/adapter; runbook retrieval có provenance.
- LLM explanation; AgentCore/Langfuse POC theo decision gate.

**Bàn giao:** incident report có score/evidence/cost/trace.

### Tuần 10: Policy, HITL và controlled action

- Risk matrix, approval, plan hash, expiry và SoD.
- Typed staging actions: rerun transient job, restart/rollout undo, notification.
- Verification Agent độc lập.

**Bàn giao:** end-to-end CD-07; action bị cấm bị từ chối.

### Tuần 11: Scenario, benchmark và ablation

- Chạy B0/B1/B2/P.
- Chạy failure/partial/security tests.
- Tính metrics bằng script và phân tích lỗi.

**Bàn giao:** raw data, metric tables, plots và error analysis.

### Tuần 12: Hardening và bảo vệ

- Chạy full CI/security/replay.
- Hoàn thiện diagram, runbook, cost, limitations và demo video.
- Đóng băng release, model/prompt/policy/knowledge versions.

**Bàn giao:** mã nguồn, IaC, dataset, báo cáo và reproducibility guide.

---

## 16. Kiểm thử

### 16.1. Unit

- Event/evidence schema, redaction và fingerprint.
- Pattern canonicalization, novelty và lifecycle.
- Entity resolution và topology traversal.
- RCA score, contradiction và stale penalty.
- LangGraph routing/loop limit.
- Policy, plan hash, expiry, SoD và idempotency.
- Verification post-conditions.

### 16.2. Contract

- GitHub webhook/API adapter.
- Kubernetes API/MCP tool output.
- RDS monitoring/log adapter.
- Prometheus/CloudWatch/trace queries.
- A2A agent response và MCP tool schema.
- pgvector/Neo4j repository contracts.

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
- Network path and VPC endpoint checks.

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
    kubernetes/
    rds/
    github_actions/
    security/
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

- GitHub–EKS–RDS deployment identity.
- Event/evidence schema và durable incident state.
- Redaction trước LLM/knowledge.
- Ba domain agents chính và Security Agent boundary.
- Deterministic Aggregator.
- Kịch bản CD-07 và SEC-01.
- Policy/HITL/verification/audit.
- Baseline, ground truth và replayable evaluation.

### Cắt trước

1. Jira/Teams/Email; giữ Telegram hoặc Slack và GitHub Checks draft.
2. Web dashboard nâng cao; giữ API và trace.
3. Full production deploy; giữ staging sandbox.
4. AgentCore deployment nếu POC region/cost/network không đạt; giữ LangGraph container trên EKS và contract A2A/MCP.
5. Langfuse nếu data governance chưa đạt; giữ CloudWatch/AgentCore trace.
6. Canary nâng cao; giữ rolling deployment và rollback.
7. Neo4j auto-discovery; giữ topology import có version.
8. DR multi-region, DDoS, ransomware execution; giữ tabletop.
9. Tự tạo PR sửa code.

---

## 19. Danh sách kiểm tra trước bảo vệ

- [ ] Baseline EC2 được mô tả đúng và có test evidence.
- [ ] Kiến trúc V2 phân biệt design, POC và deployed.
- [ ] EKS workload trải ít nhất hai AZ và có failure test.
- [ ] RDS Multi-AZ có failover/restore evidence.
- [ ] GitHub Actions dùng OIDC, không dùng AWS key dài hạn.
- [ ] Có canonical deployment identity.
- [ ] Metrics, logs, traces và CI/CD signals được correlation.
- [ ] Pattern mining có training/shadow/active và chống poisoning.
- [ ] Mọi log vào LLM/knowledge đã qua redaction.
- [ ] Agent trả structured evidence; Aggregator là điểm kết luận duy nhất.
- [ ] RCA score deterministic và version hóa.
- [ ] Partial failure không bị che giấu.
- [ ] Mọi mutation có policy, idempotency và audit.
- [ ] Action rủi ro có approval hợp lệ.
- [ ] Verification failure không tạo false resolution.
- [ ] Có B0/B1/B2/P, ablation, raw data và script metrics.
- [ ] Không commit secret, state, key hoặc runtime database.

---

## 20. Tài liệu tham chiếu và tên bắt buộc giữ

Tài liệu local:

- `README.md` và `PRODUCTION_ARCHITECTURE_COMPLETE.md`: baseline EC2.
- `docs/PLANNING.md` và `docs/CONTEXT.md`: format và kế hoạch V1.
- `agent_src/README.md` và `agent_src/RAG_SYSTEM_GUIDE.md`: AI/RAG hiện tại.
- `docs/AIops_CICD.md`: CI/CD hiện tại.

Tài liệu chính thức cần dùng khi triển khai:

- Amazon EKS best practices về subnet, data plane và Karpenter.
- Amazon RDS Multi-AZ, backup và monitoring.
- GitHub Actions OIDC với AWS và workflow run logs.
- Amazon Managed Service for Prometheus, ADOT và CloudWatch Container Insights.
- Amazon Bedrock AgentCore Runtime/Gateway, A2A, MCP và observability.

Tên code/API hiện tại như `/webhook`, `process_alerts_task`, `PostgreSQLDown`, `GEMINI_MAX_REMOTE_CALLS` và các endpoint health phải giữ trong adapter migration cho đến khi có versioning/deprecation plan rõ ràng.
