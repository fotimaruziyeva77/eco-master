"""Broadcasts: a message from the team to many users through the bot (app/broadcasts.py)."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.admin.audit import audit
from app.admin.deps import AdminOnly
from app.admin.schemas import (
    AudienceOut,
    BroadcastAudience,
    BroadcastIn,
    BroadcastListOut,
    BroadcastOut,
)
from app.broadcasts import WEEKLY_LIMIT, audience_size, sent_this_week
from app.deps import SessionDep
from app.models import AdminUser, AnalyticsEvent, Broadcast, BroadcastStatus

router = APIRouter(prefix="/broadcasts", tags=["admin-broadcasts"])


def broadcast_out(broadcast: Broadcast, author: str | None, opened: int) -> BroadcastOut:
    return BroadcastOut(
        id=broadcast.id,
        text=broadcast.text,
        audience=broadcast.audience,
        status=broadcast.status.value,
        created_by=author,
        created_at=broadcast.created_at,
        started_at=broadcast.started_at,
        finished_at=broadcast.finished_at,
        total=broadcast.total,
        sent=broadcast.sent,
        failed=broadcast.failed,
        opened=opened,
    )


@router.get("")
async def list_broadcasts(admin: AdminOnly, session: SessionDep) -> BroadcastListOut:
    rows = (
        await session.execute(
            select(Broadcast, AdminUser.name)
            .outerjoin(AdminUser, AdminUser.id == Broadcast.created_by)
            .order_by(Broadcast.id.desc())
            .limit(50)
        )
    ).all()
    key = AnalyticsEvent.props["broadcast"].astext
    opened = dict(
        (
            await session.execute(
                select(key, func.count(func.distinct(AnalyticsEvent.user_id)))
                .where(
                    AnalyticsEvent.name == "broadcast_open",
                    key.in_([str(b.id) for b, _ in rows]),
                )
                .group_by(key)
            )
        ).all()
    )
    return BroadcastListOut(
        items=[broadcast_out(b, name, opened.get(str(b.id), 0)) for b, name in rows],
        weekly_limit=WEEKLY_LIMIT,
        sent_this_week=await sent_this_week(session),
    )


@router.get("/audience")
async def audience(
    admin: AdminOnly, session: SessionDep, audience: Annotated[BroadcastAudience, Query()] = "all"
) -> AudienceOut:
    """How many users would get a broadcast now."""
    return AudienceOut(audience=audience, count=await audience_size(session, audience))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_broadcast(
    body: BroadcastIn, admin: AdminOnly, session: SessionDep
) -> BroadcastOut:
    if await sent_this_week(session) >= WEEKLY_LIMIT:
        raise HTTPException(status.HTTP_409_CONFLICT, "weekly_limit")
    broadcast = Broadcast(text=body.text, audience=body.audience, created_by=admin.id)
    session.add(broadcast)
    await session.flush()
    audit(
        session,
        admin,
        "broadcast_create",
        "broadcast",
        broadcast.id,
        audience=body.audience,
        languages=sorted(body.text),
    )
    await session.commit()
    await session.refresh(broadcast)
    return broadcast_out(broadcast, admin.name, 0)


@router.post("/{broadcast_id}/cancel")
async def cancel_broadcast(
    broadcast_id: int, admin: AdminOnly, session: SessionDep
) -> BroadcastOut:
    broadcast = await session.get(Broadcast, broadcast_id)
    if broadcast is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "broadcast_not_found")
    if broadcast.status not in (BroadcastStatus.QUEUED, BroadcastStatus.SENDING):
        raise HTTPException(status.HTTP_409_CONFLICT, "broadcast_finished")
    broadcast.status = BroadcastStatus.CANCELLED
    broadcast.finished_at = func.now()
    audit(session, admin, "broadcast_cancel", "broadcast", broadcast.id, sent=broadcast.sent)
    await session.commit()
    await session.refresh(broadcast)
    author = await session.scalar(
        select(AdminUser.name).where(AdminUser.id == broadcast.created_by)
    )
    return broadcast_out(broadcast, author, 0)
