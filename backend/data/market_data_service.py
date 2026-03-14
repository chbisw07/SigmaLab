from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import pandas as pd

from data.candle_aggregator import CandleAggregator
from data.historical_fetcher import HistoricalFetcher
from data.timeframe import Timeframe


class InstrumentTokenResolver(Protocol):
    def resolve(self, instrument_id: uuid.UUID) -> int | str: ...


class BaseCandleStore(Protocol):
    def upsert_base_candles(
        self,
        instrument_id: uuid.UUID,
        base_interval: str,
        candles: pd.DataFrame,
    ) -> None: ...


@dataclass(frozen=True)
class MarketDataService:
    """Public entrypoint for market candles.

    Higher-level engines must use this service and never call broker adapters directly.
    """

    token_resolver: InstrumentTokenResolver
    fetcher: HistoricalFetcher
    aggregator: CandleAggregator
    candle_store: BaseCandleStore | None = None

    def get_candles(
        self,
        instrument_id: uuid.UUID,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        plan = timeframe.plan()
        base_interval = plan.kite_interval

        instrument_token = self.token_resolver.resolve(instrument_id)
        base_df = self.fetcher.fetch(
            instrument_token=instrument_token,
            interval=base_interval,
            start=start,
            end=end,
        )

        if self.candle_store is not None and not base_df.empty:
            # Persist only base (broker-supported) candles. Higher timeframes are derived.
            base_interval_str = base_interval.value if hasattr(base_interval, "value") else str(base_interval)
            self.candle_store.upsert_base_candles(
                instrument_id=instrument_id,
                base_interval=base_interval_str,
                candles=base_df,
            )

        if not plan.needs_aggregation:
            return base_df

        # When aggregating, treat the fetched interval as the base timeframe.
        base_tf = Timeframe.parse(_tf_from_kite_interval(base_interval))
        return self.aggregator.aggregate(base_df, base_tf=base_tf, target_tf=timeframe)


def _tf_from_kite_interval(interval) -> str:
    m = {
        "minute": "1m",
        "3minute": "3m",
        "5minute": "5m",
        "10minute": "10m",
        "15minute": "15m",
        "30minute": "30m",
        "60minute": "1h",
        "day": "1D",
    }
    key = interval.value if hasattr(interval, "value") else interval
    return m[key]
