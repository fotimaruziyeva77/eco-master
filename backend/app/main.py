import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import (
    admin,
    auth,
    content,
    daily,
    dev,
    events,
    games,
    health,
    lessons,
    market,
    me,
    media,
    onboarding,
    rating,
    share,
)
from app.config import get_settings
from app.content_media import MEDIA_URL, media_root, resume_video_jobs

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        await resume_video_jobs()
    except Exception:
        # Never keep the API down for this, e.g. before the migrations ran in development.
        log.exception("could not resume video conversions")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    settings.check_production()

    app = FastAPI(
        title="Eco-Master API",
        version="0.1.0",
        docs_url=None if settings.is_prod else "/api/docs",
        redoc_url=None,
        openapi_url=None if settings.is_prod else "/api/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    routers = (
        health,
        auth,
        me,
        onboarding,
        content,
        games,
        daily,
        rating,
        lessons,
        share,
        market,
        media,
        events,
        admin,
    )
    for module in routers:
        app.include_router(module.router, prefix="/api")
    if settings.dev_auth_enabled:
        app.include_router(dev.router, prefix="/api")
    if not settings.is_prod:
        # In production the web server serves uploaded pictures and videos itself.
        # Only i/ and v/: tmp/ holds uploads that are not cleaned yet.
        for part in ("i", "v"):
            files = StaticFiles(directory=media_root() / part, check_dir=False)
            app.mount(f"{MEDIA_URL}/{part}", files, name=f"media-{part}")
    return app


app = create_app()
