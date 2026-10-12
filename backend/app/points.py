"""Awarding points. Only the server decides how many points an action is worth (TZ 11.1)."""

import uuid
from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import event_row
from app.leagues import join_week
from app.levels import level_for
from app.models import ActivityLog, User
from app.timeutil import local_today, week_start

# TZ 8.6 (proposed values, tuned during the closed test).
PROJECT_DONE_POINTS = 15
QUIZ_CORRECT_POINTS = 5
GAME_CORRECT_POINTS = 2
GAME_DAILY_CAP = 40


async def lock_user(session: AsyncSession, user_id: int) -> None:
    """Serialize one user's point-changing requests, so daily limits hold under parallel taps."""
    await session.execute(select(User.id).where(User.id == user_id).with_for_update())


async def points_today(session: AsyncSession, user_id: int, action: str, day: date) -> int:
    return await session.scalar(
        select(func.coalesce(func.sum(ActivityLog.points), 0)).where(
            ActivityLog.user_id == user_id,
            ActivityLog.action == action,
            ActivityLog.local_date == day,
        )
    )


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
        row = (
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(points_total=User.points_total + points)
                .returning(User.points_total, User.language, User.path)
            )
        ).one()
        level = level_for(row.points_total)
        if level.code != level_for(row.points_total - points).code:
            props = {"level": level.code}
            session.add(event_row(user_id, row.language, row.path, "level_up", props))
    if points > 0:
        # The first points of a week put the user into this week's league group.
        await join_week(session, user_id, week_start(day or local_today()))
    return True
