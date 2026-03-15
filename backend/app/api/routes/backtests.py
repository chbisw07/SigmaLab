from __future__ import annotations

import csv
import io
import math
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_app_settings, get_db_session
from app.core.settings import Settings
from app.models.orm import Instrument
from app.models.schemas import BacktestMetricSchema, BacktestRunSchema, BacktestTradeSchema
from app.services.market_data import make_market_data_service
from app.services.backtests import BacktestRunService
from app.services.repos.backtests import BacktestRepository

from app.backtesting.indicator_cache import IndicatorCache
from app.backtesting.strategy_evaluator import StrategyEvaluator
from data.timeframe import Timeframe
from strategies.context import StrategyContext
from strategies.service import StrategyService


router = APIRouter()


class BacktestRunCreate(BaseModel):
    strategy_slug: str = Field(min_length=1)
    watchlist_id: uuid.UUID
    timeframe: str = Field(min_length=1)
    start: datetime
    end: datetime
    params: dict[str, Any] | None = None


@router.post("")
def create_backtest_run(
    payload: BacktestRunCreate,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, Any]:
    try:
        svc = BacktestRunService.from_settings(session, settings=settings)
        result = svc.run(
            strategy_slug=payload.strategy_slug,
            watchlist_id=payload.watchlist_id,
            timeframe=payload.timeframe,
            start=payload.start,
            end=payload.end,
            params=payload.params,
        )
        return {"status": "ok", "run_id": str(result.run_id), "run_status": result.status, "metrics": result.overall_metrics}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("")
def list_backtest_runs(
    session: Session = Depends(get_db_session),
) -> dict[str, Any]:
    repo = BacktestRepository(session)
    runs = repo.list_runs(limit=50)
    return {"status": "ok", "runs": [BacktestRunSchema.model_validate(r).model_dump() for r in runs]}


@router.get("/{run_id}")
def get_backtest_run(
    run_id: uuid.UUID,
    session: Session = Depends(get_db_session),
) -> dict[str, Any]:
    repo = BacktestRepository(session)
    run = repo.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return {"status": "ok", "run": BacktestRunSchema.model_validate(run).model_dump()}


@router.get("/{run_id}/trades")
def list_backtest_trades(
    run_id: uuid.UUID,
    session: Session = Depends(get_db_session),
) -> dict[str, Any]:
    repo = BacktestRepository(session)
    trades = repo.list_trades(run_id, limit=5000)
    return {"status": "ok", "trades": [BacktestTradeSchema.model_validate(t).model_dump() for t in trades]}


@router.get("/{run_id}/metrics")
def list_backtest_metrics(
    run_id: uuid.UUID,
    session: Session = Depends(get_db_session),
) -> dict[str, Any]:
    repo = BacktestRepository(session)
    rows = repo.list_metrics(run_id)
    return {"status": "ok", "metrics": [BacktestMetricSchema.model_validate(m).model_dump() for m in rows]}


@router.get("/{run_id}/export/trades.csv")
def export_backtest_trades_csv(
    run_id: uuid.UUID,
    session: Session = Depends(get_db_session),
) -> StreamingResponse:
    repo = BacktestRepository(session)
    run = repo.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    trades = repo.list_trades(run_id, limit=100_000)
    rows = [BacktestTradeSchema.model_validate(t).model_dump() for t in trades]

    # Stable, UI-friendly column order.
    columns = [
        "symbol",
        "entry_ts",
        "entry_price",
        "exit_ts",
        "exit_price",
        "pnl",
        "pnl_pct",
        "holding_period_sec",
        "holding_period_bars",
        "entry_reason",
        "exit_reason",
        "close_reason",
        "instrument_id",
        "side",
        "quantity",
        "run_id",
        "id",
        "created_at",
        "updated_at",
    ]

    def iter_csv():  # type: ignore[no-untyped-def]
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=columns)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in columns})
        yield buf.getvalue()

    filename = f"sigmalab_backtest_trades_{run_id}.csv"
    return StreamingResponse(
        iter_csv(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{run_id}/export/metrics.csv")
def export_backtest_metrics_csv(
    run_id: uuid.UUID,
    session: Session = Depends(get_db_session),
) -> StreamingResponse:
    repo = BacktestRepository(session)
    run = repo.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    metrics_rows = repo.list_metrics(run_id)
    metrics = [BacktestMetricSchema.model_validate(m).model_dump() for m in metrics_rows]

    # Flatten metrics_json into columns (union of keys).
    keys: set[str] = set()
    for m in metrics:
        keys.update((m.get("metrics_json") or {}).keys())
    metric_cols = sorted(keys)

    columns = [
        "symbol",
        *metric_cols,
        "run_id",
        "id",
        "created_at",
        "updated_at",
    ]

    def iter_csv():  # type: ignore[no-untyped-def]
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=columns)
        w.writeheader()
        for m in metrics:
            row = {k: "" for k in columns}
            row["symbol"] = m.get("symbol") or "__portfolio__"
            row["run_id"] = m.get("run_id")
            row["id"] = m.get("id")
            row["created_at"] = m.get("created_at")
            row["updated_at"] = m.get("updated_at")
            mj = m.get("metrics_json") or {}
            for k in metric_cols:
                row[k] = mj.get(k, "")
            w.writerow(row)
        yield buf.getvalue()

    filename = f"sigmalab_backtest_metrics_{run_id}.csv"
    return StreamingResponse(
        iter_csv(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{run_id}/chart")
def get_backtest_chart_context(
    run_id: uuid.UUID,
    instrument_id: uuid.UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    include_overlays: bool = True,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, Any]:
    """Return an ergonomic payload for a run+symbol chart view.

    Truthfulness rules:
    - trade markers come from persisted trade ledger rows
    - candles come from MarketDataService (DB-first; may backfill from Kite if configured)
    - overlays are recomputed deterministically from strategy code + stored params (not persisted artifacts)
    """
    def _to_float_or_none(v: Any) -> float | None:
        try:
            if v is None:
                return None
            fv = float(v)
            return None if math.isnan(fv) else fv
        except Exception:
            return None

    repo = BacktestRepository(session)
    run = repo.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    inst = session.get(Instrument, instrument_id)
    symbol = inst.symbol if inst is not None else None

    # Prefer explicit query params, otherwise fall back to the run's recorded range.
    if start is None or end is None:
        parsed_start = None
        parsed_end = None
        if run.date_range and ".." in run.date_range:
            a, b = run.date_range.split("..", 1)
            try:
                parsed_start = datetime.fromisoformat(a)
                parsed_end = datetime.fromisoformat(b)
            except Exception:
                parsed_start = None
                parsed_end = None
        start = start or parsed_start or run.start_at
        end = end or parsed_end or run.end_at
    if start is None or end is None:
        raise HTTPException(status_code=400, detail="start/end could not be resolved for this run")

    # Candles for the run timeframe.
    tf = Timeframe.parse(run.timeframe)
    mds = make_market_data_service(settings, session=session)
    df = mds.get_candles(instrument_id=instrument_id, timeframe=tf, start=start, end=end)
    out = df.copy()
    if "timestamp" in out.columns:
        out["timestamp"] = out["timestamp"].apply(lambda x: x.isoformat() if hasattr(x, "isoformat") else str(x))
    candles = out.to_dict(orient="records")

    # Trade markers from persisted trades.
    trades = repo.list_trades(run_id, limit=100_000)
    markers: list[dict[str, Any]] = []
    for t in trades:
        if t.instrument_id == instrument_id or (t.instrument_id is None and symbol is not None and t.symbol == symbol):
            markers.append(
                {
                    "trade_id": str(t.id),
                    "type": "entry",
                    "timestamp": t.entry_ts.isoformat(),
                    "price": float(t.entry_price),
                    "label": t.entry_reason,
                }
            )
            if t.exit_ts is not None and t.exit_price is not None:
                markers.append(
                    {
                        "trade_id": str(t.id),
                        "type": "exit",
                        "timestamp": t.exit_ts.isoformat(),
                        "price": float(t.exit_price),
                        "label": t.close_reason or t.exit_reason,
                        "close_reason": t.close_reason,
                    }
                )

    overlays: dict[str, list[dict[str, Any]]] = {}
    signals: dict[str, list[bool]] = {}
    if include_overlays and run.strategy_slug:
        try:
            strat_svc = StrategyService.default()
            detail = strat_svc.get_detail(run.strategy_slug)
            strat = strat_svc.instantiate(run.strategy_slug)
            validated = strat_svc.validate(run.strategy_slug, run.params_json or {})

            evaluator = StrategyEvaluator(indicator_cache=IndicatorCache())
            ctx = StrategyContext(symbol=symbol or "UNKNOWN", timeframe=run.timeframe, start_date=start, end_date=end)
            sig = evaluator.evaluate(
                strategy=strat,
                instrument_id=instrument_id,
                symbol=symbol or "UNKNOWN",
                timeframe=run.timeframe,
                candles=df,
                params=validated,
                context=ctx,
            )

            ind_df = sig.indicators.copy()
            if not ind_df.empty:
                ts = out["timestamp"].tolist()
                for col in ind_df.columns:
                    s = ind_df[col]
                    pts: list[dict[str, Any]] = []
                    for i in range(len(ts)):
                        v = s.iloc[i] if i < len(s) else None
                        pts.append(
                            {
                                "timestamp": ts[i],
                                "value": _to_float_or_none(v),
                            }
                        )
                    overlays[col] = pts

            signals = {
                "long_entry": [bool(x) for x in sig.long_entry.fillna(False).tolist()],
                "long_exit": [bool(x) for x in sig.long_exit.fillna(False).tolist()],
            }
            _ = detail
        except Exception:
            # Do not fail the chart view if overlays cannot be computed for any reason.
            overlays = {}
            signals = {}

    return {
        "status": "ok",
        "run_id": str(run_id),
        "instrument_id": str(instrument_id),
        "symbol": symbol,
        "timeframe": run.timeframe,
        "start": start.isoformat() if hasattr(start, "isoformat") else str(start),
        "end": end.isoformat() if hasattr(end, "isoformat") else str(end),
        "candles": candles,
        "markers": markers,
        "overlays": overlays,
        "signals": signals,
    }
