"""merge_heads

Revision ID: c78e9882ee33
Revises: 1485070afc6b, b7c1e5d9f2a1
Create Date: 2026-11-15 01:42:03.887489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c78e9882ee33'
down_revision: Union[str, Sequence[str], None] = ('1485070afc6b', 'b7c1e5d9f2a1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
