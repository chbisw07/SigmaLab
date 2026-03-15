from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import BacktestMetric, BacktestRun, BacktestRunStatus, BacktestTrade


@dataclass(frozen=True)
class BacktestRepository:
    session: Session

    def create_run(
        self,
        *,
        strategy_version_id: uuid.UUID,
        strategy_slug: str | None,
        strategy_code_version: str | None,
        watchlist_id: uuid.UUID,
        watchlist_snapshot_json: list[dict],
        timeframe: str,
        date_range: str,
        start_at: datetime | None,
        end_at: datetime | None,
        params_json: dict,
        execution_assumptions_json: dict,
        engine_version: str,
    ) -> BacktestRun:
        run = BacktestRun(
            strategy_version_id=strategy_version_id,
            strategy_slug=strategy_slug,
            strategy_code_version=strategy_code_version,
            watchlist_id=watchlist_id,
            watchlist_snapshot_json=watchlist_snapshot_json,
            timeframe=timeframe,
            date_range=date_range,
            start_at=start_at,
            end_at=end_at,
            params_json=params_json,
            execution_assumptions_json=execution_assumptions_json,
            status=BacktestRunStatus.PENDING,
            engine_version=engine_version,
            started_at=None,
            completed_at=None,
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def set_status(
        self,
        run_id: uuid.UUID,
        *,
        status: BacktestRunStatus,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        run = self.session.get(BacktestRun, run_id)
        if run is None:
            raise KeyError("backtest run not found")
        run.status = status
        if started_at is not None:
            run.started_at = started_at
        if completed_at is not None:
            run.completed_at = completed_at
        self.session.commit()

    def add_trades(self, trades: list[dict]) -> int:
        if not trades:
            return 0
        objs = [BacktestTrade(**t) for t in trades]
        self.session.add_all(objs)
        self.session.commit()
        return len(objs)

    def upsert_metrics(
        self,
        *,
        run_id: uuid.UUID,
        symbol: str | None,
        metrics_json: dict,
        equity_curve_json: list[dict],
        drawdown_curve_json: list[dict],
    ) -> BacktestMetric:
        stmt = select(BacktestMetric).where(BacktestMetric.run_id == run_id).where(BacktestMetric.symbol == symbol)
        existing = self.session.execute(stmt).scalars().first()
        if existing is None:
            existing = BacktestMetric(
                run_id=run_id,
                symbol=symbol,
                metrics_json=metrics_json,
                equity_curve_json=equity_curve_json,
                drawdown_curve_json=drawdown_curve_json,
            )
            self.session.add(existing)
        else:
            existing.metrics_json = metrics_json
            existing.equity_curve_json = equity_curve_json
            existing.drawdown_curve_json = drawdown_curve_json
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def list_runs(self, limit: int = 50) -> list[BacktestRun]:
        stmt = select(BacktestRun).order_by(BacktestRun.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars())

    def get_run(self, run_id: uuid.UUID) -> BacktestRun | None:
        return self.session.get(BacktestRun, run_id)

    def list_trades(self, run_id: uuid.UUID, limit: int = 2000) -> list[BacktestTrade]:
        stmt = select(BacktestTrade).where(BacktestTrade.run_id == run_id).order_by(BacktestTrade.entry_ts.asc()).limit(limit)
        return list(self.session.execute(stmt).scalars())

    def list_metrics(self, run_id: uuid.UUID) -> list[BacktestMetric]:
        stmt = select(BacktestMetric).where(BacktestMetric.run_id == run_id).order_by(BacktestMetric.symbol.asc().nullsfirst())
        return list(self.session.execute(stmt).scalars())

