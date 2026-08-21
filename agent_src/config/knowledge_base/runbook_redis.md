# Runbook: Redis Cache va Redis Broker

Dung cho cac alert lien quan den Redis cache duoc demo app su dung va Redis broker phuc vu Celery queue.

## RedisDown

Chan doan: redis_exporter bao Redis cache khong san sang hoac khong scrape duoc.

Context:
- Component: `{{component}}`
- Host: `{{instance}}`
- Environment: `{{environment}}`
- Redis exporter: `{{redis_exporter_url}}`
- Tom tat: {{summary}}

Nguyen nhan uu tien:
1. `{{component}}` stopped hoac unhealthy.
2. Redis loi appendonly/volume hoac restart loop.
3. redis-exporter khong ket noi duoc Redis cache.
4. Neu Redis broker dung, AI Agent/Celery co the xu ly alert cham.

Kiem tra tren `monitor-ai-01`:
```bash
docker ps -a --filter name={{component}}
docker inspect -f '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' {{component}} || true
docker logs --tail=100 {{component}}
docker exec {{component}} redis-cli ping
curl -s {{redis_exporter_url}} | head
```

Khoi phuc nhanh:
```bash
docker start {{component}}
cd /home/ec2-user/aws-hybrid
TAG=$(cat {{state_file}})
{{deploy_command}}
```

## RedisBrokerDown

Chan doan: Redis broker cua Celery khong san sang hoac redis-broker-exporter khong scrape duoc.

Context:
- Component: `{{component}}`
- Host: `{{instance}}`
- Environment: `{{environment}}`
- Tom tat: {{summary}}

Tac dong:
1. FastAPI `/webhook` co the tra HTTP 503 vi khong enqueue duoc task.
2. Celery worker khong nhan duoc alert moi.
3. Queue backlog va alert `CeleryQueueBacklogHigh` co the tang neu broker cham.

Kiem tra tren `monitor-ai-01`:
```bash
docker ps -a --filter name={{component}}
docker logs --tail=100 {{component}}
docker exec {{component}} redis-cli ping
docker logs --tail=100 celery-worker-{{environment}} || true
curl -s http://127.0.0.1:18000/health
```

Khoi phuc nhanh:
```bash
docker start {{component}}
cd /home/ec2-user/aws-hybrid
TAG=$(cat {{state_file}})
{{deploy_command}}
```

Luu y an toan:
- Khong flush Redis broker/cache trong moi truong production neu chua xac dinh tac dong.
- Neu Redis lien tuc OOM, tang `REDIS_BROKER_MAXMEMORY` hoac `REDIS_CACHE_MAXMEMORY` thay vi xoa du lieu tuy tien.
