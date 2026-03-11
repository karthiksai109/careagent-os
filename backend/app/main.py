"""
CareAgent OS — Main Application Entry Point
Autonomous Multi-Agent Healthcare Operations Platform
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    await init_db()
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    CareAgent OS v1.0.0                       ║
║       Autonomous Multi-Agent Healthcare Operations           ║
║                                                              ║
║  6 AI Agents Ready:                                          ║
║    1. Voice Intake Agent      — Patient calls & intake       ║
║    2. Triage Agent            — AI urgency classification    ║
║    3. Prior Auth Agent        — Insurance authorization      ║
║    4. Clinical Doc Agent      — SOAP notes & ICD-10 coding   ║
║    5. Patient Advocate Agent  — Follow-ups & reminders       ║
║    6. Operations Agent        — Analytics & forecasting      ║
║                                                              ║
║  Dashboard: http://localhost:3000                            ║
║  API Docs:  http://localhost:{settings.PORT}/docs                    ║
║  API Base:  http://localhost:{settings.PORT}/api                     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    yield
    # Shutdown
    print("CareAgent OS shutting down...")


app = FastAPI(
    title="CareAgent OS",
    description="Autonomous Multi-Agent Healthcare Operations Platform — 6 specialized AI agents working together to handle patient intake, triage, documentation, prior authorizations, follow-ups, and operations analytics.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "CareAgent OS",
        "version": "1.0.0",
        "description": "Autonomous Multi-Agent Healthcare Operations Platform",
        "agents": [
            {"name": "Voice Intake Agent", "status": "active"},
            {"name": "Triage Agent", "status": "active"},
            {"name": "Prior Auth Agent", "status": "active"},
            {"name": "Clinical Doc Agent", "status": "active"},
            {"name": "Patient Advocate Agent", "status": "active"},
            {"name": "Operations Agent", "status": "active"},
        ],
        "endpoints": {
            "docs": "/docs",
            "api": "/api",
            "status": "/api/status",
            "demo": "/api/demo",
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "careagent-os"}
