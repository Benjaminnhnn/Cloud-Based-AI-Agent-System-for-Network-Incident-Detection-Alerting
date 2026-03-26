#!/bin/bash

# PostgreSQL Setup Script
# This script sets up PostgreSQL with the AIOps database

set -e

echo "🔧 Setting up PostgreSQL..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create database and user
echo -e "${BLUE}Creating database user and database...${NC}"
sudo -u postgres psql << EOF
-- Drop existing user and database if they exist (for fresh setup)
DROP DATABASE IF EXISTS aiops_db;
DROP USER IF EXISTS aiops_user;

-- Create new user
CREATE USER aiops_user WITH PASSWORD 'aiops_pass';

-- Create database
CREATE DATABASE aiops_db OWNER aiops_user;

-- Grant privileges
ALTER ROLE aiops_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE aiops_db TO aiops_user;

-- Connect to database and grant schema privileges
\c aiops_db
GRANT ALL PRIVILEGES ON SCHEMA public TO aiops_user;
EOF

echo -e "${GREEN}✓ PostgreSQL user and database created${NC}"

# Initialize schema
echo -e "${BLUE}Initializing database schema...${NC}"
sudo -u postgres psql aiops_db < $(dirname "$0")/../database/init.sql

echo -e "${GREEN}✓ Database schema initialized${NC}"

# Load seed data
echo -e "${BLUE}Loading sample data...${NC}"
sudo -u postgres psql aiops_db < $(dirname "$0")/../database/seed.sql

echo -e "${GREEN}✓ Sample data loaded${NC}"

# Test connection
echo -e "${BLUE}Testing connection...${NC}"
psql -U aiops_user -d aiops_db -h localhost -c "SELECT COUNT(*) as user_count FROM users;"

echo -e "${GREEN}✓ Database setup complete!${NC}"
echo -e "${GREEN}Connection string: postgresql://aiops_user:aiops_pass@localhost:5432/aiops_db${NC}"
