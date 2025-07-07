"""
Configuration management for the FastAPI application.
"""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application settings
    app_name: str = Field(default="Buildship FastAPI", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")

    # Database settings
    database_url: str = Field(env="DATABASE_URL")
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=40, env="DATABASE_MAX_OVERFLOW")

    # Security settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="json", env="LOG_FORMAT"
    )

    # External services
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")

    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")

    # PostgreSQL settings (for docker-compose)
    postgres_db: Optional[str] = Field(default=None, env="POSTGRES_DB")
    postgres_user: Optional[str] = Field(default=None, env="POSTGRES_USER")
    postgres_password: Optional[str] = Field(default=None, env="POSTGRES_PASSWORD")

    # API Key settings
    enable_api_key_auth: bool = Field(default=False, env="ENABLE_API_KEY_AUTH")
    api_key_header: str = Field(default="x-api-key", env="API_KEY_HEADER")
    api_keys_raw: Optional[str] = Field(default=None, env="API_KEYS")
    exclude_api_key_paths_raw: Optional[str] = Field(
        default="/docs,/redoc,/openapi.json,/health,/metrics,/",
        env="EXCLUDE_API_KEY_PATHS"
    )

    def api_keys(self) -> List[str]:
        """Get API keys as a list, parsing from comma-separated string if needed."""
        if self.api_keys_raw is None:
            return []
        if isinstance(self.api_keys_raw, str):
            return [key.strip() for key in self.api_keys_raw.split(',') if key.strip()]
        elif isinstance(self.api_keys_raw, list):
            return self.api_keys_raw
        return []

    def exclude_api_key_paths(self) -> List[str]:
        """Get exclude paths as a list, parsing from comma-separated string if needed."""
        if self.exclude_api_key_paths_raw is None:
            return ["/docs", "/redoc", "/openapi.json", "/health", "/metrics", "/"]
        if isinstance(self.exclude_api_key_paths_raw, str):
            return [path.strip() for path in self.exclude_api_key_paths_raw.split(',') if path.strip()]
        elif isinstance(self.exclude_api_key_paths_raw, list):
            return self.exclude_api_key_paths_raw
        return ["/docs", "/redoc", "/openapi.json", "/health", "/metrics", "/"]

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
