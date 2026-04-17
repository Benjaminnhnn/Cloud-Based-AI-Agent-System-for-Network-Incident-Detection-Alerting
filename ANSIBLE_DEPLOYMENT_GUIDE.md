## 📚 Ansible Deployment Guide

Sử dụng Ansible để cấu hình và triển khai toàn bộ hệ thống thay vì shell scripts.

---

## 🎯 Tổng Quan

**Trước**: Shell scripts (.sh) cấu hình từng dịch vụ riêng lẻ  
**Sau**: Ansible playbooks cấu hình tự động, idempotent, có thể kiểm soát

### Lợi Ích
- ✅ **Idempotent**: Chạy lần 2 không gây vấn đề
- ✅ **Có thể kiểm soát**: Variable-driven, dễ tùy chỉnh
- ✅ **Có từ được sao**: Dễ triển khai lại
- ✅ **Theo dõi được**: Có thể xem những gì thay đổi
- ✅ **Vận hành được**: Supports polling, retries, handlers

---

## 📁 Cấu Trúc Thư Mục Ansible

```
ansible/
├── ansible.cfg                          # Cấu hình Ansible
├── inventory.ini                        # Danh sách máy chủ
├── playbooks/
│   ├── bootstrap.yml                    # ✅ System initialization (imported)
│   ├── deploy-complete-infrastructure.yml # ✅ MAIN: One-stop deployment (7 PHASEs)
│   │   ├── PHASE 0: Import bootstrap
│   │   ├── PHASE 1: Node Exporter (all hosts)
│   │   ├── PHASE 2: Prometheus + AlertManager
│   │   ├── PHASE 3: Grafana + 3 Dashboards
│   │   ├── PHASE 4: Webserver + PostgreSQL + Redis (NEW INTEGRATED)
│   │   ├── PHASE 5: AI Agent Deployment
│   │   ├── PHASE 6: Firewall Configuration
│   │   └── PHASE 7: Health Checks & Summary
│   ├── config/
│   │   ├── alert_rules.yml
│   │   ├── alertmanager.yml
│   │   └── prometheus.yml
│   ├── templates/
│   │   ├── ai-agent.service.j2
│   │   ├── alertmanager.yml.j2
│   │   ├── env.prod.j2
│   │   ├── logrotate-ai-agent.j2
│   │   └── module2-watcher.service.j2
│   └── roles/                           # (Tùy chọn: roles)
│
├── group_vars/
│   ├── all.yml                          # Biến chung cho tất cả hosts
│   ├── app.yml                          # Biến cho app servers
│   ├── monitor.yml                      # Biến cho monitor servers
│   └── ...
│
└── host_vars/
    └── (Tùy chọn: biến cho host cụ thể)
```

---

## 🚀 Playbook Chính (One-Stop Deployment)

### Deploy Complete Infrastructure
**File**: `playbooks/deploy-complete-infrastructure.yml`

Triển khai toàn bộ hệ thống với 7 phases tự động:

```bash
# Triển khai tất cả (one-stop deployment)
ansible-playbook playbooks/deploy-complete-infrastructure.yml -i ansible/inventory.ini
```

### PHASE 0: Bootstrap
- Cài đặt dependencies (Docker, Python, etc.)
- Tạo các thư mục cần thiết
- Cấu hình SSH

### PHASE 1: Node Exporter
- Cài đặt Prometheus Node Exporter trên tất cả hosts
- Port: 9100

### PHASE 2: Prometheus + AlertManager
- Deploy Prometheus (port 9090)
- Deploy AlertManager (port 9093)
- Cấu hình alert rules

### PHASE 3: Grafana
- Deploy Grafana (port 3000)
- Tạo 3 auto-dashboards:
  1. System Overview (CPU/Memory/Disk)
  2. Alert Monitoring (Warning/Critical alerts)
  3. Network & Performance (Traffic/Load/I/O)

### PHASE 4: Webserver + Database + Cache ⭐ (NEW INTEGRATED)
**This phase now includes everything that was in configure-services.yml:**

- **PostgreSQL Database** (Docker-based)
  - Image: postgres:13-alpine
  - Port: 5432
  - Auto-initialization: aiops_db
  - Persistence: postgres_data volume
  - Health checks enabled

- **Redis Cache** (Docker-based)
  - Image: redis:7-alpine
  - Port: 6379
  - Persistence: redis_data volume
  - Health checks enabled

- **Nginx Webserver** (Docker-based)
  - Image: nginx:latest
  - Ports: 80, 443
  - Reverse proxy to backend
  - Health check endpoint

- **Docker Compose Orchestration**
  - All services in aiops-network
  - Service dependencies managed
  - Auto-restart policies
  - Integrated logging

### PHASE 5: AI Agent Deployment
- Deploy AI Agent (port 8000)
- Environment variable validation
- Service monitoring

### PHASE 6: Firewall Configuration
- Configure security groups
- Open necessary ports

### PHASE 7: Health Checks & Summary
- Verify all services
- Display deployment summary

---

## 📊 Biến (Variables) Configuration

### group_vars/all.yml
Biến chung cho tất cả hosts:
```yaml
app_name: "aiops-bank"
environment: "production"
python_requirements:
  - requests
  - watchdog
service_ports:
  webhook: 8000
  prometheus: 9090
telegram_bot_token: "{{ lookup('env', 'TELEGRAM_TOKEN') }}"
```

### group_vars/monitor.yml
Biến cho máy monitor (monitor-ai-01):
```yaml
monitoring_system:
  log_watcher:
    watch_paths:
      - /var/log/syslog
      - /var/log/nginx/error.log
    webhook_url: "http://localhost:8000/webhook"
  
  service_monitor:
    check_interval: 5
    prometheus_url: "http://localhost:9090"
```

### group_vars/app.yml
Biến cho app servers (bank-web-01, bank-core-01):
```yaml
services:
  nginx:
    enabled: yes
    port: 80
  postgresql:
    enabled: yes
    port: 5432
```

---

## 🔧 Templating

### services_config.json.j2
Template JSON được sinh ra từ biến Ansible:
```json
{
  "services": {
    "nginx": {
      "enabled": {{ services.nginx.enabled | lower }},
      "port": {{ services.nginx.port }}
    }
  },
  "thresholds": {
    "cpu_warning": {{ cpu_warning_threshold | default(75) }}
  }
}
```

### module2-watcher.service.j2
Template systemd service:
```ini
[Service]
WorkingDirectory={{ agent_src }}
User={{ app_user }}
ExecStart=/usr/bin/python3 {{ agent_src }}/service_monitor.py
```

---

## ⚡ Cách Sử Dụng (One-Stop Deployment)

### 1. Thiết Lập Biến Môi Trường
```bash
# Đặt biến cho Telegram notification
export TELEGRAM_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="987654321"
export GEMINI_API_KEY="AIzaSyD..."

# Verify
echo $TELEGRAM_TOKEN
```

### 2. Kiểm Tra Kết Nối
```bash
# Ping tất cả hosts
ansible all -i ansible/inventory.ini -m ping

# Gather facts
ansible all -i ansible/inventory.ini -m setup
```

### 3. ONE-STOP DEPLOYMENT (Recommended)
```bash
# Triển khai toàn bộ hệ thống (bootstrap + monitoring + database + cache + webserver + AI agent + firewall)
ansible-playbook ansible/playbooks/deploy-complete-infrastructure.yml \
  -i ansible/inventory.ini \
  -v

# Result: Complete infrastructure deployed with a single command
# - All 7 PHASEs executed in order
# - All services started and validated
# - All health checks passed
# - Grafana dashboards created
# - PostgreSQL and Redis initialized
```

### Alternative: Step-by-Step Deployment
```bash
# 1. Bootstrap system (if needed separately)
ansible-playbook ansible/playbooks/bootstrap.yml \
  -i ansible/inventory.ini

# 2. Deploy complete infrastructure
ansible-playbook ansible/playbooks/deploy-complete-infrastructure.yml \
  -i ansible/inventory.ini
```

### Dry-Run Before Actual Deployment
```bash
# Xem tasks trước khi chạy (dry-run chỉ cho bootstrap)
ansible-playbook ansible/playbooks/bootstrap.yml \
  -i ansible/inventory.ini \
  --check \
  -v

# Xem tasks cho main deployment
ansible-playbook ansible/playbooks/deploy-complete-infrastructure.yml \
  -i ansible/inventory.ini \
  --check \
  -v
```

---

## 🔍 Kiểm Tra Trạng Thái

```bash
# Kiểm tra status của Docker services
docker ps
docker-compose -f /opt/webserver/docker-compose.yml ps

# Verify webserver is responding
curl -s http://localhost/health

# Kiểm tra PostgreSQL
docker exec postgres psql -U postgres -d aiops_db -c "SELECT 1"

# Kiểm tra Redis
docker exec redis redis-cli ping

# Kiểm tra Grafana dashboards
curl -s http://admin:admin123@localhost:3000/api/dashboards

# Kiểm tra port listening
netstat -tlnp | grep LISTEN

# View logs
docker logs webserver
docker logs postgres
docker logs redis
```

---

## 🐛 Debugging

### Debug mode
```bash
# Verbose output
ansible-playbook ansible/playbooks/deploy-complete-infrastructure.yml \
  -i ansible/inventory.ini -vvv

# Step-by-step (pauses before each task)
ansible-playbook ansible/playbooks/deploy-complete-infrastructure.yml \
  -i ansible/inventory.ini --step

# Syntax check
ansible-playbook ansible/playbooks/deploy-complete-infrastructure.yml --syntax-check
```

### Troubleshooting Services

**Problem**: PostgreSQL container not starting
```bash
# Check logs
docker logs postgres

# Verify volume
docker volume inspect postgres_data

# Restart
docker restart postgres
```

**Problem**: Redis not responding
```bash
# Test connection
redis-cli -h localhost ping

# Check logs
docker logs redis

# Verify ports
netstat -tlnp | grep 6379
```

**Problem**: Nginx proxy not working
```bash
# Check nginx config
curl -s http://localhost/health

# View nginx logs
docker logs webserver

# Test backend connection
curl -s http://localhost:8000/
```

---

## 📝 Handler & Notifications

Handlers tự động chạy khi files thay đổi:

```yaml
handlers:
  - name: reload_nginx
    systemd:
      name: nginx
      state: reloaded
  
  - name: restart_postgresql
    systemd:
      name: postgresql
      state: restarted
```

Triggers:
```yaml
- name: Copy nginx config
  copy:
    src: nginx.conf
    dest: /etc/nginx/nginx.conf
  notify: reload_nginx  # ← Triggers handler
```

---

## 🔐 Security Best Practices

### 1. Environment Variables
```bash
# Không hardcode credentials trong playbooks
# Thay vào đó dùng environment variables
export GEMINI_API_KEY="..."
export TELEGRAM_TOKEN="..."
```

### 2. Vault (Optional)
```bash
# Encrypt sensitive variables
ansible-vault create group_vars/monitor/vault.yml

# Edit vault file
ansible-vault edit group_vars/monitor/vault.yml

# Run playbook with vault
ansible-playbook playbooks/deploy-monitoring-system.yml \
  -i inventory.ini \
  --ask-vault-pass
```

### 3. Inventory Security
```bash
# Sử dụng SSH keys
ansible_ssh_private_key_file: /home/user/.ssh/id_rsa

# Sử dụng bastion host (nếu cần)
ansible -i inventory.ini all -l host1 \
  -e ansible_ssh_common_args="-o ProxyCommand='ssh -W %h:%p bastion.example.com'"
```

---

## 📈 Scaling & Scaling Out

### Thêm máy chủ mới
```ini
# inventory.ini - Thêm máy chủ mới
[monitor]
monitor-ai-01 ansible_host=52.74.118.8 ansible_user=ec2-user
monitor-ai-02 ansible_host=52.74.118.9 ansible_user=ec2-user

[web]
bank-web-01 ansible_host=18.136.112.28 ansible_user=ec2-user
bank-web-02 ansible_host=18.136.112.29 ansible_user=ec2-user
```

### Triển khai trên máy mới
```bash
# Triển khai chỉ trên monitor-ai-02
ansible-playbook playbooks/deploy-monitoring-system.yml \
  -i inventory.ini \
  -l monitor-ai-02
```

---

## ✅ Checklist Triển Khai

- [ ] Environment variables set (`TELEGRAM_TOKEN`, `GEMINI_API_KEY`, `TELEGRAM_CHAT_ID`)
- [ ] Inventory file updated với đúng IP/hostnames
- [ ] SSH keys configured và accessible
- [ ] Ansible connectivity verified (`ansible all -m ping`)
- [ ] Playbook syntax checked (`--syntax-check`)
- [ ] Dry-run executed (`--check`)
- [ ] One-stop deployment executed (`deploy-complete-infrastructure.yml`)
- [ ] All 7 PHASEs completed successfully
- [ ] PostgreSQL database initialized
- [ ] Redis cache responding
- [ ] Nginx webserver running
- [ ] Grafana dashboards visible (port 3000)
- [ ] Health checks passed
- [ ] Services created Docker volumes
- [ ] Application can access database and cache
- [ ] Alerts configured and working
- [ ] Telegram notifications enabled

---

## 🎓 Full Deployment Script

### One-Stop Complete Infrastructure Deployment
```bash
#!/bin/bash

# Set environment
export TELEGRAM_TOKEN="your-telegram-token"
export TELEGRAM_CHAT_ID="your-chat-id"
export GEMINI_API_KEY="your-gemini-api-key"

# Navigate to project
cd /home/hoang_viet/aws-hybrid

# Step 1: Check connectivity
echo "✓ Checking connectivity..."
ansible all -i ansible/inventory.ini -m ping

# Step 2: Syntax check
echo "✓ Checking playbook syntax..."
ansible-playbook ansible/playbooks/deploy-complete-infrastructure.yml \
  --syntax-check

# Step 3: Dry-run
echo "✓ Executing dry-run..."
ansible-playbook ansible/playbooks/deploy-complete-infrastructure.yml \
  -i ansible/inventory.ini \
  --check \
  -v

# Step 4: MAIN DEPLOYMENT - One-stop deployment
echo "✓ Deploying complete infrastructure..."
ansible-playbook ansible/playbooks/deploy-complete-infrastructure.yml \
  -i ansible/inventory.ini \
  -v

# Step 5: Verify Services
echo "✓ Verifying deployment..."

# Check Docker services
echo "Checking Docker services..."
docker ps

# Check PostgreSQL
echo "Testing PostgreSQL..."
docker exec postgres psql -U postgres -d aiops_db -c "SELECT 1"

# Check Redis
echo "Testing Redis..."
docker exec redis redis-cli ping

# Check Grafana
echo "Accessing Grafana..."
curl -s http://admin:admin123@localhost:3000/api/dashboards

# Check Webserver
echo "Testing Webserver..."
curl -s http://localhost/health

echo "✓ Deployment complete!"
echo ""
echo "Access Points:"
echo "  - Grafana: http://localhost:3000 (admin/admin123)"
echo "  - Prometheus: http://localhost:9090"
echo "  - AlertManager: http://localhost:9093"
echo "  - Webserver: http://localhost"
echo ""
echo "Database & Cache:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
```

### Running the Deployment
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📚 Tài Liệu Bổ Sung

- **Ansible Documentation**: https://docs.ansible.com/
- **Jinja2 Templating**: https://jinja.palletsprojects.com/
- **Best Practices**: https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html

---

**Hết Ansible Deployment Guide!** 🎉
