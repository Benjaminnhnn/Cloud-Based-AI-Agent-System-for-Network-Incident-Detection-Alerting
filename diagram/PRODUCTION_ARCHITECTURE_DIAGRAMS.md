# Production Architecture Diagrams

## 1. Overall AWS Infrastructure Diagram

Complete AWS VPC architecture showing all 3 nodes, security groups, and Elastic IPs.

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

### Key Points

- **3 EC2 instances** deployed in public subnet (10.10.1.0/24)
- **Elastic IPs** keep public IPs static even after stop/start
- **Security Groups** act as firewalls enforcing least-privilege access
- **Prometheus** scrapes all Node Exporters from Monitor node
- **All instances** can reach internet via NAT on Elastic IP
- **Admin IP whitelist** protects monitoring services from public access

---

## 2. Monitor Node - Detailed Monitoring Stack Diagram

Detailed view of the Monitor node services, data flow, and connections.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          Monitor Node (52.74.118.8)                              │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │              Container Orchestration (Docker)                            │   │
│  │  Host OS: Amazon Linux 2023 (t3.small) | Storage: 12 GB gp3 encrypted   │   │
│  │  CPU/Memory: Sufficient for monitoring workload                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                        MONITORING STACK DATA FLOW                        │   │
│  ├──────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                          │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │  │ STEP 1: METRICS COLLECTION (Every 15 seconds)                  │   │   │
│  │  ├─────────────────────────────────────────────────────────────────┤   │   │
│  │  │                                                                 │   │   │
│  │  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐   │   │   │
│  │  │  │ Web Node Exporter│  │ Core Node Exporter│ │ Monitor NE │   │   │   │
│  │  │  │ (18.136.112.28:  │  │ (54.255.94.179:  │ │ (localhost│   │   │   │
│  │  │  │      9100)       │  │      9100)       │ │   :9100)   │   │   │   │
│  │  │  └────────┬─────────┘  └────────┬─────────┘  └─────┬──────┘   │   │   │
│  │  │           │                     │                  │           │   │   │
│  │  │           └─────────────────────┼──────────────────┘           │   │   │
│  │  │                                 │                              │   │   │
│  │  │                                 ▼                              │   │   │
│  │  │                  ┌──────────────────────────┐                 │   │   │
│  │  │                  │   PROMETHEUS (9090)      │                 │   │   │
│  │  │                  │                          │                 │   │   │
│  │  │                  │ • Pulls metrics from 3NE │                 │   │   │
│  │  │                  │ • Stores time series data│                 │   │   │
│  │  │                  │ • Retention: 15 days     │                 │   │   │
│  │  │                  │ • Scrape interval: 15s   │                 │   │   │
│  │  │                  └────────────┬─────────────┘                 │   │   │
│  │  │                               │                              │   │   │
│  │  └───────────────────────────────┼──────────────────────────────┘   │   │
│  │                                  │                                  │   │
│  │  ┌───────────────────────────────┼──────────────────────────────┐   │   │
│  │  │ STEP 2: ALERT EVALUATION (Every 30 seconds)                 │   │   │
│  │  ├────────────────────────────────▼──────────────────────────────┤   │   │
│  │  │                                                               │   │   │
│  │  │              ┌──────────────────────────┐                     │   │   │
│  │  │              │   ALERT RULES ENGINE     │                     │   │   │
│  │  │              │                          │                     │   │   │
│  │  │              │ Rules (from alert_rules):│                     │   │   │
│  │  │              │ • HighCPUUsage (80%)     │                     │   │   │
│  │  │              │ • HighMemoryUsage (85%)  │                     │   │   │
│  │  │              │ • HighDiskUsage (85%)    │                     │   │   │
│  │  │              │ • WebEndpointDown        │                     │   │   │
│  │  │              │ • NetworkHighIO          │                     │   │   │
│  │  │              │                          │                     │   │   │
│  │  │              │ Evaluates: 30s intervals │                     │   │   │
│  │  │              │ Queries: TSDB + Rules    │                     │   │   │
│  │  │              │ Output: Alert Objects    │                     │   │   │
│  │  │              └────────────┬─────────────┘                     │   │   │
│  │  │                           │                                   │   │   │
│  │  │                    ┌──────▼────────┐                          │   │   │
│  │  │                    │ IF condition  │                          │   │   │
│  │  │                    │ met FOR 5m    │                          │   │   │
│  │  │                    │ THEN fire     │                          │   │   │
│  │  │                    │ alert         │                          │   │   │
│  │  │                    └──────┬────────┘                          │   │   │
│  │  │                           │                                   │   │   │
│  │  └───────────────────────────┼───────────────────────────────────┘   │   │
│  │                              │                                       │   │
│  │  ┌───────────────────────────▼───────────────────────────────────┐   │   │
│  │  │ STEP 3: ALERT ROUTING & NOTIFICATION (Immediate)            │   │   │
│  │  ├─────────────────────────────────────────────────────────────┤   │   │
│  │  │                                                             │   │   │
│  │  │         ┌────────────────────────────────┐                 │   │   │
│  │  │         │  ALERTMANAGER (9093)          │                 │   │   │
│  │  │         │                                │                 │   │   │
│  │  │         │ • Receives alerts from         │                 │   │   │
│  │  │         │   Prometheus                   │                 │   │   │
│  │  │         │ • Groups alerts by:            │                 │   │   │
│  │  │         │   - alertname                  │                 │   │   │
│  │  │         │   - severity                   │                 │   │   │
│  │  │         │   - instance                   │                 │   │   │
│  │  │         │ • group_wait: 10s              │                 │   │   │
│  │  │         │ • repeat_interval: 4h          │                 │   │   │
│  │  │         │                                │                 │   │   │
│  │  │         └────────────┬────────────────────┘                 │   │   │
│  │  │                      │                                      │   │   │
│  │  │                      │ [Webhook POST]                       │   │   │
│  │  │                      │ http://localhost:8000/webhook        │   │   │
│  │  │                      │ Payload: Alert JSON                  │   │   │
│  │  │                      │                                      │   │   │
│  │  │                      ▼                                      │   │   │
│  │  │         ┌────────────────────────────────┐                 │   │   │
│  │  │         │    AI AGENT (8000)             │                 │   │   │
│  │  │         │                                │                 │   │   │
│  │  │         │ • Webhook endpoint: /webhook   │                 │   │   │
│  │  │         │ • Parse alert JSON             │                 │   │   │
│  │  │         │ • Call Gemini 2.5 API          │                 │   │   │
│  │  │         │   (analyze alert)              │                 │   │   │
│  │  │         │ • Format response              │                 │   │   │
│  │  │         │ • Send to Telegram Bot API     │                 │   │   │
│  │  │         │                                │                 │   │   │
│  │  │         └────────┬─────────────┬─────────┘                 │   │   │
│  │  │                  │             │                           │   │   │
│  │  │   ┌──────────────┘             └─────────────┐             │   │   │
│  │  │   │                                          │             │   │   │
│  │  │   ▼ [HTTPS POST]                   ▼ [HTTPS POST]        │   │   │
│  │  │                                                             │   │   │
│  │  │ ┌────────────────────┐              ┌──────────────────┐   │   │   │
│  │  │ │ Google Gemini API  │              │ Telegram Bot API │   │   │   │
│  │  │ │                    │              │                  │   │   │   │
│  │  │ │ • Analyze alert    │              │ • Send message   │   │   │   │
│  │  │ │ • Generate summary │              │ • Chat ID        │   │   │   │
│  │  │ │ • Return response  │              │ • Notify admin   │   │   │   │
│  │  │ └────────────────────┘              └──────────────────┘   │   │   │
│  │  │                                                             │   │   │
│  │  │              ┌─────────────────────────────────┐            │   │   │
│  │  │              │ 💬 TELEGRAM NOTIFICATION       │            │   │   │
│  │  │              ├─────────────────────────────────┤            │   │   │
│  │  │              │ ⚠️ ALERT: HighCPUUsage         │            │   │   │
│  │  │              │                                 │            │   │   │
│  │  │              │ Server: bank-core-01            │            │   │   │
│  │  │              │ Value: CPU 92%                  │            │   │   │
│  │  │              │ Duration: 5 minutes              │            │   │   │
│  │  │              │                                 │            │   │   │
│  │  │              │ Analysis by Gemini:              │            │   │   │
│  │  │              │ "Possible high load..."          │            │   │   │
│  │  │              └─────────────────────────────────┘            │   │   │
│  │  │                                                             │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                  │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │ STEP 4: VISUALIZATION (Real-time, Admin Dashboard)      │   │   │
│  │  ├──────────────────────────────────────────────────────────┤   │   │
│  │  │                                                          │   │   │
│  │  │          ┌─────────────────────────────────┐             │   │   │
│  │  │          │   GRAFANA (3000)                │             │   │   │
│  │  │          │                                 │             │   │   │
│  │  │          │ Datasource: Prometheus (9090)   │             │   │   │
│  │  │          │ Query frequency: 5s             │             │   │   │
│  │  │          │ Time range: 6h default          │             │   │   │
│  │  │          │                                 │             │   │   │
│  │  │          │ Dashboards:                     │             │   │   │
│  │  │          │ 1. System Overview              │             │   │   │
│  │  │          │    - CPU, Memory, Disk          │             │   │   │
│  │  │          │    - Load, Process count        │             │   │   │
│  │  │          │                                 │             │   │   │
│  │  │          │ 2. Network & Performance        │             │   │   │
│  │  │          │    - Bandwidth in/out           │             │   │   │
│  │  │          │    - Packets, Errors            │             │   │   │
│  │  │          │                                 │             │   │   │
│  │  │          │ 3. Alert Monitoring             │             │   │   │
│  │  │          │    - Active alerts              │             │   │   │
│  │  │          │    - Alert timeline             │             │   │   │
│  │  │          │    - Alert frequency            │             │   │   │
│  │  │          │                                 │             │   │   │
│  │  │          │ Auth: admin/admin123            │             │   │   │
│  │  │          │ Access: Admin IP only           │             │   │   │
│  │  │          └─────────────────────────────────┘             │   │   │
│  │  │                                                          │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

                                 TIME FLOW
┌─────────────────────────────────────────────────────────────────────────────┐
│ T+0s:     Node Exporters expose metrics /metrics endpoint                   │
│ T+15s:    Prometheus scrapes all 3 Node Exporters (15s interval)            │
│ T+30s:    Prometheus evaluates alert rules (30s interval)                   │
│ T+30.5s:  Alert condition met (IF statement) → fires alert                  │
│ T+31s:    Alertmanager receives alert from Prometheus                       │
│ T+31.5s:  Alertmanager groups alert (10s wait: group_wait=10s)             │
│ T+41.5s:  Alertmanager routes to webhook: AI Agent /webhook                │
│ T+42s:    AI Agent receives POST request with alert JSON                    │
│ T+43s:    AI Agent calls Google Gemini API (1s processing)                 │
│ T+44s:    Gemini returns analysis result                                    │
│ T+44.5s:  AI Agent sends message to Telegram Bot API                       │
│ T+45s:    Admin receives Telegram notification ✅                           │
│ T+60s:    Grafana dashboard updates with latest metrics (5s refresh)        │
│ T+300s:   Repeat interval may send alert again (repeat_interval=4h)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Points

- **Metrics Flow**: Node Exporters → Prometheus (scrape every 15s)
- **Alert Evaluation**: Prometheus evaluates rules every 30s
- **Alert Routing**: Prometheus → Alertmanager → AI Agent webhook (webhook POST)
- **External Integration**: AI Agent calls Gemini API + Telegram Bot API
- **Visualization**: Grafana queries Prometheus every 5s for real-time dashboards
- **Total Alert Latency**: ~45 seconds from threshold breach to Telegram notification
- **All Services**: Run in Docker containers on single instance
- **Security**: Inbound traffic restricted to admin IP, outbound allowed for APIs

---


