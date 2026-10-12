"""Messages from the bot: the daily reminder (TZ 8.5, QM-11) and the Monday summary.

Each user gets at most one message a day, at or after the time they chose, never between 21:00
and 08:00 Tashkent time. The daily reminder goes out only while the daily task is still open.
Someone who has not opened the app for three days gets a "we missed you" text instead; after a
week away only one reminder a week, and after five weeks none, so the bot never nags a child
who has moved on. On Monday, whoever earned points last week gets the week's result (points,
league place, new league) instead of the reminder.
"""

import asyncio
import html
import logging
from datetime import UTC, date, datetime, time, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import track
from app.bot.handlers import open_app_keyboard
from app.daily import current_streak, task_of_the_day
from app.db import SessionLocal, engine
from app.i18n import t
from app.leagues import WeekResult, result_of
from app.models import ActivityLog, DailyTask, LeagueMember, OnboardingStep, User
from app.timeutil import TASHKENT

log = logging.getLogger(__name__)

QUIET_FROM = time(21, 0)
QUIET_UNTIL = time(8, 0)
# Days without opening the app before the reminder changes its tone, slows down, stops.
COMEBACK_AFTER_DAYS = 3
WEEKLY_AFTER = timedelta(days=7)
GIVE_UP_AFTER = timedelta(days=35)
# Telegram allows about 30 messages a second to different users; stay a little below.
SEND_INTERVAL = 1 / 25
# Only one process may send at a time (several API/bot replicas would otherwise double up).
LOCK_KEY = 73_6201


def _may_message(clock: time):
    """Users who agreed to messages and may get one at this time of day."""
    return and_(
        User.reminders_enabled.is_(True),
        User.write_access.is_(True),
        User.is_blocked.is_(False),
        User.onboarding_step == OnboardingStep.DONE,
        User.reminder_time <= clock,
    )


async def due_users(session: AsyncSession, now: datetime) -> list[User]:
    local = now.astimezone(TASHKENT)
    today, clock = local.date(), local.time()
    if not (QUIET_UNTIL <= clock < QUIET_FROM):
        return []
    query = select(User).where(
        _may_message(clock),
        or_(User.last_task_date.is_(None), User.last_task_date < today),
        or_(User.last_reminder_date.is_(None), User.last_reminder_date < today),
        User.last_active_at >= now - GIVE_UP_AFTER,
        or_(
            User.last_active_at >= now - WEEKLY_AFTER,
            User.last_reminder_date.is_(None),
            User.last_reminder_date <= today - timedelta(days=7),
        ),
    )
    return list((await session.scalars(query.order_by(User.id))).all())


async def weekly_due_users(session: AsyncSession, now: datetime) -> list[User]:
    """On Monday: users who played last week (they are in a league group) and have no summary."""
    local = now.astimezone(TASHKENT)
    today, clock = local.date(), local.time()
    if today.weekday() != 0 or not (QUIET_UNTIL <= clock < QUIET_FROM):
        return []
    query = (
        select(User)
        .join(
            LeagueMember,
            and_(
                LeagueMember.user_id == User.id,
                LeagueMember.week_start == today - timedelta(days=7),
            ),
        )
        .where(
            _may_message(clock),
            or_(User.last_weekly_date.is_(None), User.last_weekly_date < today),
        )
    )
    return list((await session.scalars(query.order_by(User.id))).all())


def days_away(user: User, today: date) -> int:
    if user.last_active_at is None:
        return 0
    return (today - user.last_active_at.astimezone(TASHKENT).date()).days


def reminder_text(user: User, task_text: str, today: date) -> str:
    streak = current_streak(user, today)
    streak_line = (
        t("reminder_streak", user.language, days=streak)
        if streak
        else t("reminder_streak_start", user.language)
    )
    key = "reminder_comeback" if days_away(user, today) >= COMEBACK_AFTER_DAYS else "reminder"
    return t(
        key,
        user.language,
        name=html.escape(user.nickname or ""),
        task=html.escape(task_text),
        streak=streak_line,
    )


def weekly_text(user: User, points: int, result: WeekResult | None, task_text: str | None) -> str:
    """Last week in three short lines, then the new week's task (if it is still open)."""
    lang = user.language
    lines = [t("weekly_points", lang, name=html.escape(user.nickname or ""), points=points)]
    if result is not None:
        lines.append(t("weekly_rank", lang, rank=result.rank))
        tier = t(f"league_tier_{result.tier_after}", lang)
        if result.tier_after > result.tier_before:
            lines.append(t("weekly_up", lang, tier=tier))
        elif result.tier_after < result.tier_before:
            lines.append(t("weekly_down", lang, tier=tier))
    lines.append("")
    if task_text:
        lines.append(t("weekly_task", lang, task=html.escape(task_text)))
    else:
        lines.append(t("weekly_go", lang))
    return "\n".join(lines)


async def week_points(session: AsyncSession, user_id: int, monday: date) -> int:
    total = await session.scalar(
        select(func.coalesce(func.sum(ActivityLog.points), 0)).where(
            ActivityLog.user_id == user_id,
            ActivityLog.local_date.between(monday, monday + timedelta(days=6)),
        )
    )
    return int(total or 0)


async def send_due_reminders(session: AsyncSession, bot: Bot, now: datetime | None = None) -> int:
    """Send every message that is due now. Returns how many were delivered."""
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


def _task_text(task: DailyTask | None, user: User) -> str | None:
    if task is None:
        return None
    return task.text.get(user.language) or task.text.get("uz", "")


async def _send_all(session: AsyncSession, bot: Bot, now: datetime, today: date) -> int:
    task = await task_of_the_day(session, today)
    sent = 0
    last_monday = today - timedelta(days=7)
    for user in await weekly_due_users(session, now):
        points = await week_points(session, user.id, last_monday)
        if points > 0:
            result = await result_of(session, user.id, last_monday)
            open_task = _task_text(task, user) if user.last_task_date != today else None
            message = weekly_text(user, points, result, open_task)
            if await _deliver(session, bot, user, message, start="weekly"):
                sent += 1
                track(session, user, "weekly_sent")
            # The summary takes the place of that day's reminder.
            user.last_reminder_date = today
        user.last_weekly_date = today
        await session.commit()
    if task is None:
        return sent
    for user in await due_users(session, now):
        message = reminder_text(user, _task_text(task, user) or "", today)
        if await _deliver(session, bot, user, message, start="reminder"):
            sent += 1
            track(session, user, "reminder_sent")
        # Marked even on failure, so one broken chat is not retried every minute.
        user.last_reminder_date = today
        await session.commit()
    return sent


async def _deliver(session: AsyncSession, bot: Bot, user: User, message: str, start: str) -> bool:
    try:
        await _send(bot, user, message, start)
        return True
    except TelegramForbiddenError:
        # The user blocked the bot: stop writing to them (TZ 8.5).
        user.reminders_enabled = False
        user.write_access = False
    except TelegramAPIError:
        log.exception("Message to user %s failed", user.id)
    finally:
        await asyncio.sleep(SEND_INTERVAL)
    return False


async def _send(bot: Bot, user: User, message: str, start: str) -> None:
    # startapp tells analytics where the launch came from (reminder_open, app_open source).
    keyboard = open_app_keyboard(user.language, start=start)
    try:
        await bot.send_message(user.telegram_id, message, reply_markup=keyboard)
    except TelegramRetryAfter as exc:
        await asyncio.sleep(exc.retry_after)
        await bot.send_message(user.telegram_id, message, reply_markup=keyboard)


async def reminder_loop(bot: Bot, every_seconds: int = 60) -> None:
    """Runs next to the bot; checks for due messages once a minute."""
    while True:
        try:
            async with SessionLocal() as session:
                sent = await send_due_reminders(session, bot)
            if sent:
                log.info("Sent %s reminders", sent)
        except Exception:
            log.exception("Reminder round failed")
        await asyncio.sleep(every_seconds)
