#!/bin/bash

# =================================================================
# Quick Start: AI Agent Deployment to monitor-ai-01
# =================================================================
# This script automates the entire deployment process
# =================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
MONITOR_IP="18.142.210.110"
PRIVATE_KEY_PATH="$HOME/.ssh/aws-hybrid-key"
SSH_USER="ec2-user"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AI Agent - Quick Deployment Setup         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Verify prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if [ ! -f "$PRIVATE_KEY_PATH" ]; then
    echo -e "${RED}❌ ERROR: Private key not found at $PRIVATE_KEY_PATH${NC}"
    echo -e "${YELLOW}📌 Please ensure your AWS key is at: $PRIVATE_KEY_PATH${NC}"
    exit 1
fi

if ! command -v ssh &> /dev/null; then
    echo -e "${RED}❌ ERROR: SSH client not found${NC}"
    exit 1
fi

if ! command -v scp &> /dev/null; then
    echo -e "${RED}❌ ERROR: SCP client not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites verified${NC}"
echo ""

# Step 2: Test SSH connectivity
echo -e "${YELLOW}🔗 Testing SSH connectivity to $MONITOR_IP...${NC}"
if ! ssh -i "$PRIVATE_KEY_PATH" -o ConnectTimeout=5 "$SSH_USER@$MONITOR_IP" "echo 'SSH OK'" &>/dev/null; then
    echo -e "${RED}❌ ERROR: Cannot connect to monitor-ai-01${NC}"
    echo -e "${YELLOW}📌 Check if:${NC}"
    echo "   - IP is correct (currently: $MONITOR_IP)"
    echo "   - Private key is correct"
    echo "   - EC2 security group allows SSH (port 22)"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection established${NC}"
echo ""

# Step 3: Display deployment info
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo "Monitor IP:        $MONITOR_IP"
echo "SSH User:          $SSH_USER"
echo "Private Key:       $PRIVATE_KEY_PATH"
echo "Deployment Path:   /home/$SSH_USER/aws-hybrid-ai-agent"
echo ""

# Step 4: Ask for credentials
echo -e "${YELLOW}🔐 Enter Telegram & Gemini Credentials${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""

read -p "Enter GEMINI_API_KEY: " GEMINI_API_KEY
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ GEMINI_API_KEY cannot be empty${NC}"
    exit 1
fi

read -p "Enter TELEGRAM_TOKEN: " TELEGRAM_TOKEN
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo -e "${RED}❌ TELEGRAM_TOKEN cannot be empty${NC}"
    exit 1
fi

read -p "Enter TELEGRAM_CHAT_ID: " TELEGRAM_CHAT_ID
if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo -e "${RED}❌ TELEGRAM_CHAT_ID cannot be empty${NC}"
    exit 1
fi

echo ""

# Step 5: Execute deployment script
echo -e "${YELLOW}🚀 Starting deployment...${NC}"
echo ""

DEPLOY_DIR=$(pwd)
if [ ! -f "$DEPLOY_DIR/deploy-ai-agent.sh" ]; then
    echo -e "${RED}❌ ERROR: deploy-ai-agent.sh not found in current directory${NC}"
    exit 1
fi

# Run the main deployment script
bash "$DEPLOY_DIR/deploy-ai-agent.sh" "$MONITOR_IP" "$PRIVATE_KEY_PATH"

# Step 6: Configure credentials remotely
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🔐 Configuring credentials on monitor-ai-01...${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"

ssh -i "$PRIVATE_KEY_PATH" "$SSH_USER@$MONITOR_IP" << EOF
cd /home/$SSH_USER/aws-hybrid-ai-agent

# Create .env.prod with provided credentials
cat > .env.prod << 'ENVEOF'
GEMINI_API_KEY=$GEMINI_API_KEY
TELEGRAM_TOKEN=$TELEGRAM_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
ALERTMANAGER_URL=http://alertmanager:9093
PROMETHEUS_URL=http://prometheus:9090
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
DEBUG=false
ENVEOF

chmod 600 .env.prod
echo "✅ Created .env.prod"
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to configure credentials${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Credentials configured${NC}"
echo ""

# Step 7: Start services
echo -e "${YELLOW}🚀 Starting AI Agent services...${NC}"

ssh -i "$PRIVATE_KEY_PATH" "$SSH_USER@$MONITOR_IP" << EOF
cd /home/$SSH_USER/aws-hybrid-ai-agent

# Start docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Wait for container to be healthy
echo "Waiting for container to start..."
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "healthy"; then
        echo "✅ Container is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Container not healthy after 30 seconds. Check logs:"
        docker logs ai-agent
        exit 1
    fi
    sleep 1
done

# Show status
docker-compose -f docker-compose.prod.yml ps
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to start services${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Step 8: Verify deployment
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${YELLOW}✔️  Verifying deployment...${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"

# Test health endpoint
if curl -s "http://$MONITOR_IP:8000/health" | grep -q "ok"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Health check may not be responding yet${NC}"
fi

# Test API status
echo ""
echo -e "${YELLOW}📊 API Status:${NC}"
curl -s "http://$MONITOR_IP:8000/api/status" | python3 -m json.tool 2>/dev/null || \
    ssh -i "$PRIVATE_KEY_PATH" "$SSH_USER@$MONITOR_IP" "curl -s http://localhost:8000/api/status"

echo ""

# Success message
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL!${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}🎉 Your AI Agent is now running on monitor-ai-01!${NC}"
echo ""
echo -e "${BLUE}Access Information:${NC}"
echo "  Public IP:      $MONITOR_IP"
echo "  Webhook URL:    http://$MONITOR_IP:8000/webhook"
echo "  Health Check:   http://$MONITOR_IP:8000/health"
echo "  API Status:     http://$MONITOR_IP:8000/api/status"
echo "  Dashboard:      http://$MONITOR_IP:8000"
echo ""

echo -e "${BLUE}Remote Commands:${NC}"
echo "  SSH to server:"
echo "    ssh -i $PRIVATE_KEY_PATH $SSH_USER@$MONITOR_IP"
echo ""
echo "  View logs:"
echo "    ssh -i $PRIVATE_KEY_PATH $SSH_USER@$MONITOR_IP 'docker-compose -f ~/aws-hybrid-ai-agent/docker-compose.prod.yml logs -f ai-agent'"
echo ""
echo "  Stop service:"
echo "    ssh -i $PRIVATE_KEY_PATH $SSH_USER@$MONITOR_IP 'cd ~/aws-hybrid-ai-agent && docker-compose -f docker-compose.prod.yml down'"
echo ""

echo -e "${YELLOW}📌 Next Steps:${NC}"
echo "  1. Update AlertManager webhook to: http://$MONITOR_IP:8000/webhook"
echo "  2. Send a test alert to verify Telegram integration"
echo "  3. Monitor dashboard at: http://$MONITOR_IP:8000"
echo ""

echo -e "${GREEN}Happy monitoring! 🚀${NC}"
echo ""
