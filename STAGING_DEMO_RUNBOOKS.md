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
```

Kiem tra Web:

```bash
ssh -i "$KEY" ec2-user@"$WEB"
docker ps --format 'table {{.Names}}\t{{.Status}}'
curl -i http://127.0.0.1:18081/health
curl -i http://127.0.0.1:18081/api/health
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

## 7. Kich ban WebEndpointDown

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

## 8. Kich ban DockerContainerDown cho Payment API

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

## 9. Kich ban PostgreSQLDown

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

## 10. Kich ban RedisDown

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

## 11. Kich ban feedback va vong doi incident

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

## 12. Cac service khong nen dung trong demo

Khong dung cac container sau neu van muon Telegram va feedback hoat dong:

```text
ai-agent-staging
celery-worker-staging
redis-staging
```

Day la ha tang nhan webhook, xu ly task va luu context incident.

## 13. Final health check

Khoi phuc cac service demo:

```bash
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
curl -i http://127.0.0.1:18081/health
curl -i http://127.0.0.1:18081/api/health
```

Kiem tra Prometheus tren Monitor:

```bash
curl -s 'http://127.0.0.1:9090/api/v1/targets?state=active' \
  | jq '.data.activeTargets[] | select(.health!="up")'

curl -s http://127.0.0.1:9090/api/v1/alerts | jq '.data.alerts'
```

Staging sach khi cac health endpoint tra ve `HTTP 200`, khong co Prometheus target `down` va khong con alert `firing`.

## 14. Troubleshooting nhanh

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
