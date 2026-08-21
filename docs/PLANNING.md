# PLANNING.md — Kế hoạch nâng cấp đồ án thành Khóa luận tốt nghiệp

> **Khoảng thời gian:** 08/2026 – 12/2026
> **Căn cứ:** hiện trạng codebase và README ngày 2026-08-20
> **Người thực hiện:** Lê Hoàng Việt và Lê Quang Tiến
> **Mục tiêu:** biến đồ án AIOps hiện tại thành một nghiên cứu có phương pháp, đo lường và bằng chứng thực nghiệm, đủ tiêu chuẩn khóa luận tốt nghiệp.

---

## 1. Tóm tắt điều hành

Đồ án hiện tại đã có nền tảng tốt hơn một demo thông thường: Terraform + Ansible + Docker + CI/CD + Prometheus/Alertmanager/Grafana + Redis/Celery + ChromaDB + Gemini + Telegram, cùng cơ chế dedup, rollback và phân tách vai trò `monitor` / `core` / `web`.

Để lên tầm khóa luận, hệ thống cần chuyển từ **tích hợp công nghệ** sang **nghiên cứu có đóng góp, có so sánh và chứng minh định lượng**. Trọng tâm là:

> Xây dựng mô hình AIOps **nhận biết ngữ cảnh** (metrics + logs + traces + topology) kết hợp **luật xác định + RAG + LLM có kiểm soát** để giảm cảnh báo trùng, nâng cao độ chính xác chẩn đoán và hạn chế hành động sai.

---

## 2. Hiện trạng và khoảng trống

### 2.1. Điểm mạnh hiện có

- Kiến trúc 4 lớp rõ ràng: Terraform / Ansible / Release image / CI/CD.
- Phân tách ba vai trò hạ tầng `monitor`, `core`, `web`.
- Alert flow hoàn chỉnh: Alertmanager → webhook → Redis → Celery → RAG → Gemini → Telegram → verify → incident memory.
- Dedup/cooldown theo fingerprint, rollback tự động theo health check.
- Có deterministic diagnosis cho nhiều sự cố quen thuộc.

### 2.2. Khoảng trống cần bổ sung

| # | Khoảng trống | Ảnh hưởng đến khóa luận |
|---|---|---|
| 1 | Chưa có **đóng góp khoa học** rõ ràng | Bị đánh giá là “lắp ghép công nghệ” |
| 2 | Chưa có **bộ dữ liệu + ground truth** để đánh giá | Không tái lập và không định lượng được |
| 3 | Chưa **so sánh định lượng** giữa các phương pháp | Thiếu bằng chứng hiệu quả |
| 4 | Chưa **correlate** đa nguồn (metric/log/trace/topology) | Khó phân biệt triệu chứng vs. nguyên nhân gốc |
| 5 | Chưa đánh giá **hallucination / độ tin cậy / an toàn AI** | Thiếu chiều sâu khoa học |
| 6 | Hạ tầng **single-AZ, mở Internet, credential tĩnh** | Chưa đạt chuẩn production-grade |
| 7 | Chưa chứng minh bằng **MTTA / MTTR / accuracy / chi phí** | Không thấy hiệu quả vận hành |

---

## 3. Đề tài khóa luận

- **Tiếng Việt:** Xây dựng hệ thống AIOps nhận biết ngữ cảnh để phát hiện, chẩn đoán và hỗ trợ xử lý sự cố mạng trong môi trường Cloud.
- **Tiếng Anh:** Context-Aware Hybrid AIOps System for Cloud Network Incident Detection, Diagnosis and Safe Remediation.

### 3.1. Đóng góp chính

Hệ thống không chỉ dùng LLM để trả lời cảnh báo, mà xây dựng mô hình:

```text
Metrics + Logs + Traces + Service Topology
                    |
                    v
          Incident Correlation Engine
                    |
                    v
     Rule Engine + RAG + LLM Reasoning
                    |
                    v
   Structured Diagnosis + Confidence + Evidence
                    |
                    v
     Human Approval / Safe Remediation
```

Điểm mới: **mô hình AIOps lai** gồm luật xác định, tương quan sự kiện, RAG và LLM có kiểm soát nhằm giảm cảnh báo trùng, tăng độ chính xác chẩn đoán và hạn chế hành động sai.

---

## 4. Câu hỏi nghiên cứu & giả thuyết

### 4.1. Câu hỏi nghiên cứu (RQ)

| Mã | Câu hỏi |
|---|---|
| RQ1 | Kết hợp metric + log + trace + topology có nâng cao độ chính xác chẩn đoán so với chỉ dùng Alertmanager ở mức đơn lẻ không? |
| RQ2 | Mô hình Hybrid Rule + RAG + LLM có giảm hallucination và tạo chẩn đoán có bằng chứng không? |
| RQ3 | Dedup + correlation + giới hạn LLM có giúp giảm độ trễ, chi phí và số thông báo không? |

### 4.2. Giả thuyết nghiên cứu (H)

| Mã | Giả thuyết |
|---|---|
| H1 | Hybrid AIOps đạt F1 chẩn đoán cao hơn rule-only và LLM-only. |
| H2 | RAG có trích dẫn bằng chứng làm giảm tỷ lệ khuyến nghị không căn cứ. |
| H3 | Correlation theo topology giảm số incident giả do cùng một nguyên nhân gốc. |
| H4 | Dedup giúp giảm số lần gọi LLM và giảm backlog Celery. |
| H5 | Human-approval gate đưa tỷ lệ remediation sai về gần 0 trong thử nghiệm. |

> Quy tắc: mỗi giả thuyết phải được chứng minh bằng số liệu đo thực tế, không phóng đại.

---

## 5. Kiến trúc cần cải tiến

### 5.1. Chuẩn hóa Incident Event

Tạo schema thống nhất thay cho việc truyền thẳng payload Alertmanager:

```json
{
  "incident_id": "INC-2026-0001",
  "event_id": "evt-001",
  "timestamp": "...",
  "environment": "staging",
  "service": "payment-api",
  "component": "postgres",
  "severity": "critical",
  "symptom": "readiness_failed",
  "source": "prometheus",
  "fingerprint": "...",
  "trace_id": "...",
  "evidence": [],
  "status": "firing"
}
```

**Lợi ích:** dễ correlation, dễ lưu trữ/truy vấn, dễ đánh giá lịch sử, dễ tích hợp CloudWatch/Prometheus/OpenTelemetry.

### 5.2. Incident Correlation Engine

Triển khai trước bằng Redis/PostgreSQL (chưa cần Kafka):

1. Gom các alert trong cửa sổ thời gian (ví dụ 60s).
2. So sánh theo service, instance, component, thời gian, topology, trace ID.
3. Xác định `root_cause_candidate`, `symptom_events`, `related_incidents`.

Ví dụ — một sự cố dây chuyền phải gộp thành một incident thay vì ba:

```text
PostgreSQLDown  -> PaymentAPIEndpointDown -> FrontendAPIProxyDown
        ^
Root cause: PostgreSQL unavailable
Downstream: Payment API readiness failed; Frontend proxy failed
```

### 5.3. Service Dependency Graph

```text
User --> Frontend --> Payment API --> PostgreSQL

AI Agent --> Redis Broker --> Celery Worker
```

Lưu dạng YAML hoặc PostgreSQL và dùng để ưu tiên nguyên nhân gốc:

```yaml
services:
  frontend:
    depends_on: [payment-api]
  payment-api:
    depends_on: [postgres]
  celery-worker:
    depends_on: [redis]
```

### 5.4. OpenTelemetry (mức tối thiểu)

- Trace `frontend → payment-api → postgres`.
- Gắn `trace_id` vào log; gắn `incident_id` vào log và Telegram.
- Đo latency, error rate, dependency failure.
- Stack: OpenTelemetry SDK → Collector → Prometheus + Jaeger/Tempo + Grafana.

### 5.5. Chuẩn hóa đầu ra LLM

Bắt buộc LLM trả JSON có cấu trúc, không trả lời tự do:

```json
{
  "classification": "database_failure",
  "root_cause": "postgres_unavailable",
  "confidence": 0.94,
  "severity": "critical",
  "evidence": ["pg_up == 0", "Payment API /api/ready = 503", "Frontend proxy failed 20s later"],
  "recommended_actions": [],
  "requires_human_approval": true
}
```

Bắt buộc có: confidence, evidence, runbook reference, reasoning summary, recommended actions, mức độ nguy hiểm, cờ cần phê duyệt.

---

## 6. Từ “AI trả lời” sang “AI có kiểm soát”

### 6.1. Phân cấp hành động

| Cấp | Loại | Chính sách |
|---|---|---|
| Read-only | ping, health check, đọc metric/log/state | Tự động được phép |
| Reversible | restart container, retry worker, reload config | Chỉ ở staging hoặc sau phê duyệt |
| Destructive | xóa DB/volume, đổi SG/route/IAM, xóa instance | Cấm tuyệt đối với AI |

### 6.2. Policy Gate

```text
AI đề xuất -> Policy Engine kiểm tra -> rủi ro thấp? -> Tự động (staging)
                                            |            |
                                            Không        +---> Telegram xin phê duyệt
```

---

## 7. Bộ thí nghiệm & chỉ số đánh giá

### 7.1. Kịch bản tối thiểu (12)

| # | Kịch bản |
|---|---|
| 1 | Frontend container down |
| 2 | Payment API container down |
| 3 | PostgreSQL down |
| 4 | Redis broker down |
| 5 | CPU spike |
| 6 | Memory leak |
| 7 | Disk gần đầy |
| 8 | Network packet loss |
| 9 | API latency tăng |
| 10 | Failure chain: Postgres → API → Frontend |
| 11 | Alertmanager gửi lặp |
| 12 | LLM quota giới hạn / không khả dụng |

Mỗi kịch bản ghi: cách tạo lỗi, thời điểm, ground truth, alert kỳ vọng, root cause đúng, cách phục hồi, thời điểm kết thúc.

### 7.2. Các mô hình so sánh

| Mô hình | Thành phần |
|---|---|
| Baseline 1 | Chỉ dùng rule |
| Baseline 2 | LLM không RAG |
| Baseline 3 | RAG + LLM |
| **Proposed** | Correlation + topology + rule + RAG + LLM |
| Proposed + remediation | Có thêm policy gate |

### 7.3. Chỉ số đánh giá

| Nhóm | Chỉ số |
|---|---|
| Phát hiện | Precision, Recall, F1, FPR, detection latency |
| Chẩn đoán | Root cause Top-1/Top-3 accuracy, evidence coverage, unsupported claim, hallucination rate |
| Vận hành | MTTA, MTTR, queue backlog, P95 latency, LLM calls/incident, dedup rate, Telegram dư thừa |
| An toàn | Action trái policy, số lần cần phê duyệt, recovery success, rollback, tác động ngoài phạm vi |

### 7.4. Minh họa bảng kết quả (mẫu — phải đo thực tế)

| Chỉ số | Baseline | Proposed |
|---|---:|---:|
| Số alert cho 1 sự cố dây chuyền | 3 | 1 |
| Root cause Top-1 | 66% | 93% |
| Unsupported claim | 18% | 5% |
| P95 thời gian phân tích | 42s | 18s |
| LLM calls / incident | 3.2 | 1.1 |
| MTTA | 75s | 25s |
| False positive | 14% | 6% |

---

## 8. Lộ trình thực hiện

| GĐ | Nội dung | Sản phẩm |
|---|---|---|
| 1 | Chốt bài toán & baseline | Incident schema, KPI, 12 kịch bản, baseline JSON/CSV/log |
| 2 | Correlation & topology | Correlation module, dependency graph, lifecycle incident, lưu PostgreSQL |
| 3 | Nâng cấp AI | RAG theo service, LLM output JSON, evidence + confidence, fallback deterministic |
| 4 | Observability & an toàn | trace_id/incident_id, policy gate, human approval, remediation an toàn staging |
| 5 | Đánh giá khoa học | Chạy mỗi kịch bản 20–30 lần, so sánh baseline, thống kê, phân tích lỗi |
| 6 | Đóng gói bảo vệ | Sơ đồ, sequence, state machine, bảng trước/sau, video/repo tái lập |

---

## 9. Khuyến nghị hạ tầng theo mức ưu tiên

| Mức | Nội dung |
|---|---|
| **Bắt buộc** | Chuẩn hóa incident event, correlation, topology, structured LLM output, fault injection, benchmark + ground truth, KPI dashboard, test tự động |
| **Nên có** | OpenTelemetry, Postgres lưu incident, log tập trung (Loki/ELK), policy engine, human approval, SLO/error budget |
| **Mở rộng** | AWS Secrets Manager, SSM thay SSH, private subnet, ALB/HTTPS, multi-AZ, RDS, ECS/EKS, CloudWatch, chaos engineering |

> Không đưa toàn bộ “mở rộng” vào mục tiêu chính; chỉ thiết kế khả năng mở rộng và triển khai có chọn lọc.

---

## 10. Việc cần sửa trước khi bảo vệ

1. Terraform chỉ có 1 public subnet / 1 AZ.
2. Prometheus, Grafana, Alertmanager, AI Agent mở Internet.
3. Compose chứa credential database tĩnh.
4. Một số image monitoring dùng tag `latest` (thiếu tái lập).
5. ChromaDB phù hợp prototype, chưa đủ cho truy vấn incident giao dịch.
6. Chưa có distributed tracing.
7. Metrics mới chỉ đếm alert/queue/latency, chưa đo chất lượng chẩn đoán.
8. Chưa có benchmark định lượng.
9. Rollback dựa trên health check, chưa dựa trên SLO/error rate.
10. Cần tách rõ “AI đề xuất” và “AI được quyền thực thi”.

---

## 11. Cấu trúc khóa luận

| Chương | Nội dung |
|---|---|
| 1 | Giới thiệu — bối cảnh AIOps, alert fatigue, mục tiêu, phạm vi, đóng góp |
| 2 | Cơ sở lý thuyết — observability, SRE/ITIL, RAG, tool calling, event correlation, fault injection, MTTA/MTTR |
| 3 | Phân tích hệ thống hiện tại — baseline, luồng alert, hạn chế, yêu cầu |
| 4 | Mô hình đề xuất — incident schema, correlation, topology, hybrid reasoning, policy gate, an toàn |
| 5 | Triển khai — AWS, Docker, Prometheus, Celery/Redis, RAG, OTel, CI/CD |
| 6 | Thực nghiệm & đánh giá — kịch bản, baseline, phương pháp đo, kết quả, thống kê, phân tích lỗi |
| 7 | Kết luận — mức độ đạt mục tiêu, đóng góp, hạn chế, hướng phát triển |

---

## 12. Đánh giá rủi ro

**Mức độ: Medium.**

Rủi ro lớn nhất: mở rộng quá nhiều công nghệ (Kafka, K8s, multi-region, EKS, RDS) khiến mất trọng tâm và không đủ thời gian đo lường.

**Hướng xử lý:** ưu tiên đóng góp cốt lõi — correlation, topology, structured RAG/LLM, fault injection, benchmark định lượng. Các phần mở rộng hạ tầng chỉ dừng ở thiết kế + POC nếu thiếu thời gian.

### Thứ tự cắt giảm khi thiếu thời gian

1. Không cắt: evaluation framework, scenario evidence, HITL safety, verification, báo cáo, demo.
2. Giảm: triển khai Multi-AZ thực tế → giữ thiết kế Terraform + failure injection POC + phân tích chi phí.
3. Chỉ triển khai restart container + rollback trước; scale/traffic shift dừng ở thiết kế + mock.
4. Không bỏ baseline và so sánh trước/sau.

---

## 13. Quy trình xác nhận mỗi mốc

```text
Implement -> unit test -> integration/scenario test -> collect evidence
          -> update CONTEXT/README/thesis -> CI validation -> supervisor review
```

Mỗi mốc chỉ coi là hoàn thành khi có code, test chạy được, evidence đã lưu và không phóng đại trong tài liệu.
