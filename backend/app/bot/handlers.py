import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal
from app.i18n import pick_language, t
from app.models import User

log = logging.getLogger(__name__)
router = Router()


async def upsert_bot_user(
    session: AsyncSession, telegram_id: int, language_code: str | None, source: str | None
) -> User:
    """Create the user on first /start. Starting the bot also allows it to send reminders."""
    stmt = insert(User).values(
        telegram_id=telegram_id,
        language=pick_language(language_code),
        source=source[:64] if source else None,
        write_access=True,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[User.telegram_id], set_={"write_access": True}
    )
    await session.execute(stmt)
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    await session.commit()
    return user


def open_app_keyboard(lang: str) -> InlineKeyboardMarkup | None:
    url = get_settings().webapp_url
    if not url.startswith("https://"):
        # Telegram only accepts HTTPS Mini App URLs; in local dev use a tunnel.
        log.warning("WEBAPP_URL is not https (%s); sending /start without the app button", url)
        return None
    button = InlineKeyboardButton(text=t("open_app", lang), web_app=WebAppInfo(url=url))
    return InlineKeyboardMarkup(inline_keyboard=[[button]])


@router.message(CommandStart())
async def on_start(message: Message, command: CommandObject) -> None:
    async with SessionLocal() as session:
        user = await upsert_bot_user(
            session, message.from_user.id, message.from_user.language_code, command.args
        )
    await message.answer(t("start", user.language), reply_markup=open_app_keyboard(user.language))


@router.message(Command("help"))
async def on_help(message: Message) -> None:
    async with SessionLocal() as session:
        user = await upsert_bot_user(
            session, message.from_user.id, message.from_user.language_code, None
        )
    await message.answer(t("help", user.language), reply_markup=open_app_keyboard(user.language))
