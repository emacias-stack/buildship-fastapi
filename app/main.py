"""
Main FastAPI application.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.config import settings
from app.database import get_db, init_db
from app.middleware import setup_middleware
from app.schemas import HealthCheck, PaginatedResponse
from app.api.v1.endpoints import auth, items
from app.auth import get_current_active_user_optional
from app.crud import get_items, get_items_count
from app.models import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the FastAPI application."""
    # Startup - removed auto database initialization
    # Database tables will be created on first access or manually
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
    # Remove any global security requirements
    openapi_tags=[
        {
            "name": "public",
            "description": "Public endpoints that don't require authentication"
        },
        {
            "name": "authentication",
            "description": "Authentication endpoints"
        },
        {
            "name": "items",
            "description": "Items management (requires authentication)"
        }
    ]
)

# Setup middleware
setup_middleware(app)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(items.router, prefix="/api/v1/items", tags=["items"])

@app.get("/", tags=["public"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Buildship FastAPI",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else None,
    }

@app.get("/health", response_model=HealthCheck, tags=["public"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    # Test database connection and initialize tables if needed
    try:
        db.execute(text("SELECT 1"))
        # Try to initialize tables if they don't exist
        try:
            init_db()
        except Exception:
            # Tables might already exist, which is fine
            pass
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return HealthCheck(
        status="healthy" if db_status == "healthy" else "unhealthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        database=db_status,
    )

@app.get("/metrics", tags=["public"])
async def metrics():
    """Prometheus metrics endpoint."""
    # This would typically return Prometheus metrics
    # For now, return basic application metrics
    return {
        "app_version": settings.app_version,
        "uptime": "running",
        "database_connections": "active",
    }

@app.get("/public/items", response_model=PaginatedResponse, tags=["public"])
async def read_public_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user_optional),
):
    """Get public list of items (no authentication required)."""
    items = get_items(db, skip=skip, limit=limit)
    total = get_items_count(db)

    pages = (total + limit - 1) // limit
    page = (skip // limit) + 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=limit,
        pages=pages,
    )
