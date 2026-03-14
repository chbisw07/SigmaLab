from __future__ import annotations

from sqlalchemy.dialects import postgresql

from app.services.repos.instruments import InstrumentRepository


def test_instrument_repo_upsert_builds_postgres_statement_without_metadata_collision() -> None:
    """
    Regression test: instruments table has a column named 'metadata' (JSONB).

    Using ORM bulk insert helpers with a dict key 'metadata' can collide with
    SQLAlchemy's internal `.metadata` attribute and raise:
    AttributeError: 'MetaData' object has no attribute '_bulk_update_tuples'
    """

    class FakeSession:
        def execute(self, stmt):  # type: ignore[no-untyped-def]
            compiled = stmt.compile(dialect=postgresql.dialect())
            sql = str(compiled)
            assert "ON CONFLICT" in sql
            assert "metadata" in sql

        def commit(self) -> None:
            return None

    repo = InstrumentRepository(session=FakeSession())  # type: ignore[arg-type]
    n = repo.upsert_many(
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
    assert n == 1

