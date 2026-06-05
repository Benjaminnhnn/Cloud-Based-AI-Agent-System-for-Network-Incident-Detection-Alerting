# GitHub Webhook Tool Registry Runbook Demo

Tai lieu nay mo ta luong **GitHub Webhook Auto-Discovery -> Tool Registry -> Runbook Draft Review** va cach thuc hien kich ban kiem thu khi them cac cong cu CI nhu **Trivy**, **terraform validate**, va **ansible-lint**.

## Muc tieu

Tinh nang nay dung de chung minh Agent co the tu phat hien thay doi trong CI workflow, tu do tao de xuat runbook nhung khong tu y ghi de runbook dang dung.

Luong ky vong:

```text
Developer cap nhat .github/workflows/ci.yml
-> GitHub gui webhook push/pull_request den Agent
-> Agent doc changed files/diff tu GitHub
-> Agent phat hien cong cu CI moi
-> Agent dang ky revision vao Tool Registry
-> Celery tao runbook draft
-> Telegram gui admin nut Duyet / Tu choi
-> Admin bam Duyet hoac Tu choi
-> Callback goi /telegram/webhook
-> Neu Duyet: publish runbook version moi
-> Khong ghi de runbook dang dung
```

## Thanh phan lien quan

### GitHub Webhook

GitHub webhook duoc cau hinh tro toi Agent:

```text
https://aiops.viettien.fun/github/webhook
```

Webhook nhan event:

```text
push
pull_request
```

Khi co commit moi hoac pull request, GitHub gui payload den endpoint nay.

### Public Webhook Domain

Domain public dang dung:

```text
https://aiops.viettien.fun
```

Domain nay tro ve EC2 monitor:

```text
18.140.152.176
```

Tren EC2 co Caddy reverse proxy:

```text
https://aiops.viettien.fun
-> Caddy port 443
-> 127.0.0.1:18000
-> ai-agent-staging
```

### GitHub Webhook Secret

Agent dung `GITHUB_WEBHOOK_SECRET` de xac thuc chu ky webhook:

```text
X-Hub-Signature-256
```

Neu chu ky sai, request bi tu choi. Nho vay endpoint co the mo public nhung khong chap nhan webhook gia mao.

Lay secret tren EC2:

```bash
ssh -i /home/hoang_viet/.ssh/aws-hybrid ec2-user@18.140.152.176 \
  'cat /home/ec2-user/aws-hybrid/release/.github_webhook_secret'
```

### Tool Auto-Discovery

Logic phat hien nam trong:

```text
agent_src/core/tool_auto_discovery.py
```

Agent chi phan tich cac file co kha nang chua thay doi ve CI/IaC:

```text
.github/workflows/*.yml
.github/workflows/*.yaml
ansible/**/*.yml
ansible/**/*.yaml
terraform/**/*.tf
Dockerfile
Makefile
```

Hien tai Agent nhan dien cac pattern:

```text
trivy
terraform validate
ansible-lint
```

Neu push khong chua cac pattern nay, webhook van tra ve `202`, nhung Agent se bo qua va khong tao runbook draft.

Vi du:

```text
Push chi sua README.md
-> webhook nhan request
-> khong nam trong file watched
-> ignored
```

```text
Push sua .github/workflows/ci.yml nhung chi them pytest
-> webhook nhan request
-> khong co trivy / terraform validate / ansible-lint
-> ignored
```

```text
Push sua .github/workflows/ci.yml va them trivy
-> webhook nhan request
-> Agent phat hien Trivy
-> dang ky Tool Registry
-> tao runbook draft
```

## Vi sao tao duoc runbook?

Ket qua duoc tao qua 5 buoc:

1. **GitHub webhook kich hoat Agent**

   GitHub gui `push` hoac `pull_request` den:

   ```text
   POST /github/webhook
   ```

2. **Agent lay danh sach file thay doi**

   Voi event `push`, Agent dung GitHub compare API:

   ```text
   /repos/{owner}/{repo}/compare/{before}...{after}
   ```

   Voi event `pull_request`, Agent lay danh sach file cua PR:

   ```text
   /repos/{owner}/{repo}/pulls/{pull_number}/files
   ```

3. **Agent phan tich diff**

   Agent doc `filename` va `patch` de tim cac lenh:

   ```text
   trivy
   terraform validate
   ansible-lint
   ```

4. **Agent tao metadata cho Tool Registry**

   Neu phat hien toolchain CI, Agent tao tool metadata:

   ```json
   {
     "name": "ci_security_iac_quality_gate",
     "risk_level": "read_only",
     "related_services": ["github-actions", "container-image", "terraform", "ansible", "deployment"],
     "runbook_tags": ["ci", "security", "iac", "ansible", "quality-gate"]
   }
   ```

   Revision duoc luu trong:

   ```text
   /app/config/runbook_workflow/tool_registry/ci_security_iac_quality_gate
   ```

5. **Celery tao runbook draft va gui Telegram**

   Sau khi Tool Registry co revision moi, Agent enqueue:

   ```text
   review_tool_change_task
   ```

   Celery worker tao draft va gui Telegram cho admin.

## Ket qua sau khi admin duyet

Neu admin bam **Duyet**, Telegram callback goi:

```text
POST /telegram/webhook
```

Sau do runbook duoc publish thanh version moi:

```text
/app/config/knowledge_base/published/ci-tooling/vYYYYMMDDHHMMSS.md
```

File con tro version hien tai:

```text
/app/config/knowledge_base/published/ci-tooling/current.json
```

Runbook cu khong bi ghi de. Moi lan publish tao mot file version moi.

## Kich ban kiem thu end-to-end

## Cau hinh he thong de chay webhook public

Phan nay mo ta cac cau hinh da thuc hien de GitHub va Telegram co the goi ve Agent bang domain public.

### 1. DNS tren Hostinger

Tao A record cho subdomain:

```text
Type: A
Name: aiops
Value / Points to: 18.140.152.176
TTL: 300 hoac 14400
```

Sau khi DNS propagate, kiem tra:

```bash
getent hosts aiops.viettien.fun
```

Ket qua mong doi:

```text
18.140.152.176 aiops.viettien.fun
```

### 2. AWS Security Group

Security Group cua monitor host:

```text
sg-04875d8000835d38b
aiops-bank-dev-monitor-sg
```

Can mo inbound:

```text
HTTP  80  0.0.0.0/0
HTTPS 443 0.0.0.0/0
```

Port `80` can cho Let's Encrypt HTTP-01 challenge va redirect HTTP sang HTTPS.

Port `443` can cho GitHub webhook va Telegram callback.

### 3. Caddy reverse proxy tren EC2

Caddy duoc dung de cap TLS tu dong va reverse proxy den Agent.

File cau hinh tren EC2:

```text
/home/ec2-user/aws-hybrid/release/caddy/Caddyfile
```

Noi dung:

```caddyfile
aiops.viettien.fun {
  encode gzip

  reverse_proxy 127.0.0.1:18000
}
```

Lenh chay Caddy:

```bash
docker run -d --name ai-agent-webhook-proxy \
  --restart unless-stopped \
  --network host \
  -v /home/ec2-user/aws-hybrid/release/caddy/Caddyfile:/etc/caddy/Caddyfile:ro \
  -v caddy-data:/data \
  -v caddy-config:/config \
  caddy:2-alpine
```

Kiem tra Caddy:

```bash
docker ps | grep ai-agent-webhook-proxy
docker logs ai-agent-webhook-proxy | tail -n 100
curl -sS https://aiops.viettien.fun/health
```

Ket qua SSL thanh cong trong log:

```text
certificate obtained successfully
```

### 4. Bien moi truong cua Agent

File env staging tren EC2:

```text
/home/ec2-user/aws-hybrid/release/.env.staging
```

Can co:

```env
AI_AGENT_PUBLIC_URL=https://aiops.viettien.fun
GITHUB_WEBHOOK_SECRET=<secret-trung-voi-GitHub-webhook>
GITHUB_DISCOVERY_TOKEN=
```

`AI_AGENT_PUBLIC_URL` duoc Agent dung de dang ky Telegram webhook:

```text
https://aiops.viettien.fun/telegram/webhook
```

`GITHUB_WEBHOOK_SECRET` duoc dung de xac thuc webhook GitHub qua header:

```text
X-Hub-Signature-256
```

Neu repo private hoac can tranh rate limit GitHub API, cau hinh:

```env
GITHUB_DISCOVERY_TOKEN=<github-token-readonly>
```

Secret hien tai co the lay tren EC2:

```bash
cat /home/ec2-user/aws-hybrid/release/.github_webhook_secret
```

Hoac tao secret moi:

```bash
openssl rand -hex 32 > /home/ec2-user/aws-hybrid/release/.github_webhook_secret
chmod 600 /home/ec2-user/aws-hybrid/release/.github_webhook_secret
```

Sau khi sua `.env.staging`, restart Agent:

```bash
cd /home/ec2-user/aws-hybrid
GHCR_OWNER=benjaminnhnn IMAGE_TAG=<image-tag> \
  docker-compose -p aws-hybrid-staging-monitor \
  -f release/docker-compose.staging.yml \
  up -d --no-deps ai-agent celery-worker
```

Kiem tra Agent da nhan env:

```bash
docker exec ai-agent-staging sh -lc 'printenv AI_AGENT_PUBLIC_URL'
docker exec ai-agent-staging sh -lc 'test -n "$GITHUB_WEBHOOK_SECRET" && echo secret-set'
```

## Build va deploy image moi

Tinh nang GitHub Webhook Auto-Discovery nam trong source code Agent, nen can build image moi va deploy vao `ai-agent-staging` + `celery-worker-staging`.

### Cach 1: Deploy chinh thuc qua GitHub Actions

Day la cach nen dung cho staging/prod.

1. Commit code:

```bash
git status
git add agent_src/core/main.py \
        agent_src/core/tool_auto_discovery.py \
        agent_src/tests/test_github_tool_auto_discovery.py \
        release/.env.example \
        release/docker-compose.staging.yml \
        release/docker-compose.production.yml \
        GITHUB_WEBHOOK_TOOL_REGISTRY_RUNBOOK_DEMO.md

git commit -m "Add GitHub webhook tool auto-discovery runbook workflow"
git push origin <branch>
```

2. GitHub Actions build image Agent moi.

Workflow staging hien co se build:

```text
ghcr.io/benjaminnhnn/aws-hybrid-ai-agent:staging-<commit-sha>
```

3. CD deploy role `monitor` len EC2.

Sau deploy, kiem tra image dang chay:

```bash
ssh -i /home/hoang_viet/.ssh/aws-hybrid ec2-user@18.140.152.176
docker inspect -f '{{.Config.Image}}' ai-agent-staging
docker inspect -f '{{.Config.Image}}' celery-worker-staging
```

4. Kiem endpoint moi:

```bash
curl -sS -X POST https://aiops.viettien.fun/github/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -d '{"zen":"test"}'
```

Neu `GITHUB_WEBHOOK_SECRET` dang bat, request khong co signature se bi tu choi. Khi test nhanh khong co signature, co the test noi bo hoac dung script tao signature nhu ben duoi.

### Cach 2: Deploy thu cong tren EC2 bang image tag co san

Neu image da ton tai tren GHCR, deploy:

```bash
ssh -i /home/hoang_viet/.ssh/aws-hybrid ec2-user@18.140.152.176

cd /home/ec2-user/aws-hybrid
GHCR_OWNER=benjaminnhnn ./automation/app-release-deploy.sh staging <image-tag> monitor
```

Vi du:

```bash
GHCR_OWNER=benjaminnhnn ./automation/app-release-deploy.sh staging staging-f88baafc937e monitor
```

Script se:

```text
pull image moi
recreate ai-agent-staging, celery-worker-staging, log-watcher, redis exporters
health check /health
rollback neu health check fail
```

### Cach 3: Hotfix nhanh de demo

Cach nay da duoc dung de demo nhanh khi chua co image GHCR moi. Chi nen dung cho staging/demo.

Copy file code len EC2:

```bash
scp -i /home/hoang_viet/.ssh/aws-hybrid \
  agent_src/core/main.py \
  agent_src/core/tool_auto_discovery.py \
  ec2-user@18.140.152.176:/tmp/
```

Patch container dang chay va commit thanh local image:

```bash
ssh -i /home/hoang_viet/.ssh/aws-hybrid ec2-user@18.140.152.176

docker cp /tmp/main.py ai-agent-staging:/app/core/main.py
docker cp /tmp/tool_auto_discovery.py ai-agent-staging:/app/core/tool_auto_discovery.py

docker commit ai-agent-staging \
  ghcr.io/benjaminnhnn/aws-hybrid-ai-agent:tool-autodiscovery-hotfix
```

Recreate API va worker bang image hotfix:

```bash
cd /home/ec2-user/aws-hybrid

GHCR_OWNER=benjaminnhnn IMAGE_TAG=tool-autodiscovery-hotfix \
  docker-compose -p aws-hybrid-staging-monitor \
  -f release/docker-compose.staging.yml \
  up -d --no-deps ai-agent celery-worker
```

Kiem tra:

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep staging
curl -sS http://127.0.0.1:18000/health
```

## Cau hinh GitHub Webhook

Vao GitHub repository:

```text
Settings
-> Webhooks
-> Add webhook
```

Nhap:

```text
Payload URL: https://aiops.viettien.fun/github/webhook
Content type: application/json
Secret: noi dung cua /home/ec2-user/aws-hybrid/release/.github_webhook_secret
SSL verification: Enable SSL verification
```

Chon event:

```text
Pushes
Pull requests
```

Sau khi tao webhook, GitHub gui `ping`. Ket qua dung:

```text
HTTP 202
```

Response body:

```json
{
  "status": "ignored",
  "reason": "unsupported event: ping"
}
```

Day la dung vi Agent chi xu ly `push` va `pull_request`.

## Test webhook bang chu ky HMAC

Neu muon test thu cong dung nhu GitHub, tao signature:

```bash
SECRET=$(ssh -i /home/hoang_viet/.ssh/aws-hybrid ec2-user@18.140.152.176 \
  'cat /home/ec2-user/aws-hybrid/release/.github_webhook_secret')

BODY='{"zen":"domain-test"}'
SIG=$(printf "%s" "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

curl -sS -X POST https://aiops.viettien.fun/github/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -H "X-Hub-Signature-256: sha256=$SIG" \
  -d "$BODY"
```

Ket qua mong doi:

```json
{
  "status": "ignored",
  "reason": "unsupported event: ping"
}
```

## Cau hinh volume de khong mat registry/runbook

`ai-agent-staging` va `celery-worker-staging` phai dung chung volume cho Tool Registry va published runbook.

Trong `release/docker-compose.staging.yml`:

```yaml
ai-agent:
  volumes:
    - runbook-workflow-staging:/app/config/runbook_workflow
    - runbook-published-staging:/app/config/knowledge_base/published

celery-worker:
  volumes:
    - vector-db-staging:/app/vector_db
    - runbook-workflow-staging:/app/config/runbook_workflow
    - runbook-published-staging:/app/config/knowledge_base/published

volumes:
  runbook-workflow-staging:
  runbook-published-staging:
```

Ly do:

```text
API container ghi tool revision vao /app/config/runbook_workflow
Celery worker doc revision de tao draft
Ca hai container phai nhin cung mot thu muc
```

Neu thieu volume chung, API co the register tool thanh cong nhung worker se loi:

```text
No such file or directory: /app/config/runbook_workflow/tool_registry/...
```

### Buoc 1: Kiem tra Agent public

Chay:

```bash
curl -sS https://aiops.viettien.fun/health
```

Ket qua mong doi:

```json
{
  "status": "healthy",
  "queue": "celery-redis",
  "redis": "connected"
}
```

### Buoc 2: Kiem tra GitHub webhook

Vao GitHub:

```text
Repository
-> Settings
-> Webhooks
-> chon webhook https://aiops.viettien.fun/github/webhook
-> Recent Deliveries
```

Khi GitHub gui ping, response dung la:

```json
{
  "status": "ignored",
  "reason": "unsupported event: ping"
}
```

`ping` bi ignored la dung, vi Agent chi xu ly `push` va `pull_request`.

### Buoc 3: Tao thay doi CI

Sua file:

```text
.github/workflows/ci.yml
```

Them cac step:

```yaml
- name: Trivy image scan
  run: trivy image ghcr.io/${{ github.repository }}:${{ github.sha }}

- name: Terraform validate
  run: terraform validate

- name: Ansible lint
  run: ansible-lint ansible/playbooks
```

Commit va push len GitHub.

### Buoc 4: Kiem tra webhook da vao Agent

SSH vao monitor:

```bash
ssh -i /home/hoang_viet/.ssh/aws-hybrid ec2-user@18.140.152.176
```

Xem log Agent:

```bash
docker logs --since 10m ai-agent-staging | grep "github/webhook"
```

Ket qua mong doi:

```text
POST /github/webhook HTTP/1.1" 202 Accepted
```

### Buoc 5: Kiem tra Tool Registry

```bash
curl -sS http://127.0.0.1:18000/api/tools
```

Ket qua mong doi co tool:

```text
ci_security_iac_quality_gate
```

Tool nay phai co thong tin:

```text
discovered_tools: Trivy, terraform validate, ansible-lint
source.changed_files: .github/workflows/ci.yml
```

### Buoc 6: Kiem tra runbook draft

```bash
curl -sS "http://127.0.0.1:18000/api/runbook-drafts"
```

Neu chua duyet, draft se co:

```text
status: pending_approval
runbook_slug: ci-tooling
tool_name: ci_security_iac_quality_gate
```

Neu da bam Duyet tren Telegram, draft se co:

```text
status: published
published_version: vYYYYMMDDHHMMSS
published_path: /app/config/knowledge_base/published/ci-tooling/vYYYYMMDDHHMMSS.md
```

### Buoc 7: Kiem tra Telegram

Telegram admin se nhan thong bao co nut:

```text
Duyet
Tu choi
```

Neu bam **Duyet**, Agent publish runbook.

Neu bam **Tu choi**, draft chuyen sang:

```text
rejected
```

### Buoc 8: Xem runbook da publish

Liet ke file published:

```bash
docker exec ai-agent-staging find /app/config/knowledge_base/published -maxdepth 4 -type f | sort
```

Xem file runbook:

```bash
docker exec ai-agent-staging cat /app/config/knowledge_base/published/ci-tooling/vYYYYMMDDHHMMSS.md
```

Xem current pointer:

```bash
docker exec ai-agent-staging cat /app/config/knowledge_base/published/ci-tooling/current.json
```

## Kich ban da kiem chung thuc te

Lan kiem thu tren AWS staging da co ket qua:

```text
Tool: ci_security_iac_quality_gate
Revision: rev-20260605185651-df365f
Draft: draft-20260605185651-968fc1
Status: published
Published version: v20260605185716
Published by: HoangViet051
```

File da publish:

```text
/app/config/knowledge_base/published/ci-tooling/v20260605185716.md
```

Agent da phat hien tu GitHub webhook:

```text
Trivy
terraform validate
ansible-lint
```

## Cach doc ket qua khi demo

Co the trinh bay ngan gon:

```text
Khi developer cap nhat CI workflow, GitHub webhook gui event den Agent.
Agent xac thuc chu ky webhook, doc diff, phat hien toolchain moi gom Trivy, terraform validate va ansible-lint.
Agent khong tu sua runbook dang dung. No chi tao Tool Registry revision va sinh runbook draft.
Draft duoc gui Telegram cho admin duyet.
Chi khi admin bam Duyet, runbook moi duoc publish thanh version moi.
Runbook dang dung khong bi ghi de.
```

## Luu y ve cong cu khac

Webhook se nhan moi event `push` va `pull_request`, nhung Agent chi tao runbook khi thay cong cu nam trong danh sach pattern hien tai.

Hien tai danh sach pattern la:

```text
trivy
terraform validate
ansible-lint
```

Neu muon phat hien them cong cu khac, can bo sung pattern vao:

```text
agent_src/core/tool_auto_discovery.py
```

Vi du co the them:

```text
checkov
tflint
tfsec
hadolint
gitleaks
semgrep
snyk
helm lint
kubectl diff
```

Sau khi bo sung pattern, luong runbook draft van giu nguyen:

```text
Webhook -> Auto-Discovery -> Tool Registry -> Draft -> Telegram approval -> Publish version moi
```

## Checklist nhanh truoc khi demo

```bash
curl -sS https://aiops.viettien.fun/health
curl -sS https://aiops.viettien.fun/api/tools
curl -sS https://aiops.viettien.fun/api/runbook-drafts
```

Tren AWS:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
docker logs --since 10m ai-agent-staging | grep "github/webhook"
docker logs --since 10m celery-worker-staging | grep "Created runbook draft"
```

Thanh cong khi co:

```text
GitHub webhook response 202
Tool Registry co ci_security_iac_quality_gate
Runbook draft duoc tao
Telegram co nut Duyet / Tu choi
Sau khi Duyet co file published/ci-tooling/v*.md
```
