"""Market for users (phase 9): browse, list a thing, like, report, ask for it, agree."""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response, status
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.dialects.postgresql import distinct_on, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app import timeutil
from app.analytics import track
from app.deps import BotDep, CurrentUser, SessionDep, SettingsDep
from app.market import (
    DROP_OFF_DAYS,
    EDITABLE,
    HANDOVER,
    ITEM_TYPES,
    MAX_LOOSE_PHOTOS,
    MAX_NEW_PER_DAY,
    MAX_OPEN_REQUESTS,
    MAX_PENDING,
    MAX_PHOTOS,
    OPEN_REQUEST,
    PICK_UP_DAYS,
    REPORTS_TO_HIDE,
    MarketError,
    Note,
    check_text,
    deliver,
    end_handover,
    handover_of,
    new_codes,
    note,
    notes_for_decline,
    point_text,
)
from app.media import MAX_UPLOAD_BYTES, PhotoError, clean_photo, photo_url
from app.models import (
    Category,
    ContentStatus,
    Listing,
    ListingKind,
    ListingLike,
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
from app.schemas import (
    HandoverOut,
    LikeOut,
    ListingCardOut,
    ListingIn,
    ListingOut,
    ListingPageOut,
    ListingReportIn,
    ListingRequestOut,
    MyListingOut,
    MyRequestOut,
    PhotoOut,
    PickupPointOut,
)
from app.timeutil import TASHKENT

router = APIRouter(prefix="/market", tags=["market"])

PAGE_SIZE = 24
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
upload_limit = RateLimiter(limit=30, window=3600)


def fail(exc: MarketError) -> HTTPException:
    return HTTPException(exc.status, exc.code)


def point_out(point: PickupPoint | None) -> PickupPointOut | None:
    if point is None:
        return None
    return PickupPointOut(id=point.id, name=point.name, address=point.address, hours=point.hours)


def photo_out(secret: str, photo: ListingPhoto, audience: str) -> PhotoOut:
    return PhotoOut(
        id=photo.id,
        url=photo_url(secret, photo.id, "full", audience),
        thumb_url=photo_url(secret, photo.id, "thumb", audience),
        width=photo.width,
        height=photo.height,
    )


def require_nickname(user: User) -> None:
    """Listings and requests show the nickname, so onboarding must be finished."""
    if not user.nickname:
        raise HTTPException(status.HTTP_409_CONFLICT, "nickname_required")


def shown_nickname(user: User | None) -> str | None:
    return None if user is None or user.nickname_hidden else user.nickname


async def first_photos(session: AsyncSession, listing_ids: list[int]) -> dict[int, int]:
    """The cover photo (lowest position) of each listing."""
    if not listing_ids:
        return {}
    rows = await session.execute(
        select(ListingPhoto.listing_id, ListingPhoto.id)
        .where(ListingPhoto.listing_id.in_(listing_ids))
        .order_by(ListingPhoto.listing_id, ListingPhoto.position, ListingPhoto.id)
        .ext(distinct_on(ListingPhoto.listing_id))
    )
    return dict(rows.all())


async def published_point(session: AsyncSession, point_id: int | None) -> PickupPoint:
    point = await session.get(PickupPoint, point_id) if point_id else None
    if point is None or point.status != ContentStatus.PUBLISHED:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "point_unavailable")
    return point


async def own_listing(session: AsyncSession, listing_id: int, user: User) -> Listing:
    listing = await session.get(Listing, listing_id)
    if listing is None or listing.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "listing_not_found")
    return listing


async def latest_request(
    session: AsyncSession, listing_id: int, user_id: int
) -> ListingRequest | None:
    return await session.scalar(
        select(ListingRequest)
        .where(ListingRequest.listing_id == listing_id, ListingRequest.requester_id == user_id)
        .order_by(ListingRequest.id.desc())
        .limit(1)
    )


async def visible_listing(
    session: AsyncSession, listing_id: int, user: User
) -> tuple[Listing, ListingRequest | None]:
    """The listing if this user may see it: in the market, their own, or one they asked for."""
    listing = await session.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "listing_not_found")
    if listing.owner_id == user.id:
        return listing, None
    mine = await latest_request(session, listing.id, user.id)
    owner = await session.get(User, listing.owner_id) if listing.owner_id else None
    public = listing.status == ListingStatus.APPROVED and not (owner and owner.is_blocked)
    involved = mine is not None and mine.status in (*OPEN_REQUEST, RequestStatus.DONE)
    if not public and not involved:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "listing_not_found")
    return listing, mine


def deadline_of(request: ListingRequest) -> datetime | None:
    if request.status == RequestStatus.ACCEPTED and request.decided_at:
        return request.decided_at + timedelta(days=DROP_OFF_DAYS)
    if request.status == RequestStatus.AT_POINT and request.dropped_at:
        return request.dropped_at + timedelta(days=PICK_UP_DAYS)
    return None


async def listing_out(
    session: AsyncSession, secret: str, listing: Listing, user: User, mine: ListingRequest | None
) -> ListingOut:
    is_mine = listing.owner_id == user.id
    audience = "p" if listing.status == ListingStatus.APPROVED and not is_mine else "o"
    photos = await session.scalars(
        select(ListingPhoto)
        .where(ListingPhoto.listing_id == listing.id)
        .order_by(ListingPhoto.position, ListingPhoto.id)
    )
    owner = await session.get(User, listing.owner_id) if listing.owner_id else None
    point = (
        await session.get(PickupPoint, listing.pickup_point_id) if listing.pickup_point_id else None
    )
    liked = await session.scalar(
        select(ListingLike.user_id).where(
            ListingLike.listing_id == listing.id, ListingLike.user_id == user.id
        )
    )
    out = ListingOut(
        id=listing.id,
        kind=listing.kind,
        title=listing.title,
        description=listing.description,
        category=listing.category,
        condition=listing.condition,
        giveaway=listing.giveaway,
        status=listing.status,
        ready_at_point=listing.stored_at_point,
        likes=listing.likes_count,
        liked=liked is not None,
        is_mine=is_mine,
        owner_id=listing.owner_id,
        owner_nickname=shown_nickname(owner),
        photos=[photo_out(secret, p, audience) for p in photos.all()],
        point=point_out(point),
        created_at=listing.created_at,
        published_at=listing.published_at,
    )
    handover = await handover_of(session, listing.id)
    if is_mine:
        out.reject_reason = listing.reject_reason
        out.moderator_note = listing.moderator_note
        waiting = await session.execute(
            select(ListingRequest, User)
            .join(User, User.id == ListingRequest.requester_id)
            .where(
                ListingRequest.listing_id == listing.id,
                ListingRequest.status == RequestStatus.PENDING,
            )
            .order_by(ListingRequest.id)
        )
        out.requests = [
            ListingRequestOut(
                id=r.id,
                requester_id=u.id,
                nickname=shown_nickname(u),
                status=r.status,
                created_at=r.created_at,
            )
            for r, u in waiting.all()
        ]
        if handover:
            requester = await session.get(User, handover.requester_id)
            out.handover = HandoverOut(
                request_id=handover.id,
                status=handover.status,
                code=handover.drop_code if handover.status == RequestStatus.ACCEPTED else None,
                deadline=deadline_of(handover),
                other_nickname=shown_nickname(requester),
            )
    elif mine is not None:
        out.my_request = mine.status
        if handover is not None and handover.id == mine.id:
            out.handover = HandoverOut(
                request_id=mine.id,
                status=mine.status,
                code=mine.pick_code if mine.status == RequestStatus.AT_POINT else None,
                deadline=deadline_of(mine),
                other_nickname=shown_nickname(owner),
            )
    out.can_request = (
        not is_mine
        and listing.status == ListingStatus.APPROVED
        and listing.giveaway
        and (mine is None or mine.status not in OPEN_REQUEST)
    )
    return out


# ------------------------------------------------------------------ browsing


@router.get("/points")
async def points(user: CurrentUser, session: SessionDep) -> list[PickupPointOut]:
    """Handover points where things change hands."""
    rows = await session.scalars(
        select(PickupPoint)
        .where(PickupPoint.status == ContentStatus.PUBLISHED)
        .order_by(PickupPoint.sort_order, PickupPoint.id)
    )
    return [point_out(p) for p in rows.all()]


@router.get("")
async def browse(
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    kind: ListingKind | None = None,
    point: int | None = None,
    giveaway: bool | None = None,
    offset: Annotated[int, Query(ge=0, le=10_000)] = 0,
) -> ListingPageOut:
    """Approved listings, newest first. Owners who were blocked disappear with their listings."""
    query = (
        select(Listing)
        .outerjoin(User, User.id == Listing.owner_id)
        .where(
            Listing.status == ListingStatus.APPROVED,
            or_(User.id.is_(None), User.is_blocked.is_(False)),
        )
    )
    if kind is not None:
        query = query.where(Listing.kind == kind)
    if point is not None:
        query = query.where(Listing.pickup_point_id == point)
    if giveaway is not None:
        query = query.where(Listing.giveaway.is_(giveaway))
    rows = (
        await session.scalars(
            query.order_by(Listing.published_at.desc().nulls_last(), Listing.id.desc())
            .offset(offset)
            .limit(PAGE_SIZE + 1)
        )
    ).all()
    page = rows[:PAGE_SIZE]
    ids = [listing.id for listing in page]
    covers = await first_photos(session, ids)
    liked = set(
        (
            await session.scalars(
                select(ListingLike.listing_id).where(
                    ListingLike.user_id == user.id, ListingLike.listing_id.in_(ids)
                )
            )
        ).all()
    )
    items = [
        ListingCardOut(
            id=listing.id,
            kind=listing.kind,
            title=listing.title,
            category=listing.category,
            thumb_url=photo_url(settings.jwt_secret, covers[listing.id], "thumb", "p")
            if listing.id in covers
            else None,
            likes=listing.likes_count,
            liked=listing.id in liked,
            giveaway=listing.giveaway,
            ready_at_point=listing.stored_at_point,
            pickup_point_id=listing.pickup_point_id,
        )
        for listing in page
    ]
    return ListingPageOut(
        items=items, next_offset=offset + PAGE_SIZE if len(rows) > PAGE_SIZE else None
    )


@router.get("/mine")
async def my_listings(
    user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> list[MyListingOut]:
    listings = (
        await session.scalars(
            select(Listing).where(Listing.owner_id == user.id).order_by(Listing.id.desc())
        )
    ).all()
    ids = [listing.id for listing in listings]
    covers = await first_photos(session, ids)
    waiting = dict(
        (
            await session.execute(
                select(ListingRequest.listing_id, func.count())
                .where(
                    ListingRequest.listing_id.in_(ids),
                    ListingRequest.status == RequestStatus.PENDING,
                )
                .group_by(ListingRequest.listing_id)
            )
        ).all()
    )
    handovers = dict(
        (
            await session.execute(
                select(ListingRequest.listing_id, ListingRequest.status).where(
                    ListingRequest.listing_id.in_(ids), ListingRequest.status.in_(HANDOVER)
                )
            )
        ).all()
    )
    return [
        MyListingOut(
            id=listing.id,
            kind=listing.kind,
            title=listing.title,
            status=listing.status,
            thumb_url=photo_url(settings.jwt_secret, covers[listing.id], "thumb", "o")
            if listing.id in covers
            else None,
            likes=listing.likes_count,
            waiting_requests=waiting.get(listing.id, 0),
            handover_status=handovers.get(listing.id),
            ready_at_point=listing.stored_at_point,
            created_at=listing.created_at,
        )
        for listing in listings
    ]


@router.get("/requests")
async def my_requests(
    user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> list[MyRequestOut]:
    """Things this user asked for, the newest first."""
    rows = (
        await session.execute(
            select(ListingRequest, Listing)
            .join(Listing, Listing.id == ListingRequest.listing_id)
            .where(ListingRequest.requester_id == user.id)
            .order_by(ListingRequest.id.desc())
            .limit(50)
        )
    ).all()
    covers = await first_photos(session, [listing.id for _, listing in rows])
    result = []
    for request, listing in rows:
        point = (
            await session.get(PickupPoint, listing.pickup_point_id)
            if listing.pickup_point_id
            else None
        )
        result.append(
            MyRequestOut(
                id=request.id,
                status=request.status,
                listing_id=listing.id,
                title=listing.title,
                thumb_url=photo_url(settings.jwt_secret, covers[listing.id], "thumb", "o")
                if listing.id in covers
                else None,
                code=request.pick_code if request.status == RequestStatus.AT_POINT else None,
                deadline=deadline_of(request),
                point=point_out(point),
                created_at=request.created_at,
            )
        )
    return result


@router.get("/{listing_id}")
async def get_listing(
    listing_id: int, user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> ListingOut:
    listing, mine = await visible_listing(session, listing_id, user)
    return await listing_out(session, settings.jwt_secret, listing, user, mine)


# ------------------------------------------------------------------- listing


@router.post("/photos", status_code=status.HTTP_201_CREATED)
async def upload_photo(
    request: Request, user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> PhotoOut:
    """One photo as the request body (image/jpeg, png or webp). Saved with a listing later."""
    if request.headers.get("content-type", "").split(";")[0].strip() not in IMAGE_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "photo_format")
    if not upload_limit.allow(user.id):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_uploads")
    loose = await session.scalar(
        select(func.count()).where(
            ListingPhoto.owner_id == user.id, ListingPhoto.listing_id.is_(None)
        )
    )
    if loose >= MAX_LOOSE_PHOTOS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_uploads")
    data = bytearray()
    async for chunk in request.stream():
        data += chunk
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "photo_too_large")
    try:
        photo = await run_in_threadpool(clean_photo, bytes(data))
    except PhotoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, exc.code) from exc
    row = ListingPhoto(
        owner_id=user.id,
        width=photo.width,
        height=photo.height,
        full=photo.full,
        thumb=photo.thumb,
    )
    session.add(row)
    await session.commit()
    return photo_out(settings.jwt_secret, row, "o")


async def check_values(session: AsyncSession, body: ListingIn) -> tuple[bool, str | None]:
    """Category, condition and handover point as the listing kind needs them."""
    if body.kind == ListingKind.HANDMADE:
        if await session.scalar(select(Category.id).where(Category.code == body.category)) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "bad_category")
        giveaway, condition = body.giveaway, None
    else:
        if body.category not in ITEM_TYPES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "bad_category")
        if body.condition is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "condition_required")
        # Unneeded things are listed to be given away.
        giveaway, condition = True, body.condition
    if giveaway:
        await published_point(session, body.pickup_point_id)
    try:
        await check_text(session, body.title, body.description)
    except MarketError as exc:
        raise fail(exc) from exc
    return giveaway, condition


async def attach_photos(
    session: AsyncSession, listing: Listing, user: User, photo_ids: list[int]
) -> None:
    """Exactly these photos, in this order. Removed ones are deleted."""
    if len(set(photo_ids)) != len(photo_ids) or len(photo_ids) > MAX_PHOTOS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "bad_photos")
    allowed = or_(
        and_(ListingPhoto.owner_id == user.id, ListingPhoto.listing_id.is_(None)),
        ListingPhoto.listing_id == listing.id,
    )
    photos = {
        p.id: p
        for p in (
            await session.scalars(
                select(ListingPhoto).where(ListingPhoto.id.in_(photo_ids), allowed)
            )
        ).all()
    }
    if len(photos) != len(photo_ids):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "bad_photos")
    await session.execute(
        delete(ListingPhoto).where(
            ListingPhoto.listing_id == listing.id, ListingPhoto.id.not_in(photo_ids)
        )
    )
    for position, photo_id in enumerate(photo_ids):
        photos[photo_id].listing_id = listing.id
        photos[photo_id].position = position


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_listing(
    body: ListingIn, user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> ListingOut:
    """A new listing waits for a moderator; nobody else sees it before that."""
    require_nickname(user)
    pending = await session.scalar(
        select(func.count()).where(
            Listing.owner_id == user.id, Listing.status == ListingStatus.PENDING
        )
    )
    if pending >= MAX_PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "too_many_pending")
    day_start = (
        timeutil.utc_now().astimezone(TASHKENT).replace(hour=0, minute=0, second=0, microsecond=0)
    )
    today = await session.scalar(
        select(func.count()).where(Listing.owner_id == user.id, Listing.created_at >= day_start)
    )
    if today >= MAX_NEW_PER_DAY:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_today")
    giveaway, condition = await check_values(session, body)
    listing = Listing(
        owner_id=user.id,
        kind=body.kind,
        title=body.title,
        description=body.description,
        category=body.category,
        condition=condition,
        giveaway=giveaway,
        pickup_point_id=body.pickup_point_id if giveaway else None,
        status=ListingStatus.PENDING,
        submitted_at=timeutil.utc_now(),
    )
    session.add(listing)
    await session.flush()
    await attach_photos(session, listing, user, body.photo_ids)
    track(session, user, "listing_submit", kind=body.kind.value)
    await session.commit()
    await session.refresh(listing)
    return await listing_out(session, settings.jwt_secret, listing, user, None)


@router.put("/{listing_id}")
async def update_listing(
    listing_id: int, body: ListingIn, user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> ListingOut:
    """Any change goes back to a moderator before others see it again."""
    listing = await own_listing(session, listing_id, user)
    if listing.status not in EDITABLE:
        raise HTTPException(status.HTTP_409_CONFLICT, "listing_locked")
    giveaway, condition = await check_values(session, body)
    point_id = body.pickup_point_id if giveaway else None
    if listing.stored_at_point and (not giveaway or point_id != listing.pickup_point_id):
        # The item is at the point already: it stays offered there.
        raise HTTPException(status.HTTP_409_CONFLICT, "item_at_point")
    await attach_photos(session, listing, user, body.photo_ids)
    listing.kind = body.kind
    listing.title = body.title
    listing.description = body.description
    listing.category = body.category
    listing.condition = condition
    listing.giveaway = giveaway
    listing.pickup_point_id = point_id
    listing.status = ListingStatus.PENDING
    listing.reject_reason = None
    listing.moderator_note = None
    listing.submitted_at = timeutil.utc_now()
    await session.commit()
    await session.refresh(listing)
    return await listing_out(session, settings.jwt_secret, listing, user, None)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: int,
    user: CurrentUser,
    session: SessionDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> Response:
    listing = await own_listing(session, listing_id, user)
    if listing.status not in (*EDITABLE, ListingStatus.GIVEN):
        raise HTTPException(status.HTTP_409_CONFLICT, "listing_locked")
    if listing.stored_at_point:
        raise HTTPException(status.HTTP_409_CONFLICT, "item_at_point")
    notes = await notes_for_decline(session, listing, "market_withdrawn")
    await session.delete(listing)
    await session.commit()
    background.add_task(deliver, bot, notes)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------ likes, reports


async def public_listing(session: AsyncSession, listing_id: int, user: User) -> Listing:
    listing, _ = await visible_listing(session, listing_id, user)
    if listing.status != ListingStatus.APPROVED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "listing_not_found")
    if listing.owner_id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "own_listing")
    return listing


@router.post("/{listing_id}/like")
async def like(listing_id: int, user: CurrentUser, session: SessionDep) -> LikeOut:
    """«Zo'r!» — no points, just a thumbs-up for the maker."""
    listing = await public_listing(session, listing_id, user)
    added = await session.scalar(
        insert(ListingLike)
        .values(listing_id=listing.id, user_id=user.id)
        .on_conflict_do_nothing()
        .returning(ListingLike.user_id)
    )
    if added is not None:
        listing.likes_count += 1
        track(session, user, "listing_like")
    await session.commit()
    return LikeOut(likes=listing.likes_count, liked=True)


@router.delete("/{listing_id}/like")
async def unlike(listing_id: int, user: CurrentUser, session: SessionDep) -> LikeOut:
    listing = await public_listing(session, listing_id, user)
    result = await session.execute(
        delete(ListingLike).where(
            ListingLike.listing_id == listing.id, ListingLike.user_id == user.id
        )
    )
    if result.rowcount:
        listing.likes_count = max(0, listing.likes_count - 1)
    await session.commit()
    return LikeOut(likes=listing.likes_count, liked=False)


@router.post("/{listing_id}/report", status_code=status.HTTP_201_CREATED)
async def report(
    listing_id: int,
    body: ListingReportIn,
    user: CurrentUser,
    session: SessionDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> dict:
    """Enough reports from different people take the listing down until a moderator decides."""
    listing = await public_listing(session, listing_id, user)
    already = await session.scalar(
        select(ListingReport.id).where(
            ListingReport.listing_id == listing.id,
            ListingReport.reporter_id == user.id,
            ListingReport.status == ReportStatus.OPEN,
        )
    )
    notes: list[Note] = []
    if already is None:
        session.add(ListingReport(listing_id=listing.id, reporter_id=user.id, reason=body.reason))
        await session.flush()
        reporters = await session.scalar(
            select(func.count(func.distinct(ListingReport.reporter_id))).where(
                ListingReport.listing_id == listing.id, ListingReport.status == ReportStatus.OPEN
            )
        )
        if reporters >= REPORTS_TO_HIDE:
            listing.status = ListingStatus.HIDDEN
            notes += await notes_for_decline(session, listing, "market_withdrawn")
            owner = await session.get(User, listing.owner_id) if listing.owner_id else None
            notes += note(owner, "market_hidden", title=listing.title, reason="reports")
        await session.commit()
    background.add_task(deliver, bot, notes)
    return {"ok": True}


# ------------------------------------------------------------------ requests


@router.post("/{listing_id}/request")
async def ask_for(
    listing_id: int,
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> ListingOut:
    """«Olmoqchiman». An item already waiting at the point goes to the first one who asks."""
    require_nickname(user)
    listing = await public_listing(session, listing_id, user)
    if not listing.giveaway:
        raise HTTPException(status.HTTP_409_CONFLICT, "not_given_away")
    point = await published_point(session, listing.pickup_point_id)
    existing = await latest_request(session, listing.id, user.id)
    if existing is not None and existing.status in OPEN_REQUEST:
        raise HTTPException(status.HTTP_409_CONFLICT, "already_requested")
    mine = await session.scalar(
        select(func.count()).where(
            ListingRequest.requester_id == user.id, ListingRequest.status.in_(OPEN_REQUEST)
        )
    )
    if mine >= MAX_OPEN_REQUESTS:
        raise HTTPException(status.HTTP_409_CONFLICT, "too_many_requests")
    request = ListingRequest(
        listing_id=listing.id, requester_id=user.id, status=RequestStatus.PENDING
    )
    session.add(request)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "already_requested") from exc
    track(session, user, "listing_request")
    notes: list[Note] = []
    owner = await session.get(User, listing.owner_id) if listing.owner_id else None
    if listing.stored_at_point:
        notes += await start_handover(session, listing, request, point.id)
    else:
        notes += note(owner, "market_new_request", title=listing.title, name=user.nickname or "")
    await session.commit()
    background.add_task(deliver, bot, notes)
    listing, mine_now = await visible_listing(session, listing.id, user)
    return await listing_out(session, settings.jwt_secret, listing, user, mine_now)


async def start_handover(
    session: AsyncSession, listing: Listing, request: ListingRequest, point_id: int
) -> list[Note]:
    """The owner agreed (or the item already waits at the point): codes and messages."""
    now = timeutil.utc_now()
    requester = await session.get(User, request.requester_id)
    owner = await session.get(User, listing.owner_id) if listing.owner_id else None
    drop_code, pick_code = await new_codes(session, point_id, 2)
    request.decided_at = now
    request.pick_code = pick_code
    notes: list[Note] = []
    if listing.stored_at_point:
        request.status = RequestStatus.AT_POINT
        request.dropped_at = now
        listing.status = ListingStatus.AT_POINT
        listing.stored_at_point = False
        where, hours = await point_text(session, point_id, requester.language)
        notes += note(
            requester,
            "market_ready",
            title=listing.title,
            point=where,
            hours=hours,
            code=pick_code,
            days=PICK_UP_DAYS,
        )
    else:
        request.status = RequestStatus.ACCEPTED
        request.drop_code = drop_code
        listing.status = ListingStatus.RESERVED
        notes += note(requester, "market_accepted", title=listing.title)
        if owner is not None:
            where, hours = await point_text(session, point_id, owner.language)
            notes += note(
                owner,
                "market_bring",
                title=listing.title,
                point=where,
                hours=hours,
                code=drop_code,
                days=DROP_OFF_DAYS,
            )
    await session.flush()
    notes += await notes_for_decline(session, listing, "market_declined")
    return notes


async def owner_request(
    session: AsyncSession, request_id: int, user: User
) -> tuple[ListingRequest, Listing]:
    row = (
        await session.execute(
            select(ListingRequest, Listing)
            .join(Listing, Listing.id == ListingRequest.listing_id)
            .where(ListingRequest.id == request_id, Listing.owner_id == user.id)
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "request_not_found")
    return row[0], row[1]


@router.post("/requests/{request_id}/accept")
async def accept(
    request_id: int,
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> ListingOut:
    request, listing = await owner_request(session, request_id, user)
    if request.status != RequestStatus.PENDING or listing.status != ListingStatus.APPROVED:
        raise HTTPException(status.HTTP_409_CONFLICT, "request_closed")
    point = await published_point(session, listing.pickup_point_id)
    notes = await start_handover(session, listing, request, point.id)
    await session.commit()
    background.add_task(deliver, bot, notes)
    return await listing_out(session, settings.jwt_secret, listing, user, None)


@router.post("/requests/{request_id}/decline")
async def decline(
    request_id: int,
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> ListingOut:
    request, listing = await owner_request(session, request_id, user)
    if request.status != RequestStatus.PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "request_closed")
    request.status = RequestStatus.DECLINED
    request.decided_at = timeutil.utc_now()
    notes = note(
        await session.get(User, request.requester_id), "market_declined", title=listing.title
    )
    await session.commit()
    background.add_task(deliver, bot, notes)
    return await listing_out(session, settings.jwt_secret, listing, user, None)


@router.post("/{listing_id}/cancel")
async def cancel_handover(
    listing_id: int,
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> ListingOut:
    """The owner changed their mind before bringing the item to the point."""
    listing = await own_listing(session, listing_id, user)
    request = await handover_of(session, listing.id)
    if request is None or request.status != RequestStatus.ACCEPTED:
        raise HTTPException(status.HTTP_409_CONFLICT, "item_at_point" if request else "no_handover")
    await end_handover(session, listing, request, RequestStatus.CANCELLED)
    notes = note(
        await session.get(User, request.requester_id), "market_cancelled", title=listing.title
    )
    await session.commit()
    background.add_task(deliver, bot, notes)
    return await listing_out(session, settings.jwt_secret, listing, user, None)


@router.delete("/{listing_id}/request")
async def withdraw_request(
    listing_id: int,
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    bot: BotDep,
    background: BackgroundTasks,
) -> ListingOut:
    """The requester no longer wants it; an item already at the point waits for someone else."""
    listing, mine = await visible_listing(session, listing_id, user)
    if mine is None or mine.status not in OPEN_REQUEST:
        raise HTTPException(status.HTTP_409_CONFLICT, "request_closed")
    notes: list[Note] = []
    if mine.status == RequestStatus.PENDING:
        mine.status = RequestStatus.CANCELLED
        mine.decided_at = timeutil.utc_now()
    else:
        await end_handover(session, listing, mine, RequestStatus.CANCELLED)
        owner = await session.get(User, listing.owner_id) if listing.owner_id else None
        notes += note(owner, "market_requester_left", title=listing.title)
    await session.commit()
    background.add_task(deliver, bot, notes)
    return await listing_out(session, settings.jwt_secret, listing, user, mine)
