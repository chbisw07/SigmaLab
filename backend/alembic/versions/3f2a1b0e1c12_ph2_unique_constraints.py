"""PH2 unique constraints for idempotent sync.

Revision ID: 3f2a1b0e1c12
Revises: 0dcc4345aa9f
Create Date: 2026-03-14
"""

from __future__ import annotations

from alembic import op

revision = "3f2a1b0e1c12"
down_revision = "0dcc4345aa9f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_instruments_broker_token_exchange",
        "instruments",
        ["broker_instrument_token", "exchange"],
    )
    op.create_unique_constraint(
        "uq_watchlist_items_watchlist_instrument",
        "watchlist_items",
        ["watchlist_id", "instrument_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_watchlist_items_watchlist_instrument", "watchlist_items", type_="unique")
    op.drop_constraint("uq_instruments_broker_token_exchange", "instruments", type_="unique")

