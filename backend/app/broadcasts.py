"""Messages from the team to many users at once, sent by the bot process (stage 7).

An administrator writes the text in the admin panel (Uzbek, and Russian / English if they
like), picks who gets it and queues it. The bot sends it in chunks, slower than Telegram's
limit, and remembers how far it got, so a restart goes on where it stopped. Only users who
keep bot messages on (the reminders switch) get it, and at most WEEKLY_LIMIT broadcasts go out
in seven days: the bot is for children, not for advertising.
"""

import asyncio
import html
import logging
from datetime import UTC, datetime, timedelta
from typing import Literal, get_args

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import track
from app.bot.handlers import open_app_keyboard
from app.db import SessionLocal, engine
from app.models import Broadcast, BroadcastStatus, OnboardingStep, User, UserPath
from app.reminders import QUIET_FROM, QUIET_UNTIL
from app.timeutil import TASHKENT

log = logging.getLogger(__name__)

Audience = Literal["all", "student", "teacher", "general"]
AUDIENCES: tuple[str, ...] = get_args(Audience)
WEEKLY_LIMIT = 2
MAX_TEXT = 1000
CHUNK = 100
SEND_INTERVAL = 1 / 25
# Messages between looks for a cancel from the admin panel.
CHECK_EVERY = 10
# Advisory lock keys: sending (one bot process at a time) and queueing (one admin at a time).
LOCK_KEY = 73_6203
QUEUE_LOCK_KEY = 73_6204


def recipients(audience: str):
    """Users who agreed to bot messages, in id order."""
    query = select(User).where(
        User.write_access.is_(True),
        User.reminders_enabled.is_(True),
        User.is_blocked.is_(False),
        User.onboarding_step == OnboardingStep.DONE,
    )
    if audience != "all":
        query = query.where(User.path == UserPath(audience))
    return query.order_by(User.id)


async def audience_size(session: AsyncSession, audience: str) -> int:
    return await session.scalar(select(func.count()).select_from(recipients(audience).subquery()))


async def sent_this_week(session: AsyncSession, now: datetime | None = None) -> int:
    """Broadcasts of the last seven days that reached someone or are still going out."""
    since = (now or datetime.now(UTC)) - timedelta(days=7)
    return await session.scalar(
        select(func.count())
        .select_from(Broadcast)
        .where(
            Broadcast.created_at >= since,
            or_(
                Broadcast.status.in_((BroadcastStatus.QUEUED, BroadcastStatus.SENDING)),
                Broadcast.sent > 0,
            ),
        )
    )


async def cancelled(session: AsyncSession, broadcast_id: int) -> bool:
    status = await session.scalar(select(Broadcast.status).where(Broadcast.id == broadcast_id))
    return status == BroadcastStatus.CANCELLED


def message_for(broadcast: Broadcast, language: str) -> str:
    """Plain text: whatever the administrator typed is shown as typed. Telegram's HTML mode
    needs only <, > and & replaced; apostrophes, common in Uzbek, stay as they are."""
    body = broadcast.text.get(language) or broadcast.text.get("uz", "")
    return html.escape(body, quote=False)


async def send_next_chunk(session: AsyncSession, bot: Bot, now: datetime | None = None) -> bool:
    """Send one chunk of the oldest unfinished broadcast. Returns whether work is left.

    Like the reminders, nothing goes out between 21:00 and 08:00 Tashkent time: a broadcast
    queued in the evening (or still going at nine) goes on in the morning.
    """
    clock = (now or datetime.now(UTC)).astimezone(TASHKENT).time()
    if not (QUIET_UNTIL <= clock < QUIET_FROM):
        return False
    async with engine.connect() as lock_conn:
        if not await lock_conn.scalar(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}):
            return False
        try:
            return await _chunk(session, bot)
        finally:
            await lock_conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})


async def _move(
    session: AsyncSession, broadcast: Broadcast, old: BroadcastStatus, **values
) -> bool:
    """Change the status only if nobody else did meanwhile (a cancel from the admin panel)."""
    moved = await session.scalar(
        update(Broadcast)
        .where(Broadcast.id == broadcast.id, Broadcast.status == old)
        .values(**values)
        .returning(Broadcast.id)
    )
    await session.commit()
    await session.refresh(broadcast)
    return moved is not None


async def _chunk(session: AsyncSession, bot: Bot) -> bool:
    broadcast = await session.scalar(
        select(Broadcast)
        .where(Broadcast.status.in_((BroadcastStatus.QUEUED, BroadcastStatus.SENDING)))
        .order_by(Broadcast.id)
        .limit(1)
        .execution_options(populate_existing=True)
    )
    if broadcast is None:
        return False
    if broadcast.status == BroadcastStatus.QUEUED:
        total = await audience_size(session, broadcast.audience)
        started = await _move(
            session,
            broadcast,
            BroadcastStatus.QUEUED,
            status=BroadcastStatus.SENDING,
            started_at=datetime.now(UTC),
            total=total,
        )
        if not started:
            return True  # cancelled just now

    users = (
        await session.scalars(
            recipients(broadcast.audience).where(User.id > broadcast.last_user_id).limit(CHUNK)
        )
    ).all()
    if not users:
        await _move(
            session,
            broadcast,
            BroadcastStatus.SENDING,
            status=BroadcastStatus.DONE,
            finished_at=datetime.now(UTC),
        )
        return True

    for i, user in enumerate(users):
        # A cancel from the admin panel stops it within a few messages.
        if i % CHECK_EVERY == 0 and await cancelled(session, broadcast.id):
            broadcast.status = BroadcastStatus.CANCELLED
            return True
        if await _send(bot, user, message_for(broadcast, user.language), broadcast.id):
            broadcast.sent += 1
            track(session, user, "broadcast_sent", broadcast=broadcast.id)
        else:
            broadcast.failed += 1
        broadcast.last_user_id = user.id
        # Saved after every message: after a restart nobody gets the same broadcast twice.
        await session.commit()
        await asyncio.sleep(SEND_INTERVAL)
    return True


async def _send(bot: Bot, user: User, message: str, broadcast_id: int) -> bool:
    # The id in startapp lets the admin panel count who opened the app from this broadcast.
    keyboard = open_app_keyboard(user.language, start=f"broadcast_{broadcast_id}")
    try:
        try:
            await bot.send_message(user.telegram_id, message, reply_markup=keyboard)
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            await bot.send_message(user.telegram_id, message, reply_markup=keyboard)
        return True
    except TelegramForbiddenError:
        # The user blocked the bot: no more messages to them.
        user.write_access = False
        user.reminders_enabled = False
    except TelegramAPIError:
        log.exception("Broadcast to user %s failed", user.id)
    return False


async def broadcast_loop(bot: Bot, every_seconds: int = 20) -> None:
    """Runs in the bot process; sends queued broadcasts chunk by chunk."""
    while True:
        try:
            async with SessionLocal() as session:
                while await send_next_chunk(session, bot):
                    pass
        except Exception:
            log.exception("Broadcast round failed")
        await asyncio.sleep(every_seconds)
