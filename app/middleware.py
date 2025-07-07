"""
Custom middleware for the FastAPI application.
"""

import time
from typing import Any, Callable, cast

import structlog
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

# Configure structured logging
# Choose the appropriate renderer based on settings
renderer = (
    structlog.processors.JSONRenderer()
    if settings.log_format == "json"
    else structlog.dev.ConsoleRenderer()
)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        cast(Any, renderer),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Process request
        response = cast(Response, await call_next(request))

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
        )

        # Add processing time to response headers
        response.headers["X-Process-Time"] = str(process_time)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = cast(Response, await call_next(request))

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000; includeSubDomains"

        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication with Swagger exclusion."""

    def __init__(self, app: Starlette, settings: Any) -> None:
        super().__init__(app)
        self.settings = settings
        self.api_key_header = settings.api_key_header
        self.exclude_paths = settings.exclude_api_key_paths

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip API key check if not enabled
        if not self.settings.enable_api_key_auth:
            return cast(Response, await call_next(request))

        # Skip API key check for Swagger/OpenAPI requests
        if self._should_skip_api_key_check(request):
            return cast(Response, await call_next(request))

        # Check for API key
        api_key = request.headers.get(self.api_key_header)
        if not api_key:
            return Response(
                status_code=401,
                content="API key required",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # Validate API key
        if not self._validate_api_key(api_key):
            return Response(
                status_code=401,
                content="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        return cast(Response, await call_next(request))

    def _should_skip_api_key_check(self, request: Request) -> bool:
        """Check if API key validation should be skipped."""

        # Skip for configured exclude paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return True

        # Skip for Swagger UI requests (check User-Agent)
        user_agent = request.headers.get("user-agent", "").lower()
        swagger_user_agents = [
            "swagger-ui",
            "swagger",
            "openapi",
            "fastapi",
            "mozilla/5.0",  # Browser requests
        ]

        if any(agent in user_agent for agent in swagger_user_agents):
            return True

        # Skip for requests coming from Swagger UI (check Referer)
        referer = request.headers.get("referer", "").lower()
        if "docs" in referer or "swagger" in referer:
            return True

        # Skip for development environment
        if self.settings.debug:
            return True

        # Skip for localhost requests
        if request.client and request.client.host in ["127.0.0.1", "localhost", "::1"]:
            return True

        return False

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate the API key."""
        # Check against configured API keys
        return api_key in self.settings.api_keys


def setup_middleware(app: Starlette) -> None:
    """Setup all middleware for the application."""

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Configure appropriately for production
    )

    # Add custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # Add API key middleware (conditional)
    app.add_middleware(APIKeyMiddleware, settings=settings)
