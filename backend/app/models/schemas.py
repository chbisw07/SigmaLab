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
    strategy_slug: str | None = None
    strategy_code_version: str | None = None
    watchlist_id: uuid.UUID
    watchlist_snapshot_json: list[dict]
    timeframe: str
    date_range: str
    start_at: datetime | None = None
    end_at: datetime | None = None
    params_json: dict
    execution_assumptions_json: dict
    status: BacktestRunStatus
    engine_version: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class BacktestTradeSchema(Timestamped):
    run_id: uuid.UUID
    instrument_id: uuid.UUID | None = None
    symbol: str
    side: str
    quantity: float
    entry_ts: datetime
    exit_ts: datetime | None = None
    holding_period_sec: int | None = None
    holding_period_bars: int | None = None
    entry_price: float
    exit_price: float | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    entry_reason: str | None = None
    exit_reason: str | None = None
    close_reason: str | None = None


class BacktestMetricSchema(Timestamped):
    run_id: uuid.UUID
    symbol: str | None = None
    metrics_json: dict
    equity_curve_json: list[dict]
    drawdown_curve_json: list[dict]


class OptimizationJobSchema(Timestamped):
    strategy_version_id: uuid.UUID
    watchlist_id: uuid.UUID
    search_space_json: dict
    status: OptimizationJobStatus
    result_summary_json: dict
