from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DOTENV_REPO = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    """Environment-based settings for SigmaLab (PH1 foundation)."""

    model_config = SettingsConfigDict(
        env_prefix="SIGMALAB_",
        # Allow running from repo root or other CWDs; production should use real env vars.
        env_file=(str(_DOTENV_REPO), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["local", "dev", "test", "prod"] = Field(default="local")
    log_level: str = Field(default="INFO")

    # Primary persisted database. For PH1 we only scaffold config; app startup must not
    # require a live DB connection.
    database_url: str = Field(
        default="postgresql+psycopg://sigmalab:sigmalab@localhost:5432/sigmalab"
    )
    database_echo: bool = Field(default=False)

    # Placeholders for Kite credentials. Do not hardcode real secrets.
    kite_api_key: str | None = Field(default=None)
    kite_api_secret: str | None = Field(default=None)
    kite_access_token: str | None = Field(default=None)

    # Frontend/dev UX. Comma-separated list in SIGMALAB_CORS_ORIGINS.
    # Example: "http://localhost:5173,http://127.0.0.1:5173"
    cors_origins: list[str] = Field(default_factory=list)

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        if not value.startswith("postgresql"):
            raise ValueError("SIGMALAB_DATABASE_URL must be a PostgreSQL URL (postgresql...)")
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):  # type: ignore[no-untyped-def]
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            v = value.strip()
            if not v:
                return []
            # Accept JSON-like lists as well, but keep the common CSV path simple.
            if v.startswith("[") and v.endswith("]"):
                return [s.strip().strip("\"'") for s in v.strip("[]").split(",") if s.strip().strip("\"'")]
            return [s.strip() for s in v.split(",") if s.strip()]
        return []


@lru_cache
def get_settings() -> Settings:
    return Settings()
