# PLANNING.md - Kế hoạch khóa luận khoa học ứng dụng về AIOps

> **Thời gian dự kiến:** 08/2026 - 12/2026
> **Mục tiêu:** thiết kế, triển khai và đánh giá một hệ thống Multi-Agent AIOps trên AWS hai Availability Zone theo pipeline **Celery fan-out các agent chuyên trách -> Aggregator tổng hợp -> Human approval -> Controlled remediation -> Verification**.
> **Định hướng:** ưu tiên giải quyết một bài toán vận hành cụ thể bằng một hệ thống chạy được, có thể tái lập và được đánh giá bằng dữ liệu thực nghiệm. Khóa luận không tuyên bố đề xuất một thuật toán RCA tổng quát, một nền tảng HA tuyệt đối hay một sản phẩm sẵn sàng cho mọi môi trường sản xuất.

---

## Cách đọc kế hoạch này

Kế hoạch đi theo một câu chuyện duy nhất:

```text
Hệ thống hiện tại còn xử lý alert rời rạc
                |
                v
Đặt một bài toán vận hành cụ thể: nhiều alert cùng phát sinh trong một sự cố
                |
                v
Xây incident core để chuẩn hóa, gom nhóm và lưu timeline
                |
                v
Thêm dependency + metric + log + probe để các agent chuyên trách tìm nguyên nhân có bằng chứng song song
                |
                v
Aggregator hợp nhất kết quả, sinh báo cáo cho kỹ sư và đề xuất playbook có kiểm soát
                |
                v
Xin phê duyệt -> chạy playbook staging -> xác minh kết quả
                |
                v
Triển khai workload trên AWS hai AZ
                 |
                 v
So sánh Multi-Agent/Multi-AZ với quy trình hiện tại bằng các kịch bản lỗi có thể phát lại
```

Nói ngắn gọn, khóa luận không xây nhiều tính năng độc lập. Khóa luận xây một **vòng xử lý sự cố hoàn chỉnh**:

> **Alert -> Incident -> Evidence -> Diagnosis -> Approval -> Action -> Verification -> Evaluation**

Trong đó Multi-Agent là cơ chế phân công có kiểm soát, không phải mục tiêu tạo ra càng nhiều LLM agent càng tốt:

```text
Celery fan-out
  -> Correlation | Dependency | Metric | Log | Probe | Change/Runbook Agent
  -> Aggregator (merge evidence + deterministic RCA scoring)
  -> Human approval -> Controlled remediation -> Verification Agent
```

Mỗi phần phía sau chỉ được xây sau khi phần phía trước đã chạy được:

| Bước | Câu hỏi cần trả lời | Phần tương ứng |
|---|---|---|
| 1. Hiện trạng | Hệ thống đang xử lý sự cố như thế nào? | Mục 1, 3 |
| 2. Bài toán | Vấn đề vận hành nào cần cải thiện? | Mục 1, 4, 5 |
| 3. Lõi sự cố | Làm sao biến nhiều alert thành một incident? | Mục 6, 9 |
| 4. Chẩn đoán | Vì sao sự cố xảy ra và dựa trên bằng chứng nào? | Mục 6, 7 |
| 5. Xử lý an toàn | Có thể hành động mà không để LLM tự ý thay đổi hệ thống không? | Mục 7, 8, 10 |
| 6. Đánh giá | Giải pháp có tốt hơn quy trình hiện tại không? | Mục 11, 12 |
| 7. Thực hiện | Xây theo thứ tự nào và bàn giao gì? | Mục 13, 14, 15 |

Kết quả cần đạt không phải là “có nhiều thành phần AI”, mà là kỹ sư có thể theo dõi được một incident từ lúc alert xuất hiện đến lúc hệ thống xác minh đã phục hồi hoặc chuyển người xử lý.

---

## 1. Định hướng tổng thể

### 1.1. Hệ thống hiện tại

```text
Prometheus / bộ giám sát dịch vụ / bộ theo dõi nhật ký
        -> Alertmanager hoặc webhook
        -> FastAPI /webhook
        -> Redis + Celery
        -> quy trình xử lý xác định hoặc Gemini + RAG
        -> Telegram
        -> xác minh sau một khoảng thời gian
```

Hệ thống hiện tại đã là một **bot cảnh báo thông minh**. Nó nhận cảnh báo, loại bỏ cảnh báo lặp, tìm quy trình xử lý trong ChromaDB, gọi Gemini khi cần, gửi báo cáo Telegram và kiểm tra lại sau đó.

Đây là nền tảng tốt nhưng không nên được xem là đóng góp mới chính, vì Zabbix, Grafana và Alertmanager cũng có thể phát hiện bất thường rồi gửi thông báo.

### 1.2. Hệ thống cần xây dựng

```text
Quan sát -> Chuẩn hóa -> Incident Core
                         |
                         v
                 Celery group/chord fan-out
        Correlation | Dependency | Metric
        Log | Probe | Change/Runbook agents
                         |
                         v
       Aggregator: merge evidence + RCA scoring + impact
                         |
       RAG/LLM explanation -> Human approval -> Policy
                         |
       Controlled remediation -> Verification Agent
                         |
       RESOLVED / FAILED / ESCALATED -> Incident memory
```

Khóa luận tập trung vào bài toán ứng dụng:

> Trong một hạ tầng phân tán có nhiều dịch vụ phụ thuộc nhau, việc bổ sung tương quan sự kiện, cấu trúc phụ thuộc và bằng chứng đa nguồn có giúp kỹ sư giảm cảnh báo thừa, xác định nguyên nhân và xử lý sự cố an toàn hơn quy trình hiện tại hay không?

### 1.3. Tên đề tài đề xuất

> **Xây dựng và đánh giá hệ thống Multi-Agent AIOps hỗ trợ tương quan cảnh báo, chẩn đoán sự cố và tự phục hồi có kiểm soát trên hạ tầng AWS hai Availability Zone.**

Nếu trường yêu cầu tên tiếng Anh, có thể dịch riêng trong hồ sơ. Nội dung kế hoạch và luận văn nên trình bày bằng tiếng Việt.

---

## 2. Đóng góp kỹ thuật và ứng dụng

### 2.1. Đóng góp chính: một pipeline AIOps có bằng chứng cho vận hành sự cố

Đề tài không xem việc gọi LLM hoặc số lượng agent là đóng góp. Đóng góp chính là thiết kế và triển khai một pipeline có thể dùng trong quy trình vận hành thử nghiệm, trong đó các agent chuyên trách thu thập evidence song song và Aggregator xếp hạng nguyên nhân dựa trên:

1. Thứ tự thời gian của các sự kiện.
2. Quan hệ phụ thuộc giữa các dịch vụ.
3. Bằng chứng từ chỉ số.
4. Bằng chứng từ nhật ký.
5. Bằng chứng từ phép kiểm tra dịch vụ và mạng.
6. Thay đổi triển khai gần đây.
7. Bằng chứng mâu thuẫn làm giảm điểm.

Mô hình điểm dự kiến:

```text
Điểm nguyên nhân gốc =
    trọng số thời gian       * điểm thứ tự thời gian
  + trọng số phụ thuộc       * điểm quan hệ phụ thuộc
  + trọng số chỉ số          * điểm bằng chứng chỉ số
  + trọng số nhật ký         * điểm bằng chứng nhật ký
  + trọng số kiểm tra        * điểm bằng chứng kiểm tra
  + trọng số thay đổi        * điểm thay đổi gần đây
  - trọng số mâu thuẫn       * điểm bằng chứng mâu thuẫn
```

Các trọng số phải được ghi rõ và cố định trước khi chạy tập đánh giá. Aggregator là thành phần áp dụng công thức sau khi nhận kết quả fan-out; specialist agent không tự quyết định RCA cuối cùng. Việc loại bỏ từng thành phần được dùng để kiểm tra giá trị thực tế của thiết kế, không nhằm tuyên bố một thuật toán mới. Không lấy độ tin cậy do LLM tự sinh làm kết quả chuẩn.

Đóng góp của khóa luận được đánh giá chủ yếu ở các mặt sau:

1. Cải thiện quy trình xử lý cảnh báo và điều tra sự cố.
2. Khả năng gom nhiều tín hiệu thành một incident có timeline và phạm vi ảnh hưởng.
3. Khả năng cung cấp RCA có mã bằng chứng để con người kiểm tra.
4. Khả năng thực hiện playbook thử nghiệm qua approval, allowlist và verification.
5. Khả năng tái lập các kịch bản và đo lường kết quả bằng dữ liệu thô.

### 2.2. Vai trò của LLM

LLM chỉ là thành phần hỗ trợ suy luận và trình bày:

- Tóm tắt sự cố.
- Giải thích các bằng chứng đã thu thập.
- Đề xuất giả thuyết hoặc bước điều tra tiếp theo.
- Tìm quy trình xử lý và sự cố tương tự.
- Chuyển kết quả có cấu trúc thành báo cáo dễ đọc.

LLM không được:

- Tự quyết định hành động thay đổi hệ thống.
- Tự tạo lệnh `shell`, `SSH`, mạng hoặc AWS.
- Tự bỏ qua chính sách và phê duyệt.
- Tự coi một giả thuyết là sự thật tuyệt đối.

### 2.3. Giá trị ứng dụng và giới hạn triển khai

Sau khi hoàn thành phần chẩn đoán, hệ thống có thể lập kế hoạch khôi phục có kiểm soát:

```text
Chẩn đoán
  -> Đề xuất hành động
  -> Kiểm tra chính sách
  -> Xin phê duyệt
  -> Chạy kịch bản Ansible có sẵn
  -> Xác minh kết quả
  -> Khôi phục phiên bản hoặc chuyển người xử lý
```

Phần này là một phần của giá trị ứng dụng. Tuy nhiên, remediation chỉ được dùng để chứng minh quy trình vận hành an toàn trong staging, không phải mục tiêu xây dựng hệ thống tự sửa lỗi production hoàn chỉnh.

Khóa luận được phân bổ trọng tâm theo hướng:

- Khoảng 60% cho thiết kế và triển khai hệ thống.
- Khoảng 25% cho kịch bản lỗi, benchmark và đo lường vận hành.
- Khoảng 15% cho phân tích scoring, ablation và cơ sở lý thuyết.

---

## 3. Đối chiếu với kho mã hiện tại

### 3.1. Bốn lớp đang có

| Lớp | Thư mục hiện tại | Trách nhiệm |
|---|---|---|
| Hạ tầng đám mây | `terraform/` | VPC, subnet, Security Group, EIP và EC2 |
| Cấu hình máy chủ | `ansible/` | Docker, Prometheus, Alertmanager, Grafana và exporter |
| Ứng dụng và bản phát hành | `release/`, `demo-web/`, `agent_src/` | Các image và Docker Compose |
| Phân phối | `.github/workflows/`, `automation/` | Kiểm thử, triển khai theo vai trò, kiểm tra sức khỏe và khôi phục bản phát hành |

Không trộn trách nhiệm giữa các lớp:

- Terraform quản lý tài nguyên AWS.
- Ansible quản lý cấu hình máy chủ và kịch bản xử lý.
- `release/` là nguồn chuẩn của môi trường chạy.
- `automation/app-release-deploy.sh` là cổng duy nhất cho triển khai bản phát hành.

### 3.2. Các máy chủ hiện tại

```text
monitor-ai-01  -> Prometheus, Alertmanager, Grafana, Redis, AI Agent, Celery
bank-core-01   -> Payment API, PostgreSQL, PostgreSQL exporter
bank-web-01    -> Frontend/Nginx
```

Môi trường thử nghiệm và môi trường sản xuất chạy đồng thời trên cùng EC2 với cổng khác nhau:

```text
Thử nghiệm: AI Agent 18000, API 18080, Frontend 18081
Sản xuất:   AI Agent 8000,  API 8080,  Frontend 3000
```

Không thay đổi cơ chế tách cổng này trong phạm vi khóa luận.

### 3.3. Những thành phần AI đã có

- `agent_src/core/main.py`: FastAPI, `/webhook`, Telegram webhook, chỉ số, API quy trình xử lý và kiểm tra sức khỏe.
- `agent_src/core/tasks.py`: Celery xử lý cảnh báo, loại bỏ trùng, chẩn đoán xác định, RAG, Gemini, Telegram và xác minh.
- `agent_src/core/rag_engine.py`: ChromaDB với `standard_runbooks` và `incident_memory`.
- `agent_src/core/runbook_registry.py`: quản lý bản nháp quy trình xử lý và phản hồi quản trị viên.
- `agent_src/tools/diag_tools.py`: công cụ thử nghiệm cho chỉ số máy, tiến trình, nhật ký, ping, DNS, HTTP và kết nối cơ sở dữ liệu.
- `agent_src/tools/prometheus_check.py`: kiểm tra Prometheus.
- `agent_src/monitoring/service_monitor.py`: theo dõi cổng và trạng thái dịch vụ.
- `agent_src/monitoring/log_watcher.py`: theo dõi nhật ký và gửi cảnh báo.

### 3.4. Những khả năng đã có

1. Nhận cảnh báo Alertmanager qua `/webhook`.
2. Đưa công việc vào Redis và Celery để webhook không bị chặn lâu.
3. Dùng fingerprint hoặc hash nhãn để xác định cảnh báo.
4. Loại bỏ cảnh báo lặp bằng Redis, có dự phòng trong bộ nhớ.
5. Giới hạn số lần gọi Gemini để tránh cạn hạn mức.
6. Có quy trình xác định cho `PostgreSQLDown`, `PaymentAPIEndpointDown`, `FrontendAPIProxyDown`, `RedisDown`, cảnh báo tài nguyên và container.
7. Có hai trạng thái quan trọng của Payment API:

   ```text
   /api/health  -> kiểm tra tiến trình còn sống
   /api/ready   -> kiểm tra cả kết nối PostgreSQL
   ```

8. Có thông báo Telegram, xác minh sau cảnh báo và phản hồi của quản trị viên.

### 3.5. Khoảng trống cần giải quyết

1. Cảnh báo vẫn chủ yếu được xử lý riêng lẻ, chưa có sự cố tổng hợp theo quan hệ phụ thuộc.
2. Chưa có lược đồ sự kiện chung cho chỉ số, nhật ký, phép kiểm tra và thay đổi.
3. Redis đang dùng cho hàng đợi, thời gian nguội và ngữ cảnh tạm thời; chưa phải nơi lưu trữ sự cố lâu dài.
4. ChromaDB phù hợp cho tìm kiếm, chưa phù hợp làm nguồn dữ liệu giao dịch của vòng đời sự cố.
5. Chưa có kho cấu trúc phụ thuộc được phiên bản hóa.
6. `diag_tools.py` mới là bộ công cụ thử nghiệm; chưa có hợp đồng công cụ, phân quyền, giới hạn đích đến và nhật ký kiểm toán đầy đủ.
7. Chưa có công thức tính điểm nguyên nhân gốc dựa trên nhiều loại bằng chứng.
8. Chưa có máy trạng thái bền vững cho sự cố.
9. Chưa có quy trình khôi phục có kiểm soát tách khỏi triển khai bản phát hành.
10. Chưa có bộ tạo lỗi, dữ liệu chuẩn và phép so sánh định lượng.

### 3.6. Kiến trúc mục tiêu Multi-AZ và Multi-Agent

Phạm vi triển khai thực tế của khóa luận là một workload đại diện trên AWS hai AZ:

```text
Internet
   -> Public ALB (AZ-a, AZ-b)
   -> Web instances/ASG (AZ-a, AZ-b)
   -> Internal ALB
   -> Payment API instances/ASG (AZ-a, AZ-b)
   -> RDS PostgreSQL Multi-AZ
   -> ElastiCache Redis replication group
```

Lớp AIOps giữ vai trò control plane. Các agent chuyên trách dùng chung `incident context` và bị điều phối bởi lõi quản lý sự cố:

```text
Alertmanager / logs / metrics / probes
                    |
          Incident Orchestrator
                    |
          Celery group/chord fan-out
     +------+------+------+------+------+
     |      |      |      |      |      |
 Correlation Dependency Metric Log Probe Change/Runbook
     +------+------+------+------+------+
                    |
              Aggregator
       merge evidence + RCA scoring
                    |
       RAG/LLM explanation + proposal
                    |
         Policy + human approval
                    |
       Typed Ansible staging executor
                    |
             Verification Agent
```

Chỉ web/API workload bắt buộc có dự phòng giữa hai AZ. AI control plane, Celery, Redis, Prometheus, control-plane-db và ChromaDB có thể giữ một node trong phạm vi khóa luận, nhưng phải có graceful degradation, cảnh báo rõ ràng và được ghi nhận là giới hạn kiến trúc. Không tuyên bố toàn hệ thống không có single point of failure.

---

## 4. Phạm vi khóa luận khoa học ứng dụng

### 4.1. Giai đoạn A - Lát cắt vận hành cốt lõi, bắt buộc

```text
Cảnh báo
  -> Chuẩn hóa
  -> Loại bỏ trùng
  -> Tương quan
  -> Cấu trúc phụ thuộc
  -> Bằng chứng
  -> Xếp hạng nguyên nhân gốc
  -> Phạm vi ảnh hưởng
  -> Báo cáo Telegram/Web
```

Đây là lát cắt ứng dụng trung tâm. Phải hoàn thành và chạy được qua API trước khi xây giao diện hoặc phần tự động xử lý.

Để không lệch khỏi đề tài chính thức, lát cắt này vẫn phải thể hiện ba năng lực ở mức phù hợp:

1. **Đa nút:** thu thập và tương quan tín hiệu từ các node/role frontend, payment-api và monitor.
2. **Phát hiện bất thường chủ động:** bổ sung ít nhất một detector đơn giản trên time window của metric, dùng như một nguồn tín hiệu bổ sung cho alert rule tĩnh. Detector không phải trọng tâm thuật toán riêng.
3. **Tự phục hồi có kiểm soát:** chạy một số playbook staging có allowlist, approval và verification; không tự động sửa production.

### 4.2. Giai đoạn B - Vận hành an toàn, phần ứng dụng

```text
Chẩn đoán
  -> Kế hoạch khôi phục
  -> Kiểm tra chính sách
  -> Phê duyệt con người
  -> Kịch bản xử lý trên môi trường thử nghiệm
  -> Xác minh
  -> Khôi phục hoặc chuyển người xử lý
```

Chỉ chạy hành động trên môi trường thử nghiệm. Không tự động sửa môi trường sản xuất.

### 4.3. Giai đoạn C - Đánh giá khả năng áp dụng, bắt buộc cho khóa luận

```text
Tạo lỗi có kiểm soát
  -> Dữ liệu chuẩn
  -> Chạy các phương pháp so sánh
  -> Tính chỉ số
  -> Loại bỏ từng thành phần để kiểm tra
  -> Phân tích sai sót
```

### 4.4. Không thuộc phạm vi chính

- Kafka, Neo4j, Temporal, Kubernetes, multi-region và số lượng agent lớn.
- HA tuyệt đối cho mọi thành phần control plane và tự động xử lý production.
- Tự thay đổi VPC, subnet, route table, Security Group, IAM, firewall hoặc BGP.
- Lệnh SSH, shell, `kubectl`, `terraform apply` hoặc AWS do LLM tự tạo.
- Dự đoán sự cố trước khi xảy ra.
- Tự động thay đổi cấu hình mạng.

Các nội dung trên chỉ đưa vào phần hướng phát triển sau này.

Multi-Agent trong phạm vi chính gồm các specialist agent cho correlation, dependency, metric/anomaly, log, probe và change/runbook, được chạy bằng Celery fan-out, cùng một Aggregator để hợp nhất. Remediation và Verification là các cổng chuyên biệt; không trao quyền shell hoặc AWS trực tiếp cho LLM.

---

## 5. Kịch bản trung tâm và tiêu chí hoàn thành

### 5.1. Kịch bản chuỗi lỗi PostgreSQL

Khi dừng container `postgres-staging` trong Docker Compose:

```text
PostgreSQLDown
PaymentAPIEndpointDown
FrontendAPIProxyDown
              -> một sự cố
```

Hệ thống phải:

1. Nhận payload tại `/webhook`.
2. Chuẩn hóa thành sự kiện có mã sự kiện, fingerprint, môi trường, dịch vụ và thời gian.
3. Loại bỏ payload lặp.
4. Nhận ra ba cảnh báo thuộc cùng một chuỗi lỗi.
5. Dùng cấu trúc phụ thuộc:

   ```text
   Frontend -> Payment API -> PostgreSQL
                         \-> Redis
   ```

6. Thu thập trạng thái dịch vụ, `/api/ready`, Prometheus, nhật ký và thứ tự thời gian.
7. Xếp hạng `PostgreSQL process stopped` cao nhất.
8. Tính Payment API và Frontend là thành phần bị ảnh hưởng.
9. Gửi báo cáo có bằng chứng, điểm số, mức chưa chắc chắn và đề xuất.
10. Nếu bật phần xử lý an toàn, xin phê duyệt rồi chạy kịch bản khởi động lại PostgreSQL trên môi trường thử nghiệm.
11. Kiểm tra PostgreSQL, Payment API, Frontend và thời gian ổn định.
12. Chuyển sang `RESOLVED` chỉ khi các điều kiện sau xử lý đạt yêu cầu.
13. Nếu kiểm tra thất bại, khôi phục nếu có cách an toàn; nếu không thì chuyển người xử lý.

### 5.2. Kịch bản phụ 1: độ trễ ứng dụng

Tạo truy vấn cơ sở dữ liệu chậm hoặc làm đầy nhóm kết nối. Hệ thống phải phân biệt:

```text
Chỉ số cơ sở dữ liệu tăng trước -> độ trễ API tăng sau
```

với lỗi mạng:

```text
Mất gói hoặc lỗi giao diện mạng tăng trước -> nhiều dịch vụ hết thời gian chờ sau
```

Mục tiêu của kịch bản này là chứng minh giá trị của thứ tự thời gian và hợp nhất bằng chứng.

### 5.3. Kịch bản phụ 2: an toàn và kiểm tra thất bại

- Yêu cầu xóa EC2 hoặc sửa Security Group phải bị chính sách từ chối.
- Kịch bản xử lý trả về thành công nhưng API vẫn lỗi phải chuyển sang `FAILED` hoặc `ESCALATED`, không được chuyển sang `RESOLVED`.

### 5.4. Điều kiện hoàn thành kịch bản trung tâm

- Một chuỗi lỗi tạo đúng một sự cố.
- Nguyên nhân gốc đứng đầu đúng theo dữ liệu chuẩn.
- Báo cáo có mã bằng chứng và phạm vi ảnh hưởng.
- Không có hành động thay đổi trước khi qua chính sách và phê duyệt.
- Kịch bản chỉ chạy đúng mục tiêu thử nghiệm trong danh sách cho phép.
- Kiểm tra thất bại không tạo trạng thái đã giải quyết giả.
- Có thể xem lại dòng thời gian và nhật ký kiểm toán.
- Có thể chạy lại kịch bản và lưu kết quả thành tệp thực nghiệm.

---

## 6. Kiến trúc đề xuất

```text
Prometheus / Alertmanager / Loki / phép kiểm tra
                         |
                         v
                 Bộ chuẩn hóa sự kiện
                         |
                         v
                 Lõi quản lý sự cố
             loại trùng / tương quan / trạng thái
                    /                    \
                   v                      v
          Cấu trúc phụ thuộc        Kho bằng chứng
                   \                    /
                    v                  v
                  Aggregator
       merge evidence + bộ tính điểm RCA
                          |
                          v
                  RAG/LLM giải thích
                         |
                         v
                 Kế hoạch + chính sách
                    /             \
                   v               v
             Phê duyệt       Kịch bản Ansible thử nghiệm
                                   |
                                   v
                              Xác minh
```

### 6.1. Lược đồ sự kiện chung

Mọi nguồn phải chuyển về lược đồ có phiên bản:

```json
{
  "schema_version": "1.0",
  "event_id": "evt-uuid",
  "correlation_id": "corr-uuid",
  "incident_id": null,
  "source": "prometheus",
  "event_type": "service_health_failed",
  "status": "firing",
  "observed_at": "2026-08-21T10:00:00Z",
  "received_at": "2026-08-21T10:00:02Z",
  "environment": "staging",
  "host_id": "bank-core-01",
  "service_id": "payment-api",
  "component_id": "postgres-staging",
  "severity": "critical",
  "labels": {"alertname": "PostgreSQLDown"},
  "signal": {"name": "pg_up", "value": 0, "threshold": 1},
  "fingerprint": "sha256:..."
}
```

Phải phân biệt thời điểm quan sát và thời điểm nhận. Không đưa bí mật, thông tin xác thực hoặc nhật ký chưa che dữ liệu nhạy cảm vào LLM.

### 6.2. Máy trạng thái sự cố

```text
RECEIVED -> CORRELATING -> OPEN -> INVESTIGATING -> AGGREGATING -> DIAGNOSED
         -> PLANNED -> AWAITING_APPROVAL -> APPROVED
         -> EXECUTING -> VERIFYING -> RESOLVED

PLANNED -> REJECTED
EXECUTING / VERIFYING -> FAILED -> ESCALATED
RESOLVED -> REOPENED
```

Chỉ Verification Agent được tạo trạng thái `RESOLVED`. Mỗi lần chuyển trạng thái phải có người thực hiện, lý do, thời gian và nhật ký kiểm toán. Nếu một specialist timeout hoặc lỗi, Aggregator phải ghi nhận partial evidence và uncertainty; nếu không đủ evidence thì chuyển `FAILED` hoặc `ESCALATED`, không tự suy đoán.

### 6.3. Mô hình cấu trúc phụ thuộc

Phiên bản tối thiểu dùng một cơ sở dữ liệu riêng cho hệ thống quản lý sự cố, với các nhóm bảng:

```text
hosts
services
components
dependencies
service_criticality
business_capabilities
topology_versions
```

Phần cấu trúc ban đầu được khai báo rõ ràng, chưa cần tự động phát hiện:

```yaml
services:
  frontend:
    depends_on: [payment-api]
  payment-api:
    depends_on: [postgres, redis]
```

Mỗi phiên bản cấu trúc phụ thuộc phải có thời điểm hiệu lực, môi trường và người quản lý.

### 6.4. Mô hình bằng chứng

```text
evidence_id
incident_id
fanout_run_id
agent_name
kind: metric | log | probe | topology | change | runbook
source
query_or_reference
observed_at
value
freshness
quality
supports_hypotheses
contradicts_hypotheses
```

Các giả thuyết ban đầu của sự cố PostgreSQL:

```text
H1: Tiến trình PostgreSQL bị dừng
H2: Máy chủ cạn tài nguyên
H3: Ổ đĩa đầy
H4: Mạng không kết nối được
H5: Đang bảo trì theo kế hoạch
```

Bộ tính điểm sử dụng thứ tự thời gian, quan hệ phụ thuộc, chỉ số, nhật ký, phép kiểm tra, thay đổi gần đây và bằng chứng mâu thuẫn. LLM chỉ giải thích kết quả và nêu điểm chưa chắc chắn.

---

## 7. Công cụ điều tra và ranh giới an toàn

### 7.1. Công cụ hiện có

`agent_src/tools/diag_tools.py` hiện có các khả năng thử nghiệm:

- Thu thập chỉ số CPU, bộ nhớ và ổ đĩa.
- Liệt kê tiến trình.
- Đọc nhật ký theo danh sách cho phép.
- Thu thập chỉ số mạng.
- Ping, phân giải DNS và kiểm tra HTTP.
- Kiểm tra kết nối cơ sở dữ liệu.

`agent_src/tools/prometheus_check.py` hỗ trợ đọc Prometheus. Các hàm này sẽ được bọc lại bằng hợp đồng công cụ mới, không đưa trực tiếp toàn bộ hàm thử nghiệm cho LLM.

### 7.2. Cổng công cụ cần xây

Mỗi công cụ phải khai báo:

```text
tên và phiên bản
mục đích
lược đồ đầu vào
mục tiêu được phép
chỉ đọc hay không
vai trò được phép gọi
thời gian chờ
giới hạn tần suất
lược đồ đầu ra
chất lượng bằng chứng
```

Các công cụ chỉ đọc của phiên bản tối thiểu được phân nhóm theo agent để enforce least privilege:

```text
get_service_status()
get_container_status()
query_prometheus()
query_loki()
get_host_metrics()
get_service_dependencies()
get_topology_neighbors()
get_recent_changes()
run_http_probe()
run_network_probe()
search_runbooks()
search_similar_incidents()
```

Phân nhóm gọi công cụ:

```text
Correlation/Dependency Agent: get_service_dependencies, get_topology_neighbors
Metric Agent: query_prometheus, get_host_metrics
Log Agent: query_loki
Probe Agent: get_service_status, get_container_status, run_http_probe, run_network_probe
Change/Runbook Agent: get_recent_changes, search_runbooks, search_similar_incidents
```

Không cung cấp cho LLM các công cụ chung như `exec`, `ssh`, `bash`, `aws`, `kubectl` hoặc Terraform.

### 7.3. Phân quyền

| Thành phần | Được phép |
|---|---|
| Lõi xác định | Lược đồ, loại trùng, tương quan, tính điểm, chính sách, trạng thái và xác minh |
| LLM | Tóm tắt, giải thích, giả thuyết và đề xuất điều tra chỉ đọc |
| Quản trị viên | Phê duyệt hoặc từ chối hành động trong phạm vi được cấp |
| Bộ thực thi Ansible | Chạy kịch bản đã có phiên bản và danh sách mục tiêu cho phép |
| Trí tuệ nhân tạo | Không sửa hạ tầng, mạng, bảo mật hoặc tự tạo lệnh |

### 7.4. Giới hạn điều tra

- Tối đa 90 giây cho một lần fan-out và aggregation.
- Mỗi specialist có ngân sách công cụ riêng, mặc định tối đa 4 lần gọi read-only.
- Toàn pipeline có ngân sách LLM bảo thủ; giữ `GEMINI_MAX_ATTEMPTS=1` và `GEMINI_MAX_REMOTE_CALLS=1` mặc định.
- Aggregator ưu tiên scoring deterministic; LLM chỉ giải thích hoặc chuẩn hóa proposal.
- Hết giới hạn, specialist timeout hoặc lỗi thì ghi nhận partial evidence và uncertainty; nếu không đủ evidence, chuyển người xử lý.

---

## 8. Khôi phục có kiểm soát

Đây là phần ứng dụng để chứng minh hệ thống có thể hành động an toàn, không phải đóng góp nghiên cứu chính.

### 8.1. Phân biệt hành động

```text
Khôi phục     = khởi động lại, tải lại hoặc thử lại để dịch vụ hoạt động
Khôi phục bản = quay về image hoặc cấu hình trước đó
Chuyển người  = không còn hành động an toàn hoặc xác minh thất bại
```

Khởi động lại PostgreSQL không phải là khôi phục bản. Nếu khởi động lại thất bại, hệ thống chỉ được thử lại tối đa một lần nếu kịch bản cho phép, sau đó chuyển người xử lý.

### 8.2. Kịch bản xử lý của phiên bản tối thiểu

Chỉ chạy trên môi trường thử nghiệm:

1. Khởi động lại exporter.
2. Khởi động lại Celery worker thử nghiệm.
3. Khởi động lại Payment API thử nghiệm.
4. Khởi động lại PostgreSQL thử nghiệm.
5. Khôi phục image ứng dụng thử nghiệm về thẻ phát hành trước đó.
6. Chuyển người xử lý.

Mỗi kịch bản phải có:

```text
mã và phiên bản
danh sách mục tiêu
danh sách môi trường
mức rủi ro
có cần phê duyệt hay không
điều kiện trước khi chạy
điều kiện sau khi chạy
thời gian chờ
số lần thử tối đa
cách khôi phục hoặc chuyển người
```

Bộ thực thi Ansible chỉ nhận mã kịch bản và tham số có kiểu. Không nhận chuỗi lệnh từ LLM.

### 8.3. Phê duyệt

Quản trị viên phải thấy:

- Sự cố và dòng thời gian.
- Các giả thuyết và bằng chứng.
- Dịch vụ bị ảnh hưởng và phạm vi ảnh hưởng.
- Kịch bản, mục tiêu, môi trường và phiên bản chính xác.
- Rủi ro, kết quả mong đợi và thời gian gián đoạn dự kiến.
- Điều kiện trước, điều kiện sau và cách khôi phục.
- Thời hạn và mã băm của kế hoạch.

Phê duyệt hết hạn, yêu cầu phê duyệt bị gửi lại hoặc mã băm kế hoạch thay đổi đều phải bị từ chối.

### 8.4. Xác minh

Với hành động khởi động lại PostgreSQL:

```text
Kiểm tra PostgreSQL = khỏe mạnh
Payment API /api/ready = 200
Kiểm tra Frontend = thành công
Tỷ lệ lỗi dưới ngưỡng
Độ trễ trở về gần mức trước sự cố
Ổn định trong 60 giây
```

Không đánh dấu đã giải quyết chỉ vì Ansible trả mã thoát bằng 0.

---

## 9. Lưu trữ dữ liệu

### 9.1. Cơ sở dữ liệu riêng cho hệ thống quản lý sự cố

Không dùng PostgreSQL của Payment API làm nơi lưu sự cố. Khi PostgreSQL của ứng dụng bị dừng, hệ thống quản lý sự cố vẫn phải giữ được dòng thời gian và nhật ký.

Trong môi trường phát triển và thử nghiệm cần có hai cơ sở dữ liệu:

```text
workload-db      -> cơ sở dữ liệu của Payment API
control-plane-db -> sự cố, cấu trúc phụ thuộc, kiểm toán và dữ liệu thí nghiệm
```

Các nhóm bảng chính:

```text
events
incidents
incident_events
incident_timeline
hypotheses
evidence
investigation_runs
fanout_runs
agent_runs
aggregator_runs
tool_calls
services
dependencies
topology_versions
remediation_plans
actions
approvals
execution_runs
verification_runs
audit_log
incident_feedback
```

Dòng thời gian và nhật ký kiểm toán chỉ được ghi thêm, không sửa xóa. Timeline phải ghi được `FANOUT_STARTED`, `AGENT_COMPLETED`, `AGENT_FAILED`, `AGGREGATED`, `APPROVAL_REQUESTED`, `EXECUTION_STARTED`, `VERIFICATION_PASSED` hoặc `VERIFICATION_FAILED`. Mọi sự kiện, agent run và hành động có mã duy nhất cùng khóa chống thực hiện lặp.

### 9.2. RAG và trí nhớ sự cố

Giữ ChromaDB hiện tại cho:

- `standard_runbooks`: các tài liệu quy trình xử lý đã được xem xét.
- `incident_memory`: tóm tắt sự cố và phản hồi dùng cho tìm kiếm tương tự.

PostgreSQL có cấu trúc là nguồn dữ liệu chính cho vòng đời, bằng chứng, phê duyệt và kết quả hành động. ChromaDB không được là nơi duy nhất lưu trạng thái sự cố.

### 9.3. Bổ sung vào Docker Compose

Môi trường phát triển hiện có cơ sở dữ liệu ứng dụng và Redis. Cần thêm cơ sở dữ liệu riêng cho hệ thống quản lý sự cố, không dùng chung volume hoặc lược đồ.

---

## 10. Telegram và bảng điều khiển

### 10.1. Telegram

Telegram được giữ lại vì codebase đã có webhook, kiểm tra `TELEGRAM_CHAT_ID`, phản hồi quản trị viên và thông báo xác minh.

Vai trò mới:

```text
SỰ CỐ #INC-001
Nguyên nhân có khả năng cao: tiến trình PostgreSQL bị dừng
Bằng chứng: pg_up=0, API sẵn sàng=503, Frontend lỗi sau đó
Báo cáo Aggregator: top-1 score=..., evidence IDs=E-001,E-002,E-003
Bị ảnh hưởng: Payment API, Frontend
Hành động: khởi động lại PostgreSQL thử nghiệm
Rủi ro: trung bình | plan_hash: ...

[PHÊ DUYỆT] [TỪ CHỐI] [XEM]
```

Telegram là kênh tương tác nhanh. Bảng điều khiển web là nơi xem đầy đủ bằng chứng và dòng thời gian.

### 10.2. Bảng điều khiển tối thiểu

Không xây một Grafana khác. Chỉ xây màn hình thông tin vận hành:

- Danh sách sự cố và trạng thái.
- Chi tiết sự cố: dòng thời gian, bằng chứng, giả thuyết, điểm số và ảnh hưởng.
- Cấu trúc phụ thuộc và phạm vi ảnh hưởng.
- Phê duyệt: rủi ro, hành động, mục tiêu và xác minh.
- Nhật ký kiểm toán và kết quả thí nghiệm.

Bảng điều khiển chỉ triển khai sau khi phần lõi có thể chạy bằng API và dữ liệu phát lại. Giao diện không được làm chậm phần nghiên cứu chính.

---

## 11. Bộ thí nghiệm và đánh giá

### 11.1. Kịch bản chính

Ba kịch bản cần chạy đầy đủ từ đầu đến cuối:

1. Chuỗi lỗi PostgreSQL.
2. Độ trễ ứng dụng do cơ sở dữ liệu hoặc nhóm kết nối.
3. Xác minh thất bại sau khi xử lý.

### 11.2. Kịch bản phụ

Chỉ dùng để đánh giá phát hiện, tương quan hoặc chẩn đoán:

```text
Redis bị dừng
CPU tăng đột biến
Thiếu bộ nhớ
Ổ đĩa gần đầy
Mất gói mạng
Alertmanager gửi lại cùng cảnh báo
LLM hoặc cổng công cụ không hoạt động
```

Mỗi kịch bản phải có cách tạo lỗi, nguyên nhân chuẩn, phạm vi ảnh hưởng chuẩn, thời điểm bắt đầu/kết thúc và cách phục hồi dự kiến.

### 11.3. Các phương pháp so sánh trong quy trình vận hành

| Mã | Phương pháp |
|---|---|
| B0 | Quy trình hiện tại: cảnh báo và Telegram riêng lẻ, không tương quan |
| B1 | Tương quan bằng luật xác định |
| B2 | LLM/RAG từ cảnh báo và ngữ cảnh, không có điểm cấu trúc phụ thuộc |
| P | Hợp nhất bằng chứng có nhận biết cấu trúc phụ thuộc, LLM chỉ giải thích |

### 11.4. Chỉ số đánh giá khả năng áp dụng

Các chỉ số được ưu tiên theo câu hỏi: hệ thống có giúp con người vận hành nhanh hơn, đúng hơn và an toàn hơn không?

**Hiệu quả vận hành:**

- Thời gian phát hiện sự cố.
- Thời gian điều tra.
- MTTD và MTTR trong từng kịch bản.
- Số cảnh báo và số incident cần con người xử lý.
- Số lần gọi LLM và công cụ trên mỗi incident.
- Thời gian fan-out, thời gian Aggregator và tỷ lệ specialist hoàn thành đúng hạn.
- Tỷ lệ fan-out thành công và tỷ lệ incident phải xử lý với partial evidence.

**Tương quan:**

- Tỷ lệ nén cảnh báo thành sự cố.
- Độ chính xác tương quan.
- Tỷ lệ gom nhầm.
- Tỷ lệ loại bỏ cảnh báo trùng.

**Chẩn đoán:**

- Độ chính xác nguyên nhân gốc đứng đầu và trong ba vị trí đầu.
- Mức độ bao phủ bằng chứng.
- Tỷ lệ nhận định không có bằng chứng.
- Độ chính xác phạm vi ảnh hưởng.
- Độ phù hợp giữa điểm tin cậy và kết quả thật.

**An toàn:**

- Số hành động trái phép.
- Số lần chạy sai mục tiêu.
- Số lần vượt qua phê duyệt.
- Tỷ lệ xác minh thành công.
- Tỷ lệ đánh dấu đã giải quyết sai.
- Độ bao phủ evidence khi một hoặc nhiều specialist bị timeout.

Không ghi trước các con số trong luận văn như thể đó là kết quả. Mọi kết quả phải được sinh từ dữ liệu thô và chương trình tính chỉ số. Các chỉ số học thuật như top-1, top-3 và ablation là bằng chứng bổ trợ cho khả năng áp dụng, không phải mục tiêu duy nhất của khóa luận.

### 11.5. Thí nghiệm loại bỏ thành phần

Để chứng minh từng thành phần có giá trị, so sánh:

```text
P-đầy-đủ: cấu trúc + thời gian + chỉ số + nhật ký + kiểm tra + thay đổi
P-bỏ-cấu-trúc
P-bỏ-nhật-ký
P-bỏ-thứ-tự-thời-gian
P-chỉ-dùng-luật
P-chỉ-dùng-LLM
```

Thí nghiệm này có giá trị học thuật hơn việc bổ sung thêm nhiều công nghệ.

---

## 12. Câu hỏi nghiên cứu và giả thuyết

### 12.1. Câu hỏi đánh giá ứng dụng

- **CH1:** Hệ thống có giảm số cảnh báo và incident trùng lặp cần con người xử lý so với quy trình hiện tại không?
- **CH2:** Hệ thống có giúp xác định nguyên nhân và phạm vi ảnh hưởng nhanh, đúng và có bằng chứng hơn không?
- **CH3:** Dependency và bằng chứng đa nguồn có cải thiện kết quả trong các kịch bản lỗi thực nghiệm không?
- **CH4:** Chính sách, phê duyệt và xác minh có ngăn được hành động sai, chạy sai mục tiêu và trạng thái giải quyết giả không?
- **CH5:** Hệ thống có duy trì hành vi an toàn khi LLM, Redis, nguồn quan sát hoặc control-plane database bị lỗi không?

### 12.2. Tiêu chí và giả thuyết đánh giá

- **G1:** Quy trình đề xuất giảm thời gian điều tra hoặc số thông báo thừa so với quy trình hiện tại.
- **G2:** Dependency và hợp nhất bằng chứng giúp RCA có bằng chứng và phạm vi ảnh hưởng chính xác hơn trong các kịch bản được kiểm thử.
- **G3:** Chính sách và phê duyệt ngăn hành động trái phép trong toàn bộ kiểm thử an toàn.
- **G4:** Xác minh sau xử lý phát hiện được trường hợp phục hồi giả mà mã thoát của playbook không phát hiện.
- **G5:** Khi một thành phần AI hoặc observability bị lỗi, hệ thống chuyển sang đường xác định hoặc chuyển người xử lý thay vì tự thực hiện hành động không an toàn.

---

## 13. Lộ trình thực hiện trong 12 tuần

### 13.1. Phân công cố định cho nhóm hai người

| Role | Trách nhiệm chính | Bàn giao bắt buộc |
|---|---|---|
| **Infrastructure Engineer** | Terraform VPC hai AZ, subnet, route, SG, ALB, compute, RDS/Redis, Ansible, Celery/Redis runtime, monitoring, deployment, allowlist executor và fault injection hạ tầng | Hạ tầng tái lập được, sơ đồ mạng, log triển khai, playbook typed trên staging, kịch bản node/AZ failure và bảng chi phí |
| **AI Engineer** | Event schema, Incident Core, correlation, specialist agents, Celery fan-out/chord, Aggregator, dependency, evidence, RCA scoring, RAG/LLM, approval gateway, Verification Agent và benchmark | API/schema có kiểm thử, incident timeline, agent/aggregator trace, báo cáo RCA có evidence, dữ liệu thí nghiệm và biểu đồ |

Hai thành viên cùng chịu trách nhiệm về thiết kế tổng thể, review chéo, tích hợp cuối tuần và viết luận văn. Không để một thành viên sở hữu độc quyền phần tích hợp hoặc dữ liệu đánh giá.

### 13.2. Nguyên tắc lập kế hoạch

- Mỗi tuần phải có một bản chạy được hoặc một artifact kiểm chứng được.
- Infrastructure Engineer không chờ toàn bộ AI hoàn thiện mới dựng hạ tầng; dùng health endpoint và payload giả lập để tích hợp sớm.
- AI Engineer không chờ Multi-AZ hoàn thiện mới xây incident pipeline; dùng Docker Compose và fixture để phát triển trước.
- Không chuyển sang UI nâng cao, self-healing mở rộng hoặc tối ưu LLM nếu kịch bản PostgreSQL trung tâm chưa chạy ổn định.
- Cuối mỗi tuần phải có review chéo, cập nhật dữ liệu thô và ghi nhận giới hạn.

### Tuần 1: Đóng băng baseline và chốt kiến trúc

**Infrastructure Engineer:**

- Kiểm tra region, hai AZ khả dụng và ngân sách.
- Vẽ kiến trúc VPC hai AZ gồm public/private subnet, ALB, compute và datastore.
- Quyết định rõ mô hình EC2/ASG, RDS Multi-AZ, ElastiCache và NAT Gateway.
- Tạo kế hoạch Terraform, chưa triển khai phá hủy hoặc thay thế tài nguyên đang chạy.

**AI Engineer:**

- Ghi lại luồng cảnh báo hiện tại từ `main.py` và `tasks.py`.
- Chốt event schema phiên bản `1.0` và incident context dùng chung giữa các agent.
- Tạo danh sách kịch bản và nguyên nhân chuẩn.
- Phát lại chuỗi lỗi PostgreSQL bằng payload giả lập.
- Đo phương pháp hiện tại: số cảnh báo, thời gian xử lý, số thông báo Telegram và số lần gọi LLM.

**Bàn giao chung:** báo cáo baseline, sơ đồ Multi-AZ, event schema, bảng phân công, danh sách scenario và bộ dữ liệu có thể chạy lại.

### Tuần 2: Nền tảng dữ liệu và network hai AZ

**Infrastructure Engineer:** public/private subnet, route table, SG, NAT và nền tảng ALB trên Terraform.

**AI Engineer:** event ingestion, chuẩn hóa alert, incident repository tối thiểu và contract test.

**Bàn giao:** hệ thống nhận được event chuẩn hóa; hạ tầng hai AZ có thể validate bằng Terraform.

### Tuần 3: Lõi quản lý sự cố

**Infrastructure Engineer:** dựng workload staging theo topology mới, giữ health endpoint và service naming ổn định.

**AI Engineer:** tạo incident, timeline, idempotency key và máy trạng thái bền vững.

**Bàn giao:** alert lặp không tạo incident lặp; các lần chuyển trạng thái có kiểm thử.

### Tuần 4: Load balancing và dependency graph

**Infrastructure Engineer:** đưa web/API lên ALB, kiểm thử target health và failover giữa hai AZ.

**AI Engineer:** khai báo dependency Frontend -> Payment API -> PostgreSQL/Redis và tính phạm vi ảnh hưởng.

**Bàn giao:** chuỗi lỗi được gắn vào topology; ALB loại được target unhealthy.

### Tuần 5: Datastore và khả năng chịu lỗi

**Infrastructure Engineer:** cấu hình RDS PostgreSQL Multi-AZ, Redis replication và backup/restore staging.

**AI Engineer:** tích hợp incident/control-plane storage tách khỏi workload database và tiếp tục lưu evidence.

**Bàn giao:** workload database lỗi không làm mất incident timeline; có log và bằng chứng failover.

### Tuần 6: Celery fan-out và specialist agents

**Infrastructure Engineer:** hoàn thiện service discovery/monitoring target cho các node hai AZ.

**AI Engineer:** cài đặt Celery `group/chord`, Correlation Agent, Dependency Agent, time window và detector metric đơn giản.

**Bàn giao:** ba cảnh báo trong chuỗi PostgreSQL trở thành một incident.

### Tuần 7: Evidence agents và Aggregator

**Infrastructure Engineer:** tạo và kiểm thử fault injection cho node, service, AZ/workload dependency.

**AI Engineer:** triển khai Metric, Log, Probe và Change/Runbook Agent; xây Aggregator, chuẩn hóa evidence và bộ tính điểm RCA deterministic.

**Bàn giao:** RCA có giả thuyết, evidence ID, điểm số, độ chưa chắc chắn và impact.

### Tuần 8: Aggregator explanation và LLM boundary

**Infrastructure Engineer:** chuẩn hóa deployment artifact và cơ chế rollback staging.

**AI Engineer:** tích hợp Aggregator với RAG và LLM chỉ để giải thích/propose output có schema; thêm policy gateway.

**Bàn giao:** LLM không tự sinh hoặc thực thi lệnh; proposal có policy input rõ ràng.

### Tuần 9: Approval, policy và remediation

**Infrastructure Engineer:** triển khai playbook Ansible staging cho restart/rollback có allowlist.

**AI Engineer:** approval Telegram, expiry, plan hash, audit log và hợp đồng typed executor.

**Bàn giao:** không có hành động thay đổi trước approval hợp lệ.

### Tuần 10: Verification Agent

**Infrastructure Engineer:** kiểm thử recovery và rollback trên workload hai AZ.

**AI Engineer:** triển khai Verification Agent, kiểm tra post-condition, trạng thái `RESOLVED/FAILED/ESCALATED` và lưu incident memory.

**Bàn giao:** mã thoát playbook thành công nhưng health vẫn lỗi phải bị phát hiện.

### Tuần 11: Benchmark và ablation

**Cả hai thành viên:**

- Chạy B0, B1, B2 và P trên các scenario đã chốt.
- Đo MTTD, MTTR, alert compression, RCA top-1/top-3, evidence coverage, recovery và safety.
- Chạy ablation cho dependency, timeline và evidence đa nguồn.

**Bàn giao:** dữ liệu thô, script tính chỉ số, bảng kết quả và phân tích sai sót.

### Tuần 12: Đóng gói và bảo vệ

- Hoàn thiện sơ đồ kiến trúc, trình tự, máy trạng thái và mô hình đe dọa.
- Viết báo cáo, giới hạn, chi phí và hướng phát triển.
- Quay trình diễn từ đầu đến cuối.
- Chạy toàn bộ kiểm tra tương đương CI.

**Bàn giao:** mã nguồn, Terraform/Ansible, dữ liệu, báo cáo, video và hướng dẫn tái lập.

---

## 14. Kiểm thử

### 14.1. Kiểm thử đơn vị

- Lược đồ sự kiện, che dữ liệu nhạy cảm, fingerprint và khóa chống lặp.
- Tương quan, duyệt cấu trúc phụ thuộc và tính phạm vi ảnh hưởng.
- Điểm nguyên nhân gốc, độ mới của bằng chứng và phạt mâu thuẫn.
- Chuyển trạng thái, chính sách và hết hạn phê duyệt.
- Bộ đánh giá điều kiện sau xử lý.

### 14.2. Kiểm thử tích hợp

- Alertmanager -> `/webhook` -> sự kiện chuẩn hóa -> cơ sở dữ liệu sự cố.
- Bộ kết nối Prometheus và Loki.
- Chuỗi lỗi PostgreSQL trên Docker Compose thử nghiệm.
- Xác thực phê duyệt Telegram.
- Kịch bản xử lý -> xác minh -> giải quyết hoặc chuyển người.
- Celery fan-out chạy các specialist song song và Aggregator vẫn trả kết quả khi một agent timeout.
- Aggregator không đủ evidence phải chuyển `ESCALATED`, không được chuyển sang `EXECUTING`.
- Specialist retry, task replay và chord callback phải idempotent.

### 14.3. Kiểm thử an toàn

- Chèn chỉ dẫn độc hại vào nhật ký hoặc tài liệu quy trình.
- Tham số công cụ giả hoặc mục tiêu ngoài danh sách cho phép.
- Gửi lại yêu cầu phê duyệt cũ.
- Thay đổi mã băm kế hoạch sau khi đã phê duyệt.
- Làm lộ bí mật trong ngữ cảnh LLM hoặc nhật ký kiểm toán.
- Yêu cầu hành động bị cấm.

### 14.4. Kiểm tra CI cần giữ

```text
kiểm tra lỗi cú pháp và tên chưa định nghĩa bằng ruff
kiểm thử agent_src
kiểm thử demo-web/backend
xây dựng ba image Docker
kiểm tra cấu hình Docker Compose phát hành
```

Bổ sung kiểm thử lược đồ, tương quan, chính sách và phát lại kịch bản khi từng giai đoạn hoàn thành.

---

## 15. An toàn và cách xử lý khi lỗi

### 15.1. Ranh giới tin cậy

```text
Webhook
  -> Tiếp nhận
  -> Lõi quản lý sự cố
  -> Cổng công cụ chỉ đọc
  -> Chính sách và phê duyệt
  -> Bộ thực thi kịch bản có kiểu
  -> Ứng dụng thử nghiệm
```

LLM không có thông tin xác thực đặc quyền. Cổng công cụ và bộ thực thi mới có quyền, với quyền tối thiểu và danh sách mục tiêu cho phép.

### 15.2. Quy tắc an toàn khi thành phần hỏng

| Thành phần lỗi | Phản ứng |
|---|---|
| LLM hết hạn mức hoặc không hoạt động | Dùng đường xác định nếu có; nếu không thì báo cáo và chuyển người |
| Redis lỗi | Giữ hệ thống giám sát; không tạo hành động thay đổi lặp |
| Cơ sở dữ liệu quản lý sự cố lỗi | Không thực hiện thay đổi; xếp hàng hoặc thử lại sự kiện an toàn |
| Cổng công cụ lỗi | Giữ sự cố mở; không bỏ qua bằng chứng |
| Telegram lỗi | Dùng giao diện web; không xem việc thiếu phê duyệt là đã phê duyệt |
| Kịch bản Ansible hết thời gian | Đánh dấu chưa rõ, xác minh hoặc chuyển người; không thử vô hạn |
| Xác minh thất bại | Khôi phục nếu có cách an toàn; nếu không thì chuyển người |
| Lõi quản lý sự cố khởi động lại | Tiếp tục từ trạng thái bền vững và khóa chống lặp |

Prometheus, Alertmanager và các thành phần giám sát phải tiếp tục hoạt động kể cả khi AI Agent, LLM, Redis hoặc lõi quản lý sự cố bị lỗi.

---

## 16. Cấu trúc khóa luận

1. **Bối cảnh và bài toán vận hành:** AIOps, cảnh báo thừa, khó khăn của kỹ sư và mục tiêu cải tiến.
2. **Cơ sở và yêu cầu hệ thống:** khả năng quan sát, tương quan sự kiện, dependency, RAG/LLM, approval và verification.
3. **Hệ thống hiện tại:** kiến trúc repo, luồng cảnh báo, loại trùng, thời gian nguội, RAG và hạn chế.
4. **Thiết kế giải pháp:** yêu cầu, lược đồ sự kiện, correlation, anomaly signal, dependency, evidence và safety boundary.
5. **Triển khai:** incident core, bộ kết nối, cơ sở dữ liệu, Telegram, playbook staging và verification.
6. **Đánh giá khả năng áp dụng:** kịch bản, quy trình hiện tại làm baseline, metric vận hành, kết quả và phân tích lỗi.
7. **Kết luận:** mức cải thiện, giới hạn triển khai, chi phí và hướng phát triển.

---

## 17. Ưu tiên khi thiếu thời gian

### Không được cắt

- Kịch bản chuỗi lỗi PostgreSQL.
- Lược đồ sự kiện chung.
- Lõi sự cố và cấu trúc phụ thuộc.
- Mô hình bằng chứng và bộ tính điểm nguyên nhân gốc.
- Dữ liệu chuẩn, phương pháp so sánh và đánh giá.
- Chính sách từ chối và kịch bản xác minh thất bại.
- Nhật ký kiểm toán và khả năng tái lập.

### Cắt trước

1. Giao diện web nâng cao; giữ API và Telegram.
2. Xử lý môi trường production; chỉ remediation trên staging.
3. Tự động xử lý lỗi mạng; giữ phần phát hiện và chẩn đoán.
4. HA tuyệt đối cho AI control plane; giữ graceful degradation và nêu giới hạn.
5. Theo dõi dấu vết đầy đủ; giữ chỉ số, nhật ký và phép kiểm tra.
6. Chuyển sang pgvector; giữ bộ kết nối ChromaDB.
7. Tự động học từ phản hồi.
8. Kafka, Neo4j, Temporal, Kubernetes, các agent ngoài nhóm specialist đã định nghĩa và dự đoán sự cố.

---

## 18. Danh sách kiểm tra trước khi bảo vệ

- [ ] Đề tài nêu rõ tương quan theo cấu trúc phụ thuộc và chẩn đoán dựa trên bằng chứng.
- [ ] Có phương pháp so sánh B0, B1, B2 và P.
- [ ] Có lược đồ sự kiện chung và cơ sở dữ liệu riêng cho lõi quản lý sự cố.
- [ ] Có chuỗi PostgreSQL: ba cảnh báo thành một sự cố.
- [ ] Có kết quả cấu trúc phụ thuộc và phạm vi ảnh hưởng.
- [ ] Có bộ tính điểm không phụ thuộc hoàn toàn vào độ tin cậy của LLM.
- [ ] Có mã bằng chứng và kiểm tra nhận định không có bằng chứng.
- [ ] Có thí nghiệm loại bỏ cấu trúc, thứ tự thời gian và loại bằng chứng.
- [ ] Có phê duyệt con người và chính sách từ chối hành động nguy hiểm.
- [ ] Có trường hợp xác minh thất bại không tạo trạng thái giải quyết giả.
- [ ] Có tạo lỗi, dữ liệu chuẩn, dữ liệu thô và chương trình tính chỉ số.
- [ ] Có kiểm thử chèn chỉ dẫn độc hại, chạy sai mục tiêu và gửi lại phê duyệt cũ.
- [ ] Hệ thống giám sát vẫn hoạt động khi AI, LLM hoặc Redis lỗi.
- [ ] Không commit thông tin xác thực, `.env`, Terraform state hoặc dữ liệu ChromaDB chạy thực tế.

---

## 19. Nguyên tắc triển khai từng giai đoạn

```text
Chốt hợp đồng dữ liệu
  -> Xây lát cắt dọc nhỏ nhất
  -> Kiểm thử đơn vị
  -> Kiểm thử tích hợp
  -> Kiểm thử kịch bản
  -> Thu thập dữ liệu thực nghiệm
  -> Cập nhật tài liệu
  -> Chạy kiểm tra CI
  -> Người hướng dẫn xem xét
```

Một giai đoạn chỉ hoàn thành khi có mã nguồn, kiểm thử, dữ liệu thực nghiệm và tài liệu tương ứng. Một ảnh chụp màn hình của trường hợp tốt không đủ làm bằng chứng cho khóa luận.

---

## 20. Ghi chú về những tên bắt buộc giữ nguyên

Các tên sau được giữ nguyên vì phải khớp với codebase hoặc công cụ thực tế:

- Tên thư mục, tệp, hàm và API như `agent_src/core/main.py`, `/webhook`, `PostgreSQLDown`.
- Tên sản phẩm và thư viện như Prometheus, Alertmanager, FastAPI, Redis, Celery, Gemini, ChromaDB, Docker, Ansible và Telegram.
- Tên biến môi trường như `GEMINI_MAX_ATTEMPTS`, `ALERT_AI_COOLDOWN_SECONDS`.
- Tên trạng thái máy như `OPEN`, `RESOLVED`, `FAILED`, `ESCALATED`.

Phần diễn giải xung quanh các tên kỹ thuật này được viết bằng tiếng Việt để người đọc hiểu đầy đủ bối cảnh và kế hoạch.
