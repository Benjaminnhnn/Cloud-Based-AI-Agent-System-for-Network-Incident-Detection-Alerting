#!/bin/bash

# AWS Deployment Script for Web Server
# This script configures and deploys the frontend on AWS EC2

set -e

echo "🚀 Setting up Web Server (Frontend)..."

# Update system
sudo yum update -y
sudo yum install -y nodejs npm nginx git

# Create application directory
sudo mkdir -p /var/www/app
cd /var/www/app

# Clone repository (replace with your repo URL)
# sudo git clone https://github.com/your-username/aws-hybrid.git
# For now, we'll assume code is deployed separately

# Navigate to frontend directory
cd frontend || exit 1

# Install dependencies
npm install

# Build React app
npm run build

# Setup Nginx
sudo tee /etc/nginx/conf.d/app.conf > /dev/null <<'EOF'
server {
    listen 80 default_server;
    server_name _;

    root /var/www/app/frontend/build;
    index index.html index.htm;

    # SPA routing - serve index.html for all non-file requests
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://api-server:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable and start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Create systemd service for auto-restart (optional)
sudo tee /etc/systemd/system/nginx.service.d/override.conf > /dev/null <<EOF
[Service]
Restart=on-failure
RestartSec=5s
EOF

sudo systemctl daemon-reload

echo "✅ Web Server setup complete!"
echo "Frontend accessible at: http://$(hostname -I | awk '{print $1}')"
