#!/bin/bash
# Docker entrypoint - start all monitoring components

set -e

echo "🚀 Starting AI Ops Monitoring System..."
echo "   • log_watcher.py (Module 2 - Log monitoring)"
echo "   • service_monitor.py (Modules 1,3 - Prometheus + Ports)"
echo "   • main.py (Webhook + AI analysis)"
echo ""

# Start log_watcher in background
echo "📝 Starting log_watcher..."
python3 log_watcher.py > /dev/stdout 2>&1 &
LOG_WATCHER_PID=$!
echo "   PID: $LOG_WATCHER_PID"

# Start service_monitor in background
echo "📊 Starting service_monitor..."
python3 service_monitor.py > /dev/stdout 2>&1 &
SERVICE_MONITOR_PID=$!
echo "   PID: $SERVICE_MONITOR_PID"

# Start main (webhook) in foreground
echo "🌐 Starting webhook server (main)..."
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# Cleanup on exit
trap "kill $LOG_WATCHER_PID $SERVICE_MONITOR_PID" EXIT
