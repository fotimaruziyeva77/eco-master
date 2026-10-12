"""Weekly leagues: groups of one tier, standings, moving up and down between weeks."""

from datetime import date, timedelta

from sqlalchemy import func, select, update

from app import leagues
from app.leagues import moved_tier
from app.models import LeagueGroup, LeagueMember, OnboardingStep, User, UserPath
from app.points import award
from tests.conftest import login

MONDAY = date(2026, 11, 2)
NEXT_MONDAY = MONDAY + timedelta(days=7)


async def make_users(session, count: int, tier: int = 0, start: int = 0) -> list[int]:
    users = [
        User(
            telegram_id=900_000 + start + i,
            nickname=f"Player_{start + i}",
            path=UserPath.STUDENT,
            onboarding_step=OnboardingStep.DONE,
            league_tier=tier,
        )
        for i in range(count)
    ]
    session.add_all(users)
    await session.commit()
    return [u.id for u in users]


async def earn(session, user_id: int, points: int, day: date) -> None:
    await award(session, user_id, "test", points, day=day)
    await session.commit()


async def tier_of(session, user_id: int) -> int:
    return await session.scalar(
        select(User.league_tier).where(User.id == user_id).execution_options(populate_existing=True)
    )


def test_moving_rules():
    assert moved_tier(0, rank=1, size=4, points=10) == 1
    assert moved_tier(0, rank=6, size=12, points=10) == 0
    # Bronze can not go down; small groups never go down.
    assert moved_tier(0, rank=12, size=12, points=1) == 0
    assert moved_tier(1, rank=4, size=4, points=1) == 2  # the top five of a small group
    assert moved_tier(1, rank=12, size=12, points=1) == 0
    assert moved_tier(1, rank=9, size=9, points=1) == 1
    # Diamond is the top; nobody goes higher.
    assert moved_tier(3, rank=1, size=30, points=99) == 3
    # No points, no promotion.
    assert moved_tier(0, rank=1, size=3, points=0) == 0


async def test_first_points_of_the_week_join_one_group(session):
    [user] = await make_users(session, 1)
    await earn(session, user, 5, MONDAY)
    await earn(session, user, 5, MONDAY + timedelta(days=2))
    rows = (await session.scalars(select(LeagueMember))).all()
    assert [(r.week_start, r.user_id, r.tier) for r in rows] == [(MONDAY, user, 0)]


async def test_groups_hold_thirty(session):
    users = await make_users(session, 31)
    for user in users:
        await earn(session, user, 2, MONDAY)
    sizes = (
        await session.execute(
            select(LeagueMember.group_id, func.count()).group_by(LeagueMember.group_id)
        )
    ).all()
    assert sorted(size for _, size in sizes) == [1, 30]
    assert await session.scalar(select(func.count()).select_from(LeagueGroup)) == 2


async def test_top_five_go_up_and_bottom_five_go_down(session):
    silver = await make_users(session, 12, tier=1)
    for rank, user in enumerate(silver):
        await earn(session, user, 100 - rank, MONDAY)

    # Next week everyone comes back: their tier follows last week's rank.
    for user in silver:
        await earn(session, user, 1, NEXT_MONDAY)
    tiers = [await tier_of(session, user) for user in silver]
    assert tiers == [2] * 5 + [1] * 2 + [0] * 5


async def test_a_week_away_keeps_the_tier(session):
    [user] = await make_users(session, 1, tier=2)
    await earn(session, user, 10, MONDAY - timedelta(days=14))
    await earn(session, user, 10, NEXT_MONDAY)
    assert await tier_of(session, user) == 2


async def test_league_endpoint(client, session, monkeypatch):
    others = await make_users(session, 3)
    body = await login(client, telegram_id=901_500)
    headers = {"Authorization": f"Bearer {body['token']}"}
    me = body["user"]["id"]
    await session.execute(
        update(User)
        .where(User.id == me)
        .values(nickname="Men_Ozim", onboarding_step=OnboardingStep.DONE, path=UserPath.STUDENT)
    )
    await session.commit()
    monkeypatch.setattr(leagues, "PROMOTE", 1)

    # Last week: second of four. This week: not playing yet.
    for user, points in zip([*others, me], [40, 10, 5, 20], strict=True):
        await earn(session, user, points, MONDAY)
    monkeypatch.setattr("app.api.league.local_today", lambda: NEXT_MONDAY + timedelta(days=2))
    waiting = (await client.get("/api/league", headers=headers)).json()
    assert waiting["joined"] is False
    assert waiting["entries"] == []
    assert waiting["last_week"] == {"tier_before": 0, "tier_after": 0, "rank": 2, "size": 4}
    assert waiting["days_left"] == 5

    # Points this week put the user into a group; the board shows it.
    await earn(session, others[0], 7, NEXT_MONDAY)
    await earn(session, me, 9, NEXT_MONDAY + timedelta(days=1))
    playing = (await client.get("/api/league", headers=headers)).json()
    assert playing["joined"] is True
    # The winner of last week plays one tier up now; the user stays in bronze.
    assert playing["tier"] == 0
    assert [(e["nickname"], e["points"], e["is_me"]) for e in playing["entries"]] == [
        ("Men_Ozim", 9, True)
    ]
    assert playing["promote"] == 1 and playing["demote"] == 0
    assert await tier_of(session, others[0]) == 1


async def test_blocked_players_are_not_on_the_board(session):
    users = await make_users(session, 2)
    for user in users:
        await earn(session, user, 3, MONDAY)
    await session.execute(update(User).where(User.id == users[0]).values(is_blocked=True))
    await session.commit()
    group = await session.scalar(
        select(LeagueMember.group_id).where(LeagueMember.user_id == users[1])
    )
    table = await leagues.standings(session, group, MONDAY)
    assert [s.user_id for s in table] == [users[1]]
