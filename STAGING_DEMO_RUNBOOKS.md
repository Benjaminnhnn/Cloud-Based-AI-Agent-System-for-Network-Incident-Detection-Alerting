# Staging Demo Runbooks

Ngay kiem thu: 2026-05-30

## Muc tieu

Demo 4 su co tren moi truong staging va chung minh luong phat hien - canh bao - huong dan xu ly - khoi phuc hoat dong dung:

1. `WebEndpointDown`
2. `PostgreSQLDown`
3. `RedisDown`
4. `DockerContainerDown`

## Thong tin host

```bash
KEY=/home/qtienle/.ssh/aws-hybrid
WEB=13.228.171.39
CORE=18.140.170.236
MONITOR=47.131.35.71
```

## Preflight

Chay truoc demo:

```bash
curl -i http://13.228.171.39:18081/api/health
curl -i http://18.140.170.236:18080/api/health
curl -i http://47.131.35.71:18000/health

curl -s 'http://47.131.35.71:9090/api/v1/targets?state=active' \
  | jq '.data.activeTargets[] | select(.health!="up")'
```

Ket qua mong doi:

- Frontend proxy `/api/health`: `200 OK`
- Backend API `/api/health`: `200 OK`
- AI Agent `/health`: `200 OK`
- Prometheus khong co active target `down`

## Kich ban 1: WebEndpointDown

### Gay loi

```bash
ssh -i $KEY ec2-user@$WEB
docker stop frontend-web-staging
exit
```

### Theo doi alert

```bash
ssh -i $KEY ec2-user@$MONITOR
watch -n 5 "curl -s 'http://127.0.0.1:9090/api/v1/alerts' | jq '.data.alerts[] | select(.labels.alertname==\"WebEndpointDown\") | {state, activeAt, labels, annotations}'"
```

### Telegram mong doi

AI Agent gui canh bao `WebEndpointDown` cho `bank-web-01`, chi ra component `frontend-web-staging`, cac nguyen nhan uu tien, lenh kiem tra container/nginx va cach khoi phuc bang `docker start frontend-web-staging` hoac redeploy role `web`.

### Khoi phuc

```bash
ssh -i $KEY ec2-user@$WEB
docker start frontend-web-staging
curl -i http://127.0.0.1:18081/api/health
exit
```

## Kich ban 2: PostgreSQLDown

### Gay loi

```bash
ssh -i $KEY ec2-user@$CORE
docker stop postgres-staging
exit
```

### Theo doi alert

```bash
ssh -i $KEY ec2-user@$MONITOR
watch -n 5 "curl -s 'http://127.0.0.1:9090/api/v1/alerts' | jq '.data.alerts[] | select(.labels.alertname==\"PostgreSQLDown\") | {state, activeAt, labels, annotations}'"
```

### Telegram mong doi

AI Agent gui canh bao `PostgreSQLDown` cho `bank-core-01`, chi ra component `postgres-staging`, `postgres-exporter`, lenh `pg_isready`, lenh kiem tra backend `/api/health`, va cach khoi phuc role `core`.

### Khoi phuc

```bash
ssh -i $KEY ec2-user@$CORE
docker start postgres-staging
docker exec postgres-staging pg_isready -U aiops_user -d aiops_db
curl -i http://127.0.0.1:18080/api/health
exit
```

### Xac nhan

```bash
ssh -i $KEY ec2-user@$MONITOR
curl -sG 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=pg_up{component="postgres-staging"}' | jq '.data.result'
```

Ket qua mong doi: `pg_up = 1`.

## Kich ban 3: RedisDown

Dung `redis-cache-staging`, khong dung `redis-staging` vi `redis-staging` la broker cua AI Agent/Celery.

### Gay loi

```bash
ssh -i $KEY ec2-user@$MONITOR
docker stop redis-cache-staging
```

### Theo doi alert

```bash
watch -n 5 "curl -s 'http://127.0.0.1:9090/api/v1/alerts' | jq '.data.alerts[] | select(.labels.alertname==\"RedisDown\") | {state, activeAt, labels, annotations}'"
```

### Telegram mong doi

AI Agent gui canh bao `RedisDown` cho `monitor-ai-01`, chi ra component `redis-cache-staging`, `redis-exporter`, lenh `redis-cli ping`, endpoint exporter `127.0.0.1:19121/metrics`, va cach khoi phuc role `monitor`.

### Khoi phuc

```bash
docker start redis-cache-staging
docker exec redis-cache-staging redis-cli ping
curl -s http://127.0.0.1:19121/metrics | head
```

### Xac nhan

```bash
curl -sG 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=redis_up{component="redis-cache-staging"}' | jq '.data.result'
```

Ket qua mong doi: `redis_up = 1`.

## Kich ban 4: DockerContainerDown

Rule hien tai theo doi cac container ung dung bat buoc. Dung `payment-api-staging` tren core node de demo `DockerContainerDown`. Khong dung `log-watcher-staging` neu Prometheus rule chua theo doi container nay.

### Gay loi

```bash
ssh -i $KEY ec2-user@$CORE
docker rm -f payment-api-staging
exit
```

### Theo doi alert

```bash
ssh -i $KEY ec2-user@$MONITOR
watch -n 10 "curl -s 'http://127.0.0.1:9090/api/v1/alerts' | jq '.data.alerts[] | select(.labels.alertname==\"DockerContainerDown\" and .labels.component==\"payment-api-staging\") | {state, activeAt, labels, annotations}'"
```

Luu y: rule dung `absent(container_last_seen...)`, nen co the can vai phut de Prometheus danh dau series stale truoc khi alert xuat hien.

### Telegram mong doi

AI Agent gui canh bao `DockerContainerDown` cho `bank-core-01`, chi ra component `payment-api-staging`, role khoi phuc `core`, lenh kiem tra Docker/container/disk, va lenh redeploy bang `./automation/app-release-deploy.sh staging "$TAG" core`.

### Khoi phuc

```bash
ssh -i $KEY ec2-user@$CORE
cd /home/ec2-user/aws-hybrid
TAG=$(cat release/.state/staging.tag)
./automation/app-release-deploy.sh staging "$TAG" core
curl -i http://127.0.0.1:18080/api/health
exit
```

Neu gap `ghcr.io/your-org/... manifest unknown`, chay:

```bash
cd /home/ec2-user/aws-hybrid
TAG=$(cat release/.state/staging.tag)
GHCR_OWNER=benjaminnhnn ./automation/app-release-deploy.sh staging "$TAG" core
```

Nguyen nhan loi nay la deploy script cu uu tien default `your-org` hon `GHCR_OWNER` trong `.env.staging`. Ban sua moi da chinh lai de `.env.staging` duoc ton trong neu shell khong override.

### Xac nhan

```bash
ssh -i $KEY ec2-user@$MONITOR
curl -sG 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=container_last_seen{name=~".*payment-api-staging",instance="bank-core-01"}' | jq '.data.result'

curl -s 'http://127.0.0.1:9090/api/v1/targets?state=active' \
  | jq '.data.activeTargets[] | select(.health!="up")'
```

Ket qua mong doi:

- `container_last_seen` co series cho `payment-api-staging`
- Khong co Prometheus target `down`

## Cac loi vat da gap khi demo

1. Chay `ssh -i $KEY ...` ben trong EC2 bi loi vi bien `$KEY`, `$WEB`, `$CORE`, `$MONITOR` chi duoc set tren may local. Khi dang o EC2, thoat ra local roi moi SSH sang host khac.
2. Thu `docker start postgres-staging` tren monitor node bi loi vi PostgreSQL nam tren core node.
3. Dung `log-watcher-staging` cho `DockerContainerDown` khong co alert vi rule hien tai chua theo doi container nay.
4. Redeploy core bi pull `ghcr.io/your-org/...` do deploy script cu ghi de `GHCR_OWNER` tu `.env.staging`. Ban sua moi da fix loi nay.

## Final Health Check

Chay sau moi demo:

```bash
curl -i http://13.228.171.39:18081/api/health
curl -i http://18.140.170.236:18080/api/health
curl -i http://47.131.35.71:18000/health

ssh -i $KEY ec2-user@$MONITOR
curl -s 'http://127.0.0.1:9090/api/v1/targets?state=active' \
  | jq '.data.activeTargets[] | select(.health!="up")'
```

Neu query cuoi khong in gi ra va 3 endpoint deu `200 OK`, staging da sach.
