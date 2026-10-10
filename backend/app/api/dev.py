"""Development-only helpers. Mounted only when ENV=dev and DEV_AUTH=true."""

import json
import time

from fastapi import APIRouter, Query

from app.deps import SettingsDep
from app.schemas import DevInitDataOut
from app.security import sign_init_data

router = APIRouter(tags=["dev"])


@router.get("/dev/init-data")
async def dev_init_data(
    settings: SettingsDep,
    telegram_id: int = Query(100001, ge=1),
    language_code: str = Query("uz", max_length=10),
    start_param: str | None = Query(None, max_length=64),
) -> DevInitDataOut:
    """Signed initData for a fake user, so the Mini App can be opened in a normal browser."""
    user = json.dumps(
        {"id": telegram_id, "first_name": "Dev", "language_code": language_code},
        separators=(",", ":"),
    )
    fields = {"auth_date": str(int(time.time())), "query_id": "dev", "user": user}
    if start_param:
        fields["start_param"] = start_param
    return DevInitDataOut(init_data=sign_init_data(settings.effective_bot_token, fields))
