from __future__ import annotations

from app.services.repos import instruments as instruments_repo
from app.services.repos.instruments import InstrumentRepository


def test_instrument_repo_upsert_many_batches_to_avoid_postgres_parameter_limit() -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.exec_calls = 0
            self.commits = 0

        def execute(self, stmt):  # type: ignore[no-untyped-def]
            self.exec_calls += 1

        def commit(self) -> None:
            self.commits += 1

    # Temporarily reduce batch size so we don't create a huge test input.
    original = instruments_repo._UPSERT_BATCH_SIZE
    instruments_repo._UPSERT_BATCH_SIZE = 2
    try:
        session = FakeSession()
        repo = InstrumentRepository(session=session)  # type: ignore[arg-type]
        n = repo.upsert_many(
            [
                {"broker_instrument_token": "1", "exchange": "NSE", "symbol": "A", "instrument_metadata": {}},
                {"broker_instrument_token": "2", "exchange": "NSE", "symbol": "B", "instrument_metadata": {}},
                {"broker_instrument_token": "3", "exchange": "NSE", "symbol": "C", "instrument_metadata": {}},
            ]
        )

        assert n == 3
        assert session.exec_calls == 2  # 2 + 1 rows -> 2 batches
        assert session.commits == 1
    finally:
        instruments_repo._UPSERT_BATCH_SIZE = original

