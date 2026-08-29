# CONTEXT_V2.md — Bối cảnh, baseline và kiến trúc nâng cấp Multi-Agent AIOps

> **Phiên bản:** 2.0
> **Cập nhật:** 2026-08-29
> **Giai đoạn:** Thiết kế và chuyển đổi từ baseline EC2 sang kiến trúc Fintech EKS/RDS Multi-AZ, 08/2026–12/2026
> **Trạng thái tài liệu:** Kiến trúc mục tiêu; không đồng nghĩa các thành phần V2 đã được triển khai

## 1. Thông tin khóa luận

| Hạng mục | Nội dung |
|---|---|
| Tên tiếng Việt đề xuất | Xây dựng và đánh giá hệ thống Multi-Agent AIOps hỗ trợ phát hiện bất thường, chẩn đoán xuyên miền CI/CD–production và tự phục hồi có kiểm soát cho hạ tầng Fintech trên AWS |
| Tên tiếng Anh đề xuất | Design and Evaluation of a Multi-Agent AIOps System for Anomaly Detection, Cross-Domain CI/CD-to-Production Diagnosis, and Controlled Remediation in AWS Fintech Infrastructure |
| Đơn vị | Trường Đại học Công nghệ Thông tin, ĐHQG TP. Hồ Chí Minh |
| Cán bộ hướng dẫn | ThS. Trần Thị Dung |
| Sinh viên | Lê Hoàng Việt (23521778), Lê Quang Tiến (23521572) |
| Thời gian | 08/2026–12/2026 |

## 2. Bài toán và câu hỏi nghiên cứu

Hệ thống Fintech dùng microservices, Kubernetes, database HA và CI/CD tạo ra lượng lớn logs, metrics, traces và workflow events. Monitoring dựa trên threshold có các hạn chế:

- Alert fatigue do một lỗi gốc tạo nhiều cảnh báo downstream.
- Điều tra lâu vì evidence nằm rải rác ở Prometheus, CloudWatch, Kubernetes, RDS và GitHub Actions.
- Không nhận ra tốt các “unknown unknowns” chưa có rule.
- Thiếu liên kết giữa commit/workflow/deployment và lỗi production.
- Log có thể chứa PII/PCI/secret, trong khi mọi quyết định cần audit.

Câu hỏi nghiên cứu:

> Việc kết hợp pattern mining, knowledge graph và các agent chuyên trách có giúp giảm cảnh báo thừa, tăng chất lượng RCA và rút ngắn xử lý sự cố xuyên GitHub Actions–EKS–RDS, đồng thời đảm bảo redaction, least privilege, HITL và auditability hay không?

Phạm vi là sandbox Fintech đại diện. Không tuyên bố đây là hệ thống production-ready hoặc đã được chứng nhận compliance.

## 3. Baseline repository đã kiểm tra

### 3.1. Hạ tầng hiện tại

Terraform hiện tạo:

- Một VPC `10.10.0.0/16`.
- Một public subnet ở Availability Zone đầu tiên.
- Internet Gateway và public route table.
- Ba EC2 có public IP/EIP: `monitor-ai-01`, `bank-web-01`, `bank-core-01`.
- Security Group theo role; root volume mã hóa và IMDSv2 bắt buộc.

```text
Internet
  -> public subnet / single AZ
       -> monitor-ai-01
       -> bank-web-01
       -> bank-core-01
```

Chưa có private subnet, NAT Gateway, VPC Endpoint, Load Balancer, Auto Scaling Group, EKS hoặc RDS.

### 3.2. Runtime hiện tại

| Role | Thành phần |
|---|---|
| Monitor/AI | Prometheus, Alertmanager, Grafana, Redis broker/cache, FastAPI AI Agent, Celery worker, log watcher |
| Core | Payment API, PostgreSQL container, PostgreSQL exporter |
| Web | React/Nginx frontend |

Staging và production chạy đồng thời trên cùng EC2 nhưng tách compose/state/cổng:

| Service | Staging | Production |
|---|---:|---:|
| AI Agent | 18000 | 8000 |
| Payment API | 18080 | 8080 |
| Frontend | 18081 | 3000 |

`/api/health` là liveness của Payment API; `/api/ready` kiểm tra cả PostgreSQL.

### 3.3. Alert/AI pipeline hiện tại

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

- `process_alerts_task` xử lý alert riêng; chưa có Celery `group/chord`, specialist agents hoặc Aggregator.
- Incident context chủ yếu ở Redis có TTL; chưa có durable incident state machine.
- `propose_remediation()` chỉ tạo proposal; chưa phải executor cho EKS/RDS/GitHub.
- GitHub webhook chưa tải/phân tích workflow logs/artifacts như CI/CD Agent mục tiêu.
- Chưa có pattern mining, knowledge graph, pgvector hoặc PII/PCI redaction boundary đầy đủ.

Kết quả kiểm thử ngày 2026-08-29:

```text
PYTHONPATH=agent_src venv/bin/pytest -q agent_src/tests
59 passed, 8 warnings
```

Warnings gồm API deprecated trong dependency test và `datetime.utcnow()` tại log watcher; không làm test thất bại nhưng cần backlog.

### 3.4. CI/CD hiện tại

- CI lint/test/build ba images và validate Docker Compose.
- Staging deploy theo changed role.
- Production deploy theo tag `v*` hoặc manual dispatch.
- Image lưu ở GHCR.
- Deploy qua SSH tới EC2, health check và rollback bằng `automation/app-release-deploy.sh`.

Chưa có GitHub OIDC với AWS, EKS deployment, SAST/DAST đầy đủ, workflow telemetry hoặc canonical deployment identity.

## 4. Kiến trúc V2 mục tiêu

```text
GitHub Actions/webhooks/API                 AWS workload telemetry
             |                                      |
             +---------- Ingestion Gateway ----------+
                              |
               signature/schema/security redaction
                              |
          Event Normalizer + Pattern Mining + Incident Core
                              |
                    LangGraph Orchestrator
             +----------------+----------------+
             |                |                |
       Kubernetes Agent    RDS Agent    GitHub Actions Agent
             \                |                /
              +------- Security/Compliance ---+
                              |
                  Evidence Aggregator
          deterministic RCA + impact + uncertainty
                              |
                 RAG/LLM explanation
                              |
                 Policy + Human approval
                              |
                 typed controlled action
                              |
                  Verification Agent
                              |
               audit + reviewed learning
```

### 4.1. Infrastructure

- VPC ba AZ với public subnets cho ingress/NAT và private subnets cho EKS/data.
- NAT Gateway theo AZ cho production reference; POC một NAT phải ghi rõ giới hạn.
- VPC endpoints cho các AWS services cần thiết.
- EKS worker và pods ở private subnets; cluster/workload trải ít nhất hai AZ.
- Managed Node Group ổn định cho system components; Karpenter cho workload biến động.
- RDS PostgreSQL Multi-AZ, automated backup, KMS, TLS và monitoring.
- Secrets Manager và short-lived identity.

### 4.2. EKS workload

- Namespaces tách `app`, `aiops`, `observability` và `security`.
- RBAC/service identity least privilege.
- Resource request/limit, HPA, readiness/liveness/startup probes.
- PodDisruptionBudget, topology spread và anti-affinity.
- NetworkPolicy và Security Group chỉ cho phép path cần thiết.
- Không expose Prometheus/Alertmanager/AI API công khai như baseline.

### 4.3. Observability

| Tín hiệu | Nguồn | Đích |
|---|---|---|
| Metrics | EKS, app, RDS, GitHub workflow | ADOT/Prometheus -> AMP hoặc CloudWatch |
| Logs | Pod, EKS audit/control plane, RDS, GitHub, CloudTrail | CloudWatch Logs sau redaction |
| Traces | Microservices, agent graph, MCP/tool calls, workflow instrumentation | OpenTelemetry -> X-Ray/CloudWatch |

GitHub webhook là đường near-real-time; polling scheduler là reconciliation fallback. Logs/artifacts được lấy qua GitHub API và redact trước khi lưu hoặc gửi LLM.

### 4.4. Knowledge

- Neo4j lưu quan hệ Repository–Commit–Workflow–Image–Deployment–Kubernetes workload–Service–RDS.
- Aurora PostgreSQL-compatible/PostgreSQL với `pgvector` lưu embeddings của runbook và incident đã duyệt.
- ChromaDB hiện tại chỉ giữ như adapter local trong migration.
- Control-plane database tách khỏi workload database.

### 4.5. Agent runtime

- LangGraph quản lý state machine, branching, checkpoint và loop limit.
- Orchestrator route theo event/entity/evidence gap, không chỉ theo keyword.
- Amazon Bedrock là foundation model platform mục tiêu; Claude 3.5 Sonnet từ đặc tả là ứng viên ban đầu. Model ID phải được cấu hình, kiểm thử trong region và ghi vào audit, không hard-code.
- AgentCore Runtime/Gateway là target sau POC về region, VPC, auth và cost.
- MCP dùng cho tool contract; A2A dùng cho agent contract.
- Celery hiện tại có thể tiếp tục ingestion/background trong phase đầu, nhưng không là incident source of truth.
- Kubernetes Agent dùng custom LangGraph trong MVP; Kagent chỉ là POC tùy chọn dưới cùng RBAC/MCP policy.

Presentation layer mục tiêu gồm Web Dashboard, Slack hoặc Telegram cho HITL, GitHub Checks cho PR/commit và Jira draft. Email/Teams là mở rộng; mọi nội dung phải dùng bản đã redact.

## 5. Agent contracts và quyền

| Agent | Đầu ra bắt buộc | Quyền |
|---|---|---|
| Kubernetes Agent | pod/node/deployment diagnosis + evidence IDs | Kubernetes read-only |
| RDS Agent | query/connection/lock/failover/migration diagnosis | RDS/monitoring read-only |
| GitHub Actions Agent | workflow/job/log/artifact/deploy diagnosis | GitHub read-only; mutation chỉ qua policy |
| Security/Compliance Agent | redaction report, policy findings, veto | Read-only + veto |
| Aggregator | ranked causes, impact, contradictions, uncertainty | Không mutation |
| Verification Agent | post-condition results | Read-only; quyền cập nhật verification state |

Mỗi agent response phải có:

```text
schema_version, incident_id, agent_run_id
status: COMPLETE | PARTIAL | FAILED
started_at, completed_at
evidence[], hypotheses[]
tool_calls[], errors[]
data_classification, redaction_status
```

## 6. Luồng xử lý V2

```text
Signal
  -> authenticate/validate
  -> redact PII/PCI/secret
  -> normalize event
  -> mine/score pattern
  -> deduplicate/correlate
  -> create or update incident
  -> LangGraph parallel investigation
  -> Aggregator
  -> RAG/LLM explanation
  -> policy decision
  -> approval when required
  -> typed action
  -> independent verification
  -> RESOLVED/FAILED/ESCALATED
  -> reviewed incident/pattern memory
```

Chỉ Verification Agent hoặc deterministic verification service được tạo `RESOLVED`. Exit code thành công không đủ.

## 7. Pattern mining và self-evolution

Log được redact, normalize và phân cụm bằng Drain/Drain3 hoặc thuật toán LogPAI được chọn. Baseline phải có scope theo service, environment và application version.

```text
CANDIDATE -> OBSERVED -> REVIEWED_NORMAL
                     \-> REVIEWED_ABNORMAL
                     \-> QUARANTINED

REVIEWED_NORMAL -> DRIFTED -> CANDIDATE
```

Ba mode:

1. Training trên window đã loại incident/maintenance.
2. Shadow chỉ đo, không action.
3. Active sau validation.

Self-evolution chỉ promote runbook, incident memory hoặc pattern sau verification/review. Không tự fine-tune model weights và không tự học từ LLM output chưa kiểm chứng.

## 8. Canonical identity xuyên CI/CD–production

Mỗi deployment record phải nối được:

```text
repository -> commit_sha -> pull_request -> workflow_run/job
-> artifact/image_digest -> deployment_id
-> EKS cluster/namespace/workload/revision
-> database_migration_id
```

Thiếu chuỗi identity này thì GitHub Actions Agent chỉ có thể báo lỗi CI riêng lẻ, chưa thể chẩn đoán cross-domain.

## 9. Security, HITL và audit

- Webhook phải có signature/auth, replay protection và schema validation.
- Redaction xảy ra trước LLM, vector store, trace và notification.
- GitHub Actions dùng OIDC với trust conditions; không giữ AWS access key dài hạn.
- MCP tools có input/output schema, target allowlist, timeout, rate limit và audit.
- LLM không có generic shell/SSH/`kubectl`/AWS/SQL mutation.
- Rerun workflow, restart/scale staging là action có kiểm soát.
- Production rollback, RDS failover hoặc secret rotation yêu cầu approval rủi ro cao.
- IAM/SG broadening và destructive migration bị từ chối tự động.
- Approval có plan hash, expiry, target, environment và approver identity.
- Audit store append-only; Langfuse/agent trace không thay thế audit.

## 10. Kịch bản và đánh giá bắt buộc

Kịch bản trung tâm: deployment thất bại do database migration. GitHub Agent, RDS Agent và Kubernetes Agent phải phối hợp để xác định migration là root cause và rollout/pod readiness là impact.

Các scenario bổ sung:

- Pod CrashLoopBackOff/OOMKilled.
- RDS failover.
- Flaky test và GitHub rate limit.
- Webhook downtime với polling fallback.
- Secret/PII leakage trong CI log.
- Prometheus hoặc LLM outage.
- Verification failure sau action.

So sánh:

| Mã | Phương pháp |
|---|---|
| B0 | Baseline EC2 hiện tại |
| B1 | Rule correlation + dependency |
| B2 | Multi-Agent không pattern/graph đầy đủ |
| P | V2 đầy đủ |

Metrics: MTTD, MTTR, alert compression, RCA top-1/top-3, cross-domain accuracy, evidence coverage, false positive, redaction recall, HITL compliance, false resolution, latency và cost/incident.

Các con số trong đặc tả là acceptance targets cần đo, không phải kết quả đã đạt.

## 11. Khoảng cách triển khai

| Nhóm | Hiện trạng | V2 cần đạt |
|---|---|---|
| HA | EC2 single-AZ | EKS/RDS Multi-AZ và failure evidence |
| CI/CD identity | SSH deploy theo role | OIDC + immutable deployment identity |
| Observability | Metrics/alerts là chính | metrics/logs/traces + GitHub telemetry |
| Detection | Threshold | pattern mining + time-window anomaly |
| Multi-Agent | Chưa có specialist/Aggregator | LangGraph + four domain agents + Aggregator |
| State | Redis TTL | durable incident/evidence/audit store |
| Knowledge | ChromaDB | reviewed graph + pgvector |
| Security | HMAC GitHub và SG | redaction, policy, SoD, KMS, full audit |
| Remediation | Proposal + EC2 release rollback | typed staging actions + HITL + verification |
| Evaluation | Unit tests, chưa benchmark V2 | replay dataset, ground truth, baseline và ablation |

## 12. Nguyên tắc phát triển

- Giữ baseline hoạt động đến khi EKS staging đạt acceptance test.
- Tách rõ “đã có”, “POC”, “mục tiêu” và “mở rộng”.
- Chốt schema và security boundary trước khi thêm agent.
- Deterministic preprocessing/scoring/policy trước LLM.
- Mọi claim có evidence; không đủ evidence thì `INCONCLUSIVE/ESCALATED`.
- Mỗi graph có loop limit, deadline và tool budget.
- Mọi mutation có typed action, policy, idempotency, audit và verification.
- Không dùng workload database làm control-plane database.
- Không ghi trước số liệu thực nghiệm.
- Không commit secret, `.env`, Terraform state, key hoặc runtime data.

## 13. Decision gates

| Quyết định | Default | Điều kiện thay đổi |
|---|---|---|
| Agent orchestration | LangGraph | Chỉ đổi khi benchmark/reliability chứng minh |
| Agent deployment | EKS trước, AgentCore POC | Chuyển AgentCore khi region/VPC/auth/cost đạt |
| Foundation model | Amazon Bedrock, model qua cấu hình | Model phải có trong region và vượt evaluation; không hard-code |
| Metrics store | AMP hoặc CloudWatch theo POC | Chốt theo query/cost/retention |
| Vector store | PostgreSQL/pgvector target | ChromaDB chỉ local migration |
| Graph | Neo4j | Có fallback relational edges nếu vận hành quá nặng |
| CI event collection | Webhook + API polling | OTel workflow telemetry là bổ sung |
| Production mutation | Disabled mặc định | Chỉ mở sau policy/security review ngoài phạm vi MVP |

## 14. Tài liệu tham chiếu

Tài liệu local:

| Đường dẫn | Vai trò |
|---|---|
| `README.md` | Baseline runtime, alert và release |
| `PRODUCTION_ARCHITECTURE_COMPLETE.md` | Kiến trúc EC2 hiện tại |
| `docs/PLANNING.md`, `docs/CONTEXT.md` | Format V1 |
| `docs/PLANNING_V2.md` | Kế hoạch triển khai chi tiết V2 |
| `agent_src/README.md`, `agent_src/RAG_SYSTEM_GUIDE.md` | AI Agent và RAG hiện tại |
| `docs/AIops_CICD.md` | CI/CD hiện tại |

Tài liệu chính thức cần kiểm tra khi triển khai:

- [Amazon EKS Karpenter best practices](https://docs.aws.amazon.com/eks/latest/best-practices/karpenter.html)
- [Amazon EKS VPC and subnet considerations](https://docs.aws.amazon.com/eks/latest/best-practices/subnets.html)
- [Amazon RDS Multi-AZ deployments](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html)
- [GitHub Actions OIDC with AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
- [GitHub workflow run logs](https://docs.github.com/en/actions/how-tos/monitor-workflows/use-workflow-run-logs)
- [Amazon Managed Service for Prometheus on EKS](https://docs.aws.amazon.com/eks/latest/userguide/prometheus.html)
- [OTel Container Insights for Amazon EKS](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/container-insights-eks-otel.html)
- [Amazon Bedrock AgentCore A2A](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-a2a.html)
- [Amazon Bedrock AgentCore Gateway with MCP](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-using.html)
