"""Weekly leagues: players of one tier compete in groups of up to 30 for one week.

Instead of one board where a newcomer never sees the top, everyone plays against about thirty
people of their own tier. A player joins a group with their first points of a week. When the
next week starts, last week's group decides their tier: the top five go one tier up, the bottom
five of a group of ten or more go one down, the rest stay. That is worked out the moment they
join the new week, from a week that can no longer change, so no weekly job is needed. Players
who sit a week out keep their tier.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog, LeagueGroup, LeagueMember, User

TIERS = 4  # 0 bronze, 1 silver, 2 gold, 3 diamond
GROUP_SIZE = 30
PROMOTE = 5
DEMOTE = 5
# Small groups only move up: dropping a tier for being 3rd of 4 would feel unfair.
DEMOTE_FROM_SIZE = 10
# Serialises filling the groups of one week and tier (advisory lock key base).
LOCK_BASE = 73_7000_000


@dataclass(frozen=True)
class Standing:
    rank: int
    user_id: int
    nickname: str | None
    avatar: str | None
    points_total: int
    points: int


def promote_count(tier: int) -> int:
    return PROMOTE if tier < TIERS - 1 else 0


def demote_count(tier: int, size: int) -> int:
    return DEMOTE if tier > 0 and size >= DEMOTE_FROM_SIZE else 0


def moved_tier(tier: int, rank: int, size: int, points: int) -> int:
    """The tier after a week, from the rank in the group."""
    if points > 0 and rank <= promote_count(tier):
        return tier + 1
    if rank > size - demote_count(tier, size):
        return tier - 1
    return tier


async def standings(session: AsyncSession, group_id: int, monday: date) -> list[Standing]:
    """The group's players by points of that week; equal points: who got them first."""
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
    points = func.coalesce(week.c.points, 0)
    rows = await session.execute(
        select(
            User.id,
            User.nickname,
            User.nickname_hidden,
            User.avatar,
            User.points_total,
            points.label("points"),
        )
        .join(LeagueMember, LeagueMember.user_id == User.id)
        .outerjoin(week, week.c.user_id == User.id)
        .where(
            LeagueMember.group_id == group_id,
            LeagueMember.week_start == monday,
            User.is_blocked.is_(False),
        )
        .order_by(points.desc(), week.c.last_gain.asc().nulls_last(), User.id)
    )
    return [
        Standing(
            rank=i,
            user_id=row.id,
            nickname=None if row.nickname_hidden else row.nickname,
            avatar=row.avatar,
            points_total=row.points_total,
            points=row.points,
        )
        for i, row in enumerate(rows.all(), start=1)
    ]


async def membership(session: AsyncSession, user_id: int, monday: date) -> LeagueMember | None:
    return await session.get(LeagueMember, (monday, user_id))


@dataclass(frozen=True)
class WeekResult:
    tier_before: int
    tier_after: int
    rank: int
    size: int


async def result_of(session: AsyncSession, user_id: int, monday: date) -> WeekResult | None:
    """How the user did in that week's group, and the tier it gives them."""
    member = await membership(session, user_id, monday)
    if member is None:
        return None
    table = await standings(session, member.group_id, monday)
    mine = next((s for s in table if s.user_id == user_id), None)
    if mine is None:
        return None
    after = moved_tier(member.tier, mine.rank, len(table), mine.points)
    return WeekResult(member.tier, after, mine.rank, len(table))


async def join_week(session: AsyncSession, user_id: int, monday: date) -> None:
    """Put the user into a group of this week, settling last week's result first.

    Called with the user's first points of a week (app.points.award); later calls do nothing.
    """
    if await membership(session, user_id, monday) is not None:
        return
    user = await session.get(User, user_id)
    if user is None:
        return
    tier = user.league_tier
    last = await result_of(session, user_id, monday - timedelta(days=7))
    if last is not None:
        tier = last.tier_after
    lock = LOCK_BASE + monday.toordinal() * 10 + tier
    await session.execute(select(func.pg_advisory_xact_lock(lock)))
    group_id = await session.scalar(
        select(LeagueGroup.id)
        .outerjoin(LeagueMember, LeagueMember.group_id == LeagueGroup.id)
        .where(LeagueGroup.week_start == monday, LeagueGroup.tier == tier)
        .group_by(LeagueGroup.id)
        .having(func.count(LeagueMember.user_id) < GROUP_SIZE)
        .order_by(LeagueGroup.id)
        .limit(1)
    )
    if group_id is None:
        group = LeagueGroup(week_start=monday, tier=tier)
        session.add(group)
        await session.flush()
        group_id = group.id
    inserted = await session.execute(
        insert(LeagueMember)
        .values(week_start=monday, user_id=user_id, group_id=group_id, tier=tier)
        .on_conflict_do_nothing()
        .returning(LeagueMember.user_id)
    )
    if inserted.scalar_one_or_none() is not None and user.league_tier != tier:
        user.league_tier = tier


def days_left(today: date, monday: date) -> int:
    """Days of the week still to play, today included."""
    return (monday + timedelta(days=7) - today).days
