# 🚀 Cloud-Based AI Agent System for Network Incident Detection & Alerting

Hệ thống giám sát hạ tầng mạng và phát hiện sự cố thông minh dựa trên AI (AI Ops). Hệ thống không chỉ cảnh báo khi có lỗi mà còn sử dụng AI (Gemini 2.0) để phân tích nguyên nhân gốc rễ và đề xuất giải pháp xử lý ngay lập tức.

---

## 🌟 Tính năng nổi bật

- **Giám sát thời gian thực**: Thu thập metric (CPU, RAM, Disk, Network) từ các server AWS EC2.
- **Phân tích Log thông minh**: Tự động đọc file log hệ thống, phát hiện lỗi và gửi đi phân tích.
- **Trí tuệ nhân tạo (AI Ops)**: Tích hợp Google Gemini 2.0 Flash để "đọc hiểu" sự cố và đưa ra lời khuyên như một chuyên gia hệ thống.
- **Thông báo tức thì**: Gửi báo cáo chi tiết qua Telegram Bot.
- **Dashboard trực quan**: Theo dõi sức khỏe hệ thống qua Grafana.
- **Triển khai tự động**: Hỗ trợ Terraform (Infras) và Ansible (Cấu hình).

---

## 🏗️ Kiến trúc hệ thống

```text
[ SERVERS ] --(Metrics)--> [ PROMETHEUS ] --(Alerts)--> [ AI AGENT (FastAPI) ]
    |                          ^                              |
    |                          |                       [ GEMINI 2.0 AI ]
    |                          |                              |
[ LOGS ] ----(Error)----> [ LOG WATCHER ]                     v
    |                                                 [ TELEGRAM NOTIFY ]
    v
[ GRAFANA DASHBOARD ]
```

---

## 🛠️ Công nghệ sử dụng

- **Hạ tầng**: AWS (EC2, VPC), Terraform, Ansible.
- **Giám sát**: Prometheus, Node Exporter, Alertmanager, Grafana.
- **AI & Backend**: Python, FastAPI, Google Gemini API.
- **Container**: Docker, Docker Compose.
- **Ứng dụng Demo**: React (Frontend), FastAPI (Backend), PostgreSQL.

---

## 🚀 Hướng dẫn cài đặt nhanh (Dành cho người mới)

Dưới đây là cách chạy toàn bộ hệ thống trên máy tính cá nhân của bạn bằng Docker.

### 1. Chuẩn bị (Prerequisites)
- Đã cài đặt [Docker](https://docs.docker.com/get-docker/) và [Docker Compose](https://docs.docker.com/compose/install/).
- Có tài khoản Google để lấy **Gemini API Key** (Miễn phí tại [Google AI Studio](https://aistudio.google.com/)).
- Tạo một **Telegram Bot** (Qua [@BotFather](https://t.me/botfather)) để nhận thông báo.

### 2. Cấu hình biến môi trường
Truy cập vào thư mục `agent_src/`, tạo file `.env` (hoặc sửa file có sẵn) và điền các thông tin sau:

```env
GEMINI_API_KEY=your_gemini_api_key_here
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_personal_chat_id_here
```
*(Lưu ý: Để lấy `TELEGRAM_CHAT_ID`, bạn có thể chat với [@userinfobot](https://t.me/userinfobot) trên Telegram)*

### 3. Khởi chạy hệ thống
Mở Terminal (hoặc CMD/PowerShell) tại thư mục gốc của dự án và chạy lệnh:

```bash
docker-compose up -d
```

### 4. Truy cập các dịch vụ
Sau khi lệnh chạy xong, bạn có thể truy cập các địa chỉ sau:

- **Ứng dụng Web Demo**: [http://localhost:3000](http://localhost:3000)
- **API Backend**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Grafana (Dashboard)**: [http://localhost:3001](http://localhost:3001) (User: `admin` / Pass: `admin123`)
- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **AI Agent (Webhook)**: [http://localhost:8080/health](http://localhost:8080/health)

---

## 📂 Cấu trúc thư mục

- `agent_src/`: Mã nguồn của AI Agent xử lý cảnh báo.
- `ansible/`: Các kịch bản cấu hình server tự động.
- `demo-web/`: Ứng dụng mẫu để kiểm thử việc giám sát.
- `scripts/`: Các script hỗ trợ cài đặt và vận hành.
- `terraform/`: Mã nguồn định nghĩa hạ tầng trên AWS.
- `docker-compose.yml`: File cấu hình chạy toàn bộ hệ thống bằng Docker.

---

## ⚠️ Lưu ý quan trọng
- Các script trong thư mục `scripts/` hiện tại đang được cấu hình cho môi trường Ubuntu/Linux. Nếu bạn dùng Windows, hãy ưu tiên sử dụng **Docker Compose**.
- Để AI phân tích hiệu quả, hãy đảm bảo Internet của bạn không chặn API của Google Gemini.

---
**Dự án được thực hiện cho mục đích học tập và nghiên cứu AI Ops.**
