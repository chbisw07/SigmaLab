from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, Index, String, Text, UniqueConstraint, Uuid, func
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
    __table_args__ = (
        UniqueConstraint(
            "broker_instrument_token",
            "exchange",
            name="uq_instruments_broker_token_exchange",
        ),
    )

    broker_instrument_token: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(16), nullable=False)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(128))
    segment: Mapped[str | None] = mapped_column(String(32))
    instrument_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )


class Candle(Base, TimestampMixin):
    """Base timeframe candle storage.

    PH2 stores only base (broker-supported) intervals. Higher timeframes are produced via aggregation.
    """

    __tablename__ = "candles"
    __table_args__ = (
        # Critical lookup index for historical ranges.
        Index("ix_candles_instrument_ts", "instrument_id", "ts"),
    )

    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("instruments.id"), primary_key=True
    )
    base_interval: Mapped[str] = mapped_column(String(16), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)

    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int | None] = mapped_column(BigInteger)


class Watchlist(Base, IdMixin, TimestampMixin):
    __tablename__ = "watchlists"

    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)

    items: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="watchlist", cascade="all, delete-orphan"
    )


class WatchlistItem(Base, IdMixin, TimestampMixin):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint(
            "watchlist_id",
            "instrument_id",
            name="uq_watchlist_items_watchlist_instrument",
        ),
    )

    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("watchlists.id"), nullable=False, index=True
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("instruments.id"), nullable=False, index=True
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
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("strategy_versions.id")
    )

    versions: Mapped[list["StrategyVersion"]] = relationship(back_populates="strategy")


class StrategyVersion(Base, IdMixin, TimestampMixin):
    __tablename__ = "strategy_versions"

    strategy_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("strategies.id"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text)
    parameter_schema: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    default_params: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    strategy: Mapped[Strategy] = relationship(back_populates="versions")


class ParameterPreset(Base, IdMixin, TimestampMixin):
    __tablename__ = "parameter_presets"

    strategy_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("strategy_versions.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    values_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class BacktestRun(Base, IdMixin, TimestampMixin):
    __tablename__ = "backtest_runs"

    strategy_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("strategy_versions.id"), nullable=False, index=True
    )
    # Snapshot the strategy identity in run records for reproducibility even if DB catalog evolves.
    strategy_slug: Mapped[str | None] = mapped_column(String(128), index=True)
    strategy_code_version: Mapped[str | None] = mapped_column(String(32))

    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("watchlists.id"), nullable=False, index=True
    )
    # Snapshot the watchlist constituents at run time so later watchlist edits don't affect reproducibility.
    watchlist_snapshot_json: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)

    timeframe: Mapped[str] = mapped_column(String(16), nullable=False)
    date_range: Mapped[str] = mapped_column(String(64), nullable=False)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    params_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    execution_assumptions_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    status: Mapped[BacktestRunStatus] = mapped_column(
        Enum(BacktestRunStatus), nullable=False, default=BacktestRunStatus.PENDING
    )
    engine_version: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BacktestTrade(Base, IdMixin, TimestampMixin):
    __tablename__ = "backtest_trades"
    __table_args__ = (
        Index("ix_backtest_trades_run_symbol_entry_ts", "run_id", "symbol", "entry_ts"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("backtest_runs.id"), nullable=False, index=True
    )
    instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("instruments.id"), index=True
    )
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False, default="long")
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    entry_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    holding_period_sec: Mapped[int | None] = mapped_column(BigInteger)
    holding_period_bars: Mapped[int | None] = mapped_column(BigInteger)
    entry_price: Mapped[float] = mapped_column(nullable=False)
    exit_price: Mapped[float | None] = mapped_column()
    pnl: Mapped[float | None] = mapped_column()
    pnl_pct: Mapped[float | None] = mapped_column()
    entry_reason: Mapped[str | None] = mapped_column(Text)
    exit_reason: Mapped[str | None] = mapped_column(Text)
    close_reason: Mapped[str | None] = mapped_column(String(32), index=True)


class BacktestMetric(Base, IdMixin, TimestampMixin):
    """Backtest metrics and visualization-ready series artifacts.

    Store a single row for overall (portfolio-level) metrics with symbol=None, plus
    optional per-symbol rows with symbol set.
    """

    __tablename__ = "backtest_metrics"
    __table_args__ = (
        Index("ix_backtest_metrics_run_id", "run_id"),
        Index("ix_backtest_metrics_run_symbol", "run_id", "symbol"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("backtest_runs.id"), nullable=False, index=True
    )
    symbol: Mapped[str | None] = mapped_column(String(64))

    metrics_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    equity_curve_json: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    drawdown_curve_json: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)


class OptimizationJob(Base, IdMixin, TimestampMixin):
    __tablename__ = "optimization_jobs"

    strategy_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("strategy_versions.id"), nullable=False, index=True
    )
    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("watchlists.id"), nullable=False, index=True
    )
    search_space_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[OptimizationJobStatus] = mapped_column(
        Enum(OptimizationJobStatus), nullable=False, default=OptimizationJobStatus.PENDING
    )
    result_summary_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
