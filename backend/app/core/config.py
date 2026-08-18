"""Typed application settings, loaded once from the environment."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]

_INSECURE_SECRET_PREFIX = "dev-only-secret"


class Settings(BaseSettings):
    """Runtime configuration.

    Every value is overridable through an environment variable of the same
    name (case-insensitive), which is how the Docker Compose stack injects it.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Runtime ---------------------------------------------------------
    app_env: Environment = "development"
    log_level: str = "INFO"

    # --- Database --------------------------------------------------------
    database_url: str = "postgresql+asyncpg://peyredoule:peyredoule@localhost:5432/peyredoule"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False

    # --- Security --------------------------------------------------------
    app_secret_key: str = Field(min_length=32)
    access_token_ttl_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_ttl_days: int = Field(default=7, ge=1, le=90)
    cookie_secure: bool = False
    cookie_domain: str | None = None
    login_max_attempts: int = Field(default=5, ge=1, le=50)
    login_lockout_minutes: int = Field(default=15, ge=1, le=1440)

    # --- Seeded administrator -------------------------------------------
    admin_email: str = "admin@clos-peyredoule.fr"
    admin_password: str = "ChangeMe!2026"
    admin_full_name: str = "Propriétaire"

    # --- URLs ------------------------------------------------------------
    public_base_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Content ---------------------------------------------------------
    seed_demo_content: bool = True

    @field_validator("cookie_domain", mode="before")
    @classmethod
    def _blank_domain_is_none(cls, value: str | None) -> str | None:
        """Treat an empty COOKIE_DOMAIN as "host-only cookie"."""
        if value is None or not str(value).strip():
            return None
        return str(value).strip()

    @property
    def is_production(self) -> bool:
        """Whether the app runs with production hardening enabled."""
        return self.app_env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins as a list, parsed from the comma-separated setting."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def assert_production_ready(self) -> None:
        """Fail fast when production is configured with development defaults.

        Raises:
            RuntimeError: if an insecure default would be used in production.
        """
        if not self.is_production:
            return
        problems: list[str] = []
        if self.app_secret_key.startswith(_INSECURE_SECRET_PREFIX):
            problems.append("APP_SECRET_KEY still uses the development default")
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE must be true when serving over HTTPS")
        if self.admin_password == "ChangeMe!2026":
            problems.append("ADMIN_PASSWORD still uses the documented default")
        if problems:
            raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
