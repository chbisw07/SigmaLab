from __future__ import annotations

import pytest

from app.core.settings import Settings


def test_settings_default_database_is_postgres() -> None:
    s = Settings(env="test")
    assert s.database_url.startswith("postgresql")


def test_settings_rejects_non_postgres_database_url() -> None:
    with pytest.raises(ValueError, match="PostgreSQL URL"):
        Settings(env="test", database_url="sqlite:///tmp.db")

