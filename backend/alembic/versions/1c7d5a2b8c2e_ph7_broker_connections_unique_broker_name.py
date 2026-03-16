"""ph7 broker connections unique broker name

Revision ID: 1c7d5a2b8c2e
Revises: f2f1b4e0d7ad
Create Date: 2026-03-16 00:00:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "1c7d5a2b8c2e"
down_revision = "f2f1b4e0d7ad"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_broker_connections_broker_name",
        "broker_connections",
        ["broker_name"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_broker_connections_broker_name",
        "broker_connections",
        type_="unique",
    )

