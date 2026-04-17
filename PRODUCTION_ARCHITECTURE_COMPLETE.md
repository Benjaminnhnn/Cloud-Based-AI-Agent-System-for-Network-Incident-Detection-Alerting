# Production Architecture - Complete Reference

**Date**: 2026-04-17  
**Status**: ✅ Active Production  
**Sources**: 
- PRODUCTION_ARCHITECTURE_SUMMARY.md
- diagram/ARCHITECTURE_DIAGRAMS.md

---

## 📑 Quick Navigation

1. [Production Topology](#1-production-topology)
2. [Public Access Points](#2-public-access-points)
3. [Infrastructure Diagram](#3-infrastructure-diagram)
4. [Monitoring Stack](#4-monitoring-stack)
5. [Alert Flow](#5-alert-processing-flow)
6. [Security Posture](#6-security-hardening)
7. [Operations Guide](#7-operations-guide)

---

## 1. Production Topology

### 1.1 Instances Overview

| Node | Public IP | Private IP | Role | Region |
|------|-----------|------------|------|--------|
| **Monitor** | `52.74.118.8` | `10.10.1.231` | Monitoring, AI, Alerts | ap-southeast-1 |
| **Web** | `18.136.112.28` | `10.10.1.68` | Nginx, Frontend, API Proxy | ap-southeast-1 |
| **Core** | `54.255.94.179` | `10.10.1.78` | Internal Services | ap-southeast-1 |

### 1.2 VPC Configuration

```
VPC CIDR: 10.10.0.0/16
Public Subnet: 10.10.1.0/24 (contains all 3 instances)
Internet Gateway: Enabled
NAT: Not used (all instances have Elastic IPs for outbound)
```

### 1.3 Services Deployed

**Monitor Node (52.74.118.8)**
- Prometheus (9090) - Time-series database & alert evaluation
- Alertmanager (9093) - Alert routing & grouping
- Grafana (3000) - Dashboards & visualization
- Node Exporter (9100) - System metrics collection
- AI Agent (8000) - Alert analysis & Telegram notifications

**Web Node (18.136.112.28)**
- Nginx (80/443) - Reverse proxy
- Frontend React App - Running behind Nginx at `/`
- Backend API Proxy - Routes `/api/*` to Core node
- Node Exporter (9100) - Host metrics

**Core Node (54.255.94.179)**
- Internal business logic services
- Database connections
- API endpoints (not directly exposed, accessed via Web node)
- Node Exporter (9100) - Host metrics

---

## 2. Public Access Points

### 2.1 For Users

| Service | URL | Purpose |
|---------|-----|---------|
| Web App | `http://18.136.112.28` | Frontend application |
| API Health | `http://18.136.112.28/api/health` | Backend health check |

### 2.2 For Admins

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | `http://52.74.118.8:3000` | admin / admin123 |
| Prometheus | `http://52.74.118.8:9090` | None (view-only) |
| Alertmanager | `http://52.74.118.8:9093` | None (view-only) |

### 2.3 Health Check Endpoints

```bash
# Prometheus
curl http://52.74.118.8:9090/-/healthy

# Alertmanager  
curl http://52.74.118.8:9093/-/healthy

# Grafana
curl http://52.74.118.8:3000/api/health

# API
curl http://18.136.112.28/api/health
```

---

## 3. Infrastructure Diagram

### 3.1 Overall Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AWS PUBLIC CLOUD (ap-southeast-1)                │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  AWS VPC (10.10.0.0/16)                      │  │
│  │                                                               │  │
│  │  ┌─────────────────┐  ┌──────────────────┐                   │  │
│  │  │   Web Node      │  │   Core Node      │   Monitor Node    │  │
│  │  │  18.136.112.28  │  │  54.255.94.179   │  52.74.118.8      │  │
│  │  │  10.10.1.68     │  │  10.10.1.78      │  10.10.1.231      │  │
│  │  │                 │  │                  │                   │  │
│  │  │ • Nginx (80)    │  │ • Internal APIs  │ • Prometheus      │  │
│  │  │ • Frontend      │  │ • Services       │ • Grafana (3000)  │  │
│  │  │ • API Proxy     │  │ • Database       │ • AlertManager    │  │
│  │  │ • Node Exp      │  │ • Node Exporter  │ • AI Agent (8000) │  │
│  │  │   (9100)        │  │   (9100)         │ • Node Exp (9100) │  │
│  │  └────────┬────────┘  └────────┬─────────┘ └─────────────────┘  │
│  │           │                    │                                 │
│  │           └────────┬───────────┘                                 │
│  │                    │                                             │
│  │            ┌───────▼────────┐                                    │
│  │            │ Prometheus     │                                    │
│  │            │ Scrape All     │                                    │
│  │            │ Node Exporters │                                    │
│  │            └────────────────┘                                    │
│  │                                                                   │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │       Security Groups (Firewall Rules Applied)               │  │
│  │                                                               │  │
│  │  Web SG:                                                      │  │
│  │    ✓ SSH (22) from Admin IP only                             │  │
│  │    ✓ HTTP (80) from 0.0.0.0/0 (Internet)                    │  │
│  │    ✓ HTTPS (443) from 0.0.0.0/0 (Internet)                  │  │
│  │    ✓ Node Exporter (9100) from Monitor SG                    │  │
│  │                                                               │  │
│  │  Monitor SG:                                                  │  │
│  │    ✓ SSH (22) from Admin IP only                             │  │
│  │    ✓ Prometheus (9090) from Admin IP only                    │  │
│  │    ✓ Alertmanager (9093) from Admin IP only                  │  │
│  │    ✓ Grafana (3000) from Admin IP only                       │  │
│  │    ✓ AI Agent (8000) from Admin IP only                      │  │
│  │                                                               │  │
│  │  Core SG:                                                     │  │
│  │    ✓ SSH (22) from Admin IP only                             │  │
│  │    ✓ API (8000) from Web SG and Monitor SG only              │  │
│  │    ✓ Node Exporter (9100) from Monitor SG                    │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Elastic IPs (Static Public IPs)                  │  │
│  │  • Monitor: 52.74.118.8 (allocated for monitoring services)  │  │
│  │  • Web:     18.136.112.28 (allocated for web access)         │  │
│  │  • Core:    54.255.94.179 (allocated for API access)         │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

        ┌──────────────────────────────────┐
        │ INTERNET (0.0.0.0/0)             │
        ├──────────────────────────────────┤
        │ • Users access Web Node port 80  │
        │ • Admins access Monitor port 3000│
        └──────────────────────────────────┘
```

### 3.2 Monitoring Stack

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Monitor Node (52.74.118.8)                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Container Orchestration                         │   │
│  │  Host OS: Amazon Linux 2023 (t3.small)                       │   │
│  │  Storage: 12 GB gp3 (encrypted)                              │   │
│  │  CPU/Memory: Sufficient for monitoring workload              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────────┐ │
│  │  PROMETHEUS    │  │  ALERTMANAGER   │  │  GRAFANA (3000)      │ │
│  │  (9090)        │  │  (9093)         │  │                      │ │
│  │                │  │                 │  │  ┌────────────────┐  │ │
│  │ • Time series  │  │ • Routes alerts │  │  │  Datasource:   │  │ │
│  │   database     │  │ • Groups by     │  │  │  Prometheus    │  │ │
│  │ • 15-day       │  │   alertname,    │  │  │  (9090)        │  │ │
│  │   retention    │  │   severity,     │  │  │                │  │ │
│  │ • Evaluation   │  │   instance      │  │  │  Dashboards:   │  │ │
│  │   interval: 30s│  │ • Webhook to    │  │  │  • System      │  │ │
│  │ • Scrape       │  │   AI Agent      │  │  │  • Network     │  │ │
│  │   interval: 15s│  │   (8000)        │  │  │  • Alerts      │  │ │
│  │                │  │ • group_wait:   │  │  │                │  │ │
│  │ Alert Rules:   │  │   10s           │  │  │  Users: admin  │  │ │
│  │ • High CPU     │  │ • repeat_inte   │  │  │  Pass: admin123│  │ │
│  │ • High Memory  │  │   rval: 4h      │  │  └────────────────┘  │ │
│  │ • High Disk    │  │                 │  │                      │ │
│  │ • Service Down │  │                 │  │  • Update freq: 5s   │ │
│  │ • Network High │  │                 │  │  • Time range: 6h    │ │
│  └────────────────┘  └────────┬────────┘  └──────────────────────┘ │
│                               │                                     │
│                   ┌───────────▼─────────────┐                       │
│                   │  NODE EXPORTER (9100)   │                       │
│                   │                         │                       │
│                   │ Collects metrics from:  │                       │
│                   │ • CPU (idle, user, sys) │                       │
│                   │ • Memory (available)    │                       │
│                   │ • Disk I/O              │                       │
│                   │ • Network I/O           │                       │
│                   │ • Load average          │                       │
│                   │ • Process count         │                       │
│                   │                         │                       │
│                   │ Exposed on 9100/metrics │                       │
│                   │ Scraped every 15s       │                       │
│                   └─────────────────────────┘                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  AI AGENT (8000)                                             │   │
│  │  ┌──────────────────────────────────────────────────────────┤   │
│  │  │ Webhook endpoint: /webhook                               │   │
│  │  │ • Receives alerts from AlertManager                      │   │
│  │  │ • Parses alert JSON                                      │   │
│  │  │ • Calls Google Gemini 2.5 Flash API                      │   │
│  │  │ • Formats response for Telegram                          │   │
│  │  │ • Sends to Telegram Bot API                              │   │
│  │  │                                                          │   │
│  │  │ Health endpoint: /health                                 │   │
│  │  │ • Returns 200 OK if running                              │   │
│  │  └──────────────────────────────────────────────────────────┤   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
       ▲                          │                        │
       │                          │                        │
    Scrapes                  Webhook POST              Grafana
    from Web,                to AI Agent               queries
    Core,                                              metrics
    Monitor
    Node
    Exporters
```

---

## 4. Monitoring Stack - Detailed View

### 4.1 Prometheus Configuration

```yaml
Global Settings:
  - Scrape Interval: 15s
  - Evaluation Interval: 30s
  - Retention: 30d

Scrape Targets:
  1. Web Node: 18.136.112.28:9100 (Node Exporter)
  2. Core Node: 54.255.94.179:9100 (Node Exporter)
  3. Monitor Node: 127.0.0.1:9100 (Node Exporter)

Alert Rules:
  - HighCPUUsage: CPU > 80% for 5 minutes
  - CriticalCPUUsage: CPU > 95% for 1 minute
  - HighMemoryUsage: Memory > 85% for 2 minutes
  - CriticalMemoryUsage: Memory > 95% for 1 minute
  - HighDiskUsage: Disk > 80% for 5 minutes
  - CriticalDiskUsage: Disk > 90% for 2 minutes
  - HighNetworkTraffic: Network RX > 10MB/s for 2 minutes
  - ServiceDown: Any monitored service returns UP=0 for 1 minute
  - WebEndpointDown: Blackbox probe failed for 30s
```

### 4.2 Alertmanager Configuration

```yaml
Routing:
  - Default receiver: 'default'
  - Critical alerts: 5s wait, 5s interval, 1h repeat
  - Warning alerts: 10s wait, 10s interval, 4h repeat
  - System alerts: 10s wait, 10s interval, 6h repeat
  - Availability alerts: 5s wait, 5s interval, 2h repeat

Receivers:
  - name: 'default'
    webhook_configs:
      - url: http://localhost:8000/webhook
        send_resolved: true

Inhibition Rules:
  - Critical alerts suppress Warning alerts
  - Critical alerts suppress Info alerts
```

### 4.3 Grafana Dashboards

```
Available Dashboards:
  1. System Overview
     - CPU usage (gauge + timeseries)
     - Memory usage (gauge + timeseries)
     - Disk usage (gauge + timeseries)
     - System load average

  2. Network & Performance
     - Network RX/TX bytes
     - System load average (1, 5, 15 min)
     - Disk I/O operations
     - Network errors

  3. Alert Monitoring
     - Active alerts count
     - Alert firing rate
     - Alert history
     - Alert severity distribution

Refresh Rate: 5 seconds
Time Range: Last 6 hours (default)
```

---

## 5. Alert Processing Flow

### 5.1 Step-by-Step Alert Journey

```
T+0s:   System metric spike detected (e.g., CPU → 85%)
        └─ Node Exporter reports to Prometheus

T+15s:  Prometheus scrapes Node Exporter
        └─ Stores: node_cpu{instance="web-01"} = 0.85

T+30s:  Prometheus evaluates alert rules
        └─ Check: rate(cpu > 0.80) == true ✓
        └─ Check: duration > 5 min == false ✗
        └─ Result: Alert NOT FIRED (waiting for threshold)

T+5m:   CPU still elevated (5+ minutes)
        └─ Prometheus re-evaluates
        └─ Check: rate(cpu > 0.80) == true ✓
        └─ Check: duration > 5 min == true ✓
        └─ Result: ALERT FIRES! 🔴

T+5m+5s: AlertManager receives alert
         └─ GroupBy: alertname=HighCPUUsage, instance=web-01
         └─ Deduplicates (first time, so send)
         └─ Routes to webhook receiver

T+5m+7s: AI Agent receives webhook POST
         ├─ Parses alert JSON
         ├─ Calls Gemini API: "Alert analysis..."
         └─ Waits for response (~2 seconds)

T+5m+9s: Gemini returns analysis
         └─ "High CPU likely due to increased traffic..."

T+5m+10s: AI Agent sends to Telegram
          └─ Message: "⚠️ HIGH CPU on web-01 (85%)"
          └─ Includes AI suggestion

T+5m+12s: DevOps team receives Telegram notification 📱
          └─ Team clicks link to Grafana
          └─ Views metrics in detail
          └─ SSH to instance to investigate
          └─ Finds and fixes issue

T+10m:   CPU returns to normal (25%)
         └─ Prometheus: rate(cpu > 0.80) == false
         └─ Alert transitions to RESOLVED

T+10m+5s: AlertManager sends RESOLVED notification
          └─ Telegram: "✅ HighCPUUsage RESOLVED"
          └─ Team informed
```

### 5.2 Alert Severity Levels

```
CRITICAL (Red) 🔴
  - CPU > 95% for 1 minute
  - Memory > 95% for 1 minute
  - Disk > 90% for 2 minutes
  - Any critical service DOWN
  → Repeat notification every 1 hour
  → Team immediate action required

WARNING (Yellow) 🟡
  - CPU > 80% for 5 minutes
  - Memory > 85% for 2 minutes
  - Disk > 80% for 5 minutes
  - Non-critical service DOWN
  → Repeat notification every 4 hours
  → Team should investigate within 1 hour

INFO (Blue) 🔵
  - Network high traffic
  - Service degraded
  → Repeat notification every 6 hours
  → Log for audit purposes
```

---

## 6. Security Hardening

### 6.1 Network Security (Security Groups)

**Web Node Security Group**
```
Inbound:
  ✓ SSH (22)        from Admin IP only
  ✓ HTTP (80)       from 0.0.0.0/0 (Internet)
  ✓ HTTPS (443)     from 0.0.0.0/0 (Internet)
  ✓ Node Exporter   from Monitor SG
  ✗ All other ports → DENY

Outbound:
  ✓ All traffic     to 0.0.0.0/0
```

**Monitor Node Security Group**
```
Inbound:
  ✓ SSH (22)        from Admin IP only
  ✓ Prometheus      from Admin IP only
  ✓ Alertmanager    from Admin IP only
  ✓ Grafana (3000)  from Admin IP only
  ✓ AI Agent (8000) from Admin IP only
  ✓ Node Exporter   from self + other SGs
  ✗ All other ports → DENY

Outbound:
  ✓ All traffic     to 0.0.0.0/0 (for API calls to Gemini, Telegram)
```

**Core Node Security Group**
```
Inbound:
  ✓ SSH (22)              from Admin IP only
  ✓ API (8000)            from Web SG + Monitor SG only
  ✓ Internal (8080)       from Web SG + Monitor SG only
  ✓ Node Exporter (9100)  from Monitor SG only
  ✗ All other ports       → DENY

Outbound:
  ✓ All traffic           to 0.0.0.0/0
```

### 6.2 Secrets Management

```
Credentials NEVER committed to Git:
  ✓ GEMINI_API_KEY        → Stored in agent_src/.env
  ✓ TELEGRAM_TOKEN        → Stored in agent_src/.env
  ✓ TELEGRAM_CHAT_ID      → Stored in agent_src/.env
  ✓ AWS credentials       → Stored in ~/.aws/credentials
  ✓ SSH keys              → Stored in ~/.ssh/

At runtime:
  ✓ Docker injects .env variables
  ✓ No secrets in container logs
  ✓ No secrets in metric exports
  ✓ AI Agent masks sensitive data in Telegram messages
```

### 6.3 Data Protection

```
Encryption:
  ✓ EBS volumes (gp3)     → Encrypted at rest
  ✓ HTTPS (443)           → Encrypted in transit (future)
  ✓ SSH (22)              → Key-based, no passwords

Data Retention:
  ✓ Prometheus metrics    → 30 days (configurable)
  ✓ Grafana dashboards    → Persistent in container volume
  ✓ Alert history         → 15 days default
  ✓ Logs                  → Container default (limited)

Access Control:
  ✓ SSH key authentication only (no password login)
  ✓ Grafana admin panel secured (admin/admin123 → change in production)
  ✓ API endpoints protected by Nginx
```

---

## 7. Operations Guide

### 7.1 Daily Operations

```bash
# Morning health check
curl http://52.74.118.8:9090/-/healthy && echo "✅ Prometheus OK"
curl http://52.74.118.8:9093/-/healthy && echo "✅ Alertmanager OK"
curl http://52.74.118.8:3000/api/health && echo "✅ Grafana OK"
curl http://18.136.112.28/api/health && echo "✅ API OK"

# View current alerts
curl http://52.74.118.8:9093/api/v1/alerts | jq '.data | length'

# Check instance IPs (from Terraform)
cd terraform && terraform output -raw elastic_ips
```

### 7.2 Troubleshooting

**Issue: Prometheus not scraping metrics**
```bash
# SSH to Monitor node
ssh -i ~/.ssh/id_rsa ec2-user@52.74.118.8

# Check Prometheus status
curl http://localhost:9090/api/v1/status/config | jq '.data.scrape_configs'

# Check target status
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets'
```

**Issue: Alerts not firing**
```bash
# Check alert rules
curl http://localhost:9090/api/v1/rules | jq '.data.groups[0].rules'

# Check recent alert evaluations
curl http://localhost:9090/api/v1/query?query=ALERTS | jq '.data'
```

**Issue: Telegram notifications not received**
```bash
# SSH to Monitor node
ssh -i ~/.ssh/id_rsa ec2-user@52.74.118.8

# Check AI Agent logs
docker logs ai-agent | tail -50

# Test webhook manually
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" \
  -d '{"status":"firing","alerts":[{"labels":{"alertname":"TestAlert"}}]}'
```

### 7.3 Accessing Services

**From Your Local Machine:**

```bash
# Grafana Dashboard (requires VPN or IP whitelist)
open http://52.74.118.8:3000
Login: admin / admin123

# Web Application (publicly available)
open http://18.136.112.28

# API Documentation
open http://18.136.112.28/api/docs
```

**If Access Fails:**

```bash
# 1. Verify your current IP
curl https://api.ipify.org

# 2. Check Terraform whitelist
cat terraform/terraform.tfvars | grep my_ip_cidr

# 3. Update if IP changed
# Edit terraform/terraform.tfvars
# my_ip_cidr = "YOUR_NEW_IP/32"

# 4. Re-apply Terraform
cd terraform
terraform plan
terraform apply -auto-approve

# 5. Wait 1-2 minutes for security group updates
```

### 7.4 Common Operations

```bash
# Restart all monitoring services
docker-compose -f platform-config/docker-compose.prod.yml restart

# View logs of specific service
docker logs -f prometheus
docker logs -f alertmanager
docker logs -f grafana
docker logs -f ai-agent

# Check disk usage
docker exec monitor-ai-01 df -h

# Backup Grafana dashboards
docker exec grafana grafana-cli admin export-dashboard dashboard-name
```

---

## 8. Deployment Files Reference

| File | Purpose | Location |
|------|---------|----------|
| provider.tf | AWS provider config | terraform/ |
| network.tf | VPC, subnet, IGW | terraform/ |
| security.tf | Security groups | terraform/ |
| compute.tf | EC2, Elastic IPs | terraform/ |
| terraform.tfvars | Configuration values | terraform/ |
| bootstrap.yml | OS setup | ansible/playbooks/ |
| deploy-complete-infrastructure.yml | Full deployment | ansible/playbooks/ |
| alert_rules.yml | Prometheus rules | ansible/config/ |
| alertmanager.yml | Alertmanager config | ansible/config/ |
| docker-compose.prod.yml | Production containers | platform-config/ |

---

## 9. Support & Documentation

- **Deployment**: See DEPLOYMENT_GUIDE.md
- **Service Startup**: See SERVICE_STARTUP_GUIDE.md
- **Ansible Guide**: See ANSIBLE_DEPLOYMENT_GUIDE.md
- **Troubleshooting**: See HOW_TO_CHECK_LOGS.md
- **Architecture Diagrams**: See diagram/ARCHITECTURE_DIAGRAMS.md

---

**Last Updated**: 2026-04-17  
**Version**: 1.0  
**Maintained By**: DevOps Team  
**Status**: ✅ Production Ready
