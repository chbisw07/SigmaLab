from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from data.market_data_service import MarketDataService
from data.timeframe import Timeframe


@dataclass
class CandleCache:
    """Simple per-run in-memory candle cache (PH4).

    This sits above MarketDataService to avoid repeated DB reads and repeated aggregation
    work during a single backtest run.
    """

    _cache: dict[tuple[uuid.UUID, str, datetime, datetime], pd.DataFrame] = field(default_factory=dict)

    def get(
        self,
        mds: MarketDataService,
        *,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        key = (instrument_id, timeframe.value, start, end)
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        df = mds.get_candles(
            instrument_id=instrument_id,
            timeframe=timeframe,
            start=start,
            end=end,
        )
        self._cache[key] = df
        return df
