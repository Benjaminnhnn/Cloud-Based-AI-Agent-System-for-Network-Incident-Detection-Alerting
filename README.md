# Hệ thống AIOps Hybrid Cloud phát hiện sự cố và cảnh báo thông minh

Dự án xây dựng một hệ thống AIOps chạy trên AWS EC2, kết hợp hạ tầng cloud, giám sát dịch vụ, AI Agent và quy trình phát hành có healthcheck, rollback tự động.

---

## 1. Tổng quan kiến trúc

Hệ thống hiện tại được tách thành bốn lớp rõ ràng:

1. **Hạ tầng AWS bằng Terraform**
   - Tạo VPC, subnet, route, security group, Elastic IP.
   - Tạo ba EC2:
     - `monitor-ai-01`
     - `bank-web-01`
     - `bank-core-01`

2. **Bootstrap và cấu hình máy chủ bằng Ansible**
   - Cài package nền, Docker, Docker Compose.
   - Cấu hình SSH, firewall host-level.
   - Triển khai Node Exporter.
   - Cấu hình Prometheus, Alertmanager, Grafana và dashboard.
   - Đặt release compose, file mẫu môi trường và deploy script lên EC2 release host.

3. **Release ứng dụng bằng image versioned**
   - AI Agent được build thành Docker image.
   - Backend được build thành Docker image.
   - Frontend được build thành image Nginx phục vụ static assets và reverse proxy `/api`.

4. **CI/CD bằng GitHub Actions**
   - Build, test, đóng gói image.
   - Push image lên GHCR.
   - SSH vào EC2 để chạy release script.
   - Health check toàn bộ stack.
   - Rollback về tag trước nếu release mới lỗi.

---

## 2. Các thành phần chính

| Thành phần | Vai trò |
|---|---|
| Terraform | Provision hạ tầng AWS |
| Ansible | Bootstrap EC2, cấu hình monitoring và release runtime |
| Prometheus | Thu thập metrics |
| Alertmanager | Gửi cảnh báo tới AI Agent |
| Grafana | Dashboard giám sát |
| AI Agent | Nhận webhook, phân tích sự cố, phối hợp worker |
| Celery + Redis | Xử lý tác vụ nền |
| Payment API | Backend FastAPI mẫu |
| Frontend Nginx | Giao diện web image-based |
| GitHub Actions | CI/CD và release orchestration |

---

## 3. Cấu trúc thư mục

```text
aws-hybrid/
|- terraform/                         # Hạ tầng AWS bằng Terraform
|- ansible/                           # Bootstrap, monitoring, release runtime config
|  `- playbooks/
|     |- bootstrap.yml
|     |- configure-monitoring-stack.yml
|     `- configure-release-runtime.yml
|- automation/
|  |- app-release-deploy.sh           # Pull image, start stack, health check, rollback
|  `- update-infrastructure.sh        # Cập nhật IP và inventory khi IP máy dev thay đổi
|- release/
|  |- .env.example
|  |- docker-compose.staging.yml
|  `- docker-compose.production.yml
|- agent_src/                         # AI Agent
|- demo-web/
|  |- backend/                        # Payment API
|  `- frontend/                       # React frontend, đóng gói thành Nginx image
|- platform-config/                  # Compose và cấu hình phục vụ local/dev
|- diagram/                          # Tài liệu sơ đồ
|- AWS_INFRASTRUCTURE_DEPLOYMENT_GUIDE.md
|- AIops_CICD.md
`- README.md
```

---

## 4. Luồng phát hiện và xử lý sự cố

1. Prometheus, Blackbox Exporter hoặc service monitor phát hiện bất thường.
2. Alertmanager gửi webhook tới AI Agent.
3. AI Agent ghi nhận alert và đẩy tác vụ vào Redis queue.
4. Celery worker xử lý alert, gọi công cụ chẩn đoán và mô hình AI khi cần.
5. Kết quả được gửi tới Telegram để người vận hành theo dõi hoặc phê duyệt.

---

## 5. Luồng triển khai chuẩn hiện tại

```text
Developer push code
  -> GitHub Actions chạy lint, test, build
  -> Build 3 Docker images:
       - aws-hybrid-ai-agent
       - aws-hybrid-payment-api
       - aws-hybrid-frontend
  -> Push image lên GHCR với cùng tag
  -> Workflow SSH vào EC2 release host
  -> Chạy automation/app-release-deploy.sh
  -> EC2 pull image
  -> docker compose up -d
  -> Health check AI Agent, backend, frontend
  -> Thành công hoặc rollback về tag cũ
```

---

## 6. Các playbook Ansible đang dùng

### Bootstrap EC2

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/bootstrap.yml
```

### Cấu hình monitoring và host services

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/configure-monitoring-stack.yml
```

Playbook này chỉ đảm nhiệm lớp monitoring/config:
- Node Exporter
- Prometheus
- Blackbox Exporter
- Alertmanager
- Grafana
- firewall host-level

Nó không deploy backend hoặc frontend production.

### Đặt release runtime trên EC2

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/configure-release-runtime.yml
```

Playbook này chép:
- `release/docker-compose.staging.yml`
- `release/docker-compose.production.yml`
- `release/.env.example`
- `automation/app-release-deploy.sh`

---

## 7. Deploy staging và production

### Staging

```bash
git push origin develop
```

Workflow staging sẽ phát hành image tag dạng:

```text
staging-<commit-sha>
```

Script chạy trên EC2:

```bash
./automation/app-release-deploy.sh staging staging-<commit-sha>
```

Health check:

```text
AI Agent: http://127.0.0.1:18000/health
Backend:  http://127.0.0.1:18080/api/health
Frontend: http://127.0.0.1:18081/health
```

### Production

```bash
git tag v1.0.0
git push origin v1.0.0
```

Workflow production sẽ phát hành image tag dạng:

```text
v1.0.0
```

Script chạy trên EC2:

```bash
./automation/app-release-deploy.sh production v1.0.0
```

Health check:

```text
AI Agent: http://127.0.0.1:8000/health
Backend:  http://127.0.0.1:8080/api/health
Frontend: http://127.0.0.1:8081/health
```

Nếu bất kỳ health check nào thất bại, script sẽ tự rollback về tag đã lưu trước đó.

---

## 8. Chạy local cho phát triển

Môi trường local vẫn dùng Docker Compose riêng:

```bash
docker-compose -f platform-config/docker-compose.dev.yml up -d
```

Compose local phục vụ mục đích phát triển và kiểm thử thủ công, không phải đường production release.

---

## 9. Các secret CI/CD cần cấu hình

Repository secrets trên GitHub cần có:

| Secret | Mục đích |
|---|---|
| `GHCR_USERNAME` | Tài khoản push image lên GHCR |
| `GHCR_TOKEN` | Token registry |
| `SSH_HOST` | EC2 release host |
| `SSH_PORT` | Cổng SSH |
| `SSH_PRIVATE_KEY` | Private key dùng bởi workflow |
| `GEMINI_API_KEY` | Khóa API AI |
| `TELEGRAM_TOKEN` | Token bot Telegram |
| `TELEGRAM_CHAT_ID` | Kênh nhận cảnh báo |
| `AI_AGENT_PUBLIC_URL` | URL public của Agent khi cần |
| `DATABASE_URL` | Kết nối backend |
| `SECRET_KEY` | Secret backend |
| `PROMETHEUS_URL` | URL Prometheus |

---

## 10. Endpoint tham khảo

| Dịch vụ | Endpoint |
|---|---|
| Grafana | `http://<monitor-ip>:3000` |
| Prometheus | `http://<monitor-ip>:9090` |
| Alertmanager | `http://<monitor-ip>:9093` |
| AI Agent production | `http://<monitor-ip>:8000/health` |
| Frontend release internal | `http://127.0.0.1:8081/health` |

---

## 11. Tài liệu liên quan

- [AWS_INFRASTRUCTURE_DEPLOYMENT_GUIDE.md](AWS_INFRASTRUCTURE_DEPLOYMENT_GUIDE.md)
- [AIops_CICD.md](AIops_CICD.md)
- [diagram/CI_CD_DEPLOYMENT_DIAGRAM.md](diagram/CI_CD_DEPLOYMENT_DIAGRAM.md)

---

## 12. Ghi chú vận hành

- Không build production image trực tiếp trên EC2.
- Không copy source application lên EC2 để phát hành production.
- EC2 chỉ nên pull artifact đã được CI tạo.
- Terraform quản lý cloud resource; Ansible quản lý bootstrap và cấu hình host.
- `automation/app-release-deploy.sh` là cửa release thống nhất cho staging và production.
