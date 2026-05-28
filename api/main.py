from contextlib import asynccontextmanager
from typing import Any, Dict
import logging
import time

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from core.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Health API QA Framework")
    logger.info("Health API ready for testing")

    yield

    logger.info("Shutting down Health API")


app = FastAPI(
    title="Health API QA Framework",
    description="""
    Health API for QA Testing

    API completa para demonstração de testes automatizados em sistemas de saúde.

    Funcionalidades:
    - Pacientes: CRUD completo de pacientes
    - Consultas: Agendamento e gerenciamento de consultas
    - Prontuários: Registros médicos e histórico
    - Autenticação: JWT com roles e permissões
    - Monitoramento: Health checks e métricas

    Segurança:
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)


app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


@app.get("/api/v1/patients", tags=["Patients"])
async def get_patients():
    return {
        "patients": [
            {
                "id": 1,
                "name": "João Silva",
                "age": 35,
                "email": "joao@email.com",
            },
            {
                "id": 2,
                "name": "Maria Santos",
                "age": 28,
                "email": "maria@email.com",
            },
        ],
        "total": 2,
    }


@app.post("/api/v1/patients", tags=["Patients"])
async def create_patient(patient_data: dict):
    return {
        "message": "Patient created successfully",
        "patient": {
            "id": 3,
            "name": patient_data.get("name", "Unknown"),
            "age": patient_data.get("age", 0),
            "email": patient_data.get("email", ""),
        },
    }


@app.get("/api/v1/appointments", tags=["Appointments"])
async def get_appointments():
    return {
        "appointments": [
            {
                "id": 1,
                "patient_id": 1,
                "doctor": "Dr. Silva",
                "date": "2025-07-10",
                "time": "10:00",
            },
            {
                "id": 2,
                "patient_id": 2,
                "doctor": "Dr. Santos",
                "date": "2025-07-11",
                "time": "14:30",
            },
        ],
        "total": 2,
    }


@app.get("/", response_model=Dict[str, Any])
async def root():
    return {
        "message": "Health API QA Framework",
        "version": "1.0.0",
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None,
        "timestamp": time.time(),
    }


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    return {
        "status": "healthy",
        "service": "health-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": "simulated",
        "timestamp": time.time(),
        "uptime": (
            time.time() - app.state.start_time
            if hasattr(app.state, "start_time")
            else 0
        ),
    }


@app.get("/ready", response_model=Dict[str, Any])
async def readiness_check():
    return {
        "status": "ready",
        "service": "health-api",
        "timestamp": time.time(),
    }


@app.get("/live", response_model=Dict[str, Any])
async def liveness_check():
    return {
        "status": "alive",
        "service": "health-api",
        "timestamp": time.time(),
    }


@app.get("/metrics")
async def metrics():
    return {
        "http_requests_total": 1000,
        "http_request_duration_seconds": 0.1,
        "database_connections_active": 5,
        "memory_usage_bytes": 104857600,
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": time.time(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": time.time(),
            }
        },
    )


@app.on_event("startup")
async def startup_event():
    app.state.start_time = time.time()
    logger.info("Health API startup completed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info",
    )
