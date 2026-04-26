# AWS Hybrid Cloud Monitoring

Complete deployment of an AI-powered monitoring and alerting platform for hybrid web workloads on AWS.

The system combines Terraform (infrastructure provisioning), Ansible (configuration management), Docker Compose (service orchestration), Prometheus + Alertmanager + Grafana (observability), and an AI Agent (Gemini + Telegram) for intelligent alert analysis.

## Project Overview

This repository provides:

- AWS infrastructure for monitor, web, and core nodes.
- Automated multi-phase deployment via Ansible playbooks.
- Local development stack with backend, frontend, database, and monitoring services.
- AI Agent webhook for alert enrichment and Telegram notifications.

## Architecture

- Monitor node: Prometheus, Alertmanager, Grafana.
- Web node: React frontend.
- Core node: FastAPI backend and app services.
- Node Exporter on all nodes for host metrics.
- Alert flow: Prometheus -> Alertmanager -> AI Agent -> Gemini -> Telegram.

## Repository Structure

```text
aws-hybrid/
|- terraform/              # AWS infrastructure as code
|- ansible/                # Playbooks, inventory, templates
|- platform-config/        # Docker Compose and monitoring configs
|- release/                # Production deployment manifests & configs
|- agent_src/              # AI agent source (FastAPI webhook)
|- demo-web/               # Full-stack demo application
|- automation/             # Deployment automation & orchestration scripts
|- diagram/                # Architecture, CI/CD, and deployment diagrams
`- README.md
```

### Key Automation Scripts

- `automation/deploy.sh` - Main deployment script (handles image pull, health checks, rollback)
- `automation/deploy-infrastructure.sh` - AWS infrastructure initialization
- `automation/ansible-deploy.sh` - Ansible wrapper for configuration management
- `automation/update-infrastructure.sh` - Infrastructure updates with IP sync

## Prerequisites

- Linux/macOS shell environment
- Docker and Docker Compose
- Python 3
- Terraform (for cloud provisioning)
- Ansible (for remote configuration)
- SSH private key configured at `~/.ssh/id_rsa`

## Configuration

Set AI Agent credentials before deployment.

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export TELEGRAM_TOKEN="your-telegram-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

Or create and edit the environment file used by the Ansible wrapper and production AI Agent stack:

```bash
cat > agent_src/.env << 'EOF'
GEMINI_API_KEY=your-gemini-api-key
TELEGRAM_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-chat-id
EOF
```

### GitHub Actions Secrets

Before running `CD Staging` or `CD Production`, verify these repository secrets in GitHub:

```text
Repository -> Settings -> Secrets and variables -> Actions -> Repository secrets
```

Required secrets:

| Secret | Purpose |
|--------|---------|
| `AWS_ACCESS_KEY_ID` | AWS automation credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS automation credentials |
| `SSH_HOST` | EC2 public IP used by the deployment workflow |
| `SSH_PORT` | SSH port, usually `22` |
| `SSH_PRIVATE_KEY` | Private key used by GitHub Actions to connect to EC2 |
| `GHCR_USERNAME` | GitHub Container Registry username |
| `GHCR_TOKEN` | GitHub token with package read/write access |

When Terraform recreates EC2 instances, update `SSH_HOST` with the new public IP before rerunning CD.

Local preflight:

```bash
ssh -i ~/.ssh/id_rsa -p 22 ec2-user@<SSH_HOST> 'echo auth-ok'
ssh -i ~/.ssh/id_rsa ec2-user@<SSH_HOST> 'docker --version && docker compose version'
```

## Quick Start

### Option 1: One-command deployment (recommended)

```bash
bash automation/deploy-infrastructure.sh
```

This script validates connectivity, checks Terraform state presence, and runs the full Ansible deployment playbook.

### Option 2: Ansible wrapper deployment

```bash
bash automation/ansible-deploy.sh
```

This wrapper loads credentials from `agent_src/.env`, runs bootstrap, then executes full deployment phases.

### Option 3: Manual Terraform + Ansible

```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan

cd ../ansible
ansible-playbook -i inventory.ini playbooks/deploy-complete-infrastructure.yml -v
```

## Local Development Stack

Start all local services:

```bash
docker-compose -f platform-config/docker-compose.dev.yml up -d
docker-compose -f platform-config/docker-compose.dev.yml ps
```

Stop all local services:

```bash
docker-compose -f platform-config/docker-compose.dev.yml down
```

## Production AI Agent Stack

Run only AI Agent in production mode:

```bash
docker-compose -f platform-config/docker-compose.prod.yml up -d
docker-compose -f platform-config/docker-compose.prod.yml ps
```

## Service Endpoints

### AWS deployment (from current inventory)

- Monitor node: `52.74.118.8`
- Web node: `18.136.112.28`
- Core node: `54.255.94.179`

Main URLs:

- Grafana: `http://52.74.118.8:3000`
- Prometheus: `http://52.74.118.8:9090`
- Alertmanager: `http://52.74.118.8:9093`
- Frontend: `http://18.136.112.28:3000`
- Backend API docs: `http://54.255.94.179:8000/docs`

### Local development

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- Alertmanager: `http://localhost:9093`
- Node Exporter: `http://localhost:9100/metrics`
- AI Agent webhook: `http://localhost:5000`

## Default Credentials

- Grafana username: `admin`
- Grafana password: `admin123`
- Local PostgreSQL: `aiops_user / aiops_pass`

## Monitoring Rules

The stack includes alert rules for:

- High CPU usage
- High memory usage
- Prometheus availability
- Alertmanager availability
- AI Agent availability

Rule files are managed in:

- `ansible/config/alert_rules.yml`
- `platform-config/prometheus.yml`

## Troubleshooting

- Check container states:

	```bash
	docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
	```

- Check Ansible connectivity:

	```bash
	ansible all -i ansible/inventory.ini -m ping
	```

- Follow service logs:

	```bash
	docker-compose -f platform-config/docker-compose.dev.yml logs -f
	```

## CI/CD Pipeline

The project uses GitHub Actions for automated building, testing, and deployment:

- **CI Workflow**: Lint, test, and build Docker images on all pushes to feature/develop/main branches
- **CD Staging**: Automatic deployment to staging EC2 when code is pushed to `develop` branch
- **CD Production**: Manual deployment to production with approval gate when tags are created on `main` branch
- **Health Checks**: Automatic validation of deployments with rollback capability

Check the deployed staging tag on EC2:

```bash
ssh -i ~/.ssh/id_rsa ec2-user@<SSH_HOST> \
  'cd /home/ec2-user/aws-hybrid && cat release/.state/staging.tag'
```

See `diagram/CI_CD_DEPLOYMENT_DIAGRAM.md` for complete CI/CD flow visualization.

## Documentation

- `diagram/ARCHITECTURE_DIAGRAMS.md` - AWS infrastructure and component diagrams
- `diagram/CI_CD_DEPLOYMENT_DIAGRAM.md` - GitHub Actions CI/CD pipeline and deployment model
- `diagram/D1_TEST_SCENARIO_REPORT.md` - Test scenario reports
- `diagram/MODULE_OVERVIEW_DIAGRAM.md` - Module structure overview
- `diagram/PRODUCTION_ARCHITECTURE_DIAGRAMS.md` - Detailed production environment diagrams
- `ANSIBLE_DEPLOYMENT_GUIDE.md` - Ansible playbook documentation
- `PRODUCTION_ARCHITECTURE_SUMMARY.md` - Production architecture details

## Contributing

1. Create a feature branch.
2. Implement and validate changes.
3. Open a pull request with deployment/test notes.

## License

This project is licensed under the MIT License.
