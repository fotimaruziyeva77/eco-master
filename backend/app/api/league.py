"""The user's weekly league group (app/leagues.py)."""

from dataclasses import asdict
from datetime import timedelta

from fastapi import APIRouter

from app.deps import CurrentUser, SessionDep
from app.leagues import (
    days_left,
    demote_count,
    latest_result,
    membership,
    promote_count,
    result_of,
    standings,
)
from app.levels import level_for
from app.schemas import LeagueOut, LeagueResultOut, RankedMemberOut
from app.timeutil import local_today, week_start

router = APIRouter(tags=["league"])


@router.get("/league")
async def league(user: CurrentUser, session: SessionDep) -> LeagueOut:
    today = local_today()
    monday = week_start(today)
    member = await membership(session, user.id, monday)
    last = await result_of(session, user.id, monday - timedelta(days=7))
    tier = user.league_tier
    entries: list[RankedMemberOut] = []
    if member is not None:
        tier = member.tier
        entries = [
            RankedMemberOut(
                rank=s.rank,
                user_id=s.user_id,
                nickname=s.nickname,
                avatar=s.avatar,
                level_code=level_for(s.points_total).code,
                points=s.points,
                is_me=s.user_id == user.id,
            )
            for s in await standings(session, member.group_id, monday)
        ]
    else:
        # Not in a group yet this week: the last week played says where they will play.
        latest = last or await latest_result(session, user.id, monday)
        if latest is not None:
            tier = latest.tier_after
    return LeagueOut(
        tier=tier,
        week_start=monday,
        days_left=days_left(today, monday),
        joined=member is not None,
        entries=entries,
        promote=promote_count(tier),
        demote=demote_count(tier, len(entries)),
        last_week=LeagueResultOut(**asdict(last)) if last else None,
    )
