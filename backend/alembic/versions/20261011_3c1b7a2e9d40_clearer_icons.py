"""clearer icons: no champagne bottle for glass, badges unlike the waste types

Revision ID: 3c1b7a2e9d40
Revises: 9ffb28cfa8b7
Create Date: 2026-10-11 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c1b7a2e9d40'
down_revision: Union[str, Sequence[str], None] = '9ffb28cfa8b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CUP, LOTION = "🥤", "🧴"
JAR, CHAMPAGNE = "🫙", "🍾"
RECYCLE, WASTEBASKET = "♻️", "🗑️"

# (table, code, old icon, new icon). Only rows that still show the old picture change: an icon
# chosen in the admin panel stays.
CHANGES = [
    ("categories", "plastic", LOTION, CUP),
    ("categories", "glass", CHAMPAGNE, JAR),
    ("badges", "master_plastic", LOTION, CUP),
    ("badges", "master_glass", CHAMPAGNE, JAR),
    ("badges", "sorting_master", WASTEBASKET, RECYCLE),
]


def _set(table: str, code: str, old: str, new: str) -> None:
    op.execute(
        sa.text(f"UPDATE {table} SET icon = :new WHERE code = :code AND icon = :old").bindparams(
            new=new, code=code, old=old
        )
    )


def upgrade() -> None:
    """Upgrade schema."""
    for table, code, old, new in CHANGES:
        _set(table, code, old, new)
    # A champagne bottle is no picture for a children's app: glass bottles get a jar.
    op.execute(
        sa.text("UPDATE game_items SET icon = :new WHERE icon = :old").bindparams(
            new=JAR, old=CHAMPAGNE
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    for table, code, old, new in CHANGES:
        _set(table, code, new, old)
    # Game items are left as they are: the jar was already used for jars.
