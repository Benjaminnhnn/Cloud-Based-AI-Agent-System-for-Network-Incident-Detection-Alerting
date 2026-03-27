#!/bin/bash

# =================================================================
# AI Agent Deployment Script for monitor-ai-01 (EC2)
# =================================================================
# Usage: ./deploy-ai-agent.sh <MONITOR_IP> <PRIVATE_KEY_PATH>
# Example: ./deploy-ai-agent.sh 18.142.210.110 ~/.ssh/aws-hybrid-key
# =================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONITOR_IP="${1:-18.142.210.110}"
PRIVATE_KEY="${2:-$HOME/.ssh/aws-hybrid-key}"
SSH_USER="ec2-user"
REMOTE_HOME="/home/$SSH_USER"
DEPLOY_PATH="$REMOTE_HOME/aws-hybrid-ai-agent"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AI Agent Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Validate inputs
if [ ! -f "$PRIVATE_KEY" ]; then
    echo -e "${RED}❌ ERROR: Private key not found: $PRIVATE_KEY${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
echo "  Monitor IP: $MONITOR_IP"
echo "  SSH User: $SSH_USER"
echo "  Private Key: $PRIVATE_KEY"
echo "  Deploy Path: $DEPLOY_PATH"
echo ""

# Function to run remote SSH command
remote_cmd() {
    ssh -i "$PRIVATE_KEY" "$SSH_USER@$MONITOR_IP" "$@"
}

# Step 1: Upload agent code
echo -e "${BLUE}[1/6]${NC} ${YELLOW}Uploading AI Agent code...${NC}"
scp -i "$PRIVATE_KEY" -r ./agent_src "$SSH_USER@$MONITOR_IP:$REMOTE_HOME/" || {
    echo -e "${RED}❌ Failed to upload code${NC}"
    exit 1
}
echo -e "${GREEN}✅ Code uploaded${NC}"
echo ""

# Step 2: Upload docker-compose
echo -e "${BLUE}[2/6]${NC} ${YELLOW}Uploading docker-compose.prod.yml...${NC}"
scp -i "$PRIVATE_KEY" ./docker-compose.prod.yml "$SSH_USER@$MONITOR_IP:$DEPLOY_PATH/" || {
    echo -e "${RED}❌ Failed to upload docker-compose${NC}"
    exit 1
}
echo -e "${GREEN}✅ docker-compose uploaded${NC}"
echo ""

# Step 3: Upload environment template
echo -e "${BLUE}[3/6]${NC} ${YELLOW}Uploading environment template...${NC}"
scp -i "$PRIVATE_KEY" ./.env.prod.template "$SSH_USER@$MONITOR_IP:$DEPLOY_PATH/.env.prod.template" || {
    echo -e "${RED}❌ Failed to upload .env template${NC}"
    exit 1
}
echo -e "${GREEN}✅ Environment template uploaded${NC}"
echo ""

# Step 4: Check Docker installation
echo -e "${BLUE}[4/6]${NC} ${YELLOW}Checking Docker installation...${NC}"
remote_cmd "docker --version" || {
    echo -e "${YELLOW}⚠️  Docker not found. Installing...${NC}"
    remote_cmd "sudo yum update -y && sudo yum install -y docker"
    remote_cmd "sudo systemctl start docker && sudo systemctl enable docker"
    remote_cmd "sudo usermod -aG docker $SSH_USER"
}
echo -e "${GREEN}✅ Docker ready${NC}"
echo ""

# Step 5: Build Docker image
echo -e "${BLUE}[5/6]${NC} ${YELLOW}Building Docker image on monitor-ai-01...${NC}"
remote_cmd "cd $DEPLOY_PATH && docker build -t aws-hybrid_ai-agent:latest ./agent_src" || {
    echo -e "${RED}❌ Failed to build Docker image${NC}"
    exit 1
}
echo -e "${GREEN}✅ Docker image built${NC}"
echo ""

# Step 6: Create .env.prod from template
echo -e "${BLUE}[6/6]${NC} ${YELLOW}Setting up environment configuration...${NC}"
remote_cmd "cd $DEPLOY_PATH && cp .env.prod.template .env.prod && chmod 600 .env.prod" || {
    echo -e "${RED}❌ Failed to create .env.prod${NC}"
    exit 1
}
echo -e "${YELLOW}⚠️  Please update .env.prod with your credentials:${NC}"
echo "  - GEMINI_API_KEY"
echo "  - TELEGRAM_TOKEN"
echo "  - TELEGRAM_CHAT_ID"
echo ""
echo -e "${YELLOW}SSH to update:${NC}"
echo "  ssh -i $PRIVATE_KEY $SSH_USER@$MONITOR_IP"
echo "  nano $DEPLOY_PATH/.env.prod"
echo ""
echo -e "${GREEN}✅ Environment template created${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. SSH to monitor-ai-01:"
echo "   ssh -i $PRIVATE_KEY $SSH_USER@$MONITOR_IP"
echo ""
echo "2. Edit environment variables:"
echo "   nano $DEPLOY_PATH/.env.prod"
echo ""
echo "3. Start AI Agent using docker-compose:"
echo "   cd $DEPLOY_PATH"
echo "   docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "4. Check logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f ai-agent"
echo ""
echo "5. Verify health:"
echo "   curl http://localhost:8000/health"
echo ""
