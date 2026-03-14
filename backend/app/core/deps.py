from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.db import Database


def get_database(request: Request) -> Database:
    db = getattr(request.app.state, "database", None)
    if db is None:
        raise RuntimeError("Database not configured on app.state")
    return db


def get_db_session(db: Database = Depends(get_database)) -> Generator[Session, None, None]:
    session = db.session()
    try:
        yield session
    finally:
        session.close()

