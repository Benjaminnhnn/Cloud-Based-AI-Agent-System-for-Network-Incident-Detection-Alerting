# Staging Demo Runbooks

Tai lieu nay mo ta toan bo quy trinh deploy, khoi dong, cau hinh Telegram webhook va chay demo tren AWS Staging.

## 1. Thong tin he thong

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
AI Agent: http://127.0.0.1:18000/health
Backend:  http://127.0.0.1:18080/api/health
Frontend: http://127.0.0.1:18081/health
```

## 2. Deploy Staging

Push code len nhanh `develop` de GitHub Actions build image va deploy Staging:

```bash
git checkout develop
git pull --rebase origin develop
git push origin develop
```

Neu co thay doi trong Prometheus alert rules, chay lai monitoring playbook sau khi push:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/configure-monitoring-stack.yml
```

GitHub Actions se copy `release/` va `automation/` len EC2, sau do chay:

```bash
./automation/app-release-deploy.sh staging staging-<commit-sha> <monitor|core|web>
```

## 3. Khoi dong lai cac role bang tay

Chi dung khi can khoi dong lai toan bo role ma khong muon push commit moi.

Monitor:

```bash
ssh -i "$KEY" ec2-user@"$MONITOR"
cd /home/ec2-user/aws-hybrid
TAG=$(cat release/.state/staging.tag)
./automation/app-release-deploy.sh staging "$TAG" monitor
```

Core:

```bash
ssh -i "$KEY" ec2-user@"$CORE"
cd /home/ec2-user/aws-hybrid
TAG=$(cat release/.state/staging.tag)
./automation/app-release-deploy.sh staging "$TAG" core
```

Web:

```bash
ssh -i "$KEY" ec2-user@"$WEB"
cd /home/ec2-user/aws-hybrid
TAG=$(cat release/.state/staging.tag)
./automation/app-release-deploy.sh staging "$TAG" web
```

## 4. Preflight truoc demo

Kiem tra Monitor:

```bash
ssh -i "$KEY" ec2-user@"$MONITOR"
cd /home/ec2-user/aws-hybrid
docker ps --format 'table {{.Names}}\t{{.Status}}'
curl -i http://127.0.0.1:18000/health
curl -s http://127.0.0.1:9090/api/v1/alerts | jq '.data.alerts'
curl -s 'http://127.0.0.1:9090/api/v1/targets?state=active' \
  | jq '.data.activeTargets[] | select(.health!="up")'
```

Kiem tra Core:

```bash
ssh -i "$KEY" ec2-user@"$CORE"
docker ps --format 'table {{.Names}}\t{{.Status}}'
curl -i http://127.0.0.1:18080/api/health
curl -i http://127.0.0.1:18080/api/ready
```

Kiem tra Web:

```bash
ssh -i "$KEY" ec2-user@"$WEB"
docker ps --format 'table {{.Names}}\t{{.Status}}'
curl -i http://127.0.0.1:18081/health
curl -i http://127.0.0.1:18081/api/health
curl -i http://127.0.0.1:18081/api/ready
```

Ket qua mong doi:

- Cac container Staging dang `Up` hoac `healthy`.
- Ba health endpoint tra ve `HTTP 200`.
- Prometheus khong co target `down`.
- Prometheus khong co alert `firing` tu lan demo truoc.

## 5. Cau hinh Telegram webhook qua ngrok

Telegram can public HTTPS URL, trong khi AI Agent dang chay tren Monitor EC2 tai port `18000`.

Luong ket noi:

```text
Telegram
  -> ngrok public HTTPS URL
  -> localhost:18000 tren may local
  -> SSH tunnel
  -> 127.0.0.1:18000 tren Monitor EC2
  -> ai-agent-staging /telegram/webhook
```

### Terminal 1: SSH tunnel

Giu terminal nay chay trong suot buoi demo:

```bash
ssh -i "$KEY" -N -L 18000:127.0.0.1:18000 ec2-user@"$MONITOR"
```

Neu bao `Address already in use`, da co tunnel hoac process khac dang dung port. Kiem tra:

```bash
curl -i http://127.0.0.1:18000/health
ss -ltnp | grep ':18000'
```

Neu health tra ve `HTTP 200`, khong can mo tunnel thu hai.

### Terminal 2: ngrok

Giu terminal nay chay trong suot buoi demo:

```bash
curl -i http://127.0.0.1:18000/health
ngrok http 18000
```

Lay HTTPS URL tu ngrok, vi du:

```text
https://example-name.ngrok-free.dev
```

### Cau hinh webhook mot lan

Lenh `setWebhook` chi can chay khi URL ngrok hoac Telegram token thay doi:

```bash
export TELEGRAM_TOKEN='<telegram-bot-token>'
export NGROK_URL='https://example-name.ngrok-free.dev'

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook" \
  -d "url=${NGROK_URL}/telegram/webhook" | jq

curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getWebhookInfo" | jq
```

Ket qua mong doi:

- `url` ket thuc bang `/telegram/webhook`.
- Ngrok hien thi `POST /telegram/webhook 200 OK` khi gui tin nhan moi.
- `last_error_message` co the la loi cu; chi can request moi tra ve `200 OK`.

Cap nhat GitHub Secret `AI_AGENT_PUBLIC_URL` bang URL ngrok goc, khong them `/telegram/webhook`.

## 6. Theo doi alert trong luc demo

Tren Monitor:

```bash
watch -n 5 "curl -s 'http://127.0.0.1:9090/api/v1/alerts' | jq '.data.alerts[] | {state, alertname:.labels.alertname, component:.labels.component, instance:.labels.instance, activeAt}'"
```

Rule `DockerContainerDown` phat hien container da dung sau khoang `60-90 giay`. Moi alert co Incident ID rieng.

## 7. Kich ban cau hinh sai PAYMENT_API_UPSTREAM

Kich ban nay khong dung container. Frontend va Payment API van chay, nhung Nginx proxy sai upstream.

### Gay loi

Tren Web:

```bash
cd /home/ec2-user/aws-hybrid
cp release/.env.staging /tmp/.env.staging.demo-backup
sed -i 's|^PAYMENT_API_UPSTREAM=.*|PAYMENT_API_UPSTREAM=http://127.0.0.1:9|' release/.env.staging

docker-compose -p aws-hybrid-staging-web \
  --env-file release/.env.staging \
  -f release/docker-compose.staging.yml \
  up -d --force-recreate frontend-web

curl -i http://127.0.0.1:18081/health
curl -i http://127.0.0.1:18081/api/ready
```

Ket qua mong doi:

- `/health` van tra `200`, chung minh frontend container dang chay.
- `/api/ready` tra `502`.
- Telegram nhan `FrontendAPIProxyDown`.
- Telegram khong nhan `PaymentAPIEndpointDown`, vi backend truc tiep van khoe.
- Agent hien thi upstream mong doi tu inventory va dua lenh sua `PAYMENT_API_UPSTREAM` cu the.
- Release script khong tu suy ra upstream dung; neu `.env.staging` van sai thi redeploy van tiep tuc loi.

Feedback mau:

```text
/feedback <incident_id> Frontend health van 200 nhung /api/ready tra 502. Sua PAYMENT_API_UPSTREAM ve http://10.10.1.119:18080, sau do redeploy web va kiem tra lai readiness.
```

### Khoi phuc

```bash
cp /tmp/.env.staging.demo-backup release/.env.staging
grep '^PAYMENT_API_UPSTREAM=' release/.env.staging

# Neu backup khong dung, sua truc tiep theo core private IP hien tai:
sed -i 's|^PAYMENT_API_UPSTREAM=.*|PAYMENT_API_UPSTREAM=http://10.10.1.119:18080|' release/.env.staging

TAG=$(cat release/.state/staging.tag)
./automation/app-release-deploy.sh staging "$TAG" web

curl -i http://127.0.0.1:18081/api/ready
```

## 8. Kich ban cau hinh sai DATABASE_URL

Kich ban nay giu PostgreSQL va Payment API container dang chay, nhung Payment API khong ket noi duoc database.

### Gay loi

Tren Core:

```bash
cd /home/ec2-user/aws-hybrid
cp release/docker-compose.staging.yml /tmp/docker-compose.staging.yml.demo-backup
sed -i 's|postgresql://aiops_user:aiops_pass@postgres:5432/aiops_db|postgresql://aiops_user:wrong_password@postgres:5432/aiops_db|' release/docker-compose.staging.yml

docker-compose -p aws-hybrid-staging-core \
  --env-file release/.env.staging \
  -f release/docker-compose.staging.yml \
  up -d --force-recreate payment-api

docker ps --filter name=payment-api-staging
curl -i http://127.0.0.1:18080/api/health
curl -i http://127.0.0.1:18080/api/ready
```

Ket qua mong doi:

- `/api/health` van tra `200`, chung minh API process dang song.
- `/api/ready` tra `503`, chung minh dependency database bi loi.
- Telegram nhan `PaymentAPIEndpointDown`.
- Telegram co the nhan them `FrontendAPIProxyDown` vi frontend proxy toi API khong ready.
- Agent uu tien kiem tra dependency, logs, endpoint va network thay vi chi `docker start`.

Feedback mau:

```text
/feedback <incident_id> API process van healthy nhung readiness tra 503. Kiem tra DATABASE_URL va ket noi PostgreSQL truoc khi restart container.
```

### Khoi phuc

```bash
cp /tmp/docker-compose.staging.yml.demo-backup release/docker-compose.staging.yml

docker-compose -p aws-hybrid-staging-core \
  --env-file release/.env.staging \
  -f release/docker-compose.staging.yml \
  up -d --force-recreate payment-api

curl -i http://127.0.0.1:18080/api/ready
```

## 9. Kich ban CPU cao do process bat thuong

Kich ban nay khong sua Docker. No tao mot process gay tai tren host de Prometheus phat hien `HighCPUUsage` hoac `CriticalCPUUsage`.

### Gay loi

Tren Core:

```bash
rm -f /tmp/aiops-cpu-demo.pids
for i in $(seq 1 "$(nproc)"); do
  yes > /dev/null &
  echo $! >> /tmp/aiops-cpu-demo.pids
done

top -b -n 1 | head -20
```

Ket qua mong doi sau khoang `1-2 phut`:

- Telegram nhan `HighCPUUsage` hoac `CriticalCPUUsage` cho `bank-core-01`.
- Agent de xuat `top`, `ps`, `docker stats` va tim process gay tai.
- Khong co container nao bi stop.

Feedback mau:

```text
/feedback <incident_id> Tim process dung CPU cao bang top va ps, xac nhan day co phai workload hop le truoc khi kill process.
```

### Khoi phuc

```bash
xargs -r kill < /tmp/aiops-cpu-demo.pids
rm -f /tmp/aiops-cpu-demo.pids
top -b -n 1 | head -20
```

## 10. Kich ban phat hien loi tu log

Kich ban nay khong dung service. `log-watcher-staging` phat hien loi ung dung tu noi dung log.

### Gay loi

Tren Monitor:

```bash
printf '%s\n' \
  'CRITICAL payment gateway timeout: upstream returned 504 after 30 seconds' \
  >> /tmp/aiops-test-syslog.log

docker logs --tail=100 log-watcher-staging
docker logs --tail=100 celery-worker-staging
```

Ket qua mong doi:

- Telegram nhan `LogFileErrorDetected`.
- Agent phan tich noi dung log va de xuat huong kiem tra.
- Phu hop de demo phat hien loi ma metric/container chua thay doi.

Feedback mau:

```text
/feedback <incident_id> Kiem tra latency va error rate cua payment gateway, doi chieu timeout trong log truoc khi retry request.
```

Luu y: log alert hien khong co resolved event tu Alertmanager, nen dung de demo phat hien va feedback.

## 11. Kich ban WebEndpointDown

### Gay loi

Tren Web:

```bash
docker stop frontend-web-staging
curl -i http://127.0.0.1:18081/health
```

Telegram mong doi:

- Nhan `WebEndpointDown` cho `frontend-web-staging`.
- Co the nhan them `DockerContainerDown` vi cung mot container da dung.
- Hai alert la hai tin hieu giam sat khac nhau va co Incident ID rieng.

### Feedback

Gui tren Telegram:

```text
/feedback <incident_id> Kiem tra docker ps -a va docker logs. Neu container dung thi start lai va kiem tra /health.
```

### Khoi phuc

```bash
docker start frontend-web-staging
curl -i http://127.0.0.1:18081/health
curl -i http://127.0.0.1:18081/api/health
```

## 12. Kich ban DockerContainerDown cho Payment API

### Gay loi

Tren Core:

```bash
docker stop payment-api-staging
docker ps -a --filter name=payment-api-staging
```

Telegram mong doi:

- Nhan `DockerContainerDown`.
- Component la `payment-api-staging`.
- Agent de xuat kiem tra Docker va redeploy role `core`.

Kiem tra Prometheus:

```bash
curl -sG http://127.0.0.1:9090/api/v1/query \
  --data-urlencode 'query=time() - container_last_seen{name=~".*payment-api-staging",instance="bank-core-01"}' | jq
```

### Khoi phuc

```bash
docker start payment-api-staging
curl -i http://127.0.0.1:18080/api/health
```

## 13. Kich ban PostgreSQLDown

### Gay loi

Tren Core:

```bash
docker stop postgres-staging
```

Telegram mong doi:

- Nhan `PostgreSQLDown`.
- Co the nhan them `DockerContainerDown` cho `postgres-staging`.
- Agent de xuat `pg_isready`, kiem tra logs va redeploy role `core`.

### Feedback

```text
/feedback <incident_id> Kiem tra logs postgres-staging va pg_isready. Neu database dung thi start lai, khong xoa volume du lieu.
```

### Khoi phuc

```bash
docker start postgres-staging
docker exec postgres-staging pg_isready -U aiops_user -d aiops_db
curl -i http://127.0.0.1:18080/api/health
```

## 14. Kich ban RedisDown

Dung `redis-cache-staging`, khong dung `redis-staging`. `redis-staging` la broker cua AI Agent va Celery.

### Gay loi

Tren Monitor:

```bash
docker stop redis-cache-staging
```

Telegram mong doi:

- Nhan `RedisDown`.
- Co the nhan them `DockerContainerDown` cho `redis-cache-staging`.
- AI Agent va Telegram van hoat dong vi broker `redis-staging` khong bi dung.

### Feedback

```text
/feedback <incident_id> Kiem tra redis-cli ping va logs redis-cache-staging. Neu container dung thi start lai, khong xoa volume.
```

### Khoi phuc

```bash
docker start redis-cache-staging
docker exec redis-cache-staging redis-cli ping
```

## 15. Kich ban feedback va vong doi incident

### Feedback hop le khi incident con loi

```text
/feedback <incident_id> Kiem tra docker ps -a va docker logs. Neu container dung thi start lai va kiem tra health endpoint.
```

Agent mong doi tra ve `accepted` hoac `revised`.

### Feedback nguy hiem

```text
/feedback <incident_id> Xoa Docker volume roi deploy lai
```

Agent mong doi tra ve:

```text
Ket qua: rejected
Luu vao RAG: no
```

### Kiem tra context Redis

Khi incident van con loi, context phai ton tai ke ca sau task verify:

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

Incident da resolved se khong nhan feedback moi. Moi lan service tai phat phai tao Incident ID moi.

## 16. Cac service khong nen dung trong demo

Khong dung cac container sau neu van muon Telegram va feedback hoat dong:

```text
ai-agent-staging
celery-worker-staging
redis-staging
```

Day la ha tang nhan webhook, xu ly task va luu context incident.

## 17. Final health check

Khoi phuc cac service demo:

```bash
# Neu da chay demo cau hinh sai
test -f /tmp/.env.staging.demo-backup && cp /tmp/.env.staging.demo-backup release/.env.staging
test -f /tmp/docker-compose.staging.yml.demo-backup && cp /tmp/docker-compose.staging.yml.demo-backup release/docker-compose.staging.yml

# Web
docker start frontend-web-staging

# Core
docker start payment-api-staging
docker start postgres-staging

# Monitor
docker start redis-cache-staging
```

Kiem tra lai tren tung host:

```bash
curl -i http://127.0.0.1:18000/health
curl -i http://127.0.0.1:18080/api/health
curl -i http://127.0.0.1:18080/api/ready
curl -i http://127.0.0.1:18081/health
curl -i http://127.0.0.1:18081/api/health
curl -i http://127.0.0.1:18081/api/ready
```

Kiem tra Prometheus tren Monitor:

```bash
curl -s 'http://127.0.0.1:9090/api/v1/targets?state=active' \
  | jq '.data.activeTargets[] | select(.health!="up")'

curl -s http://127.0.0.1:9090/api/v1/alerts | jq '.data.alerts'
```

Staging sach khi cac health endpoint tra ve `HTTP 200`, khong co Prometheus target `down` va khong con alert `firing`.

## 18. Troubleshooting nhanh

Webhook tra ve `503 Service Unavailable`:

```bash
curl -i http://127.0.0.1:18000/health
curl -i "$NGROK_URL/health"
```

SSH tunnel bao `Address already in use`:

```bash
ss -ltnp | grep ':18000'
curl -i http://127.0.0.1:18000/health
```

Khong thay context incident:

```bash
docker exec redis-staging redis-cli GET "incident:<incident_id>"
```

Phai thay `<incident_id>` bang ID that, vi du:

```bash
docker exec redis-staging redis-cli GET "incident:65d76f40"
```

Khong thay `DockerContainerDown`:

```bash
curl -sG http://127.0.0.1:9090/api/v1/query \
  --data-urlencode 'query=time() - container_last_seen{name=~".*payment-api-staging",instance="bank-core-01"}' | jq

docker exec prometheus grep -n "payment-api-staging" /etc/prometheus/alert_rules.yml
```

Neu Prometheus dang dung rule cu, chay lai:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/configure-monitoring-stack.yml
```
