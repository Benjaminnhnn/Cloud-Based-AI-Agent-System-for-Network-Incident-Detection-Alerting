#!/bin/bash

# Deploy Complete Infrastructure Script
# This script automates the deployment of Prometheus, Grafana, Webserver, and AI Agent

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../" && pwd)"
ANSIBLE_DIR="${PROJECT_ROOT}/ansible"

echo "=============================================="
echo "AWS Hybrid Infrastructure Deployment"
echo "=============================================="
echo "Project Root: ${PROJECT_ROOT}"
echo "Ansible Dir: ${ANSIBLE_DIR}"
echo ""

# Check if running from correct directory
if [ ! -f "${ANSIBLE_DIR}/inventory.ini" ]; then
    echo "ERROR: inventory.ini not found!"
    exit 1
fi

# Check if AI Agent environment variables are set
if [ -z "$GEMINI_API_KEY" ] || [ -z "$TELEGRAM_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "WARNING: AI Agent environment variables not all set!"
    echo "  GEMINI_API_KEY: ${GEMINI_API_KEY:-NOT SET}"
    echo "  TELEGRAM_TOKEN: ${TELEGRAM_TOKEN:-NOT SET}"
    echo "  TELEGRAM_CHAT_ID: ${TELEGRAM_CHAT_ID:-NOT SET}"
    echo ""
    echo "To continue without these, press Enter"
    echo "Or set them now:"
    echo "  export GEMINI_API_KEY='your-key'"
    echo "  export TELEGRAM_TOKEN='your-token'"
    echo "  export TELEGRAM_CHAT_ID='your-chat-id'"
    echo ""
    read -p "Continue with deployment? (y/N): " continue
    if [ "$continue" != "y" ] && [ "$continue" != "Y" ]; then
        exit 1
    fi
fi

# Verify connectivity to all hosts
echo "[1/4] Verifying host connectivity..."
ansible all -i "${ANSIBLE_DIR}/inventory.ini" -m ping

# Check Terraform state
if [ -f "${PROJECT_ROOT}/terraform/terraform.tfstate" ]; then
    echo "[2/4] Terraform infrastructure verified"
else
    echo "WARNING: Terraform state not found. Make sure infrastructure is deployed first."
fi

# Run the deployment playbook
echo "[3/4] Deploying complete infrastructure..."
echo "Command: ansible-playbook -i '${ANSIBLE_DIR}/inventory.ini' '${ANSIBLE_DIR}/playbooks/deploy-complete-infrastructure.yml' -v"
echo ""

cd "${ANSIBLE_DIR}"
ansible-playbook -i inventory.ini playbooks/deploy-complete-infrastructure.yml -v

# Final verification
echo ""
echo "[4/4] Running post-deployment verification..."
sleep 5

ansible all -i inventory.ini -m shell -a "docker ps --format 'table {{.Names}}\t{{.Status}}'"

echo ""
echo "=============================================="
echo "DEPLOYMENT COMPLETED!"
echo "=============================================="
echo ""
echo "Access your services:"
echo "  Grafana: http://$(grep monitor-ai-01 ${ANSIBLE_DIR}/inventory.ini | grep ansible_host | cut -d= -f2 | tr -d ' '):3000"
echo "  Prometheus: http://$(grep monitor-ai-01 ${ANSIBLE_DIR}/inventory.ini | grep ansible_host | cut -d= -f2 | tr -d ' '):9090"
echo "  AlertManager: http://$(grep monitor-ai-01 ${ANSIBLE_DIR}/inventory.ini | grep ansible_host | cut -d= -f2 | tr -d ' '):9093"
echo ""
