# 📚 Hướng dẫn Tạo Hạ tầng AWS & Deploy CI/CD System 

---

## 📑 Mục lục

1. [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
2. [Chuẩn bị AWS Account](#chuẩn-bị-aws-account)
3. [Tạo Infrastructure với Terraform](#tạo-infrastructure-với-terraform)
4. [Đồng bộ Ansible Inventory](#đồng-bộ-ansible-inventory)
5. [Deploy Hạ tầng và Dịch vụ bằng Ansible](#deploy-hạ-tầng-và-dịch-vụ-bằng-ansible)
6. [Deploy Staging Environment](#deploy-staging-environment)
7. [Deploy Production Environment](#deploy-production-environment)
8. [Kiểm tra & Validation](#kiểm-tra--validation)
9. [Monitoring & Logs](#monitoring--logs)
10. [Troubleshooting](#troubleshooting)
11. [Disaster Recovery](#disaster-recovery)

---

## 🏗️ Kiến trúc hệ thống

### Mô hình hệ thống (Thực tế)

```
┌──────────────────────────────────────────────────────────────┐
│                   AWS Account (ap-southeast-1 Singapore)      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │    VPC: aiops-bank-vpc (Mạng riêng ảo)               │ │
│  │    CIDR: 10.0.0.0/16                                  │ │
│  │                                                        │ │
│  │  ┌──────────────┐  ┌─────────────────────────────┐   │ │
│  │  │  IGW        │  │  Subnets (3 vùng sẵn sàng)  │   │ │
│  │  │              │  │  - 10.0.1.0/24 (ap-se-1a)   │   │ │
│  │  │              │  │  - 10.0.2.0/24 (ap-se-1b)   │   │ │
│  │  └──────────────┘  │  - 10.0.3.0/24 (ap-se-1c)   │   │ │
│  │                    └─────────────────────────────┘   │ │
│  │                                                        │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │   EC2 Instances với Elastic IPs (Tĩnh)        │ │ │
│  │  │                                                 │ │ │
│  │  │  ┌──────────────────────────┐                   │ │ │
│  │  │  │ monitor-ai-01 (AI & Monitoring)         │ │ │
│  │  │  │ (t3.small: 2CPU, 2GB)    │                   │ │ │
│  │  │  │ EIP: 52.74.118.8         │                   │ │ │
│  │  │  │ Dịch vụ:                 │                   │ │ │
│  │  │  │  - AI Agent: 8000        │                   │ │ │
│  │  │  │  - Prometheus: 9090      │                   │ │ │
│  │  │  │  - Grafana: 3000         │                   │ │ │
│  │  │  └──────────────────────────┘                   │ │ │
│  │  │                                                 │ │ │
│  │  │  ┌──────────────────────────┐                   │ │ │
│  │  │  │ bank-web-01 (API & Frontend)            │ │ │
│  │  │  │ (t2.micro: 1CPU, 1GB)    │                   │ │ │
│  │  │  │ EIP: 18.136.112.28       │                   │ │ │
│  │  │  │ Dịch vụ:                 │                   │ │ │
│  │  │  │  - Payment API: 8000     │                   │ │ │
│  │  │  │  - Frontend: 3000        │                   │ │ │
│  │  │  └──────────────────────────┘                   │ │ │
│  │  │                                                 │ │ │
│  │  │  ┌──────────────────────────┐                   │ │ │
│  │  │  │ bank-core-01 (Database & Cache)         │ │ │
│  │  │  │ (t2.micro: 1CPU, 1GB)    │                   │ │ │
│  │  │  │ EIP: 54.255.94.179       │                   │ │ │
│  │  │  │ Dịch vụ:                 │                   │ │ │
│  │  │  │  - PostgreSQL: 5432      │                   │ │ │
│  │  │  │  - Redis: 6379           │                   │ │ │
│  │  │  │  - API Backend: 8000     │                   │ │ │
│  │  │  └──────────────────────────┘                   │ │ │
│  │  │                                                 │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │  ┌────────────────────────────────────────────────┐  │ │
│  │  │  Nhóm bảo mật (Security Groups)                │  │ │
│  │  │  - SG-Monitor: SSH(22), HTTP(9090), Grafana(3000) │ │
│  │  │  - SG-Web: SSH(22), HTTP(8000), HTTPS(443)    │  │ │
│  │  │  - SG-Core: SSH(22), DB(5432), Cache(6379)    │  │ │
│  │  │  - SG-Internal: Giao tiếp giữa instances       │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  │                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Dịch vụ Bên ngoài                              │ │
│  │  - GitHub (Kho mã + GitHub Actions)                   │ │
│  │  - GHCR (ghcr.io - Kho chứa Container)               │ │
│  │  - Telegram API (Thông báo Bot)                       │ │
│  │  - Google Gemini API (Phân tích AI)                   │ │
│  │  - ChromaDB (Cơ sở dữ liệu Vector - cục bộ)          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Thông số kỹ thuật EC2 (Hiện tại)

| Instance | Loại | CPU | RAM | Disk | EIP | Mục đích |
|----------|------|-----|-----|------|-----|---------|
| monitor-ai-01 | t3.small | 2 | 2GB | 12GB | 52.74.118.8 | AI Agent, Prometheus, Grafana |
| bank-web-01 | t2.micro | 1 | 1GB | 12GB | 18.136.112.28 | API Thanh toán, Frontend |
| bank-core-01 | t2.micro | 1 | 1GB | 12GB | 54.255.94.179 | PostgreSQL, Redis, CSDL |
| **Tổng chi phí** | - | - | - | - | - | **~$30/tháng** |

**📝 Ghi chú:** Elastic IPs (EIP) là **tĩnh** - không thay đổi khi dừng/khởi động lại instances

---

### 🤖 Kiến trúc AI Agent (agent_src)

**Mục đích:** Phát hiện tự động sự cố, chẩn đoán và xử lý sử dụng RAG + Gemini LLM

**Structure:**

```
agent_src/
├── core/
│   ├── main.py              # Server FastAPI (nhận webhook)
│   ├── rag_engine.py        # ChromaDB RAG + truy vấn cơ sở kiến thức
│   ├── tasks.py             # Celery async tasks
│   ├── celery_app.py        # Cấu hình Celery
│   └── metrics.py           # Theo dõi chỉ số
├── monitoring/
│   ├── log_watcher.py       # Giám sát log thời gian thực (3.9 KB)
│   └── service_monitor.py   # Kiểm tra sức khỏe dịch vụ (12.6 KB)
├── tools/
│   └── diag_tools.py        # Hàm chẩn đoán (ping, chỉ số, logs)
├── utils/
│   └── telegram_bot.py      # Tích hợp Telegram
├── config/
│   ├── services_config.json # Định nghĩa dịch vụ (nginx, postgresql, redis, docker)
│   └── knowledge_base/      # RAG runbooks
│       ├── runbook_docker.md
│       ├── runbook_nginx.md
│       ├── runbook_postgresql.md
│       └── runbook_redis.md
├── vector_db/               # Kho vector ChromaDB (embeddings)
│   └── chroma.sqlite3       # CSDL SQLite (282 KB)
├── tests/                   # Bài kiểm tra đơn vị
├── requirements.txt         # Phụ thuộc (FastAPI, ChromaDB, Celery, google-genai, v.v.)
└── Dockerfile              # Docker image đa giai đoạn
```

**Công nghệ chính:**
- **Framework:** FastAPI + Uvicorn (Python 3.11)
- **AI/ML:** Google Gemini API, CSDL vector ChromaDB, Sentence Transformers
- **Async:** Celery task queue + Redis
- **Giám sát:** Theo dõi log, kiểm tra sức khỏe dịch vụ, chỉ số hệ thống
- **Tích hợp:** Telegram Bot API, Nhận webhook

**Luồng công việc:**
1. **Phát hiện** → Log watcher hoặc service monitor phát hiện bất thường
2. **Truy xuất** → Truy vấn RAG engine để tìm runbooks liên quan
3. **Phân tích** → Gemini LLM phân tích với RAG context + công cụ chẩn đoán
4. **Đề xuất** → Gửi phân tích tới Telegram với nút hành động
5. **Thực thi** → Chạy các hành động được phê duyệt, học cho các sự cố trong tương lai

---

### 📦 Tổng quan CI/CD Pipeline

**GitHub Actions Workflows:**

| Workflow | Trigger | Purpose | Details |
|----------|---------|---------|---------|
| `ci.yml` | PR to develop/main, push to feature/develop/main | Lint, Test, Build | Ruff (linting), pytest, Docker build for AI Agent & Payment API |
| `cd-staging.yml` | Push to develop | Auto-deploy to staging | Build images → SSH to monitor instance → docker compose pull/up |
| `cd-production.yml` | Tag v*.*.*, manual dispatch | Manual deploy to production | Requires approval → Build → SSH deploy to monitor instance |

**Cổng triển khai:**
- **Staging (monitor-ai-01: 52.74.118.8):**
  - AI Agent: 18000 (để kiểm tra)
  - Prometheus: 9090
  - Grafana: 3000
- **Production (monitor-ai-01):**
  - AI Agent: 8000
  - Prometheus: 9090
  - Grafana: 3000

**Docker Images:**
- `ghcr.io/{owner}/aws-hybrid-ai-agent:staging-latest` / `{tag}`
- `ghcr.io/{owner}/aws-hybrid-payment-api:staging-latest` / `{tag}`

---

### 📁 Project Folder Structure

```
aws-hybrid/
├── .github/
│   └── workflows/           # GitHub Actions CI/CD
│       ├── ci.yml          # Lint, test, build
│       ├── cd-staging.yml  # Auto-deploy to staging
│       └── cd-production.yml # Manual deploy to production
├── agent_src/              # AI Agent (see above)
├── demo-web/               # Demo application
│   ├── backend/            # FastAPI payment API
│   ├── frontend/           # React UI
│   └── database/           # PostgreSQL init.sql, seed.sql
├── ansible/                # Ansible playbooks & config
│   ├── inventory.ini       # Pre-configured for 3 instances
│   ├── playbooks/          # Deployment & bootstrap playbooks
│   └── config/             # Alert rules, Prometheus config
├── terraform/              # Infrastructure as Code
│   ├── compute.tf          # EC2 instances definition
│   ├── network.tf          # VPC, subnets, IGW
│   ├── security.tf         # Security groups
│   ├── provider.tf         # AWS provider config
│   ├── variables.tf        # Input variables
│   ├── outputs.tf          # Terraform outputs (EIPs, SSH commands)
│   ├── terraform.tfvars    # Variable values (DO NOT commit!)
│   ├── terraform.tfstate   # Current state (updated by terraform apply)
│   └── versions.tf         # Provider versions
├── release/                # Deployment manifests
│   ├── docker-compose.staging.yml
│   ├── docker-compose.production.yml
│   ├── .env.example        # Environment template
│   ├── .env.staging        # Staging config (DO NOT commit!)
│   └── .env.production     # Production config (DO NOT commit!)
├── automation/             # Deployment scripts
│   ├── ansible-deploy.sh      # Deploy hạ tầng/dịch vụ bằng Ansible
│   ├── app-release-deploy.sh  # Deploy app release qua Docker Compose (CI/CD)
│   ├── update-infrastructure.sh
│   └── fix-credentials.sh
├── platform-config/        # Local development config
│   ├── docker-compose.dev.yml
│   ├── prometheus.yml
│   └── blackbox.yml
├── diagram/                # Architecture diagrams
│   ├── CI_CD_DEPLOYMENT_DIAGRAM.md
│   └── PRODUCTION_ARCHITECTURE_SUMMARY.md
├── scripts/                # Legacy scripts
└── README.md               # Main documentation

**Important Files (DO NOT commit to GitHub):**
- terraform/terraform.tfvars (AWS credentials location)
- release/.env.staging
- release/.env.production
- .ssh/ (private keys)
```

---

### 📋 Workflow Tóm tắt

```
┌─────────────────────────────────────┐
│  LOCAL MACHINE (Dev)                │
├─────────────────────────────────────┤
│ Step 1: Create AWS Account          │
│ Step 2: SSH Key Pair Generation ⭐  │
│ Step 3: Run Terraform               │
│   export AWS_ACCESS_KEY_ID=xxx      │ ← Local only, NOT in GitHub
│   terraform apply                   │
│                                     │
│ Result: EC2 instances created       │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  Ansible Control Machine (Local)    │
├─────────────────────────────────────┤
│ Bước 4: Đồng bộ inventory           │
│   terraform output ansible_inventory│
│                                     │
│ Bước 5: Bootstrap + deploy stack    │
│   automation/ansible-deploy.sh      │
│                                     │
│ Kết quả: Docker, monitoring, web,   │
│ core services, AI Agent được cài    │
│ trên EC2 instances                  │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  GitHub Repository                  │
├─────────────────────────────────────┤
│ Bước 6: Thiết lập GitHub Secrets    │
│   - SSH_HOST (từ terraform)         │
│   - SSH_PORT (22)                   │
│   - SSH_PRIVATE_KEY ⭐              │
│   - GHCR_USERNAME                   │
│   - GHCR_TOKEN                      │
│                                     │
│ Bước 7: Kích hoạt CI/CD Workflow    │
│   - Push tới develop → Staging      │
│   - Tag v1.0.0 → Production         │
│                                     │
│ Kết quả: App release được cập nhật  │
│ qua SSH/GitHub Actions              │
└─────────────────────────────────────┘
```

**🔑 Chỉ cần AWS credentials (Access Key) khi:**
- Chạy `terraform init/apply` trên local machine
- KHÔNG cần trong GitHub Actions (SSH deployment đủ)

**🧭 Luồng đúng hiện tại:** Terraform chỉ tạo tài nguyên AWS. Sau khi EC2 đã chạy, Ansible là lớp chính để bootstrap server và deploy toàn bộ stack dịch vụ.

### Chuẩn bị máy dev mới

Nếu một dev khác dùng máy riêng để triển khai, họ cần cấu hình các giá trị phụ thuộc máy local trước khi chạy Terraform/Ansible.

```bash
# 1. Clone repo và đặt biến PROJECT_ROOT cho terminal hiện tại
git clone <repo-url> aws-hybrid
cd aws-hybrid
export PROJECT_ROOT="$(pwd)"

# 2. Cài công cụ cần thiết trên máy local
terraform version
ansible --version
aws --version

# 3. Cấu hình AWS profile đúng với terraform/provider.tf
aws configure --profile target-account

# 4. Chuẩn bị SSH key dùng để vào EC2
export SSH_KEY_PATH="$HOME/.ssh/id_rsa"
chmod 600 "$SSH_KEY_PATH"
test -f "${SSH_KEY_PATH}.pub"
```

Các giá trị cần điều chỉnh theo từng máy:

| Giá trị | Nằm ở đâu | Ví dụ |
|---------|-----------|-------|
| `PROJECT_ROOT` | Terminal local | `/home/alice/aws-hybrid` |
| `SSH_KEY_PATH` | Terminal local và `terraform.tfvars` | `/home/alice/.ssh/id_rsa` |
| `public_key_path` | `terraform/terraform.tfvars` | `/home/alice/.ssh/id_rsa.pub` |
| `private_key_path` | `terraform/terraform.tfvars` | `/home/alice/.ssh/id_rsa` |
| `my_ip_cidr` | `terraform/terraform.tfvars` | `x.x.x.x/32` |
| `agent_src/.env` | File local, không commit | Gemini/Telegram credentials |

**Không hard-code đường dẫn của máy khác** như `/home/hoang_viet/...` hoặc `/mnt/c/Users/win/...` khi giao cho dev mới.

### Step 1: Create AWS Account

```bash
# 1. Vào https://aws.amazon.com
# 2. Click "Create an AWS Account"
# 3. Fill information:
#    - Email
#    - Password
#    - AWS Account name
#    - Contact information
# 4. Add credit card
# 5. Verify phone number
# 6. Choose Support Plan (Free tier okay)
```

### Step 2: Create IAM User cho Terraform (OPTIONAL)

⚠️ **CHỈ CẦN NẾU muốn tự động hóa Terraform trong CI/CD**

Hiện tại, Terraform được chạy **MANUAL** trên local machine, nên bước này KHÔNG bắt buộc.

Nếu muốn GitHub Actions tự động chạy `terraform apply` (không khuyến cáo), thì:

```bash
# 1. Vào AWS Console → IAM
# 2. Click "Users" → "Create user"
# 3. User name: "github-actions"
# 4. Click "Next"
# 5. Permissions:
#    - Attach policy: "AmazonEC2FullAccess"
#    - Attach policy: "AmazonVPCFullAccess"
# 6. Click "Create user"
# 7. Security credentials:
#    - Access key ID: copy this
#    - Secret access key: copy this
# 8. Save to GitHub Secrets (nếu tự động hóa):
#    AWS_ACCESS_KEY_ID
#    AWS_SECRET_ACCESS_KEY
```

❌ **KHÔNG KHUYẾN CÁO**: Tự động hóa Terraform có rủi ro cao (thay đổi production infrastructure). Cách làm hiện tại (manual + SSH deploy) an toàn hơn.

### Step 3: Generate SSH Key Pair (BẮT BUỘC ⭐)

Terraform tạo AWS EC2 Key Pair từ `public_key_path`, nên mỗi dev cần có SSH key pair local trước khi chạy `terraform apply`.

```bash
# Trên máy local của dev
export SSH_KEY_PATH="$HOME/.ssh/id_rsa"

# Tạo key nếu máy chưa có
if [ ! -f "$SSH_KEY_PATH" ]; then
  ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N ""
fi

chmod 600 "$SSH_KEY_PATH"
test -f "${SSH_KEY_PATH}.pub"

# Sau đó cấu hình trong terraform/terraform.tfvars:
# public_key_path  = "/home/<your-user>/.ssh/id_rsa.pub"
# private_key_path = "/home/<your-user>/.ssh/id_rsa"

# Nếu dùng GitHub Actions CD, lưu private key vào GitHub Secret:
# SSH_PRIVATE_KEY = nội dung file $SSH_KEY_PATH
```

### Step 4: Kiểm tra GitHub Secrets trước khi chạy CI/CD

Trước khi trigger workflow `CD Staging` hoặc `CD Production`, kiểm tra repository đã có đủ secrets cần thiết.

**Secrets cho CI/CD Deployment:**

| Secret | Mục đích | Status | Ghi chú |
|--------|----------|--------|---------|
| `SSH_HOST` | EC2 target để deploy | ⭐ **BẮT BUỘC** | Public IP của EC2 (lấy từ `terraform output`) |
| `SSH_PORT` | SSH port | ⭐ **BẮT BUỘC** | Thường là `22` |
| `SSH_PRIVATE_KEY` | SSH key để GitHub Actions vào EC2 | ⭐ **BẮT BUỘC** | Nội dung private key tương ứng với `private_key_path` |
| `GHCR_USERNAME` | Login GitHub Container Registry | ⭐ **BẮT BUỘC** | GitHub username hoặc bot account |
| `GHCR_TOKEN` | Pull/push image trên GHCR | ⭐ **BẮT BUỘC** | PAT có quyền `read:packages`, `write:packages`; nếu repo private cần `repo` |
| `GEMINI_API_KEY` | Runtime config cho AI Agent | ⭐ **BẮT BUỘC** | Workflow ghi vào `release/.env.*` |
| `TELEGRAM_TOKEN` | Telegram bot token | ⭐ **BẮT BUỘC nếu bật Telegram** | Workflow ghi vào `release/.env.*` |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | ⭐ **BẮT BUỘC nếu bật Telegram** | Workflow ghi vào `release/.env.*` |
| `AI_AGENT_PUBLIC_URL` | Public URL của AI Agent | Tùy cấu hình | Dùng nếu app cần callback/public URL |
| `DATABASE_URL` | Database URL cho service cần DB | Tùy cấu hình | Workflow ghi vào `release/.env.*` nếu có |
| `SECRET_KEY` | Secret key cho backend/API | ⭐ **BẮT BUỘC nếu backend dùng auth/session** | Workflow ghi vào `release/.env.*` |
| `PROMETHEUS_URL` | Prometheus URL | Production | Dùng trong `cd-production.yml` |
| `AWS_ACCESS_KEY_ID` | Terraform (Local only) | ❌ **KHÔNG CẦN** | Chỉ dùng khi chạy `terraform apply` trên local machine |
| `AWS_SECRET_ACCESS_KEY` | Terraform (Local only) | ❌ **KHÔNG CẦN** | Chỉ dùng khi chạy `terraform apply` trên local machine |

**Kiểm tra bằng GitHub UI:**

```text
Repository → Settings → Secrets and variables → Actions → Repository secrets

Verify (BẮT BUỘC cho CI/CD):
✅ SSH_HOST trùng với public IP của EC2 hiện tại
✅ SSH_PORT = 22
✅ SSH_PRIVATE_KEY = private key đầy đủ (không phải public key .pub)
✅ GHCR_USERNAME = GitHub username
✅ GHCR_TOKEN = GitHub token với quyền packages
✅ GEMINI_API_KEY / TELEGRAM_TOKEN / TELEGRAM_CHAT_ID / SECRET_KEY đã có nếu service cần
✅ DATABASE_URL / AI_AGENT_PUBLIC_URL / PROMETHEUS_URL đã có nếu workflow/service đang dùng

KHÔNG CẦN cho CI/CD deployment (chỉ dùng local):
❌ AWS_ACCESS_KEY_ID (chỉ dùng khi chạy Terraform trên local)
❌ AWS_SECRET_ACCESS_KEY (chỉ dùng khi chạy Terraform trên local)
```

**Kiểm tra bằng GitHub CLI (nếu đã cài `gh`):**

```bash
gh secret list

# Required for CI/CD deployment:
# SSH_HOST
# SSH_PORT
# SSH_PRIVATE_KEY
# GHCR_USERNAME
# GHCR_TOKEN
# GEMINI_API_KEY
# TELEGRAM_TOKEN
# TELEGRAM_CHAT_ID
# AI_AGENT_PUBLIC_URL
# DATABASE_URL
# SECRET_KEY
# PROMETHEUS_URL (production)

# NOT needed for CI/CD (local only):
# AWS_ACCESS_KEY_ID (chỉ cho terraform apply trên local)
# AWS_SECRET_ACCESS_KEY (chỉ cho terraform apply trên local)
```

**Cập nhật `SSH_HOST` từ Terraform outputs:**

```bash
cd terraform
terraform output -raw monitor_public_ip

# Giá trị hiện tại: 52.74.118.8
# Cập nhật GitHub Secret: SSH_HOST = 52.74.118.8
# (Đây là monitor instance chạy AI Agent, Prometheus, Grafana)
```

**Cấu hình GitHub Secrets:**

```bash
# Settings → Secrets and variables → Actions → Repository secrets

SSH_HOST: 52.74.118.8              # Monitor instance (Elastic IP - tĩnh)
SSH_PORT: 22                        # Cổng SSH chuẩn
SSH_PRIVATE_KEY: <key content>      # Nội dung private key trong private_key_path
GHCR_USERNAME: your-github-name     # Tên người dùng GitHub
GHCR_TOKEN: ghp_xxxxxxxxx...        # Token GitHub có phạm vi packages
```

**Kiểm tra trước chuyến bay (máy local):**

```bash
# Kiểm tra kết nối SSH tới monitor instance
ssh -i "$SSH_KEY_PATH" -p 22 ec2-user@52.74.118.8 'echo "SSH OK"'

# Kiểm tra Docker trên monitor instance
ssh -i "$SSH_KEY_PATH" ec2-user@52.74.118.8 'docker --version && docker compose version'

# Kiểm tra đăng nhập GHCR
echo $GHCR_TOKEN | docker login ghcr.io -u $GHCR_USERNAME --password-stdin
ssh -i "$SSH_KEY_PATH" ec2-user@<SSH_HOST> 'docker --version && docker compose version'
```

---

### 🔍 Cấu hình Dịch vụ Giám sát

**Dịch vụ được giám sát** (agent_src/config/services_config.json):

| Dịch vụ | Cổng | Loại | Độ ưu tiên | Khoảng kiểm tra | Chỉ số |
|---------|------|------|-----------|-----------------|--------|
| Nginx | 80 | Web Server | CRITICAL | 5s | response_time, error_rate, uptime |
| PostgreSQL | 5432 | Database | CRITICAL | 5s | connection_count, qps, replication_lag |
| Redis | 6379 | Cache | HIGH | 10s | memory_usage, hit_rate, commands_per_sec |
| Docker | - | Container | HIGH | 30s | container_status, resource_usage |

**Cơ sở kiến thức cho phân tích AI** (agent_src/config/knowledge_base/):
- `runbook_docker.md` - Khắc phục sự cố container Docker
- `runbook_nginx.md` - Cấu hình Nginx và thủ tục khởi động lại
- `runbook_postgresql.md` - Vấn đề kết nối cơ sở dữ liệu và nhân rộng
- `runbook_redis.md` - Quản lý tính nhất quán cache và bộ nhớ

---

## 🔧 Tạo Infrastructure với Terraform

### Step 1: Initialize Terraform (Chạy trên LOCAL MACHINE)

⚠️ **Terraform chạy MANUAL trên máy local, KHÔNG tự động trong GitHub Actions**

```bash
cd "$PROJECT_ROOT/terraform"

# 1. Cấu hình AWS credentials (LOCAL ONLY - không commit!)
export AWS_ACCESS_KEY_ID="your-access-key"          # IAM user access key
export AWS_SECRET_ACCESS_KEY="your-secret-key"      # IAM user secret key
export AWS_DEFAULT_REGION="ap-southeast-1"          # Singapore

# 2. Initialize Terraform
terraform init
# → Downloads AWS provider plugins

# 3. Check configuration
terraform validate
# → Validates syntax

# 4. Preview changes
terraform plan -out=tfplan
# → Shows what will be created
```

**🔐 Bảo mật:**
```bash
# KHÔNG commit terraform.tfvars hoặc .env!
echo "terraform.tfvars" >> .gitignore
echo ".env" >> .gitignore

# AWS credentials chỉ ở local machine, KHÔNG push lên GitHub
export AWS_ACCESS_KEY_ID=xxx   # Terminal session only
unset AWS_ACCESS_KEY_ID        # Clean up after use
```

### Step 2: Review terraform.tfvars

```bash
# File: terraform/terraform.tfvars

cat > terraform.tfvars << 'EOF'
aws_region = "ap-southeast-1"  # Singapore - closest to Vietnam

# Security Groups
my_ip_cidr = "YOUR_PUBLIC_IP/32"  # Example: 125.235.236.242/32
ci_cd_ssh_cidr_blocks = []        # Add CI/CD runner CIDRs only if needed

# SSH key paths
public_key_path  = "/home/<your-user>/.ssh/id_rsa.pub"
private_key_path = "/home/<your-user>/.ssh/id_rsa"

# EC2 Instances
monitor_instance_type = "t3.small"
web_instance_type     = "t3.micro"
core_instance_type    = "t3.micro"

# EBS root volumes
root_volume_size = 30

# Optional tags
project_name = "aiops-bank"
environment  = "dev"
EOF
```

**⚠️ QUAN TRỌNG:**
```
- Đổi my_ip_cidr thành IP public cụ thể của bạn, định dạng x.x.x.x/32
- Đổi public_key_path/private_key_path thành đường dẫn SSH key trên máy đang triển khai
- Không để ci_cd_ssh_cidr_blocks = ["0.0.0.0/0"] trừ khi chỉ dùng tạm thời để debug
- Để nguyên region ap-southeast-1 (Singapore - gần nhất)
- AWS profile hiện đang cấu hình trong terraform/provider.tf: profile = "target-account"
- Instance types có thể giảm/tăng tùy budget: monitor_instance_type, web_instance_type, core_instance_type
```

### Bước 3: Áp dụng Cấu hình Terraform

```bash
# 1. Xem lại kế hoạch
terraform plan

# 2. Áp dụng cấu hình
terraform apply tfplan
# → Tạo:
#    ✅ VPC
#    ✅ Subnets
#    ✅ Internet Gateway
#    ✅ Route Tables
#    ✅ Security Groups
#    ✅ EC2 Instances
#    ✅ Elastic IPs

# 3. Xác minh
terraform show
# Hiển thị tất cả các tài nguyên đã tạo

# 4. Lấy outputs
terraform output
# Ví dụ:
# monitor_public_ip = "52.74.118.8"
# web_public_ip     = "18.136.112.28"
# core_public_ip    = "54.255.94.179"
```

### Bước 4: Lưu Giá trị Outputs

```bash
# Lấy giá trị từ terraform
terraform output -json > outputs.json

# Hoặc sao chép thủ công:
echo "Monitor IP: $(terraform output -raw monitor_public_ip)"
echo "Web IP: $(terraform output -raw web_public_ip)"
echo "Core IP: $(terraform output -raw core_public_ip)"

# Cập nhật GitHub Secrets:
# SSH_HOST = monitor_public_ip nếu dùng GitHub Actions deploy app lên monitor instance
```

---

## 🧭 Đồng bộ Ansible Inventory

Sau khi Terraform tạo xong EC2 instances, bước tiếp theo là đồng bộ IP từ Terraform outputs sang `ansible/inventory.ini`. Đây là inventory thực tế Ansible dùng để bootstrap và deploy dịch vụ.

### Bước 1: Kiểm tra Terraform outputs

```bash
cd "$PROJECT_ROOT/terraform"
terraform output

# Outputs cần có:
# monitor_public_ip
# web_public_ip
# core_public_ip
# ansible_inventory
```

### Bước 2: Sinh Ansible inventory từ Terraform output

```bash
cd "$PROJECT_ROOT/terraform"
terraform output -raw ansible_inventory > "$PROJECT_ROOT/ansible/inventory.ini"

cd "$PROJECT_ROOT"
cat ansible/inventory.ini
```

Lệnh này sẽ:
- Đọc IP EC2 từ Terraform outputs.
- Ghi lại `ansible/inventory.ini`.
- Dùng `ssh_user` từ Terraform, mặc định là `ec2-user`.
- Dùng `private_key_path` trong `terraform/terraform.tfvars`, đúng theo máy của dev đang triển khai.

**Lưu ý:** Nếu IP public của máy dev thay đổi, cập nhật lại `my_ip_cidr` trong `terraform/terraform.tfvars`, chạy `terraform apply`, rồi sinh lại inventory bằng lệnh trên.

Inventory kỳ vọng:

```ini
[monitor]
monitor-ai-01 ansible_host=52.74.118.8 ansible_user=ec2-user

[web]
bank-web-01 ansible_host=18.136.112.28 ansible_user=ec2-user

[core]
bank-core-01 ansible_host=54.255.94.179 ansible_user=ec2-user

[app:children]
web
core

[all:vars]
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_private_key_file=/home/<your-user>/.ssh/id_rsa
```

### Bước 3: Kiểm tra SSH/Ansible

```bash
cd "$PROJECT_ROOT"
ansible all -i ansible/inventory.ini -m ping
```

Kết quả kỳ vọng là cả 3 host đều `SUCCESS`.

---

## 🚀 Deploy Hạ tầng và Dịch vụ bằng Ansible

Ansible là cơ chế chính để cấu hình EC2 sau Terraform. Không cần SSH từng máy để cài Docker thủ công. Playbook sẽ tự động bootstrap server và triển khai toàn bộ stack.

### Các file Ansible chính

| File | Vai trò |
|------|--------|
| `ansible/inventory.ini` | Danh sách EC2 hosts và SSH user/key |
| `ansible/playbooks/bootstrap.yml` | Cài package hệ thống, Docker, Python modules, sudoers |
| `ansible/playbooks/deploy-complete-infrastructure.yml` | Deploy Node Exporter, Prometheus, AlertManager, Grafana, Webserver, Core services, AI Agent |
| `automation/ansible-deploy.sh` | Wrapper one-stop: load credentials, ping, bootstrap, deploy |

### Bước 1: Chuẩn bị credentials cho AI Agent

Credentials được lưu trong `agent_src/.env`. Nếu file này đã có sẵn thì chỉ cần kiểm tra nội dung, không cần export thủ công từng biến.

```bash
cd "$PROJECT_ROOT"

# Chỉ tạo file nếu chưa có
if [ ! -f agent_src/.env ]; then
  cat > agent_src/.env << 'EOF'
GEMINI_API_KEY=your-gemini-api-key
TELEGRAM_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id
EOF
  chmod 600 agent_src/.env
fi

# Kiểm tra nhanh các key đã có trong file hiện tại
grep -E "^(GEMINI_API_KEY|TELEGRAM_TOKEN|TELEGRAM_CHAT_ID)=" agent_src/.env
```

### Bước 2: Chạy Ansible deployment

```bash
cd "$PROJECT_ROOT"
bash automation/ansible-deploy.sh
```

Script này thực hiện 4 bước:

```text
[STEP 1/4] Load credentials từ agent_src/.env
[STEP 2/4] Test SSH connectivity bằng ansible ping
[STEP 3/4] Chạy bootstrap.yml
[STEP 4/4] Chạy deploy-complete-infrastructure.yml
```

### Bước 3: Kiểm tra sau deploy

```bash
cd "$PROJECT_ROOT"

# Kiểm tra containers trên tất cả instances
ansible all -i ansible/inventory.ini -m shell -a "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# Kiểm tra service trên monitor
ansible monitor -i ansible/inventory.ini -m shell -a "curl -s http://localhost:9090/-/ready && curl -s http://localhost:3000/api/health"

# Kiểm tra service trên web/core
ansible web -i ansible/inventory.ini -m shell -a "docker ps"
ansible core -i ansible/inventory.ini -m shell -a "docker ps"
```

### URL truy cập sau khi Ansible deploy thành công

```text
Frontend React:   http://18.136.112.28:3000
API Docs:         http://54.255.94.179:8000/docs
API Health:       http://54.255.94.179:8000/api/health
AI Agent Health:  http://52.74.118.8:8000/health
Prometheus:       http://52.74.118.8:9090
Grafana:          http://52.74.118.8:3000
AlertManager:     http://52.74.118.8:9093
```

**Ghi chú:** Các lệnh SSH/Docker thủ công chỉ dùng để debug. Luồng chuẩn của dự án là Terraform tạo AWS resources, sau đó Ansible bootstrap và deploy services.

---

## 📦 Triển khai Môi trường Staging (monitor-ai-01: 52.74.118.8)

### Triển khai qua GitHub Actions

```
Workflow: cd-staging.yml
Kích hoạt: Push vào nhánh develop
Hành động:
  1. Build Docker images (AI Agent, Payment API)
  2. Đẩy vào GHCR
  3. Tạo release/.env.staging từ GitHub Secrets
  4. SSH vào monitor instance bằng SSH_PRIVATE_KEY
  5. Copy release/ và automation/ lên EC2
  6. Chạy: automation/app-release-deploy.sh staging {image-tag}
  7. Docker compose pull & up
  8. Kiểm tra sức khỏe (18x retries)
  9. Lưu trạng thái triển khai
```

### GitHub Secrets dùng cho Staging

Workflow staging lấy toàn bộ cấu hình runtime từ GitHub Secrets, không tạo `.env` thủ công trên EC2.

| Secret | Vai trò |
|--------|--------|
| `SSH_HOST` | Public IP/EIP của monitor instance |
| `SSH_PORT` | SSH port, thường là `22` |
| `SSH_PRIVATE_KEY` | Private key để GitHub Actions SSH vào EC2 |
| `GHCR_USERNAME` | Username để login GHCR |
| `GHCR_TOKEN` | Token để push/pull GHCR packages |
| `GEMINI_API_KEY` | Gemini API key cho AI Agent |
| `TELEGRAM_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat ID |
| `AI_AGENT_PUBLIC_URL` | Public URL của AI Agent nếu cần |
| `DATABASE_URL` | Database URL cho service cần DB |
| `SECRET_KEY` | Secret key cho backend/API |

### Cách trigger staging

```bash
git checkout develop
git push origin develop

# Hoặc chạy thủ công:
# GitHub → Actions → CD Staging → Run workflow
```

### Kiểm tra trên GitHub

```text
GitHub → Actions → CD Staging → run mới nhất

Kiểm tra các step:
- Login to GHCR
- Build & push AI Agent
- Build & push Payment API
- Prepare environment files
- Preflight SSH authentication
- Copy files to EC2 using SCP
- Run deploy script on EC2
```

### Cổng Dịch vụ trên Staging (monitor-ai-01)

```
AI Agent:       http://52.74.118.8:18000/health
Prometheus:     http://52.74.118.8:9090
Grafana:        http://52.74.118.8:3000
```

### Kiểm tra Dịch vụ

```bash
ssh -i "$SSH_KEY_PATH" ec2-user@52.74.118.8
cd /home/ec2-user/aws-hybrid

# Kiểm tra containers đang chạy
docker compose -f release/docker-compose.staging.yml ps

# Kiểm tra log
docker compose -f release/docker-compose.staging.yml logs ai-agent
docker compose -f release/docker-compose.staging.yml logs payment-api

# Kiểm tra endpoints
curl http://localhost:18000/health
curl http://localhost:18080/api/health

# Phản hồi kỳ vọng:
# {
#   "status": "healthy",
#   "queue": "ok",
#   "redis": "ok"
# }
```

---

## 🏢 Triển khai Môi trường Production (monitor-ai-01: 52.74.118.8)

### Triển khai qua GitHub Actions

```
Workflow: cd-production.yml
Kích hoạt: Tạo tag git (v*) hoặc workflow_dispatch với release_tag
Hành động:
  1. Build Docker images với production tag
  2. Đẩy lên GHCR
  3. Tạo release/.env.production từ GitHub Secrets
  4. Yêu cầu phê duyệt environment production nếu GitHub Environment đang bật approval
  5. SSH tới monitor instance bằng SSH_PRIVATE_KEY
  6. Copy release/ và automation/ lên EC2
  7. Chạy: automation/app-release-deploy.sh production {release-tag}
  8. Docker compose pull & up (production config)
  9. Kiểm tra sức khỏe (18x retry)
  10. Lưu trạng thái triển khai
```

### GitHub Secrets dùng cho Production

Production dùng cùng nhóm secrets với staging, và thêm `PROMETHEUS_URL` nếu production cần trỏ AI Agent/API tới Prometheus.

| Secret | Vai trò |
|--------|--------|
| `SSH_HOST` | Public IP/EIP của monitor instance |
| `SSH_PORT` | SSH port, thường là `22` |
| `SSH_PRIVATE_KEY` | Private key để GitHub Actions SSH vào EC2 |
| `GHCR_USERNAME` | Username để login GHCR |
| `GHCR_TOKEN` | Token để push/pull GHCR packages |
| `GEMINI_API_KEY` | Gemini API key cho AI Agent |
| `TELEGRAM_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat ID |
| `AI_AGENT_PUBLIC_URL` | Public URL của AI Agent nếu cần |
| `DATABASE_URL` | Database URL cho service cần DB |
| `SECRET_KEY` | Secret key cho backend/API |
| `PROMETHEUS_URL` | Prometheus URL cho production monitoring |

**Luồng công việc triển khai:**

```bash
# Trên máy local - tạo và đẩy tag production
git tag v1.0.0
git push origin v1.0.0

# → GitHub Actions tự động:
#   1. Build images với tag v1.0.0
#   2. Chờ phê duyệt trong GitHub
#   3. Triển khai tới production trên monitor instance
```

Hoặc chạy thủ công:

```text
GitHub → Actions → CD Production → Run workflow → release_tag = v1.0.0
```

**Phê duyệt GitHub Actions:**
```
GitHub → Actions → cd-production.yml run → Phê duyệt triển khai → Phê duyệt
```

### Cổng Dịch vụ trên Production (monitor-ai-01)

```
AI Agent:       http://52.74.118.8:8000/health
Prometheus:     http://52.74.118.8:9090
Grafana:        http://52.74.118.8:3000
```

### Cấu hình Production

Docker-compose production sử dụng:
- **Cổng 8000** cho AI Agent (thay vì 18000 cho staging)
- Các biến môi trường giống staging
- Cùng kiểm tra sức khỏe và giám sát

**Kiểm tra Production:**

```bash
ssh -i "$SSH_KEY_PATH" ec2-user@52.74.118.8
cd /home/ec2-user/aws-hybrid

# Kiểm tra containers đang chạy
docker compose -f release/docker-compose.production.yml ps

# Kiểm tra log
docker compose -f release/docker-compose.production.yml logs ai-agent

# Kiểm tra endpoints
curl http://localhost:8000/health
curl http://localhost:8080/api/health
```

### Hoàn trả ngược Production

Nếu triển khai thất bại:

```bash
# SSH vào monitor
ssh -i "$SSH_KEY_PATH" ec2-user@52.74.118.8

cd /home/ec2-user/aws-hybrid

# 1. Kéo phiên bản trước đó
docker pull ghcr.io/{owner}/aws-hybrid-ai-agent:v0.9.9

# 2. Cập nhật docker-compose
sed -i 's/v1.0.0/v0.9.9/g' release/.env.production

# 3. Triển khai lại
./automation/app-release-deploy.sh production v0.9.9

# 4. Kiểm tra
docker compose -f release/docker-compose.production.yml ps
curl http://localhost:8000/health
```

## ✅ Kiểm tra & Validation

### Health Check Checklist

```bash
# 1. Service Status
┌─────────────────────┐
│ docker compose ps   │
├─────────────────────┤
│ ai-agent: UP        │ ✅
│ payment-api: UP     │ ✅
└─────────────────────┘

# 2. Port Binding
┌──────────────────────────────┐
│ netstat -tlnp                │
├──────────────────────────────┤
│ Staging:                     │
│  LISTEN 0.0.0.0:18000 ✅     │
│  LISTEN 0.0.0.0:18080 ✅     │
│ Production:                  │
│  LISTEN 0.0.0.0:8000 ✅      │
│  LISTEN 0.0.0.0:8080 ✅      │
└──────────────────────────────┘

# 3. API Response
┌──────────────────────────────┐
│ curl -s http://localhost:    │
│        18000/health | jq     │
├──────────────────────────────┤
│ {                            │
│   "status": "healthy",       │ ✅
│   "queue": "ok",             │ ✅
│   "redis": "ok"              │ ✅
│ }                            │
└──────────────────────────────┘

# 4. Container Logs
┌──────────────────────────────┐
│ docker compose logs          │
│   ai-agent -f --tail=20      │
├──────────────────────────────┤
│ No errors                    │ ✅
│ All services started         │ ✅
└──────────────────────────────┘

# 5. Network Connectivity
┌──────────────────────────────┐
│ docker network inspect       │
│   staging_default            │
├──────────────────────────────┤
│ All containers connected     │ ✅
│ All services can reach each  │ ✅
│   other via service name     │
└──────────────────────────────┘

# 6. Volume Mount
┌──────────────────────────────┐
│ docker inspect <container>   │
│   | grep Mounts -A10         │
├──────────────────────────────┤
│ Volumes mounted correctly    │ ✅
│ Permissions correct          │ ✅
└──────────────────────────────┘

# 7. Environment Variables
┌──────────────────────────────┐
│ docker exec ai-agent env     │
│   | grep ENVIRONMENT         │
├──────────────────────────────┤
│ ENVIRONMENT=staging          │ ✅
│ DB_HOST correct              │ ✅
└──────────────────────────────┘
```

### Validation Script

```bash
#!/bin/bash
# File: automation/validate-deployment.sh

set -e

ENVIRONMENT=${1:-staging}
PORT_HEALTH=18000
API_PORT=18080

if [ "$ENVIRONMENT" = "production" ]; then
  PORT_HEALTH=8000
  API_PORT=8080
fi

echo "🔍 Validating $ENVIRONMENT deployment..."

# 1. Check services running
echo "Checking services..."
docker compose ps | grep -E "ai-agent|payment-api" || exit 1

# 2. Check ports
echo "Checking ports..."
netstat -tlnp | grep -E ":$PORT_HEALTH |:$API_PORT " || exit 1

# 3. Health check AI Agent
echo "Health check AI Agent..."
RESPONSE=$(curl -s http://localhost:$PORT_HEALTH/health)
echo "$RESPONSE" | grep -q "healthy" || exit 1

# 4. Health check API
echo "Health check API..."
RESPONSE=$(curl -s http://localhost:$API_PORT/api/health)
echo "$RESPONSE" | grep -q "healthy" || exit 1

# 5. Check logs for errors
echo "Checking logs..."
docker compose logs --tail=50 | grep -i error && exit 1

echo "✅ All validations passed!"
```

---

## 📊 Giám sát & Logs

### Xem Logs - Lệnh Cơ bản

```bash
# 1. Kiểm tra containers trên tất cả EC2 bằng Ansible
ansible all -i ansible/inventory.ini -m shell -a "docker ps --format 'table {{.Names}}\t{{.Status}}'"

# 2. Logs AI Agent trên monitor instance
ansible monitor -i ansible/inventory.ini -m shell -a "cd /opt/ai-agent && docker-compose logs --tail=100 ai-agent"

# 3. Follow logs trực tiếp bằng SSH khi cần debug sâu
ssh -i "$SSH_KEY_PATH" ec2-user@52.74.118.8
cd /opt/ai-agent
docker-compose logs -f ai-agent

# 4. Truy cập logs container trực tiếp
docker logs <container-id>
docker logs --tail=100 <container-id>
docker logs --follow <container-id>  # Thực tế

# 5. Logs Prometheus/Grafana trên monitor
cd /opt/prometheus && docker-compose logs --tail=100
cd /opt/grafana && docker-compose logs --tail=100

# 6. Lưu logs và tìm kiếm
cd /opt/ai-agent
docker-compose logs > /tmp/ai-agent-deploy.log
grep "ERROR\|WARNING" /tmp/ai-agent-deploy.log
```

---

### Các Lỗi Thường gặp & Giải pháp

#### ❌ Lỗi 1: Container Exit Code 1 (Lỗi chung)

**Ví dụ Log:**
```
ai-agent exited with code 1
```

**Chẩn đoán:**
```bash
# 1. Kiểm tra logs khi thoát
docker compose logs ai-agent --tail=50

# 2. Tìm kiếm:
# - Lỗi cú pháp Python
# - Lỗi nhập khẩu module
# - Biến môi trường bị thiếu
# - Cổng đã được sử dụng
# - Kết nối cơ sở dữ liệu bị từ chối
```

**Nguyên nhân thường gặp:**
```
- PYTHONUNBUFFERED không được đặt → output bị đệm
- GEMINI_API_KEY bị thiếu → lỗi nhập khẩu
- Phụ thuộc bị thiếu → ModuleNotFoundError
- Cổng 8000 đã bị ràng buộc → AddressInUse
```

**Sửa chữa:**
```bash
docker compose down
docker compose pull
docker compose up -d
docker compose logs ai-agent
```

---

#### ❌ Lỗi 2: Kết nối bị từ chối

**Ví dụ Log:**
```
ERROR - Connection refused to localhost:5432
ConnectionRefusedError: [Errno 111] Connection refused
```

**Chẩn đoán:**
```bash
# 1. Kiểm tra nếu dịch vụ đang chạy
docker compose ps

# 2. Kiểm tra ràng buộc cổng
netstat -tlnp | grep 5432

# 3. Kiểm tra logs dịch vụ
docker compose logs payment-api --tail=50

# 4. Kiểm tra kết nối
docker exec ai-agent curl http://payment-api:8000/health
```

**Giải pháp:**
```bash
# Nếu cơ sở dữ liệu không chạy
docker compose restart postgres

# Nếu dịch vụ chưa sẵn sàng
docker compose logs payment-api | grep "Uvicorn running"

# Chờ khởi động dịch vụ
sleep 10
curl http://localhost:18000/health
```

---

#### ❌ Lỗi 3: Hết bộ nhớ (OOM)

**Ví dụ Log:**
```
killed (signal 9)
Killed
Exception in thread "Finalizer": java.lang.OutOfMemoryError
```

**Chẩn đoán:**
```bash
# Kiểm tra mức sử dụng bộ nhớ
docker stats ai-agent payment-api

# Kiểm tra giới hạn container
docker inspect ai-agent | grep -A5 "Memory"

# Kiểm tra bộ nhớ hệ thống
free -h
df -h
```

**Giải pháp:**
```bash
# Tăng giới hạn bộ nhớ trong docker-compose
# ai-agent:
#   deploy:
#     resources:
#       limits:
#         memory: 2G

# Khởi động lại với giới hạn mới
docker compose down
docker compose up -d
docker stats
```

---

#### ❌ Lỗi 4: Cổng đã được sử dụng

**Ví dụ Log:**
```
Error starting userland proxy: listen tcp 0.0.0.0:18000: bind: address already in use
```

**Chẩn đoán:**
```bash
# Tìm kiếm điều gì đang sử dụng cổng
lsof -i :18000
netstat -tlnp | grep 18000
ss -tlnp | grep 18000
```

**Giải pháp:**
```bash
# Kết thúc quy trình
kill -9 <PID>

# Hoặc dừng container
docker ps -a | grep 18000
docker kill <container-id>

# Hoặc thay đổi cổng trong docker-compose
# ports:
#   - "18001:8000"  # Sử dụng cổng khác
```

---

#### ❌ Lỗi 5: Kiểm tra Sức khỏe Hết thời gian

**Ví dụ Log:**
```
Health check failed: timeout reached
Starting 2nd attempt
```

**Chẩn đoán:**
```bash
# Kiểm tra nếu dịch vụ đang phản hồi
curl -v http://localhost:18000/health

# Kiểm tra logs trong khi kiểm tra sức khỏe
docker compose logs ai-agent -f

# Kiểm tra ràng buộc cổng
netstat -tlnp | grep 18000

# Kiểm tra ràng buộc tài nguyên
docker stats ai-agent
```

**Giải pháp:**
```bash
# Chờ lâu hơn (dịch vụ có thể khởi động chậm)
sleep 15
curl http://localhost:18000/health

# Tăng thời gian chờ kiểm tra sức khỏe
# healthcheck:
#   test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
#   interval: 30s
#   timeout: 10s  # Tăng giá trị này
#   retries: 3
#   start_period: 40s  # Chờ trước khi kiểm tra đầu tiên

# Khởi động lại với cấu hình mới
docker compose down
docker compose up -d
```

---

### Hướng dẫn Phân tích Log chi tiết

#### Bước 1: Chụp Ngữ cảnh Lỗi Đầy đủ

```bash
# Chụp lỗi với các dòng xung quanh
docker compose logs ai-agent 2>&1 | tee debug.log

# Tìm lỗi
grep -n "ERROR\|EXCEPTION\|Failed\|Traceback" debug.log

# Show context (10 lines before/after error)
grep -B10 -A10 "ERROR\|EXCEPTION" debug.log
```

#### Bước 2: Xác định Loại Lỗi

**Lỗi Python:**
```
Traceback (most recent call last):       ← Bắt đầu stack trace
  File "main.py", line 45, in <module>
ModuleNotFoundError: No module named 'x'  ← Loại lỗi và tin nhắn
```

**Lỗi Docker:**
```
ERROR: failed to solve with frontend dockerfile.v0
```

**Lỗi Mạng:**
```
ConnectionError: [Errno 110] Connection timed out
requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected(...))
```

**Lỗi Cấu hình:**
```
ValueError: invalid literal for int() with base 10: 'invalid'
KeyError: 'GEMINI_API_KEY'
```

#### Bước 3: Theo dõi Nguyên nhân gốc

**Ví dụ 1: ModuleNotFoundError**
```
ERROR: ModuleNotFoundError: No module named 'google'

Hành động:
1. Kiểm tra requirements.txt có "google-generativeai"
2. Xác minh pip install đã chạy thành công
3. Xây dựng lại Docker image: docker compose build
4. Xác minh: docker exec ai-agent pip list | grep google
```

**Ví dụ 2: Kết nối bị từ chối**
```
ERROR: ConnectionRefusedError: [Errno 111] Connection refused

Hành động:
1. Kiểm tra dịch vụ đích đang chạy: docker compose ps
2. Kiểm tra cổng chính xác: grep "ports:" docker-compose.yml
3. Kiểm tra tường lửa: netstat -tlnp | grep 5432
4. Khởi động lại dịch vụ: docker compose restart postgres
```

**Ví dụ 3: Hết bộ nhớ**
```
ERROR: Killed

Hành động:
1. Kiểm tra bộ nhớ: docker stats ai-agent
2. Kiểm tra giới hạn: docker inspect ai-agent | grep Memory
3. Tăng giới hạn trong docker-compose.yml
4. Khởi động lại: docker compose down && docker compose up -d
```

#### Bước 4: Trích xuất Thông tin Có hành động

```bash
# Count errors by type
grep "ERROR" debug.log | awk -F: '{print $NF}' | sort | uniq -c

# Find first error
grep -m1 "ERROR\|EXCEPTION" debug.log

# Find last error
grep "ERROR\|EXCEPTION" debug.log | tail -1

# Dòng thời gian các lỗi
grep "ERROR" debug.log | awk '{print $1}' | sort -u
```

---

### Kiểm tra GitHub Actions Log

#### Bước 1: Truy cập GitHub Actions Logs

```
GitHub Repo → Actions → [Workflow Name] → [Run #] → [Job] → Logs
```

#### Bước 2: Tìm kiếm Lỗi trong Logs

```
Ctrl+F (hoặc Cmd+F trên Mac) → Tìm kiếm:
- "error"
- "failed"
- "exit code"
- "FAILED"
```

#### Bước 3: Các Lỗi CI phổ biến

**❌ Lint thất bại:**
```
Lint (critical rules)
E9: SyntaxError in agent_src/main.py:45: invalid syntax
```

**Sửa:**
```bash
ruff check agent_src --show-fixes
# Sửa lỗi cú pháp
git add agent_src
git commit -m "fix: syntax error"
git push
```

**❌ Test thất bại:**
```
Test AI Agent (pytest)
FAILED agent_src/tests/test_health.py::test_endpoint
AssertionError: assert 404 == 200
```

**Sửa:**
```bash
pytest -v agent_src/tests/test_health.py
# Fix test or code
git add .
git commit -m "fix: test assertion"
git push
```

**❌ Docker Build Failed:**
```
Build & push AI Agent
ERROR: failed to solve with frontend dockerfile.v0
lstat /agent_src/missing_file: no such file or directory
```

**Fix:**
```bash
# Check Dockerfile COPY commands
docker build -t test agent_src
# Add missing files or fix paths
git add .
git commit -m "fix: docker build"
git push
```

**❌ SSH Deploy Failed:**
```
Deploy to staging EC2 via SSH
Permission denied (publickey)
```

**Sửa:**
```bash
# Xác minh SSH credentials trong GitHub Secrets
# SSH_PRIVATE_KEY, SSH_HOST, SSH_USER, SSH_PORT đều chính xác
# Chạy lại workflow
```

#### Bước 4: Tải xuống Đầy đủ Logs

```
GitHub Actions → [Run] → Summary → Tải xuống logs (zip)
```

---

### Các Kỹ thuật Gỡ lỗi Log Container

#### Kỹ thuật 1: Giám sát Thực tế (Hai terminal)

**Terminal 1: Xem logs**
```bash
ssh -i "$SSH_KEY_PATH" ec2-user@52.74.118.8
cd /opt/ai-agent
docker-compose logs -f ai-agent --timestamps
```

**Terminal 2: Kích hoạt hành động**
```bash
curl -X POST http://localhost:18000/detect \
  -H "Content-Type: application/json" \
  -d '{"event": "test"}'
```

**Đầu ra Terminal 1:**
```
ai-agent  | 2026-04-24T10:30:45.123Z INFO - Received request
ai-agent  | 2026-04-24T10:30:45.456Z DEBUG - Processing event
ai-agent  | 2026-04-24T10:30:45.789Z INFO - Response sent
```

#### Kỹ thuật 2: Shell Tương tác

```bash
# Truy cập shell container
docker exec -it ai-agent bash

# Bên trong container
python -c "import google; print(google.__version__)"
curl http://payment-api:8000/health
env | grep GEMINI
ls -la /app/
```

#### Kỹ thuật 3: Phân tích File Log

```bash
# Lưu tất cả logs vào file
docker compose logs > /tmp/all-logs.log

# Phân tích với grep
grep -E "ERROR|WARN|INFO" /tmp/all-logs.log | cut -d'|' -f2 | sort | uniq -c

# Hiển thị lỗi có dấu thời gian
grep "ERROR" /tmp/all-logs.log | awk '{print $1, $NF}'

# Tìm các vấn đề về hiệu suất
grep "took.*ms" /tmp/all-logs.log | awk '{print $NF}' | sort -rn | head -10
```

#### Kỹ thuật 4: Giám sát Tài nguyên

```bash
# Giám sát tài nguyên khi chạy
watch -n 1 'docker stats --no-stream ai-agent payment-api'

# Kiểm tra file descriptors
docker exec ai-agent lsof | wc -l

# Kiểm tra kết nối
docker exec ai-agent netstat -an | grep ESTABLISHED | wc -l

# Mức sử dụng bộ nhớ
docker exec ai-agent ps aux | grep python
```

---

### Giải thích File Log

#### Định dạng Log Docker Compose

```
tên-dịch-vụ | dấu-thời-gian | mức-độ | tin-nhắn

Ví dụ:
ai-agent | 2026-04-24T10:30:45.123456789Z INFO - Uvicorn running on 0.0.0.0:8000
payment-api | 2026-04-24T10:30:46.987654321Z INFO - Server started
```

#### Cấp độ Log

| Cấp độ | Ý nghĩa | Ví dụ |
|--------|---------|--------|
| DEBUG | Thông tin chẩn đoán chi tiết | Giá trị biến, gọi hàm |
| INFO | Thông tin chung | Máy chủ đã bắt đầu, yêu cầu nhận được |
| WARNING | Cảnh báo | Chức năng không dùng nữa, bộ nhớ thấp |
| ERROR | Lỗi xảy ra nhưng tiếp tục | Không thể kết nối, đầu vào không hợp lệ |
| CRITICAL | Lỗi nghiêm trọng, có thể thoát | Hết bộ nhớ, hệ thống file đầy |

#### Ví dụ Log Kiểm tra Sức khỏe

```bash
# Tốt
ai-agent | health check passed (response time: 45ms)

# Cảnh báo
ai-agent | health check slow (response time: 2456ms)

# Thất bại
ai-agent | health check failed (attempt 1/3): connection refused
ai-agent | health check failed (attempt 2/3): timeout
ai-agent | health check failed (attempt 3/3): timeout
ai-agent | health check failed: service will be restarted
```

---

### Thiết lập Xoay vòng Log

```bash
# File: /etc/logrotate.d/ai-agent

/opt/ai-agent/logs/*.log {
  daily                    # Xoay hàng ngày
  rotate 7                 # Giữ 7 ngày
  compress                 # Nén logs cũ (gzip)
  delaycompress            # Không nén log mới nhất
  notifempty               # Không xoay nếu trống
  missingok                # Không lỗi nếu thiếu
  create 0640 ec2-user ec2-user # Tệp mới: quyền 640
  sharedscripts
  postrotate
    cd /opt/ai-agent && docker-compose restart ai-agent > /dev/null 2>&1 || true
  endscript
}

# Kiểm tra logrotate
sudo logrotate -f /etc/logrotate.d/ai-agent

# Xác minh
ls -la /opt/ai-agent/logs/
```

---

### Thiết lập Giám sát (Prometheus + Grafana)

```bash
# Prometheus, AlertManager và Grafana được tạo bởi Ansible.
# Không cần docker run thủ công.

cd "$PROJECT_ROOT"
ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-complete-infrastructure.yml -v

# Kiểm tra trên monitor instance
ansible monitor -i ansible/inventory.ini -m shell -a "cd /opt/prometheus && docker-compose ps"
ansible monitor -i ansible/inventory.ini -m shell -a "cd /opt/grafana && docker-compose ps"

# Truy cập các bảng điều khiển
# Prometheus: http://52.74.118.8:9090
#   - Targets → Kiểm tra sức khỏe
#   - Graph → Truy vấn số liệu
#
# Grafana: http://52.74.118.8:3000 (admin/admin123)
#   - Datasource Prometheus được provision bởi Ansible
#   - Dashboards được provision bởi Ansible
#   - Đặt cảnh báo

# 5. Các truy vấn Prometheus hữu ích
# Container CPU: container_cpu_usage_seconds_total
# Container Memory: container_memory_usage_bytes
# HTTP Requests: http_requests_total
# Error Rate: rate(errors_total[5m])
```

---

### Tham khảo nhanh Xem Log

| Lệnh | Mục đích |
|------|---------|
| `docker compose logs ai-agent` | Hiển thị tất cả logs cho ai-agent |
| `docker compose logs -f` | Theo dõi logs (thực tế) |
| `docker compose logs --tail=50` | 50 dòng cuối cùng |
| `docker compose logs --since 10m` | 10 phút gần đây |
| `docker logs <container-id>` | Logs container trực tiếp |
| `docker inspect <container-id>` | Chi tiết container & cấu hình |
| `docker exec <container> bash` | Truy cập shell container |
| `docker stats <container>` | Mức sử dụng CPU/Bộ nhớ |
| `netstat -tlnp` | Hiển thị các cổng mở |
| `grep ERROR <logfile>` | Tìm lỗi trong file |
| `tail -f <logfile>` | Theo dõi cập nhật file |
| `journalctl -u docker` | Logs dịch vụ Docker |
| `dmesg` | Logs kernel (OOM kills, v.v) |

---

## 🔧 Khắc phục sự cố

### Vấn đề 1: Cổng đã được sử dụng

```bash
# Vấn đề: Lỗi ràng buộc cổng 18000

# Giải pháp:
lsof -i :18000
kill -9 <PID>

# HOẶC tìm kiếm thứ gì đang sử dụng nó
ss -tlnp | grep 18000
docker ps -a | grep 18000
```

### Vấn đề 2: Container Bị sập khi Khởi động

```bash
# Kiểm tra logs
docker compose logs ai-agent --tail=50

# Các vấn đề phổ biến:
# - Biến môi trường bị thiếu
# - Cổng đã bị ràng buộc
# - Ràng buộc bộ nhớ/CPU
# - Không thể kéo image

# Giải pháp:
docker compose down
docker compose pull
docker compose up -d
```

### Vấn đề 3: Các vấn đề Mạng

```bash
# Container không thể tiếp cận các dịch vụ bên ngoài

# 1. Kiểm tra DNS
docker exec ai-agent nslookup google.com

# 2. Kiểm tra mạng
docker network ls
docker network inspect staging_default

# 3. Kiểm tra tường lửa (Security Groups)
# AWS Console → Security Groups
# Xác minh các quy tắc gửi đi cho phép lưu lượng
```

### Vấn đề 4: Không đủ dung lượng đĩa

```bash
# Kiểm tra đĩa
df -h
du -sh /var/lib/docker

# Giải pháp:
docker system prune -a
docker volume prune

# Hoặc dọn dẹp các images cũ:
docker image rm $(docker image ls -q -f "dangling=true")
```

### Vấn đề 5: Xác thực GHCR thất bại

```bash
# Vấn đề: Error response from daemon: unauthorized

# Giải pháp:
docker logout ghcr.io
echo $GHCR_TOKEN | docker login ghcr.io -u $GHCR_USERNAME --password-stdin

# Xác minh token có quyền:
# GitHub → Settings → Personal access tokens
# Kiểm tra: read:packages, write:packages
```

### Vấn đề 6: Kiểm tra sức khỏe Hết thời gian

```bash
# Vấn đề: curl: (7) Failed to connect

# Giải pháp:
# 1. Kiểm tra dịch vụ đang chạy
docker compose ps

# 2. Kiểm tra cổng
netstat -tlnp | grep 18000

# 3. Kiểm tra tường lửa
sudo ufw status
sudo ufw allow 18000

# 4. Chờ khởi động dịch vụ
sleep 10
curl http://localhost:18000/health
```

---

## 🆘 Phục hồi Thảm họa

### Chiến lược Sao lưu

```bash
# 1. Sao lưu cơ sở dữ liệu (nếu sử dụng)
docker exec postgres pg_dump -U admin database_name > backup.sql

# 2. Sao lưu các volume
docker run --rm \
  -v staging_data:/data \
  -v /opt/backups:/backup \
  alpine tar czf /backup/data-$(date +%Y%m%d).tar.gz -C /data .

# 3. Sao lưu cấu hình
tar czf /opt/backups/config-$(date +%Y%m%d).tar.gz \
  /opt/ai-agent/.env \
  /opt/ai-agent/docker-compose.yml \
  /opt/prometheus/prometheus.yml \
  /opt/alertmanager/alertmanager.yml \
  /opt/grafana/provisioning
```

### Quy trình Hoàn trả ngược

```bash
# 1. Nếu container bị hỏng
docker compose pull <previous-tag>
docker compose up -d

# 2. Nếu triển khai bị hỏng (thông qua GitHub)
# GitHub → Releases → Chọn phiên bản trước
# Tạo tag (git tag v1.0.0) → Đẩy
# Workflow CD tự động triển khai

# 3. Hoàn trả ngược thủ công
docker compose down
docker image rm ghcr.io/owner/ai-agent:staging-latest
docker pull ghcr.io/owner/ai-agent:staging-abc123  # hash trước đó
docker tag ghcr.io/owner/ai-agent:staging-abc123 ghcr.io/owner/ai-agent:staging-latest
docker compose up -d
```

### Tắt máy Khẩn cấp

```bash
# Nếu bạn cần tắt máy tất cả:
docker compose down

# Dừng tất cả containers
docker stop $(docker ps -q)

# Xóa tất cả containers
docker rm $(docker ps -aq)

# Dọn dẹp tất cả (NGUY HIỂM!)
docker system prune -a --volumes
```

---

## 📋 Danh sách Kiểm tra Cuối cùng

### Trước khi Đi trực tiếp

- [ ] Tài khoản AWS được tạo
- [ ] Khóa SSH được tạo và lưu trữ ⭐ (bắt buộc để triển khai)
- [ ] Cơ sở hạ tầng Terraform được tạo (chạy cục bộ)
- [ ] Người dùng IAM được tạo (tùy chọn - chỉ nếu tự động hóa Terraform)
- [ ] EC2 instances đang chạy
- [ ] Docker được cài đặt trên tất cả instances
- [ ] Các file môi trường được cấu hình
- [ ] GitHub Secrets được cấu hình (SSH_HOST, SSH_PORT, SSH_PRIVATE_KEY, GHCR credentials)
- [ ] Triển khai staging thành công
- [ ] Tất cả kiểm tra sức khỏe đang vượt qua
- [ ] Triển khai production thành công
- [ ] Thiết lập giám sát hoàn tất
- [ ] Logs đang được thu thập
- [ ] Chiến lược sao lưu đã có sẵn
- [ ] Team trained on procedures
- [ ] Documentation complete
- [ ] Disaster recovery tested

### Post-Deployment

- [ ] Monitor logs for 24 hours
- [ ] Run load tests
- [ ] Test rollback procedure
- [ ] Verify backups working
- [ ] Team does dry-run of scenarios
- [ ] Update runbooks
- [ ] Create on-call rotation
- [ ] Schedule regular reviews

---

## 🆘 Getting Help

**If something goes wrong:**

1. Check logs: `docker compose logs -f`
2. Verify configuration: `docker compose config`
3. Check health: `curl http://localhost:PORT/health`
4. Read troubleshooting section above
5. Contact DevOps team with:
   - Error message
   - Command you ran
   - Output/logs
   - Environment (staging/production)
   - When it started failing

---
