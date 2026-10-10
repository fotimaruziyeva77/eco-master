"""Awarding points. Only the server decides how many points an action is worth (TZ 11.1)."""

import uuid
from datetime import date

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog, User
from app.timeutil import local_today

PROJECT_DONE_POINTS = 15


async def award(
    session: AsyncSession,
    user_id: int,
    action: str,
    points: int,
    *,
    object_id: str | None = None,
    client_event_id: uuid.UUID | None = None,
    day: date | None = None,
) -> bool:
    """Record an action and add its points. Returns False if it was already recorded.

    Duplicates are rejected by the database itself: a repeated client_event_id, a second
    'project_done'/'quiz_correct' for the same object, or a second daily task on one day.
    """
    stmt = (
        insert(ActivityLog)
        .values(
            user_id=user_id,
            action=action,
            object_id=object_id,
            points=points,
            local_date=day or local_today(),
            client_event_id=client_event_id,
        )
        .on_conflict_do_nothing()
        .returning(ActivityLog.id)
    )
    if (await session.execute(stmt)).scalar_one_or_none() is None:
        return False
    if points:
        await session.execute(
            update(User).where(User.id == user_id).values(points_total=User.points_total + points)
        )
    return True
