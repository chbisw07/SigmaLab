from __future__ import annotations

import uuid
from datetime import datetime

import pandas as pd

from data.market_data_service import MarketDataService
from data.timeframe import Timeframe


def _df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": datetime(2026, 3, 14, 9, 15), "open": 1, "high": 2, "low": 1, "close": 2, "volume": 10},
            {"timestamp": datetime(2026, 3, 14, 9, 30), "open": 2, "high": 3, "low": 2, "close": 3, "volume": 20},
            {"timestamp": datetime(2026, 3, 14, 9, 45), "open": 3, "high": 4, "low": 3, "close": 4, "volume": 30},
        ]
    )


def test_market_data_service_base_timeframe_fetch_no_aggregation() -> None:
    inst_id = uuid.uuid4()

    class Resolver:
        def resolve(self, instrument_id):  # type: ignore[no-untyped-def]
            assert instrument_id == inst_id
            return 123

    class Fetcher:
        def __init__(self) -> None:
            self.calls = []

        def fetch(self, instrument_token, interval, start, end):  # type: ignore[no-untyped-def]
            self.calls.append((instrument_token, interval, start, end))
            return _df()

    class Aggregator:
        def __init__(self) -> None:
            self.called = False

        def aggregate(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            self.called = True
            raise AssertionError("should not aggregate for base timeframe")

    class Store:
        def __init__(self) -> None:
            self.calls = []

        def upsert_base_candles(self, instrument_id, base_interval, candles):  # type: ignore[no-untyped-def]
            self.calls.append((instrument_id, base_interval, candles))

    fetcher = Fetcher()
    aggregator = Aggregator()
    store = Store()
    svc = MarketDataService(token_resolver=Resolver(), fetcher=fetcher, aggregator=aggregator, candle_store=store)

    tf = Timeframe.parse("15m")
    df = svc.get_candles(inst_id, tf, start=datetime(2026, 3, 14), end=datetime(2026, 3, 15))

    assert not aggregator.called
    assert len(fetcher.calls) == 1
    assert len(store.calls) == 1
    assert store.calls[0][1] == "15minute"
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]


def test_market_data_service_aggregates_when_needed() -> None:
    inst_id = uuid.uuid4()

    class Resolver:
        def resolve(self, instrument_id):  # type: ignore[no-untyped-def]
            return 123

    class Fetcher:
        def fetch(self, instrument_token, interval, start, end):  # type: ignore[no-untyped-def]
            return _df()

    class Aggregator:
        def __init__(self) -> None:
            self.calls = []

        def aggregate(self, candles, base_tf, target_tf):  # type: ignore[no-untyped-def]
            self.calls.append((base_tf, target_tf))
            # return a simplified aggregated frame
            return pd.DataFrame(
                [
                    {
                        "timestamp": datetime(2026, 3, 14, 10, 0),
                        "open": 1,
                        "high": 4,
                        "low": 1,
                        "close": 4,
                        "volume": 60,
                    }
                ]
            )

    class Store:
        def upsert_base_candles(self, instrument_id, base_interval, candles):  # type: ignore[no-untyped-def]
            return None

    agg = Aggregator()
    svc = MarketDataService(token_resolver=Resolver(), fetcher=Fetcher(), aggregator=agg, candle_store=Store())

    tf = Timeframe.parse("45m")
    out = svc.get_candles(inst_id, tf, start=datetime(2026, 3, 14), end=datetime(2026, 3, 15))

    assert len(agg.calls) == 1
    base_tf, target_tf = agg.calls[0]
    assert str(base_tf.value) == "15m"
    assert str(target_tf.value) == "45m"
    assert out.iloc[0]["volume"] == 60

