from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import Settings


@dataclass(frozen=True)
class Database:
    """Lightweight SQLAlchemy database holder.

    PH1 intentionally avoids connecting on import or app startup. Engine creation
    should be safe even when a PostgreSQL server is not running locally.
    """

    engine: Engine
    session_factory: sessionmaker[Session]

    @classmethod
    def from_settings(cls, settings: Settings) -> "Database":
        engine = create_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,
            future=True,
        )
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        return cls(engine=engine, session_factory=session_factory)

    def session(self) -> Session:
        return self.session_factory()

