# Hệ Thống CI/CD AIops 

---

## Đặt vấn đề

### Tình huống trước khi triển khai

Trong quá trình phát triển dự án **aws-hybrid** (hệ thống AI Agent + Payment API), chúng ta gặp phải những **thách thức lớn**:

#### **1. Vấn đề Chất lượng Code**
- Lỗi syntax và import không được phát hiện đến khi deploy
- Unit test thường xuyên bị bỏ qua hoặc chạy không đúng
- Pull Request được merge mà có bug (test import từ module không tồn tại)
- Package dependency không đồng nhất giữa local vs production:
  - Google Generative API: `google-genai` vs `google-generativeai` gây confusion
  - httpx version 0.28+ không tương thích với FastAPI TestClient

#### **2. Vấn đề Deployment Manual**
- Deploy thủ công → dễ sai sót, mất thời gian
- Không có audit trail về ai deploy cái gì lúc nào
- Staging & Production không cách ly → dễ ảnh hưởng lẫn nhau
- Khi deployment fail → không tự động rollback, phải thủ công sửa
- Deploy staging có thể làm hỏng production nếu cùng port

#### **3. Vấn đề Thông báo & Monitoring**
- Khi CI fail → không ai biết, chỉ developer tình cờ check
- Deployment fail mà không có alert → downtime không được phát hiện
- Production deployment fail mà không biết chi tiết lỗi là gì
- Admin phải kiểm tra GitHub Actions thủ công lúc nghi ngờ có vấn đề

#### **4. Vấn đề Chi phí Infrastructure**
- Cần 2 EC2 instance riêng cho staging & production → chi phí cao
- Không cách ly namespace → dễ xảy ra resource conflict
- Không thể chạy cả 2 cùng EC2 vì port conflict (8000, 8080)

#### **5. Vấn đề Tính Ổn định & Reliability**
- Merge PR không kiểm tra → broken code vào main branch
- Deployment không validate health → service down nhưng không biết
- Không rollback mechanism → phải restart thủ công hoặc redeploy
- Không staging environment test kỹ → bug chỉ phát hiện ở production

---

## Tổng quan hệ thống

### Mục đích
Xây dựng **CI/CD tự động hoàn toàn** cho dự án aws-hybrid, đảm bảo:
- Kiểm soát chất lượng code (lint, test, build)
- Triển khai tự động staging/production
- Thông báo lỗi ngay lập tức cho admin
- Rollback tự động nếu deployment fail
- Không conflict khi chạy staging + production cùng EC2

### Công nghệ sử dụng

| Công cụ | Mục đích | Phiên bản |
|---------|---------|----------|
| **GitHub Actions** | CI/CD Orchestration | Latest |
| **Docker** | Container Build | 26.0+ |
| **Docker Compose** | Multi-container | 2.20+ |
| **GHCR** | Image Registry | GitHub native |
| **Telegram API** | Admin Notifications | Bot API |
| **AWS EC2** | Compute | Ubuntu 22.04 LTS |
| **Python** | Backend Runtime | 3.11 |
| **FastAPI** | API Framework | 0.104.1 |

### Thành phần chính

```
┌─────────────────────────────────────────────────────┐
│         GitHub Repository (aws-hybrid)              │
├─────────────────────────────────────────────────────┤
│ .github/workflows/                                  │
│ ├── ci.yml                (Lint → Test → Build)    │
│ ├── cd-staging.yml        (Deploy Staging)         │
│ └── cd-production.yml     (Deploy Production)       │
├─────────────────────────────────────────────────────┤
│ automation/                                         │
│ ├── deploy.sh             (Deployment Script)       │
│ └── notify.sh             (Telegram Notifications)  │
├─────────────────────────────────────────────────────┤
│ release/                                            │
│ ├── docker-compose.staging.yml                      │
│ ├── docker-compose.production.yml                   │
│ ├── .env.staging                                    │
│ └── .env.production                                 │
└─────────────────────────────────────────────────────┘
         ↓
    GitHub Actions Runners
         ↓
    GHCR (Container Registry)
         ↓
    EC2 Instance (SSH Deploy)
         ↓
    Staging (Port 18000/18080)
    Production (Port 8000/8080)
```

---

## 🏗️ Kiến trúc CI/CD

### Pipeline Flow Tổng thể

```
Developer Push Code
    ↓
┌─────────────────────────┐
│   CI Pipeline           │
│ (Lint/Test/Build)       │  ← Kiểm tra chất lượng code
│ .github/workflows/ci.yml│
└─────────────────────────┘
    ↓ (Success)
┌────────────────────────────┐         ┌──────────────────────┐
│  Push to develop branch    │         │  Push tag v*         │
│  (cd-staging.yml trigger)  │         │  (cd-production.yml) │
└────────────────────────────┘         └──────────────────────┘
    ↓                                       ↓
┌──────────────────────────┐        ┌─────────────────────────┐
│  CD Staging Pipeline     │        │ CD Production Pipeline  │
│ - Build images           │        │ - Build images          │
│ - Push to GHCR           │        │ - Push to GHCR          │
│ - SSH to EC2             │        │ - SSH to EC2            │
│ - Deploy (Port 18000)    │        │ - Deploy (Port 8000)    │
│ - Health check           │        │ - Health check          │
└──────────────────────────┘        └─────────────────────────┘
    ↓ (Fail)                             ↓ (Fail)
    └─────────────┬───────────────────────┘
                  ↓
        ┌─────────────────────┐
        │  Send Telegram      │
        │  Alert to Admin     │
        │  notify.sh          │
        └─────────────────────┘
```

---

## 📋 Chi tiết từng Pipeline

### 1️⃣ CI Pipeline (.github/workflows/ci.yml)

**Trigger:** PR hoặc push đến feature/*, develop, main

**8 Bước thực hiện:**

#### Bước 1: Checkout Code
```bash
- uses: actions/checkout@v4
```
- Git clone repository vào GitHub Actions runner
- Chuẩn bị code để validate

#### Bước 2: Setup Python 3.11
```bash
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
```
- Cài đặt Python runtime trên ubuntu-latest

#### Bước 3: Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r agent_src/requirements.txt
pip install -r demo-web/backend/requirements.txt
pip install pytest ruff "httpx<0.28"
```
- Cài FastAPI, google-genai, pydantic, etc.
- **Quan trọng:** `httpx<0.28` (fix compatibility với FastAPI TestClient)

#### Bước 4: Lint Check (ruff)
```bash
ruff check agent_src demo-web/backend/app \
  --select E9,F63,F7,F82
```
- Kiểm tra syntax critical errors
- E9: SyntaxError
- F63: Invalid print syntax
- F7: Undefined names in __all__
- F82: Undefined names in function

**Nếu fail:** ❌ Trigger notify.sh → Telegram alert

#### Bước 5: Test AI Agent
```bash
PYTHONPATH=agent_src pytest -q agent_src/tests
```
- Chạy test_health.py
- Kiểm tra `/health` endpoint
- Response phải có: status, queue, redis fields

**Test Code Sample:**
```python
def test_health_endpoint():
    from core.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "queue" in data
    assert "redis" in data
```

#### Bước 6: Test Backend API
```bash
PYTHONPATH=demo-web/backend pytest -q demo-web/backend/tests
```
- Chạy API endpoint tests
- Kiểm tra payment, health, status endpoints

#### Bước 7: Build Docker Images
```bash
docker build -t local/ai-agent:ci-${{ github.sha }} agent_src
docker build -t local/payment-api:ci-${{ github.sha }} demo-web/backend
```
- Build 2 services locally
- Tag bằng commit hash
- Kiểm tra Dockerfile syntax & build process

#### Bước 8: Validate Docker Compose Files
```bash
docker compose -f release/docker-compose.staging.yml config > /dev/null
docker compose -f release/docker-compose.production.yml config > /dev/null
```
- Kiểm tra syntax compose files
- Verify all service references
- Kiểm tra environment variables binding

**Success Outcome:**
```
✅ CI Pipeline SUCCESS
→ Cho phép merge PR
→ Trigger CD pipeline (nếu push vào develop/main)
```

**Failure Outcome:**
```
❌ CI Pipeline FAILED at [Step Name]
→ Block PR merge
→ Send Telegram alert: "CI Pipeline failed - [error details]"
→ Developer must fix và push lại
```

---

### 2️⃣ CD Staging Pipeline (.github/workflows/cd-staging.yml)

**Trigger:** Push đến develop branch hoặc workflow_dispatch (manual)

**Workflow Structure:**

```yaml
jobs:
  build-and-push:
    runs-on: ubuntu-latest
    outputs:
      owner_lc: ghcr.io owner in lowercase
      image_tag: staging-<commit-hash>
      
  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
```

#### Job 1: Build & Push Images

**Step 1 - Prepare Variables:**
```bash
owner_lc=${GITHUB_REPOSITORY_OWNER,,}  # hoang_viet
image_tag=staging-${GITHUB_SHA}         # staging-abc123def456
```

**Step 2 - Login GHCR:**
```bash
docker login ghcr.io \
  -u ${{ secrets.GHCR_USERNAME }} \
  -p ${{ secrets.GHCR_TOKEN }}
```
- Đăng nhập GitHub Container Registry
- Credentials từ GitHub Secrets

**Step 3 - Build & Push AI Agent:**
```bash
docker buildx build --push \
  -t ghcr.io/hoang_viet/aws-hybrid-ai-agent:staging-abc123def456 \
  -t ghcr.io/hoang_viet/aws-hybrid-ai-agent:staging-latest \
  ./agent_src
```

**Step 4 - Build & Push Payment API:**
```bash
docker buildx build --push \
  -t ghcr.io/hoang_viet/aws-hybrid-payment-api:staging-abc123def456 \
  -t ghcr.io/hoang_viet/aws-hybrid-payment-api:staging-latest \
  ./demo-web/backend
```

#### Job 2: Deploy to Staging EC2

**Step 1 - SSH Connection:**
```yaml
uses: appleboy/ssh-action@v1.0.3
with:
  host: ${{ secrets.SSH_HOST }}              # IP EC2
  username: ${{ secrets.SSH_USER }}          # ubuntu
  key: ${{ secrets.SSH_PRIVATE_KEY }}        # SSH key
  port: ${{ secrets.SSH_PORT }}              # 22
  script_stop: true
  script: |
    cd /opt/aws-hybrid
    chmod +x automation/deploy.sh
    export GHCR_OWNER="hoang_viet"
    export GHCR_TOKEN="${{ secrets.GHCR_TOKEN }}"
    ./automation/deploy.sh staging "staging-abc123def456"
```

**Deploy Script Execution:**
```
automation/deploy.sh staging staging-abc123def456
├─ Kiểm tra environment variables
├─ Load .env.staging
├─ WORK_DIR=/opt/aws-hybrid/staging
├─ COMPOSE_FILE=release/docker-compose.staging.yml
├─ AI_HEALTH_URL=http://127.0.0.1:18000/health
├─ API_HEALTH_URL=http://127.0.0.1:18080/api/health
│
├─ docker login GHCR
├─ docker compose pull (download images)
├─ docker compose up -d (start containers)
│
├─ Health check loop (18 retries × 10s):
│  ├─ curl http://127.0.0.1:18000/health → HTTP 200 ✓
│  ├─ curl http://127.0.0.1:18080/api/health → HTTP 200 ✓
│  └─ Save tag to .state/staging.tag
│
└─ If any fail:
   ├─ Restore previous image tag
   ├─ docker compose pull [PREVIOUS_TAG]
   ├─ Rollback deployed
   └─ Exit error → notify.sh trigger
```

**Success Output:**
```
✅ Staging deployment successful
→ Services live on port 18000 (AI Agent)
→ Services live on port 18080 (Payment API)
→ Health checks passing
```

**Failure Output:**
```
❌ Staging deployment failed
→ Automatic rollback to previous version
→ Telegram notification sent to admin
→ Production not affected (different port/namespace)
```

---

### 3️⃣ CD Production Pipeline (.github/workflows/cd-production.yml)

**Trigger:** Push tag v* hoặc workflow_dispatch với release_tag input

**Workflow Structure:** Tương tự staging nhưng:
- Image tags: `v1.2.3`, `<commit-sha>`, `latest`
- Deploy đến `/opt/aws-hybrid/production`
- Health check URL: `http://127.0.0.1:8000/health`
- Port: 8000 (AI Agent), 8080 (API)
- Alert level: **CRITICAL** (ưu tiên cao hơn staging)

**Tag Push Example:**
```bash
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
→ GitHub detects tag → cd-production.yml triggers
```

**Manual Trigger Example:**
```
GitHub UI:
  Actions → CD Production → Run workflow
  release_tag input: v1.2.3
  → Deploy specified version
```

---

## 📱 Hệ thống thông báo

### Architecture

```
GitHub Actions Workflow
        ↓
    if: failure()
        ↓
automation/notify.sh
        ↓
Telegram Bot API
        ↓
Admin Telegram Chat
```

### Notification Script (automation/notify.sh)

```bash
#!/bin/bash

# Variables
TELEGRAM_TOKEN="${TELEGRAM_TOKEN}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID}"
WORKFLOW_NAME="${1:-CI/CD Pipeline}"
STATUS="${2:-failed}"
DETAILS="${3:-Unknown error}"
GITHUB_REPO="${GITHUB_REPOSITORY:-aws-hybrid}"
GITHUB_SHA="${GITHUB_SHA:-unknown}"
GITHUB_REF="${GITHUB_REF:-unknown}"
GITHUB_ACTOR="${GITHUB_ACTOR:-unknown}"
RUN_ID="${GITHUB_RUN_ID:-unknown}"

# Build HTML formatted message
MESSAGE="🚨 <b>CI/CD Pipeline Failure</b>

<b>Workflow:</b> $WORKFLOW_NAME
<b>Repository:</b> $GITHUB_REPO
<b>Branch:</b> $GITHUB_REF
<b>Commit:</b> ${GITHUB_SHA:0:7}
<b>Triggered by:</b> $GITHUB_ACTOR

<b>Error:</b> $DETAILS

<b>Action:</b> Check logs at GitHub Actions Run #$RUN_ID"

# Send via Telegram API
curl -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=${MESSAGE}" \
  -d "parse_mode=HTML"
```

### Cách sử dụng trong Workflow

```yaml
- name: Send Telegram notification on failure
  if: failure()
  env:
    TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  run: |
    chmod +x automation/notify.sh
    ./automation/notify.sh "CI Pipeline" "failed" \
      "Lint/Test/Build validation failed for ${{ github.ref_name }}"
```

### Cấu hình GitHub Secrets

**Cách 1: Qua GitHub UI**
```
Settings → Secrets and variables → Actions
  TELEGRAM_TOKEN = 8482081904:AAHPcNZRY8FGIw_VkwEgJXnVjYeYsK-M8mk
  TELEGRAM_CHAT_ID = -1003502728155
```

**Cách 2: Qua GitHub CLI**
```bash
gh secret set TELEGRAM_TOKEN -b "8482081904:AAHPcNZRY8FGIw_..."
gh secret set TELEGRAM_CHAT_ID -b "-1003502728155"
```

### Alert Levels

| Level | Workflow | Alert Message |
|-------|----------|---------------|
| 🟡 Warning | CI Pipeline | "CI Pipeline failed - [error]" |
| 🔴 Error | CD Staging | "Staging deployment failed - Tag: staging-abc123" |
| 🚨 Critical | CD Production | "**CRITICAL**: Production deployment failed! Tag: v1.2.3" |

---

## 🔀 Namespace Separation

### Problem
Staging và production cùng chạy trên 1 EC2 → cần tách biệt để không conflict

### Solution: Port Mapping + Working Directory Isolation

```
┌─────────────────────────────────────────────────┐
│         Single EC2 Instance                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────────────┐                   │
│  │     STAGING             │                   │
│  ├─────────────────────────┤                   │
│  │ Working Dir:            │                   │
│  │ /opt/aws-hybrid/staging │                   │
│  │                         │                   │
│  │ Ports:                  │                   │
│  │ - 18000:8000 (AI)       │                   │
│  │ - 18080:8000 (API)      │                   │
│  │                         │                   │
│  │ .env.staging            │                   │
│  │ docker-compose.         │                   │
│  │   staging.yml           │                   │
│  └─────────────────────────┘                   │
│                                                 │
│  ┌─────────────────────────┐                   │
│  │     PRODUCTION          │                   │
│  ├─────────────────────────┤                   │
│  │ Working Dir:            │                   │
│  │ /opt/aws-hybrid/        │                   │
│  │   production            │                   │
│  │                         │                   │
│  │ Ports:                  │                   │
│  │ - 8000:8000 (AI)        │                   │
│  │ - 8080:8000 (API)       │                   │
│  │                         │                   │
│  │ .env.production         │                   │
│  │ docker-compose.         │                   │
│  │   production.yml        │                   │
│  └─────────────────────────┘                   │
│                                                 │
│  Isolation Strategy:                           │
│  ✓ Không port conflict                        │
│  ✓ Không file path conflict                   │
│  ✓ Không volume mount conflict                │
│  ✓ Có thể deploy cùng lúc                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Implementation

#### Docker Compose Files

**staging.yml:**
```yaml
services:
  ai-agent:
    ports:
      - "0.0.0.0:18000:8000"  # Port 18000 public
  
  payment-api:
    ports:
      - "0.0.0.0:18080:8000"  # Port 18080 public
```

**production.yml:**
```yaml
services:
  ai-agent:
    ports:
      - "0.0.0.0:8000:8000"   # Port 8000 public
  
  payment-api:
    ports:
      - "0.0.0.0:8080:8000"   # Port 8080 public
```

#### Deploy Script Logic

```bash
case "$ENVIRONMENT" in
  staging)
    WORK_DIR="/opt/aws-hybrid/staging"
    COMPOSE_FILE="release/docker-compose.staging.yml"
    ENV_FILE="release/.env.staging"
    AI_HEALTH_URL="http://127.0.0.1:18000/health"
    API_HEALTH_URL="http://127.0.0.1:18080/api/health"
    ;;
  production)
    WORK_DIR="/opt/aws-hybrid/production"
    COMPOSE_FILE="release/docker-compose.production.yml"
    ENV_FILE="release/.env.production"
    AI_HEALTH_URL="http://127.0.0.1:8000/health"
    API_HEALTH_URL="http://127.0.0.1:8080/api/health"
    ;;
esac

# Tất cả operations trong WORK_DIR
cd "$WORK_DIR"
docker compose -f "$COMPOSE_FILE" up -d
```

---

## 🚀 Quy trình Deployment

### Deployment Flow Chi tiết

```
INPUT: ENVIRONMENT (staging/production), IMAGE_TAG (commit hash / version)

PHASE 1: VALIDATION
├─ Check environment parameter valid
├─ Load corresponding compose file
├─ Load corresponding .env file
└─ Verify both files exist

PHASE 2: SETUP WORKING DIRECTORY
├─ mkdir -p /opt/aws-hybrid/{staging|production}
├─ mkdir -p .state/ (for state files)
├─ Copy compose files to work dir (if needed)
└─ Change to work directory: cd $WORK_DIR

PHASE 3: SAVE PREVIOUS STATE
├─ Read .state/{staging|production}.tag file
├─ Store previous image tag for rollback
└─ Initialize new state for current deploy

PHASE 4: AUTHENTICATION
├─ docker login ghcr.io
├─ Username: $GHCR_USERNAME
├─ Password: $GHCR_TOKEN
└─ Verify login successful

PHASE 5: PULL LATEST IMAGES
├─ docker compose pull
├─ Download images from GHCR:
│  ├─ ghcr.io/hoang_viet/aws-hybrid-ai-agent:$IMAGE_TAG
│  └─ ghcr.io/hoang_viet/aws-hybrid-payment-api:$IMAGE_TAG
└─ Verify image pull successful

PHASE 6: START CONTAINERS
├─ docker compose down --remove-orphans
├─ Stop old containers
├─ docker compose up -d
├─ Start new containers
└─ Verify containers are running

PHASE 7: HEALTH CHECK LOOP
├─ Retry: 18 times (180 seconds total timeout)
├─ Each retry: sleep 10 seconds
├─ Check AI Agent health:
│  └─ curl http://127.0.0.1:{PORT}/health
│     Expect: HTTP 200, JSON response with "status": "healthy"
├─ Check API health:
│  └─ curl http://127.0.0.1:{PORT}/api/health
│     Expect: HTTP 200
└─ If all checks pass → Go to PHASE 8
   If all retries exhausted → Go to PHASE 9

PHASE 8: SUCCESS
├─ Save new image tag to .state file:
│  └─ echo "$IMAGE_TAG" > .state/{environment}.tag
├─ Log success message
├─ Exit code 0
└─ Deployment complete ✅

PHASE 9: FAILURE & ROLLBACK
├─ Read PREVIOUS_TAG from state file
├─ docker compose pull PREVIOUS_TAG
├─ docker compose down --remove-orphans
├─ docker compose up -d (restore old version)
├─ Run health check loop for old version
├─ If old version passes:
│  ├─ Keep old version running
│  └─ Exit error code
└─ Log detailed error information
```

### State File Management

```bash
# .state/ directory structure
.state/
├─ staging.tag      # Current deployed tag for staging
└─ production.tag   # Current deployed tag for production

# Content example
$ cat .state/staging.tag
staging-abc123def456

# Rollback scenario
Current deployment: staging-new123
Old version in state: staging-abc123def456
Health check fails → restore to staging-abc123def456
```

---

## ✅ Health Check & Rollback

### Health Check Mechanism

**Purpose:** Verify deployed services are healthy before marking deployment successful

**Configuration:**

```yaml
# docker-compose.staging.yml
services:
  ai-agent:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
  
  payment-api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
```

**Health Check Response:**

```json
{
  "status": "healthy",
  "queue": {
    "total": 5,
    "pending": 2,
    "processing": 3
  },
  "redis": {
    "connected": true,
    "latency_ms": 2.3
  }
}
```

### Rollback Mechanism

**Automatic Rollback Flow:**

```
New Deployment Initiated
    ↓
Save Previous Tag: staging-old123
    ↓
Deploy New Tag: staging-new456
    ↓
Start Containers
    ↓
Health Check Loop:
  Retry 1-3: OK ✓
  Retry 4-6: Timeout (service not responding)
  Retry 7-18: Still failing
    ↓
✗ Health check failed after 18 retries
    ↓
AUTOMATIC ROLLBACK:
├─ docker compose pull staging-old123
├─ docker compose down --remove-orphans
├─ docker compose up -d (with old tag)
├─ Health check old version
└─ If passes → Deployment marked FAILED but service restored
              → Exit error code → notify.sh triggered
```

**Manual Rollback (if needed):**

```bash
# SSH to EC2
cd /opt/aws-hybrid/staging

# Check state file
cat release/.state/staging.tag

# Manual rollback
export IMAGE_TAG="previous-stable-tag"
export GHCR_OWNER="hoang_viet"
docker compose -f release/docker-compose.staging.yml pull
docker compose -f release/docker-compose.staging.yml up -d

# Verify health
curl http://127.0.0.1:18000/health
```

---

## 🔧 Troubleshooting

### CI Pipeline Failures

#### 1. Lint Check Failed
```
Error: ruff check failed with E9, F7, F82
```

**Giải pháp:**
```bash
# Run locally first
cd /path/to/project
ruff check agent_src demo-web/backend/app \
  --select E9,F63,F7,F82

# Fix errors
# Commit and push again
```

#### 2. Test Failed
```
Error: test_health_endpoint failed: assert 'queue' in data
```

**Giải pháp:**
```bash
# Run test locally
cd agent_src
PYTHONPATH=. pytest -xvs tests/test_health.py

# Check endpoint response
curl http://localhost:8000/health

# Update test if needed
# agent_src/tests/test_health.py
```

#### 3. Docker Build Failed
```
Error: docker build failed: base image not found
```

**Giải pháp:**
```bash
# Check Dockerfile
cat agent_src/Dockerfile

# Verify base image
docker pull python:3.11-slim

# Rebuild locally
docker build -t test:latest agent_src
```

### CD Pipeline Failures

#### 1. SSH Connection Failed
```
Error: Permission denied (publickey,password).
```

**Giải pháp:**
1. Verify SSH_HOST, SSH_USER, SSH_PRIVATE_KEY secrets
2. Test SSH locally:
   ```bash
   ssh -i ~/.ssh/id_rsa ubuntu@<SSH_HOST>
   ```
3. Regenerate SSH key if needed

#### 2. Health Check Timeout
```
Error: Health check failed after 18 retries
```

**Giải pháp:**
1. SSH to EC2 and check container logs:
   ```bash
   cd /opt/aws-hybrid/staging
   docker compose logs ai-agent
   docker compose logs payment-api
   ```
2. Check network connectivity:
   ```bash
   curl http://127.0.0.1:18000/health -v
   curl http://127.0.0.1:18080/api/health -v
   ```
3. Check port availability:
   ```bash
   netstat -tuln | grep 1800
   ```

#### 3. Image Pull Failed
```
Error: failed to pull image: ghcr.io/.../ai-agent:staging-abc123
```

**Giải pháp:**
1. Verify GHCR_TOKEN in secrets
2. Test Docker login:
   ```bash
   docker login ghcr.io -u <username> -p <token>
   docker pull ghcr.io/hoang_viet/aws-hybrid-ai-agent:staging-latest
   ```
3. Check image exists in GHCR registry

### Notification Failures

#### 1. Telegram Alert Not Received
```
Error: Failed to send Telegram notification
```

**Giải pháp:**
1. Verify TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
   ```bash
   curl -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
     -d "chat_id=${CHAT_ID}" \
     -d "text=Test" \
     -d "parse_mode=HTML"
   ```
2. Check token validity:
   ```bash
   curl "https://api.telegram.org/bot${TOKEN}/getMe"
   ```
3. Verify chat ID (should be negative for group)

#### 2. Bad Request Error
```
Error: Bad Request: can't parse entities
```

**Giải pháp:**
- Use HTML format instead of Markdown (done in current notify.sh)
- Escape special characters if needed
- Use `parse_mode=HTML` in API call

---

## 📊 Monitoring & Maintenance

### Log Locations

**GitHub Actions Logs:**
- UI: Repository → Actions → Workflow runs → Click run → View logs
- API: 
  ```bash
  gh run view <run_id> --log
  ```

**EC2 Deployment Logs:**
```bash
# SSH to EC2
cd /opt/aws-hybrid/staging

# Docker compose logs
docker compose logs ai-agent
docker compose logs payment-api

# Deploy script logs (if saved)
cat deploy.log

# System logs
journalctl -u docker -n 50
```

### Regular Maintenance Tasks

#### Weekly
- Check health check status
- Review failed deployments
- Update Docker images (base images)

#### Monthly
- Clean up old Docker images
  ```bash
  docker image prune -a
  ```
- Review and update dependencies
- Test rollback procedure

#### Quarterly
- Security audit of secrets management
- Performance optimization review
- Disaster recovery drill

---

## 📚 Quick Reference

### Push to different branches

```bash
# Feature branch (CI runs)
git checkout -b feature/my-feature
git push origin feature/my-feature

# Develop branch (CI + CD Staging)
git checkout develop
git push origin develop

# Main/master (CI runs)
git checkout main
git push origin main

# Production tag (CI + CD Production)
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

### Manual workflow dispatch

```bash
# Trigger CD Staging
gh workflow run cd-staging.yml

# Trigger CD Production
gh workflow run cd-production.yml -f release_tag=v1.2.3
```

### Environment Variables

**GitHub Secrets Required:**
```
GHCR_USERNAME        - GitHub username
GHCR_TOKEN          - GitHub PAT with packages:write
SSH_HOST            - EC2 IP address
SSH_USER            - EC2 username (ubuntu)
SSH_PRIVATE_KEY     - SSH private key for EC2
SSH_PORT            - SSH port (default 22)
TELEGRAM_TOKEN      - Telegram bot token
TELEGRAM_CHAT_ID    - Telegram chat ID (negative for groups)
```

**Environment Files:**
```
release/.env.staging        - Staging environment variables
release/.env.production     - Production environment variables
agent_src/.env              - Local development (not committed)
```

---

## Tài liệu tham khảo

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [FastAPI Health Checks](https://fastapi.tiangolo.com/advanced/health-checks/)

---

