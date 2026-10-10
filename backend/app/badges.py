"""Badge conditions (TZ 8.6). Badge names and icons live in the badges table (see seed_data)."""

from sqlalchemy import String, cast, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import track
from app.models import ActivityLog, Badge, Category, ContentStatus, Project, User, UserBadge
from app.schemas import BadgeOut

QUIZ_CHAMPION_ANSWERS = 50
SORTING_MASTER_SORTS = 100
STREAK_BADGE_DAYS = 7

# Badge code -> waste type whose projects must all be done.
CATEGORY_MASTERS = {
    "master_plastic": "plastic",
    "master_glass": "glass",
    "master_paper": "paper",
    "master_textile": "textile",
    "master_organic": "organic",
}


async def _count(session: AsyncSession, user_id: int, action: str) -> int:
    return await session.scalar(
        select(func.count())
        .select_from(ActivityLog)
        .where(ActivityLog.user_id == user_id, ActivityLog.action == action)
    )


async def category_progress(session: AsyncSession, user_id: int) -> dict[str, tuple[int, int]]:
    """Per waste type: (projects done by the user, published projects)."""
    done = (
        select(ActivityLog.object_id)
        .where(ActivityLog.user_id == user_id, ActivityLog.action == "project_done")
        .scalar_subquery()
    )
    rows = await session.execute(
        select(
            Category.code,
            func.count(Project.id).filter(cast(Project.id, String).in_(done)),
            func.count(Project.id),
        )
        .join(Project, Project.category_id == Category.id)
        .where(Project.status == ContentStatus.PUBLISHED)
        .group_by(Category.code)
    )
    return {code: (finished, total) for code, finished, total in rows.all()}


async def badge_progress(session: AsyncSession, user: User) -> dict[str, tuple[int, int]]:
    """(current, target) per badge, for progress bars in the profile."""
    categories = await category_progress(session, user.id)
    progress = {
        "first_step": (1 if user.points_total > 0 else 0, 1),
        "streak_7": (min(user.streak_best, STREAK_BADGE_DAYS), STREAK_BADGE_DAYS),
        "quiz_champion": (
            min(await _count(session, user.id, "quiz_correct"), QUIZ_CHAMPION_ANSWERS),
            QUIZ_CHAMPION_ANSWERS,
        ),
        "sorting_master": (
            min(await _count(session, user.id, "game_correct"), SORTING_MASTER_SORTS),
            SORTING_MASTER_SORTS,
        ),
    }
    for code, category in CATEGORY_MASTERS.items():
        progress[code] = categories.get(category, (0, 0))
    return progress


async def earned_badge_codes(session: AsyncSession, user: User) -> set[str]:
    codes: set[str] = set()
    if user.points_total > 0:
        codes.add("first_step")
    if user.streak_best >= STREAK_BADGE_DAYS:
        codes.add("streak_7")
    if await _count(session, user.id, "quiz_correct") >= QUIZ_CHAMPION_ANSWERS:
        codes.add("quiz_champion")
    if await _count(session, user.id, "game_correct") >= SORTING_MASTER_SORTS:
        codes.add("sorting_master")
    categories = await category_progress(session, user.id)
    codes.update(
        code
        for code, category in CATEGORY_MASTERS.items()
        if (progress := categories.get(category)) and progress[1] > 0 and progress[0] == progress[1]
    )
    return codes


async def award_badges(session: AsyncSession, user_id: int) -> list[Badge]:
    """Grant every badge whose condition is now met. Returns only the newly earned ones.

    A badge is never taken away, even if new projects are added to its category later.
    """
    user = await session.get(User, user_id, populate_existing=True)
    codes = await earned_badge_codes(session, user)
    if not codes:
        return []
    badges = (await session.scalars(select(Badge).where(Badge.code.in_(codes)))).all()
    if not badges:
        return []
    inserted = await session.scalars(
        insert(UserBadge)
        .values([{"user_id": user_id, "badge_id": b.id} for b in badges])
        .on_conflict_do_nothing()
        .returning(UserBadge.badge_id)
    )
    new_ids = set(inserted.all())
    new = sorted((b for b in badges if b.id in new_ids), key=lambda b: b.sort_order)
    for badge in new:
        track(session, user, "badge_earned", badge=badge.code)
    return new


def badges_out(badges: list[Badge]) -> list[BadgeOut]:
    return [
        BadgeOut(code=b.code, name=b.name, description=b.description, icon=b.icon) for b in badges
    ]
