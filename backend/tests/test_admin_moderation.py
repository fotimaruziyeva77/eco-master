import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import (
    ActivityLog,
    AnalyticsEvent,
    Badge,
    OnboardingStep,
    User,
    UserBadge,
)
from app.seed import seed_badges, seed_banned_words, seed_categories, seed_demo
from app.timeutil import local_today
from tests.admin_helpers import admin_client
from tests.test_phase4_api import onboard


@pytest.fixture
async def admin(client, session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_banned_words(session)
    await seed_demo(session)
    await session.commit()
    return await admin_client(client, session)


async def leaderboard_ids(client, headers, period="week") -> list[int]:
    board = (await client.get(f"/api/leaderboard?period={period}", headers=headers)).json()
    return [e["user_id"] for e in board["entries"]]


async def earn(client, headers) -> None:
    """15 points for a project, and the first-step badge."""
    await client.post(
        "/api/projects/dry-leaves-compost/done",
        json={"client_event_id": str(uuid.uuid4())},
        headers=headers,
    )


async def test_search_and_card(admin, client):
    headers, user_id = await onboard(client, 5551, "Green_Fox")
    await earn(client, headers)
    by_name = (await admin.get("/api/admin/users?q=green")).json()
    assert [u["id"] for u in by_name] == [user_id]
    by_telegram = (await admin.get("/api/admin/users?q=5551")).json()
    assert [u["nickname"] for u in by_telegram] == ["Green_Fox"]
    huge = await admin.get("/api/admin/users?q=" + "9" * 30)
    assert huge.status_code == 200 and huge.json() == []

    card = (await admin.get(f"/api/admin/users/{user_id}")).json()
    assert card["telegram_id"] == 5551
    assert card["points_total"] == 15
    # The only organic project: done, so the organic master badge comes too.
    assert [b["code"] for b in card["badges"]] == ["first_step", "master_organic"]
    assert card["activity"][0]["action"] == "project_done"


async def test_blocked_user_leaves_the_rating_at_once(admin, client):
    # QM-13: hidden or blocked users disappear from the leaderboard (here: immediately).
    headers, user_id = await onboard(client, 5552, "Fast_One")
    other_headers, _ = await onboard(client, 5553, "Watcher")
    await earn(client, headers)
    assert user_id in await leaderboard_ids(client, other_headers)

    r = await admin.post(f"/api/admin/users/{user_id}/block", json={"blocked": True})
    assert r.json()["is_blocked"] is True
    assert user_id not in await leaderboard_ids(client, other_headers)
    assert (await client.get("/api/me", headers=headers)).status_code == 403

    await admin.post(f"/api/admin/users/{user_id}/block", json={"blocked": False})
    assert user_id in await leaderboard_ids(client, other_headers)


async def test_hide_and_force_nickname_change(admin, client, session):
    headers, user_id = await onboard(client, 5554, "Rude_Name")
    other_headers, _ = await onboard(client, 5555, "Kind_Name")
    await earn(client, headers)

    await admin.post(f"/api/admin/users/{user_id}/nickname", json={"action": "hide"})
    assert user_id not in await leaderboard_ids(client, other_headers)

    reset = (
        await admin.post(
            f"/api/admin/users/{user_id}/nickname", json={"action": "reset", "reason": "odobsiz"}
        )
    ).json()
    assert reset["nickname"] is None and reset["nickname_hidden"] is False
    me = (await client.get("/api/me", headers=headers)).json()
    assert me["onboarding_step"] == "nickname"

    # The user picks a new nickname and is back; the old one is free again.
    await client.post("/api/onboarding/nickname", json={"nickname": "Nice_Name"}, headers=headers)
    await client.post("/api/onboarding/complete", headers=headers)
    assert user_id in await leaderboard_ids(client, other_headers)
    check = await client.get(
        "/api/onboarding/nickname-check?value=Rude_Name", headers=other_headers
    )
    assert check.json()["ok"] is True


async def test_void_fake_points(admin, client, session):
    headers, user_id = await onboard(client, 5556, "Cheater")
    other_headers, _ = await onboard(client, 5557, "Honest")
    await earn(client, headers)
    await client.post(
        "/api/daily/done", json={"client_event_id": str(uuid.uuid4())}, headers=headers
    )
    card = (await admin.get(f"/api/admin/users/{user_id}")).json()
    assert card["points_total"] == 35 and card["streak_current"] == 1
    ids = [a["id"] for a in card["activity"]]

    voided = (
        await admin.post(
            f"/api/admin/users/{user_id}/void", json={"entry_ids": ids, "reason": "bot orqali"}
        )
    ).json()
    assert voided["points_total"] == 0
    assert voided["streak_current"] == 0 and voided["last_task_date"] is None
    assert voided["badges"] == []  # first step relied on these points
    assert {a["action"] for a in voided["activity"]} == {"voided"}
    assert voided["activity"][0]["voided"]["reason"] == "bot orqali"
    assert user_id not in await leaderboard_ids(client, other_headers)

    again = await admin.post(
        f"/api/admin/users/{user_id}/void", json={"entry_ids": ids, "reason": "takror"}
    )
    assert again.status_code == 409

    # The daily task can be done again honestly today; the cache follows the log.
    redo = await client.post(
        "/api/daily/done", json={"client_event_id": str(uuid.uuid4())}, headers=headers
    )
    assert redo.json()["points_total"] == 20


async def test_void_keeps_unrelated_badges(admin, client, session):
    headers, user_id = await onboard(client, 5558, "Mixed")
    await earn(client, headers)
    await client.post(
        "/api/daily/done", json={"client_event_id": str(uuid.uuid4())}, headers=headers
    )
    daily_row = await session.scalar(
        select(ActivityLog.id).where(
            ActivityLog.user_id == user_id, ActivityLog.action == "daily_task"
        )
    )
    result = (
        await admin.post(
            f"/api/admin/users/{user_id}/void", json={"entry_ids": [daily_row], "reason": "test"}
        )
    ).json()
    assert result["points_total"] == 15
    assert [b["code"] for b in result["badges"]] == ["first_step", "master_organic"]  # kept


async def test_reports_queue(admin, client, session):
    _, target = await onboard(client, 5560, "Bad_Name")
    for telegram_id, nickname in ((5561, "Reporter_A"), (5562, "Reporter_B")):
        headers, _ = await onboard(client, telegram_id, nickname)
        await client.post("/api/reports", json={"target_user_id": target}, headers=headers)

    queue = (await admin.get("/api/admin/reports/open")).json()
    assert len(queue) == 1
    assert queue[0]["target"]["id"] == target and queue[0]["count"] == 2
    flagged = (await admin.get("/api/admin/users?filter=reported")).json()
    assert [u["id"] for u in flagged] == [target]

    r = await admin.post(
        "/api/admin/reports/resolve", json={"target_user_id": target, "action": "hide"}
    )
    assert r.json() == {"resolved": 2}
    assert (await admin.get("/api/admin/reports/open")).json() == []
    history = (await admin.get("/api/admin/reports")).json()
    assert {h["status"] for h in history} == {"resolved"}
    assert history[0]["resolved_by"] == "Boss"
    assert (await session.get(User, target, populate_existing=True)).nickname_hidden is True


async def test_word_lists_apply_to_new_nicknames(admin, client):
    headers, _ = await onboard(client, 5563, "Someone")
    check = await client.get("/api/onboarding/nickname-check?value=ekoboy", headers=headers)
    assert check.json()["ok"] is True

    added = await admin.post("/api/admin/words", json={"word": " EKO ", "kind": "reserved"})
    assert added.json()["word"] == "eko"
    assert (
        await admin.post("/api/admin/words", json={"word": "eko", "kind": "reserved"})
    ).status_code == 409
    check = await client.get("/api/onboarding/nickname-check?value=ekoboy", headers=headers)
    assert check.json()["error"] == "nickname_forbidden"

    await admin.delete(f"/api/admin/words/{added.json()['id']}")
    check = await client.get("/api/onboarding/nickname-check?value=ekoboy", headers=headers)
    assert check.json()["ok"] is True


async def test_suspicious_activity(admin, client, session):
    _, user_id = await onboard(client, 5564, "Too_Fast")
    today = local_today()
    session.add(ActivityLog(user_id=user_id, action="test", points=350, local_date=today))
    start = datetime.now(UTC) - timedelta(minutes=5)
    session.add_all(
        AnalyticsEvent(
            user_id=user_id,
            name="quiz_answer",
            props={"round": "r1", "question_id": i, "correct": True},
            created_at=start + timedelta(milliseconds=300 * i),
        )
        for i in range(10)
    )
    await session.commit()

    flags = (await admin.get("/api/admin/stats/flags")).json()
    assert flags["points"][0]["user_id"] == user_id and flags["points"][0]["points"] == 350
    assert flags["fast"][0]["game"] == "quiz" and flags["fast"][0]["avg_seconds"] < 1
    card = (await admin.get(f"/api/admin/users/{user_id}")).json()
    assert {f["kind"] for f in card["flags"]} == {"points", "fast"}
    listed = (await admin.get("/api/admin/users?filter=flagged")).json()
    assert [u["id"] for u in listed] == [user_id]


async def test_audit_log_pages(admin, client):
    _, user_id = await onboard(client, 5565, "Audited")
    await admin.post(f"/api/admin/users/{user_id}/block", json={"blocked": True, "reason": "spam"})
    await admin.post(f"/api/admin/users/{user_id}/block", json={"blocked": False})
    page = (await admin.get("/api/admin/audit?limit=2")).json()
    assert [r["action"] for r in page["rows"]] == ["user.unblock", "user.block"]
    assert page["rows"][1]["details"] == {"reason": "spam"}
    assert page["rows"][0]["admin_name"] == "Boss"
    older = (await admin.get(f"/api/admin/audit?before_id={page['next_before_id']}")).json()
    assert [r["action"] for r in older["rows"]] == ["auth.login"]
    assert older["next_before_id"] is None


async def test_badges_table_has_codes(session):
    # Sanity check for the badge codes used by moderation.
    await seed_badges(session)
    await session.commit()
    codes = set((await session.scalars(select(Badge.code))).all())
    assert {"first_step", "streak_7", "quiz_champion", "sorting_master"} <= codes
    assert not (await session.scalars(select(UserBadge))).all()
    assert OnboardingStep.NICKNAME.value == "nickname"
