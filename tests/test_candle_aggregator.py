from __future__ import annotations

from datetime import datetime

import pandas as pd

from data.candle_aggregator import CandleAggregator
from data.timeframe import Timeframe


def test_aggregate_15m_to_45m_ohlcv() -> None:
    # 3 x 15m candles starting at India market open.
    df = pd.DataFrame(
        [
            {"timestamp": datetime(2025, 1, 1, 9, 15), "open": 100, "high": 105, "low": 99, "close": 102, "volume": 10},
            {"timestamp": datetime(2025, 1, 1, 9, 30), "open": 102, "high": 106, "low": 101, "close": 104, "volume": 20},
            {"timestamp": datetime(2025, 1, 1, 9, 45), "open": 104, "high": 107, "low": 103, "close": 103, "volume": 30},
        ]
    )

    agg = CandleAggregator()
    out = agg.aggregate(df, base_tf=Timeframe.M15, target_tf=Timeframe.M45)

    assert len(out) == 1
    row = out.iloc[0].to_dict()
    assert row["open"] == 100
    assert row["close"] == 103
    assert row["high"] == 107
    assert row["low"] == 99
    assert row["volume"] == 60

