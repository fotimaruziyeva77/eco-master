"""Moderation (TZ 8.12): fake points, nicknames, suspicious activity (TZ 11.1)."""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import String, cast, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.badges import CATEGORY_MASTERS, earned_badge_codes
from app.models import (
    ActivityLog,
    AdminUser,
    AnalyticsEvent,
    Badge,
    Category,
    OnboardingStep,
    Project,
    User,
    UserBadge,
)
from app.timeutil import TASHKENT

# TZ 11.1: "more than 300 points a day or unnaturally fast answers" goes to the admin.
SUSPICIOUS_DAILY_POINTS = 300
FAST_AVG_SECONDS = 1.0
FAST_MIN_ANSWERS = 5

# Badges whose rule counts one kind of activity: voiding that activity re-checks them.
BADGE_ACTIONS = {
    "streak_7": "daily_task",
    "quiz_champion": "quiz_correct",
    "sorting_master": "game_correct",
}


async def recompute_user(session: AsyncSession, user: User) -> None:
    """Rebuild cached points and streaks from the activity log, the source of truth (TZ 10)."""
    user.points_total = await session.scalar(
        select(func.coalesce(func.sum(ActivityLog.points), 0)).where(ActivityLog.user_id == user.id)
    )
    days = sorted(
        (
            await session.scalars(
                select(ActivityLog.local_date).where(
                    ActivityLog.user_id == user.id, ActivityLog.action == "daily_task"
                )
            )
        ).all()
    )
    best = run = 0
    previous: date | None = None
    for day in days:
        run = run + 1 if previous is not None and day == previous + timedelta(days=1) else 1
        best = max(best, run)
        previous = day
    user.streak_best = best
    user.streak_current = run
    user.last_task_date = previous


async def void_entries(
    session: AsyncSession, admin: AdminUser, user: User, entry_ids: list[int], reason: str
) -> tuple[int, list[str]]:
    """Cancel points of the given log rows. Returns (rows voided, badges taken away).

    The rows stay for the record; their action becomes "voided" and points 0, so every
    total, limit and leaderboard leaves them out from now on.
    """
    rows = (
        await session.scalars(
            select(ActivityLog)
            .where(
                ActivityLog.user_id == user.id,
                ActivityLog.id.in_(entry_ids),
                ActivityLog.action != "voided",
            )
            .with_for_update()
        )
    ).all()
    if not rows:
        return 0, []
    now = datetime.now(UTC).isoformat()
    actions = {row.action for row in rows}
    projects = [row.object_id for row in rows if row.action == "project_done"]
    for row in rows:
        row.voided = {
            "action": row.action,
            "points": row.points,
            "at": now,
            "admin_id": admin.id,
            "reason": reason,
        }
        row.action = "voided"
        row.points = 0
    await session.flush()
    await recompute_user(session, user)
    await session.flush()
    return len(rows), await _revoke_badges(session, user, actions, projects)


async def _revoke_badges(
    session: AsyncSession, user: User, actions: set[str], project_ids: list[str | None]
) -> list[str]:
    """Take back badges that relied on the voided rows and are no longer earned.

    Other badges stay, even if a rule would now fail for an unrelated reason (for example
    new projects added to a waste type later).
    """
    affected = {code for code, action in BADGE_ACTIONS.items() if action in actions}
    if user.points_total <= 0:
        affected.add("first_step")
    if project_ids:
        codes = (
            await session.scalars(
                select(Category.code)
                .join(Project, Project.category_id == Category.id)
                .where(cast(Project.id, String).in_([p for p in project_ids if p]))
            )
        ).all()
        affected |= {badge for badge, category in CATEGORY_MASTERS.items() if category in codes}
    revoke = affected - await earned_badge_codes(session, user)
    if not revoke:
        return []
    await session.execute(
        delete(UserBadge).where(
            UserBadge.user_id == user.id,
            UserBadge.badge_id.in_(select(Badge.id).where(Badge.code.in_(revoke))),
        )
    )
    return sorted(revoke)


def reset_nickname(user: User) -> None:
    """The user must pick a new nickname at the next launch (TZ 8.12 "forced change")."""
    user.nickname = None
    user.nickname_hidden = False
    user.onboarding_step = OnboardingStep.NICKNAME


# ------------------------------------------------------------ suspicious activity


async def points_flags(session: AsyncSession, since: date, user_id: int | None = None):
    """(user id, nickname, day, points) for days above the suspicious total."""
    query = (
        select(
            ActivityLog.user_id,
            User.nickname,
            ActivityLog.local_date,
            func.sum(ActivityLog.points).label("points"),
        )
        .join(User, User.id == ActivityLog.user_id)
        .where(ActivityLog.local_date >= since)
        .group_by(ActivityLog.user_id, User.nickname, ActivityLog.local_date)
        .having(func.sum(ActivityLog.points) > SUSPICIOUS_DAILY_POINTS)
        .order_by(ActivityLog.local_date.desc(), func.sum(ActivityLog.points).desc())
    )
    if user_id is not None:
        query = query.where(ActivityLog.user_id == user_id)
    return (await session.execute(query)).all()


async def fast_flags(session: AsyncSession, since: datetime, user_id: int | None = None):
    """Rounds answered faster than a person can read: (user id, nickname, event, day,
    answers, average seconds per answer)."""
    round_id = AnalyticsEvent.props["round"].astext
    seconds = func.extract(
        "epoch", func.max(AnalyticsEvent.created_at) - func.min(AnalyticsEvent.created_at)
    ) / (func.count() - 1)
    query = (
        select(
            AnalyticsEvent.user_id,
            User.nickname,
            AnalyticsEvent.name,
            func.min(AnalyticsEvent.created_at).label("started"),
            func.count().label("answers"),
            seconds.label("avg_seconds"),
        )
        .join(User, User.id == AnalyticsEvent.user_id)
        .where(
            AnalyticsEvent.name.in_(("quiz_answer", "game_answer")),
            AnalyticsEvent.created_at >= since,
        )
        .group_by(AnalyticsEvent.user_id, User.nickname, AnalyticsEvent.name, round_id)
        .having(func.count() >= FAST_MIN_ANSWERS, seconds < FAST_AVG_SECONDS)
        .order_by(func.min(AnalyticsEvent.created_at).desc())
    )
    if user_id is not None:
        query = query.where(AnalyticsEvent.user_id == user_id)
    return [
        (
            r.user_id,
            r.nickname,
            r.name,
            r.started.astimezone(TASHKENT).date(),
            r.answers,
            float(r.avg_seconds),
        )
        for r in (await session.execute(query)).all()
    ]
