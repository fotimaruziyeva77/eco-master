"""Market photos behind signed, expiring links (app.media).

<img> tags can not send the session token, so the link itself carries the permission:
the API hands out links only to people who may see the photo.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from app.deps import SessionDep, SettingsDep
from app.media import Audience, Size, link_valid
from app.models import Listing, ListingPhoto, ListingStatus

router = APIRouter(tags=["media"])


@router.get("/media/{photo_id}/{size}", response_class=Response)
async def photo(
    photo_id: int,
    size: Size,
    session: SessionDep,
    settings: SettingsDep,
    a: Audience,
    e: int,
    s: Annotated[str, Query(max_length=64)],
) -> Response:
    if not link_valid(settings.jwt_secret, photo_id, size, a, e, s):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "bad_link")
    column = ListingPhoto.full if size == "full" else ListingPhoto.thumb
    row = (
        await session.execute(
            select(column, Listing.status)
            .outerjoin(Listing, Listing.id == ListingPhoto.listing_id)
            .where(ListingPhoto.id == photo_id)
        )
    ).first()
    # A public link stops working as soon as the listing leaves the market.
    if row is None or (a == "p" and row[1] != ListingStatus.APPROVED):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "photo_not_found")
    return Response(
        content=row[0],
        media_type="image/webp",
        headers={"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"},
    )
