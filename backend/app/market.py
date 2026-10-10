"""Market (phase 9): things children made from waste, or no longer need.

A listing is seen by others only after a moderator approved it. Things change hands only at a
handover point run by adults: the owner brings the item and says their code, the new owner
collects it with theirs. Children never meet, chat or see each other's contacts; only
nicknames are shown.
"""

import asyncio
import html
import logging
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app import timeutil
from app.bot.handlers import open_app_keyboard
from app.db import SessionLocal, engine
from app.i18n import t
from app.models import (
    BannedWord,
    Listing,
    ListingPhoto,
    ListingRequest,
    ListingStatus,
    PickupPoint,
    RequestStatus,
    User,
    WordKind,
)

log = logging.getLogger(__name__)

MAX_PHOTOS = 3
MAX_LOOSE_PHOTOS = 10  # uploaded but not yet saved with a listing
LOOSE_PHOTO_TTL = timedelta(days=1)
MAX_PENDING = 3  # listings waiting for a moderator, per user
MAX_NEW_PER_DAY = 5
MAX_OPEN_REQUESTS = 3  # per requester
DROP_OFF_DAYS = 7  # to bring a promised item to the point
PICK_UP_DAYS = 14  # to collect it from there
REPORTS_TO_HIDE = 3  # different people

ITEM_TYPES = ("books", "toys", "clothes", "school", "sports", "other")
# For the admin panel, which is in Uzbek.
ITEM_TYPE_NAMES = {
    "books": "Kitoblar",
    "toys": "O'yinchoqlar",
    "clothes": "Kiyim",
    "school": "O'quv qurollari",
    "sports": "Sport anjomlari",
    "other": "Boshqa",
}
CONDITIONS = ("new", "good", "used")
REJECT_REASONS = ("personal_info", "face", "not_eco", "forbidden", "bad_photo", "other")
REPORT_REASONS = ("personal_info", "rude", "forbidden", "other")

OPEN_REQUEST = (RequestStatus.PENDING, RequestStatus.ACCEPTED, RequestStatus.AT_POINT)
HANDOVER = (RequestStatus.ACCEPTED, RequestStatus.AT_POINT)
# Statuses the owner can still change or remove; the rest are part of a handover.
EDITABLE = (
    ListingStatus.PENDING,
    ListingStatus.REJECTED,
    ListingStatus.APPROVED,
    ListingStatus.HIDDEN,
)

# Phone numbers, @usernames and links: contacts are not allowed in listings (TZ 11.3).
PHONE_LIKE = re.compile(r"[\d\s\-()+.]{7,}")
CONTACT = re.compile(r"(?<!\w)@[A-Za-z0-9_]{4,}|t\.me/|https?://|www\.", re.IGNORECASE)


class MarketError(Exception):
    def __init__(self, code: str, status: int = 409):
        super().__init__(code)
        self.code = code
        self.status = status


def has_contact(value: str) -> bool:
    if CONTACT.search(value):
        return True
    return any(sum(c.isdigit() for c in m.group()) >= 7 for m in PHONE_LIKE.finditer(value))


async def check_text(session: AsyncSession, *values: str) -> None:
    """No contacts and no words from the profanity list in the title or description."""
    if any(has_contact(v) for v in values):
        raise MarketError("contact_not_allowed", 422)
    words = await session.scalars(
        select(BannedWord.word).where(BannedWord.kind == WordKind.PROFANITY)
    )
    lowered = " ".join(values).lower()
    for word in words.all():
        # At a word start, so endings are caught ("word", "words") but not unrelated words.
        if re.search(rf"(?<!\w){re.escape(word.lower())}", lowered):
            raise MarketError("text_not_allowed", 422)


async def new_codes(session: AsyncSession, point_id: int, count: int) -> list[str]:
    """Six-digit codes not used by another handover at the same point."""
    rows = await session.execute(
        select(ListingRequest.drop_code, ListingRequest.pick_code)
        .join(Listing, Listing.id == ListingRequest.listing_id)
        .where(Listing.pickup_point_id == point_id, ListingRequest.status.in_(HANDOVER))
    )
    taken = {code for row in rows.all() for code in row if code}
    codes: list[str] = []
    while len(codes) < count:
        code = f"{secrets.randbelow(1_000_000):06d}"
        if code not in taken and code not in codes:
            codes.append(code)
    return codes


async def handover_of(session: AsyncSession, listing_id: int) -> ListingRequest | None:
    return await session.scalar(
        select(ListingRequest).where(
            ListingRequest.listing_id == listing_id, ListingRequest.status.in_(HANDOVER)
        )
    )


async def point_text(session: AsyncSession, point_id: int | None, lang: str) -> tuple[str, str]:
    point = await session.get(PickupPoint, point_id) if point_id else None
    if point is None:
        return "", ""
    pick = lambda value: value.get(lang) or value.get("uz", "")  # noqa: E731
    return f"{pick(point.name)}, {pick(point.address)}", pick(point.hours)


# ---------------------------------------------------------------- notifications


@dataclass
class Note:
    """A bot message to send after the change is committed."""

    chat_id: int
    language: str
    key: str
    params: dict[str, Any] = field(default_factory=dict)


def note(user: User | None, key: str, **params: Any) -> list[Note]:
    if user is None or not user.write_access or user.is_blocked:
        return []
    escaped = {k: html.escape(str(v)) if isinstance(v, str) else v for k, v in params.items()}
    return [Note(user.telegram_id, user.language, key, escaped)]


def render(item: Note) -> str:
    params = dict(item.params)
    if "reason" in params:
        params["reason"] = t(f"market_reason_{params['reason']}", item.language)
    if params.get("note"):
        params["note"] = t("market_note", item.language, note=params["note"])
    else:
        params["note"] = ""
    return t(item.key, item.language, **params)


async def deliver(bot: Bot | None, notes: list[Note]) -> None:
    """Send after the response; a blocked bot or a network error only skips the message."""
    if bot is None:
        return
    for item in notes:
        keyboard = open_app_keyboard(item.language, start="market")
        try:
            await bot.send_message(item.chat_id, render(item), reply_markup=keyboard)
        except TelegramAPIError:
            log.warning("Market message %s was not delivered", item.key)


# ------------------------------------------------------------------ handovers


async def notes_for_decline(session: AsyncSession, listing: Listing, key: str) -> list[Note]:
    """Decline every request still waiting for the owner's answer."""
    waiting = await session.scalars(
        select(ListingRequest).where(
            ListingRequest.listing_id == listing.id,
            ListingRequest.status == RequestStatus.PENDING,
        )
    )
    notes: list[Note] = []
    now = timeutil.utc_now()
    for request in waiting.all():
        request.status = RequestStatus.DECLINED
        request.decided_at = now
        notes += note(await session.get(User, request.requester_id), key, title=listing.title)
    return notes


async def end_handover(
    session: AsyncSession, listing: Listing, request: ListingRequest, status: RequestStatus
) -> None:
    """Close an accepted request that did not end in a handover. The listing returns to the
    market; an item that already reached the point stays there for the next taker."""
    if request.status == RequestStatus.AT_POINT:
        listing.stored_at_point = True
    request.status = status
    request.decided_at = timeutil.utc_now()
    if listing.status in (ListingStatus.RESERVED, ListingStatus.AT_POINT):
        listing.status = ListingStatus.APPROVED


async def expire_handovers(session: AsyncSession, now: datetime | None = None) -> list[Note]:
    """Promised items never brought to the point, and items never collected from it."""
    now = now or timeutil.utc_now()
    due = await session.execute(
        select(ListingRequest, Listing)
        .join(Listing, Listing.id == ListingRequest.listing_id)
        .where(
            (
                (ListingRequest.status == RequestStatus.ACCEPTED)
                & (ListingRequest.decided_at < now - timedelta(days=DROP_OFF_DAYS))
            )
            | (
                (ListingRequest.status == RequestStatus.AT_POINT)
                & (ListingRequest.dropped_at < now - timedelta(days=PICK_UP_DAYS))
            )
        )
    )
    notes: list[Note] = []
    for request, listing in due.all():
        never_brought = request.status == RequestStatus.ACCEPTED
        await end_handover(session, listing, request, RequestStatus.EXPIRED)
        requester = await session.get(User, request.requester_id)
        if never_brought:
            notes += note(requester, "market_expired", title=listing.title)
            notes += note(
                await session.get(User, listing.owner_id), "market_expired", title=listing.title
            )
        else:
            notes += note(requester, "market_not_collected", title=listing.title)
    return notes


async def remove_loose_photos(session: AsyncSession, now: datetime | None = None) -> int:
    """Photos uploaded but never saved with a listing."""
    now = now or timeutil.utc_now()
    result = await session.execute(
        delete(ListingPhoto).where(
            ListingPhoto.listing_id.is_(None), ListingPhoto.created_at < now - LOOSE_PHOTO_TTL
        )
    )
    return result.rowcount or 0


async def before_account_deletion(session: AsyncSession, user: User) -> None:
    """Handovers already under way survive the deletion of either side (QM-17).

    An item at the point stays there, anonymous, for the person collecting it. A requester
    who leaves releases the item: back to the market, or kept at the point for the next one.
    """
    at_point = (
        select(Listing.id)
        .where(
            Listing.owner_id == user.id,
            (Listing.status == ListingStatus.AT_POINT) | Listing.stored_at_point.is_(True),
        )
        .scalar_subquery()
    )
    await session.execute(
        update(ListingPhoto).where(ListingPhoto.listing_id.in_(at_point)).values(owner_id=None)
    )
    await session.execute(
        update(Listing)
        .where(
            Listing.owner_id == user.id,
            (Listing.status == ListingStatus.AT_POINT) | Listing.stored_at_point.is_(True),
        )
        .values(owner_id=None)
    )
    mine = await session.execute(
        select(ListingRequest, Listing)
        .join(Listing, Listing.id == ListingRequest.listing_id)
        .where(ListingRequest.requester_id == user.id, ListingRequest.status.in_(HANDOVER))
    )
    for request, listing in mine.all():
        await end_handover(session, listing, request, RequestStatus.CANCELLED)
    await session.flush()


# ------------------------------------------------------------------ background

LOCK_KEY = 73_6202


async def market_round(bot: Bot | None) -> None:
    async with engine.connect() as lock_conn:
        if not await lock_conn.scalar(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}):
            return
        try:
            async with SessionLocal() as session:
                notes = await expire_handovers(session)
                removed = await remove_loose_photos(session)
                await session.commit()
            if notes or removed:
                log.info(
                    "Market: %s handovers expired, %s loose photos removed", len(notes), removed
                )
            await deliver(bot, notes)
        finally:
            await lock_conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})


async def market_loop(bot: Bot, every_seconds: int = 600) -> None:
    """Runs in the bot process next to the reminders."""
    while True:
        try:
            await market_round(bot)
        except Exception:
            log.exception("Market round failed")
        await asyncio.sleep(every_seconds)
