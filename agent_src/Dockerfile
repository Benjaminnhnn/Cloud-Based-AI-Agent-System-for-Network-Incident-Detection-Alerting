FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks and diagnostics
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default runtime for AI webhook service.
# Log watcher can run from the same image by overriding command in Compose.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
