#!/bin/bash

# Quick start script for local development
# This script starts all services locally for development

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 AIOps Full Stack - Local Development${NC}"
echo "========================================"
echo ""

# Check if services are running
check_postgres() {
    if psql -U aiops_user -d aiops_db -h localhost -c "SELECT 1;" &> /dev/null; then
        echo -e "${GREEN}✓ PostgreSQL is running${NC}"
        return 0
    else
        echo -e "${RED}✗ PostgreSQL is not running${NC}"
        return 1
    fi
}

check_backend() {
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo -e "${GREEN}✓ Backend is running${NC}"
        return 0
    else
        echo -e "${RED}✗ Backend is not running${NC}"
        return 1
    fi
}

check_frontend() {
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✓ Frontend is running${NC}"
        return 0
    else
        echo -e "${RED}✗ Frontend is not running${NC}"
        return 1
    fi
}

echo -e "${BLUE}Checking prerequisites...${NC}"
echo ""

# Check and setup PostgreSQL
echo -e "${YELLOW}PostgreSQL:${NC}"
if ! check_postgres; then
    echo -e "${YELLOW}Setting up PostgreSQL...${NC}"
    bash "${SCRIPT_DIR}/setup_db.sh"
    echo ""
fi
echo ""

# Check and setup Backend
echo -e "${YELLOW}Backend (FastAPI):${NC}"
if [ ! -d "${PROJECT_ROOT}/backend/venv" ]; then
    echo -e "${YELLOW}Setting up Backend...${NC}"
    bash "${SCRIPT_DIR}/setup_backend.sh"
fi

# Check and setup Frontend
echo -e "${YELLOW}Frontend (React):${NC}"
if [ ! -d "${PROJECT_ROOT}/frontend/node_modules" ]; then
    echo -e "${YELLOW}Setting up Frontend...${NC}"
    bash "${SCRIPT_DIR}/setup_frontend.sh"
fi

echo -e "${BLUE}======================================== ${NC}"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo -e "${BLUE}To start development:${NC}"
echo ""
echo -e "${YELLOW}Terminal 1 - Backend:${NC}"
echo "  cd ${PROJECT_ROOT}/backend"
echo "  source venv/bin/activate"
echo "  python -m uvicorn app.main:app --reload"
echo ""
echo -e "${YELLOW}Terminal 2 - Frontend:${NC}"
echo "  cd ${PROJECT_ROOT}/frontend"
echo "  npm start"
echo ""
echo -e "${BLUE}Access points:${NC}"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
