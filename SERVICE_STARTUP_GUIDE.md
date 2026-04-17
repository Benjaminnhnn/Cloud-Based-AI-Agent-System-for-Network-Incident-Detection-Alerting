# 🚀 SERVICE STARTUP GUIDE - Hướng dẫn Khởi động Dịch vụ

**Project**: AWS Hybrid Cloud - AI Monitoring & Alert System  
**Last Updated**: 2026-04-07

---

## 📋 Mục Lục

1. [Quick Start](#quick-start) - Khởi động nhanh
2. [Full Stack](#full-stack) - Khởi động toàn bộ hệ thống
3. [Individual Services](#individual-services) - Khởi động từng dịch vụ
4. [Status & Verification](#status--verification) - Kiểm tra trạng thái
5. [Viewing Logs](#viewing-logs) - Xem logs
6. [Stopping Services](#stopping-services) - Dừng dịch vụ

---

## 🎯 Quick Start

### Khởi động toàn bộ hệ thống (Dev Stack)

```bash
cd /home/hoang_viet/aws-hybrid

# Khởi động tất cả services
docker-compose -f config/docker-compose.dev.yml up -d

# Kiểm tra trạng thái
docker-compose -f config/docker-compose.dev.yml ps

# Xem logs
docker-compose -f config/docker-compose.dev.yml logs -f
```

**Thời gian**: ~30 giây để tất cả services ready

---

## 🐳 Full Stack

### Khởi động Toàn bộ (All Services)

```bash
cd /home/hoang_viet/aws-hybrid

# ✅ Khởi động toàn bộ dev stack (bao gồm cả monitoring)
docker-compose -f config/docker-compose.dev.yml up -d

# Hoặc khởi động production stack (chỉ AI Agent)
docker-compose -f config/docker-compose.prod.yml up -d
```

### Services sẽ được khởi động:

**DEV Stack (8 services):**
1. ✅ PostgreSQL DB (5432)
2. ✅ FastAPI Backend (8000)
3. ✅ React Frontend (3000)
4. ✅ Node Exporter (9100)
5. ✅ Prometheus (9090)
6. ✅ AlertManager (9093)
7. ✅ Grafana (3001)
8. ✅ AI Agent (5000→8000)

**PROD Stack (1 service):**
1. ✅ AI Agent (8000)

---

## 🎛️ Individual Services

### 1. Prometheus (Time Series Database)

```bash
# ✅ Khởi động
docker-compose -f config/docker-compose.dev.yml up -d prometheus

# ✅ Kiểm tra
docker ps | grep prometheus
curl http://localhost:9090/-/healthy

# ✅ Xem logs
docker logs prometheus

# ✅ Dừng
docker-compose -f config/docker-compose.dev.yml down prometheus
```

**Access**: http://localhost:9090

---

### 2. Grafana (Visualization Dashboard)

```bash
# ✅ Khởi động
docker-compose -f config/docker-compose.dev.yml up -d grafana

# ✅ Kiểm tra
docker ps | grep grafana
curl http://localhost:3001/api/health

# ✅ Xem logs
docker logs grafana

# ✅ Dừng
docker-compose -f config/docker-compose.dev.yml stop grafana
```

**Access**: http://localhost:3001  
**Credentials**: admin / admin123

---

### 3. AlertManager (Alert Routing)

```bash
# ✅ Khởi động (phụ thuộc trên Prometheus)
docker-compose -f config/docker-compose.dev.yml up -d alertmanager

# ✅ Kiểm tra
docker ps | grep alertmanager
curl http://localhost:9093/-/healthy

# ✅ Xem logs
docker logs alertmanager

# ✅ Dừng
docker-compose -f config/docker-compose.dev.yml stop alertmanager
```

**Access**: http://localhost:9093

---

### 4. Node Exporter (Host Metrics)

```bash
# ✅ Khởi động
docker-compose -f config/docker-compose.dev.yml up -d node_exporter

# ✅ Kiểm tra
docker ps | grep node_exporter
curl http://localhost:9100/metrics | head -10

# ✅ Xem logs
docker logs node_exporter

# ✅ Dừng
docker-compose -f config/docker-compose.dev.yml stop node_exporter
```

**Access**: http://localhost:9100/metrics

---

### 5. PostgreSQL Database

```bash
# ✅ Khởi động
docker-compose -f config/docker-compose.dev.yml up -d db

# ✅ Kiểm tra
docker ps | grep aiops-db
docker exec aiops-db pg_isready -U aiops_user

# ✅ Xem logs
docker logs aiops-db

# ✅ Kết nối database
docker exec -it aiops-db psql -U aiops_user -d aiops_db

# ✅ Dừng
docker-compose -f config/docker-compose.dev.yml stop db
```

**Connection String**: `postgresql://aiops_user:aiops_pass@localhost:5432/aiops_db`

---

### 6. FastAPI Backend

```bash
# ✅ Khởi động (phụ thuộc trên DB)
docker-compose -f config/docker-compose.dev.yml up -d api

# ✅ Kiểm tra
docker ps | grep aiops-api
curl http://localhost:8000/api/health

# ✅ Xem logs
docker logs -f aiops-api

# ✅ Dừng
docker-compose -f config/docker-compose.dev.yml stop api
```

**Access**: http://localhost:8000  
**Endpoints**:
- Health: `/api/health`
- Docs: `/api/docs` (Swagger)

---

### 7. React Frontend

```bash
# ✅ Khởi động (phụ thuộc trên API)
docker-compose -f config/docker-compose.dev.yml up -d web

# ✅ Kiểm tra
docker ps | grep aiops-web

# ✅ Xem logs
docker logs aiops-web

# ✅ Dừng
docker-compose -f config/docker-compose.dev.yml stop web
```

**Access**: http://localhost:3000

---

### 8. AI Agent Telegram Bot

```bash
# ✅ Khởi động (Docker)
docker-compose -f config/docker-compose.dev.yml up -d ai-agent

# ✅ Hoặc khởi động trực tiếp (Python)
cd /home/hoang_viet/aws-hybrid/agent_src
python3 telegram_bot_handler.py

# ✅ Hoặc khởi động ngBackground
nohup python3 telegram_bot_handler.py > /tmp/telegram_bot.log 2>&1 &

# ✅ Kiểm tra
docker ps | grep ai-agent
ps aux | grep telegram_bot_handler

# ✅ Xem logs
docker logs ai-agent
tail -f /tmp/telegram_bot.log

# ✅ Dừng
docker-compose -f config/docker-compose.dev.yml stop ai-agent
pkill -f telegram_bot_handler.py
```

**Version**:
- Docker: Port 8000
- Python: Standalone process

---

## ✅ Status & Verification

### 1. Kiểm tra tất cả containers

```bash
# Danh sách containers đang chạy
docker-compose -f config/docker-compose.dev.yml ps

# Danh sách tất cả containers (kể cả stopped)
docker-compose -f config/docker-compose.dev.yml ps -a

# Kiểm tra docker network
docker network ls | grep aiops-network
```

### 2. Kiểm tra từng service

```bash
# Prometheus
curl -s http://localhost:9090/api/v1/status/config | jq '.status'

# Grafana
curl -s http://localhost:3001/api/health | jq '.database'

# AlertManager
curl -s http://localhost:9093/api/v1/alerts | jq '.'

# API
curl -s http://localhost:8000/api/health | jq '.'

# Node Exporter
curl -s http://localhost:9100/metrics | head -5

# Database
docker exec aiops-db pg_isready -U aiops_user
```

### 3. Quick Health Check Script

```bash
#!/bin/bash
echo "🔍 SYSTEM HEALTH CHECK"
echo "═════════════════════════════════"

# Prometheus
echo -n "Prometheus (9090): "
curl -s http://localhost:9090/-/healthy > /dev/null && echo "✅" || echo "❌"

# Grafana
echo -n "Grafana (3001): "
curl -s http://localhost:3001/api/health > /dev/null && echo "✅" || echo "❌"

# AlertManager
echo -n "AlertManager (9093): "
curl -s http://localhost:9093/-/healthy > /dev/null && echo "✅" || echo "❌"

# API
echo -n "API (8000): "
curl -s http://localhost:8000/api/health > /dev/null && echo "✅" || echo "❌"

# Database
echo -n "Database (5432): "
docker exec aiops-db pg_isready -U aiops_user -q && echo "✅" || echo "❌"

# Frontend
echo -n "Frontend (3000): "
curl -s http://localhost:3000 > /dev/null && echo "✅" || echo "❌"

echo "═════════════════════════════════"
```

---

## 📋 Viewing Logs

### 1. View Logs (Real-time)

```bash
# Prometheus
docker logs -f prometheus

# Grafana
docker logs -f grafana

# API
docker logs -f aiops-api

# All services
docker-compose -f config/docker-compose.dev.yml logs -f

# Specific service
docker-compose -f config/docker-compose.dev.yml logs -f prometheus
```

### 2. View Logs (History)

```bash
# Last 50 lines
docker logs --tail=50 prometheus

# Last 100 lines
docker logs --tail=100 grafana

# Follow with timestamp
docker logs -f --timestamps prometheus

# Specific time range
docker logs --since 2026-04-07T10:00:00 prometheus
```

### 3. AI Agent Logs

```bash
# Docker logs
docker logs -f ai-agent

# Python logs (if running directly)
tail -f /tmp/telegram_bot.log

# Recent incidents
tail -f /tmp/telegram_incidents.json
```

---

## ⏹️ Stopping Services

### 1. Dừng Một Service

```bash
# Dừng nhưng giữ container
docker-compose -f config/docker-compose.dev.yml stop prometheus

# Dừng và xóa container
docker-compose -f config/docker-compose.dev.yml rm -f prometheus

# Dừng Python process
pkill -f telegram_bot_handler.py
```

### 2. Dừng Tất cả Services

```bash
# Dừng tất cả nhưng giữ volumes
docker-compose -f config/docker-compose.dev.yml down

# Dừng và xóa volumes (⚠️ DATA LOSS)
docker-compose -f config/docker-compose.dev.yml down -v

# Dừng và xóa images (⚠️ IMAGE LOSS)
docker-compose -f config/docker-compose.dev.yml down --rmi all
```

### 3. Restart Services

```bash
# Restart một service
docker-compose -f config/docker-compose.dev.yml restart prometheus

# Restart tất cả
docker-compose -f config/docker-compose.dev.yml restart

# Restart cụ thể
docker-compose -f config/docker-compose.dev.yml restart prometheus grafana alertmanager
```

---

## 🔄 Dependency Order

**Khởi động đúng thứ tự (nếu khởi động từng cái):**

```
1️⃣  Node Exporter (không phụ thuộc)
2️⃣  PostgreSQL DB (không phụ thuộc)
3️⃣  Prometheus (phụ thuộc Node Exporter)
4️⃣  AlertManager (độc lập, nhưng tốt khi Prometheus sẵn sàng)
5️⃣  Grafana (phụ thuộc Prometheus)
6️⃣  API/FastAPI (phụ thuộc DB)
7️⃣  Frontend/React (phụ thuộc API)
8️⃣  AI Agent (độc lập, nhưng Prometheus/AlertManager tốt)
```

**Docker Compose sẽ tự động xử lý dependencies!**

---

## 🔧 Troubleshooting

### Service không khởi động

```bash
# 1. Kiểm tra logs
docker logs <service-name>

# 2. Kiểm tra port bị chiếm
sudo lsof -i :9090  # Prometheus
sudo lsof -i :3001  # Grafana
sudo lsof -i :8000  # API

# 3. Xóa container cũ
docker rm -f <container-name>

# 4. Restart
docker-compose -f config/docker-compose.dev.yml up -d <service>
```

### Container stopped

```bash
# Kiểm tra lý do
docker inspect <container-name> | grep State

# Chạy lại
docker-compose -f config/docker-compose.dev.yml restart <service>

# Hoặc rebuild
docker-compose -f config/docker-compose.dev.yml restart --no-deps <service>
```

### Port already in use

```bash
# Tìm process sử dụng port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Hoặc thay đổi port trong docker-compose

# Restart
docker-compose -f config/docker-compose.dev.yml restart
```

---

## 📚 Useful Commands Reference

```bash
# Startup
docker-compose -f config/docker-compose.dev.yml up -d
docker-compose -f config/docker-compose.dev.yml up -d <service>

# Status
docker-compose -f config/docker-compose.dev.yml ps
docker ps | grep <service>

# Logs
docker-compose -f config/docker-compose.dev.yml logs -f
docker logs -f <container>
tail -f <log-file>

# Stop/Restart
docker-compose -f config/docker-compose.dev.yml stop
docker-compose -f config/docker-compose.dev.yml restart <service>

# Cleanup
docker-compose -f config/docker-compose.dev.yml down
docker rm -f <container>
docker volume rm <volume>

# Health check
curl http://localhost:PORT/health
docker exec <container> <health-check-cmd>
```

---

## 🎯 Common Startup Scenarios

### Scenario 1: Full Development Stack

```bash
cd /home/hoang_viet/aws-hybrid
docker-compose -f config/docker-compose.dev.yml up -d
docker-compose -f config/docker-compose.dev.yml logs -f
```

**Result**: All 8 services running

---

### Scenario 2: Only Monitoring Stack

```bash
cd /home/hoang_viet/aws-hybrid
docker-compose -f config/docker-compose.dev.yml up -d \
  node_exporter prometheus grafana alertmanager

docker-compose -f config/docker-compose.dev.yml ps
```

**Result**: 4 monitoring services

---

### Scenario 3: Production AI Agent Only

```bash
cd /home/hoang_viet/aws-hybrid
docker-compose -f config/docker-compose.prod.yml up -d

# or run bot directly
cd agent_src
python3 telegram_bot_handler.py
```

**Result**: AI agent running

---

### Scenario 4: Database + API Only

```bash
cd /home/hoang_viet/aws-hybrid
docker-compose -f config/docker-compose.dev.yml up -d db api

docker-compose -f config/docker-compose.dev.yml ps
```

**Result**: DB and API running

---

## ✨ Tips & Tricks

```bash
# 1. Run command inside container
docker exec -it <container> bash

# 2. Check resource usage
docker stats --no-stream

# 3. View all volumes
docker volume ls

# 4. Prune unused resources
docker system prune -a

# 5. Export logs
docker logs <container> > logs.txt

# 6. Check network connectivity
docker network inspect aiops-network

# 7. Rebuild without cache
docker-compose build --no-cache

# 8. One-liner to restart everything
docker-compose -f config/docker-compose.dev.yml down && \
docker-compose -f config/docker-compose.dev.yml up -d
```

---

## 📞 Quick Help

```bash
# Need help?
docker-compose --help
docker-compose -f config/docker-compose.dev.yml --help

# Check version
docker-compose --version
docker --version
```

---

**Version**: 1.0  
**Last Updated**: 2026-04-07  
**Status**: ✅ Production Ready
