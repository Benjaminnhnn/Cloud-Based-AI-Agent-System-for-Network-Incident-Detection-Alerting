#!/bin/bash

# Ansible Deployment Script for AWS Demo Web
# Deploys complete stack using Ansible playbooks (One-Stop Deployment)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../" && pwd)"
ANSIBLE_DIR="${PROJECT_ROOT}/ansible"

cd "${PROJECT_ROOT}"

echo "=========================================="
echo "🚀 AWS Hybrid - Ansible Deployment"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if Ansible is installed
if ! command -v ansible &> /dev/null; then
    echo -e "${YELLOW}Installing Ansible...${NC}"
    sudo apt-get update
    sudo apt-get install -y ansible
fi

# Verify SSH key permissions
if [ -f ~/.ssh/id_rsa ]; then
    PERMS=$(stat -c '%a' ~/.ssh/id_rsa)
    if [ "$PERMS" != "600" ]; then
        echo -e "${YELLOW}Fixing SSH key permissions...${NC}"
        chmod 600 ~/.ssh/id_rsa
    fi
fi

# Extract IPs from inventory.ini dynamically
echo -e "${BLUE}📍 Reading AWS Infrastructure from inventory...${NC}"
MONITOR_IP=$(grep -A1 "^\[monitor\]" "${ANSIBLE_DIR}/inventory.ini" | grep ansible_host | cut -d'=' -f2 | xargs)
WEB_IP=$(grep -A1 "^\[web\]" "${ANSIBLE_DIR}/inventory.ini" | grep ansible_host | cut -d'=' -f2 | xargs)
CORE_IP=$(grep -A1 "^\[all:children\]" -A10 "${ANSIBLE_DIR}/inventory.ini" | grep -E "monitor-ai|bank-web|bank-core" | head -3 | tail -1 | cut -d'=' -f2 | xargs)

# Try alternative method if above fails
if [ -z "$MONITOR_IP" ]; then
    MONITOR_IP=$(grep "monitor-ai-01" "${ANSIBLE_DIR}/inventory.ini" | grep ansible_host | cut -d'=' -f2 | xargs)
fi
if [ -z "$WEB_IP" ]; then
    WEB_IP=$(grep "bank-web-01" "${ANSIBLE_DIR}/inventory.ini" | grep ansible_host | cut -d'=' -f2 | xargs)
fi
if [ -z "$CORE_IP" ]; then
    CORE_IP=$(grep "bank-core-01" "${ANSIBLE_DIR}/inventory.ini" | grep ansible_host | cut -d'=' -f2 | xargs)
fi

echo "   Monitor:  ${MONITOR_IP:-NOT FOUND}"
echo "   Web:      ${WEB_IP:-NOT FOUND}"
echo "   Core:     ${CORE_IP:-NOT FOUND}"
echo ""

# Load environment variables from agent_src/.env
echo -e "${BLUE}[STEP 1/4] Loading credentials from agent_src/.env...${NC}"
ENV_FILE="${PROJECT_ROOT}/agent_src/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}ERROR: Environment file not found: $ENV_FILE${NC}"
    exit 1
fi

# Source the .env file
set +e  # Temporarily allow sourcing to fail gracefully
source "$ENV_FILE"
set -e

# Validate loaded variables
ENV_CHECK=0
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}   ✗ GEMINI_API_KEY not found in $ENV_FILE${NC}"
    ENV_CHECK=1
else
    echo -e "${GREEN}   ✓ GEMINI_API_KEY loaded${NC}"
fi

if [ -z "$TELEGRAM_TOKEN" ]; then
    echo -e "${RED}   ✗ TELEGRAM_TOKEN not found in $ENV_FILE${NC}"
    ENV_CHECK=1
else
    echo -e "${GREEN}   ✓ TELEGRAM_TOKEN loaded${NC}"
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo -e "${RED}   ✗ TELEGRAM_CHAT_ID not found in $ENV_FILE${NC}"
    ENV_CHECK=1
else
    echo -e "${GREEN}   ✓ TELEGRAM_CHAT_ID loaded${NC}"
fi

if [ $ENV_CHECK -eq 1 ]; then
    echo ""
    echo -e "${RED}ERROR: Missing required credentials in $ENV_FILE${NC}"
    echo "Please update $ENV_FILE with valid credentials:"
    echo "  - GEMINI_API_KEY: Get from https://aistudio.google.com/app/apikeys"
    echo "  - TELEGRAM_TOKEN: Get from @BotFather on Telegram"
    echo "  - TELEGRAM_CHAT_ID: Get from @userinfobot on Telegram"
    exit 1
fi
echo "   ✓ All credentials loaded successfully"
echo ""

echo -e "${YELLOW}[STEP 2/4] Testing SSH connectivity...${NC}"
ansible all -i "${ANSIBLE_DIR}/inventory.ini" -m ping

echo ""
echo -e "${YELLOW}[STEP 3/4] Running bootstrap playbook...${NC}"
ansible-playbook -i "${ANSIBLE_DIR}/inventory.ini" \
    "${ANSIBLE_DIR}/playbooks/bootstrap.yml" \
    -v

echo ""
echo -e "${YELLOW}[STEP 4/4] Deploying complete infrastructure (7 PHASEs)...${NC}"
ansible-playbook -i "${ANSIBLE_DIR}/inventory.ini" \
    "${ANSIBLE_DIR}/playbooks/deploy-complete-infrastructure.yml" \
    -v

echo ""
echo -e "${GREEN}=========================================="
echo "✅ Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"
if [ -n "$WEB_IP" ]; then
    echo "   Frontend (React):   ${GREEN}http://${WEB_IP}:3000${NC}"
fi
if [ -n "$CORE_IP" ]; then
    echo "   API Docs:           ${GREEN}http://${CORE_IP}:8000/docs${NC}"
    echo "   API Health:         ${GREEN}http://${CORE_IP}:8000/api/health${NC}"
fi
if [ -n "$MONITOR_IP" ]; then
    echo "   Prometheus:         ${GREEN}http://${MONITOR_IP}:9090${NC}"
    echo "   Grafana:            ${GREEN}http://${MONITOR_IP}:3000${NC}"
    echo "   AlertManager:       ${GREEN}http://${MONITOR_IP}:9093${NC}"
fi
echo ""
echo -e "${BLUE}🔐 Credentials:${NC}"
echo "   Grafana Admin:      ${YELLOW}admin${NC}"
echo "   Grafana Password:   ${YELLOW}admin123${NC}"
echo "   PostgreSQL:         ${YELLOW}localhost:5432${NC}"
echo "   Redis:              ${YELLOW}localhost:6379${NC}"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "   - ANSIBLE_INTEGRATION_SUMMARY.md"
echo "   - ANSIBLE_DEPLOYMENT_GUIDE.md"
echo "   - README.md"
echo ""
