from __future__ import annotations

import uuid
from dataclasses import dataclass

import pandas as pd
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from app.core.settings import Settings
from app.services.kite_provider import make_kite_client
from app.services.repos.candles import CandleRepository
from app.services.repos.instruments import InstrumentRepository

from data.candle_aggregator import CandleAggregator
from data.historical_fetcher import HistoricalFetcher
from data.market_data_service import BaseCandleStore, InstrumentTokenResolver, MarketDataService


class _DisabledKiteClient:
    """KiteConnect-like stub used when Kite credentials are not configured.

    This allows DB-first candle reads (already persisted) without requiring a live
    broker session. If a missing-range backfill is needed, it fails with a clear,
    actionable error.
    """

    def __init__(self, reason: str) -> None:
        self._reason = reason

    def historical_data(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise ValueError(self._reason)


@dataclass(frozen=True)
class DBInstrumentTokenResolver(InstrumentTokenResolver):
    repo: InstrumentRepository

    def resolve(self, instrument_id: uuid.UUID) -> int | str:
        token = self.repo.get_broker_token(instrument_id)
        try:
            return int(token)
        except ValueError:
            return token


@dataclass(frozen=True)
class DBCandleStore(BaseCandleStore):
    repo: CandleRepository
    tz: str = "Asia/Kolkata"

    def get_base_candles(
        self,
        instrument_id: uuid.UUID,
        base_interval: str,
        start,
        end,
    ) -> pd.DataFrame:
        tz = ZoneInfo(self.tz)
        start_utc = _to_utc(start, tz)
        end_utc = _to_utc(end, tz)

        rows = self.repo.list_range(
            instrument_id=instrument_id,
            base_interval=base_interval,
            start=start_utc,
            end=end_utc,
        )
        if not rows:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(rows)
        ts = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(tz).dt.tz_localize(None)
        df["timestamp"] = ts
        # Keep consistent column ordering for downstream aggregation.
        return df[["timestamp", "open", "high", "low", "close", "volume"]]

    def upsert_base_candles(self, instrument_id: uuid.UUID, base_interval: str, candles: pd.DataFrame) -> None:
        if candles.empty:
            return

        df = candles[["timestamp", "open", "high", "low", "close", "volume"]].copy()
        ts = pd.to_datetime(df["timestamp"], utc=False)
        if ts.dt.tz is None:
            ts = ts.dt.tz_localize(self.tz)
        else:
            ts = ts.dt.tz_convert(self.tz)
        ts = ts.dt.tz_convert("UTC")

        df = df.assign(ts=ts.dt.to_pydatetime())
        rows = []
        for r in df.itertuples(index=False):
            rows.append(
                {
                    "instrument_id": instrument_id,
                    "base_interval": base_interval,
                    "ts": r.ts,
                    "open": float(r.open),
                    "high": float(r.high),
                    "low": float(r.low),
                    "close": float(r.close),
                    "volume": 0 if (r.volume is None or pd.isna(r.volume)) else int(r.volume),
                }
            )
        self.repo.upsert_many(rows)


def make_market_data_service(settings: Settings, session: Session) -> MarketDataService:
    try:
        kite = make_kite_client(settings, session=session)
        fetcher = HistoricalFetcher(client=kite)
    except Exception as e:
        fetcher = HistoricalFetcher(client=_DisabledKiteClient(str(e)))
    aggregator = CandleAggregator()
    inst_repo = InstrumentRepository(session)
    resolver = DBInstrumentTokenResolver(repo=inst_repo)
    candle_store = DBCandleStore(repo=CandleRepository(session))
    return MarketDataService(
        token_resolver=resolver,
        fetcher=fetcher,
        aggregator=aggregator,
        candle_store=candle_store,
    )


def _to_utc(dt, tz: ZoneInfo):  # type: ignore[no-untyped-def]
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz).astimezone(ZoneInfo("UTC"))
    return dt.astimezone(ZoneInfo("UTC"))
