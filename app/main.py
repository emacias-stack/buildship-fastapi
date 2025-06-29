"""
Main FastAPI application.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import get_db, init_db
from app.middleware import setup_middleware
from app.schemas import HealthCheck
from app.api.v1.endpoints import auth, items


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the FastAPI application."""
    # Startup
    init_db()
    yield
    # Shutdown (if needed)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A production-ready FastAPI application with comprehensive testing and monitoring",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Setup middleware
setup_middleware(app)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(items.router, prefix="/api/v1/items", tags=["items"])


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Buildship FastAPI",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else None,
    }


@app.get("/health", response_model=HealthCheck, tags=["health"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    # Test database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return HealthCheck(
        status="healthy" if db_status == "healthy" else "unhealthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        database=db_status,
    )


@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    # This would typically return Prometheus metrics
    # For now, return basic application metrics
    return {
        "app_version": settings.app_version,
        "uptime": "running",
        "database_connections": "active",
    } 