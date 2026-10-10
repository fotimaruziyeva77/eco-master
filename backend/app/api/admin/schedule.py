"""Which daily task and tip each date gets (TZ 8.5, 8.10)."""

from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from app.admin.audit import audit
from app.admin.deps import ContentStaff
from app.admin.schemas import ScheduleDayOut, ScheduleOptionOut, ScheduleOut, ScheduleSetIn
from app.deps import SessionDep
from app.models import ContentStatus, DailyTask, DailyTaskSchedule, Tip, TipSchedule
from app.timeutil import local_today

router = APIRouter(prefix="/schedule", tags=["admin-content"])

Kind = Literal["daily", "tips"]
KINDS = {
    "daily": (DailyTask, DailyTaskSchedule, "task_id"),
    "tips": (Tip, TipSchedule, "tip_id"),
}


def short(text: dict) -> str:
    value = text.get("uz") or next((v for v in text.values() if v), "")
    return value if len(value) <= 90 else value[:89] + "…"


@router.get("/{kind}")
async def get_schedule(
    kind: Kind,
    admin: ContentStaff,
    session: SessionDep,
    start: Annotated[date | None, Query()] = None,
    days: Annotated[int, Query(ge=1, le=92)] = 35,
) -> ScheduleOut:
    model, schedule, column = KINDS[kind]
    first = start or local_today()
    last = first + timedelta(days=days - 1)
    items = (
        await session.scalars(
            select(model)
            .where(model.status == ContentStatus.PUBLISHED)
            .order_by(model.sort_order, model.id)
        )
    ).all()
    by_id = {i.id: i for i in items}
    planned = dict(
        (
            await session.execute(
                select(schedule.day, getattr(schedule, column)).where(
                    schedule.day.between(first, last)
                )
            )
        ).all()
    )
    out = []
    for offset in range(days):
        day = first + timedelta(days=offset)
        # The same rotation the app uses when a date has nothing scheduled (app/daily.py).
        auto = items[day.toordinal() % len(items)] if items else None
        item = by_id.get(planned.get(day))
        out.append(
            ScheduleDayOut(
                day=day,
                item_id=item.id if item else None,
                item_title=short(item.text) if item else None,
                auto_item_id=auto.id if auto else None,
                auto_item_title=short(auto.text) if auto else None,
            )
        )
    return ScheduleOut(
        kind=kind,
        days=out,
        items=[ScheduleOptionOut(id=i.id, title=short(i.text)) for i in items],
    )


@router.put("/{kind}/{day}", status_code=status.HTTP_204_NO_CONTENT)
async def set_day(
    kind: Kind, day: date, body: ScheduleSetIn, admin: ContentStaff, session: SessionDep
) -> Response:
    """Pin an item to a date, or clear it (item_id null) to fall back to the rotation."""
    model, schedule, column = KINDS[kind]
    if body.item_id is None:
        await session.execute(delete(schedule).where(schedule.day == day))
    else:
        item = await session.get(model, body.item_id)
        if item is None or item.status != ContentStatus.PUBLISHED:
            raise HTTPException(status.HTTP_409_CONFLICT, "only_published")
        await session.execute(
            insert(schedule)
            .values(day=day, **{column: item.id})
            .on_conflict_do_update(index_elements=[schedule.day], set_={column: item.id})
        )
    audit(session, admin, "schedule.set", kind, day.isoformat(), item_id=body.item_id)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
