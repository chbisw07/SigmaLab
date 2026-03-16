from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from app.backtesting.indicator_cache import IndicatorCache
from app.backtesting.metrics import combine_equity_curves, compute_metrics
from app.backtesting.models import ExecutionAssumptions, Trade
from app.backtesting.replay_engine import ReplayEngine
from app.backtesting.strategy_evaluator import StrategyEvaluator
from app.models.orm import BacktestRunStatus, OptimizationJobStatus
from app.optimization.search_space import ParamGrid, SearchSpaceError, build_param_grid
from app.services.backtests import BacktestRunService
from app.services.repos.backtests import BacktestRepository
from app.services.repos.optimizations import OptimizationRepository
from app.services.repos.presets import ParameterPresetRepository
from app.services.repos.strategy_catalog import StrategyCatalogRepository
from app.services.watchlists import WatchlistService
from strategies.context import StrategyContext
from strategies.service import StrategyService


def _utcnow() -> datetime:
    return datetime.now(tz=ZoneInfo("UTC"))


def _to_utc(dt: datetime, tz: str) -> datetime:
    local_tz = ZoneInfo(tz)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=local_tz).astimezone(ZoneInfo("UTC"))
    return dt.astimezone(ZoneInfo("UTC"))


@dataclass(frozen=True)
class OptimizationCreateInput:
    strategy_slug: str
    watchlist_id: uuid.UUID
    timeframe: str
    start: datetime
    end: datetime
    objective_metric: str
    sort_direction: str  # "asc" | "desc"
    selection: dict[str, dict[str, Any]]
    max_combinations: int = 250


@dataclass(frozen=True)
class OptimizationCreateResult:
    job_id: uuid.UUID
    total_combinations: int


@dataclass(frozen=True)
class OptimizationService:
    """PH5 optimization orchestrator over PH4 backtesting.

    This service is designed to be run in a background task (long-running).
    """

    session: Session
    assumptions: ExecutionAssumptions
    tz: str = "Asia/Kolkata"
    engine_version: str = "ph4-replay-0.1"

    @classmethod
    def default(cls, session: Session) -> "OptimizationService":
        return cls(session=session, assumptions=ExecutionAssumptions())

    def preview(self, *, strategy_slug: str, selection: dict[str, dict[str, Any]]) -> dict[str, Any]:
        svc = StrategyService.default()
        detail = svc.get_detail(strategy_slug)
        grid = build_param_grid(specs=detail.parameters, selection=selection)
        return {
            "status": "ok",
            "total_combinations": grid.combination_count(),
            "keys": grid.keys_sorted(),
        }

    def create_job(self, *, inp: OptimizationCreateInput) -> OptimizationCreateResult:
        # Resolve strategy, validate selection against strategy schema.
        strat_svc = StrategyService.default()
        detail = strat_svc.get_detail(inp.strategy_slug)

        try:
            grid = build_param_grid(specs=detail.parameters, selection=inp.selection)
        except SearchSpaceError as e:
            raise ValueError(str(e)) from e

        total = grid.combination_count()
        if total <= 0:
            raise ValueError("Search space produced 0 combinations")
        if total > inp.max_combinations:
            raise ValueError(
                f"Search space too large: {total} combinations exceeds max {inp.max_combinations}. "
                "Reduce params, narrow ranges, or increase step."
            )

        # Ensure DB Strategy/StrategyVersion exist.
        catalog = StrategyCatalogRepository(self.session)
        version = catalog.get_or_create_version(metadata=detail.metadata, parameters=detail.parameters)

        repo = OptimizationRepository(self.session)
        job = repo.create_job(
            strategy_version_id=version.id,
            strategy_slug=detail.metadata.slug,
            strategy_code_version=detail.metadata.version,
            watchlist_id=inp.watchlist_id,
            timeframe=inp.timeframe,
            start_at=_to_utc(inp.start, self.tz),
            end_at=_to_utc(inp.end, self.tz),
            objective_metric=inp.objective_metric,
            sort_direction=inp.sort_direction,
            total_combinations=total,
            search_space_json={
                "selection": inp.selection,
                "max_combinations": inp.max_combinations,
                "param_keys": grid.keys_sorted(),
            },
            execution_assumptions_json=self.assumptions.to_json(),
        )
        return OptimizationCreateResult(job_id=job.id, total_combinations=total)

    def run_job(self, *, job_id: uuid.UUID, settings) -> None:  # type: ignore[no-untyped-def]
        """Execute an optimization job (grid search) and persist ranked candidates."""
        opt_repo = OptimizationRepository(self.session)
        job = opt_repo.get_job(job_id)
        if job is None:
            raise KeyError("optimization job not found")

        opt_repo.set_status(job_id, status=OptimizationJobStatus.RUNNING, started_at=_utcnow())

        try:
            strat_svc = StrategyService.default()
            if job.strategy_slug is None:
                raise RuntimeError("optimization job missing strategy_slug snapshot")
            detail = strat_svc.get_detail(job.strategy_slug)
            strat = strat_svc.instantiate(job.strategy_slug)

            # Rebuild the grid deterministically from persisted selection.
            sel = (job.search_space_json or {}).get("selection") or {}
            grid: ParamGrid = build_param_grid(specs=detail.parameters, selection=sel)
            combos = grid.enumerate()

            # Prepare candles once for this job.
            bt = BacktestRunService.from_settings(self.session, settings=settings)
            wl_svc = WatchlistService(self.session)
            instruments = wl_svc.list_instruments(job.watchlist_id)
            prepared = bt._prepare_input(  # noqa: SLF001 (intentional reuse)
                strategy_slug=job.strategy_slug,
                timeframe=job.timeframe,
                start=(job.start_at or datetime.now()).astimezone(ZoneInfo(self.tz)),
                end=(job.end_at or datetime.now()).astimezone(ZoneInfo(self.tz)),
                instruments=instruments,
            )

            ind_cache = IndicatorCache()
            evaluator = StrategyEvaluator(indicator_cache=ind_cache)
            engine = ReplayEngine()
            bt_repo = BacktestRepository(self.session)

            # Persist candidate runs as we go, and keep a compact in-memory summary for ranking.
            candidate_summaries: list[dict[str, Any]] = []

            completed = 0
            for params in combos:
                # Validate params using the strategy schema.
                validated = strat_svc.validate(job.strategy_slug, params)

                # Persist a BacktestRun for this candidate.
                version = job.strategy_version_id
                snapshot = [{"instrument_id": str(i.id), "symbol": i.symbol, "exchange": i.exchange} for i in instruments]
                run_row = bt_repo.create_run(
                    strategy_version_id=version,
                    strategy_slug=detail.metadata.slug,
                    strategy_code_version=detail.metadata.version,
                    watchlist_id=job.watchlist_id,
                    watchlist_snapshot_json=snapshot,
                    timeframe=job.timeframe,
                    date_range=f"{job.start_at.isoformat() if job.start_at else ''}..{job.end_at.isoformat() if job.end_at else ''}",
                    start_at=job.start_at,
                    end_at=job.end_at,
                    params_json=validated.values,
                    execution_assumptions_json=job.execution_assumptions_json or {},
                    engine_version=self.engine_version,
                )
                bt_repo.set_status(run_row.id, status=BacktestRunStatus.RUNNING, started_at=_utcnow())

                # Run PH4 backtest loop using prepared inputs.
                all_trades_rows: list[dict] = []
                all_trades: list[Trade] = []
                per_symbol_equity = []

                per_symbol_metrics_payload: list[tuple[str, dict[str, Any], list[dict], list[dict]]] = []

                for sym_input in prepared.symbols:
                    sym = sym_input.symbol
                    candles = sym_input.candles
                    if candles is None or candles.empty:
                        continue

                    ctx = StrategyContext(symbol=sym, timeframe=job.timeframe, start_date=job.start_at, end_date=job.end_at)
                    sig = evaluator.evaluate(
                        strategy=strat,
                        instrument_id=sym_input.instrument_id,
                        symbol=sym,
                        timeframe=job.timeframe,
                        candles=candles,
                        params=validated,
                        context=ctx,
                    )
                    replay = engine.run(
                        candles,
                        sig,
                        metadata=detail.metadata,
                        symbol=sym,
                        instrument_id=sym_input.instrument_id,
                        run_id=run_row.id,
                    )
                    if replay.trades:
                        all_trades_rows.extend([t.to_orm_row() for t in replay.trades])
                        all_trades.extend(replay.trades)

                    mres = compute_metrics(replay.trades, replay.equity_curve)
                    per_symbol_equity.append(mres.equity_curve)
                    per_symbol_metrics_payload.append(
                        (
                            sym,
                            mres.metrics,
                            [p.to_json() for p in mres.equity_curve],
                            [p.to_json() for p in mres.drawdown_curve],
                        )
                    )

                if all_trades_rows:
                    bt_repo.add_trades(all_trades_rows)
                for sym, m, eq, dd in per_symbol_metrics_payload:
                    bt_repo.upsert_metrics(
                        run_id=run_row.id,
                        symbol=sym,
                        metrics_json=m,
                        equity_curve_json=eq,
                        drawdown_curve_json=dd,
                    )

                portfolio_curve = combine_equity_curves(per_symbol_equity)
                portfolio_res = compute_metrics(all_trades, portfolio_curve)
                bt_repo.upsert_metrics(
                    run_id=run_row.id,
                    symbol=None,
                    metrics_json=portfolio_res.metrics,
                    equity_curve_json=[p.to_json() for p in portfolio_res.equity_curve],
                    drawdown_curve_json=[p.to_json() for p in portfolio_res.drawdown_curve],
                )
                bt_repo.set_status(run_row.id, status=BacktestRunStatus.SUCCESS, completed_at=_utcnow())

                obj = float(portfolio_res.metrics.get(job.objective_metric, 0.0))
                candidate_summaries.append(
                    {
                        "backtest_run_id": run_row.id,
                        "params_json": validated.values,
                        "objective_value": obj,
                        "metrics_json": portfolio_res.metrics,
                    }
                )

                completed += 1
                if completed % 5 == 0 or completed == len(combos):
                    opt_repo.set_progress(job_id, completed_combinations=completed)

            # Rank and persist candidates metadata rows.
            reverse = (job.sort_direction or "desc").lower() != "asc"
            ranked = sorted(candidate_summaries, key=lambda r: r["objective_value"], reverse=reverse)

            for idx, row in enumerate(ranked, start=1):
                opt_repo.add_candidate(
                    optimization_job_id=job_id,
                    backtest_run_id=row["backtest_run_id"],
                    rank=idx,
                    params_json=row["params_json"],
                    objective_value=row["objective_value"],
                    metrics_json=row["metrics_json"],
                )

            # Summary: store top-N and basic stats.
            top = ranked[: min(10, len(ranked))]
            opt_repo.set_result_summary(
                job_id,
                result_summary_json={
                    "total_candidates": len(ranked),
                    "objective_metric": job.objective_metric,
                    "sort_direction": job.sort_direction,
                    "top": [
                        {
                            "rank": i + 1,
                            "objective_value": t["objective_value"],
                            "backtest_run_id": str(t["backtest_run_id"]),
                            "params_json": t["params_json"],
                        }
                        for i, t in enumerate(top)
                    ],
                },
            )

            opt_repo.set_status(job_id, status=OptimizationJobStatus.SUCCESS, completed_at=_utcnow())
        except Exception:
            opt_repo.set_status(job_id, status=OptimizationJobStatus.FAILED, completed_at=_utcnow())
            raise

    def save_preset_from_candidate(
        self,
        *,
        job_id: uuid.UUID,
        candidate_id: uuid.UUID,
        name: str,
    ):
        opt_repo = OptimizationRepository(self.session)
        job = opt_repo.get_job(job_id)
        if job is None:
            raise KeyError("optimization job not found")
        candidates = opt_repo.list_candidates(job_id, limit=100_000)
        cand = next((c for c in candidates if c.id == candidate_id), None)
        if cand is None:
            raise KeyError("candidate not found")
        preset_repo = ParameterPresetRepository(self.session)
        return preset_repo.create(strategy_version_id=job.strategy_version_id, name=name, values_json=cand.params_json)

