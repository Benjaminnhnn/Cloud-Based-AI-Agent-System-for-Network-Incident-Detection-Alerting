#!/bin/bash
# Docker entrypoint - start all monitoring components in new structure

set -e

# Đảm bảo PYTHONPATH trỏ tới gốc để các module tìm thấy nhau
export PYTHONPATH=$PYTHONPATH:/app

# Tạo sẵn các file log để bộ monitor không bị crash
mkdir -p /var/log/nginx
touch /var/log/syslog /var/log/nginx/error.log /tmp/test_syslog.log

echo "🚀 Starting AIOps Agent System (Celery & Hybrid Search Enabled)..."
echo "   • monitoring/log_watcher.py"
echo "   • monitoring/service_monitor.py"
echo "   • Celery Worker (Background)"
echo "   • core/main.py (FastAPI Server)"
echo ""

# Start log_watcher
python3 monitoring/log_watcher.py > /dev/stdout 2>&1 &
LOG_WATCHER_PID=$!

# Start service_monitor
python3 monitoring/service_monitor.py > /dev/stdout 2>&1 &
SERVICE_MONITOR_PID=$!

# Start Celery Worker
echo "⚙️ Starting Celery Worker..."
celery -A core.celery_app worker --loglevel=info > /dev/stdout 2>&1 &
CELERY_PID=$!

# Start main (webhook) using module path
echo "🌐 Starting FastAPI Agent Server..."
exec python3 -m uvicorn core.main:app --host 0.0.0.0 --port 8000

# Cleanup on exit
trap "kill $LOG_WATCHER_PID $SERVICE_MONITOR_PID $CELERY_PID" EXIT
