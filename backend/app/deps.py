from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from aiogram import Bot
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.client import get_bot
from app.config import Settings, get_settings
from app.db import get_session
from app.models import User
from app.security import decode_session_token

bearer = HTTPBearer(auto_error=False)

# Writing last_active_at on every request is wasteful; once a minute is enough for DAU.
ACTIVITY_TOUCH_INTERVAL = timedelta(minutes=1)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_current_user(
    session: SessionDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not_authenticated")
    try:
        user_id = decode_session_token(credentials.credentials, settings.jwt_secret)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_token") from exc

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user_not_found")
    if user.is_blocked:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "user_blocked")

    now = datetime.now(UTC)
    if now - user.last_active_at > ACTIVITY_TOUCH_INTERVAL:
        user.last_active_at = now
        await session.commit()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def bot_dep() -> Bot | None:
    """The Telegram bot, or None without BOT_TOKEN. Tests replace this with a fake."""
    return get_bot()


BotDep = Annotated[Bot | None, Depends(bot_dep)]
