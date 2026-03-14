from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.orm import Candle


_CANDLE_UPSERT_BATCH_SIZE = 5000


@dataclass(frozen=True)
class CandleRepository:
    session: Session

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
