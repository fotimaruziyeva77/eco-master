import pytest

from app.seed import seed_banned_words
from tests.conftest import login


@pytest.fixture
async def headers(client, session):
    await seed_banned_words(session)
    await session.commit()
    body = await login(client, telegram_id=700, language_code="ru")
    return {"Authorization": f"Bearer {body['token']}"}


async def test_full_onboarding_flow(client, headers):
    r = await client.post("/api/onboarding/language", json={"language": "uz"}, headers=headers)
    assert r.json()["language"] == "uz"
    assert r.json()["onboarding_step"] == "path"

    r = await client.post("/api/onboarding/path", json={"path": "student"}, headers=headers)
    assert r.json()["onboarding_step"] == "nickname"

    r = await client.post("/api/onboarding/nickname", json={"nickname": "EcoHero"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["nickname"] == "EcoHero"
    assert r.json()["onboarding_step"] == "intro"

    r = await client.post("/api/onboarding/complete", headers=headers)
    assert r.json()["onboarding_step"] == "done"

    # Onboarding is shown once: the saved step survives the next login (QM-01).
    again = await login(client, telegram_id=700)
    assert again["user"]["onboarding_step"] == "done"


async def test_progress_is_resumed_and_never_goes_back(client, headers):
    await client.post("/api/onboarding/language", json={"language": "en"}, headers=headers)
    await client.post("/api/onboarding/path", json={"path": "teacher"}, headers=headers)

    resumed = await login(client, telegram_id=700)
    assert resumed["user"]["onboarding_step"] == "nickname"

    # Returning to the language screen does not reset progress.
    r = await client.post("/api/onboarding/language", json={"language": "ru"}, headers=headers)
    assert r.json()["onboarding_step"] == "nickname"


async def test_complete_requires_path_and_nickname(client, headers):
    r = await client.post("/api/onboarding/complete", headers=headers)
    assert r.status_code == 409
    assert r.json()["detail"] == "onboarding_incomplete"


@pytest.mark.parametrize(
    ("nickname", "status", "code"),
    [
        ("ab", 422, "nickname_length"),
        ("eco boy", 422, "nickname_chars"),
        ("admin_1", 422, "nickname_forbidden"),
        ("f_u_c_k", 422, "nickname_forbidden"),
    ],
)
async def test_bad_nicknames_are_rejected(client, headers, nickname, status, code):
    # QM-03: forbidden or malformed nicknames are refused with a code the UI translates.
    r = await client.post("/api/onboarding/nickname", json={"nickname": nickname}, headers=headers)
    assert r.status_code == status
    assert r.json()["detail"] == code


async def test_nickname_is_unique_ignoring_case(client, headers):
    other = await login(client, telegram_id=701)
    other_headers = {"Authorization": f"Bearer {other['token']}"}
    await client.post(
        "/api/onboarding/nickname", json={"nickname": "GreenCat"}, headers=other_headers
    )

    r = await client.post(
        "/api/onboarding/nickname", json={"nickname": "greencat"}, headers=headers
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "nickname_taken"

    check = await client.get(
        "/api/onboarding/nickname-check", params={"value": "GREENCAT"}, headers=headers
    )
    assert check.json() == {"ok": False, "error": "nickname_taken"}


async def test_user_can_keep_own_nickname(client, headers):
    await client.post("/api/onboarding/nickname", json={"nickname": "Tree"}, headers=headers)
    check = await client.get(
        "/api/onboarding/nickname-check", params={"value": "tree"}, headers=headers
    )
    assert check.json()["ok"] is True


async def test_nickname_cannot_change_via_onboarding_after_finish(client, headers):
    await client.post("/api/onboarding/path", json={"path": "general"}, headers=headers)
    await client.post("/api/onboarding/nickname", json={"nickname": "Leaf"}, headers=headers)
    await client.post("/api/onboarding/complete", headers=headers)
    r = await client.post("/api/onboarding/nickname", json={"nickname": "Leaf2"}, headers=headers)
    assert r.status_code == 409


async def test_write_access(client, headers):
    r = await client.post("/api/me/write-access", json={"granted": True}, headers=headers)
    assert r.json()["write_access"] is True
    r = await client.post("/api/me/write-access", json={"granted": False}, headers=headers)
    assert r.json()["write_access"] is True
