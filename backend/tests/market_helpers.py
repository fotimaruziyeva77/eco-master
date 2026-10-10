"""Helpers for market tests: photos, handover points, listings."""

import io

from PIL import Image
from sqlalchemy import update

from app.models import ContentStatus, Listing, ListingStatus, PickupPoint
from app.seed import seed_badges, seed_banned_words, seed_categories
from tests.test_phase4_api import onboard

GPS_TAG = 0x8825
ORIENTATION_TAG = 0x0112


def jpeg(width: int = 800, height: int = 600, *, gps: bool = True, orientation: int = 1) -> bytes:
    """A camera-like JPEG: with a GPS position and an orientation tag."""
    image = Image.new("RGB", (width, height), (40, 160, 90))
    exif = Image.Exif()
    exif[ORIENTATION_TAG] = orientation
    exif[0x010F] = "PhoneMaker"  # camera make
    if gps:
        exif[GPS_TAG] = {1: "N", 2: (41.0, 18.0, 0.0), 3: "E", 4: (69.0, 16.0, 0.0)}
    out = io.BytesIO()
    image.save(out, "JPEG", exif=exif, quality=90)
    return out.getvalue()


async def market_setup(session) -> PickupPoint:
    """Waste categories, badges, the word list and one published handover point."""
    await seed_categories(session)
    await seed_badges(session)
    await seed_banned_words(session)
    point = PickupPoint(
        name={"uz": "12-maktab eko-burchagi", "ru": "Эко-уголок школы 12", "en": "School 12"},
        address={"uz": "Chilonzor 5", "ru": "Чиланзар 5", "en": "Chilanzar 5"},
        hours={"uz": "Du–Ju 14:00–17:00", "ru": "Пн–Пт 14:00–17:00", "en": "Mon–Fri 2–5 pm"},
        status=ContentStatus.PUBLISHED,
    )
    session.add(point)
    await session.commit()
    return point


async def child(client, telegram_id: int, nickname: str) -> tuple[dict, int]:
    """An onboarded user who allowed the bot to write (market messages need that)."""
    headers, user_id = await onboard(client, telegram_id, nickname)
    await client.post("/api/me/write-access", json={"granted": True}, headers=headers)
    await client.patch("/api/me", json={"language": "uz"}, headers=headers)
    return headers, user_id


async def upload(
    client, headers: dict, data: bytes | None = None, content_type: str = "image/jpeg"
):
    return await client.post(
        "/api/market/photos",
        content=jpeg() if data is None else data,
        headers=headers | {"Content-Type": content_type},
    )


async def new_listing(client, headers: dict, point_id: int | None, **values) -> dict:
    photo = (await upload(client, headers)).json()
    body = {
        "kind": "handmade",
        "title": "Plastik butilkadan qushlar uyasi",
        "description": "Eski butilkadan yasadim.",
        "category": "plastic",
        "giveaway": point_id is not None,
        "pickup_point_id": point_id,
        "photo_ids": [photo["id"]],
    } | values
    response = await client.post("/api/market", json=body, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def set_status(session, listing_id: int, status: ListingStatus) -> None:
    await session.execute(
        update(Listing)
        .where(Listing.id == listing_id)
        .values(status=status, published_at=Listing.created_at)
    )
    await session.commit()
