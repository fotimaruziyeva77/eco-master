from datetime import timedelta

import pytest
from sqlalchemy import select

from app.daily import task_of_the_day
from app.models import AdminAuditLog, DailyTask, Question, TeacherLesson
from app.seed import seed_badges, seed_categories, seed_demo
from app.timeutil import local_today
from tests.admin_helpers import admin_client
from tests.conftest import login

ALL = ("uz", "ru", "en")


def i18n(text: str) -> dict:
    return {lang: f"{text} {lang}" for lang in ALL}


def i18n_list(*items: str) -> dict:
    return {lang: [f"{item} {lang}" for item in items] for lang in ALL}


@pytest.fixture
async def admin(client, session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_demo(session)
    await session.commit()
    return await admin_client(client, session)


def project_values(**overrides) -> dict:
    values = {
        "slug": "bottle-feeder",
        "category": "plastic",
        "title": i18n("Qush oxuri"),
        "difficulty": "easy",
        "safety_level": "green",
        "duration_min": 25,
        "materials": i18n_list("Butilka", "Ip"),
        "steps": i18n_list("Kesing", "Osing"),
        "safety_text": {"uz": "", "ru": "", "en": ""},
        "video_url": None,
        "poster_url": None,
        "tested_by": "Aziza",
        "tested_at": "2026-10-01",
        "sort_order": 10,
    }
    return values | overrides


async def test_types_and_form_description(admin):
    types = (await admin.get("/api/admin/content")).json()
    keys = [t["key"] for t in types]
    assert keys == [
        "projects",
        "questions",
        "game-items",
        "daily-tasks",
        "tips",
        "cards",
        "lessons",
        "categories",
    ]
    projects = next(t for t in types if t["key"] == "projects")
    assert projects["counts"]["published"] == 3

    meta = (await admin.get("/api/admin/content/projects/meta")).json()
    category = next(f for f in meta["fields"] if f["name"] == "category")
    codes = {o["value"] for o in category["options"]}
    assert "plastic" in codes and "metal" not in codes  # only waste types with projects
    slug = next(f for f in meta["fields"] if f["name"] == "slug")
    assert slug["fixed"] is True


async def test_publish_needs_three_languages_safety_text_and_testing(admin, client):
    # QM-14: incomplete content can not be published.
    draft = project_values(
        title={"uz": "Qush oxuri", "ru": "", "en": ""},
        safety_level="yellow",
        tested_by=None,
        tested_at=None,
    )
    created = await admin.post("/api/admin/content/projects", json={"values": draft})
    assert created.status_code == 201
    item = created.json()
    assert item["status"] == "draft"
    messages = [i["message"] for i in item["issues"] if i["level"] == "error"]
    assert any("rus tilida yo'q" in m for m in messages)
    assert any("xavfsizlik matni" in m for m in messages)
    assert any("sinab ko'rilmagan" in m for m in messages)

    url = f"/api/admin/content/projects/{item['id']}"
    blocked = await admin.post(f"{url}/status", json={"status": "published"})
    assert blocked.status_code == 422
    assert blocked.json()["detail"]["code"] == "publish_blocked"

    fixed = project_values(safety_level="yellow", safety_text=i18n("Qaychi bilan ehtiyot bo'ling"))
    assert (await admin.put(url, json={"values": fixed})).status_code == 200
    review = await admin.post(f"{url}/status", json={"status": "review"})
    assert review.json()["status"] == "review"
    published = await admin.post(f"{url}/status", json={"status": "published"})
    assert published.json()["status"] == "published"
    assert [i["level"] for i in published.json()["issues"]] == ["warning"]  # no video yet

    # Live in the Mini App right away.
    body = await login(client, telegram_id=7001)
    headers = {"Authorization": f"Bearer {body['token']}"}
    project = (await client.get("/api/projects/bottle-feeder", headers=headers)).json()
    assert project["title"]["ru"] == "Qush oxuri ru"
    assert project["safety_level"] == "yellow"


async def test_published_item_stays_valid_and_keeps_its_slug(admin):
    created = (
        await admin.post("/api/admin/content/projects", json={"values": project_values()})
    ).json()
    url = f"/api/admin/content/projects/{created['id']}"
    await admin.post(f"{url}/status", json={"status": "published"})

    broken = project_values(title={"uz": "Qush oxuri", "ru": "", "en": "Feeder"})
    r = await admin.put(url, json={"values": broken})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "publish_blocked"

    renamed = await admin.put(url, json={"values": project_values(slug="new-slug")})
    assert renamed.status_code == 422
    assert "slug" in renamed.json()["detail"]["errors"]


async def test_field_validation(admin):
    bad = project_values(
        slug="Bad Slug", video_url="http://plain.example", duration_min=0, category="metal"
    )
    r = await admin.post("/api/admin/content/projects", json={"values": bad})
    assert r.status_code == 422
    errors = r.json()["detail"]["errors"]
    assert set(errors) == {"slug", "video_url", "duration_min", "category"}

    taken = await admin.post(
        "/api/admin/content/projects", json={"values": project_values(slug="dry-leaves-compost")}
    )
    assert taken.status_code == 409


async def test_question_rules(admin, session):
    values = {
        "category": None,
        "text": i18n("Qaysi biri qayta ishlanadi?"),
        "options": {
            "uz": ["Shisha", "Tosh"],
            "ru": ["Стекло", "Камень", "Песок"],
            "en": ["Glass", "Stone"],
        },
        "correct_answer": 3,
        "explanation": i18n("Shisha qayta ishlanadi"),
        "image_url": None,
        "sort_order": 1,
    }
    item = (await admin.post("/api/admin/content/questions", json={"values": values})).json()
    errors = [i["message"] for i in item["issues"] if i["level"] == "error"]
    assert any("bir xil" in m for m in errors)
    assert any("To'g'ri javob" in m for m in errors)

    values["options"]["ru"] = ["Стекло", "Камень"]
    values["correct_answer"] = 1
    url = f"/api/admin/content/questions/{item['id']}"
    await admin.put(url, json={"values": values})
    published = await admin.post(f"{url}/status", json={"status": "published"})
    assert published.json()["status"] == "published"
    question = await session.get(Question, item["id"])
    assert question.correct_index == 0  # shown 1-based, stored 0-based
    assert question.category_id is None  # general ecology


async def test_lesson_parts_are_merged_into_the_body(admin, session):
    lesson = await session.scalar(
        select(TeacherLesson).where(TeacherLesson.slug == "plastic-and-us")
    )
    url = f"/api/admin/content/lessons/{lesson.id}"
    item = (await admin.get(url)).json()
    values = item["values"]
    assert sum(step["minutes"] for step in values["plan"]["ru"]) == 45
    values["goal"]["ru"] = "Новая цель урока"
    values["plan"]["en"] = values["plan"]["en"][:2]  # 25 minutes: allowed, but warned
    saved = (await admin.put(url, json={"values": values})).json()
    warnings = [i for i in saved["issues"] if i["level"] == "warning"]
    assert any("45" in w["message"] for w in warnings)

    await session.refresh(lesson)
    assert lesson.body["ru"]["goal"] == "Новая цель урока"
    assert lesson.body["ru"]["homework"]  # untouched parts survive
    pdf = await admin.get(f"/api/admin/content/lessons/{lesson.id}/pdf?lang=en")
    assert pdf.content.startswith(b"%PDF")


async def test_only_drafts_can_be_deleted(admin, session):
    published = await session.scalar(select(DailyTask.id).limit(1))
    r = await admin.delete(f"/api/admin/content/daily-tasks/{published}")
    assert r.status_code == 409
    draft = (
        await admin.post(
            "/api/admin/content/daily-tasks",
            json={"values": {"text": i18n("Vazifa"), "points": 20, "sort_order": 99}},
        )
    ).json()
    assert (await admin.delete(f"/api/admin/content/daily-tasks/{draft['id']}")).status_code == 204
    actions = (await session.scalars(select(AdminAuditLog.action))).all()
    assert actions == ["auth.login", "content.create", "content.delete"]


async def test_archived_content_leaves_the_app(admin, client):
    body = await login(client, telegram_id=7002)
    headers = {"Authorization": f"Bearer {body['token']}"}
    lessons = (await client.get("/api/lessons", headers=headers)).json()
    first = lessons[0]["slug"]
    rows = (await admin.get("/api/admin/content/lessons?q=" + first)).json()
    assert len(rows) == 1
    await admin.post(
        f"/api/admin/content/lessons/{rows[0]['id']}/status", json={"status": "archived"}
    )
    assert len((await client.get("/api/lessons", headers=headers)).json()) == len(lessons) - 1
    filtered = (await admin.get("/api/admin/content/lessons?status=archived")).json()
    assert [r["id"] for r in filtered] == [rows[0]["id"]]


async def test_category_code_is_fixed(admin):
    rows = (await admin.get("/api/admin/content/categories")).json()
    plastic = next(r for r in rows if r["subtitle"] == "plastic")
    url = f"/api/admin/content/categories/{plastic['id']}"
    values = (await admin.get(url)).json()["values"]
    values["name"]["en"] = "Plastics"
    assert (await admin.put(url, json={"values": values})).status_code == 200
    values["code"] = "plastics"
    assert (await admin.put(url, json={"values": values})).status_code == 422
    assert (await admin.delete(url)).status_code == 400


async def test_schedule_pins_a_task_to_a_date(admin, session):
    day = local_today() + timedelta(days=3)
    schedule = (await admin.get(f"/api/admin/schedule/daily?start={day}&days=7")).json()
    assert schedule["days"][0]["item_id"] is None
    assert schedule["days"][0]["auto_item_id"] == (await task_of_the_day(session, day)).id

    pick = schedule["items"][-1]["id"]
    r = await admin.put(f"/api/admin/schedule/daily/{day}", json={"item_id": pick})
    assert r.status_code == 204
    assert (await task_of_the_day(session, day)).id == pick

    await admin.put(f"/api/admin/schedule/daily/{day}", json={"item_id": None})
    assert (await task_of_the_day(session, day)).id == schedule["days"][0]["auto_item_id"]

    draft = (
        await admin.post(
            "/api/admin/content/daily-tasks",
            json={"values": {"text": i18n("Yangi"), "points": 20, "sort_order": 1}},
        )
    ).json()
    refused = await admin.put(f"/api/admin/schedule/daily/{day}", json={"item_id": draft["id"]})
    assert refused.status_code == 409
