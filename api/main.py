# Health API QA Framework - Main Application
# FastAPI application with health-related endpoints

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting Health API QA Framework")
    logger.info("🎯 Health API ready for testing!")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Health API")

# FastAPI application
app = FastAPI(
    title="Health API QA Framework",
    description="""
    ## 🏥 Health API for QA Testing
    
    API completa para demonstração de testes automatizados em sistemas de saúde.
    
    ### Funcionalidades:
    - **Pacientes**: CRUD completo de pacientes
    - **Consultas**: Agendamento e gerenciamento de consultas
    - **Prontuários**: Registros médicos e histórico
    - **Autenticação**: JWT com roles e permissões
    - **Monitoramento**: Health checks e métricas
    
    ### Segurança:
    - Autenticação JWT
    - Rate limiting
    - CORS configurado
    - Headers de segurança
    - Validação de entrada
    """,
    version="1.0.0",
    contact={
        "name": "QA Engineering Team",
        "email": "qa-team@healthapi.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Security Middleware (simplified for demo)
# app.add_middleware(SecurityHeadersMiddleware)
# app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Sample endpoints for testing
@app.get("/api/v1/patients", tags=["Patients"])
async def get_patients():
    """Get all patients - Sample endpoint for testing"""
    return {
        "patients": [
            {"id": 1, "name": "João Silva", "age": 35, "email": "joao@email.com"},
            {"id": 2, "name": "Maria Santos", "age": 28, "email": "maria@email.com"}
        ],
        "total": 2
    }

@app.post("/api/v1/patients", tags=["Patients"])
async def create_patient(patient_data: dict):
    """Create new patient - Sample endpoint for testing"""
    return {
        "message": "Patient created successfully",
        "patient": {
            "id": 3,
            "name": patient_data.get("name", "Unknown"),
            "age": patient_data.get("age", 0),
            "email": patient_data.get("email", "")
        }
    }

@app.get("/api/v1/appointments", tags=["Appointments"])
async def get_appointments():
    """Get all appointments - Sample endpoint for testing"""
    return {
        "appointments": [
            {"id": 1, "patient_id": 1, "doctor": "Dr. Silva", "date": "2025-07-10", "time": "10:00"},
            {"id": 2, "patient_id": 2, "doctor": "Dr. Santos", "date": "2025-07-11", "time": "14:30"}
        ],
        "total": 2
    }

# Root endpoint
@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🏥 Health API QA Framework",
        "version": "1.0.0",
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None,
        "timestamp": time.time()
    }

# Health check endpoint
@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "health-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": "simulated",
        "timestamp": time.time(),
        "uptime": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
    }

# Readiness probe
@app.get("/ready", response_model=Dict[str, Any])
async def readiness_check():
    """Readiness probe for Kubernetes"""
    return {
        "status": "ready",
        "service": "health-api",
        "timestamp": time.time()
    }

# Liveness probe
@app.get("/live", response_model=Dict[str, Any])
async def liveness_check():
    """Liveness probe for Kubernetes"""
    return {
        "status": "alive",
        "service": "health-api",
        "timestamp": time.time()
    }

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    # This would typically return Prometheus format metrics
    return {
        "http_requests_total": 1000,
        "http_request_duration_seconds": 0.1,
        "database_connections_active": 5,
        "memory_usage_bytes": 104857600
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": time.time()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": time.time()
            }
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    app.state.start_time = time.time()
    logger.info("🎯 Health API startup completed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info"
    )
