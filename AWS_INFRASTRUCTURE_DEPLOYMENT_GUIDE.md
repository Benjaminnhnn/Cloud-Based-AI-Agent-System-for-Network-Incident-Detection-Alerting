# Huong Dan Deploy Ha Tang AWS Hybrid

Guide nay ghi lai luong deploy thuc te da chay thanh cong cho repo `aws-hybrid`.
No tap trung vao Terraform + Ansible, bo cac chi dan CI/CD, staging/production release va cac buoc khong can thiet cho viec dung ha tang hien tai.

## Kien Truc Hien Tai

He thong gom 3 EC2 instances trong AWS region `ap-southeast-1`:

| Nhom | Host | Vai tro | Dich vu |
|------|------|---------|---------|
| monitor | `monitor-ai-01` | Monitoring va AI Agent | Prometheus `9090`, Alertmanager `9093`, Grafana `3000`, AI Agent `8000`, Redis rieng cho AI Agent |
| web | `bank-web-01` | Public web gateway | Nginx `80/443`, proxy `/api`, `/docs`, `/openapi.json` sang core backend |
| core | `bank-core-01` | Backend va data services | FastAPI backend `8000`, PostgreSQL `5432`, Redis `6379` |

Security group dang dung:

- SSH `22` chi nen mo cho IP local hien tai va/hoac CIDR CI neu that su can.
- Web `80/443` mo public tren node web.
- Monitor `3000/9090/9093/8000` mo theo `my_ip_cidr`.
- Core `8000` chi cho web/monitor security group truy cap.
- Node Exporter `9100` chi cho monitor truy cap.

## File Quan Trong

| File | Muc dich |
|------|----------|
| `terraform/terraform.tfvars` | Region, IP cho security group, SSH key path, instance type |
| `terraform/security.tf` | Security groups |
| `ansible/inventory.ini` | Public IP va SSH user cua 3 EC2 |
| `ansible.cfg` | Cau hinh Ansible SSH, timeout, host key checking |
| `agent_src/.env` | Gemini/Telegram credentials cho AI Agent, khong commit |
| `automation/update-infrastructure.sh` | Cap nhat IP local, `terraform apply`, sync inventory |
| `automation/ansible-deploy.sh` | Bootstrap server va deploy full stack |
| `ansible/playbooks/deploy-complete-infrastructure.yml` | Playbook deploy monitoring, web gateway, core backend/db/cache, AI Agent |

## Dieu Kien Truoc Khi Chay

Chay cac lenh tu root repo:

```bash
cd /home/hoang_viet/aws-hybrid
```

Kiem tra tool local:

```bash
terraform version
ansible --version
aws --version
docker --version
```

## Buoc 1: Cap Nhat AWS Credentials Cho Profile `target-account`

Terraform provider dung AWS profile `target-account`, nen can cau hinh profile nay truoc.

```bash
aws configure --profile target-account
```

Nhap cac gia tri:

```text
AWS Access Key ID: <access-key>
AWS Secret Access Key: <secret-key>
Default region name: ap-southeast-1
Default output format: json
```

Kiem tra profile:

```bash
aws sts get-caller-identity --profile target-account
```

Neu lenh nay tra ve `Account`, `Arn`, `UserId` thi credentials OK.

## Buoc 2: Chuan Bi SSH Key

Repo dang dung SSH key:

```text
/home/hoang_viet/.ssh/aws-hybrid
/home/hoang_viet/.ssh/aws-hybrid.pub
```

Neu chua co key:

```bash
ssh-keygen -t rsa -b 4096 -f /home/hoang_viet/.ssh/aws-hybrid -N ""
chmod 600 /home/hoang_viet/.ssh/aws-hybrid
```

Kiem tra file key:

```bash
ls -l /home/hoang_viet/.ssh/aws-hybrid /home/hoang_viet/.ssh/aws-hybrid.pub
```

## Buoc 3: Kiem Tra `terraform.tfvars`

Mo `terraform/terraform.tfvars` va dam bao cac gia tri chinh dung:

```hcl
aws_region       = "ap-southeast-1"
my_ip_cidr       = "<your-public-ip>/32"
ci_cd_ssh_cidr_blocks = []

public_key_path  = "/home/hoang_viet/.ssh/aws-hybrid.pub"
private_key_path = "/home/hoang_viet/.ssh/aws-hybrid"

monitor_instance_type = "t3.small"
web_instance_type     = "t3.micro"
core_instance_type    = "t3.micro"
root_volume_size      = 30
```

Lay public IP hien tai:

```bash
curl -s https://api.ipify.org
```

Sau do cap nhat `my_ip_cidr = "<ip>/32"` neu IP da thay doi.

Luu y: `terraform.tfvars`, private key va `.env` la secrets/local config, khong commit len GitHub.

## Buoc 4: Chay Terraform

```bash
cd terraform
terraform init
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
cd ..
```

Sau khi apply, lay IP tu Terraform:

```bash
cd terraform
terraform output
cd ..
```

## Buoc 5: Cap Nhat Lai Ha Tang Va Inventory

Script nay da duoc dung de cap nhat IP local vao `terraform.tfvars`, chay `terraform apply`, va ghi lai `ansible/inventory.ini` tu Terraform output.

```bash
bash automation/update-infrastructure.sh
```

Sau buoc nay, kiem tra inventory:

```bash
cat ansible/inventory.ini
```

Dang ky vong inventory co dang:

```ini
[monitor]
monitor-ai-01 ansible_host=<monitor-public-ip> ansible_user=ec2-user

[web]
bank-web-01 ansible_host=<web-public-ip> ansible_user=ec2-user

[core]
bank-core-01 ansible_host=<core-public-ip> ansible_user=ec2-user

[all:vars]
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_private_key_file=/home/hoang_viet/.ssh/aws-hybrid
```

## Buoc 6: Kiem Tra Ket Noi Ansible

```bash
ansible all -i ansible/inventory.ini -m ping
```

Ket qua dung:

```text
monitor-ai-01 | SUCCESS
bank-web-01   | SUCCESS
bank-core-01  | SUCCESS
```

Neu loi SSH:

- Kiem tra `ansible_ssh_private_key_file` trong `ansible/inventory.ini`.
- Kiem tra `my_ip_cidr` da dung public IP hien tai.
- Chay lai `bash automation/update-infrastructure.sh`.
- Dam bao file private key co permission `600`.

## Buoc 7: Chuan Bi Credentials Cho AI Agent

Tao hoac cap nhat file `agent_src/.env`:

```bash
touch agent_src/.env
nano agent_src/.env
```

Noi dung can co:

```env
AI_AGENT_PORT=8000
GEMINI_API_KEY=<your-gemini-api-key>
TELEGRAM_TOKEN=<your-telegram-bot-token>
TELEGRAM_CHAT_ID=<your-telegram-chat-id>
```

`automation/ansible-deploy.sh` se source file nay va export credentials cho playbook.

## Buoc 8: Deploy Full Stack Bang Ansible

Chay:

```bash
bash automation/ansible-deploy.sh
```

Script se thuc hien:

1. Doc IP tu `ansible/inventory.ini`.
2. Load credentials tu `agent_src/.env`.
3. Kiem tra Ansible connectivity.
4. Bootstrap cac EC2 instances.
5. Deploy Node Exporter tren tat ca instances.
6. Deploy Prometheus, Alertmanager, Grafana tren monitor.
7. Deploy core backend stack tren `bank-core-01`:
   - `aiops-api`
   - `postgres`
   - `redis`
8. Deploy web gateway tren `bank-web-01`:
   - `webserver` Nginx
   - proxy `/api`, `/docs`, `/redoc`, `/openapi.json` sang core backend
9. Deploy AI Agent tren `monitor-ai-01`:
   - `ai-agent`
   - `ai-agent-redis`
10. Kiem tra health va in access URLs.

Ket qua dung o cuoi lenh:

```text
DEPLOYMENT COMPLETED SUCCESSFULLY
failed=0
unreachable=0
```

## Buoc 9: Kiem Tra Sau Deploy

### Kiem tra containers tren tat ca instances

Dung lenh nay khi chay qua Ansible ad-hoc. Can boc Docker Go template bang `{% raw %}` de Ansible khong parse `{{ }}` nhu Jinja:

```bash
ansible all -i ansible/inventory.ini -m shell -a "docker ps --format '{% raw %}table {{.Names}}\t{{.Status}}\t{{.Ports}}{% endraw %}'"
```

Ket qua mong doi:

```text
monitor-ai-01:
ai-agent         Up ... (healthy)   0.0.0.0:8000->8000/tcp
ai-agent-redis   Up ... (healthy)   6379/tcp
alertmanager     Up ...
prometheus       Up ...
grafana          Up ...             0.0.0.0:3000->3000/tcp

bank-web-01:
webserver         Up ...             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp

bank-core-01:
aiops-api         Up ... (healthy)   0.0.0.0:8000->8000/tcp
postgres          Up ... (healthy)   0.0.0.0:5432->5432/tcp
redis             Up ... (healthy)   0.0.0.0:6379->6379/tcp
```

### Kiem tra service tren monitor

```bash
ansible monitor -i ansible/inventory.ini -m shell -a "curl -s http://localhost:9090/-/ready && curl -s http://localhost:3000/api/health && curl -s http://localhost:8000/health"
```

Ket qua mong doi:

```text
Prometheus Server is Ready.
{
  "database": "ok",
  "version": "...",
  "commit": "..."
}
{"status":"healthy","queue":"celery-redis","redis":"connected"}
```

### Kiem tra service tren web

```bash
ansible web -i ansible/inventory.ini -m shell -a "docker ps && curl -s http://localhost/health && curl -s http://localhost/api/health"
```

Ket qua mong doi:

```text
webserver Up ...
OK
{"status":"healthy","environment":"production","service":"AIOps Backend API"}
```

### Kiem tra service tren core

```bash
ansible core -i ansible/inventory.ini -m shell -a "docker ps && curl -s http://localhost:8000/api/health && docker exec postgres psql -U aiops_user -d aiops_db -c 'SELECT 1' && docker exec redis redis-cli ping"
```

Ket qua mong doi:

```text
aiops-api Up ... (healthy)
postgres  Up ... (healthy)
redis     Up ... (healthy)
{"status":"healthy","environment":"production","service":"AIOps Backend API"}
 ?column?
----------
        1
(1 row)
PONG
```

## Access URLs

Lay IP moi nhat tu inventory:

```bash
cat ansible/inventory.ini
```

Dang hien tai:

```text
Webserver:    http://3.1.78.149
Grafana:      http://54.151.146.219:3000
Prometheus:   http://54.151.146.219:9090
Alertmanager: http://54.151.146.219:9093
```

Grafana default credential:

```text
Username: admin
Password: admin123
```

Core API public IP co the khong truy cap duoc tu may local neu security group chi cho web/monitor. Cach dung khuyen nghi:

```text
http://<web-public-ip>/api/health
http://<web-public-ip>/docs
```

## Troubleshooting Ngan Gon

### `terraform plan -out=tfplan` loi credentials

Kiem tra profile:

```bash
aws sts get-caller-identity --profile target-account
aws configure --profile target-account
```

### `ansible all -m ping` loi unreachable

Chay:

```bash
bash automation/update-infrastructure.sh
ansible all -i ansible/inventory.ini -m ping
```

Kiem tra them:

```bash
chmod 600 /home/hoang_viet/.ssh/aws-hybrid
cat ansible/inventory.ini
```

### `docker ps --format 'table {{.Names}}...'` bi loi `unexpected '.'`

Nguyen nhan: Ansible parse `{{.Names}}` thanh Jinja template.

Dung ban escape:

```bash
ansible all -i ansible/inventory.ini -m shell -a "docker ps --format '{% raw %}table {{.Names}}\t{{.Status}}\t{{.Ports}}{% endraw %}'"
```

### Core khong co container Docker

Core phai co:

```text
aiops-api
postgres
redis
```

Neu core trong, chay lai deploy:

```bash
bash automation/ansible-deploy.sh
```

Sau do kiem tra:

```bash
ansible core -i ansible/inventory.ini -m shell -a "docker ps"
```

### Web con `postgres` hoac `redis`

Web chi nen co `webserver`. Neu web con container cu `postgres`/`redis`, don orphan:

```bash
ansible web -i ansible/inventory.ini -m shell -a "cd /opt/webserver && docker-compose up -d --remove-orphans"
```

Playbook hien tai da dung `--remove-orphans` cho lan deploy sau.

### Warning `Found variable using reserved name 'environment'`

Day la warning cua Ansible do `ansible/group_vars/all.yml` co bien ten `environment`.
Warning nay khong lam deploy fail. Co the doi ten bien sau neu muon lam sach log.

### Warning docker-compose `version is obsolete`

Docker Compose moi khong can field `version`.
Warning nay khong lam container fail. Co the xoa field `version` trong compose templates sau neu muon lam sach log.

## Lenh Deploy Nhanh

Khi ha tang da ton tai va chi can deploy lai:

```bash
cd /home/hoang_viet/aws-hybrid
bash automation/update-infrastructure.sh
ansible all -i ansible/inventory.ini -m ping
bash automation/ansible-deploy.sh
```

Kiem tra sau deploy:

```bash
ansible all -i ansible/inventory.ini -m shell -a "docker ps --format '{% raw %}table {{.Names}}\t{{.Status}}\t{{.Ports}}{% endraw %}'"
ansible monitor -i ansible/inventory.ini -m shell -a "curl -s http://localhost:9090/-/ready && curl -s http://localhost:3000/api/health"
ansible web -i ansible/inventory.ini -m shell -a "docker ps"
ansible core -i ansible/inventory.ini -m shell -a "docker ps"
```
