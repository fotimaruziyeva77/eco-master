"""Ready-made share messages (TZ 8.11, QM-16)."""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from fastapi import APIRouter, HTTPException

from app.analytics import track
from app.deps import BotDep, CurrentUser, SessionDep, SettingsDep
from app.schemas import ShareIn, ShareOut
from app.sharing import ShareError, inline_query_for, share_article, share_text, share_url

log = logging.getLogger(__name__)
router = APIRouter(tags=["share"])


async def inline_mode_enabled(bot: Bot) -> bool:
    """switchInlineQuery only works when inline mode is on in BotFather (/setinline)."""
    try:
        return bool((await bot.me()).supports_inline_queries)
    except TelegramAPIError:
        return False


@router.post("/share")
async def share(
    body: ShareIn, user: CurrentUser, session: SessionDep, settings: SettingsDep, bot: BotDep
) -> ShareOut:
    """Text and link to share. Where the bot is configured, also a prepared Telegram message
    (Bot API 8.0+) and an inline query for older clients."""
    try:
        text = await share_text(session, user, body.kind, body.object_id)
    except ShareError as exc:
        raise HTTPException(exc.status, exc.code) from exc
    url = share_url(settings)
    track(session, user, "share_click", kind=body.kind)
    await session.commit()

    out = ShareOut(text=text, url=url)
    if bot is None or not settings.bot_username:
        return out
    try:
        prepared = await bot.save_prepared_inline_message(
            user_id=user.telegram_id,
            result=share_article(user.language, text, url),
            allow_user_chats=True,
            allow_group_chats=True,
        )
        out.prepared_message_id = prepared.id
    except TelegramAPIError:
        # The client falls back to switchInlineQuery or Telegram's share link.
        log.warning("Could not prepare a share message", exc_info=True)
    if await inline_mode_enabled(bot):
        out.inline_query = inline_query_for(body.kind, body.object_id)
    return out
