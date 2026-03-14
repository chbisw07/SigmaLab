from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.orm import Instrument


@dataclass(frozen=True)
class InstrumentRepository:
    session: Session

    def upsert_many(self, instruments: list[dict]) -> int:
        if not instruments:
            return 0

        # Expect normalized dicts. Map instrument_metadata -> DB column name "metadata".
        values = []
        for row in instruments:
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

        stmt = insert(Instrument).values(values)
        excluded = stmt.excluded
        stmt = stmt.on_conflict_do_update(
            constraint="uq_instruments_broker_token_exchange",
            set_={
                "symbol": excluded.symbol,
                "name": excluded.name,
                "segment": excluded.segment,
                "metadata": excluded.metadata,
                "updated_at": func.now(),
            },
        )
        self.session.execute(stmt)
        self.session.commit()
        return len(values)

