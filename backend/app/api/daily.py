"""Daily task and streak (TZ 8.5)."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.badges import award_badges, badges_out
from app.daily import (
    STREAK_BONUS_POINTS,
    complete_daily_task,
    current_streak,
    days_to_bonus,
    task_of_the_day,
)
from app.deps import CurrentUser, SessionDep
from app.models import User
from app.points import lock_user
from app.schemas import DailyDoneOut, DailyOut, DailyTaskOut, DoneIn
from app.timeutil import local_today

router = APIRouter(tags=["daily"])


async def daily_state(session: AsyncSession, user: User) -> DailyOut:
    today = local_today()
    task = await task_of_the_day(session, today)
    streak = current_streak(user, today)
    return DailyOut(
        task=DailyTaskOut(id=task.id, text=task.text, points=task.points) if task else None,
        done_today=user.last_task_date == today,
        streak_current=streak,
        streak_best=user.streak_best,
        days_to_bonus=days_to_bonus(streak),
        bonus_points=STREAK_BONUS_POINTS,
    )


@router.get("/daily")
async def daily(user: CurrentUser, session: SessionDep) -> DailyOut:
    return await daily_state(session, user)


@router.post("/daily/done")
async def daily_done(body: DoneIn, user: CurrentUser, session: SessionDep) -> DailyDoneOut:
    """20 points once per Tashkent day; keeps the streak and pays the 7-day bonus (QM-09, QM-10)."""
    today = local_today()
    task = await task_of_the_day(session, today)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no_task_today")

    await lock_user(session, user.id)
    await session.refresh(user)  # streak fields as of the lock, not as of the request start
    done, bonus = await complete_daily_task(session, user, task, today, body.client_event_id)
    new_badges = await award_badges(session, user.id) if done else []
    await session.commit()
    await session.refresh(user)
    return DailyDoneOut(
        awarded=done,
        points=task.points if done else 0,
        bonus_points=bonus,
        streak_current=current_streak(user, today),
        streak_best=user.streak_best,
        points_total=user.points_total,
        new_badges=badges_out(new_badges),
    )
