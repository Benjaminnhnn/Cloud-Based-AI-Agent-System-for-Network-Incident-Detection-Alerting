# Staging Demo Runbooks

Tai lieu nay chi bao gom 4 kich ban demo chinh. Moi kich ban co mot nguyen nhan goc, mot alert chinh va mot cach xu ly khac nhau.

## 1. Thong tin he thong

Chay tren WSL local:

```bash
export KEY=/home/qtienle/.ssh/aws-hybrid
export MONITOR=13.213.161.83
export WEB=13.250.87.160
export CORE=3.1.112.30
```

| Role | Public IP | Private identity | Dich vu chinh |
| --- | --- | --- | --- |
| Monitor | `13.213.161.83` | `monitor-ai-01` | Prometheus, Alertmanager, AI Agent, Celery, Redis |
| Web | `13.250.87.160` | `bank-web-01` | `frontend-web-staging` |
| Core | `3.1.112.30` | `bank-core-01` | `payment-api-staging`, `postgres-staging` |

Health endpoints:

```text
AI Agent:         http://127.0.0.1:18000/health
Payment API live: http://127.0.0.1:18080/api/health
Payment API ready:http://127.0.0.1:18080/api/ready
Frontend live:    http://127.0.0.1:18081/health
Frontend ready:   http://127.0.0.1:18081/api/ready
```

## 2. Deploy va nap alert rules

Push code len nhanh `develop`:

```bash
git checkout develop
git pull --rebase origin develop
git push origin develop
```

Neu co thay doi `ansible/config/alert_rules.yml`, chay lai monitoring playbook tu may local:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/configure-monitoring-stack.yml
```

Xac nhan Prometheus da nap correlation moi:

```bash
ssh -i "$KEY" ec2-user@"$MONITOR"

curl -s http://127.0.0.1:9090/api/v1/rules \
  | jq '.data.groups[].rules[] | select(.name=="WebEndpointDown" or .name=="FrontendAPIProxyDown") | {name,query}'
```

Quy tac mong doi:

```text
Container frontend dung
  -> DockerContainerDown

Container frontend con chay, /health loi
  -> WebEndpointDown

Container frontend con chay, /health OK, /api/ready loi, Payment API truc tiep OK
  -> FrontendAPIProxyDown
```

## 3. Telegram webhook qua ngrok

Telegram can public HTTPS URL, trong khi AI Agent chay tren Monitor EC2 tai port `18000`.

### Terminal 1: SSH tunnel

```bash
ssh -i "$KEY" -N -L 18000:127.0.0.1:18000 ec2-user@"$MONITOR"
```

Neu bao `Address already in use`, kiem tra tunnel cu:

```bash
curl -i http://127.0.0.1:18000/health
```

Neu tra ve `HTTP 200`, khong mo them tunnel.

### Terminal 2: ngrok

```bash
ngrok http 18000
```

### Cau hinh webhook

```bash
export TELEGRAM_TOKEN='<telegram-bot-token>'
export NGROK_URL='https://example-name.ngrok-free.dev'

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook" \
  -d "url=${NGROK_URL}/telegram/webhook" | jq

curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getWebhookInfo" | jq
```

Ket qua mong doi:

- `url` ket thuc bang `/telegram/webhook`.
- Request moi tren ngrok tra ve `POST /telegram/webhook 200 OK`.

## 4. Preflight truoc moi kich ban

Khong chay hai kich ban cung luc. Sau moi kich ban, cho alert resolved va query tro ve `[]`.

Tren Monitor:

```bash
ssh -i "$KEY" ec2-user@"$MONITOR"
cd /home/ec2-user/aws-hybrid

docker ps --format 'table {{.Names}}\t{{.Status}}'
curl -i http://127.0.0.1:18000/health
curl -s http://127.0.0.1:9090/api/v1/alerts | jq '.data.alerts'
```

Tren Core:

```bash
ssh -i "$KEY" ec2-user@"$CORE"
cd /home/ec2-user/aws-hybrid

docker ps --format 'table {{.Names}}\t{{.Status}}'
curl -i http://127.0.0.1:18080/api/health
curl -i http://127.0.0.1:18080/api/ready
```

Tren Web:

```bash
ssh -i "$KEY" ec2-user@"$WEB"
cd /home/ec2-user/aws-hybrid

docker ps --format 'table {{.Names}}\t{{.Status}}'
curl -i http://127.0.0.1:18081/health
curl -i http://127.0.0.1:18081/api/ready
```

Theo doi alert tren Monitor:

```bash
watch -n 5 "curl -s 'http://127.0.0.1:9090/api/v1/alerts' | jq '.data.alerts[] | {state, alertname:.labels.alertname, component:.labels.component, instance:.labels.instance, activeAt}'"
```

## 5. Tong quan 4 kich ban

| Kich ban | Cach gay loi | Alert chinh | Cach xu ly |
| --- | --- | --- | --- |
| 1. Container frontend dung | `docker stop` | `DockerContainerDown` | Kiem tra container, logs, sau do start lai |
| 2. Frontend proxy sai upstream | Sua `PAYMENT_API_UPSTREAM` | `FrontendAPIProxyDown` | Sua config va redeploy role web |
| 3. Payment API sai database credential | Sua `DATABASE_URL` | `PaymentAPIEndpointDown` | Sua dependency config va recreate API |
| 4. Host CPU cao | Tao process `yes` | `HighCPUUsage` hoac `CriticalCPUUsage` | Tim PID gay tai va dung process |

## 6. Kich ban 1: DockerContainerDown

Muc tieu: demo loi container lifecycle. Lenh `docker stop frontend-web-staging` chi nen tao `DockerContainerDown`.

### Gay loi

Tren Web:

```bash
docker stop frontend-web-staging
docker ps -a --filter name=frontend-web-staging
```

Cho khoang `2-3 phut` vi rule `DockerContainerDown` co `for: 2m`.

Ket qua mong doi:

- Telegram nhan `DockerContainerDown`.
- Component la `frontend-web-staging`.
- Khong nhan `WebEndpointDown`.
- Khong nhan `FrontendAPIProxyDown`.

Feedback mau:

```text
/feedback <incident_id> Kiem tra docker ps -a va docker logs frontend-web-staging. Neu container chi bi stop thi start lai, sau do kiem tra /health va /api/ready.
```

### Khoi phuc

```bash
docker logs --tail=100 frontend-web-staging
docker start frontend-web-staging
curl -i http://127.0.0.1:18081/health
curl -i http://127.0.0.1:18081/api/ready
```

## 7. Kich ban 2: FrontendAPIProxyDown

Muc tieu: demo loi cau hinh Nginx proxy. Frontend va Payment API van song, nhung frontend tro sai upstream.

### Dieu kien truoc khi gay loi

Tren Core:

```bash
curl -i http://127.0.0.1:18080/api/ready
```

Ket qua phai la `HTTP 200`.

### Gay loi

Tren Web:

```bash
cd /home/ec2-user/aws-hybrid
test -f /tmp/.env.staging.demo-backup || cp release/.env.staging /tmp/.env.staging.demo-backup

sed -i 's|^PAYMENT_API_UPSTREAM=.*|PAYMENT_API_UPSTREAM=http://127.0.0.1:9|' release/.env.staging

docker-compose -p aws-hybrid-staging-web \
  --env-file release/.env.staging \
  -f release/docker-compose.staging.yml \
  up -d --force-recreate frontend-web

curl -i http://127.0.0.1:18081/health
curl -i http://127.0.0.1:18081/api/ready
```

Ket qua mong doi:

- `/health` tra `200`.
- `/api/ready` tra `502`.
- Telegram chi nhan `FrontendAPIProxyDown`.
- Khong nhan `WebEndpointDown`, `PaymentAPIEndpointDown` hoac `DockerContainerDown`.

Feedback mau:

```text
/feedback <incident_id> Frontend health van 200 nhung /api/ready tra 502. Sua PAYMENT_API_UPSTREAM ve http://10.10.1.119:18080, redeploy web va kiem tra lai readiness.
```

### Khoi phuc

```bash
cp /tmp/.env.staging.demo-backup release/.env.staging
sed -i 's|^PAYMENT_API_UPSTREAM=.*|PAYMENT_API_UPSTREAM=http://10.10.1.119:18080|' release/.env.staging

TAG=$(cat release/.state/staging.tag)
./automation/app-release-deploy.sh staging "$TAG" web

curl -i http://127.0.0.1:18081/health
curl -i http://127.0.0.1:18081/api/ready
rm -f /tmp/.env.staging.demo-backup
```

## 8. Kich ban 3: PaymentAPIEndpointDown

Muc tieu: demo loi dependency database. Payment API process van song nhung readiness that bai vi credential sai.

### Dieu kien truoc khi gay loi

Tren Core:

```bash
docker exec postgres-staging pg_isready -U aiops_user -d aiops_db
curl -i http://127.0.0.1:18080/api/health
curl -i http://127.0.0.1:18080/api/ready
```

Tat ca phai healthy truoc khi bat dau.

### Gay loi

Tren Core:

```bash
cd /home/ec2-user/aws-hybrid
test -f /tmp/docker-compose.staging.yml.demo-backup || cp release/docker-compose.staging.yml /tmp/docker-compose.staging.yml.demo-backup

sed -i 's|postgresql://aiops_user:aiops_pass@postgres:5432/aiops_db|postgresql://aiops_user:wrong_password@postgres:5432/aiops_db|' release/docker-compose.staging.yml

docker-compose -p aws-hybrid-staging-core \
  --env-file release/.env.staging \
  -f release/docker-compose.staging.yml \
  up -d --force-recreate payment-api

curl -i http://127.0.0.1:18080/api/health
curl -i http://127.0.0.1:18080/api/ready
```

Ket qua mong doi:

- `/api/health` tra `200`.
- `/api/ready` tra `503`.
- PostgreSQL van healthy.
- Telegram chi nhan `PaymentAPIEndpointDown`.
- Khong nhan `FrontendAPIProxyDown`, `PostgreSQLDown` hoac `DockerContainerDown`.

Feedback mau:

```text
/feedback <incident_id> Payment API process van song nhung /api/ready tra 503, trong khi postgres-staging van healthy. Kiem tra docker logs --tail=100 payment-api-staging de xac nhan loi authentication, kiem tra DATABASE_URL trong container va release/docker-compose.staging.yml. Khoi phuc dung credential postgresql://aiops_user:aiops_pass@postgres:5432/aiops_db, sau do force-recreate payment-api-staging. Cuoi cung kiem tra lai /api/health, /api/ready va frontend /api/ready; khong restart PostgreSQL hoac xoa volume du lieu.
```

Checklist xu ly mong doi tu Agent:

```bash
docker logs --tail=100 payment-api-staging
docker inspect payment-api-staging --format '{{range .Config.Env}}{{println .}}{{end}}' | grep DATABASE_URL
docker exec postgres-staging pg_isready -U aiops_user -d aiops_db

# Sua DATABASE_URL trong release/docker-compose.staging.yml

docker-compose -p aws-hybrid-staging-core \
  --env-file release/.env.staging \
  -f release/docker-compose.staging.yml \
  up -d --force-recreate payment-api

curl -i http://127.0.0.1:18080/api/health
curl -i http://127.0.0.1:18080/api/ready
```

### Khoi phuc

```bash
cp /tmp/docker-compose.staging.yml.demo-backup release/docker-compose.staging.yml

docker-compose -p aws-hybrid-staging-core \
  --env-file release/.env.staging \
  -f release/docker-compose.staging.yml \
  up -d --force-recreate payment-api

curl -i http://127.0.0.1:18080/api/health
curl -i http://127.0.0.1:18080/api/ready
rm -f /tmp/docker-compose.staging.yml.demo-backup
```

## 9. Kich ban 4: CriticalCPUUsage

Muc tieu: demo loi tai nguyen host, khong dung container va khong sua config.

### Gay loi

Tren Core:

```bash
rm -f /tmp/aiops-cpu-demo.pids
for i in $(seq 1 "$(nproc)"); do
  yes > /dev/null &
  echo $! >> /tmp/aiops-cpu-demo.pids
done

top -b -n 1 | head -20
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head
```

Ket qua mong doi sau khoang `1-2 phut`:

- Telegram nhan `HighCPUUsage` hoac `CriticalCPUUsage` cho `bank-core-01`.
- Agent de xuat `top`, `ps` va `docker stats`.
- Telegram khong hien runbook Nginx, Redis hoac runbook khong lien quan.
- Khong co container nao bi stop.

Feedback mau:

```text
/feedback <incident_id> Tim PID dung CPU cao bang top va ps, xac nhan day la process bat thuong, sau do dung dung PID va kiem tra CPU tro lai binh thuong.
```

### Khoi phuc

```bash
xargs -r kill < /tmp/aiops-cpu-demo.pids
rm -f /tmp/aiops-cpu-demo.pids

top -b -n 1 | head -20
```

## 10. Kiem tra feedback va RAG

Feedback chi duoc luu vao RAG neu ket qua review la `accepted` hoac `revised`.

Tren Monitor:

```bash
docker exec celery-worker-staging python tools/inspect_rag_db.py

docker exec celery-worker-staging python tools/inspect_rag_db.py \
  --collection incident_memory \
  --source admin_feedback
```

Kiem tra context Redis khi incident van con loi:

```bash
docker exec redis-staging redis-cli GET "incident:<incident_id>"
docker exec redis-staging redis-cli TTL "incident:<incident_id>"
```

Sau khi incident resolved, context se bi xoa:

```bash
docker exec redis-staging redis-cli GET "incident:<incident_id>"
```

Ket qua mong doi:

```text
(nil)
```

## 11. Cac service khong duoc dung trong demo

Khong stop cac container sau neu van muon Telegram va feedback hoat dong:

```text
ai-agent-staging
celery-worker-staging
redis-staging
```

## 12. Final health check

Tren Web:

```bash
docker start frontend-web-staging
curl -i http://127.0.0.1:18081/health
curl -i http://127.0.0.1:18081/api/ready
```

Tren Core:

```bash
docker start postgres-staging
docker start payment-api-staging
docker exec postgres-staging pg_isready -U aiops_user -d aiops_db
curl -i http://127.0.0.1:18080/api/health
curl -i http://127.0.0.1:18080/api/ready
```

Tren Monitor:

```bash
curl -s http://127.0.0.1:9090/api/v1/alerts | jq '.data.alerts'
```

Ket qua cuoi cung:

```text
[]
```

## 13. Troubleshooting nhanh

### Docker Compose plugin khong co

Neu `docker compose` bao `unknown shorthand flag: p`, dung binary cu:

```bash
docker-compose --version
```

### Alert rules chua cap nhat

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/configure-monitoring-stack.yml
```

### Telegram khong nhan tin

```bash
docker logs --tail=200 ai-agent-staging
docker logs --tail=200 celery-worker-staging
curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getWebhookInfo" | jq
```

### Alert cu van con firing

```bash
curl -s http://127.0.0.1:9090/api/v1/alerts \
  | jq '.data.alerts[] | {state, labels, activeAt}'
```

Khoi phuc nguyen nhan goc, cho Prometheus scrape lai va chi chay kich ban tiep theo khi query tra ve `[]`.
