import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import func, select, update

from app.daily import task_of_the_day
from app.models import ActivityLog, DailyTask, DailyTaskSchedule, Report, User
from app.seed import seed_badges, seed_banned_words, seed_categories, seed_demo
from app.timeutil import local_today
from tests.conftest import login


async def onboard(client, telegram_id: int, nickname: str) -> tuple[dict, int]:
    body = await login(client, telegram_id=telegram_id)
    headers = {"Authorization": f"Bearer {body['token']}"}
    await client.post("/api/onboarding/path", json={"path": "student"}, headers=headers)
    await client.post("/api/onboarding/nickname", json={"nickname": nickname}, headers=headers)
    await client.post("/api/onboarding/complete", headers=headers)
    return headers, body["user"]["id"]


@pytest.fixture
async def player(client, session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_banned_words(session)
    await seed_demo(session)
    await session.commit()
    return await onboard(client, 1000, "Main_Player")


async def give_points(session, user_id: int, points: int, *, day: date, at: datetime) -> None:
    session.add(
        ActivityLog(user_id=user_id, action="test", points=points, local_date=day, created_at=at)
    )
    await session.execute(
        update(User).where(User.id == user_id).values(points_total=User.points_total + points)
    )
    await session.commit()


def done_payload() -> dict:
    return {"client_event_id": str(uuid.uuid4())}


# ----------------------------------------------------------------- daily + streak


async def test_daily_task_once_per_day(client, player):
    headers, _ = player
    state = (await client.get("/api/daily", headers=headers)).json()
    assert state["task"]["points"] == 20
    assert state["done_today"] is False

    first = (await client.post("/api/daily/done", json=done_payload(), headers=headers)).json()
    assert first["awarded"] is True
    assert first["points"] == 20
    assert first["streak_current"] == 1

    second = (await client.post("/api/daily/done", json=done_payload(), headers=headers)).json()
    assert second["awarded"] is False
    assert second["points_total"] == 20

    me = (await client.get("/api/me", headers=headers)).json()
    assert me["done_today"] is True
    assert me["streak_current"] == 1


async def test_seventh_day_gives_bonus_and_badge(client, player, session):
    # QM-10: 7 days in a row -> 50 bonus points and the "7-day streak" badge.
    headers, user_id = player
    yesterday = local_today() - timedelta(days=1)
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_task_date=yesterday, streak_current=6, streak_best=6)
    )
    await session.commit()

    body = (await client.post("/api/daily/done", json=done_payload(), headers=headers)).json()
    assert body["streak_current"] == 7
    assert body["bonus_points"] == 50
    assert body["points_total"] == 70
    assert "streak_7" in {b["code"] for b in body["new_badges"]}


async def test_missed_day_resets_streak(client, player, session):
    headers, user_id = player
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_task_date=local_today() - timedelta(days=2), streak_current=5, streak_best=5)
    )
    await session.commit()

    me = (await client.get("/api/me", headers=headers)).json()
    assert me["streak_current"] == 0
    body = (await client.post("/api/daily/done", json=done_payload(), headers=headers)).json()
    assert body["streak_current"] == 1
    assert body["streak_best"] == 5
    assert body["bonus_points"] == 0


async def test_task_is_shared_and_schedulable(player, session):
    day = date(2026, 10, 12)
    first = await task_of_the_day(session, day)
    assert (await task_of_the_day(session, day)).id == first.id
    assert (await task_of_the_day(session, day + timedelta(days=1))).id != first.id

    last = (await session.scalars(select(DailyTask).order_by(DailyTask.id.desc()))).first()
    session.add(DailyTaskSchedule(day=day, task_id=last.id))
    await session.commit()
    assert (await task_of_the_day(session, day)).id == last.id


async def test_home_has_daily_task_and_featured_project(client, player):
    headers, _ = player
    body = (await client.get("/api/home", headers=headers)).json()
    assert body["daily"]["task"]["text"]["uz"]
    assert body["featured"]["slug"]
    assert body["categories"][0]["examples"]["uz"]


# ------------------------------------------------------------------ leaderboard


async def test_leaderboard_order_and_ties(client, player, session):
    headers, me_id = player
    _, a = await onboard(client, 1001, "Alpha")
    _, b = await onboard(client, 1002, "Bravo")
    _, c = await onboard(client, 1003, "Charlie")
    today = local_today()
    now = datetime.now(UTC)
    await give_points(session, b, 30, day=today, at=now)
    await give_points(session, a, 30, day=today, at=now - timedelta(minutes=5))  # reached first
    await give_points(session, c, 10, day=today, at=now)

    board = (await client.get("/api/leaderboard?period=week", headers=headers)).json()
    assert [(e["nickname"], e["rank"]) for e in board["entries"]] == [
        ("Alpha", 1),
        ("Bravo", 2),
        ("Charlie", 3),
    ]
    assert board["me"] is None  # no points yet
    assert board["week_start"] == (today - timedelta(days=today.weekday())).isoformat()


async def test_weekly_board_only_counts_this_week(client, player, session):
    headers, me_id = player
    today = local_today()
    last_week = today - timedelta(days=7)
    await give_points(session, me_id, 50, day=last_week, at=datetime.now(UTC) - timedelta(days=7))
    await give_points(session, me_id, 5, day=today, at=datetime.now(UTC))

    week = (await client.get("/api/leaderboard?period=week", headers=headers)).json()
    total = (await client.get("/api/leaderboard?period=all", headers=headers)).json()
    assert week["me"]["points"] == 5
    assert total["me"]["points"] == 55
    assert week["me"]["is_me"] is True


async def test_hidden_and_blocked_users_are_not_listed(client, player, session):
    # QM-13: once the admin hides or blocks someone they disappear at once.
    headers, _ = player
    _, a = await onboard(client, 1001, "Visible")
    _, b = await onboard(client, 1002, "Hidden")
    _, c = await onboard(client, 1003, "Blocked")
    for user_id in (a, b, c):
        await give_points(session, user_id, 10, day=local_today(), at=datetime.now(UTC))
    await session.execute(update(User).where(User.id == b).values(nickname_hidden=True))
    await session.execute(update(User).where(User.id == c).values(is_blocked=True))
    await session.commit()

    board = (await client.get("/api/leaderboard?period=all", headers=headers)).json()
    assert [e["nickname"] for e in board["entries"]] == ["Visible"]


async def test_own_rank_shown_outside_top_100(client, player, session):
    # QM-12: the user sees their own place even when it is not in the top 100.
    headers, me_id = player
    today = local_today()
    others = [
        User(
            telegram_id=50_000 + i,
            nickname=f"Bot_{i}",
            onboarding_step="done",
            points_total=100 + i,
        )
        for i in range(101)
    ]
    session.add_all(others)
    await session.commit()
    await give_points(session, me_id, 1, day=today, at=datetime.now(UTC))

    board = (await client.get("/api/leaderboard?period=all", headers=headers)).json()
    assert len(board["entries"]) == 100
    assert board["entries"][0]["nickname"] == "Bot_100"
    assert board["me"]["rank"] == 102
    assert not any(e["is_me"] for e in board["entries"])


async def test_reports(client, player, session):
    headers, me_id = player
    _, other = await onboard(client, 1001, "Rude_Name")
    for _ in range(2):
        r = await client.post("/api/reports", json={"target_user_id": other}, headers=headers)
        assert r.status_code == 201
    count = await session.scalar(select(func.count()).select_from(Report))
    assert count == 1
    own = await client.post("/api/reports", json={"target_user_id": me_id}, headers=headers)
    assert own.status_code == 400


# ------------------------------------------------------------- profile/settings


@pytest.mark.parametrize(
    ("value", "ok"), [("18:30", True), ("08:00", True), ("07:00", False), ("18:15", False)]
)
async def test_reminder_time_window(client, player, value, ok):
    headers, _ = player
    r = await client.patch("/api/me", json={"reminder_time": value}, headers=headers)
    assert (r.status_code == 200) is ok


async def test_settings_update(client, player):
    headers, _ = player
    r = await client.patch(
        "/api/me", json={"path": "teacher", "reminders_enabled": False}, headers=headers
    )
    assert r.json()["path"] == "teacher"
    assert r.json()["reminders_enabled"] is False


async def test_nickname_change_once_in_30_days(client, player):
    headers, _ = player
    first = await client.post("/api/me/nickname", json={"nickname": "New_Name"}, headers=headers)
    assert first.status_code == 200
    assert first.json()["nickname"] == "New_Name"
    assert first.json()["nickname_change_available_at"]

    second = await client.post("/api/me/nickname", json={"nickname": "Other"}, headers=headers)
    assert second.status_code == 409
    assert second.json()["detail"] == "nickname_change_too_soon"


async def test_delete_account(client, player, session):
    # QM-17: after deletion the user is gone from the rating and starts from scratch.
    headers, user_id = player
    await client.post("/api/daily/done", json=done_payload(), headers=headers)

    assert (await client.delete("/api/me", headers=headers)).status_code == 204
    assert (await client.get("/api/me", headers=headers)).status_code == 401

    orphaned = await session.scalar(
        select(func.count()).select_from(ActivityLog).where(ActivityLog.user_id.is_(None))
    )
    assert orphaned == 1  # kept for statistics, no longer linked to anyone

    again = await login(client, telegram_id=1000)
    assert again["user"]["id"] != user_id
    assert again["user"]["onboarding_step"] == "language"
    assert again["user"]["points_total"] == 0


async def test_stats_and_badge_progress(client, player):
    headers, _ = player
    await client.post("/api/projects/dry-leaves-compost/done", json=done_payload(), headers=headers)
    await client.post("/api/daily/done", json=done_payload(), headers=headers)

    stats = (await client.get("/api/me/stats", headers=headers)).json()
    assert stats["projects_done"] == 1
    assert stats["projects_total"] == 3
    assert stats["tasks_done"] == 1
    assert stats["streak_current"] == 1
    assert stats["rank_all"] == 1
    assert stats["badges_earned"] == 2  # first step + compost master

    badges = {b["code"]: b for b in (await client.get("/api/me/badges", headers=headers)).json()}
    assert (
        badges["quiz_champion"]["progress_current"],
        badges["quiz_champion"]["progress_target"],
    ) == (0, 50)
    assert (
        badges["master_plastic"]["progress_current"],
        badges["master_plastic"]["progress_target"],
    ) == (0, 1)
    assert badges["master_organic"]["earned_at"]
