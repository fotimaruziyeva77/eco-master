"""Pictures and videos uploaded in the admin panel instead of links (app.content_media)."""

import io
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import select

from app import content_media
from app.admin.content import CONTENT_TYPES, Ctx, clean
from app.api.admin import media as media_api
from app.config import get_settings
from app.content_media import MediaError, Video
from app.models import AdminAuditLog, AdminRole, VideoStatus, VideoUpload
from tests.admin_helpers import admin_client

PICTURE_URL = re.compile(r"/media/i/[0-9a-f]{24}\.webp")


def image_bytes(fmt: str, size=(300, 200), mode="RGB", **save) -> bytes:
    color = (10, 120, 60, 0) if mode == "RGBA" else (10, 120, 60)
    out = io.BytesIO()
    Image.new(mode, size, color).save(out, fmt, **save)
    return out.getvalue()


def media_file(url: str) -> Path:
    return Path(get_settings().media_dir) / url.removeprefix("/media/")


async def upload(client, data: bytes, content_type: str, kind: str = "picture"):
    return await client.post(
        f"/api/admin/media/pictures?kind={kind}",
        content=data,
        headers={"Content-Type": content_type},
    )


# ----------------------------------------------------------------- pictures


async def test_picture_becomes_clean_webp(client, session):
    await admin_client(client, session, role=AdminRole.EDITOR)
    exif = Image.Exif()
    exif[0x010F] = "PhoneMaker"  # camera make: must not survive
    photo = image_bytes("JPEG", size=(2400, 1600), exif=exif.tobytes())

    r = await upload(client, photo, "image/jpeg")

    assert r.status_code == 201, r.text
    body = r.json()
    assert PICTURE_URL.fullmatch(body["url"])
    assert (body["width"], body["height"]) == (1280, 853)
    with Image.open(media_file(body["url"])) as saved:
        assert saved.format == "WEBP"
        assert saved.size == (1280, 853)
        assert not saved.getexif()
    log = await session.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "media_upload"))
    assert log.object_type == "picture" and log.object_id == body["url"]


async def test_game_item_picture_is_small_and_keeps_transparency(client, session):
    await admin_client(client, session)
    r = await upload(client, image_bytes("PNG", size=(900, 900), mode="RGBA"), "image/png", "item")

    assert r.status_code == 201, r.text
    assert (r.json()["width"], r.json()["height"]) == (512, 512)
    with Image.open(media_file(r.json()["url"])) as saved:
        assert saved.mode == "RGBA"
        assert saved.getpixel((5, 5))[3] == 0


async def test_same_picture_twice_is_one_file(client, session):
    await admin_client(client, session)
    data = image_bytes("PNG")
    first = (await upload(client, data, "image/png")).json()["url"]
    second = (await upload(client, data, "image/png")).json()["url"]
    assert first == second


@pytest.mark.parametrize(
    ("data", "content_type", "status", "code"),
    [
        (b"GIF89a....", "image/gif", 415, "picture_format"),
        (b"not a picture at all", "image/png", 422, "picture_unreadable"),
        (image_bytes("PNG", size=(40, 40)), "image/png", 422, "picture_too_small"),
    ],
)
async def test_bad_pictures_are_refused(client, session, data, content_type, status, code):
    await admin_client(client, session)
    r = await upload(client, data, content_type)
    assert r.status_code == status
    assert r.json()["detail"] == code


async def test_too_big_picture_is_refused_before_reading(client, session, monkeypatch):
    await admin_client(client, session)
    monkeypatch.setattr(media_api, "MAX_PICTURE_BYTES", 1000)
    r = await upload(client, image_bytes("PNG", size=(400, 400)), "image/png")
    assert r.status_code == 413
    assert r.json()["detail"] == "picture_too_large"


async def test_only_content_staff_upload(client, session):
    r = await upload(client, image_bytes("PNG"), "image/png")
    assert r.status_code == 401
    await admin_client(client, session, role=AdminRole.POINT, login="desk")
    r = await upload(client, image_bytes("PNG"), "image/png")
    assert r.status_code == 403


async def test_dev_server_serves_pictures_but_not_raw_uploads(client, session):
    await admin_client(client, session)
    url = (await upload(client, image_bytes("PNG"), "image/png")).json()["url"]
    r = await client.get(url)
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/webp"

    raw = content_media.media_folder("tmp") / "secret.upload"
    raw.write_bytes(b"raw")
    assert (await client.get("/media/tmp/secret.upload")).status_code == 404
    raw.unlink()


# ------------------------------------------------------------------- videos


@pytest.fixture
def fake_ffmpeg(monkeypatch):
    """Conversions without ffmpeg: the tests check the flow, not the codec."""
    monkeypatch.setattr(media_api, "video_tools", lambda: ("ffmpeg", "ffprobe"))
    seen: list[bytes] = []

    def convert(source: Path) -> Video:
        data = source.read_bytes()
        seen.append(data)
        if data == b"too long":
            raise MediaError("video_too_long")
        return Video(
            url="/media/v/" + "a" * 24 + ".mp4",
            poster_url="/media/v/" + "a" * 24 + ".webp",
            width=720,
            height=1280,
            duration_ms=45_000,
            size_bytes=5_000_000,
        )

    monkeypatch.setattr(content_media, "convert_video", convert)
    return seen


async def post_video(client, data: bytes, name="Gul tuvagi.mov"):
    return await client.post(
        "/api/admin/media/videos",
        params={"name": name},
        content=data,
        headers={"Content-Type": "video/quicktime"},
    )


async def test_video_is_converted_in_the_background(client, session, fake_ffmpeg):
    await admin_client(client, session, role=AdminRole.EDITOR)
    uploads = set(content_media.media_folder("tmp").glob("*.upload"))

    r = await post_video(client, b"video bytes")

    assert r.status_code == 202, r.text
    started = r.json()
    assert started["status"] == "processing"
    assert started["name"] == "Gul tuvagi.mov"
    await content_media.wait_for_jobs()

    r = await client.get(f"/api/admin/media/videos/{started['id']}")
    done = r.json()
    assert done["status"] == "ready"
    assert done["url"] == "/media/v/" + "a" * 24 + ".mp4"
    assert done["poster_url"].endswith(".webp")
    assert (done["width"], done["height"], done["duration_ms"]) == (720, 1280, 45_000)
    assert fake_ffmpeg == [b"video bytes"]
    # The raw upload is gone once converted.
    assert set(content_media.media_folder("tmp").glob("*.upload")) == uploads


async def test_failed_conversion_says_why(client, session, fake_ffmpeg):
    await admin_client(client, session)
    started = (await post_video(client, b"too long")).json()
    await content_media.wait_for_jobs()

    done = (await client.get(f"/api/admin/media/videos/{started['id']}")).json()
    assert done["status"] == "failed"
    assert done["error"] == "video_too_long"
    assert done["url"] is None


async def test_video_upload_limits(client, session, fake_ffmpeg, monkeypatch):
    await admin_client(client, session)
    assert (await post_video(client, b"")).json()["detail"] == "video_unreadable"

    monkeypatch.setattr(media_api, "MAX_VIDEO_BYTES", 10)
    r = await post_video(client, b"x" * 50)
    assert r.status_code == 413
    assert r.json()["detail"] == "video_too_large"

    r = await client.post(
        "/api/admin/media/videos", content=b"x", headers={"Content-Type": "image/png"}
    )
    assert r.status_code == 415


async def test_video_upload_needs_ffmpeg(client, session, monkeypatch):
    await admin_client(client, session)
    monkeypatch.setattr(media_api, "video_tools", lambda: None)
    assert (await client.get("/api/admin/media/status")).json() == {"video": False}
    r = await post_video(client, b"video bytes")
    assert r.status_code == 503
    assert r.json()["detail"] == "no_ffmpeg"

    monkeypatch.setattr(media_api, "video_tools", lambda: ("ffmpeg", "ffprobe"))
    assert (await client.get("/api/admin/media/status")).json() == {"video": True}


async def test_restart_resumes_or_fails_conversions(session, fake_ffmpeg):
    tmp = content_media.media_folder("tmp")
    (tmp / "kept.upload").write_bytes(b"kept upload")
    kept = VideoUpload(status=VideoStatus.PROCESSING, original_name="a", source_name="kept.upload")
    lost = VideoUpload(status=VideoStatus.PROCESSING, original_name="b", source_name="lost.upload")
    session.add_all([kept, lost])
    await session.commit()

    await content_media.resume_video_jobs()
    await content_media.wait_for_jobs()

    await session.refresh(kept)
    await session.refresh(lost)
    assert kept.status == VideoStatus.READY
    assert lost.status == VideoStatus.FAILED and lost.error == "interrupted"
    assert fake_ffmpeg == [b"kept upload"]


# ------------------------------------------------------------ content fields


@pytest.mark.parametrize(
    ("field", "value", "ok"),
    [
        ("video_url", "/media/v/" + "0" * 24 + ".mp4", True),
        ("video_url", "/media/v/" + "0" * 24 + ".webp", False),
        ("video_url", "/media/v/../../etc/passwd", False),
        ("video_url", "http://example.com/a.mp4", False),
        ("video_url", "https://www.youtube.com/watch?v=abcdefgh", True),
        ("poster_url", "/media/v/" + "0" * 24 + ".webp", True),
        ("poster_url", "/media/i/" + "0" * 24 + ".webp", True),
        ("poster_url", "/media/i/" + "0" * 24 + ".mp4", False),
    ],
)
def test_media_fields_take_uploaded_files(field, value, ok):
    spec = CONTENT_TYPES["projects"].field(field)
    if ok:
        assert clean(spec, value, Ctx([])) == value
    else:
        with pytest.raises(ValueError):
            clean(spec, value, Ctx([]))


# --------------------------------------------------------------- real ffmpeg


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_real_conversion_shrinks_and_strips_metadata(tmp_path):
    source = tmp_path / "phone.upload"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=1080x1920:rate=60",
         "-f", "lavfi", "-i", "sine=frequency=440", "-t", "2",
         "-metadata", "location=+41.3111+069.2797/", "-c:v", "libx264", "-c:a", "aac",
         "-f", "mov", str(source)],
        check=True,
    )  # fmt: skip

    video = content_media.convert_video(source)

    assert (video.width, video.height) == (720, 1280)
    assert 1900 <= video.duration_ms <= 2100
    out = media_file(video.url)
    info = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format_tags:stream=codec_name,avg_frame_rate",
         "-of", "json", str(out)],
        check=True, capture_output=True, text=True,
    ).stdout  # fmt: skip
    assert "location" not in info
    assert '"h264"' in info and '"aac"' in info
    assert '"30/1"' in info
    with Image.open(media_file(video.poster_url)) as poster:
        assert poster.format == "WEBP" and poster.size == (720, 1280)
