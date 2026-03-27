# ARCHITECTURE DIAGRAMS & VISUAL GUIDE

## 1. SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AWS PUBLIC CLOUD (ap-southeast-1)                │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  AWS VPC (10.10.0.0/16)                      │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────────────────────────────┐│  │
│  │  │  web-01 │ │ core-01 │ │   monitor-ai-01                  ││  │
│  │  │ 18.139  │ │ 52.77   │ │   18.142.210.110                 ││  │
│  │  │ 3000    │ │ 8000    │ │   ┌──────────────────────────────┤│  │
│  │  └─────────┘ └─────────┘ │   │ Services (Docker):            ││  │
│  │        │            │     │   │ • Prometheus (9090)          ││  │
│  │        └────┬───────┘     │   │ • AlertManager (9093)        ││  │
│  │             │             │   │ • Grafana (3001)             ││  │
│  │             ▼             │   │ • Node Exporter (9100)       ││  │
│  │        Node Exporter      │   │ • AI Agent (8000)            ││  │
│  │        (metrics:9100)     │   │                              ││  │
│  │             │             │   └──────────────────────────────┤│  │
│  │             └─────────────┼──────────────┐                    ││  │
│  │                           │              │                    ││  │
│  │  ┌──────────────────────────────────────▼──────────────────┐│  │
│  │  │              Security Groups (Firewall)                ││  │
│  │  │  Allow: SSH(22), HTTP(80), HTTPS(443)                 ││  │
│  │  │         Prometheus(9090), AlertManager(9093)          ││  │
│  │  │         Node Exporter(9100), AI Agent(8000)           ││  │
│  │  └────────────────────────────────────────────────────────┘│  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Elastic IPs (Static Public IPs)                 │  │
│  │  • monitor-ai-01: 18.142.210.110 (Monitoring & AI)         │  │
│  │  • bank-web-01:   18.139.198.122 (Web)                     │  │
│  │  • bank-core-01:  52.77.15.93 (API)                        │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. MONITORING STACK DETAILED VIEW

```
                    ┌─────────────────────────────────────────┐
                    │      monitor-ai-01 (18.142.210.110)     │
                    │      Docker Container Platform          │
                    └─────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
          ┌─────────▼──────┐ ┌─────┴──────┐ ┌─────┴──────────┐
          │  PROMETHEUS    │ │  ALERT     │ │  GRAFANA       │
          │  (9090)        │ │  MANAGER   │ │  (3001)        │
          │                │ │  (9093)    │ │                │
          │ • Time-series  │ │            │ │ • Dashboard    │
          │   database     │ │ • Routes   │ │ • Visualize    │
          │ • Alert rules  │ │   alerts   │ │ • History      │
          │ • Evaluation   │ │ • Groups   │ │ • Alerting     │
          │   every 30s    │ │   alerts   │ │                │
          │ • 15-day       │ │ • Webhook  │ │ • Data source: │
          │   retention    │ │   to       │ │   Prometheus   │
          └────┬─────┬─────┘ │   webhook  │ └────────────────┘
               │     │       └─────┬──────┘
               │     │             │
      ┌────────▼─────▼─────────────▼────────┐
      │    NODE EXPORTER (9100)             │
      │                                     │
      │ Collects System Metrics:            │
      │ • CPU (user, system, idle)          │
      │ • Memory (used, free, available)    │
      │ • Disk I/O (read, write, time)      │
      │ • Network (in, out, errors)         │
      │ • Load average                      │
      │ • Process count                     │
      │ Scraped by Prometheus every 15s     │
      └─────┬──────────────────────┬────────┘
            │                      │
      ┌─────▼──────┐        ┌──────▼──────┐
      │  Instances │        │   External  │
      │  (Prod)    │        │   Systems   │
      │            │        │             │
      │ • web-01   │        │ • AWS API   │
      │ • core-01  │        │ • Logs      │
      │ • monitor  │        │ • Traces    │
      └────────────┘        └─────────────┘
```

---

## 3. ALERT PROCESSING FLOW

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ALERT PROCESSING PIPELINE                      │
└─────────────────────────────────────────────────────────────────────┘

STEP 1: METRICS COLLECTION
┌──────────────────────────────────┐
│       System Metrics             │
├──────────────────────────────────┤
│ • CPU Usage: 45%                 │
│ • Memory: 62% used               │
│ • Disk: 78% used                 │
│ • Network I/O: 50Mbps            │
└──────────────────────────────────┘
          │ (every 15 seconds)
          ▼
┌──────────────────────────────────┐
│    Node Exporter (9100)          │
│    Converts to Prometheus format │
└────┬─────────────────────────────┘
     │
     ▼ (scrape every 15s)

STEP 2: METRICS STORAGE & EVALUATION
┌──────────────────────────────────┐
│    Prometheus (9090)             │
│ Time-Series Database             │
├──────────────────────────────────┤
│ • Stores metrics with timestamps │
│ • Indexes by labels              │
│ • Evaluates alert rules          │
│   (every 30 seconds)             │
└────┬─────────────────────────────┘
     │
     ▼ (evaluation interval: 30s)

STEP 3: ALERT RULES EVALUATION
┌──────────────────────────────────────────────┐
│ Alert Rules (5 Defined):                     │
├──────────────────────────────────────────────┤
│ Rule 1: CPU > 80% for 5 min                  │
│         Current: 45%  ✅ OK                  │
│                                              │
│ Rule 2: Memory > 80% for 5 min               │
│         Current: 62%  ✅ OK                  │
│                                              │
│ Rule 3: Prometheus Service Down              │
│         Status: UP 🟢  ✅ OK                 │
│                                              │
│ Rule 4: AIAgent Service Down                 │
│         Status: UP 🟢  ✅ OK                 │
│                                              │
│ Rule 5: AlertManager Service Down            │
│         Status: UP 🟢  ✅ OK                 │
└────┬─────────────────────────────────────────┘
     │
     ▼ (if any alert fires)

STEP 4: ALERT GENERATION
┌──────────────────────────────────────────────┐
│ Alert Fired: HighCPUUsage                    │
├──────────────────────────────────────────────┤
│ Status: firing                               │
│ Severity: warning                            │
│ Instance: web-01 (18.139.198.122)            │
│ Value: 85%                                   │
│ Start time: 2026-03-28 10:30:00 UTC         │
└────┬─────────────────────────────────────────┘
     │
     ▼ (send to AlertManager)

STEP 5: ALERT ROUTING & GROUPING
┌──────────────────────────────────────────────┐
│    AlertManager (9093)                       │
├──────────────────────────────────────────────┤
│ • Receives alert                             │
│ • Groups by: alertname, severity, instance   │
│ • Deduplicates (if already notified)         │
│ • Routes to configured receiver              │
│   → webhook_configs:                         │
│     url: http://ai-agent:8000/webhook       │
└────┬─────────────────────────────────────────┘
     │
     ▼ (HTTP POST with alert JSON)

STEP 6: WEBHOOK DELIVERY
┌──────────────────────────────────────────────┐
│    HTTP POST /webhook                        │
│    Payload: Alert JSON                       │
├──────────────────────────────────────────────┤
│ {                                            │
│   "status": "firing",                        │
│   "alerts": [...],                           │
│   "groupLabels": {},                         │
│   "commonLabels": {},                        │
│   "commonAnnotations": {}                    │
│ }                                            │
└────┬─────────────────────────────────────────┘
     │
     ▼ (received by AI Agent)

STEP 7: AI ANALYSIS
┌──────────────────────────────────────────────┐
│    AI Agent (FastAPI) /webhook               │
│    Processes Alert JSON                      │
├──────────────────────────────────────────────┤
│ 1. Parse alert data                          │
│ 2. Format for Gemini API                     │
│ 3. Call Google Gemini 2.5 Flash              │
│ 4. Get AI analysis response                  │
│ 5. Truncate to 1500 chars                    │
│ 6. Format for Telegram                       │
└────┬─────────────────────────────────────────┘
     │
     ▼ (API call to Google)

STEP 8: GEMINI AI ANALYSIS
┌──────────────────────────────────────────────┐
│    Google Gemini 2.5 Flash API               │
│    Generative AI Analysis                    │
├──────────────────────────────────────────────┤
│ Input: "Alert: HighCPUUsage on web-01        │
│         CPU: 85% for 5 minutes.               │
│         Instance: bank-web-01"               │
│                                              │
│ Output: "This high CPU usage on web-01 is    │
│ likely caused by increased traffic or a      │
│ memory leak in the application. Check:       │
│ 1. Traffic stats (curl web-01:3000/metrics) │
│ 2. Application logs for errors               │
│ 3. Consider scaling horizontally..."        │
└────┬─────────────────────────────────────────┘
     │
     ▼ (formatted message)

STEP 9: NOTIFICATION SENDING
┌──────────────────────────────────────────────┐
│    Telegram Bot API                          │
│    Send Formatted Message                    │
├──────────────────────────────────────────────┤
│ To: DevOps Telegram Chat                     │
│                                              │
│ ⚠️ HIGH CPU USAGE - web-01                  │
│ ────────────────────────────────            │
│ Severity: WARNING                            │
│ Alert: HighCPUUsage                          │
│ Value: 85%                                   │
│ Duration: 5 minutes                          │
│ Instance: bank-web-01 (18.139.198.122)      │
│                                              │
│ [AI Analysis]:                               │
│ Likely causes: Increased traffic or          │
│ memory leak. Check application logs.         │
│                                              │
│ Actions:                                     │
│ 1. View metrics: 18.142.210.110:9090        │
│ 2. SSH: ssh ec2-user@18.139.198.122         │
│ 3. Scale: terraform apply -auto-approve     │
└────┬─────────────────────────────────────────┘
     │
     ▼

STEP 10: VISUALIZATION
┌──────────────────────────────────────────────┐
│    Grafana Dashboard (3001)                  │
│    Alert Displayed in Real-time              │
├──────────────────────────────────────────────┤
│ • Alert name displayed                       │
│ • Current value: 85% CPU                     │
│ • Historical graph shown                     │
│ • Threshold line at 80%                      │
│ • Time-series trend visible                  │
│ • Acknowledge/Silence options                │
└──────────────────────────────────────────────┘
```

---

## 4. COMPONENT INTERACTION DIAGRAM

```
┌────────────────────────────────────────────────────────────────┐
│              COMPONENT INTERACTION MATRIX                      │
└────────────────────────────────────────────────────────────────┘

From ↓ → To    │Prometheus│AlertMgr│ Grafana│AI-Agent│Telegram│
───────────────┼──────────┼────────┼────────┼────────┼────────┤
Prometheus     │    -     │  →(1)  │  ←(2) │   -    │   -    │
               │  alerts  │  fires │ query │        │        │
───────────────┼──────────┼────────┼────────┼────────┼────────┤
AlertManager   │    ←     │    -   │   →   │  →(3)  │   -    │
               │  config  │        │ status│webhook │        │
───────────────┼──────────┼────────┼────────┼────────┼────────┤
Grafana        │    →     │    ←   │   -   │   →(4) │   -    │
               │  query   │  alerts│       │ status │        │
───────────────┼──────────┼────────┼────────┼────────┼────────┤
AI-Agent       │    →     │    ←   │   -   │   -    │  →(5)  │
               │  metrics │ webhook│       │        │apikey  │
───────────────┼──────────┼────────┼────────┼────────┼────────┤
Telegram       │    -     │    -   │   -   │   ←    │   -    │
               │          │        │       │message │        │
───────────────┼──────────┼────────┼────────┼────────┼────────┤
Node Exporter  │    ←     │    -   │   -   │   -    │   -    │
               │  scrape  │        │       │        │        │
───────────────┴──────────┴────────┴────────┴────────┴────────┘

Legend:
(1) Send alert to AlertManager (firing)
(2) Query metrics from Prometheus
(3) Webhook POST with alert JSON
(4) Status check API
(5) Send notification message
→  = Outbound connection
←  = Inbound connection
```

---

## 5. NETWORK TOPOLOGY

```
                    ┌─ INTERNET ─┐
                    │  (0.0.0.0) │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼────┐         ┌───▼────┐        ┌───▼──────┐
    │ Web    │         │ Core   │        │ Monitor  │
    │ Portal │         │ APIs   │        │ & AI     │
    └────────┘         └────────┘        └──────────┘
   (Elastic IP)      (Elastic IP)       (Elastic IP)
   18.139.198.122     52.77.15.93      18.142.210.110
   
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │   AWS VPC   │
                    │10.10.0.0/16 │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼─┐          ┌────▼─┐         ┌────▼─┐
    │ Pub  │          │ Pub  │         │ Pub  │
    │ Sub1 │          │ Sub2 │         │ Sub3 │
    │10.10 │          │10.10 │         │10.10 │
    │ .0/24│          │ .1/24│         │ .2/24│
    └──────┘          └──────┘         └──────┘
```

---

## 6. DATA FLOW DIAGRAM (DETAILED)

```
TIME: 10:30 - CPU SPIKED TO 85% ON web-01

10:30:00 ────────────────────────────────────────────────────────
         Node Exporter detects CPU = 85%
         └─→ Prometheus (scraped at next interval)

10:30:15 ────────────────────────────────────────────────────────
         Prometheus scrapes Node Exporter
         Stores: node_cpu{instance="web-01"} = 0.85
         └─→ Waits for next alert evaluation

10:30:30 ────────────────────────────────────────────────────────
         Prometheus EVALUATION CYCLE:
         • Check: rate(cpu > 0.80) == true
         • Check: duration > 5 min == false (only 30s elapsed)
         • Result: Alert NOT FIRED (waiting for 5 min threshold)

10:35:00 ────────────────────────────────────────────────────────
         CPU still 85% (5+ minutes)
         Prometheus EVALUATION:
         • rate(cpu > 0.80) == true ✓
         • duration > 5 min == true ✓
         • Result: ALERT FIRES! 🔴

10:35:05 ────────────────────────────────────────────────────────
         AlertManager receives alert
         • Groups by alertname + instance + severity
         • Deduplicates (first time, so send)
         • Routes to webhook receiver
         └─→ HTTP POST to ai-agent:8000/webhook

10:35:07 ────────────────────────────────────────────────────────
         AI Agent receives webhook
         • Parses JSON alert
         • Calls Gemini API with alert context
         └─→ Waits for Gemini response (~2 sec)

10:35:09 ────────────────────────────────────────────────────────
         Gemini API returns analysis:
         "High CPU likely due to:
          1. Increased web traffic
          2. Memory leak in app
          Recommend: Check logs, scale up"
         └─→ Format message for Telegram

10:35:10 ────────────────────────────────────────────────────────
         AI Agent sends to Telegram Bot API
         Message: ⚠️ HIGH CPU on web-01 (85%)
                  AI says: Check logs or scale...
         └─→ Bot sends to DevOps chat

10:35:12 ────────────────────────────────────────────────────────
         DevOps team receives notification on Telegram 📱
         
         Team actions:
         1. Click link to Grafana dashboard
         2. View metrics in detail
         3. SSH to web-01 to investigate
         4. Find memory leak in Python code
         5. Deploy hotfix
         6. CPU returns to normal

10:40:00 ────────────────────────────────────────────────────────
         CPU drops back to 25%
         Prometheus detects: rate(cpu > 0.80) == false
         └─→ Alert transitions to RESOLVED

10:40:05 ────────────────────────────────────────────────────────
         AlertManager sends RESOLVED notification
         Telegram: ✅ HIGH CPU RESOLVED on web-01
         └─→ Team informed
```

---

## 7. SECURITY & COMPLIANCE LAYERS

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────┘

LAYER 1: NETWORK SECURITY
┌────────────────────────────────────────┐
│ AWS Security Groups (Firewall)         │
│                                        │
│ Monitor SG:                            │
│ ✓ Allow SSH (22) from MY_IP/32         │
│ ✓ Allow Prometheus (9090) from 0.0.0   │
│ ✓ Allow AlertManager (9093) from 0.0.0 │
│ ✓ Allow AI Agent (8000) from 0.0.0     │
│ ✓ Allow Grafana (3001) from 0.0.0      │
│ ✗ Deny all other inbound               │
│                                        │
│ Web SG:                                │
│ ✓ Allow HTTP (80) from 0.0.0           │
│ ✓ Allow HTTPS (443) from 0.0.0         │
│ ✗ Deny all other                       │
└────────────────────────────────────────┘

LAYER 2: INFRASTRUCTURE SECURITY
┌────────────────────────────────────────┐
│ AWS IAM Roles & Policies               │
│                                        │
│ EC2 Instance Roles:                    │
│ • Minimal permissions (least privilege)│
│ • Access to CloudWatch API only        │
│ • No direct AWS console access         │
│ • Credentials rotated automatically    │
└────────────────────────────────────────┘

LAYER 3: APPLICATION SECURITY
┌────────────────────────────────────────┐
│ Prometheus & AlertManager              │
│                                        │
│ • No authentication (internal only)    │
│ • Data stored in ephemeral storage     │
│ • No sensitive data in logs            │
│ • TLS for API calls (future)           │
└────────────────────────────────────────┘

LAYER 4: DATA SECURITY
┌────────────────────────────────────────┐
│ Credentials Management                 │
│                                        │
│ .env files:                            │
│ • GEMINI_API_KEY (stored in .env)      │
│ • TELEGRAM_TOKEN (stored in .env)      │
│ • TELEGRAM_CHAT_ID (stored in .env)    │
│ • NOT committed to Git                 │
│ • NOT visible in logs                  │
│ • Injected at runtime via Docker       │
└────────────────────────────────────────┘

LAYER 5: MONITORING SECURITY
┌────────────────────────────────────────┐
│ Audit & Logging                        │
│                                        │
│ • All API calls logged                 │
│ • Alert history stored (15 days)       │
│ • Webhook requests audited             │
│ • Error logs available                 │
│ • No PII in logs                       │
└────────────────────────────────────────┘
```

---

## 8. DEPLOYMENT TIMELINE

```
Phase 1: Infrastructure Setup (Week 1)
├─ Day 1: AWS Account setup
│         VPC creation (10.10.0.0/16)
│         Security Groups configuration
├─ Day 2: Terraform code written
│         EC2 instances provisioned (3x)
│         Elastic IPs allocated
├─ Day 3: Ansible roles created
│         Docker installed on all instances
│         Network connectivity tested
└─ Day 4: Infrastructure verified ✅

Phase 2: Monitoring Setup (Week 2)
├─ Day 1: Prometheus deployed
│         Alert rules configured (5 rules)
│         retention set to 15 days
├─ Day 2: AlertManager deployed
│         Webhook routing configured
│         Grouping rules defined
├─ Day 3: Grafana deployed
│         Prometheus datasource added
│         Dashboards created
├─ Day 4: Node Exporter deployed
│         Prometheus scrape targets added
│         Metrics verified
└─ Day 5: Monitoring stack verified ✅

Phase 3: AI & Notification Setup (Week 3)
├─ Day 1: AI Agent FastAPI app created
│         Webhook endpoint implemented
│         Health check endpoint
├─ Day 2: Gemini integration tested
│         API key configured
│         Prompt engineering done
├─ Day 3: Telegram Bot integration
│         Bot token configured
│         Message formatting
├─ Day 4: End-to-end testing
│         Alert flow verified
│         Notifications received
└─ Day 5: System production ready ✅

Phase 4: Documentation & Training (Week 4)
├─ Day 1: Architecture documentation
├─ Day 2: Deployment guide
├─ Day 3: Troubleshooting guide
└─ Day 4: Team training ✅
```

---

**Document Generated**: March 28, 2026  
**Version**: 1.0  
**Status**: ✅ Complete
