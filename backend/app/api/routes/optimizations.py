from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_app_settings, get_database, get_db_session
from app.core.db import Database
from app.core.settings import Settings
from app.models.schemas import OptimizationCandidateResultSchema, OptimizationJobSchema, ParameterPresetSchema
from app.services.optimizations import OptimizationCreateInput, OptimizationService
from app.services.repos.optimizations import OptimizationRepository

router = APIRouter()


class OptimizationPreviewRequest(BaseModel):
    strategy_slug: str = Field(min_length=1)
    selection: dict[str, dict[str, Any]]


class OptimizationCreateRequest(BaseModel):
    strategy_slug: str = Field(min_length=1)
    watchlist_id: uuid.UUID
    timeframe: str = Field(min_length=1)
    start: datetime
    end: datetime
    objective_metric: str = Field(min_length=1, default="net_return_pct")
    sort_direction: str = Field(min_length=3, default="desc")  # "asc" | "desc"
    selection: dict[str, dict[str, Any]]
    max_combinations: int = Field(default=250, ge=1, le=10_000)


class SavePresetRequest(BaseModel):
    candidate_id: uuid.UUID
    name: str = Field(min_length=1, max_length=128)


def _run_job_bg(job_id: uuid.UUID, *, db: Database, settings: Settings) -> None:
    # Run the long job in a separate session.
    session = db.session()
    try:
        OptimizationService.default(session).run_job(job_id=job_id, settings=settings)
    finally:
        session.close()


@router.post("/preview")
def preview_optimization(
    payload: OptimizationPreviewRequest,
    session: Session = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        svc = OptimizationService.default(session)
        return svc.preview(strategy_slug=payload.strategy_slug, selection=payload.selection)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("")
def create_optimization(
    payload: OptimizationCreateRequest,
    background: BackgroundTasks,
    session: Session = Depends(get_db_session),
    db: Database = Depends(get_database),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, Any]:
    try:
        svc = OptimizationService.default(session)
        res = svc.create_job(
            inp=OptimizationCreateInput(
                strategy_slug=payload.strategy_slug,
                watchlist_id=payload.watchlist_id,
                timeframe=payload.timeframe,
                start=payload.start,
                end=payload.end,
                objective_metric=payload.objective_metric,
                sort_direction=payload.sort_direction,
                selection=payload.selection,
                max_combinations=payload.max_combinations,
            )
        )
        background.add_task(_run_job_bg, res.job_id, db=db, settings=settings)
        return {"status": "ok", "job_id": str(res.job_id), "total_combinations": res.total_combinations}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("")
def list_optimizations(session: Session = Depends(get_db_session)) -> dict[str, Any]:
    repo = OptimizationRepository(session)
    jobs = repo.list_jobs(limit=50)
    return {"status": "ok", "jobs": [OptimizationJobSchema.model_validate(j).model_dump() for j in jobs]}


@router.get("/{job_id}")
def get_optimization(job_id: uuid.UUID, session: Session = Depends(get_db_session)) -> dict[str, Any]:
    repo = OptimizationRepository(session)
    job = repo.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="optimization job not found")
    return {"status": "ok", "job": OptimizationJobSchema.model_validate(job).model_dump()}


@router.get("/{job_id}/candidates")
def list_candidates(job_id: uuid.UUID, session: Session = Depends(get_db_session)) -> dict[str, Any]:
    repo = OptimizationRepository(session)
    job = repo.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="optimization job not found")
    rows = repo.list_candidates(job_id, limit=5000)
    return {"status": "ok", "candidates": [OptimizationCandidateResultSchema.model_validate(r).model_dump() for r in rows]}


@router.post("/{job_id}/save-preset")
def save_preset(
    job_id: uuid.UUID,
    payload: SavePresetRequest,
    session: Session = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        svc = OptimizationService.default(session)
        preset = svc.save_preset_from_candidate(job_id=job_id, candidate_id=payload.candidate_id, name=payload.name)
        return {"status": "ok", "preset": ParameterPresetSchema.model_validate(preset).model_dump()}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

