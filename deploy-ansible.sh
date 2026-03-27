#!/bin/bash

# =================================================================
# AI Agent Deployment with Ansible
# =================================================================
# One-command deployment to monitor-ai-01 using Ansible
# =================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AI Agent Deployment with Ansible          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""

# Check if Ansible is installed
if ! command -v ansible &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Ansible...${NC}"
    sudo yum install -y ansible
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ansible files
INVENTORY_FILE="$SCRIPT_DIR/ansible/inventory.ini"
PLAYBOOK_FILE="$SCRIPT_DIR/ansible/playbooks/ai_agent_deploy.yml"

# Check files exist
if [ ! -f "$INVENTORY_FILE" ]; then
    echo -e "${RED}❌ ERROR: Inventory file not found: $INVENTORY_FILE${NC}"
    exit 1
fi

if [ ! -f "$PLAYBOOK_FILE" ]; then
    echo -e "${RED}❌ ERROR: Playbook file not found: $PLAYBOOK_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
echo ""

# Check credentials
if [ -z "$GEMINI_API_KEY" ] && [ -z "$1" ]; then
    echo -e "${YELLOW}🔐 Enter Credentials${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    read -p "GEMINI_API_KEY: " GEMINI_API_KEY
    export GEMINI_API_KEY
fi

if [ -z "$TELEGRAM_TOKEN" ] && [ -z "$2" ]; then
    read -p "TELEGRAM_TOKEN: " TELEGRAM_TOKEN
    export TELEGRAM_TOKEN
fi

if [ -z "$TELEGRAM_CHAT_ID" ] && [ -z "$3" ]; then
    read -p "TELEGRAM_CHAT_ID: " TELEGRAM_CHAT_ID
    export TELEGRAM_CHAT_ID
fi

# Arguments override if provided
if [ ! -z "$1" ]; then export GEMINI_API_KEY="$1"; fi
if [ ! -z "$2" ]; then export TELEGRAM_TOKEN="$2"; fi
if [ ! -z "$3" ]; then export TELEGRAM_CHAT_ID="$3"; fi

# Validate
if [ -z "$GEMINI_API_KEY" ] || [ -z "$TELEGRAM_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo -e "${RED}❌ ERROR: Missing required credentials${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Credentials configured${NC}"
echo ""

# Test Ansible connectivity
echo -e "${YELLOW}🔗 Testing Ansible connectivity...${NC}"

if ! ansible -i "$INVENTORY_FILE" monitor -m ping &>/dev/null; then
    echo -e "${RED}❌ ERROR: Cannot connect to monitor host${NC}"
    echo -e "${YELLOW}📌 Check:${NC}"
    echo "   - SSH key path in inventory.ini"
    echo "   - Monitor instance is running"
    echo "   - Security group allows SSH"
    exit 1
fi

echo -e "${GREEN}✅ Connection successful${NC}"
echo ""

# Display deployment info
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

MONITOR_HOST=$(grep "^monitor" "$INVENTORY_FILE" | head -1 | awk '{print $1}')
MONITOR_IP=$(grep "^monitor" "$INVENTORY_FILE" | head -1 | awk -F'ansible_host=' '{print $2}' | awk '{print $1}')

echo "Inventory: $INVENTORY_FILE"
echo "Playbook: $PLAYBOOK_FILE"
echo "Target Host: $MONITOR_HOST"
echo "Target IP: $MONITOR_IP"
echo ""
echo "Credentials: [CONFIGURED]"
echo ""

# Run playbook
echo -e "${YELLOW}🚀 Starting deployment...${NC}"
echo ""

EXTRA_ARGS=""

# Check for command line arguments
if [ ! -z "$1" ]; then
    EXTRA_ARGS="-e gemini_api_key=$GEMINI_API_KEY -e telegram_token=$TELEGRAM_TOKEN -e telegram_chat_id=$TELEGRAM_CHAT_ID"
fi

# Determine if running with verbose flag
VERBOSE_FLAG=""
if [[ "$4" == "-v" ]] || [[ "$4" == "-vv" ]] || [[ "$4" == "-vvv" ]]; then
    VERBOSE_FLAG="$4"
fi

# Run Ansible playbook
ansible-playbook \
    -i "$INVENTORY_FILE" \
    "$PLAYBOOK_FILE" \
    --extra-vars "
        gemini_api_key='$GEMINI_API_KEY'
        telegram_token='$TELEGRAM_TOKEN'
        telegram_chat_id='$TELEGRAM_CHAT_ID'
    " \
    $VERBOSE_FLAG

PLAYBOOK_EXIT_CODE=$?

echo ""
echo ""

# Display result
if [ $PLAYBOOK_EXIT_CODE -eq 0 ]; then
    echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✅ DEPLOYMENT SUCCESSFUL!                   ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${YELLOW}🎉 AI Agent is now running!${NC}"
    echo ""
    
    echo -e "${BLUE}Access Information:${NC}"
    echo "  Public IP: $MONITOR_IP"
    echo "  Webhook: http://$MONITOR_IP:8000/webhook"
    echo "  Health: http://$MONITOR_IP:8000/health"
    echo "  API Status: http://$MONITOR_IP:8000/api/status"
    echo "  Dashboard: http://$MONITOR_IP:8000"
    echo ""
    
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  View logs:"
    echo "    ssh -i \$KEY ec2-user@$MONITOR_IP 'docker logs ai-agent -f'"
    echo ""
    echo "  Restart service:"
    echo "    ssh -i \$KEY ec2-user@$MONITOR_IP 'systemctl restart ai-agent'"
    echo ""
    echo "  Check status:"
    echo "    curl http://$MONITOR_IP:8000/health"
    echo ""
    
    echo -e "${YELLOW}📌 Next Steps:${NC}"
    echo "  1. Verify AlertManager webhook is configured"
    echo "  2. Send a test alert to verify Telegram integration"
    echo "  3. Monitor the dashboard"
    echo ""
    
    echo -e "${GREEN}Happy monitoring! 🚀${NC}"
    
else
    echo -e "${RED}❌ DEPLOYMENT FAILED${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "  1. Run with -v for verbose output: $0 -v"
    echo "  2. Check network connectivity to monitor host"
    echo "  3. Verify credentials are correct"
    echo "  4. Check security group allows necessary ports"
    echo ""
    exit 1
fi
