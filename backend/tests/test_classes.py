"""Teachers' classes: codes, joining, the teacher's view, class tasks, leaving."""

import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.api import classes as classes_api
from app.models import AdminAuditLog, AdminRole, ClassMember, Project, SchoolClass, User
from app.seed import seed_badges, seed_banned_words, seed_categories, seed_demo
from app.timeutil import local_today
from tests.admin_helpers import admin_client
from tests.conftest import login


async def onboard(
    client, telegram_id: int, nickname: str, path: str = "student"
) -> tuple[dict, int]:
    body = await login(client, telegram_id=telegram_id)
    headers = {"Authorization": f"Bearer {body['token']}"}
    await client.post("/api/onboarding/path", json={"path": path}, headers=headers)
    await client.post("/api/onboarding/nickname", json={"nickname": nickname}, headers=headers)
    await client.post("/api/onboarding/complete", headers=headers)
    return headers, body["user"]["id"]


@pytest.fixture
async def content(session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_banned_words(session)
    await seed_demo(session)
    await session.commit()


@pytest.fixture
async def teacher(client, content):
    return await onboard(client, 500, "Ustoz_Nodira", "teacher")


async def make_class(client, teacher, name="7-B") -> dict:
    headers, _ = teacher
    r = await client.post("/api/classes", json={"name": name}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


async def first_project(session) -> Project:
    return await session.scalar(select(Project).where(Project.status == "published").limit(1))


async def test_only_teachers_make_classes(client, content):
    headers, _ = await onboard(client, 501, "Oddiy_Bola")
    r = await client.post("/api/classes", json={"name": "7-B"}, headers=headers)
    assert r.status_code == 403
    assert r.json()["detail"] == "teachers_only"


async def test_class_gets_a_code_and_a_link(client, teacher):
    made = await make_class(client, teacher, "  7-B   sinf ")
    assert made["name"] == "7-B sinf"
    assert len(made["code"]) == 6
    assert set(made["code"]) <= set(classes_api.CODE_ALPHABET)
    assert made["link"].endswith(f"?startapp=class_{made['code']}")
    listed = (await client.get("/api/classes", headers=teacher[0])).json()
    assert [c["id"] for c in listed] == [made["id"]]


async def test_class_names_are_checked(client, teacher):
    r = await client.post("/api/classes", json={"name": "call +998901234567"}, headers=teacher[0])
    assert r.status_code == 422
    assert r.json()["detail"] == "contact_not_allowed"


async def test_a_teacher_has_at_most_ten_classes(client, teacher, monkeypatch):
    monkeypatch.setattr(classes_api, "MAX_CLASSES", 2)
    await make_class(client, teacher, "A")
    await make_class(client, teacher, "B")
    r = await client.post("/api/classes", json={"name": "C"}, headers=teacher[0])
    assert r.status_code == 409


async def test_pupil_sees_the_class_before_joining_and_joins(client, teacher):
    made = await make_class(client, teacher)
    pupil, pupil_id = await onboard(client, 502, "Quvnoq_Bola")

    preview = (
        await client.get(f"/api/classes/preview/{made['code'].lower()}", headers=pupil)
    ).json()
    assert preview == {
        "name": "7-B",
        "teacher_nickname": "Ustoz_Nodira",
        "member_count": 0,
        "is_member": False,
    }

    joined = await client.post("/api/classes/join", json={"code": made["code"]}, headers=pupil)
    assert joined.status_code == 200, joined.text
    body = joined.json()
    assert body["name"] == "7-B"
    assert [m["user_id"] for m in body["members"]] == [pupil_id]
    assert body["members"][0]["is_me"] is True
    assert (await client.get("/api/my-class", headers=pupil)).json()["id"] == made["id"]


async def test_one_class_at_a_time(client, teacher, session):
    first = await make_class(client, teacher, "A")
    second = await make_class(client, teacher, "B")
    pupil, pupil_id = await onboard(client, 503, "Bola_Ikki")
    await client.post("/api/classes/join", json={"code": first["code"]}, headers=pupil)
    await client.post("/api/classes/join", json={"code": second["code"]}, headers=pupil)
    rows = (await session.scalars(select(ClassMember).where(ClassMember.user_id == pupil_id))).all()
    assert [r.class_id for r in rows] == [second["id"]]


async def test_teacher_can_not_join_own_class_and_full_classes_refuse(client, teacher, monkeypatch):
    made = await make_class(client, teacher)
    r = await client.post("/api/classes/join", json={"code": made["code"]}, headers=teacher[0])
    assert r.status_code == 409 and r.json()["detail"] == "own_class"

    monkeypatch.setattr(classes_api, "MAX_MEMBERS", 1)
    first, _ = await onboard(client, 504, "Birinchi_Bola")
    second, _ = await onboard(client, 505, "Ikkinchi_Bola")
    assert (
        await client.post("/api/classes/join", json={"code": made["code"]}, headers=first)
    ).status_code == 200
    r = await client.post("/api/classes/join", json={"code": made["code"]}, headers=second)
    assert r.status_code == 409 and r.json()["detail"] == "class_full"


async def test_guessing_codes_is_limited(client, teacher):
    pupil, _ = await onboard(client, 506, "Taxminchi")
    statuses = [
        (await client.get("/api/classes/preview/ZZZZZZ", headers=pupil)).status_code
        for _ in range(31)
    ]
    assert statuses[:30] == [404] * 30
    assert statuses[30] == 429


async def test_teacher_sees_members_with_points_and_tasks(client, teacher, session):
    made = await make_class(client, teacher)
    pupil, pupil_id = await onboard(client, 507, "Faol_Bola")
    lazy, lazy_id = await onboard(client, 508, "Dam_Oluvchi")
    for headers in (pupil, lazy):
        await client.post("/api/classes/join", json={"code": made["code"]}, headers=headers)
    project = await first_project(session)
    due = (local_today() + timedelta(days=3)).isoformat()

    task = await client.post(
        f"/api/classes/{made['id']}/tasks",
        json={"project_slug": project.slug, "due_date": due},
        headers=teacher[0],
    )
    assert task.status_code == 201, task.text
    assert task.json()["done_count"] == 0 and task.json()["member_count"] == 2

    # The pupil does the project: 15 points this week and the task is done.
    r = await client.post(
        f"/api/projects/{project.slug}/done",
        json={"client_event_id": str(uuid.uuid4())},
        headers=pupil,
    )
    assert r.status_code == 200, r.text

    detail = (await client.get(f"/api/classes/{made['id']}", headers=teacher[0])).json()
    assert [m["user_id"] for m in detail["members"]] == [pupil_id, lazy_id]
    assert detail["members"][0]["points_week"] == 15
    assert detail["members"][0]["projects_done"] == 1
    assert detail["tasks"][0]["done_by"] == [pupil_id]

    mine = (await client.get("/api/my-class", headers=pupil)).json()
    assert mine["tasks"][0]["done"] is True
    assert mine["tasks"][0]["done_by"] == []
    others = (await client.get("/api/my-class", headers=lazy)).json()
    assert others["tasks"][0]["done"] is False

    # Home shows the class task only to the pupil who has not done it.
    assert (await client.get("/api/home", headers=lazy)).json()["class_task"][
        "project_slug"
    ] == project.slug
    assert (await client.get("/api/home", headers=pupil)).json()["class_task"] is None


async def test_task_rules(client, teacher, session, monkeypatch):
    made = await make_class(client, teacher)
    project = await first_project(session)
    url = f"/api/classes/{made['id']}/tasks"
    today = local_today()

    past = {"project_slug": project.slug, "due_date": (today - timedelta(days=1)).isoformat()}
    assert (await client.post(url, json=past, headers=teacher[0])).status_code == 422
    unknown = {"project_slug": "no-such-project", "due_date": today.isoformat()}
    assert (await client.post(url, json=unknown, headers=teacher[0])).status_code == 404
    ok = {"project_slug": project.slug, "due_date": today.isoformat()}
    assert (await client.post(url, json=ok, headers=teacher[0])).status_code == 201
    assert (await client.post(url, json=ok, headers=teacher[0])).json()["detail"] == "task_exists"

    task_id = (await client.get(f"/api/classes/{made['id']}", headers=teacher[0])).json()["tasks"][
        0
    ]["id"]
    r = await client.delete(f"/api/classes/{made['id']}/tasks/{task_id}", headers=teacher[0])
    assert r.status_code == 204
    assert (await client.get(f"/api/classes/{made['id']}", headers=teacher[0])).json()[
        "tasks"
    ] == []


async def test_other_teachers_can_not_see_a_class(client, teacher):
    made = await make_class(client, teacher)
    other, _ = await onboard(client, 509, "Boshqa_Ustoz", "teacher")
    assert (await client.get(f"/api/classes/{made['id']}", headers=other)).status_code == 404
    assert (await client.delete(f"/api/classes/{made['id']}", headers=other)).status_code == 404


async def test_leave_remove_and_delete(client, teacher, session):
    made = await make_class(client, teacher)
    pupil, pupil_id = await onboard(client, 510, "Ketuvchi")
    other, other_id = await onboard(client, 511, "Qoluvchi")
    for headers in (pupil, other):
        await client.post("/api/classes/join", json={"code": made["code"]}, headers=headers)

    assert (await client.delete("/api/my-class", headers=pupil)).status_code == 204
    assert (await client.get("/api/my-class", headers=pupil)).json() is None

    r = await client.delete(f"/api/classes/{made['id']}/members/{other_id}", headers=teacher[0])
    assert r.status_code == 204
    assert (await client.get("/api/my-class", headers=other)).json() is None

    await client.post("/api/classes/join", json={"code": made["code"]}, headers=other)
    assert (
        await client.delete(f"/api/classes/{made['id']}", headers=teacher[0])
    ).status_code == 204
    assert await session.scalar(select(SchoolClass.id)) is None
    assert await session.scalar(select(ClassMember.user_id)) is None


async def test_admin_sees_and_removes_classes(client, teacher, session):
    made = await make_class(client, teacher, "Haqoratli nom")
    pupil, _ = await onboard(client, 512, "Admin_Korsin")
    await client.post("/api/classes/join", json={"code": made["code"]}, headers=pupil)

    admin = await admin_client(client, session, role=AdminRole.ADMIN, login="boss")
    rows = (await admin.get("/api/admin/classes", params={"q": "ustoz"})).json()
    assert [(r["name"], r["teacher_nickname"], r["member_count"]) for r in rows] == [
        ("Haqoratli nom", "Ustoz_Nodira", 1)
    ]
    assert (await admin.delete(f"/api/admin/classes/{made['id']}")).status_code == 204
    assert (await admin.get("/api/admin/classes")).json() == []
    log = await session.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "class_delete"))
    assert log.details["name"] == "Haqoratli nom"


async def test_all_projects_for_the_task_picker(client, teacher):
    projects = (await client.get("/api/projects", headers=teacher[0])).json()
    assert projects and all(p["slug"] for p in projects)


async def test_blocked_users_are_not_shown_in_classes(client, session, teacher):
    made = await make_class(client, teacher)
    kind, kind_id = await onboard(client, 560, "Yaxshi_Bola")
    rude, rude_id = await onboard(client, 561, "Yomon_Bola")
    for headers in (kind, rude):
        r = await client.post("/api/classes/join", json={"code": made["code"]}, headers=headers)
        assert r.status_code == 200, r.text
    blocked = await session.get(User, rude_id)
    blocked.is_blocked = True
    await session.commit()

    detail = (await client.get(f"/api/classes/{made['id']}", headers=teacher[0])).json()
    assert [m["user_id"] for m in detail["members"]] == [kind_id]
    assert detail["member_count"] == 1
    mine = (await client.get("/api/my-class", headers=kind)).json()
    assert [m["user_id"] for m in mine["members"]] == [kind_id]


async def test_a_blocked_teachers_class_can_not_be_joined(client, session, teacher):
    made = await make_class(client, teacher)
    headers, _ = await onboard(client, 562, "Yangi_Bola")
    owner = await session.get(User, teacher[1])
    owner.is_blocked = True
    await session.commit()
    r = await client.get(f"/api/classes/preview/{made['code']}", headers=headers)
    assert r.status_code == 404
    r = await client.post("/api/classes/join", json={"code": made["code"]}, headers=headers)
    assert r.status_code == 404
