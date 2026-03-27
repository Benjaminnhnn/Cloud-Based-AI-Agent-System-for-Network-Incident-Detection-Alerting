# AWS Hybrid Cloud - AI Monitoring & Alert System

**Complete Deployment of AI-Powered Monitoring Infrastructure on AWS EC2**

---

## 📋 Project Overview

End-to-end deployment of an intelligent monitoring system combining:
- **AWS Infrastructure**: EC2, VPC, Security Groups, Elastic IPs
- **Monitoring Stack**: Prometheus, AlertManager, Grafana, Node Exporter
- **AI Integration**: Google Gemini 2.5 Flash API for smart analysis
- **Communication**: Telegram Bot for instant notifications
- **Infrastructure as Code**: Terraform + Ansible for reproducible deployments

---

## 📁 Directory Structure

```
aws-hybrid/
│
├── 📂 docs/                          # 📄 Complete Documentation
│   ├── TRIỂN_KHAI_PUBLIC_CLOUD.docx  # Main technical report (Word)
│   ├── BAOCAO_TRIENKHAI_CLOUD.md      # Vietnamese technical documentation
│   ├── BAOCAO_TRIENKHAI_CLOUD.html    # HTML version of documentation
│   ├── ARCHITECTURE_DIAGRAMS.md       # System architecture & data flow diagrams
│   └── D1_TEST_SCENARIO_REPORT.md     # Test scenarios & validation results
│
├── 📂 terraform/                     # Infrastructure as Code
│   ├── provider.tf                    # AWS provider configuration
│   ├── variables.tf                   # Variable definitions
│   ├── compute.tf                     # EC2 instances, EBS volumes
│   ├── network.tf                     # VPC, subnets, routing
│   ├── security.tf                    # Security groups (UPDATED - port 8000)
│   ├── outputs.tf                     # Output values (IPs, DNS)
│   ├── terraform.tfstate              # Current state
│   └── terraform.tfvars               # Terraform variables
│
├── 📂 ansible/                       # Configuration Management
│   ├── ansible.cfg                    # Ansible configuration
│   ├── inventory.ini                  # Host inventory (3 EC2 instances)
│   ├── group_vars/all.yml             # Global variables
│   └── playbooks/
│       ├── bootstrap.yml              # System setup
│       ├── monitoring.yml             # Prometheus, AlertManager, Grafana
│       ├── ai_agent.yml               # AI service deployment
│       └── grafana-dashboards.yml     # Dashboard provisioning
│
├── 📂 demo-web/                      # Full Stack Web Application
│   ├── backend/                       # FastAPI Backend
│   │   ├── app/
│   │   │   ├── main.py                # Main FastAPI application
│   │   │   ├── config.py              # Configuration
│   │   │   ├── database.py            # Database connection
│   │   │   ├── models/                # SQLAlchemy models
│   │   │   ├── routes/                # API endpoints
│   │   │   ├── schemas/               # Pydantic schemas
│   │   │   └── services/              # Business logic
│   │   ├── Dockerfile                 # Backend container image
│   │   └── requirements.txt            # Python dependencies
│   │
│   ├── frontend/                      # React Frontend
│   │   ├── src/
│   │   │   ├── App.js                 # Main application
│   │   │   ├── index.js               # Entry point
│   │   │   ├── components/            # Reusable components
│   │   │   ├── pages/                 # Page components
│   │   │   ├── services/              # API client
│   │   │   └── styles/                # CSS stylesheets
│   │   ├── package.json               # Dependencies
│   │   ├── Dockerfile                 # Frontend container image
│   │   └── public/index.html           # HTML template
│
│   └── database/                      # PostgreSQL Database
│       ├── init.sql                   # Schema initialization
│       └── seed.sql                   # Sample data
│
├── 📂 config/                         # Configuration Files
│   ├── docker-compose.yml             # Multi-container orchestration (root)
│   ├── docker-compose.prod.yml        # Production compose file
│   ├── prometheus.yml                 # Prometheus scrape & alerting config
│   ├── nginx.conf                     # Nginx reverse proxy config
│   └── .env.prod.template             # Environment variables template
│
├── 📂 scripts/                        # Deployment & Setup Scripts
│   ├── setup_all.sh                   # Complete setup script
│   ├── setup_api.sh                   # API setup
│   ├── setup_backend.sh               # Backend setup
│   ├── setup_frontend.sh              # Frontend setup
│   ├── setup_docker.sh                # Docker setup
│   ├── setup_postgres.sh              # PostgreSQL setup
│   ├── setup_db.sh                    # Database setup
│   ├── setup_web.sh                   # Web server setup
│   ├── make_executable.sh             # Set execute permissions
│   └── update_infrastructure.sh        # Infrastructure update script (root)
│
├── 📂 agent_src/ (in playbooks)       # AI Agent Source Code
│   ├── main.py                        # FastAPI webhook receiver
│   ├── requirements.txt               # Dependencies
│   └── Gemini API integration         # AI analysis capability
│
├── 🐳 docker-compose.yml              # Main container orchestration (root)
├── 🔧 update-infrastructure.sh        # Infrastructure update (root)
├── 📝 .env.prod.template              # Environment template (root)
├── 📜 .gitignore                      # Git ignore rules
└── 📖 README.md                       # This file

```

---

## 🚀 Quick Start

### 1️⃣ **Infrastructure Deployment (AWS)**
```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### 2️⃣ **System Configuration (Ansible)**
```bash
cd ../ansible
ansible-playbook -i inventory.ini playbooks/bootstrap.yml
ansible-playbook -i inventory.ini playbooks/monitoring.yml
ansible-playbook -i inventory.ini playbooks/ai_agent.yml
```

### 3️⃣ **Local Development (Docker)**
```bash
docker-compose up -d
# Access services:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8080
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3001
# - AlertManager: http://localhost:9093
```

---

## 🎯 Key Features

✅ **3-Tier AWS Infrastructure**
- Monitor Server (18.142.210.110:9090 Prometheus)
- Web Server (18.139.198.122:3000 Frontend)  
- Core Server (52.77.15.93:8080 Backend)

✅ **Automated Alerting**
- 5 monitoring rules (CPU, Memory, Service health)
- AlertManager webhook integration
- Real-time Telegram notifications

✅ **AI-Powered Analysis**
- Google Gemini 2.5 Flash API integration
- Smart alert summarization
- Natural language insights

✅ **Comprehensive Monitoring**
- Prometheus metrics collection (15-day retention)
- 50+ pre-configured Grafana dashboards
- Real-time alerting with 30-second rule evaluation

✅ **Full-Stack Application**
- React frontend with user dashboard
- FastAPI backend with PostgreSQL
- Docker containerization for all services

---

## 📊 Alert Rules

| Rule | Condition | Action |
|------|-----------|--------|
| **HighCPUUsage** | CPU > 80% for 5m | Alert + Telegram |
| **HighMemoryUsage** | Memory > 85% for 5m | Alert + Telegram |
| **PrometheusDown** | No metrics for 5m | Alert + Telegram |
| **AIAgentDown** | No health response for 5m | Alert + Telegram |
| **AlertManagerDown** | No response for 5m | Alert + Telegram |

---

## 🔐 Security Configuration

**AWS Security Groups**:
- Port 22 (SSH): Restricted to admin IPs only
- Port 80 (HTTP): Open to all
- Port 443 (HTTPS): Open to all
- Port 9090 (Prometheus): Internal only / Updated for webhook
- Port 9093 (AlertManager): Internal only
- Port 3001 (Grafana): Internal only
- **Port 8000 (AI Agent Webhook): OPEN to AlertManager** ✅ FIXED

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| [docs/TRIỂN_KHAI_PUBLIC_CLOUD.docx](docs/TRIỂN_KHAI_PUBLIC_CLOUD.docx) | Main technical report (Word format) |
| [docs/BAOCAO_TRIENKHAI_CLOUD.md](docs/BAOCAO_TRIENKHAI_CLOUD.md) | Vietnamese technical documentation |
| [docs/BAOCAO_TRIENKHAI_CLOUD.html](docs/BAOCAO_TRIENKHAI_CLOUD.html) | Web-viewable documentation |
| [docs/ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md) | System architecture & diagrams |
| [docs/D1_TEST_SCENARIO_REPORT.md](docs/D1_TEST_SCENARIO_REPORT.md) | Test scenarios & validation |

---

## 🔧 Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| prometheus.yml | Metrics collection & alert rules | [config/](config/) |
| docker-compose.yml | Service orchestration | [config/](config/) or root |
| nginx.conf | Reverse proxy configuration | [config/](config/) |
| .env.prod.template | Environment variables | [config/](config/) |

---

## 📞 Service Endpoints

### **AWS Deployed Services**
- **Prometheus**: http://18.142.210.110:9090/
- **Grafana**: http://18.142.210.110:3001/
- **AlertManager**: http://18.142.210.110:9093/
- **AI Agent Webhook**: http://18.142.210.110:8000/webhook
- **Frontend**: http://18.139.198.122:3000/
- **Backend API**: http://52.77.15.93:8080/api/

### **Local Development**
- Frontend: http://localhost:3000
- Backend: http://localhost:8080
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- AlertManager: http://localhost:9093
- AI Agent: http://localhost:8000

---

## 🚨 Monitoring & Alerts

**Alert Flow**:
```
Metrics (Node Exporter)
    ↓
Prometheus (Scrape & Evaluate Rules)
    ↓
AlertManager (Route & Webhook)
    ↓
AI Agent (Webhook Receiver)  
    ↓
Google Gemini AI (Analysis)
    ↓
Telegram Bot (Notification)
    ↓
User's Phone (Instant Notification)
```

---

## 🛠️ Troubleshooting

**Issue**: Port 8000 not accessible
- **Fix**: Updated security group in `terraform/security.tf` with port 8000 ingress rule
- **Status**: ✅ Fixed and verified

**Issue**: Word document won't open  
- **Status**: ⚠️ Pending fix (XML encoding issue)
- **Workaround**: Use HTML version in `docs/BAOCAO_TRIENKHAI_CLOUD.html`

**Issue**: Services not starting
- **Solution**: Check Docker daemon, ensure ports are available, verify .env file

---

## 👤 Deployment Team

- **Infrastructure**: Terraform + AWS
- **Configuration**: Ansible
- **Monitoring**: Prometheus + Grafana + AlertManager
- **AI Integration**: Google Gemini API
- **Application**: React + FastAPI + PostgreSQL

---

## 📅 Recent Updates

✅ **Port 8000 Security Fix** - AlertManager webhook now accessible
✅ **AlertManager Integration** - Full alert routing implemented
✅ **AI Agent Deployment** - Gemini integration active  
✅ **Documentation Complete** - Full technical documentation in Vietnamese
✅ **Repository Cleanup** - Removed duplicates, organized structure

---

## 📝 License & Credits

This project combines:
- Terraform for IaC
- Ansible for configuration management
- Prometheus for monitoring
- Grafana for visualization
- FastAPI for backend
- React for frontend
- Google Gemini AI for intelligent analysis

---

**Last Updated**: 2024  
**Status**: ✅ Production Deployment Complete
