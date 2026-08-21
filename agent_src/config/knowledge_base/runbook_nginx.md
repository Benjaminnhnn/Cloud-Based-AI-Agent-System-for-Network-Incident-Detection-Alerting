# Runbook: Nginx va Frontend Web

Dung cho cac alert lien quan den frontend container, Nginx reverse proxy va ket noi tu frontend sang Payment API.

## WebEndpointDown

Chan doan: Blackbox khong nhan HTTP 2xx tu web endpoint.

Context:
- Component: `{{component}}`
- Host: `{{instance}}`
- Target: `{{target}}`
- Environment: `{{environment}}`
- Tom tat: {{summary}}

Nguyen nhan uu tien:
1. `{{component}}` stopped hoac unhealthy.
2. Nginx khong tra `/health` hoac container khong bind dung port.
3. Firewall, Security Group hoac route chan monitor truy cap frontend.
4. Neu `/health` OK nhung API loi, kiem tra `PAYMENT_API_UPSTREAM` va backend core.

Kiem tra tren `bank-web-01`:
```bash
docker ps -a --filter name={{component}}
docker inspect -f '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' {{component}} || true
docker logs --tail=100 {{component}}
curl -i {{local_web_health_url}}
curl -i {{local_web_api_health_url}}
```

Khoi phuc nhanh:
```bash
docker start {{component}}
cd /home/ec2-user/aws-hybrid
TAG=$(cat {{state_file}})
{{deploy_command}}
```

## FrontendAPIProxyDown

Chan doan: frontend van co the chay nhung Nginx proxy khong nhan HTTP 2xx tu API upstream.

Context:
- Component: `{{component}}`
- Host: `{{instance}}`
- Dependency: `{{dependency}}`
- Expected upstream: `{{expected_upstream}}`
- Target: `{{target}}`
- Environment: `{{environment}}`
- Tom tat: {{summary}}

Correlation: frontend /health vẫn trả 200 và Payment API readiness probe trực tiếp vẫn khỏe, nen loi nam o cau hinh hoac duong ket noi web-to-core.

Nguyen nhan uu tien:
1. `PAYMENT_API_UPSTREAM` sai host, sai port hoac thieu scheme `http://`.
2. Security Group, firewall hoac route chan ket noi tu web toi core.
3. Nginx chua duoc recreate sau khi thay doi cau hinh upstream.

Kiem tra tren `bank-web-01`:
```bash
docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' {{component}} | grep PAYMENT_API_UPSTREAM
docker logs --tail=100 {{component}}
curl -i {{local_web_health_url}}
curl -i {{local_proxy_ready_url}}
```

Khoi phuc cau hinh:
```bash
cd /home/ec2-user/aws-hybrid
grep '^PAYMENT_API_UPSTREAM=' release/.env.{{environment}}
sed -i 's|^PAYMENT_API_UPSTREAM=.*|PAYMENT_API_UPSTREAM={{expected_upstream}}|' release/.env.{{environment}}
TAG=$(cat {{state_file}})
{{deploy_command}}
```

Luu y an toan:
- Chi sua `PAYMENT_API_UPSTREAM` ve endpoint da duoc kiem tra.
- Neu nghi ngo Security Group, kiem tra rule web-to-core truoc khi redeploy.
