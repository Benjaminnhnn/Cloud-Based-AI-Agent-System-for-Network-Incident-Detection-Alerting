#!/bin/bash

# Docker Compose Configuration
# Simple script to build and run services using Docker

set -e

echo "🐳 Docker Setup Script"

DOCKER_COMPOSE_DIR="$(cd "$(dirname "$0")"/.. && pwd)"

# Create docker-compose.yml
cat > "${DOCKER_COMPOSE_DIR}/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:14-alpine
    container_name: aiops-db
    environment:
      POSTGRES_USER: aiops_user
      POSTGRES_PASSWORD: aiops_pass
      POSTGRES_DB: aiops_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./database/seed.sql:/docker-entrypoint-initdb.d/seed.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aiops_user -d aiops_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Backend
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: aiops-api
    environment:
      DATABASE_URL: postgresql://aiops_user:aiops_pass@db:5432/aiops_db
      ENVIRONMENT: development
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # React Frontend
  web:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: aiops-web
    environment:
      REACT_APP_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - api
    volumes:
      - ./frontend:/app
    command: npm start

volumes:
  postgres_data:

networks:
  default:
    name: aiops-network
EOF

echo "✅ docker-compose.yml created"
echo ""
echo "To start all services:"
echo "  docker-compose -f ${DOCKER_COMPOSE_DIR}/docker-compose.yml up -d"
echo ""
echo "To stop all services:"
echo "  docker-compose -f ${DOCKER_COMPOSE_DIR}/docker-compose.yml down"
echo ""
