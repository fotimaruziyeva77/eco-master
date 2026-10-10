"""Admin sign-in: password, then the authenticator code; the session lives in a cookie."""

from datetime import UTC, datetime

import jwt
from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit import audit
from app.admin.deps import CurrentAdmin
from app.admin.schemas import AdminMeOut, CodeIn, LoginIn, LoginOut, PasswordChangeIn, TotpSetupOut
from app.admin.security import (
    CODE_STEP_TTL,
    CODE_TOKEN,
    LOCKOUT,
    MAX_FAILED_LOGINS,
    SESSION_COOKIE,
    SESSION_TOKEN,
    SESSION_TTL,
    create_token,
    hash_password,
    new_totp_secret,
    password_problem,
    provisioning_uri,
    read_token,
    verify_password,
    verify_totp,
)
from app.config import Settings
from app.deps import SessionDep, SettingsDep
from app.models import AdminUser
from app.ratelimit import RateLimiter

router = APIRouter(prefix="/auth", tags=["admin"])

COOKIE_PATH = "/api/admin"
# Per client address, on top of the per-account lockout.
attempt_limit = RateLimiter(limit=20, window=600)


def check_rate(request: Request) -> None:
    if not attempt_limit.allow(request.client.host if request.client else "unknown"):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_attempts")


def is_locked(admin: AdminUser) -> bool:
    return admin.locked_until is not None and admin.locked_until > datetime.now(UTC)


async def record_failure(session: AsyncSession, admin: AdminUser) -> None:
    """Five wrong passwords or codes in a row lock the account for 15 minutes."""
    admin.failed_logins += 1
    if admin.failed_logins >= MAX_FAILED_LOGINS:
        admin.failed_logins = 0
        admin.locked_until = datetime.now(UTC) + LOCKOUT
        audit(session, admin, "auth.locked", "admin", admin.id)
    await session.commit()


def set_session(response: Response, admin: AdminUser, settings: Settings) -> None:
    token = create_token(
        settings.jwt_secret, admin.id, SESSION_TOKEN, admin.session_version, SESSION_TTL
    )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(SESSION_TTL.total_seconds()),
        path=COOKIE_PATH,
        httponly=True,  # never readable by page scripts
        secure=settings.is_prod,
        samesite="strict",
    )


@router.post("/login")
async def login(
    body: LoginIn, request: Request, session: SessionDep, settings: SettingsDep
) -> LoginOut:
    check_rate(request)
    admin = await session.scalar(
        select(AdminUser).where(AdminUser.login == body.login.strip().lower())
    )
    if admin is not None and is_locked(admin):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_attempts")
    if not verify_password(admin.password_hash if admin else None, body.password):
        if admin is not None and admin.is_active:
            await record_failure(session, admin)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_credentials")
    if not admin.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_credentials")

    setup = None
    if admin.totp_confirmed_at is None:
        # First sign-in: a new secret for the authenticator app, confirmed by the first code.
        admin.totp_secret = new_totp_secret()
        admin.totp_last_step = None
        setup = TotpSetupOut(
            secret=admin.totp_secret, uri=provisioning_uri(admin.totp_secret, admin.login)
        )
    await session.commit()
    token = create_token(
        settings.jwt_secret, admin.id, CODE_TOKEN, admin.session_version, CODE_STEP_TTL
    )
    return LoginOut(token=token, setup=setup)


@router.post("/code")
async def confirm_code(
    body: CodeIn,
    request: Request,
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
) -> AdminMeOut:
    check_rate(request)
    try:
        admin_id, version = read_token(settings.jwt_secret, body.token, CODE_TOKEN)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "code_expired") from exc
    admin = await session.get(AdminUser, admin_id)
    if (
        admin is None
        or not admin.is_active
        or admin.session_version != version
        or not admin.totp_secret
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "code_expired")
    if is_locked(admin):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_attempts")

    step = verify_totp(admin.totp_secret, body.code, admin.totp_last_step)
    if step is None:
        await record_failure(session, admin)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_code")

    now = datetime.now(UTC)
    first_setup = admin.totp_confirmed_at is None
    admin.totp_last_step = step
    admin.totp_confirmed_at = admin.totp_confirmed_at or now
    admin.failed_logins = 0
    admin.locked_until = None
    admin.last_login_at = now
    audit(
        session,
        admin,
        "auth.login",
        "admin",
        admin.id,
        **({"2fa_setup": True} if first_setup else {}),
    )
    await session.commit()
    set_session(response, admin, settings)
    return AdminMeOut.model_validate(admin)


@router.get("/me")
async def me(admin: CurrentAdmin) -> AdminMeOut:
    return AdminMeOut.model_validate(admin)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> Response:
    response.status_code = status.HTTP_204_NO_CONTENT
    response.delete_cookie(SESSION_COOKIE, path=COOKIE_PATH)
    return response


@router.post("/password")
async def change_password(
    body: PasswordChangeIn,
    response: Response,
    admin: CurrentAdmin,
    session: SessionDep,
    settings: SettingsDep,
) -> AdminMeOut:
    if not verify_password(admin.password_hash, body.current):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "wrong_password")
    if problem := password_problem(body.new):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, problem)
    admin.password_hash = hash_password(body.new)
    # Other browsers are signed out; this one gets a fresh session.
    admin.session_version += 1
    audit(session, admin, "auth.password_changed", "admin", admin.id)
    await session.commit()
    set_session(response, admin, settings)
    return AdminMeOut.model_validate(admin)
