"""Application configuration from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://meshmanager:meshmanager@localhost/meshmanager",
        description="PostgreSQL connection URL",
    )

    # OIDC Authentication
    oidc_issuer: str | None = Field(default=None, description="OIDC issuer URL")
    oidc_client_id: str | None = Field(default=None, description="OIDC client ID")
    oidc_client_secret: str | None = Field(default=None, description="OIDC client secret")
    oidc_redirect_uri: str | None = Field(default=None, description="OIDC redirect URI")

    # Session
    session_secret: str = Field(
        default="change-me-in-production",
        description="Secret key for session signing",
    )

    # Application
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:8080"],
        description="Allowed CORS origins",
    )

    # Defaults
    default_poll_interval: int = Field(
        default=300,
        description="Default poll interval for MeshMonitor sources (seconds)",
    )
    default_retention_days: int = Field(
        default=30,
        description="Default data retention period (days)",
    )

    @property
    def oidc_enabled(self) -> bool:
        """Check if OIDC is configured."""
        return all([self.oidc_issuer, self.oidc_client_id, self.oidc_client_secret])


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
