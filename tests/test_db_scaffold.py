from __future__ import annotations

from app.core.db import Database
from app.core.settings import Settings


def test_database_engine_is_constructible_without_connecting() -> None:
    settings = Settings(
        env="test",
        database_url="postgresql+psycopg://sigmalab:sigmalab@localhost:5432/sigmalab",
    )
    db = Database.from_settings(settings)
    assert str(db.engine.url).startswith("postgresql+psycopg://")

