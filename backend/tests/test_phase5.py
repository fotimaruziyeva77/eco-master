from datetime import UTC, date, datetime, time
from types import SimpleNamespace

import pytest
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import SendMessage
from sqlalchemy import select

from app.bot.handlers import feedback_report, on_inline_query
from app.config import get_settings
from app.deps import bot_dep
from app.i18n import t
from app.main import app
from app.models import OnboardingStep, User
from app.reminders import reminder_text, send_due_reminders
from app.seed import seed_badges, seed_categories, seed_demo
from app.sharing import share_text
from tests.conftest import login

DAY = date(2026, 10, 12)


def at(hour: int, minute: int = 0) -> datetime:
    """A moment on DAY given in Tashkent time (UTC+5)."""
    return datetime(DAY.year, DAY.month, DAY.day, hour - 5, minute, tzinfo=UTC)


class FakeBot:
    def __init__(self, blocked: set[int] | None = None, inline: bool = True):
        self.blocked = blocked or set()
        self.inline = inline
        self.messages: list[tuple[int, str]] = []
        self.documents: list[tuple[int, str, str]] = []
        self.prepared: list = []

    def _check(self, chat_id: int) -> None:
        if chat_id in self.blocked:
            raise TelegramForbiddenError(
                method=SendMessage(chat_id=chat_id, text="x"), message="bot was blocked by the user"
            )

    async def send_message(self, chat_id, text, **kwargs):
        self._check(chat_id)
        self.messages.append((chat_id, text))

    async def send_document(self, chat_id, document, caption=None, **kwargs):
        self._check(chat_id)
        self.documents.append((chat_id, document.filename, caption))

    async def save_prepared_inline_message(self, user_id, result, **kwargs):
        self.prepared.append(result)
        return SimpleNamespace(id="prepared-1")

    async def me(self):
        return SimpleNamespace(supports_inline_queries=self.inline)


class FakeInlineQuery:
    def __init__(self, user_id: int, query: str, language_code: str = "en"):
        self.query = query
        self.from_user = SimpleNamespace(id=user_id, language_code=language_code)
        self.answers: list = []

    async def answer(self, results, **kwargs):
        self.answers.append((results, kwargs))


@pytest.fixture
async def content(session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_demo(session)
    await session.commit()


@pytest.fixture
def fake_bot():
    bot = FakeBot()
    app.dependency_overrides[bot_dep] = lambda: bot
    yield bot
    app.dependency_overrides.pop(bot_dep, None)


async def make_user(session, telegram_id: int, **values) -> User:
    defaults = {
        "nickname": f"User{telegram_id}",
        "onboarding_step": OnboardingStep.DONE,
        "write_access": True,
        "reminders_enabled": True,
        "reminder_time": time(18, 0),
    }
    user = User(telegram_id=telegram_id, **(defaults | values))
    session.add(user)
    await session.commit()
    return user


# ------------------------------------------------------------------- reminders


async def test_reminder_is_sent_once_after_the_chosen_time(content, session):
    await make_user(session, 1)
    bot = FakeBot()

    assert await send_due_reminders(session, bot, now=at(17, 55)) == 0
    assert await send_due_reminders(session, bot, now=at(18, 5)) == 1
    assert await send_due_reminders(session, bot, now=at(19, 0)) == 0  # once a day
    assert bot.messages[0][0] == 1


@pytest.mark.parametrize(
    "values",
    [
        {"reminders_enabled": False},
        {"write_access": False},
        {"last_task_date": DAY},  # today's task is already done
        {"is_blocked": True},
        {"onboarding_step": OnboardingStep.INTRO},
    ],
)
async def test_reminder_is_skipped(content, session, values):
    # QM-11: no reminder when switched off or the task is already done.
    await make_user(session, 2, **values)
    bot = FakeBot()
    assert await send_due_reminders(session, bot, now=at(18, 30)) == 0
    assert bot.messages == []


async def test_no_reminders_in_quiet_hours(content, session):
    await make_user(session, 3, reminder_time=time(20, 0))
    bot = FakeBot()
    assert await send_due_reminders(session, bot, now=at(21, 30)) == 0
    assert bot.messages == []


async def test_blocked_bot_turns_reminders_off(content, session):
    user = await make_user(session, 4)
    bot = FakeBot(blocked={4})
    assert await send_due_reminders(session, bot, now=at(18, 30)) == 0
    await session.refresh(user)
    assert user.reminders_enabled is False
    assert user.write_access is False


async def test_one_blocked_chat_does_not_stop_the_others(content, session):
    users = [await make_user(session, telegram_id) for telegram_id in (21, 22, 23)]
    bot = FakeBot(blocked={22})
    assert await send_due_reminders(session, bot, now=at(18, 30)) == 2
    assert [chat_id for chat_id, _ in bot.messages] == [21, 23]
    for user in users:
        await session.refresh(user)
        assert user.last_reminder_date == DAY
    assert [u.reminders_enabled for u in users] == [True, False, True]


async def test_reminder_text(session):
    user = User(telegram_id=5, nickname="Leaf", language="uz", streak_current=3, last_task_date=DAY)
    text = reminder_text(user, "Sort <5> bottles", date(2026, 10, 13))
    assert "Leaf" in text
    assert "&lt;5&gt;" in text  # user-visible content is escaped for HTML mode
    assert "3 kun" in text


# --------------------------------------------------------------------- lessons


@pytest.fixture
async def headers(client, content):
    body = await login(client, telegram_id=1500, language_code="ru")
    return {"Authorization": f"Bearer {body['token']}"}


async def test_lessons_list_and_detail(client, headers):
    lessons = (await client.get("/api/lessons", headers=headers)).json()
    assert len(lessons) == 3
    detail = (await client.get(f"/api/lessons/{lessons[0]['slug']}", headers=headers)).json()
    assert set(detail["body"]) == {"uz", "ru", "en"}
    plan = detail["body"]["uz"]["plan"]
    assert sum(step["minutes"] for step in plan) == 45


@pytest.mark.parametrize("lang", ["uz", "ru", "en"])
async def test_lesson_pdf_in_every_language(client, headers, lang):
    r = await client.get(f"/api/lessons/plastic-and-us/pdf?lang={lang}", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
    assert f"plastic-and-us-{lang}.pdf" in r.headers["content-disposition"]


async def test_send_pdf_without_bot(client, headers):
    r = await client.post("/api/lessons/plastic-and-us/send", json={}, headers=headers)
    assert r.status_code == 503


async def test_send_pdf_to_chat(client, headers, fake_bot):
    # QM-15: the bot sends the lesson PDF in the user's language.
    r = await client.post("/api/lessons/plastic-and-us/send", json={}, headers=headers)
    assert r.json() == {"sent": True}
    chat_id, filename, caption = fake_bot.documents[0]
    assert chat_id == 1500
    assert filename == "eco-master-plastic-and-us-ru.pdf"
    assert "Пластик и мы" in caption


async def test_send_pdf_when_user_never_started_bot(client, headers, fake_bot, session):
    fake_bot.blocked.add(1500)
    r = await client.post("/api/lessons/plastic-and-us/send", json={}, headers=headers)
    assert r.status_code == 409
    assert r.json()["detail"] == "bot_not_started"
    user = await session.scalar(select(User).where(User.telegram_id == 1500))
    assert user.write_access is False


# ----------------------------------------------------------------------- share


async def test_share_texts(client, headers):
    progress = (await client.post("/api/share", json={"kind": "progress"}, headers=headers)).json()
    assert "Eco-Master" in progress["text"]
    assert progress["prepared_message_id"] is None  # no bot in tests

    project = await client.post(
        "/api/share",
        json={"kind": "project", "object_id": "dry-leaves-compost"},
        headers=headers,
    )
    assert "Компост из сухих листьев" in project.json()["text"]

    quiz = await client.post(
        "/api/share", json={"kind": "quiz", "object_id": "8/10"}, headers=headers
    )
    assert "8/10" in quiz.json()["text"]

    bad = await client.post(
        "/api/share", json={"kind": "quiz", "object_id": "11/10"}, headers=headers
    )
    assert bad.status_code == 422


async def test_progress_share_never_brags_about_zeros(content, session):
    user = await make_user(session, 1700, language="en")
    assert await share_text(session, user, "progress", None) == t("share_invite", "en")
    user.points_total = 35
    assert await share_text(session, user, "progress", None) == t("share_points", "en", points=35)


async def test_share_prepares_telegram_message(client, headers, fake_bot, monkeypatch):
    # QM-16: with the bot configured, a ready message with an "open app" button is prepared.
    monkeypatch.setattr(get_settings(), "bot_username", "ekoustoz_bot")
    body = (await client.post("/api/share", json={"kind": "progress"}, headers=headers)).json()
    assert body["prepared_message_id"] == "prepared-1"
    assert body["url"] == "https://t.me/ekoustoz_bot/app?startapp=share"
    button = fake_bot.prepared[0].reply_markup.inline_keyboard[0][0]
    assert button.url == body["url"]
    # Older clients share through inline mode with the same message.
    assert body["inline_query"] == "progress"

    project = await client.post(
        "/api/share",
        json={"kind": "project", "object_id": "dry-leaves-compost"},
        headers=headers,
    )
    assert project.json()["inline_query"] == "project dry-leaves-compost"


async def test_no_inline_query_without_inline_mode(client, headers, fake_bot, monkeypatch):
    monkeypatch.setattr(get_settings(), "bot_username", "ekoustoz_bot")
    fake_bot.inline = False
    body = (await client.post("/api/share", json={"kind": "progress"}, headers=headers)).json()
    assert body["prepared_message_id"] == "prepared-1"
    assert body["inline_query"] is None


async def test_inline_share_for_older_clients(content, session):
    await make_user(session, 1600, language="ru")
    query = FakeInlineQuery(1600, "quiz 7/10")
    await on_inline_query(query)
    [article], options = query.answers[0]
    assert "7/10" in article.input_message_content.message_text
    assert article.reply_markup.inline_keyboard[0][0].text == "Открыть приложение"
    assert options == {"cache_time": 0, "is_personal": True}

    # A malformed query still gives a sensible message.
    query = FakeInlineQuery(1600, "quiz 99/10")
    await on_inline_query(query)
    [article], _ = query.answers[0]
    assert "Eco-Master" in article.input_message_content.message_text


async def test_inline_share_for_strangers(content):
    query = FakeInlineQuery(777, "", language_code="uz")
    await on_inline_query(query)
    [article], _ = query.answers[0]
    assert "Qo'shil" in article.input_message_content.message_text


# -------------------------------------------------------------------- feedback


def test_feedback_report_keeps_users_anonymous():
    user = User(id=42, telegram_id=987654321, language="ru", path="teacher")
    report = feedback_report(user, "Hello <script>")
    assert "#42" in report
    assert "987654321" not in report
    assert "&lt;script&gt;" in report
