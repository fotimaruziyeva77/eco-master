import uuid
from datetime import date

import pytest
from sqlalchemy import select, update

from app.api.content import tip_of_the_day
from app.models import ContentStatus, Project, Tip, TipSchedule
from app.seed import seed_categories, seed_demo
from tests.conftest import login


@pytest.fixture
async def headers(client, session):
    await seed_categories(session)
    await seed_demo(session)
    await session.commit()
    body = await login(client, telegram_id=800)
    return {"Authorization": f"Bearer {body['token']}"}


async def test_categories_follow_tz_list(client, headers):
    r = await client.get("/api/categories", headers=headers)
    codes = [c["code"] for c in r.json()]
    assert codes == ["plastic", "glass", "paper", "textile", "organic", "metal", "hazardous"]
    by_code = {c["code"]: c for c in r.json()}
    assert by_code["plastic"]["project_count"] == 1
    assert by_code["metal"]["has_projects"] is False
    assert by_code["textile"]["is_game_bin"] is False


async def test_home_shows_project_categories_and_a_tip(client, headers):
    r = await client.get("/api/home", headers=headers)
    body = r.json()
    assert [c["code"] for c in body["categories"]] == [
        "plastic",
        "glass",
        "paper",
        "textile",
        "organic",
    ]
    assert set(body["tip"]["text"]) == {"uz", "ru", "en"}
    assert body["user"]["level"] == {"code": "seed", "min_points": 0, "next_min_points": 100}


async def test_only_published_projects_are_visible(client, headers, session):
    await session.execute(
        update(Project)
        .where(Project.slug == "cardboard-pencil-holder")
        .values(status=ContentStatus.DRAFT)
    )
    await session.commit()

    r = await client.get("/api/categories/paper", headers=headers)
    assert r.json()["projects"] == []
    r = await client.get("/api/projects/cardboard-pencil-holder", headers=headers)
    assert r.status_code == 404


async def test_project_detail(client, headers):
    r = await client.get("/api/projects/plastic-bottle-flower-pot", headers=headers)
    body = r.json()
    assert body["safety_level"] == "yellow"
    assert body["safety_text"]["uz"]
    assert len(body["steps"]["ru"]) == len(body["steps"]["uz"]) == len(body["steps"]["en"])
    assert body["done"] is False


async def test_project_done_awards_points_once(client, headers):
    # QM-06: the second "done" gives nothing; a retried request is written once.
    url = "/api/projects/dry-leaves-compost/done"
    event = str(uuid.uuid4())
    first = await client.post(url, json={"client_event_id": event}, headers=headers)
    assert first.json() == {"awarded": True, "points": 15, "points_total": 15, "new_badges": []}

    retry = await client.post(url, json={"client_event_id": event}, headers=headers)
    assert retry.json() == {"awarded": False, "points": 0, "points_total": 15, "new_badges": []}

    again = await client.post(url, json={"client_event_id": str(uuid.uuid4())}, headers=headers)
    assert again.json() == {"awarded": False, "points": 0, "points_total": 15, "new_badges": []}

    detail = await client.get("/api/projects/dry-leaves-compost", headers=headers)
    assert detail.json()["done"] is True
    me = await client.get("/api/me", headers=headers)
    assert me.json()["points_total"] == 15


async def test_points_from_different_projects_add_up(client, headers):
    for slug in ("dry-leaves-compost", "cardboard-pencil-holder"):
        await client.post(
            f"/api/projects/{slug}/done",
            json={"client_event_id": str(uuid.uuid4())},
            headers=headers,
        )
    me = await client.get("/api/me", headers=headers)
    assert me.json()["points_total"] == 30


async def test_cards(client, headers):
    r = await client.get("/api/cards", headers=headers)
    assert [c["slug"] for c in r.json()] == ["plastic-pollution", "aral-sea"]
    card = await client.get("/api/cards/aral-sea", headers=headers)
    # JSONB does not keep key order; the Mini App shows sections in a fixed order.
    sections = card.json()["sections"]["uz"]
    assert set(sections) == {"problem", "cause", "effect", "solution", "action"}


async def test_tip_rotation_and_schedule(session, headers):
    day = date(2026, 10, 10)
    first = await tip_of_the_day(session, day)
    following = await tip_of_the_day(session, date(2026, 10, 11))
    assert first is not None and following is not None
    assert first.id != following.id

    scheduled = (await session.scalars(select(Tip).order_by(Tip.id.desc()))).first()
    session.add(TipSchedule(day=day, tip_id=scheduled.id))
    await session.commit()
    assert (await tip_of_the_day(session, day)).id == scheduled.id
