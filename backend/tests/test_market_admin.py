"""Market moderation and the handover desk (phase 9)."""

import pytest
from sqlalchemy import select, update

from app.deps import bot_dep
from app.main import app
from app.models import (
    AdminAuditLog,
    AdminRole,
    Listing,
    ListingRequest,
    ListingStatus,
    PickupPoint,
    RequestStatus,
)
from tests.admin_helpers import PASSWORD, make_admin, sign_in
from tests.market_helpers import child, market_setup, new_listing, set_status
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


async def staff(client, session, point_id: int, login: str = "desk") -> None:
    admin = await make_admin(session, login=login, role=AdminRole.POINT, name="Desk")
    admin.pickup_point_id = point_id
    await session.commit()
    await sign_in(client, session, login=login)


async def test_editor_reviews_listings(client, session, point, bot):
    owner, _ = await child(client, 1, "Maker_One")
    first = await new_listing(client, owner, None, title="Karton ayiq")
    second = await new_listing(client, owner, point.id, title="Tugmali oqqush")
    await make_admin(session, login="editor", role=AdminRole.EDITOR)
    await sign_in(client, session, login="editor")

    queue = (await client.get("/api/admin/market?filter=pending")).json()
    assert [row["title"] for row in queue] == ["Karton ayiq", "Tugmali oqqush"]  # oldest first
    assert (await client.get("/api/admin/market/counts")).json() == {"pending": 2, "reported": 0}
    detail = (await client.get(f"/api/admin/market/{first['id']}")).json()
    assert detail["owner_nickname"] == "Maker_One" and len(detail["photos"]) == 1
    assert (await client.get(detail["photos"][0]["url"])).status_code == 200

    approved = (await client.post(f"/api/admin/market/{first['id']}/approve")).json()
    assert approved["status"] == "approved" and approved["reviewed_by"] == "Boss"
    rejected = await client.post(
        f"/api/admin/market/{second['id']}/reject",
        json={"reason": "face", "note": "Rasmni yuzingizsiz qayta oling"},
    )
    assert rejected.json()["status"] == "rejected"
    messages = [text for chat, text in bot.messages if chat == 1]
    assert any("bozorga chiqdi" in m for m in messages)
    assert any("yuzi ko'rinib" in m and "yuzingizsiz" in m for m in messages)

    view = (await client.get(f"/api/market/{second['id']}", headers=owner)).json()
    assert view["reject_reason"] == "face" and view["moderator_note"]
    # Rejected or approved: deciding twice is refused.
    again = await client.post(f"/api/admin/market/{second['id']}/approve")
    assert again.json()["detail"] == "bad_transition"
    actions = (await session.scalars(select(AdminAuditLog.action))).all()
    assert {"market.approve", "market.reject"} <= set(actions)


async def test_hiding_calls_off_a_handover(client, session, point, bot):
    owner, _ = await child(client, 1, "Maker_One")
    kid, _ = await child(client, 2, "Kid_Two")
    listing = await new_listing(client, owner, point.id)
    await set_status(session, listing["id"], ListingStatus.APPROVED)
    await client.post(f"/api/market/{listing['id']}/request", headers=kid)
    request_id = (await client.get(f"/api/market/{listing['id']}", headers=owner)).json()[
        "requests"
    ][0]["id"]
    await client.post(f"/api/market/requests/{request_id}/accept", headers=owner)

    await make_admin(session)
    await sign_in(client, session)
    hidden = await client.post(
        f"/api/admin/market/{listing['id']}/hide", json={"reason": "forbidden", "note": None}
    )
    assert hidden.json()["status"] == "hidden"
    request = await session.get(ListingRequest, request_id)
    await session.refresh(request)
    assert request.status == RequestStatus.CANCELLED
    assert any("bekor qilindi" in text for chat, text in bot.messages if chat == 2)
    assert any("olib tashlandi" in text for chat, text in bot.messages if chat == 1)
    assert (await client.get(f"/api/market/{listing['id']}", headers=kid)).status_code == 404


async def test_point_staff_see_only_their_desk(client, session, point):
    other = PickupPoint(name={"uz": "Boshqa"}, address={"uz": "-"}, hours={"uz": "-"})
    session.add(other)
    await session.commit()
    await staff(client, session, point.id)

    assert (await client.get("/api/admin/content")).status_code == 403
    assert (await client.get("/api/admin/market")).status_code == 403
    assert (await client.get("/api/admin/users")).status_code == 403
    desk = (await client.get(f"/api/admin/handover?point_id={other.id}")).json()
    assert desk["point"]["id"] == point.id  # always their own point
    points = (await client.get("/api/admin/handover/points")).json()
    assert [p["id"] for p in points] == [point.id]


async def test_admin_creates_point_staff(client, session, point):
    await make_admin(session)
    await sign_in(client, session)
    body = {"login": "maktab12", "name": "Navbatchi", "role": "point", "password": PASSWORD}
    missing = await client.post("/api/admin/admins", json=body)
    assert missing.json()["detail"] == "point_required"
    created = await client.post("/api/admin/admins", json=body | {"pickup_point_id": point.id})
    assert created.status_code == 201 and created.json()["pickup_point_id"] == point.id
    # Administrators choose the point on the desk.
    assert (await client.get("/api/admin/handover")).json()["detail"] == "point_required"
    assert (await client.get(f"/api/admin/handover?point_id={point.id}")).status_code == 200


async def test_codes_work_only_at_their_point(client, session, point):
    other = PickupPoint(name={"uz": "Boshqa"}, address={"uz": "-"}, hours={"uz": "-"})
    session.add(other)
    await session.commit()
    owner, _ = await child(client, 1, "Maker_One")
    kid, _ = await child(client, 2, "Kid_Two")
    listing = await new_listing(client, owner, point.id)
    await set_status(session, listing["id"], ListingStatus.APPROVED)
    await client.post(f"/api/market/{listing['id']}/request", headers=kid)
    request_id = (await client.get(f"/api/market/{listing['id']}", headers=owner)).json()[
        "requests"
    ][0]["id"]
    accepted = (
        await client.post(f"/api/market/requests/{request_id}/accept", headers=owner)
    ).json()
    code = accepted["handover"]["code"]

    await staff(client, session, other.id, login="other-desk")
    assert (await client.post("/api/admin/handover/lookup", json={"code": code})).status_code == 404
    receive = await client.post(f"/api/admin/handover/{request_id}/receive", json={"code": code})
    assert receive.status_code == 404


async def test_stored_item_goes_back_to_its_owner(client, session, point):
    owner, _ = await child(client, 1, "Maker_One")
    listing = await new_listing(client, owner, point.id)
    await set_status(session, listing["id"], ListingStatus.APPROVED)
    await session.execute(
        update(Listing).where(Listing.id == listing["id"]).values(stored_at_point=True)
    )
    await session.commit()
    await staff(client, session, point.id)
    desk = (await client.get("/api/admin/handover")).json()
    assert [item["listing_id"] for item in desk["stored"]] == [listing["id"]]
    assert (
        await client.post(f"/api/admin/handover/stored/{listing['id']}/return")
    ).status_code == 200
    row = await session.get(Listing, listing["id"])
    await session.refresh(row)
    assert not row.stored_at_point and row.status == ListingStatus.APPROVED


async def test_handover_points_are_content(client, session):
    await make_admin(session)
    await sign_in(client, session)
    values = {
        "name": {"uz": "Eko-markaz", "ru": "Эко-центр", "en": ""},
        "address": {"uz": "Yunusobod 4", "ru": "Юнусабад 4", "en": "Yunusabad 4"},
        "hours": {"uz": "Har kuni 10–18", "ru": "Ежедневно 10–18", "en": "Daily 10–18"},
        "sort_order": 0,
    }
    created = (
        await client.post("/api/admin/content/pickup-points", json={"values": values})
    ).json()
    blocked = await client.post(
        f"/api/admin/content/pickup-points/{created['id']}/status", json={"status": "published"}
    )
    assert blocked.json()["detail"]["code"] == "publish_blocked"  # English name missing
    values["name"]["en"] = "Eco centre"
    await client.put(f"/api/admin/content/pickup-points/{created['id']}", json={"values": values})
    published = await client.post(
        f"/api/admin/content/pickup-points/{created['id']}/status", json={"status": "published"}
    )
    assert published.json()["status"] == "published"
