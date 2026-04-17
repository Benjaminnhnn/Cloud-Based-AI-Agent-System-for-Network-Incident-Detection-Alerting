#!/bin/bash
# AWS Credentials Update Helper
# Use this to quickly update credentials and apply security group changes

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     AWS Security Groups Update Helper                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Your AWS credentials are INVALID. You need to:"
echo "1. Get new Access Keys from AWS Console"
echo "2. Paste them below"
echo "3. Security groups will be updated automatically"
echo ""
echo "─────────────────────────────────────────────────────────────"
echo "Step 1: Go to https://console.aws.amazon.com/"
echo "Step 2: IAM Dashboard → Users → Your User → Security Credentials"
echo "Step 3: 'Create access key' → Copy both values"
echo "─────────────────────────────────────────────────────────────"
echo ""

read -p "Paste your AWS Access Key ID: " ACCESS_KEY
read -sp "Paste your AWS Secret Access Key: " SECRET_KEY
echo ""

# Update credentials
mkdir -p ~/.aws
cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = $ACCESS_KEY
aws_secret_access_key = $SECRET_KEY
EOF

chmod 600 ~/.aws/credentials
echo "✓ Credentials saved"

# Test connection
echo ""
echo "Testing AWS connection..."
if aws ec2 describe-security-groups --region ap-southeast-1 --query 'SecurityGroups[0].GroupId' --output text &>/dev/null; then
    echo "✓ AWS connection verified!"
    echo ""
    echo "Updating security groups..."
    
    # Update security groups using AWS CLI
    MONITOR_SG="sg-07b2facae786f1ba7"
    WEB_SG="sg-07bd99bc54578289e"
    CORE_SG="sg-088882249fbfe9009"
    
    # Monitor SG - Grafana 3001 and Prometheus 9090
    aws ec2 authorize-security-group-ingress --group-id $MONITOR_SG --region ap-southeast-1 \
        --ip-permissions IpProtocol=tcp,FromPort=3001,ToPort=3001,IpRanges='[{CidrIp=0.0.0.0/0,Description=Grafana}]' \
        2>/dev/null && echo "✓ Monitor SG: Port 3001 opened" || echo "✓ Monitor SG: Port 3001 already open"
    
    aws ec2 authorize-security-group-ingress --group-id $MONITOR_SG --region ap-southeast-1 \
        --ip-permissions IpProtocol=tcp,FromPort=9090,ToPort=9090,IpRanges='[{CidrIp=0.0.0.0/0,Description=Prometheus}]' \
        2>/dev/null && echo "✓ Monitor SG: Port 9090 opened" || echo "✓ Monitor SG: Port 9090 already open"
    
    # Web SG - Frontend 3000
    aws ec2 authorize-security-group-ingress --group-id $WEB_SG --region ap-southeast-1 \
        --ip-permissions IpProtocol=tcp,FromPort=3000,ToPort=3000,IpRanges='[{CidrIp=0.0.0.0/0,Description=Frontend}]' \
        2>/dev/null && echo "✓ Web SG: Port 3000 opened" || echo "✓ Web SG: Port 3000 already open"
    
    # Core SG - API 8000
    aws ec2 authorize-security-group-ingress --group-id $CORE_SG --region ap-southeast-1 \
        --ip-permissions IpProtocol=tcp,FromPort=8000,ToPort=8000,IpRanges='[{CidrIp=0.0.0.0/0,Description=API}]' \
        2>/dev/null && echo "✓ Core SG: Port 8000 opened" || echo "✓ Core SG: Port 8000 already open"
    
    echo ""
    echo "✓ ALL SECURITY GROUPS UPDATED!"
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  Services are NOW ACCESSIBLE from Internet:               ║"
    echo "╠════════════════════════════════════════════════════════════╣"
    echo "║  Frontend (React):                                         ║"
    echo "║  → http://18.139.198.122:3000                             ║"
    echo "║                                                            ║"
    echo "║  API Backend:                                              ║"
    echo "║  → http://52.77.15.93:8000                                ║"
    echo "║  → http://52.77.15.93:8000/docs (Interactive API)         ║"
    echo "║  → http://52.77.15.93:8000/api/health (Health Check)      ║"
    echo "║                                                            ║"
    echo "║  Monitoring:                                               ║"
    echo "║  → http://18.142.210.110:3001 (Grafana - admin/admin123)  ║"
    echo "║  → http://18.142.210.110:9090 (Prometheus)                ║"
    echo "╚════════════════════════════════════════════════════════════╝"
else
    echo "✗ AWS connection FAILED - Invalid credentials"
    echo ""
    echo "Please verify:"
    echo "1. Access Key ID is correct"
    echo "2. Secret Access Key is correct"
    echo "3. Your AWS account is active"
    echo ""
    echo "Go back to AWS Console and generate new credentials"
    exit 1
fi
