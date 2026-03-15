from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.orm import Instrument


_UPSERT_BATCH_SIZE = 2000


@dataclass(frozen=True)
class InstrumentRepository:
    session: Session

    def upsert_many(self, instruments: list[dict]) -> int:
        if not instruments:
            return 0

        total = 0

        # Kite's instrument master can be tens of thousands of rows. PostgreSQL has a hard
        # limit of 65,535 bind parameters per statement, so we upsert in batches.
        for i in range(0, len(instruments), _UPSERT_BATCH_SIZE):
            batch = instruments[i : i + _UPSERT_BATCH_SIZE]

            # Expect normalized dicts. Map instrument_metadata -> DB column name "metadata".
            values = []
            for row in batch:
                values.append(
                    {
                        "broker_instrument_token": row["broker_instrument_token"],
                        "exchange": row["exchange"],
                        "symbol": row["symbol"],
                        "name": row.get("name"),
                        "segment": row.get("segment"),
                        "metadata": row.get("instrument_metadata", {}),
                    }
                )

            # Use a Core insert against the Table, not the ORM entity, because the table has a
            # column named "metadata" which would collide with SQLAlchemy ORM's `metadata`.
            stmt = insert(Instrument.__table__).values(values)
            excluded = stmt.excluded
            stmt = stmt.on_conflict_do_update(
                constraint="uq_instruments_broker_token_exchange",
                set_={
                    "symbol": excluded.symbol,
                    "name": excluded.name,
                    "segment": excluded.segment,
                    # Column is named "metadata" which collides with SQLAlchemy's `.metadata` attr.
                    "metadata": excluded["metadata"],
                    "updated_at": func.now(),
                },
            )
            self.session.execute(stmt)
            total += len(values)

        self.session.commit()
        return total

    def get_broker_token(self, instrument_id) -> str:
        inst = self.session.get(Instrument, instrument_id)
        if inst is None:
            raise KeyError("instrument not found")
        return inst.broker_instrument_token

    def list(self, *, limit: int = 50) -> list[Instrument]:
        stmt = select(Instrument).order_by(Instrument.symbol.asc()).limit(limit)
        return list(self.session.execute(stmt).scalars())

    def search(self, *, q: str, exchange: str | None = None, limit: int = 50) -> list[Instrument]:
        qq = (q or "").strip()
        stmt = select(Instrument)
        if exchange:
            stmt = stmt.where(Instrument.exchange == exchange)
        if qq:
            like = f"%{qq}%"
            stmt = stmt.where(or_(Instrument.symbol.ilike(like), Instrument.name.ilike(like)))
        stmt = stmt.order_by(Instrument.symbol.asc()).limit(limit)
        return list(self.session.execute(stmt).scalars())
