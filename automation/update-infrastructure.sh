#!/bin/bash

set -e

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Đường dẫn
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/terraform"
ANSIBLE_DIR="$SCRIPT_DIR/ansible"
TF_VARS="$TF_DIR/terraform.tfvars"
INVENTORY="$ANSIBLE_DIR/inventory.ini"

echo -e "${YELLOW}=== AWS Hybrid Infrastructure Update ===${NC}\n"

# 1. Lấy IP public hiện tại
echo -e "${YELLOW}[1/5] Lấy IP public hiện tại...${NC}"
CURRENT_IP=$(curl -s https://api.ipify.org)
if [ -z "$CURRENT_IP" ]; then
    echo -e "${RED}Không thể lấy IP public. Vui lòng kiểm tra kết nối Internet.${NC}"
    exit 1
fi
echo -e "${GREEN}IP hiện tại: $CURRENT_IP${NC}\n"

# 2. Cập nhật terraform.tfvars
echo -e "${YELLOW}[2/5] Cập nhật terraform.tfvars...${NC}"
OLD_IP=$(grep "my_ip_cidr" "$TF_VARS" | cut -d'"' -f2 | cut -d'/' -f1)
if [ "$CURRENT_IP" == "$OLD_IP" ]; then
    echo -e "${GREEN}IP không thay đổi. Bỏ qua cập nhật.${NC}\n"
else
    sed -i "s/my_ip_cidr.*= .*/my_ip_cidr       = \"${CURRENT_IP}\/32\"/" "$TF_VARS"
    echo -e "${GREEN}Cập nhật: $OLD_IP → $CURRENT_IP${NC}\n"
fi

# 3. Chạy terraform apply
echo -e "${YELLOW}[3/5] Áp dụng Terraform changes...${NC}"
cd "$TF_DIR"
terraform apply -auto-approve > /tmp/tf_apply.log 2>&1
echo -e "${GREEN}Terraform apply hoàn tất.${NC}\n"

# 4. Lấy IPs mới từ terraform output
echo -e "${YELLOW}[4/5] Cập nhật Ansible inventory...${NC}"
MONITOR_IP=$(terraform output -raw monitor_public_ip 2>/dev/null || echo "")
WEB_IP=$(terraform output -raw web_public_ip 2>/dev/null || echo "")
CORE_IP=$(terraform output -raw core_public_ip 2>/dev/null || echo "")

if [ -z "$MONITOR_IP" ] || [ -z "$WEB_IP" ] || [ -z "$CORE_IP" ]; then
    echo -e "${RED}Không thể lấy IPs từ Terraform output.${NC}"
    exit 1
fi

# Cập nhật inventory.ini
cat > "$INVENTORY" << EOF
[monitor]
monitor-ai-01 ansible_host=$MONITOR_IP ansible_user=ec2-user

[web]
bank-web-01 ansible_host=$WEB_IP ansible_user=ec2-user

[core]
bank-core-01 ansible_host=$CORE_IP ansible_user=ec2-user

[app:children]
web
core

[all:vars]
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_private_key_file=/home/hoang_viet/.ssh/id_rsa
EOF

echo -e "${GREEN}Cập nhật Ansible inventory:${NC}"
echo -e "  monitor-ai-01: $MONITOR_IP"
echo -e "  bank-web-01:   $WEB_IP"
echo -e "  bank-core-01:  $CORE_IP\n"

# 5. Test ansible ping
echo -e "${YELLOW}[5/5] Test Ansible connectivity...${NC}"
cd "$ANSIBLE_DIR"
if ansible all -m ping 2>/dev/null | grep -q "SUCCESS"; then
    echo -e "${GREEN}✓ Tất cả servers responsive${NC}\n"
else
    echo -e "${YELLOW}⚠ Một số servers chưa responsive (chờ 1-2 phút rồi thử lại)${NC}\n"
fi

echo -e "${GREEN}=== Update hoàn tất ===${NC}"
echo -e "IP public: ${YELLOW}$CURRENT_IP${NC}"
echo -e "Server status:"
cd "$ANSIBLE_DIR"
ansible all -m ping 2>/dev/null | grep -E "SUCCESS|UNREACHABLE" || true
