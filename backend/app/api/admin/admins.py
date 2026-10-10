"""Admin accounts (admin role only)."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.admin.audit import audit
from app.admin.deps import AdminOnly
from app.admin.schemas import AdminCreateIn, AdminOut, AdminUpdateIn, PasswordSetIn
from app.admin.security import hash_password, password_problem
from app.deps import SessionDep
from app.models import AdminUser

router = APIRouter(prefix="/admins", tags=["admin"])


def admin_out(admin: AdminUser) -> AdminOut:
    return AdminOut(
        id=admin.id,
        login=admin.login,
        name=admin.name,
        role=admin.role,
        is_active=admin.is_active,
        totp_enabled=admin.totp_confirmed_at is not None,
        locked=admin.locked_until is not None and admin.locked_until > datetime.now(UTC),
        last_login_at=admin.last_login_at,
        created_at=admin.created_at,
    )


async def get_admin(session, admin_id: int) -> AdminUser:
    target = await session.get(AdminUser, admin_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "admin_not_found")
    return target


def check_password(password: str) -> None:
    if problem := password_problem(password):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, problem)


@router.get("")
async def list_admins(admin: AdminOnly, session: SessionDep) -> list[AdminOut]:
    rows = await session.scalars(select(AdminUser).order_by(AdminUser.id))
    return [admin_out(a) for a in rows.all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_admin(body: AdminCreateIn, admin: AdminOnly, session: SessionDep) -> AdminOut:
    """The new person signs in with this password and then connects an authenticator app."""
    check_password(body.password)
    new = AdminUser(
        login=body.login,
        name=body.name.strip(),
        role=body.role,
        password_hash=hash_password(body.password),
    )
    session.add(new)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "login_taken") from exc
    audit(session, admin, "admin.create", "admin", new.id, login=new.login, role=new.role.value)
    await session.commit()
    await session.refresh(new)
    return admin_out(new)


@router.patch("/{admin_id}")
async def update_admin(
    admin_id: int, body: AdminUpdateIn, admin: AdminOnly, session: SessionDep
) -> AdminOut:
    target = await get_admin(session, admin_id)
    changes = body.model_dump(exclude_none=True)
    if target.id == admin.id and ("role" in changes or changes.get("is_active") is False):
        # Nobody can lock themselves (or the last admin) out by accident.
        raise HTTPException(status.HTTP_409_CONFLICT, "cannot_change_self")
    if "name" in changes:
        target.name = changes["name"].strip()
    if "role" in changes and changes["role"] != target.role:
        target.role = changes["role"]
        target.session_version += 1
    if "is_active" in changes and changes["is_active"] != target.is_active:
        target.is_active = changes["is_active"]
        target.session_version += 1
    audit(
        session,
        admin,
        "admin.update",
        "admin",
        target.id,
        **{k: getattr(v, "value", v) for k, v in changes.items()},
    )
    await session.commit()
    return admin_out(target)


@router.post("/{admin_id}/reset-2fa")
async def reset_2fa(admin_id: int, admin: AdminOnly, session: SessionDep) -> AdminOut:
    """For a lost phone: the next sign-in sets up a new authenticator app."""
    target = await get_admin(session, admin_id)
    target.totp_secret = None
    target.totp_confirmed_at = None
    target.totp_last_step = None
    target.session_version += 1
    audit(session, admin, "admin.reset_2fa", "admin", target.id)
    await session.commit()
    return admin_out(target)


@router.post("/{admin_id}/password")
async def set_password(
    admin_id: int, body: PasswordSetIn, admin: AdminOnly, session: SessionDep
) -> AdminOut:
    """A temporary password for someone who forgot theirs; it also lifts a lockout."""
    check_password(body.password)
    target = await get_admin(session, admin_id)
    target.password_hash = hash_password(body.password)
    target.failed_logins = 0
    target.locked_until = None
    target.session_version += 1
    audit(session, admin, "admin.set_password", "admin", target.id)
    await session.commit()
    return admin_out(target)
