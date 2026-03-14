from __future__ import annotations

from datetime import datetime, timedelta

from data.historical_fetcher import HistoricalFetcher
from data.timeframe import KiteInterval


class FakeKite:
    def __init__(self) -> None:
        self.calls: list[tuple[datetime, datetime, str]] = []

    def historical_data(self, instrument_token, from_date, to_date, interval):  # type: ignore[no-untyped-def]
        self.calls.append((from_date, to_date, interval))
        # Return two candles per call, with an overlapping boundary candle to exercise dedupe.
        return [
            {"date": from_date, "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 10},
            {"date": to_date, "open": 2, "high": 3, "low": 1.5, "close": 2.5, "volume": 20},
        ]


def test_fetcher_paginates_and_dedupes() -> None:
    client = FakeKite()
    fetcher = HistoricalFetcher(client=client, max_rps=1000.0, max_retries=1)

    start = datetime(2020, 1, 1)
    end = start + timedelta(days=61)  # minute interval max is 60 days, so expect 2 calls.

    df = fetcher.fetch(instrument_token=123, interval=KiteInterval.MINUTE, start=start, end=end)

    assert len(client.calls) == 2
    assert df["timestamp"].is_monotonic_increasing
    # We expect duplicates removed (to_date of first call equals from_date of second call).
    assert df["timestamp"].nunique() == len(df)

