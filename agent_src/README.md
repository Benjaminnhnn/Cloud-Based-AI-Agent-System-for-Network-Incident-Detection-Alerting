# 🤖 AIOps Intelligent Agent System

Hệ thống AI Agent chuyên dụng để tự động phát hiện, chẩn đoán và đề xuất xử lý sự cố hạ tầng mạng và hệ thống dựa trên mô hình RAG (Retrieval-Augmented Generation) và Gemini LLM.

## 🏗️ Kiến trúc hệ thống

Hệ thống bao gồm 3 lớp chính:

### 1. Lớp Giám sát (Monitoring Layer)
*   **`monitoring/log_watcher.py`**: Theo dõi các file log hệ thống/ứng dụng thời gian thực. Phát hiện các từ khóa lỗi (ERROR, CRITICAL...) và gửi cảnh báo về Webhook.
*   **`monitoring/service_monitor.py`**: Kiểm tra trạng thái các Port dịch vụ (Nginx, DB, Redis...) và các chỉ số mạng (Packet loss, TCP connections).

### 2. Lớp Xử lý Trung tâm (Core AI Layer)
*   **`core/main.py`**: Server FastAPI tiếp nhận Alert, điều phối luồng phân tích của AI và quản lý giao tiếp với Telegram.
*   **`core/rag_engine.py`**: Sử dụng **ChromaDB** để lưu trữ và truy vấn tri thức từ các Runbook (.md) và lịch sử các sự cố đã xử lý trước đó.
*   **`tools/diag_tools.py`**: Tập hợp các công cụ "cánh tay" để AI tự thực hiện các lệnh kiểm tra (ping, check metrics, read logs).

### 3. Lớp Tương tác (Integration Layer)
*   **Telegram Bot**: Gửi báo cáo phân tích chi tiết cho Quản trị viên và nhận lệnh phê duyệt thực thi hành động sửa lỗi thông qua các nút bấm tương tác.

## 🔄 Quy trình vận hành (Workflow)

1.  **Detect**: Các bộ Monitor phát hiện bất thường -> Gửi Alert qua Webhook `/webhook`.
2.  **Retrieve**: AI Agent truy vấn RAG DB để tìm quy trình xử lý (Runbook) tương ứng.
3.  **Analyze**: Gemini LLM sử dụng dữ liệu RAG và tự gọi các `diag_tools` để chẩn đoán nguyên nhân gốc rễ.
4.  **Propose**: AI gửi báo cáo kèm nút bấm "Thực thi" hoặc "Bỏ qua" qua Telegram.
5.  **Execute & Learn**: Nếu được duyệt, Agent thực hiện hành động sửa lỗi và lưu kết quả vào Vector DB để làm kinh nghiệm cho lần sau.

## 🛠️ Công nghệ sử dụng
*   **Language**: Python 3.11
*   **AI**: Google Gemini (LLM), ChromaDB (Vector DB)
*   **Framework**: FastAPI, Uvicorn
*   **Data Store**: Redis (Incident context)
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
