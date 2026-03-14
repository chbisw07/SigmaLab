from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Protocol

import pandas as pd

from data.candle_aggregator import CandleAggregator
from data.historical_fetcher import HistoricalFetcher
from data.timeframe import KiteInterval, Timeframe


class InstrumentTokenResolver(Protocol):
    def resolve(self, instrument_id: uuid.UUID) -> int | str: ...


class BaseCandleStore(Protocol):
    def get_base_candles(
        self,
        instrument_id: uuid.UUID,
        base_interval: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame: ...

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
        base_interval_str = base_interval.value if hasattr(base_interval, "value") else str(base_interval)

        start_local = _to_kolkata_naive(start)
        end_local = _to_kolkata_naive(end)
        if end_local < start_local:
            raise ValueError("end must be >= start")

        instrument_token = self.token_resolver.resolve(instrument_id)
        base_df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        if self.candle_store is not None:
            existing = self.candle_store.get_base_candles(
                instrument_id=instrument_id,
                base_interval=base_interval_str,
                start=start_local,
                end=end_local,
            )
            missing = _compute_missing_ranges(existing, start_local, end_local, base_interval)
            for m_start, m_end in missing:
                fetched = self.fetcher.fetch(
                    instrument_token=instrument_token,
                    interval=base_interval,
                    start=m_start,
                    end=m_end,
                )
                if not fetched.empty:
                    self.candle_store.upsert_base_candles(
                        instrument_id=instrument_id,
                        base_interval=base_interval_str,
                        candles=fetched,
                    )

            base_df = self.candle_store.get_base_candles(
                instrument_id=instrument_id,
                base_interval=base_interval_str,
                start=start_local,
                end=end_local,
            )
        else:
            base_df = self.fetcher.fetch(
                instrument_token=instrument_token,
                interval=base_interval,
                start=start_local,
                end=end_local,
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


def _to_kolkata_naive(dt: datetime, tz: str = "Asia/Kolkata") -> datetime:
    """Normalize user-provided datetimes into naive Asia/Kolkata wall-clock time."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(ZoneInfo(tz)).replace(tzinfo=None)


def _interval_step_seconds(interval: KiteInterval) -> int:
    return {
        KiteInterval.MINUTE: 60,
        KiteInterval.M3: 3 * 60,
        KiteInterval.M5: 5 * 60,
        KiteInterval.M10: 10 * 60,
        KiteInterval.M15: 15 * 60,
        KiteInterval.M30: 30 * 60,
        KiteInterval.H1: 60 * 60,
        KiteInterval.D1: 24 * 60 * 60,
    }[interval]


def _compute_missing_ranges(
    existing: pd.DataFrame, start: datetime, end: datetime, interval: KiteInterval
) -> list[tuple[datetime, datetime]]:
    """Compute missing [start,end] sub-ranges based on existing base candles.

    This is intentionally conservative: it guarantees we fetch enough data to cover
    the requested range, and it may occasionally fetch an already-covered edge range.
    """
    if existing is None or existing.empty:
        return [(start, end)]

    ts = pd.to_datetime(existing["timestamp"], utc=False).sort_values().reset_index(drop=True)
    if ts.empty:
        return [(start, end)]

    missing: list[tuple[datetime, datetime]] = []
    first = ts.iloc[0].to_pydatetime()
    last = ts.iloc[-1].to_pydatetime()

    if start < first:
        missing.append((start, first))
    if last < end:
        missing.append((last, end))

    # Internal gaps: only attempt for intraday intervals. Daily gaps include weekends/holidays.
    intraday = interval != KiteInterval.D1
    if intraday and len(ts) >= 2:
        step = _interval_step_seconds(interval)
        for a, b in zip(ts.iloc[:-1], ts.iloc[1:]):
            a_dt = a.to_pydatetime()
            b_dt = b.to_pydatetime()
            if a_dt.date() != b_dt.date():
                continue
            diff = (b_dt - a_dt).total_seconds()
            if diff > (step * 1.5):
                missing.append((a_dt, b_dt))

    missing = sorted(missing, key=lambda r: r[0])
    coalesced: list[tuple[datetime, datetime]] = []
    for s, e in missing:
        if e <= s:
            continue
        if not coalesced:
            coalesced.append((s, e))
            continue
        ps, pe = coalesced[-1]
        if s <= pe:
            coalesced[-1] = (ps, max(pe, e))
        else:
            coalesced.append((s, e))
    return coalesced
