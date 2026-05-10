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
  -> tao .env.deploy
  -> deploy ha tang/service bang deploy-complete-infrastructure.yml
  -> build/push AI Agent image tu agent_src/
  -> deploy AI Agent bang deploy-ai-agent.yml de EC2 pull image va chay container
  -> cap nhat GitHub Secrets truoc khi chay CI/CD
```

## 2. File Can Chinh

| File | Muc dich |
|------|----------|
| `terraform/terraform.tfvars` | IP may dev, SSH key path, instance type |
| `ansible/inventory.ini` | Public IP va SSH private key path cho Ansible |
| `agent_src/.env` | Gemini/Telegram credentials cho AI Agent runtime |
| `.env.deploy` | Docker registry/image config cho deploy bang image da build san |
| `.env.deploy.example` | File mau de tao `.env.deploy`, khong chua secret that |
| GitHub Actions Secrets | Credentials cho CD staging/production |

## 3. Dieu Kien Truoc Khi Chay

Dev moi can co:

- AWS access key/secret key co quyen tao/cap nhat EC2, VPC, EIP, Security Group, Key Pair.
- SSH private key de vao EC2, hoac quyen tao key moi.
- `GEMINI_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`.
- Docker registry token de push/pull AI Agent image, vi du GHCR token.
- Tool local: `terraform`, `aws`, `ansible`, `curl`, `git`, `docker`.

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

File nay chua runtime credentials cho AI Agent. Script deploy se doc file nay va dua cac bien can thiet vao container. Khong commit.

## 10. Tao `.env.deploy`

Tu luong moi, AI Agent khong copy `agent_src/` len EC2 va khong build image tren EC2 nua.
May local/CI se build image tu `agent_src/`, push len registry, sau do EC2 chi pull image ve chay.

Tao file deploy env local:

```bash
cp .env.deploy.example .env.deploy
```

Sua `.env.deploy`:

```env
GHCR_OWNER=<your-github-user-or-org>
IMAGE_TAG=v1
AI_AGENT_IMAGE=ghcr.io/<your-github-user-or-org>/aws-hybrid-ai-agent:v1
AI_AGENT_REGISTRY=ghcr.io

AI_AGENT_REGISTRY_USERNAME=<your-github-user>
AI_AGENT_REGISTRY_PASSWORD=<github-classic-token>
```

File `.env.deploy` chi dung local va da nam trong `.gitignore`. Khong commit file nay.

### Cach Tao `AI_AGENT_REGISTRY_PASSWORD` Cho GHCR

`AI_AGENT_REGISTRY_PASSWORD` la GitHub Personal Access Token, khong phai password GitHub.

Tren GitHub:

```text
Avatar -> Settings -> Developer settings -> Personal access tokens -> Tokens (classic)
```

Tao token classic moi, tick:

```text
write:packages
read:packages
```

Neu package/repo private, them scope `repo`.

Test login:

```bash
echo "$AI_AGENT_REGISTRY_PASSWORD" | docker login ghcr.io \
  -u "$AI_AGENT_REGISTRY_USERNAME" \
  --password-stdin
```

## 11. Deploy Ha Tang/Service, Build Image va Deploy AI Agent

Quy trinh deploy duoc tach thanh 3 buoc.

### Buoc 11.1: Deploy Ha Tang Va Service Nen

Chay playbook tong de bootstrap EC2 va deploy cac service nen: Node Exporter, Prometheus, AlertManager, Grafana, backend/core, web gateway, firewall va summary.

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-complete-infrastructure.yml
```

### Buoc 11.2: Build Va Push AI Agent Image

Sau khi service nen da co, build image AI Agent tu source trong `agent_src/` va push len registry:

```bash
bash automation/build-push-ai-agent-image.sh
```

Script nay tu doc `.env.deploy`, nen khong can export/source bien thu cong.

Ket qua la registry co image, vi du:

```text
ghcr.io/<owner>/aws-hybrid-ai-agent:v1
```

### Buoc 11.3: Deploy AI Agent Len EC2 Monitor

Sau khi image da co tren registry, deploy AI Agent rieng:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-ai-agent.yml
```

Playbook nay tu doc `.env.deploy` va `agent_src/.env`, nen khong can export/source bien thu cong.

Playbook AI Agent se:

1. Tao `/opt/ai-agent` va `/opt/ai-agent/logs`.
2. Xoa source cu trong `/opt/ai-agent` neu truoc day tung deploy theo cach copy source.
3. Tao `/opt/ai-agent/docker-compose.yml`.
4. Docker login neu `.env.deploy` co registry credentials.
5. `docker-compose pull` de EC2 pull image tu registry.
6. `docker-compose up -d --force-recreate` de chay `ai-agent`, `ai-agent-redis` va `celery-worker`.
7. Health check `http://localhost:8000/health`.

Luu y: webhook cua AI Agent chi enqueue alert vao Redis. Container `celery-worker` moi la thanh phan xu ly task, goi Gemini va gui Telegram. Neu thieu `celery-worker`, Alertmanager van thay webhook `200 OK` nhung Telegram se khong nhan alert.

Ket qua dung:

```text
AI Agent deployed successfully
Status: 200
```

### Khi Chi Update Code AI Agent Sau Nay

Khi ha tang/service nen da chay on va ban chi sua code trong `agent_src/`, chi can lap lai Buoc 11.2 va Buoc 11.3:

```bash
# sua IMAGE_TAG/AI_AGENT_IMAGE trong .env.deploy
bash automation/build-push-ai-agent-image.sh
ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-ai-agent.yml
```

Docker image la snapshot tai thoi diem build. Neu sua source trong `agent_src/`, EC2 se khong thay doi cho den khi ban build/push image moi va deploy AI Agent lai.

## 12. Kiem Tra Sau Deploy

Lay IP public tu inventory:

```bash
cat ansible/inventory.ini
```

Kiem tra container:

```bash
ansible all -i ansible/inventory.ini -m shell -a "docker ps --format '{% raw %}table {{.Names}}\t{{.Status}}\t{{.Ports}}{% endraw %}'"
```

Kiem tra health noi bo cua ha tang/service nen:

```bash
ansible monitor -i ansible/inventory.ini -m shell -a "curl -s http://localhost:9090/-/ready && echo && curl -s http://localhost:9093/-/ready && echo && curl -s http://localhost:3000/api/health"
ansible web -i ansible/inventory.ini -m shell -a "curl -s http://localhost/health && echo && curl -s http://localhost/api/health && echo && curl -s http://localhost/ | grep -qi '<div id=\"root\">' && echo frontend-ok"
ansible core -i ansible/inventory.ini -m shell -a "curl -s http://localhost:8000/api/health"
```

Kiem tra AI Agent sau khi da chay `deploy-ai-agent.yml`:

```bash
ansible monitor -i ansible/inventory.ini -m shell -a "curl -s http://localhost:8000/health"
ansible monitor -i ansible/inventory.ini -m shell -a "docker ps --format '{% raw %}table {{.Names}}\t{{.Status}}{% endraw %}' | egrep 'NAMES|ai-agent|ai-agent-redis|celery-worker'"
ansible monitor -i ansible/inventory.ini -m shell -a "docker exec ai-agent-redis redis-cli llen celery"
```

Kiem tra Prometheus co scrape du metric va Grafana co doc duoc data:

```bash
ansible monitor -i ansible/inventory.ini -m shell -a "curl -s http://localhost:9090/api/v1/targets | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(t['labels'].get('job'), t['labels'].get('instance'), t['health'], t.get('lastError','')) for t in d['data']['activeTargets']]\""
ansible monitor -i ansible/inventory.ini -m shell -a "curl -sG http://localhost:9090/api/v1/query --data-urlencode 'query=up' | python3 -c \"import sys,json; d=json.load(sys.stdin); print('series='+str(len(d['data']['result']))); [print(r['metric'].get('job'), r['metric'].get('instance'), r['value'][1]) for r in d['data']['result']]\""
ansible monitor -i ansible/inventory.ini -m shell -a "curl -s http://admin:admin123@localhost:3000/api/datasources"
```

Kiem tra URL public tu may local:

```bash
curl -i http://<web-public-ip>/
curl -i http://<web-public-ip>/api/health
curl -i http://<web-public-ip>/docs

curl -i http://<monitor-public-ip>:3000/api/health
curl -i http://<monitor-public-ip>:9090/-/ready
curl -i http://<monitor-public-ip>:9093/-/ready
```

URLs truy cap:

```text
Web UI demo:  http://<web-public-ip>
API health:   http://<web-public-ip>/api/health
API docs:     http://<web-public-ip>/docs
Grafana:      http://<monitor-public-ip>:3000
Prometheus:   http://<monitor-public-ip>:9090
Alertmanager: http://<monitor-public-ip>:9093
AI Agent:     http://<monitor-public-ip>:8000/health  # chi sau khi chay deploy-ai-agent.yml
```

URLs theo inventory hien tai:

```text
Web UI demo:  http://3.1.78.149
API health:   http://3.1.78.149/api/health
API docs:     http://3.1.78.149/docs
Grafana:      http://54.151.146.219:3000
Prometheus:   http://54.151.146.219:9090
Alertmanager: http://54.151.146.219:9093
AI Agent:     http://54.151.146.219:8000/health
```

Grafana:

```text
Username: admin
Password: admin123
```

Neu Grafana/Prometheus/Alertmanager public URL bi timeout, kiem tra IP public hien tai:

```bash
curl -s https://api.ipify.org
rg -n "my_ip_cidr" terraform/terraform.tfvars
```

Neu IP hien tai khac `my_ip_cidr`, chay:

```bash
bash automation/update-infrastructure.sh
```

## 13. Cap Nhat GitHub Secrets Truoc Khi Chay CI/CD

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

## 14. Lenh Nhanh

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
cp .env.deploy.example .env.deploy
# sua .env.deploy
ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-complete-infrastructure.yml
bash automation/build-push-ai-agent-image.sh
ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-ai-agent.yml
```

Khi da co ha tang va chi can cap nhat IP/deploy lai:

```bash
cd /path/to/aws-hybrid
bash automation/update-infrastructure.sh
ansible all -i ansible/inventory.ini -m ping
ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-complete-infrastructure.yml
ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-ai-agent.yml
```

Khi chi cap nhat AI Agent:

```bash
cd /path/to/aws-hybrid
# sua IMAGE_TAG/AI_AGENT_IMAGE trong .env.deploy
bash automation/build-push-ai-agent-image.sh
ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-ai-agent.yml
```

## 15. Troubleshooting

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

Build/deploy AI Agent bao thieu credentials:

```bash
cat agent_src/.env
cat .env.deploy
```

Khong pull duoc AI Agent image:

```bash
echo "$AI_AGENT_REGISTRY_PASSWORD" | docker login ghcr.io \
  -u "$AI_AGENT_REGISTRY_USERNAME" \
  --password-stdin
docker pull "$AI_AGENT_IMAGE"
```

Docker format bi loi `unexpected '.'`: dung lenh da boc `{% raw %}` trong phan kiem tra, vi Ansible co the parse `{{.Names}}` nhu Jinja.

### Alertmanager webhook `200 OK` nhung Telegram khong nhan alert

Dau hieu:

- Alertmanager log co `Notify success` hoac AI Agent log co `POST /webhook HTTP/1.1" 200 OK`.
- Telegram bot khong nhan alert.
- Redis queue `celery` tang len hoac co task ton dong.
- `docker ps` khong co container `celery-worker`.

Nguyen nhan:

- `core/main.py` chi nhan webhook va goi `process_alerts_task.delay(...)` de enqueue task vao Redis.
- Task gui Telegram nam trong Celery worker (`process_alerts_task` trong `agent_src/core/tasks.py`).
- Neu stack chi chay `ai-agent` va `ai-agent-redis`, alert se nam trong queue nhung khong co worker xu ly.

Kiem tra nhanh tren monitor host:

```bash
ansible monitor -i ansible/inventory.ini -m shell -a "docker ps --format '{% raw %}table {{.Names}}\t{{.Status}}{% endraw %}' | egrep 'NAMES|alertmanager|ai-agent|ai-agent-redis|celery-worker'"
ansible monitor -i ansible/inventory.ini -m shell -a "docker exec ai-agent sh -c 'for v in TELEGRAM_TOKEN TELEGRAM_CHAT_ID GEMINI_API_KEY; do if [ -n \"\$(printenv \$v)\" ]; then echo \"\$v=set\"; else echo \"\$v=missing\"; fi; done'"
ansible monitor -i ansible/inventory.ini -m shell -a "docker exec ai-agent-redis redis-cli --scan | head -50 && docker exec ai-agent-redis redis-cli llen celery"
ansible monitor -i ansible/inventory.ini -m shell -a "docker logs --since 5m ai-agent 2>&1 | egrep 'POST /webhook|ERROR|WARNING' || true"
ansible monitor -i ansible/inventory.ini -m shell -a "docker logs --since 5m celery-worker 2>&1 | egrep 'Task process_alerts_task|Message sent|All .* Telegram|ERROR|WARNING|succeeded|failed' || true"
```

Kiem tra Telegram token/chat id truc tiep, khong in token ra output:

```bash
ssh -i ~/.ssh/aws-hybrid ec2-user@<monitor-public-ip>

docker exec ai-agent sh -c 'MSG="AIOps Telegram direct test at $(date -u +%Y-%m-%dT%H:%M:%SZ)"; curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" -d chat_id="$TELEGRAM_CHAT_ID" -d text="$MSG" | python -c "import sys,json; d=json.load(sys.stdin); print({k:d.get(k) for k in (\"ok\",\"description\",\"error_code\")})"'
```

Ket qua dung:

```text
{'ok': True, 'description': None, 'error_code': None}
```

Gui alert test qua Alertmanager:

```bash
ssh -i ~/.ssh/aws-hybrid ec2-user@<monitor-public-ip>

START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
END=$(date -u -d "+2 minutes" +%Y-%m-%dT%H:%M:%SZ)
curl -sS -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d "[{\"labels\":{\"alertname\":\"TelegramPipelineWorkerTest\",\"severity\":\"warning\",\"service\":\"availability\",\"instance\":\"monitor-ai-01\"},\"annotations\":{\"summary\":\"Telegram worker pipeline test\",\"description\":\"Synthetic alert after celery-worker startup\"},\"startsAt\":\"$START\",\"endsAt\":\"$END\",\"generatorURL\":\"http://manual-test/telegram-worker-pipeline\"}]"

sleep 20
docker logs --since 1m ai-agent 2>&1 | egrep "POST /webhook|ERROR|WARNING" || true
docker logs --since 1m celery-worker 2>&1 | egrep "TelegramPipelineWorkerTest|Task process_alerts_task|Message sent|All .* Telegram|succeeded|failed|ERROR|WARNING" || true
docker exec ai-agent-redis redis-cli llen celery
```

Ket qua dung:

```text
POST /webhook HTTP/1.1" 200 OK
Task process_alerts_task[...] received
All 1 message parts sent to Telegram!
Task process_alerts_task[...] succeeded
0
```

Hotfix runtime neu thieu `celery-worker`:

```bash
ssh -i ~/.ssh/aws-hybrid ec2-user@<monitor-public-ip>
cd /opt/ai-agent
```

Them service sau vao `/opt/ai-agent/docker-compose.yml`, dung cung image va environment voi `ai-agent`:

```yaml
  celery-worker:
    image: "<same-ai-agent-image>"
    container_name: celery-worker
    command: ["celery", "-A", "core.celery_app.celery_app", "worker", "--loglevel=INFO", "--concurrency=1", "--prefetch-multiplier=1"]
    environment:
      - GEMINI_API_KEY=<same-as-ai-agent>
      - TELEGRAM_TOKEN=<same-as-ai-agent>
      - TELEGRAM_CHAT_ID=<same-as-ai-agent>
      - REDIS_HOST=ai-agent-redis
      - REDIS_PORT=6379
      - REDIS_DB=0
      - LOG_LEVEL=INFO
      - DEBUG=false
      - PYTHONUNBUFFERED=1
    depends_on:
      - ai-agent-redis
    volumes:
      - /opt/ai-agent/logs:/app/logs
    networks:
      - aiops-network
    restart: unless-stopped
```

Start worker:

```bash
docker-compose up -d celery-worker
docker ps --format "table {{.Names}}\t{{.Status}}" | egrep "NAMES|celery-worker|ai-agent|redis"
docker logs --since 2m celery-worker
docker exec ai-agent-redis redis-cli llen celery
```

Fix lau dai:

- `ansible/playbooks/deploy-ai-agent.yml` phai tao service `celery-worker` trong `/opt/ai-agent/docker-compose.yml`.
- Worker nen dung command:

```yaml
command: ["celery", "-A", "core.celery_app.celery_app", "worker", "--loglevel=INFO", "--concurrency=1", "--prefetch-multiplier=1"]
```

- `--concurrency=1` va `--prefetch-multiplier=1` giup tranh xu ly backlog qua nhanh lam Gemini bi quota `429 RESOURCE_EXHAUSTED`.
- Neu log worker co `Gemini API error: 429 RESOURCE_EXHAUSTED`, Telegram van co the gui fallback message, nhung nen giam concurrency hoac nang quota Gemini de phan tich AI on dinh hon.
- Sau khi sua playbook, chay:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-ai-agent.yml --syntax-check
ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy-ai-agent.yml
```

### Prometheus khong scrape duoc metric / target `blackbox_http_web` down

Dau hieu:

- Prometheus target `blackbox_http_web` hien `down`.
- `lastError` co dang `dial tcp 127.0.0.1:9115: connect: connection refused`.
- Alert `ServiceDown` hoac `ServiceUnreachable` firing, trong khi web endpoint that van tra `200 OK`.

Kiem tra tren monitor host:

```bash
ansible monitor -i ansible/inventory.ini -m shell -a "curl -s http://localhost:9090/api/v1/targets | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(t['labels'].get('job'), t['labels'].get('instance'), t['health'], t.get('lastError','')) for t in d['data']['activeTargets']]\""
ansible monitor -i ansible/inventory.ini -m shell -a "ss -ltnp | egrep ':(9090|9093|9100|9115|3000|8000)' || true"
ansible monitor -i ansible/inventory.ini -m shell -a "curl -sS http://localhost:9115/-/healthy || true"
ansible monitor -i ansible/inventory.ini -m shell -a "curl -sS 'http://localhost:9115/probe?module=http_2xx&target=http://<web-public-ip>/health' | egrep 'probe_success|probe_http_status_code|probe_duration_seconds' || true"
```

Nguyen nhan thuong gap:

- Prometheus config co job `blackbox_http_web` tro toi `localhost:9115`, nhung `blackbox-exporter` chua duoc deploy/chua chay.
- Web endpoint `http://<web-public-ip>/health` van tot, nhung Prometheus khong goi duoc exporter trung gian nen target van bi down.

Hotfix runtime tren monitor host:

```bash
ssh -i ~/.ssh/aws-hybrid ec2-user@<monitor-public-ip>

sudo mkdir -p /opt/blackbox
sudo tee /opt/blackbox/blackbox.yml >/dev/null <<'EOF'
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      method: GET
      preferred_ip_protocol: ip4
      valid_status_codes: []
      follow_redirects: true
EOF
sudo chown -R nobody:nobody /opt/blackbox
```

Them service sau vao `/opt/prometheus/docker-compose.yml` cung cap voi `prometheus` va `alertmanager`:

```yaml
  blackbox-exporter:
    image: prom/blackbox-exporter:latest
    container_name: blackbox-exporter
    network_mode: host
    volumes:
      - /opt/blackbox/blackbox.yml:/etc/blackbox_exporter/config.yml:ro
    command:
      - '--config.file=/etc/blackbox_exporter/config.yml'
    restart: unless-stopped
```

Neu service `prometheus` co `depends_on`, them:

```yaml
    depends_on:
      - blackbox-exporter
```

Apply lai stack:

```bash
cd /opt/prometheus
docker-compose up -d
```

Kiem tra ket qua dung:

```bash
curl -sS http://localhost:9115/-/healthy
curl -sS "http://localhost:9115/probe?module=http_2xx&target=http://<web-public-ip>/health" | egrep "probe_success|probe_http_status_code"
curl -s http://localhost:9090/api/v1/alerts
```

Ket qua dung:

```text
probe_http_status_code 200
probe_success 1
```

Fix lau dai:

- `ansible/playbooks/deploy-complete-infrastructure.yml` phai tao `/opt/blackbox/blackbox.yml`.
- Docker compose Prometheus trong playbook phai co service `blackbox-exporter`.
- `platform-config/docker-compose.dev.yml` cung nen co `blackbox-exporter` de moi truong dev khong bi lech.

### Grafana dashboard hien `No data` do tro sai datasource UID

Dau hieu:

- Prometheus van co data, vi query `up`, CPU, memory deu tra series.
- Grafana datasource `Prometheus` healthy.
- Nhung 3 dashboard Grafana (`Alert Monitoring`, `Network & Performance`, `System Overview`) hien `No data`.
- Dashboard JSON dang tro UID cu, vi du `bfijh14lltg5ce`, trong khi datasource hien tai co UID khac.

Kiem tra Prometheus co data:

```bash
ansible monitor -i ansible/inventory.ini -m shell -a "curl -sG http://localhost:9090/api/v1/query --data-urlencode 'query=up' | python3 -c \"import sys,json; d=json.load(sys.stdin); print('series='+str(len(d['data']['result']))); [print(r['metric'].get('job'), r['metric'].get('instance'), r['value'][1]) for r in d['data']['result']]\""
```

Kiem tra datasource UID hien tai:

```bash
ansible monitor -i ansible/inventory.ini -m shell -a "curl -s http://admin:admin123@localhost:3000/api/datasources/name/Prometheus"
```

Kiem tra dashboard dang tro UID nao:

```bash
ansible monitor -i ansible/inventory.ini -m shell -a "for uid in \$(curl -s 'http://admin:admin123@localhost:3000/api/search?type=dash-db' | python3 -c \"import sys,json; [print(d['uid']) for d in json.load(sys.stdin)]\"); do echo DASH:\$uid; curl -s http://admin:admin123@localhost:3000/api/dashboards/uid/\$uid | python3 -c \"import sys,json; d=json.load(sys.stdin); targets=[t for p in d.get('dashboard',{}).get('panels',[]) for t in p.get('targets',[])]; print(sorted(set(str(t.get('datasource')) for t in targets)))\"; done"
```

Hotfix runtime:

```bash
ssh -i ~/.ssh/aws-hybrid ec2-user@<monitor-public-ip>

python3 - <<'PY'
import base64
import json
import urllib.request

base = "http://localhost:3000"
auth = "Basic " + base64.b64encode(b"admin:admin123").decode()

def request(method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(base + path, data=data, method=method)
    req.add_header("Authorization", auth)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

prometheus_uid = request("GET", "/api/datasources/name/Prometheus")["uid"]
dashboards = request("GET", "/api/search?type=dash-db")

for item in dashboards:
    wrapper = request("GET", f"/api/dashboards/uid/{item['uid']}")
    dashboard = wrapper["dashboard"]
    for panel in dashboard.get("panels", []):
        for target in panel.get("targets", []):
            datasource = target.get("datasource")
            if isinstance(datasource, dict) and datasource.get("type") == "prometheus":
                datasource["uid"] = prometheus_uid
    request("POST", "/api/dashboards/db", {
        "dashboard": dashboard,
        "folderId": wrapper.get("meta", {}).get("folderId", 0),
        "overwrite": True,
        "message": "Fix Prometheus datasource UID",
    })
    print("updated", dashboard.get("title"), item["uid"], "->", prometheus_uid)
PY
```

Kiem tra Grafana query qua datasource API:

```bash
ansible monitor -i ansible/inventory.ini -m shell -a "now=\$(date +%s000); from=\$((now-300000)); curl -s -X POST -H 'Content-Type: application/json' http://admin:admin123@localhost:3000/api/ds/query --data \"{\\\"from\\\":\\\"\$from\\\",\\\"to\\\":\\\"\$now\\\",\\\"queries\\\":[{\\\"refId\\\":\\\"A\\\",\\\"datasource\\\":{\\\"type\\\":\\\"prometheus\\\",\\\"uid\\\":\\\"\$(curl -s http://admin:admin123@localhost:3000/api/datasources/name/Prometheus | python3 -c 'import sys,json; print(json.load(sys.stdin)[\\\"uid\\\"])')\\\"},\\\"expr\\\":\\\"up\\\",\\\"instant\\\":true,\\\"range\\\":false,\\\"format\\\":\\\"time_series\\\",\\\"intervalMs\\\":15000,\\\"maxDataPoints\\\":100}]}\" | python3 -c \"import sys,json; d=json.load(sys.stdin); print('frames='+str(len(d.get('results',{}).get('A',{}).get('frames',[]))))\""
```

Fix lau dai:

- Datasource Prometheus trong `deploy-complete-infrastructure.yml` nen co UID co dinh, vi du `uid: prometheus`.
- Dashboard templates trong `ansible/templates/*.json` va `ansible/playbooks/templates/*.json` khong nen giu UID cu sinh ngau nhien.
- Truoc khi import dashboard, playbook nen lay UID datasource that tu Grafana API `/api/datasources/name/Prometheus` va patch dashboard JSON tam thoi de tranh lech UID khi datasource da ton tai tu deploy cu.

## 16. Bao Mat Va Ban Giao

Khong commit:

- AWS Access Key/Secret Access Key.
- SSH private key.
- `agent_src/.env`.
- `.env.deploy`.
- Telegram/Gemini token.
- Docker registry token/GHCR token.
- Terraform state neu state co secret.

Khi ban giao cho dev khac, gui rieng:

- AWS account/profile/role duoc phep deploy.
- SSH private key hoac cach tao key moi.
- Gia tri cho `agent_src/.env`.
- Gia tri registry/image cho `.env.deploy`.
- GitHub Secrets can update.
- Public IP hien tai cua ha tang.
