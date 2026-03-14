from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.core.settings import Settings
from app.services.kite_provider import make_kite_client
from app.services.repos.instruments import InstrumentRepository

from data.candle_aggregator import CandleAggregator
from data.historical_fetcher import HistoricalFetcher
from data.market_data_service import InstrumentTokenResolver, MarketDataService


@dataclass(frozen=True)
class DBInstrumentTokenResolver(InstrumentTokenResolver):
    repo: InstrumentRepository

    def resolve(self, instrument_id: uuid.UUID) -> int | str:
        token = self.repo.get_broker_token(instrument_id)
        try:
            return int(token)
        except ValueError:
            return token


def make_market_data_service(settings: Settings, repo: InstrumentRepository) -> MarketDataService:
    kite = make_kite_client(settings)
    fetcher = HistoricalFetcher(client=kite)
    aggregator = CandleAggregator()
    resolver = DBInstrumentTokenResolver(repo=repo)
    return MarketDataService(token_resolver=resolver, fetcher=fetcher, aggregator=aggregator)

