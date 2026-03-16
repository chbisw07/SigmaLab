from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import (
    OptimizationCandidateResult,
    OptimizationJob,
    OptimizationJobStatus,
)


@dataclass(frozen=True)
class OptimizationRepository:
    session: Session

    def create_job(
        self,
        *,
        strategy_version_id: uuid.UUID,
        strategy_slug: str | None,
        strategy_code_version: str | None,
        watchlist_id: uuid.UUID,
        timeframe: str,
        start_at: datetime | None,
        end_at: datetime | None,
        objective_metric: str,
        sort_direction: str,
        total_combinations: int,
        search_space_json: dict,
        execution_assumptions_json: dict,
    ) -> OptimizationJob:
        job = OptimizationJob(
            strategy_version_id=strategy_version_id,
            strategy_slug=strategy_slug,
            strategy_code_version=strategy_code_version,
            watchlist_id=watchlist_id,
            timeframe=timeframe,
            start_at=start_at,
            end_at=end_at,
            objective_metric=objective_metric,
            sort_direction=sort_direction,
            total_combinations=total_combinations,
            completed_combinations=0,
            started_at=None,
            completed_at=None,
            search_space_json=search_space_json,
            execution_assumptions_json=execution_assumptions_json,
            status=OptimizationJobStatus.PENDING,
            result_summary_json={},
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get_job(self, job_id: uuid.UUID) -> OptimizationJob | None:
        return self.session.get(OptimizationJob, job_id)

    def list_jobs(self, limit: int = 50) -> list[OptimizationJob]:
        stmt = select(OptimizationJob).order_by(OptimizationJob.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars())

    def set_status(
        self,
        job_id: uuid.UUID,
        *,
        status: OptimizationJobStatus,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        job = self.session.get(OptimizationJob, job_id)
        if job is None:
            raise KeyError("optimization job not found")
        job.status = status
        if started_at is not None:
            job.started_at = started_at
        if completed_at is not None:
            job.completed_at = completed_at
        self.session.commit()

    def set_progress(
        self,
        job_id: uuid.UUID,
        *,
        completed_combinations: int,
    ) -> None:
        job = self.session.get(OptimizationJob, job_id)
        if job is None:
            raise KeyError("optimization job not found")
        job.completed_combinations = int(completed_combinations)
        self.session.commit()

    def set_result_summary(self, job_id: uuid.UUID, *, result_summary_json: dict) -> None:
        job = self.session.get(OptimizationJob, job_id)
        if job is None:
            raise KeyError("optimization job not found")
        job.result_summary_json = result_summary_json
        self.session.commit()

    def add_candidate(
        self,
        *,
        optimization_job_id: uuid.UUID,
        backtest_run_id: uuid.UUID,
        rank: int,
        params_json: dict,
        objective_value: float,
        metrics_json: dict,
    ) -> OptimizationCandidateResult:
        row = OptimizationCandidateResult(
            optimization_job_id=optimization_job_id,
            backtest_run_id=backtest_run_id,
            rank=int(rank),
            params_json=params_json,
            objective_value=float(objective_value),
            metrics_json=metrics_json,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_candidates(self, job_id: uuid.UUID, limit: int = 5000) -> list[OptimizationCandidateResult]:
        stmt = (
            select(OptimizationCandidateResult)
            .where(OptimizationCandidateResult.optimization_job_id == job_id)
            .order_by(OptimizationCandidateResult.rank.asc(), OptimizationCandidateResult.created_at.asc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

