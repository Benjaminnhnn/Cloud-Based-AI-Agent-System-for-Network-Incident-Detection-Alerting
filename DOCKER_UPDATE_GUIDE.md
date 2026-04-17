# Docker Update Guide - Hướng dẫn Cập nhật Docker

## 📋 Mục Lục
1. [Quick Update](#quick-update)
2. [Full Rebuild](#full-rebuild)
3. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Update
**Khi chỉ code Python thay đổi (NHANH NHẤT)**

```bash
# 1. Dừng container hiện tại
docker-compose -f config/docker-compose.prod.yml down

# 2. Rebuild image với cache (sử dụng lại layer cũ)
docker-compose -f config/docker-compose.prod.yml build

# 3. Start container mới
docker-compose -f config/docker-compose.prod.yml up -d

# 4. Verify
docker-compose -f config/docker-compose.prod.yml logs -f ai-agent
```

**Thời gian:** ~30-60 giây (sử dụng cache)

---

## 🔨 Full Rebuild
**Khi thay đổi dependencies hoặc cấu hình (ĐẤY ĐỦ)**

```bash
# 1. Dừng tất cả
docker-compose -f config/docker-compose.prod.yml down

# 2. Xóa old image (CLEAN REBUILD)
docker-compose -f config/docker-compose.prod.yml down --rmi all

# 3. Rebuild from scratch (không cache)
docker-compose -f config/docker-compose.prod.yml build --no-cache

# 4. Start
docker-compose -f config/docker-compose.prod.yml up -d

# 5. Verify
docker-compose -f config/docker-compose.prod.yml logs -f
```

**Thời gian:** 2-3 phút (tải lại tất cả)

---

## ✅ Verification Checklist

```bash
# 1. Check container running
docker-compose -f config/docker-compose.prod.yml ps

# 2. Check logs
docker-compose -f config/docker-compose.prod.yml logs ai-agent

# 3. Test Telegram bot
curl -s http://localhost:8000/health

# 4. Check ports
sudo netstat -tlnp | grep 8000

# 5. Test recovery
python3 /home/hoang_viet/aws-hybrid/agent_src/telegram_bot_handler.py
```

---

## 🔍 File Changes Guide

### Khi thay đổi những file này, hãy dùng:

#### ✅ QUICK UPDATE (Docker cache)
- `agent_src/ai_tools.py` - Thay đổi tools logic
- `agent_src/scenario_nginx_recovery.py` - Recovery workflow
- `agent_src/telegram_bot_handler.py` - Bot logic
- `agent_src/main.py` - API endpoints
- Config Nginx: `/etc/nginx/conf.d/custom.conf`

**Commands:**
```bash
cd /home/hoang_viet/aws-hybrid
docker-compose -f config/docker-compose.prod.yml down
docker-compose -f config/docker-compose.prod.yml build
docker-compose -f config/docker-compose.prod.yml up -d
```

#### 🔨 FULL REBUILD (Xóa cache)
- `agent_src/requirements.txt` - Thêm/xóa dependencies
- `agent_src/Dockerfile` - Thay đổi build steps
- System packages cần cài đặt

**Commands:**
```bash
cd /home/hoang_viet/aws-hybrid
docker-compose -f config/docker-compose.prod.yml down --rmi all
docker-compose -f config/docker-compose.prod.yml build --no-cache
docker-compose -f config/docker-compose.prod.yml up -d
```

---

## 🛠️ Troubleshooting

### Problem: Container fails to start
```bash
# 1. Check logs
docker-compose -f config/docker-compose.prod.yml logs

# 2. Check ports conflict
sudo netstat -tlnp | grep 8000

# 3. Clean and rebuild
docker-compose -f config/docker-compose.prod.yml down --rmi all
docker-compose -f config/docker-compose.prod.yml build --no-cache
docker-compose -f config/docker-compose.prod.yml up -d
```

### Problem: Python import errors
```bash
# Rebuild without cache to reinstall dependencies
docker-compose -f config/docker-compose.prod.yml down --rmi all
docker-compose -f config/docker-compose.prod.yml build --no-cache
docker-compose -f config/docker-compose.prod.yml up -d
```

### Problem: Port already in use
```bash
# Find and kill process
sudo lsof -i :8000
sudo kill -9 <PID>

# Or use different port in docker-compose.yml
# Change: 8000:8000 to 8001:8000
```

### Problem: View container errors
```bash
# Real-time logs
docker-compose -f config/docker-compose.prod.yml logs -f

# Last 100 lines
docker-compose -f config/docker-compose.prod.yml logs --tail=100

# Specific service
docker-compose -f config/docker-compose.prod.yml logs ai-agent
```

---

## 📊 Image & Container Info

```bash
# List all images
docker images | grep ai-agent

# Image size
docker images --no-trunc | grep ai-agent

# Container details
docker-compose -f config/docker-compose.prod.yml ps

# Volume info
docker volume ls | grep aws-hybrid
```

---

## 🔄 Manual Container Management

```bash
# Restart container
docker-compose -f config/docker-compose.prod.yml restart

# Stop all containers
docker-compose -f config/docker-compose.prod.yml down

# Remove all containers and images
docker-compose -f config/docker-compose.prod.yml down -v --rmi all

# Access container shell
docker-compose -f config/docker-compose.prod.yml exec ai-agent /bin/bash
```

---

## 📝 Production Workflow

```
┌─────────────────────────────────────┐
│  1. Update code in agent_src/      │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────┐
        │ Change type?│
        └──┬───────┬──┘
           │       │
      ┌────▼─┐   ┌─▼─────┐
      │Code? │   │Deps?  │
      └──┬───┘   └─┬─────┘
         │         │
    ┌────▼────┐ ┌──▼──────────┐
    │QUICK    │ │FULL REBUILD │
    │UPDATE   │ │--no-cache   │
    └────┬────┘ └──┬──────────┘
         │         │
    ┌────▼─────────▼───┐
    │docker-compose up │
    └────┬─────────────┘
         │
    ┌────▼─────────┐
    │Verify logs   │
    │Test endpoints│
    └──────────────┘
```

---

## ⚡ Quick Commands Reference

```bash
# One-liner quick update
cd /home/hoang_viet/aws-hybrid && docker-compose -f config/docker-compose.prod.yml down && docker-compose -f config/docker-compose.prod.yml build && docker-compose -f config/docker-compose.prod.yml up -d

# One-liner full rebuild
cd /home/hoang_viet/aws-hybrid && docker-compose -f config/docker-compose.prod.yml down --rmi all && docker-compose -f config/docker-compose.prod.yml build --no-cache && docker-compose -f config/docker-compose.prod.yml up -d

# View all logs
cd /home/hoang_viet/aws-hybrid && docker-compose -f config/docker-compose.prod.yml logs -f

# Stop everything
cd /home/hoang_viet/aws-hybrid && docker-compose -f config/docker-compose.prod.yml down
```

---

## 📌 Notes

- Luôn test trước khi deploy production
- Backup `.env` file trước khi rebuild
- Check disk space: `df -h` (cần at least 1GB)
- Monitor logs sau khi update: `docker-compose logs -f`
- Giữ `.env` file không bị delete trong docker down

---

**Last Updated:** 2026-04-07  
**Version:** 1.0
