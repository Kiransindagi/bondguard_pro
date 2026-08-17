"""remove unsupported breach review state

Revision ID: d0a1b2c3d4e5
Revises: cf4dd306ac1a
Create Date: 2026-08-16
"""

from typing import Sequence

from alembic import op
from sqlalchemy import Column, DateTime, String

revision: str = "d0a1b2c3d4e5"
down_revision: str | Sequence[str] | None = "cf4dd306ac1a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Retain only OPEN, ACKNOWLEDGED, and RESOLVED breach workflow data."""
    op.drop_column("breaches", "under_review_at")
    op.drop_column("breaches", "review_notes")


def downgrade() -> None:
    """Restore the removed review metadata columns."""
    op.add_column("breaches", Column("review_notes", String(), nullable=True))
    op.add_column("breaches", Column("under_review_at", DateTime(timezone=True), nullable=True))
