from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


def create_app() -> FastAPI:
    settings = get_settings()
    settings.check_production()

    app = FastAPI(
        title="Ekoustoz API",
        version="0.1.0",
        docs_url=None if settings.is_prod else "/api/docs",
        redoc_url=None,
        openapi_url=None if settings.is_prod else "/api/openapi.json",
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
    return app


app = create_app()
