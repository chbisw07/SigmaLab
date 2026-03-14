from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.orm import Candle


_CANDLE_UPSERT_BATCH_SIZE = 5000


@dataclass(frozen=True)
class CandleRepository:
    session: Session

    def list_range(
        self,
        instrument_id,
        base_interval: str,
        start,
        end,
    ) -> list[dict]:
        """Return candles in [start, end], ordered by timestamp ascending."""
        stmt = (
            select(Candle.ts, Candle.open, Candle.high, Candle.low, Candle.close, Candle.volume)
            .where(Candle.instrument_id == instrument_id)
            .where(Candle.base_interval == base_interval)
            .where(Candle.ts >= start)
            .where(Candle.ts <= end)
            .order_by(Candle.ts.asc())
        )
        rows = self.session.execute(stmt).all()
        return [
            {
                "timestamp": r.ts,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in rows
        ]

    def upsert_many(self, rows: list[dict]) -> int:
        """Upsert base candles.

        Expected keys per row:
        - instrument_id (uuid)
        - base_interval (str, broker interval string)
        - ts (datetime, tz-aware recommended)
        - open/high/low/close (float)
        - volume (int|None)
        """
        if not rows:
            return 0

        table = Candle.__table__
        total = 0
        for i in range(0, len(rows), _CANDLE_UPSERT_BATCH_SIZE):
            batch = rows[i : i + _CANDLE_UPSERT_BATCH_SIZE]

            stmt = insert(table).values(batch)
            excluded = stmt.excluded
            stmt = stmt.on_conflict_do_update(
                index_elements=["instrument_id", "base_interval", "ts"],
                set_={
                    "open": excluded.open,
                    "high": excluded.high,
                    "low": excluded.low,
                    "close": excluded.close,
                    "volume": excluded.volume,
                    "updated_at": func.now(),
                },
            )
            self.session.execute(stmt)
            total += len(batch)

        self.session.commit()
        return total
