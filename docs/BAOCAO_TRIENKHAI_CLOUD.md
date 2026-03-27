# TRIỂN KHAI MONITORING & AI ALERT HỆ THỐNG TRÊN PUBLIC CLOUD AWS

**Ngày báo cáo:** 28/03/2026  
**Dự án:** AIOps Banking Monitoring System  
**Trạng thái:** ✅ Hoàn thành triển khai giai đoạn 1

---

## 1. KHÁI NIỆM & MỤC ĐÍCH

### 1.1 Khái Niệm

Hệ thống này là một giải pháp **Monitoring & Alerting tập hợp (Unified Monitoring & Alerting Platform)** sử dụng công nghệ Open Source và Cloud-Native. Hệ thống:

- **Thu thập metrics** từ các hệ thống trong thời gian thực
- **Phát hiện sự cố** dựa trên các rule được định nghĩa sẵn
- **Phân tích tự động** bằng AI (Gemini 2.5 Flash)
- **Thông báo ngay lập tức** qua multiple channels (Telegram)
- **Visualize trạng thái** thông qua Grafana Dashboard

### 1.2 Mục Đích

| # | Mục Đích | Mô Tả |
|---|----------|-------|
| 1 | **Giám sát liên tục** | Theo dõi metrics hệ thống 24/7 (CPU, Memory, Disk, Network) |
| 2 | **Phát hiện sớm** | Cảnh báo khi có sự cố trước khi ảnh hưởng user |
| 3 | **AI Analysis** | Tự động phân tích nguyên nhân và đề xuất giải pháp |
| 4 | **Real-time Notification** | Thông báo team ngay khi có sự cố qua Telegram |
| 5 | **Centralized Dashboard** | Duy nhất một nơi để quản lý tất cả alert và metrics |
| 6 | **Reduce Alert Fatigue** | Nhóm (group) alert để tránh spam thông báo |

---

## 2. KIẾN TRÚC HỆ THỐNG

### 2.1 Sơ Đồ Kiến Trúc Tổng Quát

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS PUBLIC CLOUD                        │
│                                                                 │
│  ┌────────────────────┐  ┌────────────────────┐ ┌───────────┐  │
│  │  bank-web-01      │  │  bank-core-01      │ │ monitor- │  │
│  │  (18.139.198.122) │  │  (52.77.15.93)     │ │ ai-01    │  │
│  │                   │  │                    │ │ (18.142..│  │
│  │ Web App (3000)    │  │ API (8000)         │ │ 210.110) │  │
│  └────────────────────┘  └────────────────────┘ └───────────┘  │
│         │                        │                    │         │
│         └────────────────────────┼────────────────────┘         │
│                                  │                              │
│                                  ▼                              │
│         ┌───────────────────────────────────────┐              │
│         │    AWS VPC (10.10.0.0/16)            │              │
│         │  + Security Groups                   │              │
│         │  + Elastic IPs                       │              │
│         │  + Route Tables                      │              │
│         └───────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Thành Phần Hệ Thống

#### A. **Infrastructure Layer** (AWS)
- **VPC**: 10.10.0.0/16 với 2 public subnets
- **EC2 Instances**: 3 x t3.small
- **Security Groups**: Firewall rules cho phép traffic
- **Elastic IPs**: Static public IPs cho các instances
- **IAM Roles**: Quyền truy cập AWS resources

#### B. **Monitoring Layer** (monitor-ai-01)
```
┌──────────────────────────────────────────────┐
│          monitor-ai-01 (18.142.210.110)     │
├──────────────────────────────────────────────┤
│                     Docker                   │
│  ┌────────────────┐  ┌────────────────┐    │
│  │  Prometheus    │  │  AlertManager  │    │
│  │  (port 9090)   │  │  (port 9093)   │    │
│  └────────────────┘  └────────────────┘    │
│  ┌────────────────┐  ┌────────────────┐    │
│  │  Grafana       │  │  Node Exporter │    │
│  │  (port 3001)   │  │  (port 9100)   │    │
│  └────────────────┘  └────────────────┘    │
│  ┌────────────────────────────────────┐    │
│  │  AI Agent (FastAPI)                │    │
│  │  • Webhook Receiver                │    │
│  │  • Gemini AI Integration           │    │
│  │  • Telegram Bot Sender             │    │
│  │  (port 8000)                       │    │
│  └────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

#### C. **Data Collection** (mı instances)
- **Node Exporter**: Chạy trên tất cả EC2 instances
- **Metrics collected**:
  - CPU usage (user, system, idle)
  - Memory (used, free, available)
  - Disk I/O (read, write)
  - Network traffic
  - Process info
  - System load

#### D. **AI & Notification Layer**
- **Gemini 2.5 Flash API**: Phân tích chi tiết alert
- **Telegram Bot**: Gửi thông báo formatted

### 2.3 Quy Trình Xử Lý Alert (Alert Flow)

```
1. COLLECTION
   └─► Node Exporter (port 9100)
       Scrapes system metrics every 15s

2. STORAGE & EVALUATION
   └─► Prometheus (port 9090)
       • Time-series database
       • Evaluates alert rules every 30s
       • Stores metrics for 15 days

3. ALERT GENERATION
   └─► Alert Rules (5 defined)
       • HighCPUUsage (CPU > 80% for 5 min)
       • HighMemoryUsage (MEM > 80% for 5 min)
       • PrometheusDown (service down 1 min)
       • AIAgentDown (service down 2 min)
       • AlertManagerDown (service down 1 min)

4. ALERT ROUTING
   └─► AlertManager (port 9093)
       • Groups similar alerts
       • Deduplicates notifications
       • Routes to configured receivers

5. WEBHOOK DELIVERY
   └─► AI Agent Webhook (port 8000/webhook)
       Receives alert JSON payload

6. AI ANALYSIS
   └─► Gemini API
       • Analyzes alert content
       • Generates detailed explanation
       • Suggests remediation steps

7. NOTIFICATION
   └─► Telegram Bot
       • Formats message (max 1500 chars)
       • Sends to Telegram Chat
       • Includes alert details + AI analysis

8. VISUALIZATION
   └─► Grafana Dashboard (port 3001)
       • Real-time metrics display
       • Alert history
       • System health overview
```

### 2.4 Component Breakdown

| Component | Internal Port | External Port | Version | Purpose |
|-----------|---------------|---------------|---------|---------|
| **Prometheus** | 9090 | 9090 | v2.48.1 | Metrics collection & rules evaluation |
| **AlertManager** | 9093 | 9093 | latest | Alert routing & grouping |
| **Grafana** | 3000 | 3001 | latest | Metrics visualization |
| **Node Exporter** | 9100 | 9100 | v1.7.0 | System metrics collection |
| **AI Agent** | 8000 | 8000 | custom | Webhook + AI integration |

---

## 3. CÔNG NGHỆ TRIỂN KHAI

### 3.1 Cloud Infrastructure

| Công Nghệ | Công Dụng | Chi Tiết |
|----------|----------|---------|
| **AWS EC2** | Compute instances | t3.small (2 vCPU, 2GB RAM) |
| **AWS VPC** | Network isolation | 10.10.0.0/16 with security groups |
| **AWS Elastic IP** | Static public IPs | Non-changing IPs for all instances |
| **AWS Security Groups** | Firewall rules | Allow SSH(22), Prometheus(9090), etc. |

### 3.2 Infrastructure as Code

| Công Nghệ | Công Dụng | Chi Tiết |
|----------|----------|---------|
| **Terraform** | IaC for AWS | Provider AWS, EC2, VPC, Security Groups |
| **Ansible** | Configuration Management | Playbooks for deployment automation |
| **Bash Scripts** | Scripting | Pre-deployment setup & validation |

### 3.3 Monitoring & Observability

| Công Nghệ | Công Dụng | Chi Tiết |
|----------|----------|---------|
| **Prometheus** | Time-series metrics DB | 15-day retention, 15s scrape interval |
| **AlertManager** | Alert management | Groups, deduplicates, routes alerts |
| **Grafana** | Visualization | Dashboards, alert history, metrics |
| **Node Exporter** | Metrics collection | System metrics from all instances |

### 3.4 AI & Automation

| Công Nghệ | Công Dụng | Chi Tiết |
|----------|----------|---------|
| **Gemini 2.5 Flash** | AI Analysis | Google's generative AI for alert analysis |
| **FastAPI** | API Framework | Python web framework for AI Agent |
| **Python** | Programming | Core language for AI Agent logic |

### 3.5 Notification & Communication

| Công Nghệ | Công Dụng | Chi Tiết |
|----------|----------|---------|
| **Telegram Bot API** | Messaging | Send formatted alerts to Telegram Chat |
| **Webhooks** | Integration | AlertManager → AI Agent communication |

### 3.6 Containerization

| Công Nghệ | Công Dụng | Chi Tiết |
|----------|----------|---------|
| **Docker** | Container Runtime | Isolated environments for services |
| **Docker Compose** | Orchestration | Multi-container deployments |

---

## 4. ALERT RULES & THRESHOLDS

### 4.1 Alert Rules Defined

```yaml
📊 Alert: HighCPUUsage
   Condition: CPU utilization > 80% for 5 minutes
   Severity: WARNING
   Description: High CPU usage detected on the system

📊 Alert: HighMemoryUsage
   Condition: Memory utilization > 80% for 5 minutes
   Severity: WARNING
   Description: High memory usage detected

⚠️ Alert: PrometheusDown
   Condition: Prometheus service unresponsive for 1 minute
   Severity: CRITICAL
   Description: Prometheus monitoring service is down

⚠️ Alert: AIAgentDown
   Condition: AI Agent webhook receiver unresponsive for 2 minutes
   Severity: CRITICAL
   Description: AI alert analysis service is down

⚠️ Alert: AlertManagerDown
   Condition: AlertManager service unresponsive for 1 minute
   Severity: CRITICAL
   Description: Alert routing service is down
```

### 4.2 Alert Routing Rules

| Alert | Condition | Route | Action |
|-------|-----------|-------|--------|
| CPU/Memory | Any time | AlertManager | Immediately |
| Service Down (Critical) | Anytime | AlertManager → AI Agent | Immediate + Analysis |
| Resolved Alert | Any | AlertManager | Send "resolved" status |

---

## 5. CÁC TỆPCẤU HÌNH

### 5.1 Prometheus Configuration (`prometheus.yml`)

```yaml
global:
  scrape_interval: 15s        # Collect metrics every 15s
  evaluation_interval: 30s    # Evaluate alert rules every 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']  # Route to AlertManager

rule_files:
  - "alert_rules.yml"  # Load alert definitions

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['node_exporter:9100']
  
  - job_name: 'ai_agent'
    static_configs:
      - targets: ['ai-agent:8000']
```

### 5.2 AlertManager Configuration (`alertmanager.yml`)

```yaml
global:
  resolve_timeout: 5m  # Auto-resolve alert after 5 min if no activity

route:
  receiver: 'ai-agent'  # Default receiver
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s       # Wait 10s before sending grouped alerts
  group_interval: 10s   # Wait 10s between successive notifications
  repeat_interval: 12h  # Repeat same alert every 12 hours

receivers:
  - name: 'ai-agent'
    webhook_configs:
      - url: 'http://ai-agent:8000/webhook'  # AI Agent webhook endpoint
        send_resolved: true  # Send when alert resolves
```

### 5.3 Alert Rules (`alert_rules.yml`)

```yaml
groups:
  - name: aiops_alerts
    interval: 30s
    rules:
      - alert: HighCPUUsage
        expr: 'rate(node_cpu_seconds_total{mode!="idle"}[5m]) > 0.8'
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'High CPU usage'
          description: 'CPU above 80%'
      
      # ... more rules ...
```

### 5.4 Docker Compose (`docker-compose.yml`)

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./alert_rules.yml:/etc/prometheus/alert_rules.yml:ro
    restart: unless-stopped
  
  alertmanager:
    image: prom/alertmanager:latest
    ports: ["9093:9093"]
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    restart: unless-stopped
  
  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin123
    restart: unless-stopped
  
  node_exporter:
    image: prom/node-exporter:latest
    ports: ["9100:9100"]
    restart: unless-stopped
```

---

## 6. TRIỂN KHAI & DEPLOYMENT

### 6.1 Phương Pháp Triển Khai

| Phương Pháp | Công Cụ | Trạng Thái |
|----------|--------|----------|
| **Infrastructure** | Terraform | ✅ Triển khai thành công |
| **Configuration** | Ansible | ✅ Playbook hoàn chỉnh |
| **Containerization** | Docker Compose | ✅ All services running |
| **Deployment** | SSH + Manual Scripts | ✅ Complete |

### 6.2 Triển Khai Quy Trình

```bash
1. Git clone repository
   git clone https://github.com/aiops-bank/aws-hybrid.git

2. Terraform - Tạo infrastructure
   cd terraform
   terraform init
   terraform plan
   terraform apply

3. Ansible - Cấu hình hệ thống
   cd ansible
   ansible-playbook playbooks/bootstrap.yml
   ansible-playbook playbooks/ai_agent_deploy.yml
   ansible-playbook playbooks/monitoring.yml

4. Verify - Kiểm tra triển khai
   curl http://18.142.210.110:8000/health
   curl http://18.142.210.110:9090/-/healthy
   curl http://18.142.210.110:9093/-/healthy
```

### 6.3 Infrastructure Outputs

| Resource | Value | Purpose |
|----------|-------|---------|
| Monitor Elastic IP | 18.142.210.110 | Prometheus + AlertManager + AI Agent |
| Web Elastic IP | 18.139.198.122 | React Web Application |
| Core Elastic IP | 52.77.15.93 | FastAPI Backend |
| VPC CIDR | 10.10.0.0/16 | Private network |

---

## 7. DASHBOARDS & MONITORING

### 7.1 Grafana Access

- **URL**: http://18.142.210.110:3001
- **Username**: admin
- **Password**: admin123
- **Default Dashboard**: System Overview + Alert Status

### 7.2 Prometheus Metrics Exploration

- **URL**: http://18.142.210.110:9090
- **Query Examples**:
  - `node_cpu_seconds_total` - CPU time
  - `node_memory_MemAvailable_bytes` - Available memory
  - `node_filesystem_avail_bytes` - Free disk space
  - `up` - Service availability

### 7.3 AlertManager Console

- **URL**: http://18.142.210.110:9093
- **Features**: View active alerts, alert routing, silencing

---

## 8. API ENDPOINTS

### 8.1 AI Agent API (http://18.142.210.110:8000)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/health` | GET | Health check | ✅ Working |
| `/api/status` | GET | System status | ✅ Working |
| `/api/alerts` | GET | List alerts | ✅ Working |
| `/webhook` | POST | AlertManager webhook | ✅ Configured |
| `/metrics` | GET | Prometheus metrics | ✅ Available |

### 8.2 Webhook Request Format

```json
{
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "HighCPUUsage",
        "severity": "warning",
        "instance": "18.142.210.110:9100"
      },
      "annotations": {
        "summary": "High CPU usage",
        "description": "CPU above 80%"
      },
      "startsAt": "2026-03-27T16:00:00.000Z",
      "endsAt": "0001-01-01T00:00:00Z"
    }
  ],
  "groupLabels": {},
  "commonLabels": {},
  "commonAnnotations": {},
  "externalURL": "http://alertmanager:9093",
  "version": "4",
  "groupKey": "{}"
}
```

---

## 9. SECURITY & BEST PRACTICES

### 9.1 Security Measures

- ✅ Security Groups allow specific ports only
- ✅ Private subnets for internal traffic
- ✅ Elastic IPs for consistent access
- ✅ IAM roles for AWS access control
- ✅ API authentication via webhook signature (future)

### 9.2 High Availability Considerations

- 🔄 Multi-region deployment (future)
- 🔄 Database replication (future)
- 🔄 Load balancer for redundancy (future)
- 🔄 Alert deduplication to prevent spam

### 9.3 Scalability

- 📈 Horizontal scaling: Add more EC2 instances
- 📈 Vertical scaling: Upgrade instance types
- 📈 Prometheus retention: Configurable (currently 15 days)
- 📈 Alert rules: Easy to add/modify

---

## 10. TROUBLESHOOTING & MAINTENANCE

### 10.1 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Alerts not received | AlertManager down | Check: `docker ps` on monitor-ai-01 |
| High CPU alert spam | Rules too sensitive | Lower threshold or increase `for` duration |
| Prometheus data loss | Storage full | Check disk space, increase retention |
| Webhook timeout | Network issue | Verify security group allows port 8000 |

### 10.2 Monitoring Health

```bash
# Check all services running
ssh ec2-user@18.142.210.110 "docker ps | grep -E 'prometheus|alertmanager|grafana|node_exporter|ai-agent'"

# View Prometheus targets
curl http://18.142.210.110:9090/api/v1/targets

# View active alerts
curl http://18.142.210.110:9090/api/v1/alerts

# Check AlertManager configuration
curl http://18.142.210.110:9093/api/v1/status
```

---

## 11. KẾT LUẬN

Hệ thống monitoring & alerting AI-powered này cung cấp:

✅ **Real-time Monitoring** - Giám sát 24/7 hiệu suất hệ thống  
✅ **Intelligent Alerting** - AI phân tích tự động nguyên nhân sự cố  
✅ **Centralized Management** - Tất cả alert và metrics ở một chỗ  
✅ **Scalable Architecture** - Dễ dàng mở rộng cho thêm services  
✅ **Production Ready** - Triển khai thành công trên AWS Public Cloud  

Hệ thống sẵn sàng để:
- 🚀 Phát hiện sự cố sớm
- 🤖 Phân tích chi tiết bằng AI
- 📱 Thông báo team ngay lập tức
- 📊 Visualize trạng thái hệ thống

---

**Ngày cập nhật**: 28/03/2026  
**Trạng thái**: ✅ Production Ready
