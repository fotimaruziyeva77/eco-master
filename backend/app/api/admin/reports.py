"""Queue of nickname complaints (TZ 8.7, 8.12)."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select, update

from app.admin.audit import audit
from app.admin.deps import AdminOnly
from app.admin.schemas import ReportGroupOut, ReportOut, ResolveIn
from app.api.admin.users import apply_block, apply_nickname, reports_out, row_out
from app.deps import SessionDep
from app.models import Report, ReportStatus, User

router = APIRouter(prefix="/reports", tags=["admin-users"])


@router.get("/open")
async def open_reports(admin: AdminOnly, session: SessionDep) -> list[ReportGroupOut]:
    """Open complaints grouped by the reported user, most reported first."""
    rows = await session.execute(
        select(
            User,
            func.count(Report.id),
            func.array_agg(func.distinct(Report.reason)),
            func.min(Report.created_at),
            func.max(Report.created_at),
        )
        .join(Report, Report.target_user_id == User.id)
        .where(Report.status == ReportStatus.OPEN)
        .group_by(User.id)
        .order_by(func.count(Report.id).desc(), func.min(Report.created_at))
    )
    return [
        ReportGroupOut(
            target=row_out(user, count),
            count=count,
            reasons=sorted(reasons),
            first_at=first,
            last_at=last,
        )
        for user, count, reasons, first, last in rows.all()
    ]


@router.get("")
async def report_history(
    admin: AdminOnly,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ReportOut]:
    """Resolved and rejected complaints with the decision."""
    query = select(Report).where(Report.status != ReportStatus.OPEN).limit(limit)
    return await reports_out(session, query)


@router.post("/resolve")
async def resolve(body: ResolveIn, admin: AdminOnly, session: SessionDep) -> dict:
    """Decide on every open complaint about one user at once."""
    user = await session.get(User, body.target_user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user_not_found")
    if body.action == "block":
        await apply_block(session, admin, user, True, body.note)
    elif body.action in ("hide", "reset"):
        await apply_nickname(session, admin, user, body.action, body.note)
    decision = {
        "dismiss": "Shikoyat asossiz",
        "hide": "Taxallus yashirildi",
        "reset": "Taxallusni o'zgartirish talab qilindi",
        "block": "Foydalanuvchi bloklandi",
    }[body.action]
    resolution = f"{decision}. {body.note}" if body.note else decision
    result = await session.execute(
        update(Report)
        .where(Report.target_user_id == user.id, Report.status == ReportStatus.OPEN)
        .values(
            status=ReportStatus.REJECTED if body.action == "dismiss" else ReportStatus.RESOLVED,
            resolution=resolution,
            resolved_at=datetime.now(UTC),
            resolved_by=admin.id,
        )
    )
    audit(
        session,
        admin,
        "report.resolve",
        "user",
        user.id,
        decision=body.action,
        reports=result.rowcount,
    )
    await session.commit()
    return {"resolved": result.rowcount}
