"""Uploading pictures and videos for the content, instead of links to other sites.

The file is the request body (no multipart form). A picture is ready in the answer; a video
is converted in the background, and the admin page asks for its state until it is ready.
"""

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status
from starlette.concurrency import run_in_threadpool

from app.admin.audit import audit
from app.admin.deps import ContentStaff
from app.admin.schemas import MediaStatusOut, PictureOut, VideoOut
from app.content_media import (
    MAX_PICTURE_BYTES,
    MAX_VIDEO_BYTES,
    PICTURE_TYPES,
    MediaError,
    PictureKind,
    media_folder,
    save_picture,
    start_video_job,
    video_tools,
)
from app.deps import SessionDep
from app.models import VideoStatus, VideoUpload

router = APIRouter(prefix="/media", tags=["admin-media"])


def _content_type(request: Request) -> str:
    return request.headers.get("content-type", "").split(";")[0].strip().lower()


def _too_large(request: Request, limit: int) -> bool:
    declared = request.headers.get("content-length", "")
    return declared.isdigit() and int(declared) > limit


async def _receive(request: Request, target: Path, limit: int, code: str) -> int:
    """Stream the body into a file; refuse it once it goes over the limit."""
    size = 0
    try:
        with target.open("wb") as file:
            async for chunk in request.stream():
                size += len(chunk)
                if size > limit:
                    raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, code)
                file.write(chunk)
    except BaseException:
        await run_in_threadpool(target.unlink, missing_ok=True)
        raise
    return size


def video_out(row: VideoUpload) -> VideoOut:
    return VideoOut(
        id=row.id,
        status=row.status,
        name=row.original_name,
        url=row.url,
        poster_url=row.poster_url,
        width=row.width,
        height=row.height,
        duration_ms=row.duration_ms,
        size_bytes=row.size_bytes,
        error=row.error,
    )


@router.get("/status")
async def media_status(admin: ContentStaff) -> MediaStatusOut:
    """Asked before a video upload: an early refusal would break the upload in the browser."""
    return MediaStatusOut(video=video_tools() is not None)


@router.post("/pictures", status_code=status.HTTP_201_CREATED)
async def upload_picture(
    request: Request,
    admin: ContentStaff,
    session: SessionDep,
    kind: Annotated[PictureKind, Query()] = "picture",
) -> PictureOut:
    """A picture (image/jpeg, png or webp); "item" keeps it small for the sorting game."""
    if _content_type(request) not in PICTURE_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "picture_format")
    if _too_large(request, MAX_PICTURE_BYTES):
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "picture_too_large")
    data = bytearray()
    async for chunk in request.stream():
        data += chunk
        if len(data) > MAX_PICTURE_BYTES:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "picture_too_large")
    try:
        picture = await run_in_threadpool(save_picture, bytes(data), kind)
    except MediaError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, exc.code) from exc
    except PermissionError as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "media_not_writable") from exc
    audit(session, admin, "media_upload", "picture", picture.url, kind=kind, bytes=len(data))
    await session.commit()
    return PictureOut(url=picture.url, width=picture.width, height=picture.height)


@router.post("/videos", status_code=status.HTTP_202_ACCEPTED)
async def upload_video(
    request: Request,
    admin: ContentStaff,
    session: SessionDep,
    name: Annotated[str, Query(max_length=200)] = "",
) -> VideoOut:
    """A video file of up to 500 MB and 3 minutes; converted in the background."""
    if video_tools() is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "no_ffmpeg")
    kind = _content_type(request)
    if not (kind.startswith("video/") or kind in ("", "application/octet-stream")):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "video_format")
    if _too_large(request, MAX_VIDEO_BYTES):
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "video_too_large")
    try:
        source = media_folder("tmp") / f"{uuid.uuid4().hex}.upload"
        size = await _receive(request, source, MAX_VIDEO_BYTES, "video_too_large")
    except PermissionError as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "media_not_writable") from exc
    if size == 0:
        await run_in_threadpool(source.unlink, missing_ok=True)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "video_unreadable")
    row = VideoUpload(
        status=VideoStatus.PROCESSING,
        original_name=name.strip()[:200] or "video",
        source_name=source.name,
        admin_id=admin.id,
    )
    session.add(row)
    await session.flush()
    audit(session, admin, "media_upload", "video", row.id, name=row.original_name, bytes=size)
    await session.commit()
    start_video_job(row.id, source)
    return video_out(row)


@router.get("/videos/{video_id}")
async def video_state(video_id: int, admin: ContentStaff, session: SessionDep) -> VideoOut:
    row = await session.get(VideoUpload, video_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "video_not_found")
    return video_out(row)
