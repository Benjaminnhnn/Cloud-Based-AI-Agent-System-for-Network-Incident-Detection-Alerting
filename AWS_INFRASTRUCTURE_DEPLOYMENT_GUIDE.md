# AWS Hybrid Infrastructure Deployment Guide

Guide nay danh cho dev dung may khac clone repo va deploy ha tang AWS Hybrid bang Terraform + Ansible, sau do cap nhat GitHub Secrets de CI/CD tro vao dung server.

## 1. Tong Quan

Ha tang gom 3 EC2 instances trong region `ap-southeast-1`:

| Nhom | Host | Vai tro | Dich vu |
|------|------|---------|---------|
| `monitor` | `monitor-ai-01` | Monitoring va AI Agent | Prometheus `9090`, Alertmanager `9093`, Grafana `3000`, AI Agent `8000` |
| `web` | `bank-web-01` | Public web gateway | Nginx `80/443`, proxy API/docs sang core |
| `core` | `bank-core-01` | Backend va data | FastAPI `8000`, PostgreSQL `5432`, Redis `6379` |

Luong chay chinh:

```text
Clone repo
  -> cau hinh AWS profile target-account
  -> cau hinh SSH key
  -> sua terraform/terraform.tfvars theo may moi
  -> terraform apply
  -> cap nhat ansible/inventory.ini
  -> tao agent_src/.env
  -> bash automation/ansible-deploy.sh
  -> cap nhat GitHub Secrets truoc khi chay CI/CD
```

## 2. File Can Chinh

| File | Muc dich |
|------|----------|
| `terraform/terraform.tfvars` | IP may dev, SSH key path, instance type |
| `ansible/inventory.ini` | Public IP va SSH private key path cho Ansible |
| `agent_src/.env` | Gemini/Telegram credentials cho Ansible deploy |
| GitHub Actions Secrets | Credentials cho CD staging/production |

## 3. Dieu Kien Truoc Khi Chay

Dev moi can co:

- AWS access key/secret key co quyen tao/cap nhat EC2, VPC, EIP, Security Group, Key Pair.
- SSH private key de vao EC2, hoac quyen tao key moi.
- `GEMINI_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`.
- Tool local: `terraform`, `aws`, `ansible`, `curl`, `git`.

Chay tu root repo:

```bash
cd /path/to/aws-hybrid
```

Kiem tra tool:

```bash
terraform version
aws --version
ansible --version
```

## 4. Cau Hinh AWS Profile

Terraform provider dang dung profile `target-account`, nen may moi phai cau hinh profile nay:

```bash
aws configure --profile target-account
```

Nhap:

```text
AWS Access Key ID: <access-key>
AWS Secret Access Key: <secret-key>
Default region name: ap-southeast-1
Default output format: json
```

Kiem tra:

```bash
aws sts get-caller-identity --profile target-account
```

Lenh dung se tra ve `Account`, `Arn`, `UserId`.

## 5. Cau Hinh SSH Key

Neu tao key moi:

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/aws-hybrid -N ""
chmod 600 ~/.ssh/aws-hybrid
```

Neu dung key duoc ban giao, copy private key vao may moi, vi du:

```text
~/.ssh/aws-hybrid
```

Sau do:

```bash
chmod 600 ~/.ssh/aws-hybrid
```

Khong commit private key vao repo.

## 6. Sua `terraform/terraform.tfvars`

Lay public IP cua may dev:

```bash
curl -s https://api.ipify.org
```

Sua `terraform/terraform.tfvars`:

```hcl
aws_region = "ap-southeast-1"
my_ip_cidr = "<your-public-ip>/32"
ci_cd_ssh_cidr_blocks = []

public_key_path  = "/home/<user>/.ssh/aws-hybrid.pub"
private_key_path = "/home/<user>/.ssh/aws-hybrid"
ssh_user         = "ec2-user"

monitor_instance_type = "t3.small"
web_instance_type     = "t3.micro"
core_instance_type    = "t3.micro"
root_volume_size      = 30
```

`my_ip_cidr` phai dung IP public hien tai cua may dev, vi security group dung gia tri nay de mo SSH va cac cong monitoring.

## 7. Chay Terraform Va Cap Nhat Inventory

Chay:

```bash
cd terraform
terraform init
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
terraform output -raw ansible_inventory > ../ansible/inventory.ini
cd ..
```

Kiem tra inventory:

```bash
cat ansible/inventory.ini
```

Dang dung:

```ini
[monitor]
monitor-ai-01 ansible_host=<monitor-public-ip> ansible_user=ec2-user

[web]
bank-web-01 ansible_host=<web-public-ip> ansible_user=ec2-user

[core]
bank-core-01 ansible_host=<core-public-ip> ansible_user=ec2-user

[app:children]
web
core

[all:vars]
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_private_key_file=/home/<user>/.ssh/aws-hybrid
```

Neu may dev doi IP sau nay, chay:

```bash
bash automation/update-infrastructure.sh
```

Script nay se cap nhat `my_ip_cidr`, apply Terraform va ghi lai `ansible/inventory.ini`.

## 8. Kiem Tra SSH/Ansible

```bash
ansible all -i ansible/inventory.ini -m ping
```

Ket qua dung:

```text
monitor-ai-01 | SUCCESS
bank-web-01   | SUCCESS
bank-core-01  | SUCCESS
```

Neu `UNREACHABLE`, kiem tra lai:

- `my_ip_cidr` co dung public IP hien tai khong.
- `ansible_ssh_private_key_file` co dung duong dan tren may moi khong.
- Private key da `chmod 600` chua.
- EC2 moi tao co the can cho 1-2 phut de SSH san sang.

## 9. Tao `agent_src/.env`

Tao file:

```bash
touch agent_src/.env
```

Noi dung:

```env
AI_AGENT_PORT=8000
GEMINI_API_KEY=<your-gemini-api-key>
TELEGRAM_TOKEN=<your-telegram-bot-token>
TELEGRAM_CHAT_ID=<your-telegram-chat-id>
```

File nay chi dung local cho Ansible deploy. Khong commit.

## 10. Deploy Bang Ansible

```bash
bash automation/ansible-deploy.sh
```

Script se:

1. Load credentials tu `agent_src/.env`.
2. Test Ansible connectivity.
3. Bootstrap 3 EC2.
4. Deploy monitoring tren `monitor-ai-01`.
5. Deploy backend/db/cache tren `bank-core-01`.
6. Deploy Nginx gateway tren `bank-web-01`.
7. Deploy AI Agent tren `monitor-ai-01`.

Ket qua dung:

```text
DEPLOYMENT COMPLETED SUCCESSFULLY
failed=0
unreachable=0
```

## 11. Kiem Tra Sau Deploy

Lay IP:

```bash
cat ansible/inventory.ini
```

Kiem tra nhanh:

```bash
ansible all -i ansible/inventory.ini -m shell -a "docker ps --format '{% raw %}table {{.Names}}\t{{.Status}}\t{{.Ports}}{% endraw %}'"
ansible monitor -i ansible/inventory.ini -m shell -a "curl -s http://localhost:9090/-/ready && curl -s http://localhost:3000/api/health && curl -s http://localhost:8000/health"
ansible web -i ansible/inventory.ini -m shell -a "curl -s http://localhost/health && curl -s http://localhost/api/health"
ansible core -i ansible/inventory.ini -m shell -a "curl -s http://localhost:8000/api/health"
```

URLs:

```text
Webserver:    http://<web-public-ip>
API health:   http://<web-public-ip>/api/health
API docs:     http://<web-public-ip>/docs
Grafana:      http://<monitor-public-ip>:3000
Prometheus:   http://<monitor-public-ip>:9090
Alertmanager: http://<monitor-public-ip>:9093
AI Agent:     http://<monitor-public-ip>:8000/health
```

Grafana:

```text
Username: admin
Password: admin123
```

## 12. Cap Nhat GitHub Secrets Truoc Khi Chay CI/CD

Can cap nhat GitHub Secrets sau khi doi server/IP/key, truoc khi push `develop`, tao tag `v*`, hoac chay CD workflow thu cong.

Workflow lien quan:

- `.github/workflows/ci.yml`: lint/test/build, khong can deploy secret.
- `.github/workflows/cd-staging.yml`: deploy khi push `develop` hoac `workflow_dispatch`.
- `.github/workflows/cd-production.yml`: deploy khi push tag `v*` hoac `workflow_dispatch`.

### Chinh Secrets Tren GitHub UI

Vao repo tren GitHub:

```text
Settings -> Secrets and variables -> Actions -> Repository secrets
```

Tao secret moi:

1. Bam `New repository secret`.
2. Nhap `Name`, vi du `SSH_HOST`.
3. Paste gia tri vao `Secret`.
4. Bam `Add secret`.

Sua secret da co:

1. Tim secret trong `Repository secrets`.
2. Bam `Update`.
3. Paste gia tri moi.
4. Bam `Update secret`.

GitHub se khong hien lai gia tri sau khi luu. Neu paste sai, update lai secret do.

### Secrets Can Co

| Secret | Gia tri |
|--------|---------|
| `GHCR_USERNAME` | GitHub username/org co quyen push GHCR |
| `GHCR_TOKEN` | GitHub PAT co scope `write:packages`, them `read:packages` neu image private |
| `SSH_HOST` | Public IP/DNS cua EC2 ma workflow SSH vao de deploy release |
| `SSH_PORT` | `22` |
| `SSH_PRIVATE_KEY` | Noi dung private key, khong phai duong dan file |
| `GEMINI_API_KEY` | Gemini API key |
| `TELEGRAM_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat ID |
| `AI_AGENT_PUBLIC_URL` | `http://<monitor-public-ip>:8000` neu dung AI Agent public |
| `DATABASE_URL` | Database URL cho release stack |
| `SECRET_KEY` | Secret key cho backend/API |
| `PROMETHEUS_URL` | `http://<monitor-public-ip>:9090` |

Workflow hien tai SSH bang user `ec2-user`. Neu server dung user khac, phai sua workflow truoc khi chay CD.

### Cach Paste `SSH_PRIVATE_KEY`

Lay key tren may local:

```bash
cat ~/.ssh/aws-hybrid
```

Paste toan bo noi dung vao secret `SSH_PRIVATE_KEY`, bao gom:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

Khong paste file `.pub`, khong them dau ngoac kep, khong thay newline bang `\n`.

### Cach Tao `GHCR_TOKEN`

Tren GitHub:

```text
Avatar -> Settings -> Developer settings -> Personal access tokens -> Tokens (classic)
```

Tao token classic moi, tick:

```text
write:packages
read:packages
```

Copy token ngay sau khi tao va luu vao secret `GHCR_TOKEN`.

### Gia Tri Can Lay Tu Ha Tang Moi

```text
SSH_HOST=<public-ip-cua-node-chay-release-cicd>
SSH_PORT=22
AI_AGENT_PUBLIC_URL=http://<monitor-public-ip>:8000
PROMETHEUS_URL=http://<monitor-public-ip>:9090
```

Luu y: CD workflow copy `release/` va `automation/` vao `/home/ec2-user/aws-hybrid` tren `SSH_HOST`, sau do chay `automation/app-release-deploy.sh`. Hay chon dung server release runtime, hoac sua workflow neu muon deploy theo mo hinh 3 node.

### Kiem Tra Truoc Khi Trigger CD

Test SSH tu may local:

```bash
ssh -i ~/.ssh/aws-hybrid -p 22 ec2-user@<SSH_HOST> 'echo auth-ok'
```

Test GHCR token:

```bash
echo "<GHCR_TOKEN>" | docker login ghcr.io -u "<GHCR_USERNAME>" --password-stdin
```

Trigger staging:

```bash
git push origin develop
```

Trigger production:

```bash
git tag v<version>
git push origin v<version>
```

## 13. Lenh Nhanh

Lan dau tren may moi:

```bash
cd /path/to/aws-hybrid
aws configure --profile target-account
ssh-keygen -t rsa -b 4096 -f ~/.ssh/aws-hybrid -N ""
chmod 600 ~/.ssh/aws-hybrid
curl -s https://api.ipify.org
# sua terraform/terraform.tfvars
cd terraform
terraform init
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
terraform output -raw ansible_inventory > ../ansible/inventory.ini
cd ..
ansible all -i ansible/inventory.ini -m ping
# tao agent_src/.env
bash automation/ansible-deploy.sh
```

Khi da co ha tang va chi can cap nhat IP/deploy lai:

```bash
cd /path/to/aws-hybrid
bash automation/update-infrastructure.sh
ansible all -i ansible/inventory.ini -m ping
bash automation/ansible-deploy.sh
```

## 14. Troubleshooting Ngan

Terraform loi credentials:

```bash
aws sts get-caller-identity --profile target-account
aws configure --profile target-account
```

Ansible `UNREACHABLE`:

```bash
curl -s https://api.ipify.org
bash automation/update-infrastructure.sh
chmod 600 ~/.ssh/aws-hybrid
ansible all -i ansible/inventory.ini -m ping
```

`automation/ansible-deploy.sh` bao thieu credentials:

```bash
cat agent_src/.env
```

Docker format bi loi `unexpected '.'`: dung lenh da boc `{% raw %}` trong phan kiem tra, vi Ansible co the parse `{{.Names}}` nhu Jinja.

## 15. Bao Mat Va Ban Giao

Khong commit:

- AWS Access Key/Secret Access Key.
- SSH private key.
- `agent_src/.env`.
- Telegram/Gemini token.
- Terraform state neu state co secret.

Khi ban giao cho dev khac, gui rieng:

- AWS account/profile/role duoc phep deploy.
- SSH private key hoac cach tao key moi.
- Gia tri cho `agent_src/.env`.
- GitHub Secrets can update.
- Public IP hien tai cua ha tang.
