# Nhận xét và phạm vi khóa luận V2

## Kết luận chính

Nhận xét trước đã thu hẹp phạm vi quá nhiều. Với một khóa luận tốt nghiệp, chỉ làm một bộ Agent chạy trên EC2 sẽ chưa thể hiện đầy đủ giá trị của đề tài.

Phạm vi phù hợp hơn là xây dựng và đánh giá một **nền tảng AIOps đa Agent quản lý xuyên tầng từ ứng dụng đến hạ tầng cho Fintech trên AWS**, gồm cả:

- Hạ tầng cloud có khả năng mở rộng và chịu lỗi.
- Thu thập dữ liệu từ ứng dụng, database, Kubernetes và CI/CD.
- Phát hiện, gom nhóm và điều tra sự cố bằng nhiều Agent.
- Bảo mật dữ liệu trước khi gửi cho AI.
- Đề xuất và thực hiện một số thao tác khắc phục có kiểm soát.
- Đánh giá bằng kịch bản và số liệu có thể lặp lại.

Điểm khác biệt chính của đề tài là Agent không chỉ nói rằng một ứng dụng bị lỗi. Agent phải lần theo quan hệ phụ thuộc để trả lời được: lỗi đang xảy ra ở tầng nào, ảnh hưởng đến dịch vụ nghiệp vụ nào và nguyên nhân ban đầu là gì.

Đây là phạm vi đủ rộng cho khóa luận. Tuy nhiên, nhóm không cần biến mọi công nghệ trong tài liệu thành một sản phẩm production hoàn chỉnh. Phần bắt buộc phải là một luồng hoàn chỉnh, chạy được trên AWS và có số liệu chứng minh.

---

## 1. Đồ án đang giải quyết vấn đề gì?

Một hệ thống Fintech có nhiều dịch vụ. Khi xảy ra sự cố, hệ thống giám sát thường phát ra nhiều cảnh báo riêng lẻ. Người vận hành phải tự kiểm tra log, database, Kubernetes và lịch sử deploy để tìm nguyên nhân.

Đồ án muốn xây dựng một hệ thống có thể:

```text
Cảnh báo từ nhiều nguồn
-> Gom các cảnh báo liên quan
-> Tìm nguyên nhân chính
-> Đưa ra bằng chứng
-> Đề xuất cách xử lý
-> Chờ con người phê duyệt
-> Xử lý trên môi trường cho phép
-> Kiểm tra lại kết quả
```

Điểm nghiên cứu không phải chỉ là “gọi một mô hình AI”. Điểm quan trọng là chứng minh việc kết hợp **Agent nghiệp vụ, Agent hạ tầng, dữ liệu liên kết và luật an toàn** có giúp điều tra sự cố từ App đến Infrastructure (hạ tầng) tốt hơn hệ thống cảnh báo thông thường hay không.

---

## 2. Đánh giá hai tài liệu hiện tại

| Tài liệu | Điểm tốt | Điểm cần sửa |
|---|---|---|
| `CONTEXT_V2.md` | Mô tả đúng hệ thống hiện tại, vấn đề cần giải quyết và kiến trúc mong muốn | Chưa tách rõ mục tiêu khóa luận, phần triển khai thật và phần mở rộng |
| `PLANNING_V2.md` | Có roadmap, Agent, bảo mật, scenario và cách đánh giá | Có nhiều công nghệ nhưng chưa xác định cái nào là kết quả bắt buộc của khóa luận |

### Những nội dung nên giữ

- Chuyển từ cảnh báo đơn lẻ sang điều tra sự cố có liên kết.
- Theo dõi được quan hệ từ dịch vụ nghiệp vụ xuống API, container, database, network và cloud.
- Liên kết commit, workflow, image, deployment, Kubernetes và database.
- Có Kubernetes Agent, Database Agent, CI/CD Agent và Security Agent.
- Aggregator (bộ phận gom bằng chứng) đưa ra kết luận có cấu trúc.
- LLM chỉ giải thích và đề xuất, không có quyền tự chạy lệnh nguy hiểm.
- Có người phê duyệt trước thao tác thay đổi hệ thống.
- Có bước kiểm tra độc lập sau khi xử lý.
- Có benchmark (bộ đo thực nghiệm) để so sánh với hệ thống cũ.

---

## 3. Phạm vi khóa luận nên chốt

### 3.1. Phần bắt buộc phải hoàn thành

#### A. Các dịch vụ Fintech mẫu

Nên tổ chức hệ thống theo một nền tảng dùng chung và nhiều bộ kịch bản nghiệp vụ:

| Dịch vụ | Vai trò trong khóa luận | Kịch bản tiêu biểu |
|---|---|---|
| Mobile Banking | Dịch vụ chính, triển khai đầy đủ | Đăng nhập lỗi, chuyển tiền thất bại, API chậm |
| Buy Now Pay Later | Mở rộng khả năng dùng lại nền tảng | Tạo khoản vay lỗi, thanh toán timeout |
| Investment App | Kiểm tra dữ liệu thời gian gần thực | Giá thị trường chậm, đặt lệnh thất bại |
| AI Credit Scoring | Kiểm tra pipeline dữ liệu và model | Thiếu feature, model phản hồi chậm |

Mobile Banking nên là luồng chính. Các dịch vụ còn lại có thể là các service nhỏ hoặc scenario pack (bộ kịch bản) dùng chung hạ tầng và Agent.

#### B. Nền tảng AWS

- VPC có public subnet và private subnet.
- EKS chạy workload của ứng dụng mẫu.
- Workload trải trên ít nhất hai Availability Zone (khu vực độc lập trong một vùng AWS).
- RDS PostgreSQL Multi-AZ cho dữ liệu ứng dụng.
- GitHub Actions dùng OIDC (cấp quyền ngắn hạn thay vì lưu AWS key dài hạn).
- CI/CD build image, triển khai và ghi lại thông tin deployment.
- Monitoring có metrics, logs và health check.

#### C. Incident Core

Incident Core (bộ phận quản lý vòng đời sự cố) phải:

- Nhận dữ liệu từ Alertmanager và GitHub Actions.
- Chuẩn hóa các loại dữ liệu về một event schema (mẫu dữ liệu sự kiện chung).
- Che secret, PII và PCI trước khi gửi cho AI hoặc lưu vào kho kiến thức.
- Lưu incident, evidence, agent run và audit bền vững.
- Gom cảnh báo trùng hoặc có liên quan vào cùng một incident.
- Hỗ trợ timeout, retry giới hạn và agent bị lỗi.

#### D. Multi-Agent Investigation

Agent nên được chia thành hai nhóm:

**Application Agents** (Agent hiểu nghiệp vụ):

- Mobile Banking Agent.
- BNPL Agent.
- Investment Agent.
- AI Credit Scoring Agent.

**Infrastructure Agents** (Agent hiểu hạ tầng):

- Kubernetes Agent.
- RDS Agent.
- Network/API Gateway Agent.
- CI/CD Agent.
- Security Agent.

Không nhất thiết phải xây một Agent độc lập hoàn chỉnh cho từng dịch vụ. Application Agent chủ yếu cung cấp kiến thức, dependency và impact (mức ảnh hưởng); Infrastructure Agent chịu trách nhiệm điều tra hệ thống bên dưới.

Tối thiểu cần có:

1. **Kubernetes Agent:** kiểm tra pod, deployment, event, resource và readiness.
2. **RDS Agent:** kiểm tra kết nối, migration, lock, slow query và trạng thái database.
3. **GitHub Actions Agent:** kiểm tra workflow, job, log, artifact và deployment.
4. **Security Agent:** kiểm tra dữ liệu nhạy cảm và có quyền từ chối luồng không an toàn.

Ví dụ quan hệ cần truy được:

```text
Mobile Banking
-> Transaction Service
-> Kubernetes Pod
-> RDS PostgreSQL
-> VPC/Load Balancer
-> GitHub Deployment
```

Các Agent chỉ được dùng tool (công cụ truy vấn) đúng quyền của mình. Kết quả phải có trạng thái, lỗi, thời gian và danh sách bằng chứng.

#### E. Aggregator và quyết định

Aggregator phải:

- Gom kết quả từ các Agent.
- Loại bằng chứng trùng.
- Phát hiện kết quả mâu thuẫn.
- Xếp hạng nguyên nhân.
- Gắn từng kết luận với evidence ID (mã bằng chứng).
- Nêu rõ mức độ không chắc chắn.
- Tạo remediation plan (kế hoạch xử lý) theo mẫu cố định.

Điểm RCA (nguyên nhân gốc) phải được tính bằng luật hoặc công thức có thể lặp lại. LLM chỉ viết phần giải thích dễ đọc.

#### F. Controlled Remediation

Khóa luận cần chứng minh ít nhất một thao tác xử lý an toàn trên staging:

- Rerun một job CI/CD được xác định là lỗi tạm thời.
- Restart hoặc rollback một deployment staging.
- Gửi thông báo và tạo đề xuất xử lý.

Không cho Agent tự động thay đổi production, IAM, Security Group, database schema hoặc secret.

#### G. Đánh giá thực nghiệm

Phải có các kịch bản có nguyên nhân đúng được xác định trước:

- Database migration lỗi làm deployment thất bại.
- Pod bị CrashLoopBackOff hoặc OOMKilled.
- RDS failover.
- GitHub workflow lỗi hoặc webhook bị mất.
- Secret/PII xuất hiện trong log.
- Một Agent hoặc một nguồn dữ liệu bị gián đoạn.

Kịch bản trung tâm nên là lỗi triển khai làm hỏng giao dịch Mobile Banking:

```text
Migration database lỗi
-> Deployment API không sẵn sàng
-> Transaction Service trả lỗi
-> Mobile Banking không chuyển tiền được
```

Agent phải xác định migration là nguyên nhân gốc, còn lỗi API và giao dịch là ảnh hưởng lan truyền.

---

### 3.2. Phần nên xem là mở rộng

Các nội dung sau vẫn có thể giữ trong kiến trúc và phần hướng phát triển, nhưng không nên là điều kiện đánh trượt khóa luận:

- AgentCore Runtime.
- A2A (giao tiếp giữa các Agent theo chuẩn riêng).
- Neo4j (cơ sở dữ liệu dạng đồ thị).
- Karpenter (tự cấp phát node Kubernetes).
- AMP (dịch vụ Prometheus quản lý của AWS).
- Langfuse.
- Multi-region disaster recovery (khôi phục khi mất cả vùng AWS).
- Tự động xử lý production.
- Canary hoặc blue-green deployment nâng cao.

Đây chính là Future Work (hướng phát triển tiếp theo). Future Work không làm đề tài yếu đi. Ngược lại, nó cho thấy nhóm biết giới hạn của đề tài và biết hệ thống có thể mở rộng thế nào. Phần quản lý xuyên App và Infrastructure vẫn là phạm vi bắt buộc của khóa luận; chỉ các công nghệ triển khai nâng cao mới để lại cho Future Work.

---

## 4. Những vấn đề cần chỉnh trong hai file

| Vấn đề | Nhận xét | Cách chỉnh |
|---|---|---|
| Quá nhiều công nghệ ngang hàng | Người đọc không biết cái nào thật sự phải làm | Đánh dấu rõ `Bắt buộc`, `POC` (bản thử nghiệm) và `Future Work` |
| Chỉ nhìn một tầng hệ thống | Không chứng minh được Agent hiểu tác động nghiệp vụ của lỗi hạ tầng | Thiết kế dependency graph và scenario xuyên App -> Infrastructure |
| EKS/RDS bị xem như phần làm thêm | Không phù hợp nếu tên đề tài nhấn mạnh AWS Fintech | Đưa EKS và RDS vào phần bắt buộc ở mức một kịch bản chạy được |
| Self-healing quá rộng | Tự xử lý mọi loại sự cố là nguy hiểm và không thể hoàn thành nhanh | Chỉ làm controlled remediation trên staging |
| Chuyển hạ tầng và đổi AI cùng lúc | Khó biết kết quả tốt hơn đến từ đâu | Ghi rõ hai nhóm đánh giá: nền tảng AWS và chất lượng AIOps |
| Chưa có tiêu chí nghiệm thu | Có mục tiêu nhưng chưa nói thế nào là đạt | Thêm điều kiện kiểm tra cụ thể cho từng nhóm |
| Công thức RCA còn chung chung | Chưa biết trọng số lấy từ đâu | Chốt công thức trước benchmark và không đổi trong quá trình đo |
| Lưu dữ liệu nhạy cảm chưa rõ | Có thể làm lộ thông tin qua log, trace hoặc prompt | Thiết kế redaction trước persistence (lưu trữ) và trước LLM |
| State machine thiếu tình huống thực tế | Chưa có rejected, expired, duplicate và verification failed | Bổ sung đầy đủ trạng thái và điều kiện chuyển trạng thái |

---

## 5. Kiến trúc triển khai phù hợp

### Giai đoạn 1: Baseline

Giữ hệ thống EC2 hiện tại để có mốc so sánh:

```text
EC2 + Docker Compose
Prometheus + Alertmanager
Redis + Celery
Gemini + ChromaDB
```

### Giai đoạn 2: Nền tảng AWS mục tiêu

```text
GitHub Actions
       |
       v
VPC 2 AZ
       |
   EKS private nodes ---- RDS PostgreSQL Multi-AZ
        |
   Mobile Banking / BNPL / Investment / Credit Scoring
         |
   Monitoring + AI services
```

Hai AZ là đủ để chứng minh khả năng chịu lỗi trong phạm vi khóa luận. Ba AZ và NAT Gateway riêng theo từng AZ có thể giữ làm thiết kế production tham khảo.

### Giai đoạn 3: AIOps xuyên tầng

```text
Alertmanager/GitHub
        -> Ingestion
        -> Redaction
        -> Event Normalizer
        -> Incident Core
        -> Application + Infrastructure Agents
        -> Dependency Graph
        -> Aggregator
        -> Policy + Human Approval
        -> Staging Action
        -> Verification
        -> Audit + Knowledge
```

---

## 6. Tiêu chí hoàn thành khóa luận

Khóa luận được xem là đạt khi có đủ các kết quả sau:

- Ứng dụng mẫu chạy được trên EKS.
- Database ứng dụng chạy trên RDS Multi-AZ.
- Có ít nhất một pipeline CI/CD dùng OIDC.
- Một sự cố migration có thể được liên kết từ GitHub đến Kubernetes và RDS.
- Một lỗi hạ tầng có thể được liên kết đến dịch vụ nghiệp vụ bị ảnh hưởng.
- Mobile Banking có ít nhất một luồng xử lý xuyên từ App đến AWS Infrastructure.
- Các kịch bản BNPL, Investment hoặc AI Credit Scoring dùng lại được nền tảng chung.
- Các Agent trả về bằng chứng có cấu trúc.
- Aggregator xác định được nguyên nhân chính và tác động phụ.
- Dữ liệu nhạy cảm không xuất hiện trong prompt, notification hoặc knowledge store.
- Có ít nhất một remediation chạy được trên staging.
- Verification thất bại không được ghi nhận là đã giải quyết.
- Có xử lý agent timeout, dữ liệu thiếu và kết quả mâu thuẫn.
- Có benchmark so sánh baseline và phiên bản Multi-Agent.
- Có số liệu, log, biểu đồ và mô tả giới hạn của kết quả.

---

## 7. Roadmap 12 tuần phù hợp hơn

| Tuần | Công việc chính | Kết quả |
|---|---|---|
| 1 | Đóng băng baseline và scenario | Số liệu hệ thống cũ, ground truth (nguyên nhân đã biết) |
| 2 | VPC, IAM và OIDC | Hạ tầng mạng và quyền triển khai |
| 3 | EKS và ứng dụng mẫu | Frontend/API chạy trên EKS |
| 4 | RDS Multi-AZ và migration | Database chạy được, có kịch bản migration lỗi |
| 5 | Metrics, logs, health check và service catalog | Theo dõi được workload, deployment và dịch vụ nghiệp vụ |
| 6 | Event schema và redaction | Dữ liệu được chuẩn hóa và che thông tin nhạy cảm |
| 7 | Incident Core và dependency graph | Liên kết được App, service, deployment và infrastructure |
| 8 | Application Agents và Kubernetes/RDS Agents | Điều tra được tác động và nguyên nhân ở nhiều tầng |
| 9 | GitHub, Network, Security Agents và Aggregator | Điều tra xuyên CI/CD, App, EKS và RDS |
| 10 | Policy, phê duyệt và staging action | Có một thao tác khắc phục an toàn |
| 11 | Verification và benchmark | Đo B0, B1 và P trên các scenario |
| 12 | Hardening và hoàn thiện luận văn | Biểu đồ, giới hạn, demo và hướng phát triển |

Nếu một hạng mục bị trễ, giảm độ sâu của công nghệ mở rộng, không bỏ toàn bộ luồng chính.

---

## 8. Cách sửa trực tiếp từng file

### `CONTEXT_V2.md`

Thêm bảng này ở phần đầu:

| Nhóm | Thành phần |
|---|---|
| Đã có | EC2, monitoring, Celery, RAG, Gemini, Telegram, rollback |
| Bắt buộc trong khóa luận | VPC, EKS, RDS Multi-AZ, OIDC, event schema, redaction, agents, Aggregator, verification |
| POC | Karpenter, graph database, vector database mới, observability nâng cao |
| Future Work | AgentCore, A2A, multi-region DR, production self-healing |

Sau đó:

1. Giữ phần mô tả baseline hiện tại.
2. Thêm một sơ đồ kiến trúc MVP chạy trên EKS/RDS.
3. Ghi rõ EKS và RDS là phần triển khai bắt buộc ở mức tối thiểu.
4. Ghi rõ AgentCore, Neo4j và Karpenter không phải điều kiện bắt buộc.
5. Tách mục tiêu nghiên cứu khỏi mục tiêu production.
6. Thêm các lớp Application và Infrastructure vào sơ đồ.
7. Chọn Mobile Banking làm luồng end-to-end chính; ghi rõ các dịch vụ còn lại là scenario mở rộng.

### `PLANNING_V2.md`

1. Đổi roadmap thành ba nhóm: nền tảng AWS, AIOps và đánh giá.
2. Đưa EKS/RDS lên các tuần đầu, không để ở cuối như việc “nếu còn thời gian”.
3. Tách Application Agents và Infrastructure Agents nhưng dùng chung Orchestrator và Aggregator.
4. Thêm dependency graph nối App -> Service -> Kubernetes -> Database -> Network -> Cloud.
5. Thêm một scenario end-to-end bắt buộc: migration lỗi ảnh hưởng Mobile Banking.
6. Thêm các scenario mở rộng cho BNPL, Investment và AI Credit Scoring.
7. Thêm bảng Definition of Done (điều kiện hoàn thành) cho từng tuần.
8. Thêm tiêu chí đo và số lần chạy trước benchmark.
9. Đưa các công nghệ triển khai nâng cao vào mục Future Work.
10. Ghi rõ mọi remediation trong khóa luận chỉ chạy trên staging.

---

## 9. Kết luận

Phạm vi phù hợp nhất không phải là “chỉ làm MVP trên EC2”, cũng không phải “xây toàn bộ một nền tảng production của AWS”.

Phạm vi nên là:

```text
Nền tảng AWS thật ở mức khóa luận
+ Một luồng Multi-Agent hoàn chỉnh
+ Một số thao tác khắc phục có kiểm soát
+ Benchmark có ground truth
+ Bảo mật và audit đầy đủ
```

Như vậy đề tài đủ rộng để là một khóa luận tốt nghiệp, nhưng vẫn có ranh giới rõ ràng để hoàn thành và bảo vệ được. Future Work vẫn tồn tại, nhưng chỉ dành cho những phần mở rộng sau khi phần đóng góp chính đã chạy và có số liệu chứng minh.
