from __future__ import annotations

import uuid
from dataclasses import dataclass

import pandas as pd
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.services.kite_provider import make_kite_client
from app.services.repos.candles import CandleRepository
from app.services.repos.instruments import InstrumentRepository

from data.candle_aggregator import CandleAggregator
from data.historical_fetcher import HistoricalFetcher
from data.market_data_service import BaseCandleStore, InstrumentTokenResolver, MarketDataService


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
    kite = make_kite_client(settings)
    fetcher = HistoricalFetcher(client=kite)
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
