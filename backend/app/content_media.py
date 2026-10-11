"""Pictures and videos of the content, uploaded in the admin panel instead of links.

Files live on disk in MEDIA_DIR, not in the database: videos are far too big for it. In
production the web server serves that folder at /media (only its i/ and v/ parts) and lets
browsers keep the files for a year; names are hashes of the files, so a link never changes
what it shows.

Pictures are decoded and only their pixels drawn into a new image, so nothing a camera wrote
along survives, and saved as WebP. Videos are converted by ffmpeg in the background into an
H.264 MP4 that every phone plays (at most 1280 px on the long side and 30 frames a second, no
metadata such as the place it was filmed), and a cover picture is taken from the video. One
conversion at a time and at a low priority: the server also runs other sites.
"""

import asyncio
import hashlib
import io
import json
import logging
import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select

from app import timeutil
from app.config import get_settings
from app.db import SessionLocal
from app.models import VideoStatus, VideoUpload

log = logging.getLogger(__name__)

MEDIA_URL = "/media"

PICTURE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PICTURE_BYTES = 15 * 1024 * 1024
MAX_PICTURE_PIXELS = 60_000_000
MIN_PICTURE_SIDE = 64
PictureKind = Literal["picture", "item"]
# Covers and card or question pictures fill the screen width; game items are small squares.
PICTURE_SIDE: dict[str, int] = {"picture": 1280, "item": 512}

MAX_VIDEO_BYTES = 500 * 1024 * 1024
MAX_VIDEO_SECONDS = 180
VIDEO_SIDE = 1280
VIDEO_FPS = 30
CONVERT_TIMEOUT = 20 * 60
PROBE_TIMEOUT = 60
# Leftovers of uploads that were never converted (a crash, a full disk) go after a day.
TMP_MAX_AGE = 24 * 3600


class MediaError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def media_root() -> Path:
    return Path(get_settings().media_dir).resolve()


def media_folder(name: str) -> Path:
    path = media_root() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write(path: Path, data: bytes) -> None:
    """Write once: the same name always holds the same bytes."""
    if path.exists():
        return
    part = path.with_name(path.name + ".part")
    part.write_bytes(data)
    os.replace(part, path)


# ------------------------------------------------------------------ pictures


@dataclass(frozen=True)
class Picture:
    url: str
    width: int
    height: int


def save_picture(data: bytes, kind: PictureKind) -> Picture:
    """A JPEG/PNG/WebP upload as a clean WebP file (transparency kept), or MediaError."""
    if len(data) > MAX_PICTURE_BYTES:
        raise MediaError("picture_too_large")
    side = PICTURE_SIDE[kind]
    try:
        with Image.open(io.BytesIO(data)) as probe:
            if probe.format not in {"JPEG", "PNG", "WEBP"}:
                raise MediaError("picture_format")
            width, height = probe.size
            if width * height > MAX_PICTURE_PIXELS:
                raise MediaError("picture_too_large")
            if min(width, height) < MIN_PICTURE_SIDE:
                raise MediaError("picture_too_small")
            probe.verify()
        with Image.open(io.BytesIO(data)) as source:
            if source.format == "JPEG":
                # Decode big camera photos at a reduced scale: faster and far less memory.
                source.draft("RGB", (side * 2, side * 2))
            source.load()
            upright = ImageOps.exif_transpose(source)
            transparent = upright.mode in ("RGBA", "LA", "PA") or (
                upright.mode == "P" and "transparency" in upright.info
            )
            mode = "RGBA" if transparent else "RGB"
            # Only the pixels go on: a new image carries no EXIF, GPS, ICC profile or comments.
            clean = Image.new(mode, upright.size)
            clean.paste(upright.convert(mode))
            clean.thumbnail((side, side), Image.Resampling.LANCZOS)
    except MediaError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise MediaError("picture_unreadable") from None
    out = io.BytesIO()
    clean.save(out, "WEBP", quality=82, method=4)
    webp = out.getvalue()
    name = hashlib.sha256(webp).hexdigest()[:24] + ".webp"
    _write(media_folder("i") / name, webp)
    return Picture(url=f"{MEDIA_URL}/i/{name}", width=clean.width, height=clean.height)


# -------------------------------------------------------------------- videos


@dataclass(frozen=True)
class Video:
    url: str
    poster_url: str
    width: int
    height: int
    duration_ms: int
    size_bytes: int


@dataclass(frozen=True)
class Probe:
    width: int  # as the video is shown, after the phone's rotation
    height: int
    seconds: float
    fps: float


def video_tools() -> tuple[str, str] | None:
    """ffmpeg and ffprobe, if installed (the production image has them)."""
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    return (ffmpeg, ffprobe) if ffmpeg and ffprobe else None


def _run(args: list[str], timeout: int) -> bytes:
    nice = shutil.which("nice")
    command = [nice, "-n", "15", *args] if nice else args
    try:
        done = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        raise MediaError("video_too_slow") from None
    if done.returncode != 0:
        tail = done.stderr[-400:].decode(errors="replace").strip()
        log.warning("%s exited with %s: %s", Path(args[0]).name, done.returncode, tail)
        raise MediaError("video_unreadable")
    return done.stdout


def _number(value: object) -> float:
    try:
        return float(str(value))
    except ValueError:
        return 0.0


def _rate(value: object) -> float:
    num, _, den = str(value).partition("/")
    try:
        return float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        return 0.0


def _rotation(stream: dict) -> int:
    for data in stream.get("side_data_list") or []:
        if "rotation" in data:
            return round(abs(_number(data["rotation"]))) % 360
    tag = str((stream.get("tags") or {}).get("rotate") or "0")
    return abs(int(tag)) % 360 if tag.lstrip("-").isdigit() else 0


def probe(path: Path, ffprobe: str) -> Probe:
    raw = _run(
        [ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
         str(path)],
        PROBE_TIMEOUT,
    )  # fmt: skip
    try:
        info = json.loads(raw)
    except ValueError:
        raise MediaError("video_unreadable") from None
    # Audio files may carry a cover picture as a "video" stream; that is not a video.
    streams = [s for s in info.get("streams") or [] if s.get("codec_type") == "video"]
    video = next((s for s in streams if not (s.get("disposition") or {}).get("attached_pic")), None)
    if video is None:
        raise MediaError("video_unreadable")
    width, height = int(video.get("width") or 0), int(video.get("height") or 0)
    if not width or not height:
        raise MediaError("video_unreadable")
    if _rotation(video) % 180 == 90:
        width, height = height, width
    seconds = _number((info.get("format") or {}).get("duration")) or _number(video.get("duration"))
    fps = _rate(video.get("avg_frame_rate")) or _rate(video.get("r_frame_rate"))
    return Probe(width=width, height=height, seconds=seconds, fps=fps)


def target_size(width: int, height: int) -> tuple[int, int]:
    """At most VIDEO_SIDE on the long side, even numbers (H.264 needs them)."""
    scale = min(1.0, VIDEO_SIDE / max(width, height))
    return (max(2, round(width * scale / 2) * 2), max(2, round(height * scale / 2) * 2))


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _poster(ffmpeg: str, video: Path, seconds: float) -> bytes:
    """A frame from the first seconds as a WebP cover picture."""
    at = f"{min(1.0, seconds / 3):.2f}"
    png = _run(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-ss", at, "-i", str(video),
         "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "pipe:1"],
        PROBE_TIMEOUT,
    )  # fmt: skip
    try:
        with Image.open(io.BytesIO(png)) as frame:
            image = frame.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        raise MediaError("video_unreadable") from None
    out = io.BytesIO()
    image.save(out, "WEBP", quality=78, method=4)
    return out.getvalue()


_convert_lock = threading.Lock()


def convert_video(source: Path) -> Video:
    """Convert an uploaded video into the files the Mini App plays, or MediaError."""
    tools = video_tools()
    if tools is None:
        raise MediaError("no_ffmpeg")
    ffmpeg, ffprobe = tools
    with _convert_lock:
        info = probe(source, ffprobe)
        if info.seconds > MAX_VIDEO_SECONDS + 0.5:
            raise MediaError("video_too_long")
        if info.seconds < 1:
            raise MediaError("video_too_short")
        width, height = target_size(info.width, info.height)
        filters = [f"scale={width}:{height}:flags=lanczos", "setsar=1"]
        if info.fps > VIDEO_FPS + 0.5:
            filters.append(f"fps={VIDEO_FPS}")
        out = media_folder("tmp") / f"{source.stem}.mp4"
        try:
            _run(
                [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
                 "-map", "0:v:0", "-map", "0:a:0?", "-map_metadata", "-1", "-map_chapters", "-1",
                 "-vf", ",".join(filters),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                 "-profile:v", "high", "-level:v", "4.1", "-pix_fmt", "yuv420p",
                 "-maxrate", "2500k", "-bufsize", "5000k",
                 "-c:a", "aac", "-b:a", "96k",
                 "-movflags", "+faststart", "-threads", "2", str(out)],
                CONVERT_TIMEOUT,
            )  # fmt: skip
            poster = _poster(ffmpeg, out, info.seconds)
            name = _file_hash(out)[:24]
            final = media_folder("v") / f"{name}.mp4"
            os.replace(out, final)
            _write(media_folder("v") / f"{name}.webp", poster)
        finally:
            out.unlink(missing_ok=True)
    return Video(
        url=f"{MEDIA_URL}/v/{name}.mp4",
        poster_url=f"{MEDIA_URL}/v/{name}.webp",
        width=width,
        height=height,
        duration_ms=round(info.seconds * 1000),
        size_bytes=final.stat().st_size,
    )


# ------------------------------------------------------------ background jobs

_tasks: set[asyncio.Task] = set()


def start_video_job(video_id: int, source: Path) -> None:
    task = asyncio.create_task(_video_job(video_id, source))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def wait_for_jobs() -> None:
    """Let running conversions finish (tests)."""
    while _tasks:
        await asyncio.gather(*list(_tasks), return_exceptions=True)


async def _video_job(video_id: int, source: Path) -> None:
    result: Video | None = None
    error: str | None = None
    try:
        result = await asyncio.to_thread(convert_video, source)
    except MediaError as exc:
        error = exc.code
    except asyncio.CancelledError:
        # The API is stopping: the upload stays, and the next start converts it again.
        raise
    except Exception:
        log.exception("video %s: conversion failed", video_id)
        error = "video_unreadable"
    await asyncio.to_thread(source.unlink, missing_ok=True)
    async with SessionLocal() as session:
        row = await session.get(VideoUpload, video_id)
        if row is None:
            return
        row.source_name = None
        row.finished_at = timeutil.utc_now()
        if result is not None:
            row.status = VideoStatus.READY
            row.url = result.url
            row.poster_url = result.poster_url
            row.width = result.width
            row.height = result.height
            row.duration_ms = result.duration_ms
            row.size_bytes = result.size_bytes
        else:
            row.status = VideoStatus.FAILED
            row.error = error
        await session.commit()


async def resume_video_jobs() -> None:
    """On start: convert again what a restart interrupted, and clear old leftovers."""
    tmp = media_folder("tmp")
    active: set[str] = set()
    async with SessionLocal() as session:
        rows = await session.scalars(
            select(VideoUpload).where(VideoUpload.status == VideoStatus.PROCESSING)
        )
        for row in rows.all():
            source = tmp / (row.source_name or "-")
            if row.source_name and source.is_file():
                active.add(source.name)
                start_video_job(row.id, source)
            else:
                row.status = VideoStatus.FAILED
                row.error = "interrupted"
                row.finished_at = timeutil.utc_now()
        await session.commit()
    cutoff = time.time() - TMP_MAX_AGE
    for path in tmp.iterdir():
        if path.name not in active and path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)
