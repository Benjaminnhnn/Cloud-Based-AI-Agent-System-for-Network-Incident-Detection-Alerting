# 🤖 AIOps Intelligent Agent System

Hệ thống AI Agent chuyên dụng để tự động phát hiện, chẩn đoán và đề xuất xử lý sự cố hạ tầng mạng và hệ thống dựa trên mô hình RAG (Retrieval-Augmented Generation) và Gemini LLM.

## 🏗️ Kiến trúc hệ thống

Hệ thống bao gồm 3 lớp chính:

### 1. Lớp Giám sát (Monitoring Layer)
*   **`monitoring/log_watcher.py`**: Theo dõi các file log hệ thống/ứng dụng thời gian thực. Phát hiện các từ khóa lỗi (ERROR, CRITICAL...) và gửi cảnh báo về Webhook.
*   **`monitoring/service_monitor.py`**: Kiểm tra trạng thái các Port dịch vụ (Nginx, DB, Redis...) và các chỉ số mạng (Packet loss, TCP connections).

### 2. Lớp Xử lý Trung tâm (Core AI Layer)
*   **`core/main.py`**: Server FastAPI tiếp nhận Alertmanager webhook tại `/webhook`, validate payload và enqueue task vào Redis/Celery.
*   **`core/tasks.py`**: Celery worker xử lý alert bất đồng bộ, gọi RAG/Gemini khi cần, gửi Telegram, lưu incident context và lên lịch verify sau sự cố.
*   **`core/rag_engine.py`**: Sử dụng **ChromaDB** để lưu trữ và truy vấn tri thức từ các Runbook (.md) và lịch sử các sự cố đã xử lý trước đó.
*   **`tools/diag_tools.py`**: Tập hợp các công cụ "cánh tay" để AI tự thực hiện các lệnh kiểm tra (ping, check metrics, read logs).

### 3. Lớp Tương tác (Integration Layer)
*   **Telegram Bot**: Gửi báo cáo phân tích, fallback message khi AI quota lỗi, thông báo resolved và kết quả verify cho quản trị viên.

## 🔄 Quy trình vận hành (Workflow)

1.  **Detect**: Các bộ Monitor phát hiện bất thường -> Gửi Alert qua Webhook `/webhook`.
2.  **Queue**: FastAPI enqueue `process_alerts_task` vào Redis để Celery worker xử lý, tránh webhook bị treo lâu.
3.  **Dedup/Cooldown**: Worker dùng fingerprint từ Alertmanager hoặc hash labels để bỏ qua alert lặp trong thời gian cooldown.
4.  **Retrieve**: AI Agent truy vấn RAG DB để tìm quy trình xử lý (Runbook) tương ứng.
5.  **Analyze**: Gemini LLM sử dụng dữ liệu RAG và có thể gọi `diag_tools`, nhưng số lần gọi được giới hạn để tránh vượt quota.
6.  **Notify & Verify**: Agent gửi hướng dẫn xử lý qua Telegram, lưu incident context vào Redis, sau đó lên lịch verify và lưu kết quả vào ChromaDB.

## 📝 Thay đổi gần đây & lý do

### Giảm số lần gọi Gemini cho mỗi alert

Thay đổi trong **`core/tasks.py`**:

*   `GEMINI_MAX_ATTEMPTS` mặc định giảm từ `3` xuống `1`.
*   `GEMINI_FALLBACK_MODELS` mặc định để rỗng, không tự động fallback sang model khác nếu không cấu hình rõ.
*   Thêm `GEMINI_MAX_REMOTE_CALLS`, mặc định `1`, để giới hạn số tool/function calls mà Gemini có thể kích hoạt trong một lần phân tích.
*   Rút gọn nội dung fallback analysis khi Gemini lỗi để tránh Telegram message quá dài.

Lý do:

*   Khi test kịch bản Nginx down, worker gọi Gemini nhiều lần liên tiếp và gặp `503 high demand` hoặc `429 RESOURCE_EXHAUSTED`.
*   Mỗi alert trước đây có thể gọi model chính nhiều lần, rồi fallback model nhiều lần, cộng thêm nhiều tool calls.
*   Giới hạn mặc định giúp giảm nguy cơ chạm quota free tier, giảm độ trễ và giữ pipeline alert ổn định hơn.

### Thêm cooldown/dedup cho alert lặp

Thay đổi trong **`core/tasks.py`** và **`core/main.py`**:

*   `core/main.py` nhận thêm field `fingerprint` optional từ Alertmanager.
*   Worker tạo identity theo `fingerprint`; nếu không có thì hash các labels quan trọng như `alertname`, `instance`, `job`, `service`, `target`.
*   Thêm Redis key dạng `alert-ai-cooldown:<identity>` với TTL `ALERT_AI_COOLDOWN_SECONDS`, mặc định `900` giây.
*   Nếu Redis không khả dụng, worker dùng in-memory cooldown fallback.
*   Alert `resolved` sẽ clear cooldown để lần firing mới sau recovery vẫn được xử lý.
*   Metric `aiops_alerts_processed_total` có thêm trạng thái `deduped`.

Lý do:

*   Alertmanager có thể gửi repeat notification, resolved notification hoặc webhook retry.
*   Không nên gọi Gemini lại cho cùng một alert đang firing trong thời gian ngắn.
*   Dedup giúp giảm spam Telegram, giảm queue backlog và giảm chi phí/quota Gemini.

### Cấu hình runtime liên quan

Các biến có thể cấu hình qua `.env`/GitHub Secrets nếu cần override default:

```env
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODELS=
GEMINI_MAX_ATTEMPTS=1
GEMINI_MAX_REMOTE_CALLS=1
ALERT_AI_COOLDOWN_SECONDS=900
ALERT_DEDUP_ENABLED=true
```

### Góp ý giải pháp qua Telegram

Khi Agent gửi báo cáo sự cố, tin nhắn sẽ có `ID` của incident và hướng dẫn:

```text
/feedback <incident_id> <giải pháp hoặc góp ý của admin>
```

Admin cũng có thể reply vào tin báo có dòng `ID: ...`; Agent sẽ lấy ID từ tin được reply và dùng nội dung reply làm góp ý.

Luồng xử lý:

*   FastAPI nhận tin tại `/telegram/webhook`.
*   Chỉ chat có `TELEGRAM_CHAT_ID` mới được gửi góp ý.
*   Agent lấy context incident từ Redis, đánh giá góp ý bằng Gemini nếu có API key.
*   Nếu góp ý đúng hoặc cần chỉnh nhẹ, Agent lưu bản đã duyệt/chỉnh vào ChromaDB để RAG dùng cho incident tương tự.
*   Nếu góp ý chưa phù hợp, Agent nhắn lại lý do và giải pháp thay thế an toàn hơn cho admin.

Để Telegram gọi được webhook, cần cấu hình `AI_AGENT_PUBLIC_URL` là URL HTTPS public của agent; startup sẽ đăng ký webhook tới:

```text
<AI_AGENT_PUBLIC_URL>/telegram/webhook
```

Default hiện tại ưu tiên an toàn khi demo/production có quota Gemini thấp. Nếu dùng API key có billing/quota cao hơn, có thể tăng `GEMINI_MAX_ATTEMPTS` hoặc thêm fallback model một cách chủ động.

### Kiểm thử

Thêm **`tests/test_alert_dedup.py`** để kiểm tra:

*   Ưu tiên dùng Alertmanager `fingerprint` làm identity.
*   Cooldown bỏ qua alert trùng khi Redis unavailable.
*   Clear cooldown cho phép xử lý lại alert sau khi resolved/re-fire.

## 🛠️ Công nghệ sử dụng
*   **Language**: Python 3.11
*   **AI**: Google Gemini (LLM), ChromaDB (Vector DB)
*   **Framework**: FastAPI, Uvicorn
*   **Data Store**: Redis (Celery queue, incident context, alert cooldown)
*   **Async Worker**: Celery
*   **System**: Docker, Psutil

## 🚀 Cách khởi động nhanh
Hệ thống được đóng gói qua Docker:
```bash
docker build -t aiops-agent .
docker run --env-file .env aiops-agent
```
Hoặc chạy trực tiếp qua entrypoint:
```bash
./docker-entrypoint.sh
```
