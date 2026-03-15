from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from app.backtesting.candle_cache import CandleCache
from app.backtesting.metrics import combine_equity_curves, compute_metrics
from app.backtesting.models import ExecutionAssumptions, Trade
from app.backtesting.replay_engine import ReplayEngine
from app.models.orm import BacktestRunStatus
from app.services.market_data import make_market_data_service
from app.services.repos.backtests import BacktestRepository
from app.services.repos.strategy_catalog import StrategyCatalogRepository
from app.services.watchlists import WatchlistService

from data.market_data_service import MarketDataService
from data.timeframe import Timeframe
from strategies.context import StrategyContext
from strategies.service import StrategyService


def _utcnow() -> datetime:
    # Use tz-aware timestamps for persisted status fields.
    return datetime.now(tz=ZoneInfo("UTC"))


def _date_range_str(start: datetime, end: datetime) -> str:
    return f"{start.isoformat()}..{end.isoformat()}"


@dataclass(frozen=True)
class BacktestResultSummary:
    run_id: uuid.UUID
    status: str
    overall_metrics: dict[str, Any]


@dataclass(frozen=True)
class BacktestRunService:
    session: Session
    market_data_service: MarketDataService
    strategy_service: StrategyService
    replay_engine: ReplayEngine
    assumptions: ExecutionAssumptions
    tz: str = "Asia/Kolkata"
    engine_version: str = "ph4-replay-0.1"

    @classmethod
    def from_settings(cls, session: Session, *, settings) -> "BacktestRunService":  # type: ignore[no-untyped-def]
        mds = make_market_data_service(settings, session)
        # ReplayEngine is pure and does not depend on DB/broker state.
        replay = ReplayEngine()
        return cls(
            session=session,
            market_data_service=mds,
            strategy_service=StrategyService.default(),
            replay_engine=replay,
            assumptions=ExecutionAssumptions(),
        )

    def run(
        self,
        *,
        strategy_slug: str,
        watchlist_id: uuid.UUID,
        timeframe: str,
        start: datetime,
        end: datetime,
        params: dict[str, Any] | None = None,
    ) -> BacktestResultSummary:
        """Execute a backtest synchronously (PH4).

        For PH4 we run inline and persist results. Later phases can wrap this in an async job runner.
        """
        tf = Timeframe.parse(timeframe)

        # Resolve and validate the strategy.
        detail = self.strategy_service.get_detail(strategy_slug)
        validated_params = self.strategy_service.validate(strategy_slug, params)
        strat = self.strategy_service.instantiate(strategy_slug)

        # Ensure DB Strategy/StrategyVersion records exist and get StrategyVersion ID for run linkage.
        catalog = StrategyCatalogRepository(self.session)
        version = catalog.get_or_create_version(metadata=detail.metadata, parameters=detail.parameters)

        wl_svc = WatchlistService(self.session)
        instruments = wl_svc.list_instruments(watchlist_id)
        snapshot = [{"instrument_id": str(i.id), "symbol": i.symbol, "exchange": i.exchange} for i in instruments]

        repo = BacktestRepository(self.session)
        start_at = _to_utc(start, self.tz)
        end_at = _to_utc(end, self.tz)
        run_row = repo.create_run(
            strategy_version_id=version.id,
            strategy_slug=detail.metadata.slug,
            strategy_code_version=detail.metadata.version,
            watchlist_id=watchlist_id,
            watchlist_snapshot_json=snapshot,
            timeframe=tf.value,
            date_range=_date_range_str(start, end),
            start_at=start_at,
            end_at=end_at,
            params_json=validated_params.values,
            execution_assumptions_json=self.assumptions.to_json(),
            engine_version=self.engine_version,
        )

        started_at = _utcnow()
        repo.set_status(run_row.id, status=BacktestRunStatus.RUNNING, started_at=started_at)

        try:
            cache = CandleCache()
            engine = self.replay_engine

            all_trades_rows: list[dict] = []
            all_trades: list[Trade] = []
            per_symbol_metrics: list[tuple[str, dict[str, Any], list[dict], list[dict]]] = []
            per_symbol_equity: list[list] = []

            for inst in instruments:
                sym = inst.symbol
                candles = cache.get(
                    self.market_data_service,
                    instrument_id=inst.id,
                    timeframe=tf,
                    start=start,
                    end=end,
                )
                if candles is None or candles.empty:
                    continue

                # Enforce expected candle shape for strategy + replay.
                candles = candles[["timestamp", "open", "high", "low", "close", "volume"]].copy()
                ctx = StrategyContext(symbol=sym, timeframe=tf.value, start_date=start, end_date=end)
                sig = strat.generate_signals(candles, params=validated_params, context=ctx)  # type: ignore[arg-type]
                replay = engine.run(
                    candles,
                    sig,
                    metadata=detail.metadata,
                    symbol=sym,
                    instrument_id=inst.id,
                    run_id=run_row.id,
                )

                if replay.trades:
                    all_trades_rows.extend([t.to_orm_row() for t in replay.trades])
                    all_trades.extend(replay.trades)

                metrics_res = compute_metrics(replay.trades, replay.equity_curve)
                per_symbol_equity.append(metrics_res.equity_curve)
                per_symbol_metrics.append(
                    (
                        sym,
                        metrics_res.metrics,
                        [p.to_json() for p in metrics_res.equity_curve],
                        [p.to_json() for p in metrics_res.drawdown_curve],
                    )
                )

            if all_trades_rows:
                repo.add_trades(all_trades_rows)

            # Persist per-symbol metrics.
            for sym, m, eq, dd in per_symbol_metrics:
                repo.upsert_metrics(
                    run_id=run_row.id,
                    symbol=sym,
                    metrics_json=m,
                    equity_curve_json=eq,
                    drawdown_curve_json=dd,
                )

            # Portfolio-level metrics (equal-weight curve).
            portfolio_curve = combine_equity_curves(per_symbol_equity)
            portfolio_res = compute_metrics(
                trades=all_trades,
                equity_curve=portfolio_curve,
            )
            repo.upsert_metrics(
                run_id=run_row.id,
                symbol=None,
                metrics_json=portfolio_res.metrics,
                equity_curve_json=[p.to_json() for p in portfolio_res.equity_curve],
                drawdown_curve_json=[p.to_json() for p in portfolio_res.drawdown_curve],
            )

            repo.set_status(run_row.id, status=BacktestRunStatus.SUCCESS, completed_at=_utcnow())

            return BacktestResultSummary(
                run_id=run_row.id,
                status=BacktestRunStatus.SUCCESS.value,
                overall_metrics=portfolio_res.metrics,
            )
        except Exception:
            repo.set_status(run_row.id, status=BacktestRunStatus.FAILED, completed_at=_utcnow())
            raise


def _to_utc(dt: datetime, tz: str) -> datetime:
    """Convert naive local datetimes into UTC for persistence."""
    local_tz = ZoneInfo(tz)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=local_tz).astimezone(ZoneInfo("UTC"))
    return dt.astimezone(ZoneInfo("UTC"))
