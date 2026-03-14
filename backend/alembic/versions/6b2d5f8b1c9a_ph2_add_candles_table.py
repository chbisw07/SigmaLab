"""ph2 add candles table

Revision ID: 6b2d5f8b1c9a
Revises: 3f2a1b0e1c12
Create Date: 2026-03-15 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "6b2d5f8b1c9a"
down_revision = "3f2a1b0e1c12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candles",
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("base_interval", sa.String(length=16), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("instrument_id", "base_interval", "ts"),
    )
    op.create_index(
        "ix_candles_instrument_ts",
        "candles",
        ["instrument_id", "ts"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_candles_instrument_ts", table_name="candles")
    op.drop_table("candles")

