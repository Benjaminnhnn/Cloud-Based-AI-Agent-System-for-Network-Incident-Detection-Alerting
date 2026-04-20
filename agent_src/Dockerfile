FROM python:3.11-slim

WORKDIR /app

# Install curl and ping for health check and diagnostics
RUN apt-get update && apt-get install -y curl iputils-ping && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Start all monitoring components
ENTRYPOINT ["./docker-entrypoint.sh"]
