# CI/CD Deployment Model Diagram

## 1. High-Level CI/CD Architecture

```
                    ┌──────────────────────────────────────────┐
                    │         GitHub Repository                │
                    │  (aws-hybrid)                            │
                    └────────────┬─────────────────────────────┘
                                 │
                    ┌────────────▼─────────────────┐
                    │   GitHub Actions             │
                    │   (CI/CD Workflows)          │
                    └────────────┬─────────────────┘
                                 │
                    ┌────────────▼──────────────────────────┐
                    │  1. CI Pipeline (ci.yml)              │
                    │  - Lint & Test                        │
                    │  - Build Docker Images                │
                    │  - Push to GHCR                       │
                    └────────────┬───────────────────────────┘
                                 │
                    ┌────────────▼────────────────────────────┐
                    │  GitHub Container Registry (GHCR)      │
                    │  - ghcr.io/hoang_viet/ai-agent:tag     │
                    │  - ghcr.io/hoang_viet/api-backend:tag  │
                    └────────────┬────────────────────────────┘
                                 │
                ┌────────────────┴────────────────────┐
                │                                     │
    ┌───────────▼──────────────┐      ┌──────────────▼──────────────┐
    │ CD Staging (cd-staging)  │      │ CD Production               │
    │ (Auto on develop push)   │      │ (Manual approval on tag)    │
    └───────────┬──────────────┘      └──────────────┬──────────────┘
                │                                     │
    ┌───────────▼──────────────┐      ┌──────────────▼──────────────┐
    │ Staging EC2 Instance     │      │ Production EC2 Instance     │
    │ - Deploy compose files   │      │ - Deploy compose files     │
    │ - Pull images from GHCR  │      │ - Pull images from GHCR    │
    │ - Health check           │      │ - Health check             │
    │ - Rollback if failed     │      │ - Rollback if failed       │
    └──────────────────────────┘      └────────────────────────────┘
```

## 2. Detailed Deployment Flow (automation/deploy.sh)

```
START
  │
  ├─► Parse Arguments: ENVIRONMENT, TAG
  │   (e.g., staging, v1.2.3)
  │
  ├─► Validate Environment Variable: GHCR_TOKEN
  │   (Required for image authentication)
  │
  ├─► Set Paths & Configuration
  │   - COMPOSE_FILE: release/docker-compose.${ENVIRONMENT}.yml
  │   - ENV_FILE: release/.env.${ENVIRONMENT}
  │   - STATE_FILE: release/.state/${ENVIRONMENT}.tag
  │
  ├─► Login to GHCR
  │   echo "${GHCR_TOKEN}" | docker login ghcr.io
  │
  ├─► Pull Latest Images from Registry
  │   docker compose -f ${COMPOSE_FILE} pull
  │   - ai-agent:${TAG}
  │   - api-backend:${TAG}
  │   - postgres, prometheus, alertmanager, etc.
  │
  ├─► Deploy Docker Compose Stack
  │   docker compose -f ${COMPOSE_FILE} \
  │                   --env-file ${ENV_FILE} up -d
  │
  ├─► Health Check Loop (18 retries × 10 seconds)
  │   for i in {1..18}; do
  │     Check: curl http://localhost:PORT/health
  │     if Success:
  │       ├─► Save TAG to STATE_FILE
  │       ├─► Print: "✓ Deployment successful"
  │       └─► EXIT 0
  │     else:
  │       └─► Sleep 10s, Retry
  │   done
  │
  ├─► Health Check Failed (After 18 retries = 180 seconds)
  │   ├─► Read Previous TAG from STATE_FILE
  │   │
  │   ├─► Rollback to Previous Version
  │   │   docker compose -f ${COMPOSE_FILE} \
  │   │                   --env-file ${ENV_FILE} up -d
  │   │   (But with PREVIOUS_TAG from state file)
  │   │
  │   ├─► Verify Rollback Health
  │   │
  │   └─► EXIT 1 (Failure)
  │
  └─► END
```

## 3. GitHub Workflows & Branch Strategy

```
Feature Branch Development
│
├─► feature/* branches
│   ├─► Any push: Trigger CI (Lint, Test, Build)
│   ├─► Status checks required for PR merge
│   └─► NOT deployed anywhere
│
├─► Pull Request to develop
│   ├─► CI workflow validates all checks pass
│   └─► Require review + approval
│
├─► Merge to develop Branch
│   ├─► Trigger CI workflow
│   ├─► Trigger CD STAGING workflow (AUTOMATIC)
│   │   └─► SSH to Staging EC2
│   │   └─► Run: ./automation/deploy.sh staging ${COMMIT_SHA:0:7}
│   ├─► Deploy to Staging Environment
│   ├─► Health check validates deployment
│   └─► Staging accessible for testing
│
├─► Create Release & Tag
│   ├─► Merge develop → main
│   ├─► Create Git Tag: vX.Y.Z
│   └─► Example: v1.2.3
│
├─► Tag Push/Creation
│   ├─► Trigger CI workflow
│   ├─► Trigger CD PRODUCTION workflow
│   │   ├─► Requires environment approval
│   │   │   (Manual gate in GitHub)
│   │   ├─► SSH to Production EC2
│   │   └─► Run: ./automation/deploy.sh production ${TAG}
│   └─► Deploy to Production (MANUAL APPROVAL)
│
└─► Production Live
    ├─► Health check validates deployment
    ├─► User traffic served from production
    └─► AI Agent & API Backend running

Workflow Timing:
├─► CI Pipeline: ~3-5 minutes (Lint, Test, Build, Push)
├─► CD Staging: ~2-3 minutes (Deploy + Health Check)
└─► CD Production: ~2-3 minutes (Deploy + Health Check)
    (Plus manual approval wait time)
```

## 4. CI/CD Components & Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│                   GitHub Actions Workflows                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 1. CI Workflow (.github/workflows/ci.yml)                │   │
│ │    - Trigger: Any push to feature/*, develop, main       │   │
│ │    - Trigger: Pull Requests                              │   │
│ │    - Tasks:                                              │   │
│ │      • Check Docker Compose syntax                       │   │
│ │      • Lint Python code (agent_src, demo-web/backend)   │   │
│ │      • Run unit tests                                    │   │
│ │      • Build Docker images                              │   │
│ │      • Tag: branch_name or commit_sha (for branches)    │   │
│ │      • Tag: vX.Y.Z (for tags from main)                 │   │
│ │      • Push to GHCR with authentication                 │   │
│ │    - Success: Pass status check for PR merge             │   │
│ │    - Failure: Prevent merge until fixed                 │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 2. CD Staging Workflow (.github/workflows/cd-staging.yml)│   │
│ │    - Trigger: Push to develop branch only                │   │
│ │    - Prerequisites: CI must pass                         │   │
│ │    - Tasks:                                              │   │
│ │      • Extract tag from commit SHA (first 7 chars)      │   │
│ │      • SSH into staging EC2 instance                    │   │
│ │      • Execute: automation/deploy.sh staging ${TAG}     │   │
│ │      • Wait for health check (180 seconds max)          │   │
│ │    - Status: Auto-deploy, no approval needed             │   │
│ │    - Rollback: Automatic if health check fails           │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 3. CD Production Workflow (.github/workflows/cd-prod.yml)│   │
│ │    - Trigger: Tag creation (vX.Y.Z) on main branch      │   │
│ │    - Trigger: Manual workflow dispatch                   │   │
│ │    - Prerequisites: CI must pass                         │   │
│ │    - Approval: REQUIRED environment approval in GitHub   │   │
│ │    - Tasks:                                              │   │
│ │      • SSH into production EC2 instance                 │   │
│ │      • Execute: automation/deploy.sh production ${TAG}  │   │
│ │      • Wait for health check (180 seconds max)          │   │
│ │    - Status: Manual deploy with approval gate            │   │
│ │    - Rollback: Automatic if health check fails           │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│               Docker Images Built & Stored                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ghcr.io/hoang_viet/ai-agent:TAG                               │
│  ├─► Built from: agent_src/Dockerfile                         │
│  ├─► Components: Python AI Agent Service                       │
│  ├─► Port: 8000 (staging: 18000)                              │
│  └─► Dependencies: Python, TensorFlow, Flask                  │
│                                                                 │
│  ghcr.io/hoang_viet/api-backend:TAG                            │
│  ├─► Built from: demo-web/backend/Dockerfile                  │
│  ├─► Components: FastAPI Backend Service                       │
│  ├─► Port: 8080 (staging: 18080)                              │
│  └─► Dependencies: Python, FastAPI, SQLAlchemy                │
│                                                                 │
│  ghcr.io/hoang_viet/frontend:TAG (if applicable)               │
│  ├─► Built from: demo-web/frontend/Dockerfile                 │
│  ├─► Components: React Frontend                                │
│  └─► Served by: Nginx on Web Node                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│          Deployment Configuration Management                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  release/docker-compose.staging.yml                            │
│  ├─► Services: ai-agent (port 18000), api-backend (18080)     │
│  ├─► Environment: Development/Testing                          │
│  ├─► Volumes: Local mount for data persistence                │
│  └─► Network: Internal bridge network                         │
│                                                                 │
│  release/docker-compose.production.yml                         │
│  ├─► Services: ai-agent (port 8000), api-backend (8080)       │
│  ├─► Environment: Production with optimizations                │
│  ├─► Volumes: Named volumes for data persistence               │
│  ├─► Health checks: Enabled with restart policies              │
│  └─► Network: External subnet with security group              │
│                                                                 │
│  release/.env.staging / release/.env.production                │
│  ├─► GHCR_OWNER: hoang_viet                                   │
│  ├─► GHCR_USERNAME: GitHub username                           │
│  ├─► GHCR_TOKEN: Registry authentication token                │
│  ├─► DATABASE_URL: Environment-specific                        │
│  └─► Other service configurations                              │
│                                                                 │
│  release/.state/staging.tag / production.tag                   │
│  ├─► Stores: Currently deployed image tag                     │
│  ├─► Purpose: Enable rollback to previous version             │
│  └─► Updated: After successful health check                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 5. Health Check & Rollback Mechanism

```
                    Deployment Initiated
                            │
                            ▼
                  ┌─────────────────────┐
                  │ Pull Docker Images  │
                  │ from GHCR (Tag: X)  │
                  └─────────┬───────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │ docker compose up   │
                  │ (Start containers)  │
                  └─────────┬───────────┘
                            │
                            ▼
                  ┌─────────────────────────────┐
                  │ Health Check Loop (18x)     │
                  │ curl /health endpoint       │
                  │ Retry every 10 seconds      │
                  └─────────┬───────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼ (SUCCESS after N retries)            ▼ (FAILED after 18x)
   ┌──────────────┐                     ┌──────────────────────┐
   │ Save Tag X   │                     │ Read Previous Tag Y  │
   │ to .state/   │                     │ from .state/         │
   │ Return EXIT0 │                     └──────┬───────────────┘
   └──────────────┘                            │
                                               ▼
                                   ┌────────────────────────────┐
                                   │ Rollback: Pull Tag Y       │
                                   │ docker compose up (Tag: Y)  │
                                   └──────┬─────────────────────┘
                                          │
                                          ▼
                                   ┌────────────────────────────┐
                                   │ Verify Rollback Health     │
                                   │ curl /health endpoint      │
                                   └──────┬─────────────────────┘
                                          │
                              ┌───────────┴────────────┐
                              │                        │
                      ▼ (OK)              ▼ (FAILED - Critical)
                  ┌──────────┐      ┌────────────────────────┐
                  │ Return   │      │ Alert Team             │
                  │ EXIT1    │      │ Manual Intervention    │
                  │ (Logged) │      │ Required               │
                  └──────────┘      └────────────────────────┘

Deployment Time: ~3-5 minutes per environment
- Image Pull: 30-60 seconds
- Container Startup: 10-30 seconds
- Health Checks: Up to 180 seconds (18 × 10s)
- Rollback (if needed): 30-60 seconds
```

## 6. Environment Configuration Summary

| Aspect | Staging | Production |
|--------|---------|-----------|
| **Branch Trigger** | `develop` | `main` (via tag vX.Y.Z) |
| **Deployment Method** | Auto on push | Manual approval required |
| **AI Agent Port** | 18000 | 8000 |
| **API Backend Port** | 18080 | 8080 |
| **Image Registry** | GHCR | GHCR |
| **Compose File** | `release/docker-compose.staging.yml` | `release/docker-compose.production.yml` |
| **Env File** | `release/.env.staging` | `release/.env.production` |
| **Health Check Endpoint** | `/health` (port 8000) | `/health` (port 8000) |
| **Health Check Timeout** | 180 seconds (18 retries) | 180 seconds (18 retries) |
| **Rollback on Failure** | Automatic | Automatic |
| **Approval Gate** | None | GitHub environment approval |
| **Intent** | Testing & validation | User-facing services |

## 7. Key Files in CI/CD Pipeline

```
.github/
├── workflows/
│   ├── ci.yml                    # Build, lint, test, push to GHCR
│   ├── cd-staging.yml            # Auto-deploy to staging (develop)
│   └── cd-production.yml         # Manual deploy to production (tags)
│
release/
├── docker-compose.staging.yml    # Staging environment services
├── docker-compose.production.yml # Production environment services
├── .env.staging                  # Staging environment variables
├── .env.production               # Production environment variables
└── .state/
    ├── staging.tag               # Current staging deployment tag
    └── production.tag            # Current production deployment tag
│
automation/
└── deploy.sh                     # Deployment script (pull, up, health check, rollback)
│
agent_src/
├── Dockerfile                    # AI Agent image definition
├── main.py                       # AI Agent application
├── requirements.txt              # Python dependencies
└── service_monitor.py            # Service monitoring logic
│
demo-web/
└── backend/
    ├── Dockerfile                # Backend API image definition
    ├── app/
    │   └── main.py               # FastAPI application
    └── requirements.txt          # Python dependencies
```

---

**Deployment Model Summary:**
- **Code → GitHub** (Developer pushes)
- **GitHub Actions** runs CI (build, test, lint)
- **Build artifacts** pushed to GHCR with semantic tags
- **Staging deployment** automatic on `develop` branch
- **Production deployment** manual with approval gate on version tags
- **Health checks** validate every deployment
- **Automatic rollback** to previous version if health check fails
- **State tracking** enables quick recovery from failures
