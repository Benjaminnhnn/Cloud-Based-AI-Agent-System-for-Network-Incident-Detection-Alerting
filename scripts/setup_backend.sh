#!/bin/bash

# FastAPI Backend Setup Script
# This script sets up and runs the FastAPI backend locally

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="${PROJECT_ROOT}/backend"

echo -e "${BLUE}🚀 FastAPI Backend Setup${NC}"
echo "================================"

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
cd "${BACKEND_DIR}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Display instructions
echo ""
echo -e "${GREEN}✓ Backend setup complete!${NC}"
echo ""
echo -e "${BLUE}To start the backend:${NC}"
echo "  1. cd to ${BACKEND_DIR}"
echo "  2. source venv/bin/activate"
echo "  3. python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo -e "${BLUE}API Documentation:${NC}"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - ReDoc: http://localhost:8000/redoc"
echo ""
