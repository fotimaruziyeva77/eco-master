"""One shared Bot instance for the API (sending PDFs, preparing share messages)."""

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import get_settings

_bot: Bot | None = None


def get_bot() -> Bot | None:
    """The bot, or None when BOT_TOKEN is not configured (local development)."""
    global _bot
    settings = get_settings()
    if not settings.bot_token:
        return None
    if _bot is None:
        _bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    return _bot
