"""league members by user: the last week a user played

Revision ID: c4a9e2b7f013
Revises: 8b41f0d3e6a2
Create Date: 2026-10-12 23:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c4a9e2b7f013'
down_revision: Union[str, Sequence[str], None] = '8b41f0d3e6a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('ix_league_members_user_week', 'league_members', ['user_id', 'week_start'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_league_members_user_week', table_name='league_members')
