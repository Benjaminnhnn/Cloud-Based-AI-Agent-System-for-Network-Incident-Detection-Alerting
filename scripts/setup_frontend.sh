#!/bin/bash

# Frontend Setup Script
# This script sets up and runs the React frontend locally

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

echo -e "${BLUE}⚛️  React Frontend Setup${NC}"
echo "================================"

# Check Node.js
echo -e "${BLUE}Checking Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js ${NODE_VERSION} found${NC}"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ npm ${NPM_VERSION} found${NC}"

# Create React app if it doesn't exist
if [ ! -d "${FRONTEND_DIR}" ]; then
    echo -e "${BLUE}Creating React app...${NC}"
    cd "${PROJECT_ROOT}"
    npx create-react-app frontend
fi

cd "${FRONTEND_DIR}"

# Create .env file
if [ ! -f ".env" ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
fi

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
npm install

echo -e "${GREEN}✓ Frontend setup complete!${NC}"
echo ""
echo -e "${BLUE}To start the frontend:${NC}"
echo "  1. cd to ${FRONTEND_DIR}"
echo "  2. npm start"
echo ""
echo -e "${BLUE}Frontend will be available at:${NC}"
echo "  http://localhost:3000"
echo ""
