"""add_ratio_alerts_table_for_history_tracking

Revision ID: e18fe48fc14f
Revises: c78e9882ee33
Create Date: 2026-11-15 02:22:57.878139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e18fe48fc14f'
down_revision: Union[str, Sequence[str], None] = 'c78e9882ee33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ratio_alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('alert_code', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('category_label', sa.Text(), nullable=False),
        sa.Column('level', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('ratio_codes', sa.JSON(), nullable=False),
        sa.Column('direction', sa.Text(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('period_from', sa.Date(), nullable=False),
        sa.Column('period_to', sa.Date(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='active'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ratio_alert_org_period', 'ratio_alerts', ['organization_id', 'period_from', 'period_to'])
    op.create_index('idx_ratio_alert_org_status', 'ratio_alerts', ['organization_id', 'status', 'level'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_ratio_alert_org_status', table_name='ratio_alerts')
    op.drop_index('idx_ratio_alert_org_period', table_name='ratio_alerts')
    op.drop_table('ratio_alerts')
