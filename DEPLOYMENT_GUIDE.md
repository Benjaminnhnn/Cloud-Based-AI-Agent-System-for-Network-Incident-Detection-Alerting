# 📋 DEPLOYMENT & PRODUCTION DEPLOYMENT GUIDE

**Project**: AWS Hybrid Cloud - AI Monitoring & Alert System  
**Status**: ✅ Production Ready  
**Last Updated**: 2026-04-07

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
```bash
# Required
- Docker & Docker Compose (v1.29+)
- Git
- Linux/Mac (or WSL on Windows)

# Optional but Recommended
- Terraform (for infrastructure)
- Ansible (for configuration management)
- AWS CLI (for cloud operations)
```

### Deploy with Docker Compose
```bash
# Clone or navigate to project
cd /home/hoang_viet/aws-hybrid

# Copy environment template
cp .env.prod.template .env.prod

# Edit environment variables (add your API keys)
nano .env.prod

# Start all services
docker-compose up -d

# Verify system is running
docker ps | grep -E "(prometheus|grafana|node_exporter)"

# Access services
# - Grafana: http://localhost:3001 (admin/admin123)
# - Prometheus: http://localhost:9090
# - Node Exporter: http://localhost:9100
```

---

## 📂 Essential Files for Deployment

### Core Configuration Files (REQUIRED)
```
✅ docker-compose.yml              # Main container orchestration
✅ prometheus.yml                  # Prometheus scrape config
✅ config/prometheus.yml           # Source prometheus config
✅ .env.prod.template              # Environment variables
✅ .gitignore                       # Git ignore rules
```

### Docker Configurations (REQUIRED)
```
✅ config/docker-compose.yml       # Development compose
✅ config/docker-compose.prod.yml  # Production compose
✅ config/nginx.conf               # Nginx reverse proxy
✅ config/alertmanager.yml         # AlertManager config
✅ config/alert_rules.yml          # Prometheus alert rules
```

### Application Source Code (REQUIRED)
```
✅ agent_src/                      # AI Agent Flask app
   ├── main.py                     # Webhook handler
   ├── telegram_notify.py          # Telegram integration
   ├── log_watcher.py              # Log monitoring
   ├── Dockerfile
   └── requirements.txt

✅ demo-web/                       # Full-stack demo app
   ├── backend/                    # FastAPI backend
   ├── frontend/                   # React frontend
   └── database/                   # PostgreSQL scripts
```

### Infrastructure as Code (REQUIRED for Cloud Deployment)
```
✅ terraform/                      # Terraform configs
   ├── provider.tf                 # AWS provider
   ├── variables.tf                # Input variables
   ├── compute.tf                  # EC2 instances
   ├── network.tf                  # VPC setup
   ├── security.tf                 # Security groups
   ├── outputs.tf                  # Output values
   ├── versions.tf                 # Provider versions
   ├── terraform.tfvars            # Variable values
   └── terraform.tfstate           # Current state (KEEP PRIVATE)

✅ terraform.tfstate               # Terraform state (DO NOT COMMIT)
```

### Configuration Management (REQUIRED for Full Deployment)
```
✅ ansible/                        # Ansible playbooks
   ├── inventory.ini               # Host inventory
   ├── ansible.cfg                 # Ansible config
   ├── group_vars/                 # Group variables
   ├── playbooks/
   │   ├── bootstrap.yml           # Initial setup
   │   ├── monitoring.yml          # Prometheus/Grafana
   │   ├── ai_agent.yml            # AI Agent setup
   │   └── deploy-complete-infrastructure.yml
   └── config/
       ├── alert_rules.yml
       └── alertmanager.yml
```

### Deployment Scripts (RECOMMENDED)
```
✅ scripts/                        # Deployment automation
   ├── deploy-infrastructure.sh    # ⭐ Full infrastructure deployment
   ├── ansible-deploy.sh           # Ansible orchestration wrapper
   └── fix-credentials.sh          # AWS credentials helper (optional)
```

### Documentation (RECOMMENDED)
```
✅ README.md                       # Main documentation
✅ docs/
   ├── ARCHITECTURE_DIAGRAMS.md    # System architecture
   ├── BAOCAO_TRIENKHAI_CLOUD.md   # Vietnamese report
   └── D1_TEST_SCENARIO_REPORT.md  # Test scenarios
```

---

## 🗑️ Files NOT Needed for Deployment

### Removed During Cleanup
```
❌ terraform/aws/                 # AWS CLI binaries
❌ terraform/awscliv2.zip        # AWS CLI installer
❌ terraform/terraform.tfstate.backup
❌ terraform/terraform.tfstate.backup.old
❌ terraform/apply_output.txt     # Terraform logs
❌ terraform/tfplan               # Old terraform plan
❌ docs/docx_extracted/           # Extracted Word files
❌ **/__pycache__/                # Python cache
❌ *.pyc                          # Python compiled files
```

### Should Never Be Committed (in .gitignore)
```
❌ .env                           # Environment variables
❌ terraform/terraform.tfstate    # Terraform state
❌ .aws/                          # AWS credentials
❌ *.pem, *.pub                   # SSH keys
❌ secrets/                       # Secrets
```

---

## 🔄 Deployment Scenarios

### Scenario 1: Local Development (Docker)
**Time**: 5 minutes  
**Requirements**: Docker & Docker Compose only

```bash
# Clone project
git clone <repo-url>
cd aws-hybrid

# Start services
docker-compose up -d

# Verify
curl http://localhost:9090/api/v1/query?query=up
```

**What you get**:
- ✅ Prometheus collecting metrics
- ✅ Grafana dashboards
- ✅ AlertManager
- ✅ AI Agent webhook handler
- ✅ Database & API

### Scenario 2: Full AWS Deployment (Terraform + Ansible)
**Time**: 20-30 minutes  
**Requirements**: Terraform, Ansible, AWS Account

```bash
# 1. Initialize Terraform
cd terraform
terraform init
terraform plan

# 2. Create AWS infrastructure
terraform apply -auto-approve

# 3. Get instance IPs from output
MONITOR_IP=$(terraform output -raw monitor_public_ip)

# 4. Update Ansible inventory
sed -i "s/REPLACE_ME_MONITOR_IP/$MONITOR_IP/" ../ansible/inventory.ini

# 5. Deploy with Ansible
cd ../ansible
ansible-playbook -i inventory.ini playbooks/deploy-complete-infrastructure.yml

# 6. Access system
echo "Grafana: http://$MONITOR_IP:3001"
echo "Prometheus: http://$MONITOR_IP:9090"
```

**What you get**:
- ✅ EC2 instances for monitoring, web, core
- ✅ VPC & security groups
- ✅ Elastic IPs for access
- ✅ Auto-configured monitoring stack
- ✅ AI Agent with Telegram notifications

### Scenario 3: Kubernetes Deployment (Future)
**Time**: TBD  
**Requirements**: Kubernetes cluster

```bash
# Convert docker-compose to Kubernetes
# (Kompose or manual conversion)
kompose convert -f docker-compose.yml

# Deploy to cluster
kubectl apply -f converted-manifests/
```

---

## 📊 Architecture

### Stack Components
```
┌─────────────────────────────────────────────────────┐
│                  Grafana (3001)                      │
│              Dashboard & Visualization                │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────▼───────────┐
        │  Prometheus (9090)   │
        │  Time Series Data    │
        └──────────┬───────────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
  Node Ex    Node Ex    Node Ex
  (9100)    (9100)    (9100)
  Monitor   Web       Core


┌────────────────────────────────────────┐
│      AlertManager (9093)               │
│    Alert Routing & Deduplication       │
└──────────────┬───────────────────────┘
               │
      ┌────────▼─────────┐
      │   AI Agent (8000)│
      │  Webhook Handler │
      └────────┬─────────┘
               │
       ┌───────▼────────┐
       │  Telegram Bot  │
       │  Notifications │
       └────────────────┘
```

### Services

| Service | Port | Purpose | Container |
|---------|------|---------|-----------|
| Grafana | 3001 | Dashboards | grafana:latest |
| Prometheus | 9090 | Metrics DB | prom/prometheus |
| AlertManager | 9093 | Alert routing | prom/alertmanager |
| Node Exporter | 9100 | Host metrics | prom/node-exporter |
| API | 8000 | FastAPI backend | aws-hybrid_api |
| Web | 3000 | React frontend | aws-hybrid_web |
| DB | 5432 | PostgreSQL | postgres:14-alpine |
| AI Agent | 5000 | Webhook handler | aws-hybrid_ai-agent |

---

## 🔐 Security Checklist

### Before Production

- [ ] Change default credentials
  ```yaml
  GF_SECURITY_ADMIN_PASSWORD: (change from "admin123")
  TELEGRAM_TOKEN: (set your token)
  TELEGRAM_CHAT_ID: (set your chat ID)
  GEMINI_API_KEY: (set your API key)
  ```

- [ ] Secure Prometheus (not publicly accessible)
  - Use reverse proxy with authentication
  - Implement firewall rules

- [ ] Secure state files
  ```bash
  # Move terraform state to S3 backend
  # DO NOT commit to Git
  terraform state push  # Only with S3 backend
  ```

- [ ] Rotate credentials regularly
  - Telegram tokens
  - API keys
  - Database passwords

- [ ] Enable HTTPS
  - Use Let's Encrypt
  - Configure nginx SSL

- [ ] Backup data
  ```bash
  # Backup Prometheus data
  docker run --volumes-from prometheus \
    -v $(pwd)/backup:/backup \
    ubuntu tar czf /backup/prometheus.tar.gz \
    /prometheus

  # Backup Grafana dashboards
  docker exec grafana grafana-cli admin \
    export-dashboard <dashboard-id>
  ```

---

## 📈 Monitoring the Monitoring System

### Health Checks
```bash
# Prometheus
curl -s http://localhost:9090/api/v1/status/config | jq '.status'

# Grafana
curl -s http://admin:admin123@localhost:3001/api/health | jq '.database'

# AlertManager
curl -s http://localhost:9093/api/v1/alerts | jq '.'

# Node Exporter
curl -s http://localhost:9100/metrics | head -5
```

### Log Monitoring
```bash
# View logs
docker logs prometheus
docker logs grafana
docker logs alertmanager
docker logs ai-agent

# Follow logs
docker logs -f prometheus
```

### Performance Metrics
```bash
# Prometheus storage usage
docker exec prometheus du -sh /prometheus

# Grafana database size
docker exec grafana du -sh /var/lib/grafana

# Container resource usage
docker stats --no-stream
```

---

## 🔧 Troubleshooting

### Prometheus not collecting data
```bash
# Check config
docker exec prometheus cat /etc/prometheus/prometheus.yml

# Check targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].labels.job'

# Restart if needed
docker restart prometheus
```

### Grafana can't connect to Prometheus
```bash
# Verify datasource URL
curl http://admin:admin123@localhost:3001/api/datasources | jq '.[] | .url'

# Test connection from grafana container
docker exec grafana curl -v http://prometheus:9090/api/v1/status/config

# Recreate datasource if needed
curl -X DELETE http://admin:admin123@localhost:3001/api/datasources/1
# Then recreate through UI or API
```

### Alerts not triggering
```bash
# Check alert rules
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | {name, state}'

# Check AlertManager configuration
docker exec alertmanager cat /etc/alertmanager/alertmanager.yml

# Test webhook
curl -X POST http://localhost:5000/webhook -d '{"alerts":[]}'
```

---

## 📝 Update & Maintenance

### Update Services
```bash
# Pull latest images
docker-compose pull

# Restart with latest
docker-compose up -d

# Or rebuild from source
docker-compose build --no-cache
docker-compose up -d
```

### Backup & Restore

#### Backup
```bash
# Export Grafana dashboards
for id in $(curl -s http://admin:admin123@localhost:3001/api/search | jq '.[].id'); do
  curl -s http://admin:admin123@localhost:3001/api/dashboards/uid/<uid> > dashboard_$id.json
done

# Export Prometheus data
docker exec prometheus tar czf - /prometheus > prometheus_backup.tar.gz

# Backup configurations
tar czf configs_backup.tar.gz config/ prometheus.yml ansible/
```

#### Restore
```bash
# Restore Prometheus data
docker exec prometheus sh -c 'tar xzf - -C /' < prometheus_backup.tar.gz

# Restore configurations
tar xzf configs_backup.tar.gz
docker-compose restart
```

---

## 🚀 Performance Optimization

### For High-Volume Metrics
```yaml
# Increase Prometheus storage retention
prometheus:
  command:
    - '--storage.tsdb.retention.time=180d'
    - '--storage.tsdb.retention.size=50GB'
```

### For Many Targets
```yaml
# Increase scrape parallelism
prometheus:
  command:
    - '--query.max-concurrency=40'
    - '--query.timeout=5m'
```

### For Grafana Dashboard Performance
1. Reduce query frequency (min 30s)
2. Implement dashboard row-level collapse
3. Use query caching
4. Implement query speed tests

---

## 📞 Support & Troubleshooting

### Check System Status
```bash
cd /home/hoang_viet/aws-hybrid

# Full system check
docker-compose ps

# Check volumes
docker volume ls | grep aws-hybrid

# Check network
docker network ls | grep aws-hybrid_aiops-network

# View full logs
docker-compose logs --tail=50
```

### Emergency Restart
```bash
# Graceful restart
docker-compose restart

# Full reset (⚠️ DESTRUCTIVE)
docker-compose down -v
docker-compose up -d

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

---

## ✅ Deployment Verification Checklist

After deployment, verify:

- [ ] All containers running: `docker ps`
- [ ] Prometheus collecting metrics: Check graph at :9090
- [ ] Grafana accessible: Access at :3001
- [ ] Datasource connected: Check in Grafana UI
- [ ] Alerts configured: Check AlertManager at :9093
- [ ] AI Agent running: Check logs at `docker logs ai-agent`
- [ ] API responding: `curl http://localhost:8000/api/health`
- [ ] Database healthy: `docker logs aiops-db`
- [ ] Data flowing: `curl http://localhost:9090/api/v1/query?query=up`

---

## 🎯 Next Steps

1. **Immediate**: Deploy to production using docker-compose
2. **Short-term**: Configure auto-scaling with Kubernetes
3. **Long-term**: Implement CI/CD with GitHub Actions
4. **Ongoing**: Monitor system performance & optimize

---

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Ansible Documentation](https://docs.ansible.com/)

---

**Ready for production deployment!** 🚀 🎉

*Last Updated: 2026-04-07*  
*Status: ✅ Production Ready*
