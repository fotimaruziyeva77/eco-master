import html
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    Message,
    WebAppInfo,
)
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal
from app.i18n import pick_language, t
from app.models import OnboardingStep, User
from app.sharing import ShareError, parse_inline_query, share_article, share_text, share_url

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


def open_app_keyboard(lang: str, start: str | None = None) -> InlineKeyboardMarkup | None:
    """ "Open the app" button. With `start`, a t.me link passes it to the app as start_param."""
    settings = get_settings()
    if start and settings.bot_username:
        url = f"{settings.app_link}?startapp={start}"
        button = InlineKeyboardButton(text=t("open_app", lang), url=url)
        return InlineKeyboardMarkup(inline_keyboard=[[button]])
    url = settings.webapp_url
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


def feedback_report(user: User, text: str) -> str:
    """What the team sees. Only the internal id — no Telegram name or username (TZ 11.2)."""
    header = f"💬 #{user.id} · {user.language} · {user.path or '-'}"
    return f"{header}\n\n{html.escape(text[:3500])}"


@router.message(F.text & ~F.text.startswith("/"))
async def on_feedback(message: Message) -> None:
    """Anything users write to the bot goes to the team's private chat (TZ 8.11)."""
    settings = get_settings()
    async with SessionLocal() as session:
        user = await upsert_bot_user(
            session, message.from_user.id, message.from_user.language_code, None
        )
    if settings.feedback_chat_id:
        await message.bot.send_message(
            settings.feedback_chat_id, feedback_report(user, message.text)
        )
    else:
        log.info("Feedback from user %s (no FEEDBACK_CHAT_ID set): %s", user.id, message.text)
    await message.answer(t("feedback_thanks", user.language))


@router.inline_query()
async def on_inline_query(query: InlineQuery) -> None:
    """Share fallback for Telegram clients without shareMessage: the Mini App calls
    switchInlineQuery and the user picks this ready message (TZ 8.11)."""
    kind, object_id = parse_inline_query(query.query)
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == query.from_user.id))
        if user is None or user.onboarding_step != OnboardingStep.DONE:
            lang = user.language if user else pick_language(query.from_user.language_code)
            text = t("share_invite", lang)
        else:
            lang = user.language
            try:
                text = await share_text(session, user, kind, object_id)
            except ShareError:
                text = await share_text(session, user, "progress", None)
    article = share_article(lang, text, share_url(get_settings()))
    await query.answer([article], cache_time=0, is_personal=True)
