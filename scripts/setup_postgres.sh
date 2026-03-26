#!/bin/bash

# AWS Deployment Script for Database Server
# This script configures and deploys PostgreSQL on AWS EC2

set -e

echo "🚀 Setting up Database Server (PostgreSQL)..."

# Update system
sudo yum update -y
sudo yum install -y postgresql14-server postgresql14-contrib

# Initialize database
sudo /usr/pgsql-14/bin/postgresql-14-setup initdb

# Start and enable PostgreSQL
sudo systemctl start postgresql-14
sudo systemctl enable postgresql-14

# Wait for PostgreSQL to be ready
sleep 5

# Setup database and user
sudo -u postgres psql << 'EOF'
-- Create user
CREATE USER aiops_user WITH PASSWORD 'aiops_pass';

-- Create database
CREATE DATABASE aiops_db OWNER aiops_user;

-- Grant privileges
ALTER ROLE aiops_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE aiops_db TO aiops_user;

-- Connect to database and grant schema access
\c aiops_db
GRANT ALL PRIVILEGES ON SCHEMA public TO aiops_user;
EOF

# Configure PostgreSQL to accept remote connections
POSTGRES_CONFIG="/var/lib/pgsql/14/data/postgresql.conf"
POSTGRES_HBA="/var/lib/pgsql/14/data/pg_hba.conf"

# Update postgresql.conf
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" "$POSTGRES_CONFIG"

# Update pg_hba.conf to allow connections from application servers
sudo tee -a "$POSTGRES_HBA" > /dev/null <<EOF
# Application servers
host    aiops_db    aiops_user    0.0.0.0/0    md5
EOF

# Restart PostgreSQL to apply changes
sudo systemctl restart postgresql-14

# Create tables and seed data
sudo -u postgres psql aiops_db < /home/ec2-user/init.sql 2>/dev/null || true
sudo -u postgres psql aiops_db < /home/ec2-user/seed.sql 2>/dev/null || true

echo "✅ Database Server setup complete!"
echo "PostgreSQL listening on: 0.0.0.0:5432"
echo "Database: aiops_db"
echo "User: aiops_user"
