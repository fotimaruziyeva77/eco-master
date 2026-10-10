"""Helpers for admin API tests."""

import time

from sqlalchemy import select

from app.admin.security import TOTP_PERIOD, hash_password, hotp
from app.models import AdminRole, AdminUser

PASSWORD = "correct-horse-battery"


async def make_admin(
    session, login: str = "boss", role: AdminRole = AdminRole.ADMIN, name: str = "Boss"
) -> AdminUser:
    admin = AdminUser(login=login, name=name, role=role, password_hash=hash_password(PASSWORD))
    session.add(admin)
    await session.commit()
    return admin


def fresh_code(secret: str, last_step: int | None) -> str:
    """A code the server accepts now: the current step, or the next one if that was used."""
    step = int(time.time() // TOTP_PERIOD)
    if last_step is not None and step <= last_step:
        step = last_step + 1
    return hotp(secret, step)


async def sign_in(client, session, login: str = "boss", password: str = PASSWORD) -> dict:
    """Password + authenticator code; the session cookie stays in the client."""
    r = await client.post("/api/admin/auth/login", json={"login": login, "password": password})
    assert r.status_code == 200, r.text
    body = r.json()
    admin = await session.scalar(
        select(AdminUser).where(AdminUser.login == login).execution_options(populate_existing=True)
    )
    secret = body["setup"]["secret"] if body["setup"] else admin.totp_secret
    r = await client.post(
        "/api/admin/auth/code",
        json={"token": body["token"], "code": fresh_code(secret, admin.totp_last_step)},
    )
    assert r.status_code == 200, r.text
    return r.json()


async def admin_client(client, session, role: AdminRole = AdminRole.ADMIN, login: str = "boss"):
    await make_admin(session, login=login, role=role)
    await sign_in(client, session, login=login)
    return client
