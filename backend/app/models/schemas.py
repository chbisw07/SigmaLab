from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.orm import (
    BacktestRunStatus,
    BrokerConnectionStatus,
    BrokerName,
    OptimizationJobStatus,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Timestamped(ORMModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class BrokerConnectionSchema(Timestamped):
    broker_name: BrokerName
    status: BrokerConnectionStatus
    config_metadata: dict
    last_connected_at: datetime | None = None
    last_verified_at: datetime | None = None


class InstrumentSchema(Timestamped):
    broker_instrument_token: str
    exchange: str
    symbol: str
    name: str | None = None
    segment: str | None = None
    instrument_metadata: dict


class WatchlistSchema(Timestamped):
    name: str
    description: str | None = None


class StrategySchema(Timestamped):
    name: str
    slug: str
    category: str | None = None
    description: str | None = None
    code_ref: str | None = None


class StrategyVersionSchema(Timestamped):
    strategy_id: uuid.UUID
    version: str
    changelog: str | None = None
    parameter_schema: dict
    default_params: dict


class ParameterPresetSchema(Timestamped):
    strategy_version_id: uuid.UUID
    name: str
    values_json: dict


class BacktestRunSchema(Timestamped):
    strategy_version_id: uuid.UUID
    watchlist_id: uuid.UUID
    timeframe: str
    date_range: str
    params_json: dict
    status: BacktestRunStatus
    engine_version: str | None = None
    completed_at: datetime | None = None


class BacktestTradeSchema(Timestamped):
    run_id: uuid.UUID
    symbol: str
    entry_ts: datetime
    exit_ts: datetime | None = None
    entry_price: float
    exit_price: float | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    entry_reason: str | None = None
    exit_reason: str | None = None


class OptimizationJobSchema(Timestamped):
    strategy_version_id: uuid.UUID
    watchlist_id: uuid.UUID
    search_space_json: dict
    status: OptimizationJobStatus
    result_summary_json: dict
