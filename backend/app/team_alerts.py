"""Tells the team's chat when something waits for a moderator (stage 7).

Every few minutes the bot looks at the queue: market listings waiting for review, listings with
open complaints and nickname complaints. A message goes out only when something new arrived since
the last one, and at most once in MIN_GAP, so a busy day is a few messages, not one per listing.
The chat is MODERATION_CHAT_ID, or the feedback chat when that is not set.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import SessionLocal
from app.models import Listing, ListingReport, ListingStatus, Report, ReportStatus

log = logging.getLogger(__name__)

MIN_GAP = timedelta(minutes=30)


@dataclass(frozen=True)
class Queue:
    pending: int
    reported: int
    nicknames: int
    # When the newest of the waiting things arrived.
    newest: datetime | None

    @property
    def total(self) -> int:
        return self.pending + self.reported + self.nicknames


@dataclass
class AlertState:
    sent_at: datetime | None = None
    newest: datetime | None = None


async def moderation_queue(session: AsyncSession) -> Queue:
    pending, pending_newest = (
        await session.execute(
            select(func.count(), func.max(Listing.submitted_at)).where(
                Listing.status == ListingStatus.PENDING
            )
        )
    ).one()
    reported, reported_newest = (
        await session.execute(
            select(
                func.count(func.distinct(ListingReport.listing_id)),
                func.max(ListingReport.created_at),
            ).where(ListingReport.status == ReportStatus.OPEN)
        )
    ).one()
    nicknames, nicknames_newest = (
        await session.execute(
            select(
                func.count(func.distinct(Report.target_user_id)), func.max(Report.created_at)
            ).where(Report.status == ReportStatus.OPEN)
        )
    ).one()
    stamps = [s for s in (pending_newest, reported_newest, nicknames_newest) if s is not None]
    return Queue(pending, reported, nicknames, max(stamps) if stamps else None)


def alert_text(queue: Queue) -> str:
    lines = ["🛡 <b>Moderator kutilmoqda</b>"]
    if queue.pending:
        lines.append(f"🛍 Bozorga yangi e'lonlar: {queue.pending}")
    if queue.reported:
        lines.append(f"🚩 Shikoyat qilingan e'lonlar: {queue.reported}")
    if queue.nicknames:
        lines.append(f"👤 Taxallus shikoyatlari: {queue.nicknames}")
    return "\n".join(lines)


def alert_keyboard(settings: Settings, queue: Queue) -> InlineKeyboardMarkup | None:
    site = urlsplit(settings.webapp_url)
    if site.scheme != "https":
        return None
    admin = f"https://{site.netloc}/admin"
    buttons = []
    if queue.pending or queue.reported:
        buttons.append(InlineKeyboardButton(text="Bozor", url=f"{admin}/market"))
    if queue.nicknames:
        buttons.append(InlineKeyboardButton(text="Shikoyatlar", url=f"{admin}/reports"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None


def should_alert(queue: Queue, state: AlertState, now: datetime) -> bool:
    if queue.total == 0 or queue.newest is None:
        return False
    if state.newest is not None and queue.newest <= state.newest:
        return False  # nothing new since the last message
    return state.sent_at is None or now - state.sent_at >= MIN_GAP


async def alert_round(
    session: AsyncSession, bot: Bot, state: AlertState, now: datetime | None = None
) -> bool:
    settings = get_settings()
    chat_id = settings.moderation_chat_id or settings.feedback_chat_id
    if not chat_id:
        return False
    now = now or datetime.now(UTC)
    queue = await moderation_queue(session)
    if not should_alert(queue, state, now):
        return False
    try:
        await bot.send_message(
            chat_id, alert_text(queue), reply_markup=alert_keyboard(settings, queue)
        )
    except TelegramAPIError:
        log.exception("Could not tell the team about the moderation queue")
        return False
    state.sent_at, state.newest = now, queue.newest
    return True


async def team_alert_loop(bot: Bot, every_seconds: int = 300) -> None:
    """Runs in the bot process next to the reminders."""
    state = AlertState()
    while True:
        try:
            async with SessionLocal() as session:
                await alert_round(session, bot, state)
        except Exception:
            log.exception("Moderation alert round failed")
        await asyncio.sleep(every_seconds)
