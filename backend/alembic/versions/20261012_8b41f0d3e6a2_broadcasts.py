"""broadcasts

Revision ID: 8b41f0d3e6a2
Revises: 5d2e8f4a1c07
Create Date: 2026-10-12 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8b41f0d3e6a2'
down_revision: Union[str, Sequence[str], None] = '5d2e8f4a1c07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('broadcasts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('audience', sa.String(length=16), nullable=False),
    sa.Column('status', sa.Enum('queued', 'sending', 'done', 'cancelled', name='broadcaststatus', native_enum=False, create_constraint=False, length=16), server_default='queued', nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('total', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('sent', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('failed', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('last_user_id', sa.BigInteger(), server_default=sa.text('0'), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['admin_users.id'], name=op.f('fk_broadcasts_created_by_admin_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_broadcasts'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('broadcasts')
