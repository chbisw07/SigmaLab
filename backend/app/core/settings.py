from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-based settings for SigmaLab (PH1 foundation)."""

    model_config = SettingsConfigDict(
        env_prefix="SIGMALAB_",
        env_file=".env",
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

    # Placeholders for Kite credentials. Do not hardcode real secrets.
    kite_api_key: str | None = Field(default=None)
    kite_api_secret: str | None = Field(default=None)


@lru_cache
def get_settings() -> Settings:
    return Settings()

