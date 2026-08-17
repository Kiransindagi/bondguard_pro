"""init

Revision ID: 445188b3d94e
Revises: 
Create Date: 2026-07-06 19:40:24.242608

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '445188b3d94e'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'system_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_metadata_id'), 'system_metadata', ['id'], unique=False)
    op.create_index(op.f('ix_system_metadata_key'), 'system_metadata', ['key'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_system_metadata_key'), table_name='system_metadata')
    op.drop_index(op.f('ix_system_metadata_id'), table_name='system_metadata')
    op.drop_table('system_metadata')
