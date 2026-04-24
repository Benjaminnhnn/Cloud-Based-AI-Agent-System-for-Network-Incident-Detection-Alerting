# 📚 Hướng dẫn Tạo Hạ tầng AWS & Deploy CI/CD System

**Phiên bản:** 1.0  
**Ngày viết:** 24/04/2026  
**Tác giả:** Hoàng Việt  
**Mục đích:** Hướng dẫn chi tiết setup AWS infrastructure & deploy CI/CD system  

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

### Topology

```
┌─────────────────────────────────────────────────────────┐
│                     AWS Account                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         VPC: aws-hybrid-vpc                     │   │
│  │         CIDR: 10.0.0.0/16                       │   │
│  │                                                 │   │
│  │  ┌──────────────┐  ┌──────────────────────────┐│   │
│  │  │   IGW        │  │  Subnets (Public)        ││   │
│  │  │              │  │  - 10.0.1.0/24 (2a)      ││   │
│  │  │              │  │  - 10.0.2.0/24 (2b)      ││   │
│  │  └──────────────┘  │  - 10.0.3.0/24 (2c)      ││   │
│  │                    └──────────────────────────┘│   │
│  │                                                 │   │
│  │  ┌─────────────────────────────────────────────┤   │
│  │  │    EC2 Instances                            │   │
│  │  │                                             │   │
│  │  │  ┌─────────────────┐  Staging             │   │
│  │  │  │ ai-agent-stage  │  Port: 18000         │   │
│  │  │  │ payment-api-s   │  Port: 18080         │   │
│  │  │  └─────────────────┘                       │   │
│  │  │                                             │   │
│  │  │  ┌─────────────────┐  Production          │   │
│  │  │  │ ai-agent-prod   │  Port: 8000          │   │
│  │  │  │ payment-api-p   │  Port: 8080          │   │
│  │  │  └─────────────────┘                       │   │
│  │  │                                             │   │
│  │  │  ┌─────────────────┐  Monitoring          │   │
│  │  │  │ prometheus      │  Port: 9090          │   │
│  │  │  │ grafana         │  Port: 3000          │   │
│  │  │  └─────────────────┘                       │   │
│  │  └─────────────────────────────────────────────┤   │
│  │                                                 │   │
│  │  ┌────────────────────────────────────────────┐│   │
│  │  │  Security Groups                           ││   │
│  │  │  - SG-Web: 80, 443, 18000, 18080          ││   │
│  │  │  - SG-Prod: 8000, 8080 (restricted IP)    ││   │
│  │  │  - SG-Monitor: 9090, 3000                 ││   │
│  │  │  - SG-Internal: 22 (SSH from bastion)     ││   │
│  │  └────────────────────────────────────────────┘│   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         External Services                       │   │
│  │  - GitHub (Code Repository)                    │   │
│  │  - GHCR (Container Registry)                   │   │
│  │  - Telegram (Notifications)                    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### EC2 Instance Spec

| Thành phần | Instance Type | CPU | RAM | Disk | Giá ($/tháng) |
|-----------|---------------|-----|-----|------|---------------|
| Staging | t3.small | 2 | 2GB | 30GB | ~$12 |
| Production | t3.medium | 2 | 4GB | 50GB | ~$24 |
| Monitoring | t3.micro | 1 | 1GB | 20GB | ~$8 |
| **Total** | - | - | - | - | **~$44** |

**Note:** Có thể dùng 1 EC2 cho cả staging + production (namespace separation bằng port)

---

## ✅ Chuẩn bị AWS Account

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

### Step 2: Create IAM User cho CI/CD

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
# 8. Save to GitHub Secrets:
#    AWS_ACCESS_KEY_ID
#    AWS_SECRET_ACCESS_KEY
```

### Step 3: Generate SSH Key Pair

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

---

## 🔧 Tạo Infrastructure với Terraform

### Step 1: Initialize Terraform

```bash
cd /path/to/aws-hybrid/terraform

# 1. Cấu hình AWS credentials
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="ap-southeast-1"  # Singapore

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

### Step 3: Apply Terraform Configuration

```bash
# 1. Review plan
terraform plan

# 2. Apply configuration
terraform apply tfplan
# → Creates:
#    ✅ VPC
#    ✅ Subnets
#    ✅ Internet Gateway
#    ✅ Route Tables
#    ✅ Security Groups
#    ✅ EC2 Instances
#    ✅ Elastic IPs

# 3. Verify
terraform show
# Shows all created resources

# 4. Get outputs
terraform output
# Example:
# staging_ip = "13.251.123.45"
# production_ip = "13.251.123.46"
```

### Step 4: Save Output Values

```bash
# Get values từ terraform
terraform output -json > outputs.json

# Hoặc manually copy:
echo "Staging IP: $(terraform output -raw staging_public_ip)"
echo "Production IP: $(terraform output -raw production_public_ip)"

# Update GitHub Secrets:
# SSH_HOST = staging_public_ip (change per environment)
```

---

## 🖥️ Setup EC2 Instances

### Step 1: Connect to EC2

```bash
# 1. Get public IP từ Terraform output
STAGING_IP=$(terraform output -raw staging_public_ip)
PROD_IP=$(terraform output -raw production_public_ip)

# 2. SSH vào staging
ssh -i aws-hybrid-key.pem ubuntu@$STAGING_IP

# 3. Update system
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

### Step 2: Create Directory Structure

```bash
# 1. Create app directories
sudo mkdir -p /opt/aws-hybrid/staging
sudo mkdir -p /opt/aws-hybrid/production
sudo mkdir -p /opt/aws-hybrid/logs

# 2. Set permissions
sudo chown -R ubuntu:ubuntu /opt/aws-hybrid
chmod -R 755 /opt/aws-hybrid

# 3. Verify
ls -la /opt/aws-hybrid
```

### Step 3: Setup Environment Files

```bash
# 1. Staging environment
cat > /opt/aws-hybrid/staging/.env.staging << 'EOF'
# Staging Environment
ENVIRONMENT=staging
GHCR_OWNER=your-github-username
IMAGE_TAG=staging-latest

# Services
AI_AGENT_PORT=8000
API_PORT=8000

# Google Generative AI
GEMINI_API_KEY=your-gemini-key

# Telegram (optional)
TELEGRAM_TOKEN=your-token
TELEGRAM_CHAT_ID=your-chat-id

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aws_hybrid_staging
EOF

# 2. Production environment
cat > /opt/aws-hybrid/production/.env.production << 'EOF'
# Production Environment
ENVIRONMENT=production
GHCR_OWNER=your-github-username
IMAGE_TAG=latest

# Services
AI_AGENT_PORT=8000
API_PORT=8000

# Google Generative AI
GEMINI_API_KEY=your-gemini-key

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aws_hybrid_production
EOF

# 3. Restrict permissions
chmod 600 /opt/aws-hybrid/staging/.env.staging
chmod 600 /opt/aws-hybrid/production/.env.production
```

---

## 🐳 Install Docker & Docker Compose

### Step 1: Install Docker Engine

```bash
# 1. Remove old docker
sudo apt remove docker docker-engine docker.io containerd runc

# 2. Install dependencies
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    apt-transport-https

# 3. Add Docker GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker-archive-keyring.gpg

# 4. Setup repository
echo \
  "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 6. Verify
sudo docker --version
# Docker version 26.0.0+
```

### Step 2: Setup Docker Daemon

```bash
# 1. Add current user to docker group (no need sudo)
sudo usermod -aG docker $USER
newgrp docker

# 2. Configure Docker daemon
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

# 3. Restart Docker
sudo systemctl restart docker
sudo systemctl enable docker  # auto-start on boot

# 4. Verify
docker ps
docker info
```

### Step 3: Install Docker Compose

```bash
# Latest version
sudo curl -L \
  "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker compose --version
# Docker Compose version 2.20.0+
```

### Step 4: Test Docker

```bash
# 1. Run test container
docker run --rm -it ubuntu:22.04 echo "Hello from Docker!"

# 2. Check logs
docker logs <container-id>

# 3. List containers
docker ps -a
```

---

## 📦 Deploy Staging Environment

### Step 1: Copy Files to EC2

```bash
# From your local machine
STAGING_IP="13.251.123.45"
KEY="aws-hybrid-key.pem"

# 1. Copy code
scp -i $KEY -r . ubuntu@$STAGING_IP:/opt/aws-hybrid/staging/

# 2. Copy docker-compose
scp -i $KEY release/docker-compose.staging.yml \
  ubuntu@$STAGING_IP:/opt/aws-hybrid/staging/

# 3. Copy .env
scp -i $KEY release/.env.staging \
  ubuntu@$STAGING_IP:/opt/aws-hybrid/staging/

# 4. Copy deploy script
scp -i $KEY automation/deploy.sh \
  ubuntu@$STAGING_IP:/opt/aws-hybrid/staging/
```

### Step 2: Manual Deploy (First Time)

```bash
# SSH vào staging
ssh -i aws-hybrid-key.pem ubuntu@$STAGING_IP

# 1. Navigate
cd /opt/aws-hybrid/staging

# 2. Login to GHCR
echo $GHCR_TOKEN | docker login ghcr.io -u $GHCR_USERNAME --password-stdin

# 3. Pull images
docker compose pull

# 4. Start containers
docker compose up -d

# 5. Check status
docker compose ps

# 6. Health check
sleep 5
curl http://localhost:18000/health
curl http://localhost:18080/health
```

### Step 3: Verify Services

```bash
# Check logs
docker compose logs ai-agent
docker compose logs payment-api

# Check network
docker network ls
docker network inspect staging_default

# Check volumes
docker volume ls

# Test endpoints
curl -v http://localhost:18000/health
curl -v http://localhost:18080/api/health

# Expected response:
# {
#   "status": "healthy",
#   "queue": "ok",
#   "redis": "ok"
# }
```

---

## 🏢 Deploy Production Environment

### Step 1: Production Setup

```bash
# SSH vào production EC2
ssh -i aws-hybrid-key.pem ubuntu@$PROD_IP

# 1. Create directories
sudo mkdir -p /opt/aws-hybrid/production
sudo chown -R ubuntu:ubuntu /opt/aws-hybrid

# 2. Copy files
cd /opt/aws-hybrid/production
# Copy same files as staging

# 3. Copy .env.production
scp -i $KEY release/.env.production \
  ubuntu@$PROD_IP:/opt/aws-hybrid/production/
```

### Step 2: Configure for Production

```bash
# Edit environment file
vim /opt/aws-hybrid/production/.env.production

# Change:
# ENVIRONMENT=production
# IMAGE_TAG=latest  (instead of staging-latest)
# DB_NAME=aws_hybrid_production

# ⚠️ Restrict permissions
chmod 600 .env.production
chmod 600 docker-compose.production.yml
```

### Step 3: Deploy Production

```bash
# 1. Login to GHCR
echo $GHCR_TOKEN | docker login ghcr.io -u $GHCR_USERNAME --password-stdin

# 2. Pull production images
docker compose -f docker-compose.production.yml pull

# 3. Start containers
docker compose -f docker-compose.production.yml up -d

# 4. Verify
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs ai-agent

# 5. Health check
curl http://localhost:8000/health
curl http://localhost:8080/health
```

---

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

## 📊 Monitoring & Logs

### View Logs - Basic Commands

```bash
# 1. Real-time logs (follow - most common)
docker compose logs -f ai-agent
docker compose logs -f payment-api
docker compose logs -f -n 50  # Last 50 lines, follow new

# 2. Specific time range
docker compose logs --since 2026-04-24T10:00:00 ai-agent
docker compose logs --until 2026-04-24T12:00:00 payment-api

# 3. All container logs to file
docker compose logs > /opt/aws-hybrid/logs/all-services.log

# 4. Access container logs directly
docker logs <container-id>
docker logs --tail=100 <container-id>
docker logs --follow <container-id>  # Real-time

# 5. Logs from both services
docker compose logs ai-agent payment-api --tail=50

# 6. Save logs and search
docker compose logs > deploy.log
grep "ERROR\|WARNING" deploy.log
```

---

### Common Error Patterns & Solutions

#### ❌ Error 1: Container Exit Code 1 (General Error)

**Log Example:**
```
ai-agent exited with code 1
```

**Diagnosis:**
```bash
# 1. Check exit logs
docker compose logs ai-agent --tail=50

# 2. Look for:
# - Python syntax error
# - Module import error
# - Missing environment variable
# - Port already in use
# - Database connection refused
```

**Common causes:**
```
- PYTHONUNBUFFERED not set → buffered output
- Missing GEMINI_API_KEY → import error
- Missing dependencies → ModuleNotFoundError
- Port 8000 already bound → AddressInUse
```

**Fix:**
```bash
docker compose down
docker compose pull
docker compose up -d
docker compose logs ai-agent
```

---

#### ❌ Error 2: Connection Refused

**Log Example:**
```
ERROR - Connection refused to localhost:5432
ConnectionRefusedError: [Errno 111] Connection refused
```

**Diagnosis:**
```bash
# 1. Check if service running
docker compose ps

# 2. Check port binding
netstat -tlnp | grep 5432

# 3. Check service logs
docker compose logs payment-api --tail=50

# 4. Test connectivity
docker exec ai-agent curl http://payment-api:8000/health
```

**Solutions:**
```bash
# If database not running
docker compose restart postgres

# If service not ready
docker compose logs payment-api | grep "Uvicorn running"

# Wait for service startup
sleep 10
curl http://localhost:18000/health
```

---

#### ❌ Error 3: Out of Memory (OOM)

**Log Example:**
```
killed (signal 9)
Killed
Exception in thread "Finalizer": java.lang.OutOfMemoryError
```

**Diagnosis:**
```bash
# Check memory usage
docker stats ai-agent payment-api

# Check container limits
docker inspect ai-agent | grep -A5 "Memory"

# Check system memory
free -h
df -h
```

**Solutions:**
```bash
# Increase memory limit in docker-compose
# ai-agent:
#   deploy:
#     resources:
#       limits:
#         memory: 2G

# Restart with new limits
docker compose down
docker compose up -d
docker stats
```

---

#### ❌ Error 4: Port Already in Use

**Log Example:**
```
Error starting userland proxy: listen tcp 0.0.0.0:18000: bind: address already in use
```

**Diagnosis:**
```bash
# Find what's using the port
lsof -i :18000
netstat -tlnp | grep 18000
ss -tlnp | grep 18000
```

**Solutions:**
```bash
# Kill the process
kill -9 <PID>

# Or stop the container
docker ps -a | grep 18000
docker kill <container-id>

# Or change port in docker-compose
# ports:
#   - "18001:8000"  # Use different port
```

---

#### ❌ Error 5: Health Check Timeout

**Log Example:**
```
Health check failed: timeout reached
Starting 2nd attempt
```

**Diagnosis:**
```bash
# Check if service responding
curl -v http://localhost:18000/health

# Check logs during health check
docker compose logs ai-agent -f

# Check port binding
netstat -tlnp | grep 18000

# Check resource constraints
docker stats ai-agent
```

**Solutions:**
```bash
# Wait longer (service might be slow to start)
sleep 15
curl http://localhost:18000/health

# Increase health check timeout
# healthcheck:
#   test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
#   interval: 30s
#   timeout: 10s  # Increase this
#   retries: 3
#   start_period: 40s  # Wait before first check

# Restart with new config
docker compose down
docker compose up -d
```

---

### Detailed Log Analysis Guide

#### Step 1: Capture Complete Error Context

```bash
# Capture error with surrounding lines
docker compose logs ai-agent 2>&1 | tee debug.log

# Find error
grep -n "ERROR\|EXCEPTION\|Failed\|Traceback" debug.log

# Show context (10 lines before/after error)
grep -B10 -A10 "ERROR\|EXCEPTION" debug.log
```

#### Step 2: Identify Error Type

**Python Errors:**
```
Traceback (most recent call last):       ← Start of stack trace
  File "main.py", line 45, in <module>
ModuleNotFoundError: No module named 'x'  ← Error type and message
```

**Docker Errors:**
```
ERROR: failed to solve with frontend dockerfile.v0
```

**Network Errors:**
```
ConnectionError: [Errno 110] Connection timed out
requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected(...))
```

**Configuration Errors:**
```
ValueError: invalid literal for int() with base 10: 'invalid'
KeyError: 'GEMINI_API_KEY'
```

#### Step 3: Trace Root Cause

**Example 1: ModuleNotFoundError**
```
ERROR: ModuleNotFoundError: No module named 'google'

Action:
1. Check requirements.txt has "google-generativeai"
2. Verify pip install ran successfully
3. Rebuild Docker image: docker compose build
4. Verify: docker exec ai-agent pip list | grep google
```

**Example 2: Connection Refused**
```
ERROR: ConnectionRefusedError: [Errno 111] Connection refused

Action:
1. Check destination service running: docker compose ps
2. Check port correct: grep "ports:" docker-compose.yml
3. Check firewall: netstat -tlnp | grep 5432
4. Restart service: docker compose restart postgres
```

**Example 3: Out of Memory**
```
ERROR: Killed

Action:
1. Check memory: docker stats ai-agent
2. Check limits: docker inspect ai-agent | grep Memory
3. Increase limit in docker-compose.yml
4. Restart: docker compose down && docker compose up -d
```

#### Step 4: Extract Actionable Information

```bash
# Count errors by type
grep "ERROR" debug.log | awk -F: '{print $NF}' | sort | uniq -c

# Find first error
grep -m1 "ERROR\|EXCEPTION" debug.log

# Find last error
grep "ERROR\|EXCEPTION" debug.log | tail -1

# Timeline of errors
grep "ERROR" debug.log | awk '{print $1}' | sort -u
```

---

### GitHub Actions Log Checking

#### Step 1: Access GitHub Actions Logs

```
GitHub Repo → Actions → [Workflow Name] → [Run #] → [Job] → Logs
```

#### Step 2: Search for Errors in Logs

```
Ctrl+F (or Cmd+F on Mac) → Search for:
- "error"
- "failed"
- "exit code"
- "FAILED"
```

#### Step 3: Common CI Errors

**❌ Lint Failed:**
```
Lint (critical rules)
E9: SyntaxError in agent_src/main.py:45: invalid syntax
```

**Fix:**
```bash
ruff check agent_src --show-fixes
# Fix syntax error
git add agent_src
git commit -m "fix: syntax error"
git push
```

**❌ Test Failed:**
```
Test AI Agent (pytest)
FAILED agent_src/tests/test_health.py::test_endpoint
AssertionError: assert 404 == 200
```

**Fix:**
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

**Fix:**
```bash
# Verify SSH credentials in GitHub Secrets
# SSH_PRIVATE_KEY, SSH_HOST, SSH_USER, SSH_PORT all correct
# Re-run workflow
```

#### Step 4: Download Full Logs

```
GitHub Actions → [Run] → Summary → Download logs (zip)
```

---

### Container Log Debugging Techniques

#### Technique 1: Realtime Monitoring (Two Terminals)

**Terminal 1: Watch logs**
```bash
cd /opt/aws-hybrid/staging
docker compose logs -f ai-agent --timestamps
```

**Terminal 2: Trigger action**
```bash
curl -X POST http://localhost:18000/detect \
  -H "Content-Type: application/json" \
  -d '{"event": "test"}'
```

**Terminal 1 Output:**
```
ai-agent  | 2026-04-24T10:30:45.123Z INFO - Received request
ai-agent  | 2026-04-24T10:30:45.456Z DEBUG - Processing event
ai-agent  | 2026-04-24T10:30:45.789Z INFO - Response sent
```

#### Technique 2: Interactive Shell

```bash
# Access container shell
docker exec -it ai-agent bash

# Inside container
python -c "import google; print(google.__version__)"
curl http://payment-api:8000/health
env | grep GEMINI
ls -la /app/
```

#### Technique 3: Log File Analysis

```bash
# Save all logs to file
docker compose logs > /tmp/all-logs.log

# Analyze with grep
grep -E "ERROR|WARN|INFO" /tmp/all-logs.log | cut -d'|' -f2 | sort | uniq -c

# Show errors with timestamps
grep "ERROR" /tmp/all-logs.log | awk '{print $1, $NF}'

# Find performance issues
grep "took.*ms" /tmp/all-logs.log | awk '{print $NF}' | sort -rn | head -10
```

#### Technique 4: Resource Monitoring

```bash
# Monitor resources while running
watch -n 1 'docker stats --no-stream ai-agent payment-api'

# Check file descriptors
docker exec ai-agent lsof | wc -l

# Check connections
docker exec ai-agent netstat -an | grep ESTABLISHED | wc -l

# Memory usage
docker exec ai-agent ps aux | grep python
```

---

### Log File Interpretation

#### Docker Compose Log Format

```
service-name | timestamp | level | message

Example:
ai-agent | 2026-04-24T10:30:45.123456789Z INFO - Uvicorn running on 0.0.0.0:8000
payment-api | 2026-04-24T10:30:46.987654321Z INFO - Server started
```

#### Log Levels

| Level | Meaning | Example |
|-------|---------|---------|
| DEBUG | Detailed diagnostic info | Variable values, function calls |
| INFO | General information | Server started, request received |
| WARNING | Warning message | Deprecated function, low memory |
| ERROR | Error occurred but continues | Failed to connect, invalid input |
| CRITICAL | Critical error, might exit | Out of memory, file system full |

#### Health Check Log Example

```bash
# Good
ai-agent | health check passed (response time: 45ms)

# Warning
ai-agent | health check slow (response time: 2456ms)

# Failed
ai-agent | health check failed (attempt 1/3): connection refused
ai-agent | health check failed (attempt 2/3): timeout
ai-agent | health check failed (attempt 3/3): timeout
ai-agent | health check failed: service will be restarted
```

---

### Setup Log Rotation

```bash
# File: /etc/logrotate.d/aws-hybrid

/opt/aws-hybrid/logs/*.log {
  daily                    # Rotate daily
  rotate 7                 # Keep 7 days
  compress                 # Compress old logs (gzip)
  delaycompress            # Don't compress latest
  notifempty               # Don't rotate if empty
  missingok                # Don't error if missing
  create 0640 ubuntu ubuntu # New files: 640 permission
  sharedscripts
  postrotate
    # Signal services to reopen log files
    docker compose -f /opt/aws-hybrid/staging/docker-compose.staging.yml kill -s HUP
    docker compose -f /opt/aws-hybrid/production/docker-compose.production.yml kill -s HUP
  endscript
}

# Test logrotate
sudo logrotate -f /etc/logrotate.d/aws-hybrid

# Verify
ls -la /opt/aws-hybrid/logs/
# Should see: all-services.log, all-services.log.1.gz, all-services.log.2.gz, etc.
```

---

### Setup Monitoring (Prometheus + Grafana)

```bash
# 1. Create prometheus config
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

# 2. Start Prometheus
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /opt/aws-hybrid/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# 3. Start Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana

# 4. Access dashboards
# Prometheus: http://localhost:9090
#   - Targets → Check health
#   - Graph → Query metrics
#
# Grafana: http://localhost:3000 (admin/admin)
#   - Add Prometheus datasource
#   - Create dashboards
#   - Set alerts

# 5. Useful Prometheus queries
# Container CPU: container_cpu_usage_seconds_total
# Container Memory: container_memory_usage_bytes
# HTTP Requests: http_requests_total
# Error Rate: rate(errors_total[5m])
```

---

### Log Viewing Quick Reference

| Command | Purpose |
|---------|---------|
| `docker compose logs ai-agent` | Show all logs for ai-agent |
| `docker compose logs -f` | Follow logs (real-time) |
| `docker compose logs --tail=50` | Last 50 lines |
| `docker compose logs --since 10m` | Last 10 minutes |
| `docker logs <container-id>` | Direct container logs |
| `docker inspect <container-id>` | Container details & config |
| `docker exec <container> bash` | Access container shell |
| `docker stats <container>` | CPU/Memory usage |
| `netstat -tlnp` | Show open ports |
| `grep ERROR <logfile>` | Find errors in file |
| `tail -f <logfile>` | Follow file updates |
| `journalctl -u docker` | Docker service logs |
| `dmesg` | Kernel logs (OOM kills, etc) |

---

## 🔧 Troubleshooting

### Issue 1: Port Already in Use

```bash
# Problem: Error binding port 18000

# Solution:
lsof -i :18000
kill -9 <PID>

# OR find what's using it
ss -tlnp | grep 18000
docker ps -a | grep 18000
```

### Issue 2: Container Crashes on Start

```bash
# Check logs
docker compose logs ai-agent --tail=50

# Common issues:
# - Missing environment variables
# - Port already bound
# - Memory/CPU constraints
# - Image pull failed

# Solution:
docker compose down
docker compose pull
docker compose up -d
```

### Issue 3: Network Issues

```bash
# Container can't reach external services

# 1. Check DNS
docker exec ai-agent nslookup google.com

# 2. Check network
docker network ls
docker network inspect staging_default

# 3. Check firewall (Security Groups)
# AWS Console → Security Groups
# Verify outbound rules allow traffic
```

### Issue 4: Out of Disk Space

```bash
# Check disk
df -h
du -sh /var/lib/docker

# Solution:
docker system prune -a
docker volume prune

# Or cleanup old images:
docker image rm $(docker image ls -q -f "dangling=true")
```

### Issue 5: GHCR Authentication Failed

```bash
# Problem: Error response from daemon: unauthorized

# Solution:
docker logout ghcr.io
echo $GHCR_TOKEN | docker login ghcr.io -u $GHCR_USERNAME --password-stdin

# Verify token has permissions:
# GitHub → Settings → Personal access tokens
# Check: read:packages, write:packages
```

### Issue 6: Health Check Timeout

```bash
# Problem: curl: (7) Failed to connect

# Solution:
# 1. Check service running
docker compose ps

# 2. Check port
netstat -tlnp | grep 18000

# 3. Check firewall
sudo ufw status
sudo ufw allow 18000

# 4. Wait for service startup
sleep 10
curl http://localhost:18000/health
```

---

## 🆘 Disaster Recovery

### Backup Strategy

```bash
# 1. Backup database (if using)
docker exec postgres pg_dump -U admin database_name > backup.sql

# 2. Backup volumes
docker run --rm \
  -v staging_data:/data \
  -v /opt/backups:/backup \
  alpine tar czf /backup/data-$(date +%Y%m%d).tar.gz -C /data .

# 3. Backup configurations
tar czf /opt/backups/config-$(date +%Y%m%d).tar.gz \
  /opt/aws-hybrid/staging/.env.staging \
  /opt/aws-hybrid/production/.env.production
```

### Rollback Procedure

```bash
# 1. If container is broken
docker compose pull <previous-tag>
docker compose up -d

# 2. If deployment is broken (via GitHub)
# GitHub → Releases → Select previous version
# Create tag (git tag v1.0.0) → Push
# CD workflow automatically deploys

# 3. Manual rollback
docker compose down
docker image rm ghcr.io/owner/ai-agent:staging-latest
docker pull ghcr.io/owner/ai-agent:staging-abc123  # previous hash
docker tag ghcr.io/owner/ai-agent:staging-abc123 ghcr.io/owner/ai-agent:staging-latest
docker compose up -d
```

### Emergency Shutdown

```bash
# If you need to shutdown everything:
docker compose down

# Stop all containers
docker stop $(docker ps -q)

# Remove all containers
docker rm $(docker ps -aq)

# Cleanup everything (DANGEROUS!)
docker system prune -a --volumes
```

---

## 📋 Final Checklist

### Before Going Live

- [ ] AWS account created
- [ ] IAM users setup
- [ ] SSH keys generated and stored
- [ ] Terraform infrastructure created
- [ ] EC2 instances running
- [ ] Docker installed on all instances
- [ ] Environment files configured
- [ ] Staging deployment successful
- [ ] All health checks passing
- [ ] Production deployment successful
- [ ] Monitoring setup complete
- [ ] Logs being collected
- [ ] Backup strategy in place
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

**Version:** 1.0  
**Last Updated:** 24/04/2026  
**Status:** ✅ Ready for Team Implementation
