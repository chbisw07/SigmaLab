from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.orm import Instrument, WatchlistItem
from app.services.repos.instruments import InstrumentRepository
from app.services.watchlists import WatchlistService


def _test_db_url() -> str | None:
    return os.environ.get("SIGMALAB_TEST_DATABASE_URL")


@pytest.mark.integration
def test_instrument_upsert_and_watchlist_crud_postgres() -> None:
    url = _test_db_url()
    if not url:
        pytest.skip("Set SIGMALAB_TEST_DATABASE_URL to run Postgres integration tests")

    engine = create_engine(url, future=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

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

