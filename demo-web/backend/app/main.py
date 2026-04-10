from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry
import os
import time
import urllib.error
import urllib.request
from app.routes import users
from app.config import settings

NODE_EXPORTER_URL = os.getenv("NODE_EXPORTER_URL", "http://127.0.0.1:9100/metrics")

# Prometheus metrics
REGISTRY = CollectorRegistry()
REQUEST_COUNT = Counter(
    'aiops_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)
REQUEST_LATENCY = Histogram(
    'aiops_api_request_duration_seconds',
    'API request latency',
    ['method', 'endpoint'],
    registry=REGISTRY
)
USERS_TOTAL = Counter(
    'aiops_users_total',
    'Total users registered',
    registry=REGISTRY
)

app = FastAPI(
    title="AIOps Demo API",
    description="Backend API for AIOps Demo Application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics middleware
@app.middleware("http")
async def add_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    
    return response

# Include routers
app.include_router(users.router)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "service": "AIOps Backend API"
    }

@app.get("/api/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(REGISTRY)

@app.get("/api/node-metrics", response_class=PlainTextResponse)
async def node_metrics():
    """Proxy node_exporter metrics when Prometheus cannot reach port 9100 directly"""
    try:
        with urllib.request.urlopen(NODE_EXPORTER_URL, timeout=5) as response:
            return response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail=f"node_exporter unavailable: {exc}") from exc

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "AIOps Demo API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health",
        "metrics": "/api/metrics"
    }

@app.on_event("startup")
async def startup_event():
    print("🚀 FastAPI Backend Started")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database: {settings.DATABASE_URL}")
    print("📊 Prometheus metrics available at /api/metrics")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 FastAPI Backend Shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
