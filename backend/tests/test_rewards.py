"""Stage 6: the Monday summary, kinder reminders, avatars that unlock with levels."""

from datetime import timedelta

import pytest
from PIL import Image
from sqlalchemy import update

from app import leagues, story
from app.api import share as share_api
from app.config import get_settings
from app.content_media import media_root
from app.leagues import WeekResult
from app.models import LeagueMember, User
from app.points import award
from app.ratelimit import RateLimiter
from app.reminders import send_due_reminders, weekly_text
from app.seed import seed_badges, seed_categories, seed_demo
from app.story import story_picture
from app.tree import Growth, tree_growth, tree_parts
from tests.conftest import login
from tests.test_phase5 import DAY, FakeBot, at, make_user

# DAY is a Monday.
LAST_MONDAY = DAY - timedelta(days=7)


@pytest.fixture
async def content(session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_demo(session)
    await session.commit()


async def earn(session, user_id: int, points: int, day) -> None:
    await award(session, user_id, "test", points, day=day)
    await session.commit()


# ------------------------------------------------------------- Monday summary


async def test_monday_summary_takes_the_place_of_the_reminder(content, session):
    user = await make_user(session, 31, nickname="Leaf")
    await earn(session, user.id, 40, LAST_MONDAY + timedelta(days=2))
    bot = FakeBot()

    assert await send_due_reminders(session, bot, now=at(17, 55)) == 0  # before the chosen time
    assert await send_due_reminders(session, bot, now=at(18, 5)) == 1
    [(chat_id, text)] = bot.messages
    assert chat_id == 31
    assert "Leaf" in text and "<b>40</b>" in text
    assert "1-o'rin" in text  # alone in the group
    assert "Kumush liga" in text  # first of a bronze group goes up
    assert "Bugungi topshiriq" in text  # today's task is still open

    # No reminder on top of it, and no second summary.
    assert await send_due_reminders(session, bot, now=at(19, 0)) == 0
    await session.refresh(user)
    assert user.last_weekly_date == DAY
    assert user.last_reminder_date == DAY


async def test_summary_when_the_task_is_already_done(content, session):
    user = await make_user(session, 32, last_task_date=DAY)
    await earn(session, user.id, 15, LAST_MONDAY)
    bot = FakeBot()
    assert await send_due_reminders(session, bot, now=at(18, 30)) == 1
    assert "Yangi hafta boshlandi" in bot.messages[0][1]


async def test_no_summary_without_points_last_week(content, session):
    # Nothing earned last week: the ordinary reminder goes out.
    await make_user(session, 33)
    bot = FakeBot()
    assert await send_due_reminders(session, bot, now=at(18, 30)) == 1
    assert "kutmoqda" in bot.messages[0][1]


async def test_summary_only_on_monday(content, session):
    user = await make_user(session, 34)
    await earn(session, user.id, 20, LAST_MONDAY)
    bot = FakeBot()
    tuesday_evening = at(18, 30) + timedelta(days=1)
    assert await send_due_reminders(session, bot, now=tuesday_evening) == 1
    assert "kutmoqda" in bot.messages[0][1]
    await session.refresh(user)
    assert user.last_weekly_date is None


async def test_summary_respects_the_reminder_switch(content, session):
    user = await make_user(session, 35, reminders_enabled=False)
    await earn(session, user.id, 20, LAST_MONDAY)
    bot = FakeBot()
    assert await send_due_reminders(session, bot, now=at(18, 30)) == 0
    assert bot.messages == []


def test_weekly_text_lines():
    user = User(telegram_id=1, nickname="Leaf", language="en")
    down = weekly_text(user, 12, WeekResult(tier_before=2, tier_after=1, rank=11, size=12), None)
    assert "Place 11" in down
    assert "Silver league" in down
    assert "good luck" in down
    same = weekly_text(
        user, 12, WeekResult(tier_before=1, tier_after=1, rank=6, size=12), "Sort <3>"
    )
    assert "league</b>" not in same  # no tier line when nothing changed
    assert "&lt;3&gt;" in same


# -------------------------------------------------------- kinder reminders


async def test_comeback_text_after_three_days_away(content, session):
    await make_user(session, 41, last_active_at=at(10) - timedelta(days=4))
    bot = FakeBot()
    assert await send_due_reminders(session, bot, now=at(18, 30)) == 1
    assert "sog'indik" in bot.messages[0][1]


async def test_a_week_away_means_one_reminder_a_week_and_five_weeks_none(content, session):
    away = at(10) - timedelta(days=10)
    await make_user(session, 42, last_active_at=away, last_reminder_date=DAY - timedelta(days=3))
    await make_user(session, 43, last_active_at=away, last_reminder_date=DAY - timedelta(days=7))
    await make_user(session, 44, last_active_at=at(10) - timedelta(days=40))
    bot = FakeBot()
    assert await send_due_reminders(session, bot, now=at(18, 30)) == 1
    assert [chat_id for chat_id, _ in bot.messages] == [43]


# ------------------------------------------------------------------ avatars


async def test_avatars_unlock_with_the_level(client, session):
    body = await login(client, telegram_id=3600)
    headers = {"Authorization": f"Bearer {body['token']}"}
    avatars = (await client.get("/api/me/avatars", headers=headers)).json()
    assert len(avatars) == 28
    assert sum(a["unlocked"] for a in avatars) == 12
    penguin = next(a for a in avatars if a["emoji"] == "🐧")
    assert penguin == {"emoji": "🐧", "level_code": "beginner", "unlocked": False}

    response = await client.post("/api/me/avatar", json={"avatar": "🐧"}, headers=headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "avatar_locked"
    response = await client.post("/api/me/avatar", json={"avatar": "🦠"}, headers=headers)
    assert response.status_code == 422

    await session.execute(
        update(User).where(User.id == body["user"]["id"]).values(points_total=120)
    )
    await session.commit()
    response = await client.post("/api/me/avatar", json={"avatar": "🐧"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["avatar"] == "🐧"
    assert (await client.get("/api/me", headers=headers)).json()["avatar"] == "🐧"
    # None goes back to the picture the app picks.
    response = await client.post("/api/me/avatar", json={"avatar": None}, headers=headers)
    assert response.json()["avatar"] is None


async def test_league_board_shows_the_chosen_avatar(session):
    user = await make_user(session, 45, avatar="🐼")
    await earn(session, user.id, 5, LAST_MONDAY)
    member = await session.get(LeagueMember, (LAST_MONDAY, user.id))
    [row] = await leagues.standings(session, member.group_id, LAST_MONDAY)
    assert row.avatar == "🐼"


# ------------------------------------------------------------ tree and Stories


def test_tree_grows_with_the_level():
    assert tree_growth(0) == Growth(stage=0, progress=0.0, fruits=0)
    assert tree_growth(300) == Growth(stage=1, progress=0.5, fruits=0)
    assert tree_growth(2499).stage == 3
    assert tree_growth(2500) == Growth(stage=4, progress=1.0, fruits=1)
    assert tree_growth(99_999).fruits == 8
    # Each stage draws something more than the ground.
    for points in (0, 50, 100, 500, 1000, 2500):
        assert len(tree_parts(tree_growth(points))) > 2


async def test_story_picture(client, monkeypatch):
    body = await login(client, telegram_id=3601)
    headers = {"Authorization": f"Bearer {body['token']}"}
    first = (await client.post("/api/share/story", headers=headers)).json()
    assert "/media/s/" in first["media_url"]
    assert first["text"]
    name = first["media_url"].rsplit("/", 1)[1]
    with Image.open(media_root() / "s" / name) as picture:
        assert picture.size == (1080, 1920)
    # The same points and language give the same picture.
    again = (await client.post("/api/share/story", headers=headers)).json()
    assert again["media_url"] == first["media_url"]

    monkeypatch.setattr(share_api, "story_limit", RateLimiter(limit=0, window=3600))
    response = await client.post("/api/share/story", headers=headers)
    assert response.status_code == 429


def test_a_whole_class_can_share_the_same_picture():
    # The same points and language at the same moment: one picture, no clash, no error.
    from concurrent.futures import ThreadPoolExecutor

    settings = get_settings()
    with ThreadPoolExecutor(max_workers=4) as pool:
        names = list(pool.map(lambda _: story_picture(settings, "uz", 4321), range(4)))
    assert len(set(names)) == 1
    folder = media_root() / "s"
    assert (folder / names[0]).exists()
    assert not list(folder.glob("*.tmp"))


def test_old_pictures_go_but_the_one_handed_out_stays(monkeypatch):
    import os
    import time

    settings = get_settings()
    name = story_picture(settings, "en", 1234)
    path = media_root() / "s" / name
    other = media_root() / "s" / "old-picture.jpg"
    other.write_bytes(b"x")
    long_ago = time.time() - story.KEEP_SECONDS - 60
    os.utime(path, (long_ago, long_ago))
    os.utime(other, (long_ago, long_ago))
    # Handing the old picture out again keeps it (and refreshes it); the other one goes.
    assert story_picture(settings, "en", 1234) == name
    assert path.exists()
    assert path.stat().st_mtime > long_ago
    assert not other.exists()
