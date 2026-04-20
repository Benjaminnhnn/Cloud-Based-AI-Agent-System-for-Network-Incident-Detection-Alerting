# 🤖 Cloud-Based AI Agent System for Network Incident Detection & Alerting

Hệ thống AIOps toàn diện kết hợp sức mạnh của hạ tầng Cloud, Monitoring hiện đại và Trí tuệ nhân tạo (Generative AI) để tự động hóa việc phát hiện, phân tích và hỗ trợ xử lý sự cố mạng/dịch vụ.

---

## 🏗️ Kiến trúc hệ thống (System Architecture)

Dự án được thiết kế theo mô hình Hybrid-Cloud, triển khai tự động hóa hoàn toàn:

1.  **Infrastructure Layer (Terraform)**: Triển khai trên AWS VPC, bao gồm các EC2 Instances cho các vai trò khác nhau (Monitor, Web, Core).
2.  **Configuration Layer (Ansible)**: Tự động hóa việc cài đặt Docker, cấu hình Security, Firewall và triển khai các dịch vụ.
3.  **Monitoring Layer (Prometheus & Grafana)**: 
    *   **Prometheus**: Thu thập metrics từ Node Exporter và các dịch vụ.
    *   **AlertManager**: Quản lý và gửi cảnh báo về AI Agent qua Webhook.
    *   **Grafana**: Dashboard trực quan hóa hiệu suất hệ thống và mạng.
4.  **AI Ops Layer (AI Agent)**: 
    *   **FastAPI**: Tiếp nhận Webhook từ AlertManager.
    *   **RAG (Retrieval-Augmented Generation)**: Sử dụng ChromaDB để truy xuất Runbook và lịch sử sự cố.
    *   **Gemini AI**: Phân tích lỗi, thực hiện chẩn đoán (Function Calling) và đề xuất xử lý.
    *   **Telegram Bot**: Giao tiếp với người vận hành (Human-in-the-Loop).

---

## 📂 Cấu trúc dự án

```text
├── terraform/                # Khởi tạo hạ tầng AWS (VPC, EC2, SG, v.v.)
├── ansible/                  # Triển khai phần mềm & cấu hình dịch vụ
│   ├── playbooks/            # Kịch bản triển khai (Prometheus, Grafana, AI Agent...)
│   └── templates/            # Các mẫu Dashboard Grafana và cấu hình Alert
├── agent_src/                # Mã nguồn AI Agent (Python/FastAPI)
│   ├── core/                 # Logic chính (RAG Engine, Workflow)
│   ├── monitoring/           # Các script giám sát bổ trợ (Log Watcher, Service Monitor)
│   ├── tools/                # Công cụ chẩn đoán AI có thể gọi (Ping, Metrics, Logs)
│   └── utils/                # Tiện ích (Telegram Bot)
└── scripts/                  # Các script hỗ trợ triển khai nhanh
```

---

## 🔄 Luồng hoạt động (Incident Workflow)

1.  **Phát hiện (Detection)**: `service_monitor.py` hoặc Prometheus phát hiện Port chết, Network lỗi (Packet loss, High Latency).
2.  **Cảnh báo (Alerting)**: AlertManager gửi Webhook chứa chi tiết sự cố đến AI Agent.
3.  **Phân tích (AI Analysis)**: 
    *   AI Agent truy vấn **ChromaDB** để tìm Runbook và các sự cố tương tự.
    *   AI tự động gọi các **Diag Tools** (Ping, DNS Check, Log Read) để thu thập thêm bằng chứng.
4.  **Tương tác (HITL)**: AI gửi báo cáo phân tích và nút bấm "Phê duyệt xử lý" lên **Telegram**.
5.  **Hành động & Học tập**: Sau khi quản trị viên phê duyệt, AI thực hiện lệnh sửa lỗi và lưu toàn bộ diễn biến vào bộ nhớ để học tập cho lần sau.

---

## 🚀 Hướng dẫn triển khai (Deployment)

### Bước 1: Chuẩn bị hạ tầng (Terraform)
Cần cài đặt AWS CLI và cấu hình Credentials.
```bash
cd terraform
terraform init
terraform apply -auto-approve
```

### Bước 2: Cấu hình biến môi trường
Tạo file `.env` hoặc export các biến sau để AI Agent hoạt động:
```bash
export GEMINI_API_KEY='your_gemini_key'
export TELEGRAM_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'
```

### Bước 3: Triển khai toàn bộ bằng Ansible
Script này sẽ tự động hóa việc cài đặt tất cả thành phần (Prometheus, Grafana, Nginx, AI Agent, v.v.) lên các EC2 đã tạo.
```bash
chmod +x scripts/deploy-infrastructure.sh
./scripts/deploy-infrastructure.sh
```

---

## 📊 Truy cập các dịch vụ
Sau khi triển khai thành công, bạn có thể truy cập các địa chỉ sau:
*   **Grafana**: `http://<Monitor-IP>:3000` (admin/admin123)
*   **Prometheus**: `http://<Monitor-IP>:9090`
*   **AI Agent API**: `http://<Monitor-IP>:8000/health`
*   **Web Server**: `http://<Web-IP>:80`

---
*Dự án là giải pháp thực tế cho việc vận hành hệ thống thông minh, giảm thiểu thời gian gián đoạn dịch vụ (Downtime) bằng sức mạnh AI.*
