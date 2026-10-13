"""Stage 7: moderation alerts to the team chat, broadcasts, growth statistics."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app import broadcasts
from app.admin.stats import growth
from app.broadcasts import send_next_chunk
from app.config import get_settings
from app.models import (
    AdminAuditLog,
    AdminRole,
    Broadcast,
    BroadcastStatus,
    Listing,
    ListingKind,
    ListingStatus,
    OnboardingStep,
    Report,
    User,
    UserPath,
)
from app.points import award
from app.team_alerts import AlertState, alert_round
from tests.admin_helpers import admin_client
from tests.conftest import login
from tests.test_phase5 import FakeBot, make_user

TEAM_CHAT = -100_123


# ------------------------------------------------------------- moderation alerts


async def add_listing(session, owner_id: int, title: str = "Qalamdon") -> None:
    session.add(
        Listing(
            owner_id=owner_id,
            kind=ListingKind.HANDMADE,
            title=title,
            category="plastic",
            status=ListingStatus.PENDING,
        )
    )
    await session.commit()


async def test_team_hears_about_new_listings_once(session, monkeypatch):
    monkeypatch.setattr(get_settings(), "moderation_chat_id", TEAM_CHAT)
    owner = await make_user(session, 51)
    bot, state = FakeBot(), AlertState()
    now = datetime.now(UTC)

    assert await alert_round(session, bot, state, now=now) is False  # nothing waiting
    await add_listing(session, owner.id)
    assert await alert_round(session, bot, state, now=now) is True
    [(chat_id, text)] = bot.messages
    assert chat_id == TEAM_CHAT
    assert "Bozorga yangi e'lonlar: 1" in text
    # Nothing new: no second message.
    assert await alert_round(session, bot, state, now=now + timedelta(hours=1)) is False

    # Something new soon after: it waits for the gap, then one message about both.
    await add_listing(session, owner.id, "Gul tuvak")
    session.add(Report(reporter_id=owner.id, target_user_id=owner.id, reason="nickname"))
    await session.commit()
    assert await alert_round(session, bot, state, now=now + timedelta(minutes=10)) is False
    assert await alert_round(session, bot, state, now=datetime.now(UTC) + timedelta(hours=1))
    text = bot.messages[-1][1]
    assert "Bozorga yangi e'lonlar: 2" in text
    assert "Taxallus shikoyatlari: 1" in text


async def test_no_team_chat_no_alerts(session, monkeypatch):
    monkeypatch.setattr(get_settings(), "moderation_chat_id", None)
    monkeypatch.setattr(get_settings(), "feedback_chat_id", None)
    owner = await make_user(session, 52)
    await add_listing(session, owner.id)
    bot = FakeBot()
    assert await alert_round(session, bot, AlertState()) is False
    assert bot.messages == []


# ------------------------------------------------------------------ broadcasts


# 12:00 and 23:00 in Tashkent: broadcasts go out only in the day, like the reminders.
NOON = datetime(2026, 10, 12, 7, 0, tzinfo=UTC)
NIGHT = datetime(2026, 10, 12, 18, 0, tzinfo=UTC)


async def send_all(session, bot, now=NOON) -> None:
    while await send_next_chunk(session, bot, now=now):
        pass


async def test_broadcast_from_the_admin_panel(client, session):
    student = await make_user(session, 61, path=UserPath.STUDENT, language="ru")
    teacher = await make_user(session, 62, path=UserPath.TEACHER)
    await make_user(session, 63, path=UserPath.STUDENT, reminders_enabled=False)
    await make_user(session, 64, path=UserPath.STUDENT, onboarding_step=OnboardingStep.INTRO)
    await make_user(session, 66, path=UserPath.STUDENT, language="uz")
    await admin_client(client, session)

    count = (await client.get("/api/admin/broadcasts/audience?audience=student")).json()
    assert count == {"audience": "student", "count": 2}
    assert (await client.get("/api/admin/broadcasts/audience")).json()["count"] == 3

    response = await client.post(
        "/api/admin/broadcasts",
        json={"text": {"uz": "Yangi o'yin chiqdi!", "ru": "Новая игра!", "en": " "}},
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["status"] == "queued"
    assert created["text"] == {"uz": "Yangi o'yin chiqdi!", "ru": "Новая игра!"}

    bot = FakeBot(blocked={62})
    await send_all(session, bot)
    assert [chat_id for chat_id, _ in bot.messages] == [61, 66]
    await send_all(session, bot)
    assert len(bot.messages) == 2  # nobody gets it twice

    broadcast = await session.scalar(select(Broadcast).execution_options(populate_existing=True))
    assert broadcast.status == BroadcastStatus.DONE
    assert (broadcast.total, broadcast.sent, broadcast.failed) == (3, 2, 1)
    await session.refresh(teacher)
    assert teacher.write_access is False  # blocked the bot: no more messages

    # Opening the app from the button counts for this broadcast.
    assert student.language == "ru"
    await login(client, telegram_id=61, start_param=f"broadcast_{broadcast.id}")
    listed = (await client.get("/api/admin/broadcasts")).json()
    assert listed["items"][0]["opened"] == 1
    assert listed["sent_this_week"] == 1

    actions = (await session.scalars(select(AdminAuditLog.action))).all()
    assert "broadcast_create" in actions


async def test_broadcast_text_goes_as_typed(client, session):
    await make_user(session, 67, path=UserPath.STUDENT, language="ru")
    await make_user(session, 68, path=UserPath.STUDENT, language="uz")
    await admin_client(client, session)
    text = {"uz": "Yangi o'yin <b>chiqdi</b>!", "ru": "Новая игра!"}
    assert (await client.post("/api/admin/broadcasts", json={"text": text})).status_code == 201
    bot = FakeBot()
    await send_all(session, bot)
    # Each in their language, as plain text: nothing the admin types becomes markup.
    assert bot.messages == [(67, "Новая игра!"), (68, "Yangi o'yin &lt;b&gt;chiqdi&lt;/b&gt;!")]


async def test_broadcast_waits_for_the_morning(client, session):
    await make_user(session, 69)
    await admin_client(client, session)
    await client.post("/api/admin/broadcasts", json={"text": {"uz": "Salom"}})
    bot = FakeBot()
    assert await send_next_chunk(session, bot, now=NIGHT) is False
    assert bot.messages == []
    await send_all(session, bot)
    assert [chat_id for chat_id, _ in bot.messages] == [69]


async def test_broadcast_needs_uzbek_and_respects_the_weekly_limit(client, session):
    await admin_client(client, session)
    response = await client.post("/api/admin/broadcasts", json={"text": {"ru": "Привет"}})
    assert response.status_code == 422
    response = await client.post("/api/admin/broadcasts", json={"text": {"uz": "x" * 1001}})
    assert response.status_code == 422

    for n in (1, 2):
        response = await client.post("/api/admin/broadcasts", json={"text": {"uz": f"Salom {n}"}})
        assert response.status_code == 201
    response = await client.post("/api/admin/broadcasts", json={"text": {"uz": "Salom 3"}})
    assert response.status_code == 409
    assert response.json()["detail"] == "weekly_limit"


async def test_the_same_broadcast_is_not_queued_twice(client, session):
    # A double click, or a retry after the answer got lost.
    await admin_client(client, session)
    body = {"text": {"uz": "Salom"}, "audience": "student"}
    assert (await client.post("/api/admin/broadcasts", json=body)).status_code == 201
    response = await client.post("/api/admin/broadcasts", json=body)
    assert response.status_code == 409
    assert response.json()["detail"] == "duplicate_broadcast"
    # The same words to other people are a new broadcast.
    body["audience"] = "teacher"
    assert (await client.post("/api/admin/broadcasts", json=body)).status_code == 201


async def test_cancelled_broadcast_is_not_sent(client, session):
    await make_user(session, 65)
    await admin_client(client, session)
    created = (await client.post("/api/admin/broadcasts", json={"text": {"uz": "Salom"}})).json()
    response = await client.post(f"/api/admin/broadcasts/{created['id']}/cancel")
    assert response.json()["status"] == "cancelled"
    bot = FakeBot()
    assert await send_next_chunk(session, bot, now=NOON) is False
    assert bot.messages == []
    # A cancelled broadcast that sent nothing does not count towards the limit.
    assert (await client.get("/api/admin/broadcasts")).json()["sent_this_week"] == 0
    response = await client.post(f"/api/admin/broadcasts/{created['id']}/cancel")
    assert response.status_code == 409


async def test_a_cancel_while_sending_starts_wins(client, session, monkeypatch):
    await make_user(session, 70)
    await admin_client(client, session)
    created = (await client.post("/api/admin/broadcasts", json={"text": {"uz": "Salom"}})).json()
    real_size = broadcasts.audience_size

    async def cancel_meanwhile(session_, audience):
        # The admin presses "To'xtatish" between the bot reading the queue and starting.
        await client.post(f"/api/admin/broadcasts/{created['id']}/cancel")
        return await real_size(session_, audience)

    monkeypatch.setattr(broadcasts, "audience_size", cancel_meanwhile)
    bot = FakeBot()
    await send_all(session, bot)
    assert bot.messages == []
    status = await session.scalar(select(Broadcast.status).where(Broadcast.id == created["id"]))
    assert status == BroadcastStatus.CANCELLED


async def test_editors_can_not_broadcast(client, session):
    await admin_client(client, session, role=AdminRole.EDITOR, login="editor")
    response = await client.post("/api/admin/broadcasts", json={"text": {"uz": "Salom"}})
    assert response.status_code == 403


# ----------------------------------------------------------------- growth stats


async def test_growth_statistics(client, session):
    first = await login(client, telegram_id=71)
    await login(client, telegram_id=72)
    user = await session.get(User, first["user"]["id"])
    user.onboarding_step = OnboardingStep.DONE
    await session.commit()
    await award(session, user.id, "daily_task", 20)
    await session.commit()

    stats = await growth(session, 30)
    activation = stats.activation
    assert activation.registered == 2
    assert activation.onboarded == 1
    assert activation.first_points == 1
    assert activation.daily_task == 1
    assert activation.returned == 0  # both opened the app on one day only
    assert len(stats.cohorts) == 8
    assert stats.cohorts[-1].size == 2
    assert stats.cohorts[-1].weeks == [None] * 7  # this week: nothing to look back on yet
    assert [m.kind for m in stats.messages] == ["reminder", "weekly", "class_report", "broadcast"]

    response = await client.get("/api/admin/stats/growth")
    assert response.status_code == 401  # admins only
