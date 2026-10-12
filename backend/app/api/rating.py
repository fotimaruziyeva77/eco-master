"""Leaderboard and nickname complaints (TZ 8.7)."""

from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import CurrentUser, SessionDep
from app.levels import level_for
from app.models import ActivityLog, OnboardingStep, Report, ReportStatus, User
from app.schemas import LeaderboardEntryOut, LeaderboardOut, ReportIn
from app.timeutil import local_today, week_start

router = APIRouter(tags=["rating"])

TOP_SIZE = 100
Period = Literal["week", "all"]


def ranked_query(period: Period, today: date):
    """All visible users with points, ranked; equal points go to whoever reached them first."""
    visible = and_(
        User.is_blocked.is_(False),
        User.nickname_hidden.is_(False),
        User.nickname.is_not(None),
        User.onboarding_step == OnboardingStep.DONE,
    )
    if period == "all":
        gains = (
            select(ActivityLog.user_id, func.max(ActivityLog.created_at).label("last_gain"))
            .where(ActivityLog.points > 0)
            .group_by(ActivityLog.user_id)
            .subquery()
        )
        points = User.points_total
        last_gain = gains.c.last_gain
        base = (
            select(User.id, User.nickname, User.avatar, User.points_total)
            .outerjoin(gains, gains.c.user_id == User.id)
            .where(visible, User.points_total > 0)
        )
    else:
        monday = week_start(today)
        week = (
            select(
                ActivityLog.user_id,
                func.sum(ActivityLog.points).label("points"),
                func.max(ActivityLog.created_at).filter(ActivityLog.points > 0).label("last_gain"),
            )
            .where(ActivityLog.local_date.between(monday, monday + timedelta(days=6)))
            .group_by(ActivityLog.user_id)
            .subquery()
        )
        points = week.c.points
        last_gain = week.c.last_gain
        base = (
            select(User.id, User.nickname, User.avatar, User.points_total)
            .join(week, week.c.user_id == User.id)
            .where(visible, week.c.points > 0)
        )
    rank = func.row_number().over(
        order_by=[points.desc(), last_gain.asc().nulls_last(), User.id.asc()]
    )
    return base.add_columns(points.label("points"), rank.label("rank")).subquery()


def entry(row, me_id: int) -> LeaderboardEntryOut:
    return LeaderboardEntryOut(
        rank=row.rank,
        user_id=row.id,
        nickname=row.nickname,
        avatar=row.avatar,
        level_code=level_for(row.points_total).code,
        points=row.points,
        is_me=row.id == me_id,
    )


async def user_rank(session: AsyncSession, user_id: int, period: Period) -> int | None:
    ranked = ranked_query(period, local_today())
    return await session.scalar(select(ranked.c.rank).where(ranked.c.id == user_id))


@router.get("/leaderboard")
async def leaderboard(
    user: CurrentUser, session: SessionDep, period: Annotated[Period, Query()] = "week"
) -> LeaderboardOut:
    today = local_today()
    ranked = ranked_query(period, today)
    top = await session.execute(
        select(ranked).where(ranked.c.rank <= TOP_SIZE).order_by(ranked.c.rank)
    )
    mine = (await session.execute(select(ranked).where(ranked.c.id == user.id))).first()
    return LeaderboardOut(
        period=period,
        week_start=week_start(today) if period == "week" else None,
        entries=[entry(row, user.id) for row in top.all()],
        # Shown under the list even when outside the top 100 (QM-12).
        me=entry(mine, user.id) if mine else None,
    )


@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def report_nickname(body: ReportIn, user: CurrentUser, session: SessionDep) -> dict:
    """Complaint about an inappropriate nickname; it goes to the admin queue."""
    if body.target_user_id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot_report_self")
    if await session.get(User, body.target_user_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user_not_found")
    already = await session.scalar(
        select(Report.id).where(
            Report.reporter_id == user.id,
            Report.target_user_id == body.target_user_id,
            Report.status == ReportStatus.OPEN,
        )
    )
    if already is None:
        session.add(
            Report(reporter_id=user.id, target_user_id=body.target_user_id, reason=body.reason)
        )
        await session.commit()
    return {"ok": True}
