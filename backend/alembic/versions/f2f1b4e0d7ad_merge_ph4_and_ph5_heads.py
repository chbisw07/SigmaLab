"""merge ph4 and ph5 heads

Revision ID: f2f1b4e0d7ad
Revises: 2a7e6dd0fce0, 9f3a0f3b6a21
Create Date: 2026-03-16 00:00:00.000000
"""

from __future__ import annotations


revision = "f2f1b4e0d7ad"
down_revision = ("2a7e6dd0fce0", "9f3a0f3b6a21")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge revision: no-op. Both parent revisions must be applied.
    pass


def downgrade() -> None:
    # Merge revision: no-op.
    pass

