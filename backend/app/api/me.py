from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError

from app.api.rating import user_rank
from app.badges import badge_progress
from app.daily import current_streak
from app.deps import CurrentUser, SessionDep
from app.models import (
    ActivityLog,
    AnalyticsEvent,
    Badge,
    ContentStatus,
    Project,
    UserBadge,
)
from app.nickname import NicknameError, validate_nickname
from app.schemas import (
    NICKNAME_CHANGE_INTERVAL,
    BadgeOut,
    MeUpdate,
    NicknameIn,
    StatsOut,
    UserOut,
    WriteAccessIn,
)
from app.timeutil import local_today

router = APIRouter(tags=["me"])


@router.get("/me")
async def get_me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me")
async def update_me(body: MeUpdate, user: CurrentUser, session: SessionDep) -> UserOut:
    """Settings (TZ 8.8): language, user path, reminders."""
    for field in ("language", "path", "reminders_enabled", "reminder_time"):
        value = getattr(body, field)
        if value is not None:
            setattr(user, field, value)
    await session.commit()
    return UserOut.model_validate(user)


@router.post("/me/write-access")
async def set_write_access(body: WriteAccessIn, user: CurrentUser, session: SessionDep) -> UserOut:
    """Result of Telegram's requestWriteAccess: whether the bot may send reminders (TZ 8.1)."""
    if body.granted and not user.write_access:
        user.write_access = True
        await session.commit()
    return UserOut.model_validate(user)


@router.post("/me/nickname")
async def change_nickname(body: NicknameIn, user: CurrentUser, session: SessionDep) -> UserOut:
    """Nickname change from settings: same rules as onboarding, at most once in 30 days."""
    now = datetime.now(UTC)
    if user.nickname_changed_at and now < user.nickname_changed_at + NICKNAME_CHANGE_INTERVAL:
        raise HTTPException(status.HTTP_409_CONFLICT, "nickname_change_too_soon")
    try:
        nickname = await validate_nickname(session, body.nickname, exclude_user_id=user.id)
    except NicknameError as exc:
        code = status.HTTP_409_CONFLICT if exc.code == "nickname_taken" else 422
        raise HTTPException(code, exc.code) from exc
    if nickname == user.nickname:
        return UserOut.model_validate(user)

    user.nickname = nickname
    user.nickname_changed_at = now
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "nickname_taken") from exc
    return UserOut.model_validate(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(user: CurrentUser, session: SessionDep) -> Response:
    """Delete the account (TZ 8.8, QM-17).

    The profile, nickname and badges are removed; the activity log stays for statistics
    with the user id cleared (foreign keys use ON DELETE SET NULL / CASCADE).
    """
    await session.delete(user)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/badges")
async def my_badges(user: CurrentUser, session: SessionDep) -> list[BadgeOut]:
    """All badges; earned ones carry earned_at, the rest show how close the user is."""
    progress = await badge_progress(session, user)
    rows = await session.execute(
        select(Badge, UserBadge.earned_at)
        .outerjoin(UserBadge, and_(UserBadge.badge_id == Badge.id, UserBadge.user_id == user.id))
        .order_by(Badge.sort_order)
    )
    result = []
    for badge, earned_at in rows.all():
        current, target = progress.get(badge.code, (None, None))
        result.append(
            BadgeOut(
                code=badge.code,
                name=badge.name,
                description=badge.description,
                icon=badge.icon,
                earned_at=earned_at,
                progress_current=current,
                progress_target=target,
            )
        )
    return result


@router.get("/me/stats")
async def my_stats(user: CurrentUser, session: SessionDep) -> StatsOut:
    """Profile numbers (TZ 8.8)."""
    actions = dict(
        (
            await session.execute(
                select(ActivityLog.action, func.count())
                .where(ActivityLog.user_id == user.id)
                .group_by(ActivityLog.action)
            )
        ).all()
    )
    answers = dict(
        (
            await session.execute(
                select(AnalyticsEvent.name, func.count())
                .where(
                    AnalyticsEvent.user_id == user.id,
                    AnalyticsEvent.name.in_(("quiz_answer", "game_answer")),
                )
                .group_by(AnalyticsEvent.name)
            )
        ).all()
    )
    projects_total = await session.scalar(
        select(func.count()).select_from(Project).where(Project.status == ContentStatus.PUBLISHED)
    )
    badges_total = await session.scalar(select(func.count()).select_from(Badge))
    badges_earned = await session.scalar(
        select(func.count()).select_from(UserBadge).where(UserBadge.user_id == user.id)
    )
    return StatsOut(
        streak_current=current_streak(user, local_today()),
        streak_best=user.streak_best,
        tasks_done=actions.get("daily_task", 0),
        projects_done=actions.get("project_done", 0),
        projects_total=projects_total,
        quiz_correct=actions.get("quiz_correct", 0),
        quiz_answered=answers.get("quiz_answer", 0),
        sorted_correct=actions.get("game_correct", 0),
        sorted_total=answers.get("game_answer", 0),
        badges_earned=badges_earned,
        badges_total=badges_total,
        rank_all=await user_rank(session, user.id, "all"),
    )
