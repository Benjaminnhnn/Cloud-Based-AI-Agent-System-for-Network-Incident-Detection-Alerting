# Runbook: PostgreSQL va Payment API

Dung cho cac alert lien quan den Payment API readiness, PostgreSQL availability va ket noi API-to-database.

## PaymentAPIEndpointDown

Chan doan: Blackbox khong nhan HTTP 2xx tu Payment API endpoint.

Context:
- Component: `{{component}}`
- Host: `{{instance}}`
- Target: `{{target}}`
- Environment: `{{environment}}`
- Tom tat: {{summary}}

Nguyen nhan uu tien:
1. Payment API process loi hoac readiness endpoint tra non-2xx.
2. Security Group, firewall hoặc route chan monitor truy cap port API.
3. Payment API mat ket noi PostgreSQL.
4. Container van running nhung ung dung ben trong khong phuc vu request.

Kiem tra tren `bank-core-01`:
```bash
docker ps --filter name={{component}}
docker logs --tail=100 {{component}}
curl -i {{local_payment_ready_url}}
sudo iptables -S | grep -E '18080|8000' || true
```

Khoi phuc:
```bash
# Xoa rule firewall thu nghiem hoac sua dependency gay loi neu co.
cd /home/ec2-user/aws-hybrid
TAG=$(cat {{state_file}})
{{deploy_command}}
```

## PostgreSQLDown

Chan doan: postgres_exporter bao PostgreSQL khong san sang hoac khong scrape duoc.

Context:
- Component: `{{component}}`
- Host: `{{instance}}`
- Environment: `{{environment}}`
- Tom tat: {{summary}}

Nguyen nhan uu tien:
1. `{{component}}` stopped hoac unhealthy.
2. PostgreSQL khoi dong cham, volume loi hoac database chua ready.
3. postgres-exporter khong ket noi duoc PostgreSQL.
4. Payment API mat ket noi DB nen `/api/health` co the fail.

Kiem tra tren `bank-core-01`:
```bash
docker ps -a --filter name={{component}}
docker inspect -f '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' {{component}} || true
docker logs --tail=100 {{component}}
docker exec {{component}} pg_isready -U aiops_user -d aiops_db
curl -i {{local_payment_health_url}}
```

Khoi phuc nhanh:
```bash
docker start {{component}}
cd /home/ec2-user/aws-hybrid
TAG=$(cat {{state_file}})
{{deploy_command}}
```

Luu y an toan:
- Khong xoa PostgreSQL volume khi chua backup.
- Neu DB restart loop, uu tien doc log va kiem tra disk truoc khi redeploy.
