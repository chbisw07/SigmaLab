from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo

import pandas as pd

from data.timeframe import Timeframe


@dataclass(frozen=True)
class CandleAggregator:
    """Aggregates candles from Kite base intervals into higher timeframes."""

    tz: str = "Asia/Kolkata"
    market_open: time = time(9, 15)

    def aggregate(self, candles: pd.DataFrame, base_tf: Timeframe, target_tf: Timeframe) -> pd.DataFrame:
        if candles.empty:
            return candles

        plan = target_tf.plan()
        if not plan.needs_aggregation:
            return candles

        if plan.calendar_rule:
            return self._aggregate_calendar(candles, plan.calendar_rule)

        if plan.aggregation_factor <= 1:
            return candles

        base_plan = base_tf.plan()
        if base_plan.calendar_rule is not None:
            raise ValueError("Cannot fixed-factor aggregate from a calendar-resampled base timeframe")

        return self._aggregate_fixed_factor(
            candles=candles,
            base_interval_minutes=self._kite_minutes(base_plan.kite_interval),
            factor=plan.aggregation_factor,
        )

    def _aggregate_calendar(self, candles: pd.DataFrame, rule: str) -> pd.DataFrame:
        df = self._normalize(candles).set_index("timestamp", drop=False)
        res = df.resample(rule, label="right", closed="right").agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        res = res.dropna(subset=["open", "close"])
        res["timestamp"] = res.index
        return res.reset_index(drop=True)[["timestamp", "open", "high", "low", "close", "volume"]]

    def _aggregate_fixed_factor(
        self, candles: pd.DataFrame, base_interval_minutes: int, factor: int
    ) -> pd.DataFrame:
        df = self._normalize(candles)
        df = df.sort_values("timestamp").reset_index(drop=True)

        target_minutes = base_interval_minutes * factor
        tz = ZoneInfo(self.tz)

        ts = df["timestamp"]
        if ts.dt.tz is None:
            ts = ts.dt.tz_localize(tz)
            df = df.assign(timestamp=ts)
        else:
            df = df.assign(timestamp=ts.dt.tz_convert(tz))

        # Group within each trading day, anchored at market_open (India equities: 09:15).
        local = df["timestamp"]
        day = local.dt.floor("D")
        anchor = day + pd.to_timedelta(self.market_open.hour, unit="h") + pd.to_timedelta(
            self.market_open.minute, unit="m"
        )

        delta_min = ((local - anchor).dt.total_seconds() // 60).astype("int64")
        bucket = (delta_min // target_minutes).astype("int64")

        # Drop any candles that fall before the anchor (negative buckets).
        mask = bucket >= 0
        df = df.loc[mask].copy()
        day = day.loc[mask]
        bucket = bucket.loc[mask]

        df["_bucket_start"] = anchor.loc[mask] + pd.to_timedelta(bucket * target_minutes, unit="m")
        grouped = df.groupby(["_bucket_start"], sort=True, as_index=False).agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        grouped = grouped.rename(columns={"_bucket_start": "timestamp"})
        return grouped[["timestamp", "open", "high", "low", "close", "volume"]]

    def _normalize(self, candles: pd.DataFrame) -> pd.DataFrame:
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        missing = required - set(candles.columns)
        if missing:
            raise ValueError(f"Missing candle columns: {sorted(missing)}")
        df = candles[["timestamp", "open", "high", "low", "close", "volume"]].copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
        return df

    @staticmethod
    def _kite_minutes(interval) -> int:
        return {
            "minute": 1,
            "3minute": 3,
            "5minute": 5,
            "10minute": 10,
            "15minute": 15,
            "30minute": 30,
            "60minute": 60,
            "day": 24 * 60,
        }[interval.value if hasattr(interval, "value") else interval]
