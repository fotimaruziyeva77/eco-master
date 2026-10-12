"""avatars and the weekly summary

Revision ID: 5d2e8f4a1c07
Revises: a11903356562
Create Date: 2026-10-12 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d2e8f4a1c07'
down_revision: Union[str, Sequence[str], None] = 'a11903356562'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('avatar', sa.String(length=16), nullable=True))
    op.add_column('users', sa.Column('last_weekly_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'last_weekly_date')
    op.drop_column('users', 'avatar')
