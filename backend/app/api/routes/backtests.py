from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_app_settings, get_db_session
from app.core.settings import Settings
from app.models.schemas import BacktestMetricSchema, BacktestRunSchema, BacktestTradeSchema
from app.services.backtests import BacktestRunService
from app.services.repos.backtests import BacktestRepository


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

