import time

from sqlalchemy import select

from app.admin.security import (
    TOTP_PERIOD,
    hotp,
    provisioning_uri,
    verify_password,
    verify_totp,
)
from app.models import AdminAuditLog, AdminRole, AdminUser
from tests.admin_helpers import PASSWORD, admin_client, fresh_code, make_admin, sign_in

# ------------------------------------------------------------------- TOTP unit


def test_totp_matches_rfc_6238_vectors():
    # RFC 6238 appendix B, SHA-1 secret "12345678901234567890" (base32 below), 8 digits there;
    # the last 6 digits are what a 6-digit authenticator shows.
    secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
    assert hotp(secret, 59 // 30) == "287082"
    assert hotp(secret, 1111111109 // 30) == "081804"
    assert hotp(secret, 1234567890 // 30) == "005924"
    assert hotp(secret, 2000000000 // 30) == "279037"


def test_totp_window_and_replay():
    secret = "JBSWY3DPEHPK3PXP"
    now = 1_800_000_000.0
    step = int(now // TOTP_PERIOD)
    assert verify_totp(secret, hotp(secret, step), None, at=now) == step
    assert verify_totp(secret, hotp(secret, step - 1), None, at=now) == step - 1  # clock drift
    assert verify_totp(secret, hotp(secret, step - 2), None, at=now) is None
    assert verify_totp(secret, hotp(secret, step), step, at=now) is None  # already used
    assert verify_totp(secret, "12345", None, at=now) is None
    assert "issuer=Ekoustoz" in provisioning_uri(secret, "ali")


def test_password_hashing():
    from app.admin.security import hash_password, password_problem

    hashed = hash_password(PASSWORD)
    assert hashed.startswith("$argon2id$")
    assert verify_password(hashed, PASSWORD)
    assert not verify_password(hashed, "wrong-password")
    assert not verify_password(None, PASSWORD)
    assert password_problem("short") == "password_too_short"
    assert password_problem("aaaaaaaaaaaa") == "password_too_simple"
    assert password_problem(PASSWORD) is None


# ---------------------------------------------------------------------- sign-in


async def test_first_sign_in_sets_up_the_authenticator(client, session):
    await make_admin(session)
    r = await client.post("/api/admin/auth/login", json={"login": "BOSS", "password": PASSWORD})
    body = r.json()
    assert body["setup"]["uri"].startswith("otpauth://totp/Ekoustoz:boss?secret=")
    secret = body["setup"]["secret"]

    wrong = await client.post(
        "/api/admin/auth/code", json={"token": body["token"], "code": "000000"}
    )
    assert wrong.status_code == 401
    assert (await client.get("/api/admin/auth/me")).status_code == 401

    code = hotp(secret, int(time.time() // TOTP_PERIOD))
    ok = await client.post("/api/admin/auth/code", json={"token": body["token"], "code": code})
    assert ok.status_code == 200
    cookie = ok.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie and "path=/api/admin" in cookie
    me = (await client.get("/api/admin/auth/me")).json()
    assert me["login"] == "boss" and me["role"] == "admin"

    # Later sign-ins no longer show a secret, and the used code can not be replayed.
    again = (
        await client.post("/api/admin/auth/login", json={"login": "boss", "password": PASSWORD})
    ).json()
    assert again["setup"] is None
    replay = await client.post("/api/admin/auth/code", json={"token": again["token"], "code": code})
    assert replay.status_code == 401


async def test_password_alone_is_not_enough(client, session):
    await make_admin(session)
    await client.post("/api/admin/auth/login", json={"login": "boss", "password": PASSWORD})
    assert (await client.get("/api/admin/stats")).status_code == 401


async def test_wrong_passwords_lock_the_account(client, session):
    await make_admin(session)
    for _ in range(5):
        r = await client.post(
            "/api/admin/auth/login", json={"login": "boss", "password": "nope-nope"}
        )
        assert r.status_code == 401
    locked = await client.post(
        "/api/admin/auth/login", json={"login": "boss", "password": PASSWORD}
    )
    assert locked.status_code == 429
    unknown = await client.post("/api/admin/auth/login", json={"login": "ghost", "password": "x"})
    assert unknown.json()["detail"] == "invalid_credentials"
    audit = await session.scalar(select(AdminAuditLog.action))
    assert audit == "auth.locked"


async def test_too_many_attempts_from_one_address(client, session):
    for _ in range(20):
        await client.post("/api/admin/auth/login", json={"login": "ghost", "password": "x"})
    r = await client.post("/api/admin/auth/login", json={"login": "ghost", "password": "x"})
    assert r.status_code == 429


async def test_logout_and_password_change_end_sessions(client, session):
    await admin_client(client, session)
    old_cookie = client.cookies.get("ekoustoz_admin")
    r = await client.post(
        "/api/admin/auth/password", json={"current": PASSWORD, "new": "another-long-secret"}
    )
    assert r.status_code == 200
    assert (await client.get("/api/admin/auth/me")).status_code == 200  # fresh cookie

    # The cookie from before the change no longer works.
    client.cookies.set("ekoustoz_admin", old_cookie, path="/api/admin")
    assert (await client.get("/api/admin/auth/me")).status_code == 401

    await sign_in(client, session, password="another-long-secret")
    await client.post("/api/admin/auth/logout")
    assert (await client.get("/api/admin/auth/me")).status_code == 401


async def test_editor_sees_content_only(client, session):
    await admin_client(client, session, role=AdminRole.EDITOR)
    assert (await client.get("/api/admin/content")).status_code == 200
    for path in ("/api/admin/users", "/api/admin/stats", "/api/admin/audit", "/api/admin/admins"):
        assert (await client.get(path)).status_code == 403, path


async def test_other_sites_can_not_post(client, session):
    await admin_client(client, session)
    r = await client.post(
        "/api/admin/words",
        json={"word": "badword", "kind": "profanity"},
        headers={"Origin": "https://evil.example"},
    )
    assert r.status_code == 403
    same = await client.post(
        "/api/admin/words",
        json={"word": "badword", "kind": "profanity"},
        headers={"Origin": "http://localhost:5180"},
    )
    assert same.status_code == 201


# ------------------------------------------------------------------- accounts


async def test_manage_admins(client, session):
    await admin_client(client, session)
    weak = await client.post(
        "/api/admin/admins",
        json={"login": "dilnoza", "name": "Dilnoza", "role": "editor", "password": "short"},
    )
    assert weak.status_code == 422
    created = await client.post(
        "/api/admin/admins",
        json={"login": "dilnoza", "name": "Dilnoza", "role": "editor", "password": PASSWORD},
    )
    assert created.status_code == 201
    editor = created.json()
    assert editor["totp_enabled"] is False
    duplicate = await client.post(
        "/api/admin/admins",
        json={"login": "dilnoza", "name": "D", "role": "editor", "password": PASSWORD},
    )
    assert duplicate.status_code == 409

    me = (await client.get("/api/admin/auth/me")).json()
    self_demote = await client.patch(f"/api/admin/admins/{me['id']}", json={"role": "editor"})
    assert self_demote.status_code == 409

    off = await client.patch(f"/api/admin/admins/{editor['id']}", json={"is_active": False})
    assert off.json()["is_active"] is False
    r = await client.post("/api/admin/auth/login", json={"login": "dilnoza", "password": PASSWORD})
    assert r.status_code == 401

    reset = await client.post(f"/api/admin/admins/{editor['id']}/reset-2fa")
    assert reset.json()["totp_enabled"] is False
    admins = (await client.get("/api/admin/admins")).json()
    assert [a["login"] for a in admins] == ["boss", "dilnoza"]


async def test_deactivated_admin_loses_session(client, session):
    await admin_client(client, session)
    admin = await session.scalar(select(AdminUser).where(AdminUser.login == "boss"))
    admin.is_active = False
    await session.commit()
    assert (await client.get("/api/admin/auth/me")).status_code == 401


async def test_fresh_code_helper_moves_past_used_step():
    secret = "JBSWY3DPEHPK3PXP"
    step = int(time.time() // TOTP_PERIOD)
    assert fresh_code(secret, step) == hotp(secret, step + 1)
