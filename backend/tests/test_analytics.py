import csv
import io
import uuid
from datetime import datetime, time, timedelta

import pytest
from sqlalchemy import select

from app.models import ActivityLog, AnalyticsEvent, OnboardingStep, Question, User
from app.seed import seed_badges, seed_categories, seed_demo
from app.timeutil import TASHKENT, local_today
from tests.admin_helpers import admin_client
from tests.conftest import login
from tests.test_phase4_api import onboard


@pytest.fixture
async def content(session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_demo(session)
    await session.commit()


async def events(session, name: str | None = None) -> list[AnalyticsEvent]:
    query = select(AnalyticsEvent).order_by(AnalyticsEvent.id)
    if name:
        query = query.where(AnalyticsEvent.name == name)
    return list((await session.scalars(query)).all())


# --------------------------------------------------------------- server events


async def test_launch_and_onboarding_events(client, session, content):
    body = await login(client, telegram_id=8001, language_code="ru", start_param="teacher")
    headers = {"Authorization": f"Bearer {body['token']}"}
    await client.post("/api/onboarding/language", json={"language": "uz"}, headers=headers)
    await client.post("/api/onboarding/path", json={"path": "teacher"}, headers=headers)
    await client.post("/api/onboarding/nickname", json={"nickname": "Ustoz_1"}, headers=headers)
    await client.post("/api/onboarding/complete", headers=headers)
    await login(client, telegram_id=8001, start_param="reminder")

    rows = await events(session)
    assert [(e.name, (e.props or {}).get("step")) for e in rows] == [
        ("app_open", None),
        ("onboarding_step", "language"),
        ("onboarding_step", "path"),
        ("onboarding_step", "nickname"),
        ("onboarding_complete", None),
        ("app_open", None),
        ("reminder_open", None),
    ]
    first, last = rows[0], rows[-2]
    assert first.props == {"source": "teacher", "new": True}
    assert (first.language, first.path) == ("ru", None)
    assert last.props == {"source": "reminder", "new": False}
    assert (last.language, last.path) == ("uz", "teacher")  # state at the time of the event
    user = await session.scalar(select(User).where(User.telegram_id == 8001))
    assert user.source == "teacher"  # the first source is kept
    assert all(e.user_id == user.id for e in rows)  # internal id, never the Telegram id


async def test_quiz_and_game_rounds_finish(client, session, content):
    headers, _ = await onboard(client, 8002, "Player_8002")
    quiz = (await client.post("/api/quiz/rounds", json={"category": None}, headers=headers)).json()
    for q in quiz["questions"]:
        await client.post(
            "/api/quiz/answer",
            json={"round_token": quiz["round_token"], "question_id": q["id"], "option_index": 0},
            headers=headers,
        )
    [finish] = await events(session, "quiz_finish")
    correct = sum(e.props["correct"] for e in await events(session, "quiz_answer"))
    assert finish.props["total"] == len(quiz["questions"])
    assert finish.props["correct"] == correct

    game = (await client.post("/api/game/rounds", headers=headers)).json()
    for item in game["items"]:
        await client.post(
            "/api/game/answer",
            json={
                "round_token": game["round_token"],
                "item_id": item["id"],
                "bin": "plastic",
                "quick": True,
            },
            headers=headers,
        )
    [game_finish] = await events(session, "game_finish")
    assert game_finish.props["mode"] == "quick"
    assert game_finish.props["total"] == len(game["items"])


async def test_progress_events(client, session, content):
    headers, user_id = await onboard(client, 8003, "Learner")
    await client.get("/api/projects/dry-leaves-compost", headers=headers)
    await client.post(
        "/api/projects/dry-leaves-compost/done",
        json={"client_event_id": str(uuid.uuid4())},
        headers=headers,
    )
    await client.post(
        "/api/daily/done", json={"client_event_id": str(uuid.uuid4())}, headers=headers
    )
    await client.post("/api/share", json={"kind": "progress"}, headers=headers)
    await client.get("/api/lessons/plastic-and-us/pdf?lang=ru", headers=headers)

    names = [e.name for e in await events(session) if e.name not in ("app_open", "onboarding_step")]
    assert names == [
        "onboarding_complete",
        "project_view",
        "badge_earned",
        "badge_earned",
        "project_done",
        "daily_task_done",
        "share_click",
        "teacher_pdf",
    ]
    pdf = (await events(session, "teacher_pdf"))[0]
    assert pdf.props == {"lesson": "plastic-and-us", "lang": "ru", "via": "download"}
    daily = (await events(session, "daily_task_done"))[0]
    assert daily.props == {"date": local_today().isoformat(), "streak": 1}


async def test_level_up(client, session, content):
    headers, user_id = await onboard(client, 8004, "Climber")
    user = await session.get(User, user_id)
    user.points_total = 90
    await session.commit()
    await client.post(
        "/api/projects/dry-leaves-compost/done",
        json={"client_event_id": str(uuid.uuid4())},
        headers=headers,
    )
    [level] = await events(session, "level_up")
    assert level.props == {"level": "beginner"}


# ---------------------------------------------------------------- client events


async def test_client_events(client, session, content):
    headers, _ = await onboard(client, 8005, "Watcher_1")
    ok = await client.post(
        "/api/events",
        json={
            "events": [
                {"name": "video_play", "props": {"project": "dry-leaves-compost"}},
                {"name": "error", "props": {"type": "network", "screen": "/games"}},
            ]
        },
        headers=headers,
    )
    assert ok.status_code == 204
    play = (await events(session, "video_play"))[0]
    assert (play.props, play.language, play.path) == (
        {"project": "dry-leaves-compost"},
        "ru",
        "student",
    )

    bad_field = {"events": [{"name": "error", "props": {"telegram_id": 5}}]}
    assert (await client.post("/api/events", json=bad_field, headers=headers)).status_code == 422
    bad_name = {"events": [{"name": "purchase", "props": {}}]}
    assert (await client.post("/api/events", json=bad_name, headers=headers)).status_code == 422
    too_many = {"events": [{"name": "video_play", "props": {}}] * 21}
    assert (await client.post("/api/events", json=too_many, headers=headers)).status_code == 422

    burst = {"events": [{"name": "video_play", "props": {}}] * 20}
    codes = [
        (await client.post("/api/events", json=burst, headers=headers)).status_code
        for _ in range(7)
    ]
    assert codes[:5] == [204] * 5 and codes[-1] == 429


# ------------------------------------------------------------------ statistics


def at(day, hour: int = 12) -> datetime:
    return datetime.combine(day, time(hour), TASHKENT)


async def test_statistics(client, session, content):
    today = local_today()
    start = today - timedelta(days=8)
    returning = User(
        telegram_id=9001,
        nickname="Back_Again",
        created_at=at(start),
        onboarding_step=OnboardingStep.DONE,
    )
    gone = User(
        telegram_id=9002,
        nickname="Gone_Away",
        created_at=at(start),
        onboarding_step=OnboardingStep.DONE,
    )
    fresh = User(telegram_id=9003, created_at=at(today), source="teacher")
    session.add_all([returning, gone, fresh])
    await session.flush()
    opens = [
        (returning, start),
        (returning, start + timedelta(days=1)),
        (returning, start + timedelta(days=7)),
        (gone, start),
        (fresh, today),
    ]
    session.add_all(
        AnalyticsEvent(user_id=u.id, name="app_open", props={}, created_at=at(d)) for u, d in opens
    )
    session.add_all(
        [
            ActivityLog(
                user_id=returning.id,
                action="project_done",
                object_id="1",
                points=15,
                local_date=start,
                created_at=at(start),
            ),
            ActivityLog(
                user_id=returning.id,
                action="daily_task",
                object_id="1",
                points=20,
                local_date=start,
                created_at=at(start),
            ),
        ]
    )
    question = await session.scalar(select(Question).order_by(Question.id))
    session.add_all(
        AnalyticsEvent(
            user_id=gone.id,
            name="quiz_answer",
            props={"round": f"r{i}", "question_id": question.id, "correct": i < 2},
            created_at=at(start),
        )
        for i in range(10)
    )
    await session.commit()

    admin = await admin_client(client, session)
    stats = (await admin.get("/api/admin/stats?days=30")).json()
    assert stats["users_total"] == 3 and stats["users_onboarded"] == 2
    assert stats["new_users"] == 3
    assert stats["d1"] == {"size": 2, "value": 1, "rate": 0.5}
    assert stats["d7"] == {"size": 2, "value": 1, "rate": 0.5}
    assert stats["dau_today"] == 1 and stats["mau"] == 3
    assert stats["funnel"]["started"] == 3 and stats["funnel"]["done"] == 2
    assert stats["lesson_and_task"]["value"] == 1
    criteria = {c["key"]: c for c in stats["criteria"]}
    assert criteria["onboarding"]["ok"] is False  # 67% < 80%
    assert criteria["d1"]["ok"] is True
    assert {"source": "teacher", "users": 1} in stats["sources"]
    assert stats["daily"][-1]["day"] == today.isoformat()

    questions = (await admin.get("/api/admin/stats/questions")).json()
    hard = next(q for q in questions if q["id"] == question.id)
    assert (hard["answers"], hard["correct"], hard["rate"], hard["flag"]) == (10, 2, 0.2, "hard")


async def test_csv_export(client, session, content):
    session.add(User(telegram_id=9100, nickname="Csv_User", source="=cmd|' /C calc'!A0"))
    await session.commit()
    admin = await admin_client(client, session)
    r = await admin.get("/api/admin/stats/export/users")
    assert r.headers["content-type"].startswith("text/csv")
    assert "eco-master-users-" in r.headers["content-disposition"]
    text = r.content.decode("utf-8")
    assert text.startswith("﻿")
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    assert "telegram_id" not in rows[0]
    assert "9100" not in text  # no Telegram ids anywhere
    assert rows[1][4].startswith("'=")  # formulas are kept as text

    for kind in ("daily", "questions", "projects"):
        assert (await admin.get(f"/api/admin/stats/export/{kind}")).status_code == 200
