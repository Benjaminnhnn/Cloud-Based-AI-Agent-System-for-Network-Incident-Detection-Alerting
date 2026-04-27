FROM python:3.11-slim

WORKDIR /app

# Install curl and ping for health check and diagnostics
RUN apt-get update && apt-get install -y curl iputils-ping && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default runtime for AI webhook service.
# Restructured main app is now in core/main.py
CMD ["python", "-m", "uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000"]
