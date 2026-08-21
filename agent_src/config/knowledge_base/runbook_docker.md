# Runbook: Docker Container va Release Stack

Dung cho cac alert lien quan den container bat buoc cua release stack bi mat khoi cAdvisor hoac `container_last_seen` qua cu.

## DockerContainerDown

Chan doan: cAdvisor khong con thay container bat buoc cua release stack.

Context:
- Component: `{{component}}`
- Host: `{{instance}}`
- Deploy role: {{role}}
- Environment: `{{environment}}`
- Tom tat: {{summary}}

Nguyen nhan uu tien:
1. Container bi stop/rm thu cong trong demo hoac sau deploy loi.
2. Docker daemon restart va container khong duoc recreate dung compose project.
3. Host het disk, pull image fail hoac health check lam release chua hoan tat.
4. Neu mat `ai-agent`, Alertmanager co the khong gui duoc thong bao moi cho den khi khoi phuc.

Kiem tra tren `{{instance}}`:
```bash
docker ps -a --filter name={{component}}
docker inspect -f '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' {{component}} || true
docker logs --tail=100 {{component}} || true
df -h /
docker system df
```

Khoi phuc bang release script:
```bash
cd /home/ec2-user/aws-hybrid
TAG=$(cat {{state_file}})
{{deploy_command}}
```

Luu y an toan:
- Khong chay `docker system prune -a --volumes` tren host production neu chua xac dinh volume nao dang duoc PostgreSQL/Redis dung.
- Neu container bi xoa do deploy loi, uu tien redeploy dung role thay vi tao container thu cong.
