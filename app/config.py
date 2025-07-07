"""
Configuration management for the FastAPI application.
"""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application settings
    app_name: str = Field(default="Buildship FastAPI")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)

    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=4)

    # Database settings
    database_url: str = Field(default="sqlite:///./app.db")
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=40)

    # Security settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production"
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    # Logging settings
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # External services
    redis_url: Optional[str] = Field(default=None)
    redis_password: Optional[str] = Field(default=None)

    # Monitoring
    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=9090)

    # PostgreSQL settings (for docker-compose)
    postgres_db: Optional[str] = Field(default=None)
    postgres_user: Optional[str] = Field(default=None)
    postgres_password: Optional[str] = Field(default=None)

    # API Key settings
    enable_api_key_auth: bool = Field(default=False)
    api_key_header: str = Field(default="x-api-key")
    api_keys_raw: Optional[str] = Field(default=None)
    exclude_api_key_paths_raw: Optional[str] = Field(
        default="/docs,/redoc,/openapi.json,/health,/metrics,/"
    )

    def api_keys(self) -> List[str]:
        """Get API keys as a list, parsing from comma-separated string if needed."""
        if self.api_keys_raw is None:
            return []
        # api_keys_raw is guaranteed to be a string here
        return [key.strip() for key in self.api_keys_raw.split(',') if key.strip()]

    def exclude_api_key_paths(self) -> List[str]:
        """Get exclude paths as list, parsing from comma-separated string if needed."""
        if self.exclude_api_key_paths_raw is None:
            return [
                "/docs",
                "/redoc",
                "/openapi.json",
                "/health",
                "/metrics",
                "/"]
        # exclude_api_key_paths_raw is guaranteed to be a string here
        return [
            path.strip()
            for path in self.exclude_api_key_paths_raw.split(',')
            if path.strip()
        ]

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
