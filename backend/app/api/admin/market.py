"""Market moderation and the handover desk (phase 9).

Moderators (administrators and content editors) decide what appears in the market. Staff of a
handover point see only their point's desk: they take items in and hand them out by the
six-digit codes the children tell them.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import Text, cast, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app import timeutil
from app.admin.audit import audit
from app.admin.deps import ContentStaff, HandoverStaff
from app.admin.schemas import (
    HandoverCodeIn,
    HandoverDeskOut,
    HandoverItemOut,
    HandoverMatchOut,
    HandoverPointOut,
    MarketCountsOut,
    MarketDecisionIn,
    MarketListingOut,
    MarketPhotoOut,
    MarketReportRowOut,
    MarketRequestRowOut,
    MarketRowOut,
)
from app.analytics import track
from app.api.market import deadline_of, first_photos
from app.deps import BotDep, SessionDep, SettingsDep
from app.market import (
    ITEM_TYPE_NAMES,
    PICK_UP_DAYS,
    Note,
    deliver,
    end_handover,
    handover_of,
    note,
    notes_for_decline,
    point_text,
)
from app.media import photo_url
from app.models import (
    AdminRole,
    AdminUser,
    Category,
    ContentStatus,
    Listing,
    ListingKind,
    ListingPhoto,
    ListingReport,
    ListingRequest,
    ListingStatus,
    PickupPoint,
    ReportStatus,
    RequestStatus,
    User,
)
from app.ratelimit import RateLimiter

router = APIRouter(tags=["admin-market"])

lookup_limit = RateLimiter(limit=30, window=60)
Filter = Literal["pending", "reported", "approved", "rejected", "hidden", "handover", "all"]


async def open_reports(session: AsyncSession, listing_ids: list[int]) -> dict[int, int]:
    if not listing_ids:
        return {}
    rows = await session.execute(
        select(ListingReport.listing_id, func.count())
        .where(ListingReport.listing_id.in_(listing_ids), ListingReport.status == ReportStatus.OPEN)
        .group_by(ListingReport.listing_id)
    )
    return dict(rows.all())


def row_out(
    listing: Listing, owner: User | None, cover: int | None, reports: int, secret: str
) -> MarketRowOut:
    return MarketRowOut(
        id=listing.id,
        title=listing.title,
        kind=listing.kind,
        status=listing.status,
        giveaway=listing.giveaway,
        owner_id=listing.owner_id,
        owner_nickname=owner.nickname if owner else None,
        thumb_url=photo_url(secret, cover, "thumb", "o") if cover else None,
        reports_open=reports,
        submitted_at=listing.submitted_at,
        created_at=listing.created_at,
    )


async def get_listing(session: AsyncSession, listing_id: int) -> Listing:
    listing = await session.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "listing_not_found")
    return listing


# ------------------------------------------------------------------ moderation


@router.get("/market/counts")
async def counts(admin: ContentStaff, session: SessionDep) -> MarketCountsOut:
    pending = await session.scalar(
        select(func.count()).where(Listing.status == ListingStatus.PENDING)
    )
    reported = await session.scalar(
        select(func.count(func.distinct(ListingReport.listing_id))).where(
            ListingReport.status == ReportStatus.OPEN
        )
    )
    return MarketCountsOut(pending=pending, reported=reported)


@router.get("/market")
async def listings(
    admin: ContentStaff,
    session: SessionDep,
    settings: SettingsDep,
    show: Annotated[Filter, Query(alias="filter")] = "pending",
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> list[MarketRowOut]:
    """The review queue (oldest first), reported listings, or everything by status."""
    query = select(Listing, User).outerjoin(User, User.id == Listing.owner_id)
    if show == "pending":
        query = query.where(Listing.status == ListingStatus.PENDING).order_by(Listing.submitted_at)
    elif show == "reported":
        reported = select(ListingReport.listing_id).where(ListingReport.status == ReportStatus.OPEN)
        query = query.where(Listing.id.in_(reported)).order_by(Listing.id.desc())
    elif show == "handover":
        query = query.where(
            Listing.status.in_((ListingStatus.RESERVED, ListingStatus.AT_POINT))
            | Listing.stored_at_point.is_(True)
        ).order_by(Listing.id.desc())
    elif show != "all":
        query = query.where(Listing.status == ListingStatus(show)).order_by(Listing.id.desc())
    else:
        query = query.order_by(Listing.id.desc())
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        query = query.where(
            or_(
                Listing.title.ilike(pattern),
                User.nickname.ilike(pattern),
                cast(Listing.id, Text) == q.strip(),
            )
        )
    rows = (await session.execute(query.limit(200))).all()
    ids = [listing.id for listing, _ in rows]
    covers = await first_photos(session, ids)
    reports = await open_reports(session, ids)
    return [
        row_out(
            listing, owner, covers.get(listing.id), reports.get(listing.id, 0), settings.jwt_secret
        )
        for listing, owner in rows
    ]


@router.get("/market/{listing_id}")
async def listing_detail(
    listing_id: int, admin: ContentStaff, session: SessionDep, settings: SettingsDep
) -> MarketListingOut:
    listing = await get_listing(session, listing_id)
    return await detail_out(session, listing, settings.jwt_secret)


async def detail_out(session: AsyncSession, listing: Listing, secret: str) -> MarketListingOut:
    owner = await session.get(User, listing.owner_id) if listing.owner_id else None
    photos = (
        await session.scalars(
            select(ListingPhoto)
            .where(ListingPhoto.listing_id == listing.id)
            .order_by(ListingPhoto.position, ListingPhoto.id)
        )
    ).all()
    point = (
        await session.get(PickupPoint, listing.pickup_point_id) if listing.pickup_point_id else None
    )
    reviewer = await session.get(AdminUser, listing.reviewed_by) if listing.reviewed_by else None
    if listing.kind == ListingKind.HANDMADE:
        category = await session.scalar(select(Category).where(Category.code == listing.category))
        category_name = (
            f"{category.icon} {category.name.get('uz')}" if category else listing.category
        )
    else:
        category_name = ITEM_TYPE_NAMES.get(listing.category, listing.category)
    requests = (
        await session.execute(
            select(ListingRequest, User)
            .join(User, User.id == ListingRequest.requester_id)
            .where(ListingRequest.listing_id == listing.id)
            .order_by(ListingRequest.id.desc())
        )
    ).all()
    reports = (
        await session.scalars(
            select(ListingReport)
            .where(ListingReport.listing_id == listing.id)
            .order_by(ListingReport.id.desc())
        )
    ).all()
    base = row_out(
        listing,
        owner,
        photos[0].id if photos else None,
        sum(r.status == ReportStatus.OPEN for r in reports),
        secret,
    )
    return MarketListingOut(
        **base.model_dump(),
        description=listing.description,
        category=listing.category,
        category_name=category_name,
        condition=listing.condition,
        point_name=point.name.get("uz") if point else None,
        stored_at_point=listing.stored_at_point,
        reject_reason=listing.reject_reason,
        moderator_note=listing.moderator_note,
        likes=listing.likes_count,
        published_at=listing.published_at,
        reviewed_at=listing.reviewed_at,
        reviewed_by=reviewer.name if reviewer else None,
        photos=[
            MarketPhotoOut(
                id=p.id,
                url=photo_url(secret, p.id, "full", "o"),
                thumb_url=photo_url(secret, p.id, "thumb", "o"),
                width=p.width,
                height=p.height,
            )
            for p in photos
        ],
        requests=[
            MarketRequestRowOut(
                id=r.id,
                requester_id=u.id,
                nickname=u.nickname,
                status=r.status,
                created_at=r.created_at,
                decided_at=r.decided_at,
                dropped_at=r.dropped_at,
                given_at=r.given_at,
            )
            for r, u in requests
        ],
        reports=[
            MarketReportRowOut(id=r.id, reason=r.reason, status=r.status, created_at=r.created_at)
            for r in reports
        ],
    )


async def close_reports(
    session: AsyncSession, admin: AdminUser, listing: Listing, outcome: ReportStatus
) -> int:
    result = await session.execute(
        update(ListingReport)
        .where(ListingReport.listing_id == listing.id, ListingReport.status == ReportStatus.OPEN)
        .values(status=outcome, resolved_at=timeutil.utc_now(), resolved_by=admin.id)
    )
    return result.rowcount or 0


def reviewed(listing: Listing, admin: AdminUser) -> None:
    listing.reviewed_at = timeutil.utc_now()
    listing.reviewed_by = admin.id


@router.post("/market/{listing_id}/approve")
async def approve(
    listing_id: int,
    admin: ContentStaff,
    session: SessionDep,
    settings: SettingsDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> MarketListingOut:
    """Into the market: a new or changed listing, or one taken down that turned out fine."""
    listing = await get_listing(session, listing_id)
    if listing.status not in (ListingStatus.PENDING, ListingStatus.HIDDEN):
        raise HTTPException(status.HTTP_409_CONFLICT, "bad_transition")
    if listing.status == ListingStatus.PENDING:
        listing.published_at = timeutil.utc_now()
    listing.status = ListingStatus.APPROVED
    listing.reject_reason = None
    listing.moderator_note = None
    reviewed(listing, admin)
    dismissed = await close_reports(session, admin, listing, ReportStatus.REJECTED)
    owner = await session.get(User, listing.owner_id) if listing.owner_id else None
    notes = note(owner, "market_approved", title=listing.title)
    audit(session, admin, "market.approve", "listing", listing.id, reports_dismissed=dismissed)
    await session.commit()
    background.add_task(deliver, bot, notes)
    return await detail_out(session, listing, settings.jwt_secret)


@router.post("/market/{listing_id}/reject")
async def reject(
    listing_id: int,
    body: MarketDecisionIn,
    admin: ContentStaff,
    session: SessionDep,
    settings: SettingsDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> MarketListingOut:
    """Not published; the child gets the reason and can fix the listing."""
    listing = await get_listing(session, listing_id)
    if listing.status != ListingStatus.PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "bad_transition")
    note_text = body.note.strip() if body.note and body.note.strip() else None
    listing.status = ListingStatus.REJECTED
    listing.reject_reason = body.reason
    listing.moderator_note = note_text
    reviewed(listing, admin)
    owner = await session.get(User, listing.owner_id) if listing.owner_id else None
    notes = note(
        owner, "market_rejected", title=listing.title, reason=body.reason, note=note_text or ""
    )
    audit(session, admin, "market.reject", "listing", listing.id, reason=body.reason)
    await session.commit()
    background.add_task(deliver, bot, notes)
    return await detail_out(session, listing, settings.jwt_secret)


@router.post("/market/{listing_id}/hide")
async def hide(
    listing_id: int,
    body: MarketDecisionIn,
    admin: ContentStaff,
    session: SessionDep,
    settings: SettingsDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> MarketListingOut:
    """Take a published listing down. A handover in progress is called off; an item already
    at the point stays there until the staff returns it to its owner."""
    listing = await get_listing(session, listing_id)
    if listing.status not in (
        ListingStatus.APPROVED,
        ListingStatus.RESERVED,
        ListingStatus.AT_POINT,
        ListingStatus.HIDDEN,
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "bad_transition")
    notes: list[Note] = []
    handover = await handover_of(session, listing.id)
    if handover is not None:
        await end_handover(session, listing, handover, RequestStatus.CANCELLED)
        requester = await session.get(User, handover.requester_id)
        notes += note(requester, "market_cancelled", title=listing.title)
    notes += await notes_for_decline(session, listing, "market_withdrawn")
    note_text = body.note.strip() if body.note and body.note.strip() else None
    was_hidden = listing.status == ListingStatus.HIDDEN
    listing.status = ListingStatus.HIDDEN
    listing.reject_reason = body.reason
    listing.moderator_note = note_text
    reviewed(listing, admin)
    resolved = await close_reports(session, admin, listing, ReportStatus.RESOLVED)
    if not was_hidden or resolved:
        owner = await session.get(User, listing.owner_id) if listing.owner_id else None
        notes += note(
            owner, "market_hidden", title=listing.title, reason=body.reason, note=note_text or ""
        )
    audit(session, admin, "market.hide", "listing", listing.id, reason=body.reason)
    await session.commit()
    background.add_task(deliver, bot, notes)
    return await detail_out(session, listing, settings.jwt_secret)


@router.post("/market/{listing_id}/dismiss-reports")
async def dismiss_reports(
    listing_id: int, admin: ContentStaff, session: SessionDep, settings: SettingsDep
) -> MarketListingOut:
    """The reports were unfounded; the listing stays as it is."""
    listing = await get_listing(session, listing_id)
    dismissed = await close_reports(session, admin, listing, ReportStatus.REJECTED)
    audit(session, admin, "market.dismiss_reports", "listing", listing.id, reports=dismissed)
    await session.commit()
    return await detail_out(session, listing, settings.jwt_secret)


# --------------------------------------------------------------- handover desk


def desk_point_id(admin: AdminUser, point_id: int | None) -> int:
    """Point staff always work at their own point; administrators choose one."""
    if admin.role == AdminRole.POINT:
        return admin.pickup_point_id
    if point_id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "point_required")
    return point_id


@router.get("/handover/points")
async def handover_points(admin: HandoverStaff, session: SessionDep) -> list[HandoverPointOut]:
    query = select(PickupPoint).order_by(PickupPoint.sort_order, PickupPoint.id)
    if admin.role == AdminRole.POINT:
        query = query.where(PickupPoint.id == admin.pickup_point_id)
    else:
        query = query.where(PickupPoint.status != ContentStatus.DRAFT)
    rows = (await session.scalars(query)).all()
    return [HandoverPointOut(id=p.id, name=p.name.get("uz") or str(p.id)) for p in rows]


async def item_out(
    session: AsyncSession, listing: Listing, request: ListingRequest | None, secret: str
) -> HandoverItemOut:
    covers = await first_photos(session, [listing.id])
    owner = await session.get(User, listing.owner_id) if listing.owner_id else None
    requester = await session.get(User, request.requester_id) if request else None
    since = None
    if request is not None:
        since = (
            request.dropped_at if request.status == RequestStatus.AT_POINT else request.decided_at
        )
    return HandoverItemOut(
        request_id=request.id if request else None,
        listing_id=listing.id,
        title=listing.title,
        thumb_url=photo_url(secret, covers[listing.id], "thumb", "o")
        if listing.id in covers
        else None,
        owner_nickname=owner.nickname if owner else None,
        requester_nickname=requester.nickname if requester else None,
        status=request.status if request else None,
        since=since,
        deadline=deadline_of(request) if request else None,
    )


@router.get("/handover")
async def desk(
    admin: HandoverStaff,
    session: SessionDep,
    settings: SettingsDep,
    point_id: int | None = None,
) -> HandoverDeskOut:
    point = await session.get(PickupPoint, desk_point_id(admin, point_id))
    if point is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "point_not_found")
    active = (
        await session.execute(
            select(ListingRequest, Listing)
            .join(Listing, Listing.id == ListingRequest.listing_id)
            .where(
                Listing.pickup_point_id == point.id,
                ListingRequest.status.in_((RequestStatus.ACCEPTED, RequestStatus.AT_POINT)),
            )
            .order_by(ListingRequest.id)
        )
    ).all()
    stored = (
        await session.scalars(
            select(Listing)
            .where(Listing.pickup_point_id == point.id, Listing.stored_at_point.is_(True))
            .order_by(Listing.id)
        )
    ).all()
    secret = settings.jwt_secret
    drop, pick = [], []
    for request, listing in active:
        item = await item_out(session, listing, request, secret)
        (drop if request.status == RequestStatus.ACCEPTED else pick).append(item)
    return HandoverDeskOut(
        point=HandoverPointOut(id=point.id, name=point.name.get("uz") or str(point.id)),
        waiting_drop=drop,
        waiting_pick=pick,
        stored=[await item_out(session, listing, None, secret) for listing in stored],
    )


async def handover_at(
    session: AsyncSession, admin: AdminUser, request_id: int
) -> tuple[ListingRequest, Listing]:
    row = (
        await session.execute(
            select(ListingRequest, Listing)
            .join(Listing, Listing.id == ListingRequest.listing_id)
            .where(ListingRequest.id == request_id)
        )
    ).first()
    if row is None or (
        admin.role == AdminRole.POINT and row[1].pickup_point_id != admin.pickup_point_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "request_not_found")
    return row[0], row[1]


@router.post("/handover/lookup")
async def lookup(
    body: HandoverCodeIn, admin: HandoverStaff, session: SessionDep, settings: SettingsDep
) -> HandoverMatchOut:
    """What a code the child said belongs to: an item to take in, or one to hand out."""
    if not lookup_limit.allow(admin.id):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_lookups")
    point_id = desk_point_id(admin, body.point_id)
    row = (
        await session.execute(
            select(ListingRequest, Listing)
            .join(Listing, Listing.id == ListingRequest.listing_id)
            .where(
                Listing.pickup_point_id == point_id,
                or_(
                    (ListingRequest.status == RequestStatus.ACCEPTED)
                    & (ListingRequest.drop_code == body.code),
                    (ListingRequest.status == RequestStatus.AT_POINT)
                    & (ListingRequest.pick_code == body.code),
                ),
            )
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "code_not_found")
    request, listing = row
    action = "receive" if request.status == RequestStatus.ACCEPTED else "give"
    return HandoverMatchOut(
        action=action, item=await item_out(session, listing, request, settings.jwt_secret)
    )


@router.post("/handover/{request_id}/receive")
async def receive(
    request_id: int,
    body: HandoverCodeIn,
    admin: HandoverStaff,
    session: SessionDep,
    settings: SettingsDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> HandoverItemOut:
    """The owner brought the item and said their code."""
    request, listing = await handover_at(session, admin, request_id)
    if request.status != RequestStatus.ACCEPTED:
        raise HTTPException(status.HTTP_409_CONFLICT, "bad_transition")
    if body.code != request.drop_code:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "wrong_code")
    request.status = RequestStatus.AT_POINT
    request.dropped_at = timeutil.utc_now()
    request.handled_by = admin.id
    listing.status = ListingStatus.AT_POINT
    requester = await session.get(User, request.requester_id)
    owner = await session.get(User, listing.owner_id) if listing.owner_id else None
    where, hours = await point_text(session, listing.pickup_point_id, requester.language)
    notes = note(
        requester,
        "market_ready",
        title=listing.title,
        point=where,
        hours=hours,
        code=request.pick_code,
        days=PICK_UP_DAYS,
    )
    notes += note(owner, "market_received", title=listing.title)
    audit(session, admin, "handover.receive", "listing", listing.id, request=request.id)
    await session.commit()
    background.add_task(deliver, bot, notes)
    return await item_out(session, listing, request, settings.jwt_secret)


@router.post("/handover/{request_id}/give")
async def give(
    request_id: int,
    body: HandoverCodeIn,
    admin: HandoverStaff,
    session: SessionDep,
    settings: SettingsDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> HandoverItemOut:
    """The new owner came and said their code."""
    request, listing = await handover_at(session, admin, request_id)
    if request.status != RequestStatus.AT_POINT:
        raise HTTPException(status.HTTP_409_CONFLICT, "bad_transition")
    if body.code != request.pick_code:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "wrong_code")
    request.status = RequestStatus.DONE
    request.given_at = timeutil.utc_now()
    request.handled_by = admin.id
    listing.status = ListingStatus.GIVEN
    listing.stored_at_point = False
    owner = await session.get(User, listing.owner_id) if listing.owner_id else None
    notes = note(owner, "market_given", title=listing.title)
    if owner is not None:
        track(session, owner, "listing_given")
    audit(session, admin, "handover.give", "listing", listing.id, request=request.id)
    await session.commit()
    background.add_task(deliver, bot, notes)
    return await item_out(session, listing, request, settings.jwt_secret)


@router.post("/handover/stored/{listing_id}/return")
async def return_to_owner(listing_id: int, admin: HandoverStaff, session: SessionDep) -> dict:
    """An item nobody collected went back to its owner. Without an owner (the account was
    deleted) the listing is removed."""
    listing = await session.get(Listing, listing_id)
    if (
        listing is None
        or not listing.stored_at_point
        or (admin.role == AdminRole.POINT and listing.pickup_point_id != admin.pickup_point_id)
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "listing_not_found")
    audit(session, admin, "handover.return", "listing", listing.id)
    if listing.owner_id is None:
        await session.delete(listing)
    else:
        listing.stored_at_point = False
    await session.commit()
    return {"ok": True}
