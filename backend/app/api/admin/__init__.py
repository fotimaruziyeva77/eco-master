"""Admin API under /api/admin (TZ 8.12)."""

from fastapi import APIRouter, Depends

from app.admin.deps import same_origin_only
from app.api.admin import (
    admins,
    audit,
    auth,
    content,
    market,
    media,
    reports,
    schedule,
    stats,
    users,
    words,
)

router = APIRouter(prefix="/admin", dependencies=[Depends(same_origin_only)])
for module in (auth, admins, content, media, schedule, users, reports, words, stats, audit, market):
    router.include_router(module.router)
