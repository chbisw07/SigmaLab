from __future__ import annotations

import uuid
from datetime import datetime

import pandas as pd

from app.backtesting.candle_cache import CandleCache
from data.timeframe import Timeframe


class FakeMDS:
    def __init__(self) -> None:
        self.calls = 0

    def get_candles(self, instrument_id, timeframe, start, end):  # type: ignore[no-untyped-def]
        self.calls += 1
        return pd.DataFrame(
            {
                "timestamp": [start, end],
                "open": [1.0, 1.0],
                "high": [1.0, 1.0],
                "low": [1.0, 1.0],
                "close": [1.0, 1.0],
                "volume": [0, 0],
            }
        )


def test_candle_cache_dedupes_calls() -> None:
    mds = FakeMDS()
    cache = CandleCache()
    inst_id = uuid.uuid4()
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 2)
    tf = Timeframe.M15

    a = cache.get(mds, instrument_id=inst_id, timeframe=tf, start=start, end=end)
    b = cache.get(mds, instrument_id=inst_id, timeframe=tf, start=start, end=end)
    assert mds.calls == 1
    assert a.equals(b)

