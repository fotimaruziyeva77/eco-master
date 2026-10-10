"""Who is calling the admin API, and may they?"""

from typing import Annotated
from urllib.parse import urlsplit

import jwt
from fastapi import Depends, HTTPException, Request, status

from app.admin.security import SESSION_COOKIE, SESSION_TOKEN, read_token
from app.deps import SessionDep, SettingsDep
from app.models import AdminRole, AdminUser

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


async def same_origin_only(request: Request, settings: SettingsDep) -> None:
    """Refuse state-changing requests sent from other sites (CSRF).

    The session cookie is SameSite=Strict as well; this is the second lock. Requests without
    an Origin header come from non-browser clients, which never carry the cookie by accident.
    """
    if request.method in SAFE_METHODS:
        return
    origin = request.headers.get("origin")
    if origin is None:
        return
    allowed = {_origin(o) for o in settings.cors_origin_list}
    allowed.add(_origin(settings.webapp_url))
    allowed.add(_origin(str(request.base_url)))
    if origin not in allowed:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "bad_origin")


async def get_current_admin(
    request: Request, session: SessionDep, settings: SettingsDep
) -> AdminUser:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not_authenticated")
    try:
        admin_id, version = read_token(settings.jwt_secret, token, SESSION_TOKEN)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_session") from exc
    admin = await session.get(AdminUser, admin_id)
    if (
        admin is None
        or not admin.is_active
        or admin.session_version != version
        or admin.totp_confirmed_at is None
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_session")
    return admin


CurrentAdmin = Annotated[AdminUser, Depends(get_current_admin)]


def require_admin_role(admin: CurrentAdmin) -> AdminUser:
    """Content editors manage content only (TZ 8.12); everything else needs the admin role."""
    if admin.role != AdminRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin_only")
    return admin


def require_content_role(admin: CurrentAdmin) -> AdminUser:
    """Content and market moderation: administrators and content editors."""
    if admin.role not in (AdminRole.ADMIN, AdminRole.EDITOR):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin_only")
    return admin


def require_handover_role(admin: CurrentAdmin) -> AdminUser:
    """The handover desk: administrators, and the staff of a handover point."""
    if admin.role == AdminRole.ADMIN:
        return admin
    if admin.role == AdminRole.POINT and admin.pickup_point_id is not None:
        return admin
    raise HTTPException(status.HTTP_403_FORBIDDEN, "admin_only")


AdminOnly = Annotated[AdminUser, Depends(require_admin_role)]
ContentStaff = Annotated[AdminUser, Depends(require_content_role)]
HandoverStaff = Annotated[AdminUser, Depends(require_handover_role)]
