"""ph5 optimization jobs and candidates

Revision ID: 9f3a0f3b6a21
Revises: 8c8d0b2c6b1a
Create Date: 2026-03-16 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "9f3a0f3b6a21"
down_revision = "8c8d0b2c6b1a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("optimization_jobs", sa.Column("strategy_slug", sa.String(length=128), nullable=True))
    op.add_column("optimization_jobs", sa.Column("strategy_code_version", sa.String(length=32), nullable=True))
    op.add_column(
        "optimization_jobs",
        sa.Column("timeframe", sa.String(length=16), server_default=sa.text("'1D'"), nullable=False),
    )
    op.add_column("optimization_jobs", sa.Column("start_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("optimization_jobs", sa.Column("end_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "optimization_jobs",
        sa.Column(
            "objective_metric", sa.String(length=64), server_default=sa.text("'net_return_pct'"), nullable=False
        ),
    )
    op.add_column(
        "optimization_jobs",
        sa.Column("sort_direction", sa.String(length=8), server_default=sa.text("'desc'"), nullable=False),
    )
    op.add_column(
        "optimization_jobs",
        sa.Column("total_combinations", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "optimization_jobs",
        sa.Column("completed_combinations", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column("optimization_jobs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("optimization_jobs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "optimization_jobs",
        sa.Column(
            "execution_assumptions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.create_index("ix_optimization_jobs_strategy_slug", "optimization_jobs", ["strategy_slug"], unique=False)

    op.create_table(
        "optimization_candidate_results",
        sa.Column("optimization_job_id", sa.Uuid(), nullable=False),
        sa.Column("backtest_run_id", sa.Uuid(), nullable=False),
        sa.Column("rank", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "params_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "objective_value",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=False,
        ),
        sa.Column(
            "metrics_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["optimization_job_id"], ["optimization_jobs.id"]),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opt_candidates_job_rank", "optimization_candidate_results", ["optimization_job_id", "rank"], unique=False)
    op.create_index("ix_opt_candidates_job_id", "optimization_candidate_results", ["optimization_job_id"], unique=False)
    op.create_index("ix_opt_candidates_run_id", "optimization_candidate_results", ["backtest_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_opt_candidates_run_id", table_name="optimization_candidate_results")
    op.drop_index("ix_opt_candidates_job_id", table_name="optimization_candidate_results")
    op.drop_index("ix_opt_candidates_job_rank", table_name="optimization_candidate_results")
    op.drop_table("optimization_candidate_results")

    op.drop_index("ix_optimization_jobs_strategy_slug", table_name="optimization_jobs")
    op.drop_column("optimization_jobs", "execution_assumptions_json")
    op.drop_column("optimization_jobs", "completed_at")
    op.drop_column("optimization_jobs", "started_at")
    op.drop_column("optimization_jobs", "completed_combinations")
    op.drop_column("optimization_jobs", "total_combinations")
    op.drop_column("optimization_jobs", "sort_direction")
    op.drop_column("optimization_jobs", "objective_metric")
    op.drop_column("optimization_jobs", "end_at")
    op.drop_column("optimization_jobs", "start_at")
    op.drop_column("optimization_jobs", "timeframe")
    op.drop_column("optimization_jobs", "strategy_code_version")
    op.drop_column("optimization_jobs", "strategy_slug")

