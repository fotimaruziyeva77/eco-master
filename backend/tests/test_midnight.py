"""Day changes at 00:00 Tashkent time (TZ 4, 13): daily task, streak, weekly board, limits."""

import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select, update

from app.models import ActivityLog, User
from app.seed import seed_badges, seed_categories, seed_demo
from app.timeutil import TASHKENT
from tests.test_phase4_api import onboard

SUNDAY = date(2026, 11, 1)
MONDAY = date(2026, 11, 2)


@pytest.fixture
async def content(session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_demo(session)
    await session.commit()


@pytest.fixture
def clock(monkeypatch):
    """Pretend it is a given wall-clock time in Tashkent."""
    current: dict[str, datetime] = {}
    monkeypatch.setattr("app.timeutil.utc_now", lambda: current.get("now") or datetime.now(UTC))

    def set_tashkent_time(*parts: int) -> None:
        current["now"] = datetime(*parts, tzinfo=TASHKENT).astimezone(UTC)

    return set_tashkent_time


def event_id() -> dict:
    return {"client_event_id": str(uuid.uuid4())}


async def board(client, headers, period: str) -> list[int]:
    data = (await client.get(f"/api/leaderboard?period={period}", headers=headers)).json()
    return [e["user_id"] for e in data["entries"]]


async def test_task_done_at_23_59_counts_for_that_day(client, session, content, clock):
    # QM-09: the task changes at 00:00 Tashkent; 23:59 still belongs to the old day.
    headers, user_id = await onboard(client, 9501, "Night_Owl")
    clock(2026, 11, 1, 23, 59, 30)
    sunday = (await client.get("/api/daily", headers=headers)).json()
    done = (await client.post("/api/daily/done", json=event_id(), headers=headers)).json()
    assert done["awarded"] is True and done["streak_current"] == 1
    row = await session.scalar(
        select(ActivityLog).where(
            ActivityLog.user_id == user_id, ActivityLog.action == "daily_task"
        )
    )
    assert row.local_date == SUNDAY

    clock(2026, 11, 2, 0, 0, 30)
    monday = (await client.get("/api/daily", headers=headers)).json()
    assert monday["done_today"] is False
    assert monday["task"]["id"] != sunday["task"]["id"]
    assert monday["streak_current"] == 1  # yesterday was done: the streak lives on
    again = (await client.post("/api/daily/done", json=event_id(), headers=headers)).json()
    assert again["awarded"] is True and again["streak_current"] == 2


async def test_missed_day_resets_the_streak_at_midnight(client, session, content, clock):
    headers, user_id = await onboard(client, 9502, "Late_Comer")
    clock(2026, 11, 1, 12, 0)
    await client.post("/api/daily/done", json=event_id(), headers=headers)

    clock(2026, 11, 2, 23, 59, 59)  # Monday is nearly over: Sunday was yesterday
    assert (await client.get("/api/me", headers=headers)).json()["streak_current"] == 1
    clock(2026, 11, 3, 0, 0, 1)  # Tuesday: Monday was missed
    assert (await client.get("/api/me", headers=headers)).json()["streak_current"] == 0


async def test_weekly_board_starts_from_zero_on_monday(client, session, content, clock):
    # QM-12: the weekly leaderboard restarts at Monday 00:00 Tashkent.
    headers, user_id = await onboard(client, 9503, "Week_Star")
    other, _ = await onboard(client, 9504, "Watcher_Two")
    session.add(ActivityLog(user_id=user_id, action="test", points=30, local_date=SUNDAY))
    await session.execute(update(User).where(User.id == user_id).values(points_total=30))
    await session.commit()

    clock(2026, 11, 1, 23, 59)
    assert user_id in await board(client, other, "week")
    clock(2026, 11, 2, 0, 1)
    assert user_id not in await board(client, other, "week")
    assert user_id in await board(client, other, "all")


async def test_game_limit_starts_again_at_midnight(client, session, content, clock):
    # The 40-point daily cap of the sorting game is per Tashkent day (QM-08).
    headers, user_id = await onboard(client, 9505, "Sorter_One")
    session.add(
        ActivityLog(
            user_id=user_id, action="game_correct", object_id="1", points=40, local_date=SUNDAY
        )
    )
    await session.commit()
    clock(2026, 11, 1, 23, 58)
    assert (await client.get("/api/games", headers=headers)).json()["game_points_today"] == 40
    clock(2026, 11, 2, 0, 1)
    assert (await client.get("/api/games", headers=headers)).json()["game_points_today"] == 0


async def test_requests_per_user_are_limited(client, content):
    # TZ 11.1: requests per user are capped; normal use stays well below the limit.
    headers, _ = await onboard(client, 9506, "Busy_Bee")
    codes = [(await client.get("/api/me", headers=headers)).status_code for _ in range(125)]
    assert 429 in codes
    assert set(codes[:100]) == {200}
