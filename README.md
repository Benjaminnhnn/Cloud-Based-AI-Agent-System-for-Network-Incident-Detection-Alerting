# Cloud-Based AI Agent System for Network Incident Detection & Alerting

Hệ thống AIOps toàn diện kết hợp sức mạnh của hạ tầng Cloud, Monitoring hiện đại và Trí tuệ nhân tạo (Generative AI) để tự động hóa việc phát hiện, phân tích và hỗ trợ xử lý sự cố mạng/dịch vụ.

---

## Kiến trúc hệ thống (System Architecture)

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

## Cấu trúc dự án

```text
aws-hybrid/
|- terraform/              # AWS infrastructure as code (VPC, EC2, SG, v.v.)
|- ansible/                # Triển khai phần mềm & cấu hình dịch vụ
|- platform-config/        # Cấu hình Docker Compose và Monitoring
|- release/                # Production deployment manifests & configs
|- agent_src/              # Mã nguồn AI Agent (Python/FastAPI)
│   ├── core/              # Logic chính (RAG Engine, Workflow)
│   ├── monitoring/        # Script giám sát (Log Watcher, Service Monitor)
│   ├── tools/             # Công cụ chẩn đoán (Ping, Metrics, Logs)
│   └── utils/             # Tiện ích (Telegram Bot)
|- demo-web/               # Ứng dụng web mẫu (Full-stack React + FastAPI)
|- automation/             # Script tự động hóa triển khai & vận hành
|- diagram/                # Sơ đồ kiến trúc, CI/CD và luồng hoạt động
`- README.md
```

### Key Automation Scripts

- `automation/deploy.sh` - Script triển khai chính (xử lý pull image, check health, rollback)
- `automation/deploy-infrastructure.sh` - Khởi tạo hạ tầng AWS và chạy Ansible
- `automation/ansible-deploy.sh` - Wrapper cho Ansible (load credentials, bootstrap)
- `automation/update-infrastructure.sh` - Cập nhật hạ tầng và đồng bộ IP

---

## Luồng hoạt động (Incident Workflow)

1.  **Phát hiện (Detection)**: `service_monitor.py` hoặc Prometheus phát hiện Port chết, Network lỗi (Packet loss, High Latency).
2.  **Cảnh báo (Alerting)**: AlertManager gửi Webhook chứa chi tiết sự cố đến AI Agent.
3.  **Phân tích (AI Analysis)**: 
    *   AI Agent truy vấn **ChromaDB** để tìm Runbook và các sự cố tương tự.
    *   AI tự động gọi các **Diag Tools** (Ping, DNS Check, Log Read) để thu thập thêm bằng chứng.
4.  **Tương tác (HITL)**: AI gửi báo cáo phân tích và nút bấm "Phê duyệt xử lý" lên **Telegram**.
5.  **Hành động & Học tập**: Sau khi quản trị viên phê duyệt, AI thực hiện lệnh sửa lỗi và lưu toàn bộ diễn biến vào bộ nhớ để học tập cho lần sau.

---

## Hướng dẫn triển khai nhanh (Quick Start)

### Thiết lập biến môi trường
Tạo file `.env` trong `agent_src/` hoặc export các biến:
```bash
export GEMINI_API_KEY="your-gemini-api-key"
export TELEGRAM_TOKEN="your-telegram-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

### Cách 1: Triển khai tự động (Khuyên dùng)
```bash
bash automation/deploy-infrastructure.sh
```
Script này sẽ tự động kiểm tra hạ tầng, cài đặt môi trường và triển khai toàn bộ stack.

### Cách 2: Chạy local với Docker Compose
```bash
docker-compose -f platform-config/docker-compose.dev.yml up -d
```

---

## Truy cập các dịch vụ (Service Endpoints)

### AWS Deployment (Ví dụ IP thực tế)
*   **Grafana**: `http://<Monitor-IP>:3000` (admin/admin123)
*   **Prometheus**: `http://<Monitor-IP>:9090`
*   **AI Agent API**: `http://<Monitor-IP>:8000/health`
*   **Web Server (Frontend)**: `http://<Web-IP>:3000`
*   **API Backend Docs**: `http://<Core-IP>:8000/docs`

---

## CI/CD Pipeline
Dự án sử dụng GitHub Actions để tự động hóa quy trình Build, Test và Deploy:
- **CI Workflow**: Kiểm tra lỗi (Lint), chạy Tests và Build Docker images.
- **CD Staging**: Tự động triển khai lên môi trường Staging khi push vào branch `develop`.
- **CD Production**: Triển khai lên Production khi tạo tag trên branch `main`.

---

## Tài liệu tham khảo
Xem thêm chi tiết tại thư mục `diagram/` và các file hướng dẫn:
- `ANSIBLE_DEPLOYMENT_GUIDE.md`: Hướng dẫn chi tiết về Ansible.
- `diagram/ARCHITECTURE_DIAGRAMS.md`: Sơ đồ hạ tầng AWS.
- `diagram/CI_CD_DEPLOYMENT_DIAGRAM.md`: Sơ đồ luồng CI/CD.


