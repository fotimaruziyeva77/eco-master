"""Daily reminders from the bot (TZ 8.5, QM-11).

Each user gets at most one reminder a day, at or after the time they chose, only while the
daily task is still open, never between 21:00 and 08:00 Tashkent time.
"""

import asyncio
import html
import logging
from datetime import UTC, date, datetime, time

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import track
from app.bot.handlers import open_app_keyboard
from app.daily import current_streak, task_of_the_day
from app.db import SessionLocal, engine
from app.i18n import t
from app.models import OnboardingStep, User
from app.timeutil import TASHKENT

log = logging.getLogger(__name__)

QUIET_FROM = time(21, 0)
QUIET_UNTIL = time(8, 0)
# Telegram allows about 30 messages a second to different users; stay a little below.
SEND_INTERVAL = 1 / 25
# Only one process may send at a time (several API/bot replicas would otherwise double up).
LOCK_KEY = 73_6201


async def due_users(session: AsyncSession, now: datetime) -> list[User]:
    local = now.astimezone(TASHKENT)
    today, clock = local.date(), local.time()
    if not (QUIET_UNTIL <= clock < QUIET_FROM):
        return []
    query = select(User).where(
        User.reminders_enabled.is_(True),
        User.write_access.is_(True),
        User.is_blocked.is_(False),
        User.onboarding_step == OnboardingStep.DONE,
        User.reminder_time <= clock,
        or_(User.last_task_date.is_(None), User.last_task_date < today),
        or_(User.last_reminder_date.is_(None), User.last_reminder_date < today),
    )
    return list((await session.scalars(query.order_by(User.id))).all())


def reminder_text(user: User, task_text: str, today: date) -> str:
    streak = current_streak(user, today)
    streak_line = (
        t("reminder_streak", user.language, days=streak)
        if streak
        else t("reminder_streak_start", user.language)
    )
    return t(
        "reminder",
        user.language,
        name=html.escape(user.nickname or ""),
        task=html.escape(task_text),
        streak=streak_line,
    )


async def send_due_reminders(session: AsyncSession, bot: Bot, now: datetime | None = None) -> int:
    """Send every reminder that is due now. Returns how many were delivered."""
    now = now or datetime.now(UTC)
    today = now.astimezone(TASHKENT).date()
    # The lock lives on its own connection: the session hands its connection back to the
    # pool on every commit, which would leave a session-level lock stranded there.
    async with engine.connect() as lock_conn:
        if not await lock_conn.scalar(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}):
            return 0
        try:
            return await _send_all(session, bot, now, today)
        finally:
            await lock_conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})


async def _send_all(session: AsyncSession, bot: Bot, now: datetime, today: date) -> int:
    task = await task_of_the_day(session, today)
    if task is None:
        return 0
    sent = 0
    for user in await due_users(session, now):
        task_text = task.text.get(user.language) or task.text.get("uz", "")
        try:
            await _send(bot, user, reminder_text(user, task_text, today))
            sent += 1
            track(session, user, "reminder_sent")
        except TelegramForbiddenError:
            # The user blocked the bot: stop reminding them (TZ 8.5).
            user.reminders_enabled = False
            user.write_access = False
        except TelegramAPIError:
            log.exception("Reminder to user %s failed", user.id)
        # Marked even on failure, so one broken chat is not retried every minute.
        user.last_reminder_date = today
        await session.commit()
        await asyncio.sleep(SEND_INTERVAL)
    return sent


async def _send(bot: Bot, user: User, message: str) -> None:
    # startapp=reminder lets analytics count launches from reminders (reminder_open).
    keyboard = open_app_keyboard(user.language, start="reminder")
    try:
        await bot.send_message(user.telegram_id, message, reply_markup=keyboard)
    except TelegramRetryAfter as exc:
        await asyncio.sleep(exc.retry_after)
        await bot.send_message(user.telegram_id, message, reply_markup=keyboard)


async def reminder_loop(bot: Bot, every_seconds: int = 60) -> None:
    """Runs next to the bot; checks for due reminders once a minute."""
    while True:
        try:
            async with SessionLocal() as session:
                sent = await send_due_reminders(session, bot)
            if sent:
                log.info("Sent %s reminders", sent)
        except Exception:
            log.exception("Reminder round failed")
        await asyncio.sleep(every_seconds)
