# 📚 Hướng dẫn Tạo Hạ tầng AWS & Deploy CI/CD System 

---

## 📑 Mục lục

1. [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
2. [Chuẩn bị AWS Account](#chuẩn-bị-aws-account)
3. [Tạo Infrastructure với Terraform](#tạo-infrastructure-với-terraform)
4. [Setup EC2 Instances](#setup-ec2-instances)
5. [Install Docker & Docker Compose](#install-docker--docker-compose)
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
│   ├── deploy.sh           # Main deployment orchestrator
│   ├── deploy-infrastructure.sh
│   ├── ansible-deploy.sh
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
│  GITHUB REPOSITORY                  │
├─────────────────────────────────────┤
│ Step 4: Setup GitHub Secrets        │
│   - SSH_HOST (from terraform)       │
│   - SSH_PORT (22)                   │
│   - SSH_PRIVATE_KEY ⭐              │
│   - GHCR_USERNAME                   │
│   - GHCR_TOKEN                      │
│                                     │
│ Step 5: Trigger CI/CD Workflow      │
│   - Push to develop → Staging       │
│   - Tag v1.0.0 → Production         │
│                                     │
│ Result: Auto deploy via SSH         │
└─────────────────────────────────────┘
```

**🔑 Chỉ cần AWS credentials (Access Key) khi:**
- Chạy `terraform init/apply` trên local machine
- KH\u00d4NG cần trong GitHub Actions (SSH deployment đủ)

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

**Bắt buộc** để GitHub Actions deploy tới EC2 instances.

```bash
# Trong AWS Console → EC2 → Key Pairs
# Click "Create key pair"
# 
# Name: aws-hybrid-key
# Type: RSA
# Format: .pem (Linux/Mac) or .ppk (Windows with PuTTY)
#
# Download file: aws-hybrid-key.pem
# chmod 400 aws-hybrid-key.pem  # Linux/Mac
# 
# Save to GitHub Secrets:
# SSH_PRIVATE_KEY = content của aws-hybrid-key.pem
```

### Step 4: Kiểm tra GitHub Secrets trước khi chạy CI/CD

Trước khi trigger workflow `CD Staging` hoặc `CD Production`, kiểm tra repository đã có đủ secrets cần thiết.

**Secrets cho CI/CD Deployment:**

| Secret | Mục đích | Status | Ghi chú |
|--------|----------|--------|---------|
| `SSH_HOST` | EC2 target để deploy | ⭐ **BẮT BUỘC** | Public IP của EC2 (lấy từ `terraform output`) |
| `SSH_PORT` | SSH port | ⭐ **BẮT BUỘC** | Thường là `22` |
| `SSH_PRIVATE_KEY` | SSH key để GitHub Actions vào EC2 | ⭐ **BẮT BUỘC** | Nội dung private key `aws-hybrid-key.pem` đầy đủ |
| `GHCR_USERNAME` | Login GitHub Container Registry | ⭐ **BẮT BUỘC** | GitHub username hoặc bot account |
| `GHCR_TOKEN` | Pull/push image trên GHCR | ⭐ **BẮT BUỘC** | PAT có quyền `read:packages`, `write:packages`; nếu repo private cần `repo` |
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

KH\u00d4NG C\u1ea6N cho CI/CD deployment (ch\u1ec1 d\u00f9ng local):
❌ AWS_ACCESS_KEY_ID (ch\u1ec9 d\u00f9ng khi ch\u1ea1y Terraform tr\u00ean local)
❌ AWS_SECRET_ACCESS_KEY (ch\u1ec9 d\u00f9ng khi ch\u1ea1y Terraform tr\u00ean local)
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
SSH_PRIVATE_KEY: <key content>      # Nội dung aws-hybrid-key.pem
GHCR_USERNAME: your-github-name     # Tên người dùng GitHub
GHCR_TOKEN: ghp_xxxxxxxxx...        # Token GitHub có phạm vi packages
```

**Kiểm tra trước chuyến bay (máy local):**

```bash
# Kiểm tra kết nối SSH tới monitor instance
ssh -i aws-hybrid-key.pem -p 22 ec2-user@52.74.118.8 'echo "SSH OK"'

# Kiểm tra Docker trên monitor instance
ssh -i aws-hybrid-key.pem ec2-user@52.74.118.8 'docker --version && docker compose version'

# Kiểm tra đăng nhập GHCR
echo $GHCR_TOKEN | docker login ghcr.io -u $GHCR_USERNAME --password-stdin
ssh -i aws-hybrid-key.pem ec2-user@<SSH_HOST> 'docker --version && docker compose version'
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
cd /path/to/aws-hybrid/terraform

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
aws_profile = "default"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
vpc_name = "aws-hybrid-vpc"

# Subnets
subnet_1_cidr = "10.0.1.0/24"   # 2a (AZ 1)
subnet_1_az   = "ap-southeast-1a"
subnet_1_name = "subnet-staging"

subnet_2_cidr = "10.0.2.0/24"   # 2b (AZ 2)
subnet_2_az   = "ap-southeast-1b"
subnet_2_name = "subnet-production"

# EC2 Instances
instance_type = "t3.medium"     # 2 CPU, 4GB RAM
ami_filter    = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"

# Instance Configuration
instance_count_staging = 1
instance_count_production = 1
instance_monitoring_count = 1

# Security Groups
enable_http  = true    # Allow 80
enable_https = true    # Allow 443
allow_ssh_cidr = ["0.0.0.0/0"]  # Change to restricted IP!

# Tags
project_name = "aws-hybrid"
environment  = "staging"
EOF
```

**⚠️ QUAN TRỌNG:**
```
- Đổi allow_ssh_cidr từ 0.0.0.0/0 thành IP cụ thể của bạn
- Để nguyên region ap-southeast-1 (Singapore - gần nhất)
- Instance type: t3.medium hoặc t3.small tùy budget
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
# staging_ip = "13.251.123.45"
# production_ip = "13.251.123.46"
```

### Bước 4: Lưu Giá trị Outputs

```bash
# Lấy giá trị từ terraform
terraform output -json > outputs.json

# Hoặc sao chép thủ công:
echo "Staging IP: $(terraform output -raw staging_public_ip)"
echo "Production IP: $(terraform output -raw production_public_ip)"

# Cập nhật GitHub Secrets:
# SSH_HOST = staging_public_ip (thay đổi theo môi trường)
```

---

## 🖥️ Thiết lập EC2 Instances

### Bước 1: Kết nối tới EC2

```bash
# 1. Lấy IP công khai từ Terraform output
STAGING_IP=$(terraform output -raw staging_public_ip)
PROD_IP=$(terraform output -raw production_public_ip)

# 2. SSH vào staging
ssh -i aws-hybrid-key.pem ubuntu@$STAGING_IP

# 3. Cập nhật hệ thống
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

### Bước 2: Tạo Cấu trúc Thư mục

```bash
# 1. Tạo thư mục ứng dụng
sudo mkdir -p /opt/aws-hybrid/staging
sudo mkdir -p /opt/aws-hybrid/production
sudo mkdir -p /opt/aws-hybrid/logs

# 2. Đặt quyền
sudo chown -R ubuntu:ubuntu /opt/aws-hybrid
chmod -R 755 /opt/aws-hybrid

# 3. Xác minh
ls -la /opt/aws-hybrid
```

### Bước 3: Thiết lập File Môi trường

```bash
# 1. Môi trường staging
cat > /opt/aws-hybrid/staging/.env.staging << 'EOF'
# Môi trường Staging
ENVIRONMENT=staging
GHCR_OWNER=your-github-username
IMAGE_TAG=staging-latest

# Dịch vụ
AI_AGENT_PORT=8000
API_PORT=8000

# Google Generative AI
GEMINI_API_KEY=your-gemini-key

# Telegram (tùy chọn)
TELEGRAM_TOKEN=your-token
TELEGRAM_CHAT_ID=your-chat-id

# Cơ sở dữ liệu
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aws_hybrid_staging
EOF

# 2. Môi trường production
cat > /opt/aws-hybrid/production/.env.production << 'EOF'
# Môi trường Production
ENVIRONMENT=production
GHCR_OWNER=your-github-username
IMAGE_TAG=latest

# Dịch vụ
AI_AGENT_PORT=8000
API_PORT=8000

# Google Generative AI
GEMINI_API_KEY=your-gemini-key

# Cơ sở dữ liệu
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aws_hybrid_production
EOF

# 3. Hạn chế quyền
chmod 600 /opt/aws-hybrid/staging/.env.staging
chmod 600 /opt/aws-hybrid/production/.env.production
```

---

## 🐳 Cài đặt Docker & Docker Compose

### Bước 1: Cài đặt Docker Engine

```bash
# 1. Xóa docker cũ
sudo apt remove docker docker-engine docker.io containerd runc

# 2. Cài đặt phụ thuộc
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    apt-transport-https

# 3. Thêm Docker GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker-archive-keyring.gpg

# 4. Thiết lập kho lưu trữ
echo \
  "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Cài đặt Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 6. Xác minh
sudo docker --version
# Docker version 26.0.0+
```

### Bước 2: Thiết lập Docker Daemon

```bash
# 1. Thêm người dùng hiện tại vào nhóm docker (không cần sudo)
sudo usermod -aG docker $USER
newgrp docker

# 2. Cấu hình Docker daemon
sudo cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false
}
EOF

# 3. Khởi động lại Docker
sudo systemctl restart docker
sudo systemctl enable docker  # auto-start on boot

# 4. Xác minh
docker ps
docker info
```

### Bước 3: Cài đặt Docker Compose

```bash
# Phiên bản mới nhất
sudo curl -L \
  "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose

# Làm cho nó có thể thực thi
sudo chmod +x /usr/local/bin/docker-compose

# Xác minh
docker compose --version
# Docker Compose version 2.20.0+
```

### Bước 4: Kiểm tra Docker

```bash
# 1. Chạy test container
docker run --rm -it ubuntu:22.04 echo "Hello from Docker!"

# 2. Kiểm tra logs
docker logs <container-id>

# 3. Liệt kê containers
docker ps -a
```

---

## 📦 Triển khai Môi trường Staging (monitor-ai-01: 52.74.118.8)

### Triển khai tự động thông qua GitHub Actions (Khuyên cáo)

```
Workflow: cd-staging.yml
Kích hoạt: Push vào nhánh develop
Hành động:
  1. Build Docker images (AI Agent, Payment API)
  2. Đẩy vào GHCR
  3. SSH vào monitor instance (52.74.118.8)
  4. Chạy: automation/deploy.sh staging {image-tag}
  5. Docker compose pull & up
  6. Kiểm tra sức khỏe (18x retries)
  7. Lưu trạng thái triển khai
```

**GitHub Secrets Required:**
```
SSH_HOST = 52.74.118.8
SSH_PORT = 22
SSH_PRIVATE_KEY = <private key content>
GHCR_USERNAME = <github username>
GHCR_TOKEN = <github token>
```

### Triển khai thủ công (Lần đầu tiên)

```bash
# Từ máy local
MONITOR_IP="52.74.118.8"
MONITOR_USER="ec2-user"
KEY="aws-hybrid-key.pem"

# 1. Tạo thư mục trên monitor
ssh -i $KEY $MONITOR_USER@$MONITOR_IP \
  "mkdir -p /home/ec2-user/aws-hybrid/{release,automation}"

# 2. Sao chép file docker-compose
scp -i $KEY release/docker-compose.staging.yml \
  $MONITOR_USER@$MONITOR_IP:/home/ec2-user/aws-hybrid/release/

scp -i $KEY release/.env.example \
  $MONITOR_USER@$MONITOR_IP:/home/ec2-user/aws-hybrid/release/.env.staging

# 3. Sao chép deploy script
scp -i $KEY automation/deploy.sh \
  $MONITOR_USER@$MONITOR_IP:/home/ec2-user/aws-hybrid/automation/

chmod +x /home/ec2-user/aws-hybrid/automation/deploy.sh

# 4. SSH vào monitor
ssh -i $KEY $MONITOR_USER@$MONITOR_IP
```

**Trên Monitor Instance:**

```bash
cd /home/ec2-user/aws-hybrid

# 1. Thiết lập môi trường (cập nhật giá trị của bạn)
cat > release/.env.staging << 'EOF'
GHCR_OWNER=your-github-username
IMAGE_TAG=staging-latest
GEMINI_API_KEY=your-gemini-key
TELEGRAM_TOKEN=your-telegram-token
TELEGRAM_CHAT_ID=your-chat-id
EOF

# 2. Đăng nhập vào GHCR
echo $GHCR_TOKEN | docker login ghcr.io -u $GHCR_USERNAME --password-stdin

# 3. Chạy script triển khai
./automation/deploy.sh staging staging-latest

# 4. Kiểm tra triển khai
docker compose -f release/docker-compose.staging.yml ps

# 5. Kiểm tra log
docker compose -f release/docker-compose.staging.yml logs ai-agent --tail=50
```

### Cổng Dịch vụ trên Staging (monitor-ai-01)

```
AI Agent:       http://52.74.118.8:18000/health
Prometheus:     http://52.74.118.8:9090
Grafana:        http://52.74.118.8:3000
```

### Kiểm tra Dịch vụ

```bash
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

### Triển khai tự động thông qua GitHub Actions (Khuyên cáo)

```
Workflow: cd-production.yml
Kích hoạt: Tạo tag git (v*.*.*)
Hành động:
  1. Build Docker images với production tag
  2. Đẩy lên GHCR
  3. Yêu cầu phê duyệt môi trường
  4. SSH tới monitor instance
  5. Chạy: automation/deploy.sh production v1.0.0
  6. Docker compose pull & up (production config)
  7. Kiểm tra sức khỏe (18x retry)
  8. Lưu trạng thái triển khai
```

**Luồng công việc triển khai:**

```bash
# Trên máy local - tạo và đẩy tag
git tag v1.0.0
git push origin v1.0.0

# → GitHub Actions tự động:
#   1. Build images với tag v1.0.0
#   2. Chờ phê duyệt trong GitHub
#   3. Triển khai tới production trên monitor instance
```

**Phê duyệt GitHub Actions:**
```
GitHub → Actions → cd-production.yml run → Phê duyệt triển khai → Phê duyệt
```

### Triển khai thủ công Production (Lần đầu tiên)

```bash
# SSH vào monitor instance
ssh -i aws-hybrid-key.pem ec2-user@52.74.118.8

cd /home/ec2-user/aws-hybrid

# 1. Thiết lập môi trường production
cat > release/.env.production << 'EOF'
GHCR_OWNER=your-github-username
IMAGE_TAG=v1.0.0
GEMINI_API_KEY=your-gemini-key
TELEGRAM_TOKEN=your-telegram-token
TELEGRAM_CHAT_ID=your-chat-id
EOF

# 2. Đăng nhập vào GHCR
echo $GHCR_TOKEN | docker login ghcr.io -u $GHCR_USERNAME --password-stdin

# 3. Triển khai production
./automation/deploy.sh production v1.0.0

# 4. Kiểm tra
docker compose -f release/docker-compose.production.yml ps
docker compose -f release/docker-compose.production.yml logs ai-agent --tail=50
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
ssh -i aws-hybrid-key.pem ec2-user@52.74.118.8

cd /home/ec2-user/aws-hybrid

# 1. Kéo phiên bản trước đó
docker pull ghcr.io/{owner}/aws-hybrid-ai-agent:v0.9.9

# 2. Cập nhật docker-compose
sed -i 's/v1.0.0/v0.9.9/g' release/.env.production

# 3. Triển khai lại
./automation/deploy.sh production v0.9.9

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
# 1. Logs thực tế (follow - phổ biến nhất)
docker compose logs -f ai-agent
docker compose logs -f payment-api
docker compose logs -f -n 50  # 50 dòng cuối cùng, theo sau cái mới

# 2. Khoảng thời gian cụ thể
docker compose logs --since 2026-04-24T10:00:00 ai-agent
docker compose logs --until 2026-04-24T12:00:00 payment-api

# 3. Tất cả logs container vào file
docker compose logs > /opt/aws-hybrid/logs/all-services.log

# 4. Truy cập logs container trực tiếp
docker logs <container-id>
docker logs --tail=100 <container-id>
docker logs --follow <container-id>  # Thực tế

# 5. Logs từ cả hai dịch vụ
docker compose logs ai-agent payment-api --tail=50

# 6. Lưu logs và tìm kiếm
docker compose logs > deploy.log
grep "ERROR\|WARNING" deploy.log
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
cd /opt/aws-hybrid/staging
docker compose logs -f ai-agent --timestamps
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
# File: /etc/logrotate.d/aws-hybrid

/opt/aws-hybrid/logs/*.log {
  daily                    # Xoay hàng ngày
  rotate 7                 # Giữ 7 ngày
  compress                 # Nén logs cũ (gzip)
  delaycompress            # Không nén log mới nhất
  notifempty               # Không xoay nếu trống
  missingok                # Không lỗi nếu thiếu
  create 0640 ubuntu ubuntu # Tệp mới: quyền 640
  sharedscripts
  postrotate
    # Gửi tín hiệu cho dịch vụ để mở lại các file log
    docker compose -f /opt/aws-hybrid/staging/docker-compose.staging.yml kill -s HUP
    docker compose -f /opt/aws-hybrid/production/docker-compose.production.yml kill -s HUP
  endscript
}

# Kiểm tra logrotate
sudo logrotate -f /etc/logrotate.d/aws-hybrid

# Xác minh
ls -la /opt/aws-hybrid/logs/
# Nên thấy: all-services.log, all-services.log.1.gz, all-services.log.2.gz, v.v.
```

---

### Thiết lập Giám sát (Prometheus + Grafana)

```bash
# 1. Tạo cấu hình prometheus
cat > /opt/aws-hybrid/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'docker'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'ai-agent'
    static_configs:
      - targets: ['localhost:18000']
  
  - job_name: 'payment-api'
    static_configs:
      - targets: ['localhost:18080']
EOF

# 2. Khởi động Prometheus
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /opt/aws-hybrid/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# 3. Khởi động Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana

# 4. Truy cập các bảng điều khiển
# Prometheus: http://localhost:9090
#   - Targets → Kiểm tra sức khỏe
#   - Graph → Truy vấn số liệu
#
# Grafana: http://localhost:3000 (admin/admin)
#   - Thêm nguồn dữ liệu Prometheus
#   - Tạo các bảng điều khiển
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
  /opt/aws-hybrid/staging/.env.staging \
  /opt/aws-hybrid/production/.env.production
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


