#!/bin/bash

# Ansible Deployment Script for AWS Demo Web
# Deploys complete stack using Ansible playbooks

set -e

cd /home/hoang_viet/aws-hybrid

echo "=========================================="
echo "🚀 AWS Demo Web - Ansible Deployment"
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

echo ""
echo -e "${BLUE}📍 AWS Infrastructure${NC}"
echo "   Monitor:  18.142.210.110"
echo "   Web:      18.139.198.122"
echo "   API:      52.77.15.93"
echo ""

echo -e "${YELLOW}[STEP 1/3] Testing SSH connectivity...${NC}"
for host in 18.142.210.110 18.139.198.122 52.77.15.93; do
    echo -n "   Checking $host... "
    if timeout 5 ssh -i ~/.ssh/id_rsa -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@$host "echo OK" &>/dev/null; then
        echo -e "${GREEN}✓ Connected${NC}"
    else
        echo -e "${RED}✗ Cannot connect${NC}"
        exit 1
    fi
done

echo ""
echo -e "${YELLOW}[STEP 2/3] Running bootstrap playbook...${NC}"
ansible-playbook -i ansible/inventory.ini \
    ansible/playbooks/bootstrap.yml \
    -vvv 2>&1 | tail -20 || true

echo ""
echo -e "${YELLOW}[STEP 3/3] Deploying application stack...${NC}"
ansible-playbook -i ansible/inventory.ini \
    ansible/playbooks/deploy-webser.yml \
    -vvv

echo ""
echo -e "${GREEN}=========================================="
echo "✅ Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"
echo "   Frontend:   ${GREEN}http://18.139.198.122:3000${NC}"
echo "   API Docs:   ${GREEN}http://52.77.15.93:8000/docs${NC}"
echo "   Prometheus: ${GREEN}http://18.142.210.110:9090${NC}"
echo "   Grafana:    ${GREEN}http://18.142.210.110:3001${NC}"
echo ""
echo -e "${BLUE}🔐 Grafana Login:${NC}"
echo "   Username: ${YELLOW}admin${NC}"
echo "   Password: ${YELLOW}admin123${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "   1. Open http://18.139.198.122:3000 in browser"
echo "   2. Check Grafana: http://18.142.210.110:3001"
echo "   3. Run demo: bash demo-flow.sh"
echo ""
