"""ph4 add trade holding period

Revision ID: 2a7e6dd0fce0
Revises: 8c8d0b2c6b1a
Create Date: 2026-03-15 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "2a7e6dd0fce0"
down_revision = "8c8d0b2c6b1a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("backtest_trades", sa.Column("holding_period_sec", sa.BigInteger(), nullable=True))
    op.add_column("backtest_trades", sa.Column("holding_period_bars", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("backtest_trades", "holding_period_bars")
    op.drop_column("backtest_trades", "holding_period_sec")

