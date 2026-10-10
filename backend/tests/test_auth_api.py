from sqlalchemy import select

from app.bot.handlers import upsert_bot_user
from app.models import User
from tests.conftest import login, make_init_data


async def test_health(client):
    response = await client.get("/api/health")
    assert response.json() == {"status": "ok"}


async def test_login_creates_user_with_telegram_language(client, session):
    body = await login(client, telegram_id=500, language_code="ru")
    assert body["token"]
    assert body["user"]["language"] == "ru"
    assert body["user"]["onboarding_step"] == "language"
    assert body["user"]["nickname"] is None

    user = await session.scalar(select(User).where(User.telegram_id == 500))
    assert user is not None


async def test_unknown_telegram_language_defaults_to_uzbek(client):
    body = await login(client, language_code="kk")
    assert body["user"]["language"] == "uz"


async def test_second_login_returns_same_user_and_keeps_chosen_language(client):
    first = await login(client, telegram_id=501, language_code="ru")
    headers = {"Authorization": f"Bearer {first['token']}"}
    await client.patch("/api/me", json={"language": "en"}, headers=headers)

    second = await login(client, telegram_id=501, language_code="ru")
    assert second["user"]["id"] == first["user"]["id"]
    assert second["user"]["language"] == "en"


async def test_start_param_is_saved_only_on_first_visit(client, session):
    await login(client, telegram_id=502, start_param="school_12")
    await login(client, telegram_id=502, start_param="other")
    user = await session.scalar(select(User).where(User.telegram_id == 502))
    assert user.source == "school_12"


async def test_forged_init_data_is_rejected(client):
    # QM-05: a request without valid initData gets 401.
    forged = make_init_data(token="999:not-our-bot")
    response = await client.post("/api/auth/telegram", json={"init_data": forged})
    assert response.status_code == 401

    response = await client.post(
        "/api/auth/telegram", json={"init_data": "user=%7B%22id%22%3A1%7D"}
    )
    assert response.status_code == 401


async def test_me_requires_a_valid_token(client):
    assert (await client.get("/api/me")).status_code == 401
    bad = {"Authorization": "Bearer not-a-token"}
    assert (await client.get("/api/me", headers=bad)).status_code == 401


async def test_me_returns_and_updates_profile(client):
    body = await login(client, language_code="uz")
    headers = {"Authorization": f"Bearer {body['token']}"}

    me = await client.get("/api/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["language"] == "uz"

    updated = await client.patch("/api/me", json={"language": "ru"}, headers=headers)
    assert updated.json()["language"] == "ru"

    invalid = await client.patch("/api/me", json={"language": "de"}, headers=headers)
    assert invalid.status_code == 422


async def test_blocked_user_is_refused(client, session):
    body = await login(client, telegram_id=503)
    user = await session.scalar(select(User).where(User.telegram_id == 503))
    user.is_blocked = True
    await session.commit()

    headers = {"Authorization": f"Bearer {body['token']}"}
    assert (await client.get("/api/me", headers=headers)).status_code == 403
    again = await client.post(
        "/api/auth/telegram", json={"init_data": make_init_data(telegram_id=503)}
    )
    assert again.status_code == 403


async def test_dev_login_helper_is_not_mounted_outside_dev(client):
    assert (await client.get("/api/dev/init-data")).status_code == 404


async def test_bot_start_creates_user_and_grants_write_access(session):
    user = await upsert_bot_user(session, 600, "en", "teacher")
    assert user.language == "en"
    assert user.write_access is True
    assert user.source == "teacher"


async def test_bot_start_keeps_existing_language(client, session):
    body = await login(client, telegram_id=601, language_code="ru")
    headers = {"Authorization": f"Bearer {body['token']}"}
    await client.patch("/api/me", json={"language": "uz"}, headers=headers)

    user = await upsert_bot_user(session, 601, "ru", None)
    assert user.language == "uz"
    assert user.write_access is True
