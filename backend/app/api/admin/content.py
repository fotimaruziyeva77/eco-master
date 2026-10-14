"""Content in three languages: draft → review → published → archived (TZ 8.12, QM-14)."""

import asyncio
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit import audit
from app.admin.content import (
    CONTENT_TYPES,
    ContentInvalid,
    ContentType,
    Ctx,
    Issue,
    clean_all,
    issues_for,
    read_values,
    write_values,
)
from app.admin.deps import ContentStaff
from app.admin.schemas import (
    ContentItemOut,
    ContentMetaOut,
    ContentRowOut,
    ContentTypeOut,
    ContentValuesIn,
    FieldOptionOut,
    FieldSpecOut,
    IssueOut,
    StatusIn,
)
from app.api.lessons import pdf_response, render
from app.content_media import make_step_pictures
from app.deps import SessionDep
from app.models import ContentStatus, TeacherLesson
from app.schemas import Language

router = APIRouter(prefix="/content", tags=["admin-content"])

S = ContentStatus
# Which status an item may move to from which (TZ 8.12: Draft → In review → Published → Archive).
TRANSITIONS: dict[ContentStatus, set[ContentStatus]] = {
    S.DRAFT: {S.REVIEW, S.PUBLISHED, S.ARCHIVED},
    S.REVIEW: {S.DRAFT, S.PUBLISHED, S.ARCHIVED},
    S.PUBLISHED: {S.DRAFT, S.ARCHIVED},
    S.ARCHIVED: {S.DRAFT},
}


def content_type(key: str) -> ContentType:
    ctype = CONTENT_TYPES.get(key)
    if ctype is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "unknown_content_type")
    return ctype


async def get_item(session: AsyncSession, ctype: ContentType, item_id: int) -> Any:
    item = await session.get(ctype.model, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "item_not_found")
    return item


def issues_out(issues: list[Issue]) -> list[IssueOut]:
    return [IssueOut(level=i.level, message=i.message, field=i.field, lang=i.lang) for i in issues]


def item_out(ctype: ContentType, item: Any, ctx: Ctx) -> ContentItemOut:
    values = read_values(ctype, item, ctx)
    return ContentItemOut(
        id=item.id,
        status=item.status if ctype.has_status else None,
        values=values,
        issues=issues_out(issues_for(ctype, values, ctx)),
        created_at=getattr(item, "created_at", None),
        updated_at=getattr(item, "updated_at", None),
    )


def blocked(issues: list[Issue]) -> None:
    errors = [i for i in issues if i.level == "error"]
    if errors:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            {"code": "publish_blocked", "issues": [i.model_dump() for i in issues_out(errors)]},
        )


def invalid(exc: ContentInvalid) -> HTTPException:
    return HTTPException(
        status.HTTP_422_UNPROCESSABLE_CONTENT, {"code": "invalid", "errors": exc.errors}
    )


async def counts_by_status(session: AsyncSession, ctype: ContentType) -> dict[str, int]:
    if not ctype.has_status:
        total = await session.scalar(select(func.count()).select_from(ctype.model))
        return {"all": total}
    rows = await session.execute(
        select(ctype.model.status, func.count()).group_by(ctype.model.status)
    )
    counts = {s.value: n for s, n in rows.all()}
    counts["all"] = sum(counts.values())
    return counts


def type_out(ctype: ContentType, counts: dict[str, int]) -> ContentTypeOut:
    return ContentTypeOut(
        key=ctype.key,
        title=ctype.title,
        has_status=ctype.has_status,
        deletable=ctype.deletable,
        preview=ctype.preview,
        counts=counts,
    )


@router.get("")
async def content_types(admin: ContentStaff, session: SessionDep) -> list[ContentTypeOut]:
    return [type_out(t, await counts_by_status(session, t)) for t in CONTENT_TYPES.values()]


@router.get("/{type_key}/meta")
async def content_meta(type_key: str, admin: ContentStaff, session: SessionDep) -> ContentMetaOut:
    """Field descriptions the admin UI builds its form from."""
    ctype = content_type(type_key)
    ctx = await Ctx.load(session)
    fields = []
    for f in ctype.fields:
        options = None
        if f.kind == "select":
            options = [FieldOptionOut(value=v, label=label) for v, label in f.options]
        elif f.kind == "category":
            options = [
                FieldOptionOut(value=c.code, label=f"{c.icon} {c.name.get('uz', c.code)}")
                for c in ctx.categories
                if not f.category_filter or getattr(c, f.category_filter)
            ]
        fields.append(
            FieldSpecOut(
                name=f.name,
                label=f.label,
                kind=f.kind,
                required=f.required,
                nullable=f.nullable,
                fixed=f.fixed,
                help=f.help,
                options=options,
                min=f.min,
                max=f.max,
                max_length=f.max_length,
            )
        )
    return ContentMetaOut(
        **type_out(ctype, await counts_by_status(session, ctype)).model_dump(),
        fields=fields,
        defaults=ctype.defaults,
    )


@router.get("/{type_key}")
async def list_items(
    type_key: str,
    admin: ContentStaff,
    session: SessionDep,
    status_filter: Annotated[ContentStatus | None, Query(alias="status")] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> list[ContentRowOut]:
    ctype = content_type(type_key)
    model = ctype.model
    query = select(model).order_by(*(getattr(model, c) for c in ctype.order_by))
    if status_filter is not None and ctype.has_status:
        query = query.where(model.status == status_filter)
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        query = query.where(
            or_(*(cast(getattr(model, c), Text).ilike(pattern) for c in ctype.search_columns))
        )
    ctx = await Ctx.load(session)
    rows = []
    for item in (await session.scalars(query.limit(1000))).all():
        values = read_values(ctype, item, ctx)
        issues = issues_for(ctype, values, ctx)
        rows.append(
            ContentRowOut(
                id=item.id,
                title=ctype.row_title(values),
                subtitle=ctype.subtitle(values, ctx),
                status=item.status if ctype.has_status else None,
                updated_at=getattr(item, "updated_at", None),
                errors=sum(i.level == "error" for i in issues),
                warnings=sum(i.level == "warning" for i in issues),
            )
        )
    return rows


@router.get("/{type_key}/{item_id}")
async def get_content(
    type_key: str, item_id: int, admin: ContentStaff, session: SessionDep
) -> ContentItemOut:
    ctype = content_type(type_key)
    return item_out(ctype, await get_item(session, ctype, item_id), await Ctx.load(session))


async def save(session: AsyncSession, ctype: ContentType) -> None:
    try:
        await session.flush()
    except IntegrityError as exc:
        # The only unique values an editor types are slugs and category codes.
        await session.rollback()
        taken = {f.name: "Bu nom band" for f in ctype.fields if f.fixed}
        raise HTTPException(status.HTTP_409_CONFLICT, {"code": "invalid", "errors": taken}) from exc


async def step_pictures(ctype: ContentType, item: Any) -> None:
    """A project's steps get pictures from its video (ffmpeg, a moment per step)."""
    if ctype.key == "projects" and item.step_times:
        await asyncio.to_thread(make_step_pictures, item.video_url, item.step_times)


@router.post("/{type_key}", status_code=status.HTTP_201_CREATED)
async def create_content(
    type_key: str, body: ContentValuesIn, admin: ContentStaff, session: SessionDep
) -> ContentItemOut:
    """New items start as drafts."""
    ctype = content_type(type_key)
    ctx = await Ctx.load(session)
    try:
        values = clean_all(ctype, body.values, ctx)
    except ContentInvalid as exc:
        raise invalid(exc) from exc
    item = ctype.model()
    write_values(ctype, item, values, ctx)
    if ctype.has_status:
        item.status = ContentStatus.DRAFT
    session.add(item)
    await save(session, ctype)
    await step_pictures(ctype, item)
    audit(session, admin, "content.create", ctype.key, item.id, title=ctype.row_title(values))
    await session.commit()
    await session.refresh(item)
    return item_out(ctype, item, ctx)


@router.put("/{type_key}/{item_id}")
async def update_content(
    type_key: str,
    item_id: int,
    body: ContentValuesIn,
    admin: ContentStaff,
    session: SessionDep,
) -> ContentItemOut:
    ctype = content_type(type_key)
    item = await get_item(session, ctype, item_id)
    ctx = await Ctx.load(session)
    before = read_values(ctype, item, ctx)
    try:
        values = clean_all(ctype, body.values, ctx)
    except ContentInvalid as exc:
        raise invalid(exc) from exc

    errors = {}
    for f in ctype.fields:
        # A slug or code is part of links and references: set once, while still a draft.
        locked = not ctype.has_status or item.status != ContentStatus.DRAFT
        if f.fixed and locked and values[f.name] != before[f.name]:
            errors[f.name] = "Nashr qilingandan keyin o'zgartirib bo'lmaydi"
    if errors:
        raise invalid(ContentInvalid(errors))
    if ctype.has_status and item.status == ContentStatus.PUBLISHED:
        # A live item must keep passing the publish checks.
        blocked(issues_for(ctype, values, ctx))

    write_values(ctype, item, values, ctx)
    await save(session, ctype)
    await step_pictures(ctype, item)
    changed = sorted(f.name for f in ctype.fields if values[f.name] != before[f.name])
    if changed:
        audit(session, admin, "content.update", ctype.key, item.id, fields=changed)
    await session.commit()
    await session.refresh(item)
    return item_out(ctype, item, ctx)


@router.post("/{type_key}/{item_id}/status")
async def change_status(
    type_key: str, item_id: int, body: StatusIn, admin: ContentStaff, session: SessionDep
) -> ContentItemOut:
    ctype = content_type(type_key)
    if not ctype.has_status:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "no_status")
    item = await get_item(session, ctype, item_id)
    ctx = await Ctx.load(session)
    current = item.status
    if body.status == current:
        return item_out(ctype, item, ctx)
    if body.status not in TRANSITIONS[current]:
        raise HTTPException(status.HTTP_409_CONFLICT, "bad_transition")
    if body.status == ContentStatus.PUBLISHED:
        # Mandatory checks before publishing (TZ 8.12, QM-14).
        blocked(issues_for(ctype, read_values(ctype, item, ctx), ctx))
    item.status = body.status
    audit(
        session,
        admin,
        "content.status",
        ctype.key,
        item.id,
        old=current.value,
        new=body.status.value,
    )
    await session.commit()
    await session.refresh(item)
    return item_out(ctype, item, ctx)


@router.delete("/{type_key}/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    type_key: str, item_id: int, admin: ContentStaff, session: SessionDep
) -> Response:
    """Only drafts can be deleted; anything that was live goes to the archive instead."""
    ctype = content_type(type_key)
    if not ctype.deletable:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "not_deletable")
    item = await get_item(session, ctype, item_id)
    if item.status != ContentStatus.DRAFT:
        raise HTTPException(status.HTTP_409_CONFLICT, "only_drafts")
    title = ctype.row_title(read_values(ctype, item, await Ctx.load(session)))
    await session.delete(item)
    try:
        await session.flush()
    except IntegrityError as exc:
        # Still referred to, e.g. a handover point that market listings use.
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "in_use") from exc
    audit(session, admin, "content.delete", ctype.key, item_id, title=title)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/lessons/{item_id}/pdf")
async def lesson_pdf_preview(
    item_id: int,
    admin: ContentStaff,
    session: SessionDep,
    lang: Annotated[Language, Query()] = "uz",
) -> Response:
    """The PDF exactly as teachers will get it, also for drafts (preview, TZ 8.12)."""
    lesson = await session.get(TeacherLesson, item_id)
    if lesson is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "item_not_found")
    return pdf_response(render(lesson, lang))
