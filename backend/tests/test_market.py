"""Market (phase 9): moderation first, no contacts, handover only through a point."""

import io
from datetime import timedelta

import pytest
from PIL import Image
from sqlalchemy import func, select, update

from app.config import get_settings
from app.deps import bot_dep
from app.main import app
from app.market import expire_handovers, remove_loose_photos
from app.media import photo_url
from app.models import (
    AdminRole,
    AdminUser,
    ContentStatus,
    Listing,
    ListingPhoto,
    ListingRequest,
    ListingStatus,
    PickupPoint,
    RequestStatus,
)
from app.timeutil import utc_now
from tests.admin_helpers import make_admin, sign_in
from tests.market_helpers import (
    GPS_TAG,
    child,
    jpeg,
    market_setup,
    new_listing,
    set_status,
    upload,
)
from tests.test_phase5 import FakeBot


@pytest.fixture
async def point(session):
    return await market_setup(session)


@pytest.fixture
def bot():
    fake = FakeBot()
    app.dependency_overrides[bot_dep] = lambda: fake
    yield fake
    app.dependency_overrides.pop(bot_dep, None)


def texts(bot: FakeBot, chat_id: int) -> list[str]:
    return [text for chat, text in bot.messages if chat == chat_id]


# ---------------------------------------------------------------------- photos


async def test_photo_keeps_only_pixels(client, session, point):
    """GPS and camera data never reach the database; the photo is turned upright."""
    headers, _ = await child(client, 1, "Maker_One")
    response = await upload(client, headers, jpeg(1600, 1000, orientation=6))
    assert response.status_code == 201, response.text
    body = response.json()
    assert max(body["width"], body["height"]) == 1280
    assert body["height"] > body["width"]  # orientation 6 = rotated a quarter turn

    stored = await session.scalar(select(ListingPhoto.full).where(ListingPhoto.id == body["id"]))
    image = Image.open(io.BytesIO(stored))
    assert image.format == "WEBP"
    assert "exif" not in image.info and not image.getexif()
    assert GPS_TAG not in image.getexif()


async def test_only_real_photos_are_accepted(client, point, monkeypatch):
    headers, _ = await child(client, 1, "Maker_One")
    assert (await upload(client, headers, b"not an image")).json()["detail"] == "photo_unreadable"
    assert (await upload(client, headers, jpeg(150, 150))).json()["detail"] == "photo_too_small"
    wrong_type = await upload(client, headers, jpeg(), content_type="application/pdf")
    assert wrong_type.status_code == 415
    monkeypatch.setattr("app.api.market.MAX_UPLOAD_BYTES", 1000)
    assert (await upload(client, headers)).status_code == 413


async def test_photo_links_are_signed_and_expire(client, session, point, monkeypatch):
    headers, _ = await child(client, 1, "Maker_One")
    photo = (await upload(client, headers)).json()
    assert (await client.get(photo["thumb_url"])).headers["content-type"] == "image/webp"
    assert (await client.get(photo["url"].replace("s=", "s=0"))).status_code == 403
    later = utc_now() + timedelta(hours=3)
    monkeypatch.setattr("app.timeutil.utc_now", lambda: later)
    assert (await client.get(photo["url"])).status_code == 403


# ------------------------------------------------------------------ moderation


async def test_new_listing_waits_for_a_moderator(client, session, point):
    owner, _ = await child(client, 1, "Maker_One")
    other, _ = await child(client, 2, "Viewer_Two")
    listing = await new_listing(client, owner, point.id)
    assert listing["status"] == "pending" and listing["is_mine"]

    assert (await client.get(f"/api/market/{listing['id']}", headers=other)).status_code == 404
    assert (await client.get("/api/market", headers=other)).json()["items"] == []
    # A public link for a photo that is not in the market does not work, even if guessed.
    secret = get_settings().jwt_secret
    public = photo_url(secret, listing["photos"][0]["id"], "thumb", "p")
    assert (await client.get(public)).status_code == 404

    await set_status(session, listing["id"], ListingStatus.APPROVED)
    page = (await client.get("/api/market", headers=other)).json()
    assert [item["id"] for item in page["items"]] == [listing["id"]]
    assert (await client.get(page["items"][0]["thumb_url"])).status_code == 200
    detail = (await client.get(f"/api/market/{listing['id']}", headers=other)).json()
    assert detail["owner_nickname"] == "Maker_One" and detail["can_request"]
    assert detail["reject_reason"] is None and detail["requests"] == []


async def test_contacts_and_rude_words_are_refused(client, point):
    headers, _ = await child(client, 1, "Maker_One")
    photo = (await upload(client, headers)).json()
    base = {"kind": "handmade", "category": "paper", "photo_ids": [photo["id"]]}
    for title, description, code in (
        ("Qo'g'irchoq", "Qo'ng'iroq qiling: +998 90 123-45-67", "contact_not_allowed"),
        ("Qo'g'irchoq", "Telegram: @maker_one_uz", "contact_not_allowed"),
        ("Qo'g'irchoq t.me/maker", "", "contact_not_allowed"),
        ("Shitty toy", "", "text_not_allowed"),
    ):
        response = await client.post(
            "/api/market", json=base | {"title": title, "description": description}, headers=headers
        )
        assert response.json()["detail"] == code, title
    ok = await client.post(
        "/api/market",
        json=base | {"title": "Gulli quti", "description": "2 ta karton, 30 sm"},
        headers=headers,
    )
    assert ok.status_code == 201


async def test_listing_rules(client, session, point):
    headers, _ = await child(client, 1, "Maker_One")
    other, _ = await child(client, 2, "Viewer_Two")
    photo = (await upload(client, headers)).json()
    stranger_photo = (await upload(client, other)).json()
    base = {"title": "Kitoblar", "photo_ids": [photo["id"]]}

    def post(**values):
        return client.post("/api/market", json=base | values, headers=headers)

    unneeded = {"kind": "unneeded", "category": "books", "pickup_point_id": point.id}
    assert (await post(**unneeded)).json()["detail"] == "condition_required"
    pets = unneeded | {"category": "pets"}
    assert (await post(**pets, condition="good")).json()["detail"] == "bad_category"
    assert (await post(**(unneeded | {"pickup_point_id": None}), condition="good")).json()[
        "detail"
    ] == "point_unavailable"
    draft = PickupPoint(name={"uz": "x"}, address={"uz": "x"}, hours={"uz": "x"})
    session.add(draft)
    await session.commit()
    assert (await post(**(unneeded | {"pickup_point_id": draft.id}), condition="good")).json()[
        "detail"
    ] == "point_unavailable"
    response = await post(
        kind="handmade", category="paper", photo_ids=[photo["id"], stranger_photo["id"]]
    )
    assert response.json()["detail"] == "bad_photos"

    created = await post(**unneeded, condition="good")
    assert created.status_code == 201
    # Unneeded things are always given away; handmade ones only when the maker wants.
    assert created.json()["giveaway"] is True


async def test_limits(client, point):
    headers, _ = await child(client, 1, "Maker_One")
    for _ in range(3):
        await new_listing(client, headers, None)
    photo = (await upload(client, headers)).json()
    fourth = await client.post(
        "/api/market",
        json={
            "kind": "handmade",
            "title": "Yana bitta",
            "category": "paper",
            "photo_ids": [photo["id"]],
        },
        headers=headers,
    )
    assert fourth.json()["detail"] == "too_many_pending"


async def test_changes_go_back_to_review(client, session, point):
    headers, _ = await child(client, 1, "Maker_One")
    listing = await new_listing(client, headers, None)
    await set_status(session, listing["id"], ListingStatus.APPROVED)
    old_photo = listing["photos"][0]["id"]
    new_photo = (await upload(client, headers)).json()["id"]
    body = {
        "kind": "handmade",
        "title": "Yangilangan nom",
        "category": "plastic",
        "photo_ids": [new_photo],
    }
    updated = (await client.put(f"/api/market/{listing['id']}", json=body, headers=headers)).json()
    assert updated["status"] == "pending" and updated["title"] == "Yangilangan nom"
    assert [p["id"] for p in updated["photos"]] == [new_photo]
    assert await session.get(ListingPhoto, old_photo) is None


async def test_likes(client, session, point):
    owner, _ = await child(client, 1, "Maker_One")
    fan, _ = await child(client, 2, "Fan_Two")
    listing = await new_listing(client, owner, None)
    await set_status(session, listing["id"], ListingStatus.APPROVED)
    url = f"/api/market/{listing['id']}/like"
    assert (await client.post(url, headers=owner)).json()["detail"] == "own_listing"
    assert (await client.post(url, headers=fan)).json() == {"likes": 1, "liked": True}
    assert (await client.post(url, headers=fan)).json() == {"likes": 1, "liked": True}
    assert (await client.delete(url, headers=fan)).json() == {"likes": 0, "liked": False}


async def test_reports_take_a_listing_down(client, session, point, bot):
    owner, owner_id = await child(client, 1, "Maker_One")
    listing = await new_listing(client, owner, None)
    await set_status(session, listing["id"], ListingStatus.APPROVED)
    url = f"/api/market/{listing['id']}/report"
    for i, nickname in enumerate(("Kid_Two", "Kid_Three"), start=2):
        reporter, _ = await child(client, i, nickname)
        await client.post(url, json={"reason": "rude"}, headers=reporter)
        await client.post(url, json={"reason": "rude"}, headers=reporter)  # counted once
    listing_row = await session.get(Listing, listing["id"])
    await session.refresh(listing_row)
    assert listing_row.status == ListingStatus.APPROVED
    third, _ = await child(client, 4, "Kid_Four")
    await client.post(url, json={"reason": "personal_info"}, headers=third)
    await session.refresh(listing_row)
    assert listing_row.status == ListingStatus.HIDDEN
    assert any("olib tashlandi" in text for text in texts(bot, 1))


# -------------------------------------------------------------------- handover


async def test_handover_through_the_point(client, session, point, bot):
    """Owner and requester never meet: each tells the staff their own code."""
    owner, _ = await child(client, 1, "Maker_One")
    kid_b, b_id = await child(client, 2, "Kid_Two")
    kid_c, _ = await child(client, 3, "Kid_Three")
    listing = await new_listing(client, owner, point.id)
    await set_status(session, listing["id"], ListingStatus.APPROVED)
    lid = listing["id"]

    await client.post(f"/api/market/{lid}/request", headers=kid_b)
    view_c = (await client.post(f"/api/market/{lid}/request", headers=kid_c)).json()
    assert view_c["my_request"] == "pending" and not view_c["can_request"]
    assert sum("olmoqchi" in text for text in texts(bot, 1)) == 2

    mine = (await client.get(f"/api/market/{lid}", headers=owner)).json()
    request_b = next(r for r in mine["requests"] if r["nickname"] == "Kid_Two")
    accepted = (
        await client.post(f"/api/market/requests/{request_b['id']}/accept", headers=owner)
    ).json()
    assert accepted["status"] == "reserved" and accepted["handover"]["status"] == "accepted"
    drop_code = accepted["handover"]["code"]
    assert len(drop_code) == 6
    assert any(drop_code in text for text in texts(bot, 1))  # «bring it» message
    assert any("boshqa bolaga" in text for text in texts(bot, 3))  # Kid_Three declined
    view_b = (await client.get(f"/api/market/{lid}", headers=kid_b)).json()
    assert view_b["handover"]["status"] == "accepted" and view_b["handover"]["code"] is None
    # Others no longer see it in the market.
    assert (await client.get(f"/api/market/{lid}", headers=kid_c)).status_code == 404

    staff = await make_admin(session, login="desk", role=AdminRole.POINT, name="Desk")
    staff.pickup_point_id = point.id
    await session.commit()
    await sign_in(client, session, login="desk")
    found = (await client.post("/api/admin/handover/lookup", json={"code": drop_code})).json()
    assert found["action"] == "receive" and found["item"]["title"] == listing["title"]
    wrong = await client.post(
        f"/api/admin/handover/{found['item']['request_id']}/receive", json={"code": "000000"}
    )
    assert wrong.json()["detail"] == "wrong_code"
    received = await client.post(
        f"/api/admin/handover/{found['item']['request_id']}/receive", json={"code": drop_code}
    )
    assert received.json()["status"] == "at_point"

    view_b = (await client.get(f"/api/market/{lid}", headers=kid_b)).json()
    pick_code = view_b["handover"]["code"]
    assert view_b["status"] == "at_point" and pick_code and pick_code != drop_code
    assert any(pick_code in text for text in texts(bot, 2))  # «come and collect it»
    found = (await client.post("/api/admin/handover/lookup", json={"code": pick_code})).json()
    assert found["action"] == "give"
    given = await client.post(
        f"/api/admin/handover/{found['item']['request_id']}/give", json={"code": pick_code}
    )
    assert given.json()["status"] == "done"
    assert any("yangi egasiga" in text for text in texts(bot, 1))
    assert (await client.get(f"/api/market/{lid}", headers=kid_b)).json()["status"] == "given"
    staff_row = await session.scalar(select(AdminUser).where(AdminUser.login == "desk"))
    assert staff_row.role == AdminRole.POINT


async def test_request_rules(client, session, point):
    owner, _ = await child(client, 1, "Maker_One")
    kid, _ = await child(client, 2, "Kid_Two")
    shown_only = await new_listing(client, owner, None)
    await set_status(session, shown_only["id"], ListingStatus.APPROVED)
    response = await client.post(f"/api/market/{shown_only['id']}/request", headers=kid)
    assert response.json()["detail"] == "not_given_away"

    ids = []
    for _ in range(3):
        listing = await new_listing(client, owner, point.id)
        await set_status(session, listing["id"], ListingStatus.APPROVED)
        ids.append(listing["id"])
    # The owner can make 3 pending listings at a time; approved ones do not count.
    fourth = await new_listing(client, owner, point.id)
    await set_status(session, fourth["id"], ListingStatus.APPROVED)

    assert (await client.post(f"/api/market/{ids[0]}/request", headers=owner)).json()[
        "detail"
    ] == "own_listing"
    for lid in ids:
        assert (await client.post(f"/api/market/{lid}/request", headers=kid)).status_code == 200
    again = await client.post(f"/api/market/{ids[0]}/request", headers=kid)
    assert again.json()["detail"] == "already_requested"
    too_many = await client.post(f"/api/market/{fourth['id']}/request", headers=kid)
    assert too_many.json()["detail"] == "too_many_requests"


async def test_item_left_at_the_point_goes_to_the_next_one(client, session, point, bot):
    owner, _ = await child(client, 1, "Maker_One")
    kid_b, _ = await child(client, 2, "Kid_Two")
    kid_c, _ = await child(client, 3, "Kid_Three")
    listing = await new_listing(client, owner, point.id)
    lid = listing["id"]
    await set_status(session, lid, ListingStatus.APPROVED)
    await client.post(f"/api/market/{lid}/request", headers=kid_b)
    request_id = (await client.get(f"/api/market/{lid}", headers=owner)).json()["requests"][0]["id"]
    await client.post(f"/api/market/requests/{request_id}/accept", headers=owner)

    # The owner may change their mind before bringing it; the item returns to the market.
    cancelled = (await client.post(f"/api/market/{lid}/cancel", headers=owner)).json()
    assert cancelled["status"] == "approved"
    assert any("bekor qilindi" in text for text in texts(bot, 2))

    await client.post(f"/api/market/{lid}/request", headers=kid_b)
    request_id = (await client.get(f"/api/market/{lid}", headers=owner)).json()["requests"][0]["id"]
    await client.post(f"/api/market/requests/{request_id}/accept", headers=owner)
    await session.execute(
        update(ListingRequest)
        .where(ListingRequest.id == request_id)
        .values(status=RequestStatus.AT_POINT, dropped_at=utc_now())
    )
    await set_status(session, lid, ListingStatus.AT_POINT)

    # Kid_Two no longer wants it: it waits at the point and goes to whoever asks next.
    left = (await client.delete(f"/api/market/{lid}/request", headers=kid_b)).json()
    assert left["status"] == "approved" and left["ready_at_point"]
    taken = (await client.post(f"/api/market/{lid}/request", headers=kid_c)).json()
    assert taken["status"] == "at_point" and taken["handover"]["code"]
    assert any(taken["handover"]["code"] in text for text in texts(bot, 3))


async def test_handovers_expire(client, session, point, bot):
    owner, _ = await child(client, 1, "Maker_One")
    kid, _ = await child(client, 2, "Kid_Two")
    listing = await new_listing(client, owner, point.id)
    lid = listing["id"]
    await set_status(session, lid, ListingStatus.APPROVED)
    await client.post(f"/api/market/{lid}/request", headers=kid)
    request_id = (await client.get(f"/api/market/{lid}", headers=owner)).json()["requests"][0]["id"]
    await client.post(f"/api/market/requests/{request_id}/accept", headers=owner)

    assert await expire_handovers(session, utc_now() + timedelta(days=6)) == []
    notes = await expire_handovers(session, utc_now() + timedelta(days=8))
    await session.commit()
    assert {n.key for n in notes} == {"market_expired"} and len(notes) == 2
    request = await session.get(ListingRequest, request_id)
    await session.refresh(request)
    assert request.status == RequestStatus.EXPIRED
    row = await session.get(Listing, lid)
    await session.refresh(row)
    assert row.status == ListingStatus.APPROVED and not row.stored_at_point


async def test_loose_photos_are_removed(client, session, point):
    headers, _ = await child(client, 1, "Maker_One")
    photo = (await upload(client, headers)).json()
    assert await remove_loose_photos(session, utc_now() + timedelta(hours=2)) == 0
    assert await remove_loose_photos(session, utc_now() + timedelta(days=2)) == 1
    await session.commit()
    assert await session.get(ListingPhoto, photo["id"]) is None


async def test_deleting_the_account(client, session, point):
    """Listings and photos go with the account; a handover under way still finishes."""
    owner, owner_id = await child(client, 1, "Maker_One")
    kid, _ = await child(client, 2, "Kid_Two")
    pending = await new_listing(client, owner, None)
    at_point = await new_listing(client, owner, point.id)
    await set_status(session, at_point["id"], ListingStatus.APPROVED)
    await client.post(f"/api/market/{at_point['id']}/request", headers=kid)
    request_id = (await client.get(f"/api/market/{at_point['id']}", headers=owner)).json()[
        "requests"
    ][0]["id"]
    await client.post(f"/api/market/requests/{request_id}/accept", headers=owner)
    await session.execute(
        update(ListingRequest)
        .where(ListingRequest.id == request_id)
        .values(status=RequestStatus.AT_POINT, dropped_at=utc_now())
    )
    await set_status(session, at_point["id"], ListingStatus.AT_POINT)

    assert (await client.delete("/api/me", headers=owner)).status_code == 204
    assert await session.get(Listing, pending["id"]) is None
    remaining = await session.scalar(
        select(func.count()).select_from(ListingPhoto).where(ListingPhoto.owner_id == owner_id)
    )
    assert remaining == 0
    kept = await session.get(Listing, at_point["id"])
    await session.refresh(kept)
    assert kept.owner_id is None and kept.status == ListingStatus.AT_POINT
    view = (await client.get(f"/api/market/{at_point['id']}", headers=kid)).json()
    assert view["handover"]["code"] and view["owner_nickname"] is None

    # A requester who leaves releases the item for the next one.
    await client.delete("/api/me", headers=kid)
    await session.refresh(kept)
    assert kept.status == ListingStatus.APPROVED and kept.stored_at_point


async def test_points_list(client, session, point):
    headers, _ = await child(client, 1, "Maker_One")
    session.add(
        PickupPoint(
            name={"uz": "Yopiq"},
            address={"uz": "-"},
            hours={"uz": "-"},
            status=ContentStatus.ARCHIVED,
        )
    )
    await session.commit()
    names = [
        p["name"]["uz"] for p in (await client.get("/api/market/points", headers=headers)).json()
    ]
    assert names == ["12-maktab eko-burchagi"]
