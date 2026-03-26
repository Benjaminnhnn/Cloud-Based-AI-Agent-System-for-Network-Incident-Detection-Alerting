#!/bin/bash

# AWS Deployment Script for API Server
# This script configures and deploys FastAPI backend on AWS EC2

set -e

echo "🚀 Setting up API Server (Backend)..."

# Update system
sudo yum update -y
sudo yum install -y python3 python3-pip git

# Create application directory
sudo mkdir -p /opt/app
cd /opt/app

# Clone repository (replace with your repo URL)
# sudo git clone https://github.com/your-username/aws-hybrid.git
# For now, we'll assume code is deployed separately

# Navigate to backend directory
cd backend || exit 1

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
sudo tee /opt/app/backend/.env > /dev/null <<EOF
DATABASE_URL=postgresql://aiops_user:aiops_pass@db-server:5432/aiops_db
SECRET_KEY=your-production-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
EOF

# Create systemd service
sudo tee /etc/systemd/system/fastapi.service > /dev/null <<'EOF'
[Unit]
Description=FastAPI Application
After=network.target

[Service]
Type=notify
User=ec2-user
WorkingDirectory=/opt/app/backend
Environment="PATH=/opt/app/backend/venv/bin"
ExecStart=/opt/app/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi

echo "✅ API Server setup complete!"
echo "API accessible at: http://$(hostname -I | awk '{print $1}'):8000"
echo "API docs at: http://$(hostname -I | awk '{print $1}'):8000/docs"
