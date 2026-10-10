"""Users and moderation (TZ 8.12): search, activity, nicknames, blocking, fake points."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit import audit
from app.admin.deps import AdminOnly
from app.admin.moderation import fast_flags, points_flags, reset_nickname, void_entries
from app.admin.schemas import (
    ActivityRowOut,
    AdminUserDetailOut,
    AdminUserRowOut,
    BadgeRefOut,
    BlockIn,
    NicknameActionIn,
    ReportOut,
    UserFlagOut,
    VoidIn,
)
from app.deps import SessionDep
from app.models import (
    ActivityLog,
    AdminUser,
    Badge,
    OnboardingStep,
    Report,
    ReportStatus,
    User,
    UserBadge,
)
from app.timeutil import local_today

router = APIRouter(prefix="/users", tags=["admin-users"])

FLAG_DAYS = 14
Filter = Literal["all", "blocked", "hidden", "reported", "flagged"]


def open_reports_count():
    return (
        select(func.count())
        .where(Report.target_user_id == User.id, Report.status == ReportStatus.OPEN)
        .correlate(User)
        .scalar_subquery()
    )


def row_out(user: User, open_reports: int) -> AdminUserRowOut:
    return AdminUserRowOut(
        id=user.id,
        nickname=user.nickname,
        language=user.language,
        path=user.path.value if user.path else None,
        source=user.source,
        points_total=user.points_total,
        streak_current=user.streak_current,
        onboarding_done=user.onboarding_step == OnboardingStep.DONE,
        is_blocked=user.is_blocked,
        nickname_hidden=user.nickname_hidden,
        open_reports=open_reports,
        created_at=user.created_at,
        last_active_at=user.last_active_at,
    )


async def flagged_user_ids(session: AsyncSession) -> set[int]:
    since = local_today() - timedelta(days=FLAG_DAYS)
    ids = {row[0] for row in await points_flags(session, since)}
    ids |= {
        row[0] for row in await fast_flags(session, datetime.now(UTC) - timedelta(days=FLAG_DAYS))
    }
    return ids


@router.get("")
async def search_users(
    admin: AdminOnly,
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=64)] = None,
    filter: Annotated[Filter, Query()] = "all",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AdminUserRowOut]:
    """By nickname, internal id or Telegram id (TZ 8.12)."""
    reports = open_reports_count()
    query = select(User, reports.label("reports")).order_by(User.last_active_at.desc())
    term = (q or "").strip().lstrip("@#")
    if term.isdigit() and len(term) <= 18:  # ids fit in BIGINT
        query = query.where(or_(User.id == int(term), User.telegram_id == int(term)))
    elif term:
        query = query.where(User.nickname.ilike(f"%{term}%"))
    if filter == "blocked":
        query = query.where(User.is_blocked.is_(True))
    elif filter == "hidden":
        query = query.where(User.nickname_hidden.is_(True))
    elif filter == "reported":
        query = query.where(reports > 0)
    elif filter == "flagged":
        query = query.where(User.id.in_(await flagged_user_ids(session) or {-1}))
    rows = await session.execute(query.limit(limit))
    return [row_out(user, count) for user, count in rows.all()]


async def get_user(session: AsyncSession, user_id: int) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user_not_found")
    return user


async def reports_out(session: AsyncSession, query) -> list[ReportOut]:
    rows = await session.execute(
        query.add_columns(User.nickname, AdminUser.name)
        .join(User, User.id == Report.target_user_id)
        .outerjoin(AdminUser, AdminUser.id == Report.resolved_by)
        .order_by(Report.created_at.desc())
    )
    return [
        ReportOut(
            id=r.id,
            reporter_id=r.reporter_id,
            target_user_id=r.target_user_id,
            target_nickname=nickname,
            reason=r.reason,
            status=r.status,
            resolution=r.resolution,
            created_at=r.created_at,
            resolved_at=r.resolved_at,
            resolved_by=admin_name,
        )
        for r, nickname, admin_name in rows.all()
    ]


async def user_detail(session: AsyncSession, user: User) -> AdminUserDetailOut:
    await session.refresh(user)
    counts = dict(
        (
            await session.execute(
                select(ActivityLog.action, func.count())
                .where(ActivityLog.user_id == user.id)
                .group_by(ActivityLog.action)
            )
        ).all()
    )
    badges = (
        await session.scalars(
            select(Badge)
            .join(UserBadge, UserBadge.badge_id == Badge.id)
            .where(UserBadge.user_id == user.id)
            .order_by(Badge.sort_order)
        )
    ).all()
    activity = (
        await session.scalars(
            select(ActivityLog)
            .where(ActivityLog.user_id == user.id)
            .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
            .limit(300)
        )
    ).all()
    since = local_today() - timedelta(days=30)
    flags = [
        UserFlagOut(kind="points", message=f"Bir kunda {points} ball", day=day)
        for _, _, day, points in await points_flags(session, since, user.id)
    ] + [
        UserFlagOut(
            kind="fast",
            message=f"{'Viktorina' if name == 'quiz_answer' else 'Saralash'}: {answers} ta javob, "
            f"o'rtacha {avg:.1f} s",
            day=day,
        )
        for _, _, name, day, answers, avg in await fast_flags(
            session, datetime.now(UTC) - timedelta(days=30), user.id
        )
    ]
    open_reports = sum(
        1
        for r in await session.scalars(
            select(Report.id).where(
                Report.target_user_id == user.id, Report.status == ReportStatus.OPEN
            )
        )
    )
    row = row_out(user, open_reports)
    return AdminUserDetailOut(
        **row.model_dump(),
        telegram_id=user.telegram_id,
        streak_best=user.streak_best,
        last_task_date=user.last_task_date,
        reminders_enabled=user.reminders_enabled,
        write_access=user.write_access,
        badges=[
            BadgeRefOut(code=b.code, name=b.name.get("uz", b.code), icon=b.icon) for b in badges
        ],
        counts=counts,
        flags=flags,
        reports=await reports_out(session, select(Report).where(Report.target_user_id == user.id)),
        activity=[ActivityRowOut.model_validate(a) for a in activity],
    )


@router.get("/{user_id}")
async def user_card(user_id: int, admin: AdminOnly, session: SessionDep) -> AdminUserDetailOut:
    return await user_detail(session, await get_user(session, user_id))


async def apply_block(session: AsyncSession, admin: AdminUser, user: User, blocked: bool, reason):
    """A blocked user can not open the app and leaves the leaderboard at once (QM-13)."""
    user.is_blocked = blocked
    audit(
        session, admin, "user.block" if blocked else "user.unblock", "user", user.id, reason=reason
    )


async def apply_nickname(session: AsyncSession, admin: AdminUser, user: User, action: str, reason):
    old = user.nickname
    if action == "hide":
        user.nickname_hidden = True
    elif action == "show":
        user.nickname_hidden = False
    else:
        reset_nickname(user)
    audit(session, admin, f"user.nickname_{action}", "user", user.id, nickname=old, reason=reason)


@router.post("/{user_id}/block")
async def block_user(
    user_id: int, body: BlockIn, admin: AdminOnly, session: SessionDep
) -> AdminUserDetailOut:
    user = await get_user(session, user_id)
    await apply_block(session, admin, user, body.blocked, body.reason)
    await session.commit()
    return await user_detail(session, user)


@router.post("/{user_id}/nickname")
async def nickname_action(
    user_id: int, body: NicknameActionIn, admin: AdminOnly, session: SessionDep
) -> AdminUserDetailOut:
    user = await get_user(session, user_id)
    await apply_nickname(session, admin, user, body.action, body.reason)
    await session.commit()
    return await user_detail(session, user)


@router.post("/{user_id}/void")
async def void_points(
    user_id: int, body: VoidIn, admin: AdminOnly, session: SessionDep
) -> AdminUserDetailOut:
    """Cancel fake points (TZ 8.12): totals, streak and dependent badges are recalculated."""
    user = await get_user(session, user_id)
    await session.execute(select(User.id).where(User.id == user.id).with_for_update())
    voided, revoked = await void_entries(session, admin, user, body.entry_ids, body.reason)
    if not voided:
        raise HTTPException(status.HTTP_409_CONFLICT, "nothing_to_void")
    audit(
        session,
        admin,
        "user.void_points",
        "user",
        user.id,
        entries=voided,
        badges_revoked=revoked,
        reason=body.reason,
    )
    await session.commit()
    return await user_detail(session, user)
