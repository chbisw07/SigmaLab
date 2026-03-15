"""ph4 backtest metrics and run fields

Revision ID: 8c8d0b2c6b1a
Revises: 6b2d5f8b1c9a
Create Date: 2026-03-15 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "8c8d0b2c6b1a"
down_revision = "6b2d5f8b1c9a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("backtest_runs", sa.Column("strategy_slug", sa.String(length=128), nullable=True))
    op.add_column("backtest_runs", sa.Column("strategy_code_version", sa.String(length=32), nullable=True))
    op.add_column(
        "backtest_runs",
        sa.Column(
            "watchlist_snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column("backtest_runs", sa.Column("start_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("backtest_runs", sa.Column("end_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "backtest_runs",
        sa.Column(
            "execution_assumptions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column("backtest_runs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_backtest_runs_strategy_slug", "backtest_runs", ["strategy_slug"], unique=False)

    op.add_column("backtest_trades", sa.Column("instrument_id", sa.Uuid(), nullable=True))
    op.add_column(
        "backtest_trades", sa.Column("side", sa.String(length=8), server_default=sa.text("'long'"), nullable=False)
    )
    op.add_column(
        "backtest_trades", sa.Column("quantity", sa.Float(), server_default=sa.text("1.0"), nullable=False)
    )
    op.add_column("backtest_trades", sa.Column("close_reason", sa.String(length=32), nullable=True))
    op.create_index("ix_backtest_trades_instrument_id", "backtest_trades", ["instrument_id"], unique=False)
    op.create_index("ix_backtest_trades_close_reason", "backtest_trades", ["close_reason"], unique=False)
    op.create_index(
        "ix_backtest_trades_run_symbol_entry_ts",
        "backtest_trades",
        ["run_id", "symbol", "entry_ts"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_backtest_trades_instrument_id_instruments",
        "backtest_trades",
        "instruments",
        ["instrument_id"],
        ["id"],
    )

    op.create_table(
        "backtest_metrics",
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=True),
        sa.Column(
            "metrics_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "equity_curve_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "drawdown_curve_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["backtest_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_backtest_metrics_run_id", "backtest_metrics", ["run_id"], unique=False)
    op.create_index("ix_backtest_metrics_run_symbol", "backtest_metrics", ["run_id", "symbol"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_backtest_metrics_run_symbol", table_name="backtest_metrics")
    op.drop_index("ix_backtest_metrics_run_id", table_name="backtest_metrics")
    op.drop_table("backtest_metrics")

    op.drop_constraint("fk_backtest_trades_instrument_id_instruments", "backtest_trades", type_="foreignkey")
    op.drop_index("ix_backtest_trades_run_symbol_entry_ts", table_name="backtest_trades")
    op.drop_index("ix_backtest_trades_close_reason", table_name="backtest_trades")
    op.drop_index("ix_backtest_trades_instrument_id", table_name="backtest_trades")
    op.drop_column("backtest_trades", "close_reason")
    op.drop_column("backtest_trades", "quantity")
    op.drop_column("backtest_trades", "side")
    op.drop_column("backtest_trades", "instrument_id")

    op.drop_index("ix_backtest_runs_strategy_slug", table_name="backtest_runs")
    op.drop_column("backtest_runs", "started_at")
    op.drop_column("backtest_runs", "execution_assumptions_json")
    op.drop_column("backtest_runs", "end_at")
    op.drop_column("backtest_runs", "start_at")
    op.drop_column("backtest_runs", "watchlist_snapshot_json")
    op.drop_column("backtest_runs", "strategy_code_version")
    op.drop_column("backtest_runs", "strategy_slug")

