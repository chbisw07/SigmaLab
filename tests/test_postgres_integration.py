from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.orm import Instrument, WatchlistItem
from app.services.repos.instruments import InstrumentRepository
from app.services.watchlists import WatchlistService


def _test_db_url() -> str | None:
    return os.environ.get("SIGMALAB_TEST_DATABASE_URL")

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _reset_public_schema(engine) -> None:  # type: ignore[no-untyped-def]
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


@pytest.mark.integration
def test_instrument_upsert_and_watchlist_crud_postgres() -> None:
    url = _test_db_url()
    if not url:
        pytest.skip("Set SIGMALAB_TEST_DATABASE_URL to run Postgres integration tests")

    engine = create_engine(url, future=True)
    _reset_public_schema(engine)

    env = os.environ.copy()
    env["SIGMALAB_DATABASE_URL"] = url
    env["SIGMALAB_ENV"] = "test"
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
        cwd=str(_repo_root()),
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    Session = sessionmaker(bind=engine, future=True)
    with Session() as session:
        repo = InstrumentRepository(session)
        n1 = repo.upsert_many(
            [
                {
                    "broker_instrument_token": "123",
                    "exchange": "NSE",
                    "symbol": "RELIANCE",
                    "name": "Reliance",
                    "segment": "NSE",
                    "instrument_metadata": {"tick_size": 0.05},
                }
            ]
        )
        assert n1 == 1

        # Idempotent upsert should not create duplicates.
        n2 = repo.upsert_many(
            [
                {
                    "broker_instrument_token": "123",
                    "exchange": "NSE",
                    "symbol": "RELIANCE",
                    "name": "Reliance Industries",
                    "segment": "NSE",
                    "instrument_metadata": {"tick_size": 0.05},
                }
            ]
        )
        assert n2 == 1

        inst = session.execute(select(Instrument)).scalars().one()
        assert inst.name == "Reliance Industries"

        wl_svc = WatchlistService(session)
        wl = wl_svc.create(name=f"wl-{uuid.uuid4()}")
        wl_svc.add_instrument(wl.id, inst.id)
        wl_svc.add_instrument(wl.id, inst.id)  # should be idempotent

        items = session.execute(select(WatchlistItem)).scalars().all()
        assert len(items) == 1

        instruments = wl_svc.list_instruments(wl.id)
        assert [i.symbol for i in instruments] == ["RELIANCE"]
