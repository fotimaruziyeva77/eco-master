"""Daily task and streak (TZ 8.5)."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContentStatus, DailyTask, DailyTaskSchedule, Tip, TipSchedule, User
from app.points import award

STREAK_BONUS_EVERY = 7
STREAK_BONUS_POINTS = 50


async def pick_for_day[T: (DailyTask, Tip)](
    session: AsyncSession, model: type[T], schedule: type, column: str, day: date
) -> T | None:
    """The item scheduled for this date in the admin panel, otherwise the next one in rotation.

    Everyone gets the same item on the same day.
    """
    scheduled = await session.scalar(
        select(model)
        .join(schedule, getattr(schedule, column) == model.id)
        .where(schedule.day == day, model.status == ContentStatus.PUBLISHED)
    )
    if scheduled is not None:
        return scheduled
    items = (
        await session.scalars(
            select(model)
            .where(model.status == ContentStatus.PUBLISHED)
            .order_by(model.sort_order, model.id)
        )
    ).all()
    # After the last item the list starts again from the beginning (TZ 8.5).
    return items[day.toordinal() % len(items)] if items else None


async def task_of_the_day(session: AsyncSession, day: date) -> DailyTask | None:
    return await pick_for_day(session, DailyTask, DailyTaskSchedule, "task_id", day)


async def tip_of_the_day(session: AsyncSession, day: date) -> Tip | None:
    return await pick_for_day(session, Tip, TipSchedule, "tip_id", day)


def current_streak(user: User, today: date) -> int:
    """The stored streak is only alive if the task was done today or yesterday."""
    if user.last_task_date is not None and user.last_task_date >= today - timedelta(days=1):
        return user.streak_current
    return 0


def days_to_bonus(streak: int) -> int:
    return STREAK_BONUS_EVERY - streak % STREAK_BONUS_EVERY


async def complete_daily_task(
    session: AsyncSession, user: User, task: DailyTask, today: date, client_event_id
) -> tuple[bool, int]:
    """Record today's task. Returns (newly done, bonus points).

    A missed day resets the streak to 1; every 7th day in a row adds a 50-point bonus.
    """
    done = await award(
        session,
        user.id,
        "daily_task",
        task.points,
        object_id=str(task.id),
        client_event_id=client_event_id,
        day=today,
    )
    if not done:
        return False, 0

    streak = current_streak(user, today) + 1
    user.streak_current = streak
    user.streak_best = max(user.streak_best, streak)
    user.last_task_date = today

    bonus = 0
    if streak % STREAK_BONUS_EVERY == 0:
        await award(
            session, user.id, "streak_bonus", STREAK_BONUS_POINTS, object_id=str(streak), day=today
        )
        bonus = STREAK_BONUS_POINTS
    return True, bonus
