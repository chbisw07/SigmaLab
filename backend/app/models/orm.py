from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin


class BrokerName(enum.StrEnum):
    ZERODHA_KITE = "zerodha_kite"


class BrokerConnectionStatus(enum.StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ERROR = "error"


class BacktestRunStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class OptimizationJobStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class BrokerConnection(Base, IdMixin, TimestampMixin):
    __tablename__ = "broker_connections"

    broker_name: Mapped[BrokerName] = mapped_column(Enum(BrokerName), nullable=False)
    status: Mapped[BrokerConnectionStatus] = mapped_column(
        Enum(BrokerConnectionStatus), nullable=False, default=BrokerConnectionStatus.DISCONNECTED
    )
    config_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    encrypted_secrets: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Instrument(Base, IdMixin, TimestampMixin):
    __tablename__ = "instruments"

    broker_instrument_token: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(16), nullable=False)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(128))
    segment: Mapped[str | None] = mapped_column(String(32))
    instrument_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )


class Watchlist(Base, IdMixin, TimestampMixin):
    __tablename__ = "watchlists"

    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)

    items: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="watchlist", cascade="all, delete-orphan"
    )


class WatchlistItem(Base, IdMixin, TimestampMixin):
    __tablename__ = "watchlist_items"

    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("watchlists.id"), nullable=False, index=True
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("instruments.id"), nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    watchlist: Mapped[Watchlist] = relationship(back_populates="items")


class Strategy(Base, IdMixin, TimestampMixin):
    __tablename__ = "strategies"

    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    code_ref: Mapped[str | None] = mapped_column(String(256))
    current_version_id: Mapped[str | None] = mapped_column(ForeignKey("strategy_versions.id"))

    versions: Mapped[list["StrategyVersion"]] = relationship(back_populates="strategy")


class StrategyVersion(Base, IdMixin, TimestampMixin):
    __tablename__ = "strategy_versions"

    strategy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("strategies.id"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text)
    parameter_schema: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    default_params: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    strategy: Mapped[Strategy] = relationship(back_populates="versions")


class ParameterPreset(Base, IdMixin, TimestampMixin):
    __tablename__ = "parameter_presets"

    strategy_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("strategy_versions.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    values_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class BacktestRun(Base, IdMixin, TimestampMixin):
    __tablename__ = "backtest_runs"

    strategy_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("strategy_versions.id"), nullable=False, index=True
    )
    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("watchlists.id"), nullable=False, index=True
    )
    timeframe: Mapped[str] = mapped_column(String(16), nullable=False)
    date_range: Mapped[str] = mapped_column(String(64), nullable=False)
    params_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[BacktestRunStatus] = mapped_column(
        Enum(BacktestRunStatus), nullable=False, default=BacktestRunStatus.PENDING
    )
    engine_version: Mapped[str | None] = mapped_column(String(64))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BacktestTrade(Base, IdMixin, TimestampMixin):
    __tablename__ = "backtest_trades"

    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("backtest_runs.id"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    entry_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entry_price: Mapped[float] = mapped_column(nullable=False)
    exit_price: Mapped[float | None] = mapped_column()
    pnl: Mapped[float | None] = mapped_column()
    pnl_pct: Mapped[float | None] = mapped_column()
    entry_reason: Mapped[str | None] = mapped_column(Text)
    exit_reason: Mapped[str | None] = mapped_column(Text)


class OptimizationJob(Base, IdMixin, TimestampMixin):
    __tablename__ = "optimization_jobs"

    strategy_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("strategy_versions.id"), nullable=False, index=True
    )
    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("watchlists.id"), nullable=False, index=True
    )
    search_space_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[OptimizationJobStatus] = mapped_column(
        Enum(OptimizationJobStatus), nullable=False, default=OptimizationJobStatus.PENDING
    )
    result_summary_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
