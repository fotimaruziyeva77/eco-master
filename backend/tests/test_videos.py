"""The home screen's video feed and step clips (step times with pictures from the video)."""

import shutil
import subprocess
import uuid

import pytest
from sqlalchemy import update

from app.content_media import make_step_pictures, media_root, step_picture_name
from app.models import ContentStatus, Project
from app.seed import seed_badges, seed_categories, seed_demo
from tests.admin_helpers import admin_client
from tests.conftest import login
from tests.test_admin_content import project_values

VIDEO = f"/media/v/{'a' * 24}.mp4"
OTHER_VIDEO = f"/media/v/{'b' * 24}.mp4"


@pytest.fixture
async def content(session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_demo(session)
    await session.commit()


async def user_headers(client, telegram_id: int = 8100) -> dict:
    body = await login(client, telegram_id=telegram_id)
    return {"Authorization": f"Bearer {body['token']}"}


async def set_project(session, slug: str, **values) -> None:
    await session.execute(update(Project).where(Project.slug == slug).values(**values))
    await session.commit()


# ------------------------------------------------------------------ the feed


async def test_home_feed_has_the_video_files(client, session, content):
    await set_project(session, "plastic-bottle-flower-pot", video_url=VIDEO)
    # A link to another site can not play in the feed; a draft is not shown at all.
    await set_project(
        session, "cardboard-pencil-holder", video_url="https://www.youtube.com/watch?v=abcdefgh"
    )
    await set_project(
        session, "dry-leaves-compost", video_url=OTHER_VIDEO, status=ContentStatus.DRAFT
    )
    headers = await user_headers(client)
    home = (await client.get("/api/home", headers=headers)).json()
    assert [v["slug"] for v in home["videos"]] == ["plastic-bottle-flower-pot"]
    card = home["videos"][0]
    assert card["video_url"] == VIDEO
    assert card["category_icon"]
    assert card["done"] is False
    assert (await client.get("/api/videos", headers=headers)).json() == home["videos"]


async def test_feed_shows_what_is_not_made_yet_first(client, session, content):
    await set_project(session, "plastic-bottle-flower-pot", video_url=VIDEO)
    await set_project(session, "cardboard-pencil-holder", video_url=OTHER_VIDEO)
    headers = await user_headers(client, 8101)
    before = [v["slug"] for v in (await client.get("/api/videos", headers=headers)).json()]
    assert len(before) == 2
    made = await client.post(
        f"/api/projects/{before[0]}/done",
        json={"client_event_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert made.status_code == 200, made.text
    after = (await client.get("/api/videos", headers=headers)).json()
    assert [v["slug"] for v in after] == [before[1], before[0]]
    assert [v["done"] for v in after] == [False, True]


# ---------------------------------------------------------------- step times


async def test_step_times_are_checked(client, session, content):
    admin = await admin_client(client, session)
    url = "/api/admin/content/projects"
    for times in ([5, 3], [-1, 2], [1, "2"], [1, 700]):
        bad = project_values(slug="steps-bad", video_url=VIDEO, step_times=times)
        r = await admin.post(url, json={"values": bad})
        assert r.status_code == 422, times
        assert "step_times" in r.json()["detail"]["errors"]

    # One time per step: otherwise it can be saved but not published.
    values = project_values(slug="steps-count", video_url=VIDEO, step_times=[0, 4.26, 9])
    created = (await admin.post(url, json={"values": values})).json()
    assert created["values"]["step_times"] == [0.0, 4.3, 9.0]
    errors = [i["message"] for i in created["issues"] if i["level"] == "error"]
    assert any("Qadam vaqtlari 3 ta, qadamlar 2 ta" in m for m in errors)

    # Marked one by one: a step without a time can be saved, but not published.
    half = project_values(slug="steps-half", video_url=VIDEO, step_times=[None, 4.5])
    created = (await admin.post(url, json={"values": half})).json()
    assert created["values"]["step_times"] == [None, 4.5]
    errors = [i["message"] for i in created["issues"] if i["level"] == "error"]
    assert "Videoda belgilanmagan qadamlar: 1" in errors
    empty = project_values(slug="steps-empty", video_url=VIDEO, step_times=[None, None])
    created = (await admin.post(url, json={"values": empty})).json()
    assert created["values"]["step_times"] is None

    matching = project_values(slug="steps-ok", video_url=VIDEO, step_times=[0, 4.5])
    created = (await admin.post(url, json={"values": matching})).json()
    assert not [i for i in created["issues"] if i["field"] == "step_times"]
    # Times on a video from another site do nothing in the app.
    linked = project_values(
        slug="steps-link", video_url="https://example.com/craft.mp4", step_times=[0, 4.5]
    )
    created = (await admin.post(url, json={"values": linked})).json()
    assert [i["level"] for i in created["issues"] if i["field"] == "step_times"] == ["warning"]


async def test_project_shows_its_steps_in_the_video(client, session, content):
    await set_project(session, "plastic-bottle-flower-pot", video_url=VIDEO, step_times=[0.0, 3.5])
    folder = media_root() / "v"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / step_picture_name(VIDEO, 3.5)).write_bytes(b"webp")

    headers = await user_headers(client, 8102)
    project = (await client.get("/api/projects/plastic-bottle-flower-pot", headers=headers)).json()
    assert project["step_times"] == [0.0, 3.5]
    # Only the pictures that were made: the first one is missing here.
    assert project["step_pictures"] == [None, f"/media/v/{'a' * 24}-35.webp"]

    other = (await client.get("/api/projects/cardboard-pencil-holder", headers=headers)).json()
    assert other["step_times"] is None and other["step_pictures"] is None


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_step_pictures_come_from_the_video():
    name = "c" * 24
    folder = media_root() / "v"
    folder.mkdir(parents=True, exist_ok=True)
    video = folder / f"{name}.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x640:rate=10",
         "-t", "3", "-pix_fmt", "yuv420p", str(video)],
        check=True,
    )  # fmt: skip
    url = f"/media/v/{name}.mp4"
    assert make_step_pictures(url, [0.0, 1.5, 2.5]) == 3
    assert make_step_pictures(url, [0.0, 1.5, 2.5]) == 0  # made once
    for seconds in (0.0, 1.5, 2.5):
        assert (folder / step_picture_name(url, seconds)).stat().st_size > 0
    assert make_step_pictures("https://www.youtube.com/watch?v=abcdefgh", [1.0]) == 0
