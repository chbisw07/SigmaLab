from __future__ import annotations

import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

import pandas as pd

from data.timeframe import KiteInterval


class KiteHistoricalClient(Protocol):
    def historical_data(
        self,
        instrument_token: int | str,
        from_date: datetime,
        to_date: datetime,
        interval: str,
    ) -> list[dict]:
        ...


_KITE_MAX_DAYS: dict[KiteInterval, int] = {
    KiteInterval.MINUTE: 60,
    KiteInterval.M3: 100,
    KiteInterval.M5: 100,
    KiteInterval.M10: 100,
    KiteInterval.M15: 200,
    KiteInterval.M30: 200,
    KiteInterval.H1: 400,
    KiteInterval.D1: 2000,
}


@dataclass(frozen=True)
class HistoricalFetcher:
    client: KiteHistoricalClient
    max_rps: float = 3.0
    max_retries: int = 3

    def fetch(
        self,
        instrument_token: int | str,
        interval: KiteInterval,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """Fetch candles for a possibly-large date range, respecting Kite constraints."""
        chunks = list(self._paginate(start, end, _KITE_MAX_DAYS[interval]))
        all_rows: list[dict] = []

        last_call = 0.0
        min_gap = 1.0 / self.max_rps if self.max_rps > 0 else 0.0

        for c_start, c_end in chunks:
            # Rate limit: ~3 requests/sec.
            now = time.monotonic()
            sleep_for = (last_call + min_gap) - now
            if sleep_for > 0:
                time.sleep(sleep_for)

            rows = self._call_with_retries(
                instrument_token=instrument_token,
                interval=interval.value,
                start=c_start,
                end=c_end,
            )
            last_call = time.monotonic()
            all_rows.extend(rows)

        df = self._to_dataframe(all_rows)
        if df.empty:
            return df

        # Sort, dedupe on timestamp.
        df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="first")
        df = df.reset_index(drop=True)
        return df

    def _call_with_retries(
        self, instrument_token: int | str, interval: str, start: datetime, end: datetime
    ) -> list[dict]:
        attempt = 0
        while True:
            try:
                return self.client.historical_data(
                    instrument_token=instrument_token,
                    from_date=start,
                    to_date=end,
                    interval=interval,
                )
            except Exception:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                backoff = (0.5 * (2 ** (attempt - 1))) + random.random() * 0.2
                time.sleep(backoff)

    @staticmethod
    def _paginate(start: datetime, end: datetime, max_days: int):
        if end < start:
            raise ValueError("end must be >= start")
        cur = start
        step = timedelta(days=max_days)
        while cur < end:
            nxt = min(cur + step, end)
            yield cur, nxt
            cur = nxt

    @staticmethod
    def _to_dataframe(rows: list[dict]) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        def pick(r: dict, *keys: str):
            for k in keys:
                if k in r and r[k] is not None:
                    return r[k]
            return None

        def norm_row(r: dict) -> dict:
            # Kite historical returns: [date, open, high, low, close, volume]
            # or dicts depending on client. Normalize defensively.
            ts = pick(r, "date", "timestamp", "time", "t")
            return {
                "timestamp": ts,
                "open": pick(r, "open", "o"),
                "high": pick(r, "high", "h"),
                "low": pick(r, "low", "l"),
                "close": pick(r, "close", "c"),
                "volume": pick(r, "volume", "v") or 0,
            }

        df = pd.DataFrame([norm_row(r) for r in rows])
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
        return df[["timestamp", "open", "high", "low", "close", "volume"]]
