"""Audit log of admin actions: who, what, when (TZ 8.12)."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdminAuditLog, AdminUser


def audit(
    session: AsyncSession,
    admin: AdminUser | None,
    action: str,
    object_type: str,
    object_id: object = None,
    **details: Any,
) -> None:
    """Queue an audit row; it is written with the action's own commit."""
    session.add(
        AdminAuditLog(
            admin_id=admin.id if admin else None,
            action=action,
            object_type=object_type,
            object_id=None if object_id is None else str(object_id),
            details=details or None,
        )
    )
