"""Audit log: who did what and when (TZ 8.12)."""

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.admin.deps import AdminOnly
from app.admin.schemas import AuditPageOut, AuditRowOut
from app.deps import SessionDep
from app.models import AdminAuditLog, AdminUser

router = APIRouter(prefix="/audit", tags=["admin"])


@router.get("")
async def audit_log(
    admin: AdminOnly,
    session: SessionDep,
    before_id: Annotated[int | None, Query()] = None,
    admin_id: Annotated[int | None, Query()] = None,
    object_type: Annotated[str | None, Query(max_length=64)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AuditPageOut:
    """Newest first; pass `before_id` from the previous page to read further back."""
    query = (
        select(AdminAuditLog, AdminUser.name)
        .outerjoin(AdminUser, AdminUser.id == AdminAuditLog.admin_id)
        .order_by(AdminAuditLog.id.desc())
        .limit(limit + 1)
    )
    if before_id is not None:
        query = query.where(AdminAuditLog.id < before_id)
    if admin_id is not None:
        query = query.where(AdminAuditLog.admin_id == admin_id)
    if object_type:
        query = query.where(AdminAuditLog.object_type == object_type)
    rows = (await session.execute(query)).all()
    page = rows[:limit]
    return AuditPageOut(
        rows=[
            AuditRowOut(
                id=row.id,
                created_at=row.created_at,
                admin_id=row.admin_id,
                admin_name=name,
                action=row.action,
                object_type=row.object_type,
                object_id=row.object_id,
                details=row.details,
            )
            for row, name in page
        ],
        next_before_id=page[-1][0].id if len(rows) > limit else None,
    )
