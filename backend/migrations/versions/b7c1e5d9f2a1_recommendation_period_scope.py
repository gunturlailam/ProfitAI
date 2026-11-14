"""recommendation period scope

Revision ID: b7c1e5d9f2a1
Revises: 15249a199165
Create Date: 2026-11-14 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c1e5d9f2a1"
down_revision: Union[str, Sequence[str], None] = "15249a199165"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recommendations", sa.Column("period_from", sa.Date(), nullable=True))
    op.add_column("recommendations", sa.Column("period_to", sa.Date(), nullable=True))
    op.create_index(
        "idx_recommendation_org_period",
        "recommendations",
        ["organization_id", "period_from", "period_to"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_recommendation_org_period", table_name="recommendations")
    op.drop_column("recommendations", "period_to")
    op.drop_column("recommendations", "period_from")
