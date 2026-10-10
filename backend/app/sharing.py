"""Share messages (TZ 8.11): one text for the Mini App and for the bot's inline mode."""

import re
import uuid
from typing import Literal, get_args

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.i18n import DEFAULT_LANGUAGE, t
from app.models import ActivityLog, Badge, ContentStatus, Project, User

ShareKind = Literal["progress", "project", "badge", "quiz", "sort"]
SHARE_KINDS: tuple[str, ...] = get_args(ShareKind)

SCORE = re.compile(r"(\d{1,3})/(\d{1,3})")


class ShareError(Exception):
    """The object to share does not exist or the score is malformed."""

    def __init__(self, code: str, status: int):
        super().__init__(code)
        self.code = code
        self.status = status


async def share_text(
    session: AsyncSession, user: User, kind: ShareKind, object_id: str | None
) -> str:
    lang = user.language
    if kind == "progress":
        projects = await session.scalar(
            select(func.count())
            .select_from(ActivityLog)
            .where(ActivityLog.user_id == user.id, ActivityLog.action == "project_done")
        )
        # Never brag about zeros: fall back to points, then to a plain invitation.
        if projects:
            return t("share_progress", lang, projects=projects, points=user.points_total)
        if user.points_total:
            return t("share_points", lang, points=user.points_total)
        return t("share_invite", lang)
    if kind == "project":
        project = await session.scalar(
            select(Project).where(
                Project.slug == object_id, Project.status == ContentStatus.PUBLISHED
            )
        )
        if project is None:
            raise ShareError("project_not_found", 404)
        title = project.title.get(lang) or project.title[DEFAULT_LANGUAGE]
        return t("share_project", lang, title=title)
    if kind == "badge":
        badge = await session.scalar(select(Badge).where(Badge.code == object_id))
        if badge is None:
            raise ShareError("badge_not_found", 404)
        name = badge.name.get(lang) or badge.name[DEFAULT_LANGUAGE]
        return t("share_badge", lang, badge=name)
    match = SCORE.fullmatch(object_id or "")
    if not match or int(match[1]) > int(match[2]) or int(match[2]) == 0:
        raise ShareError("invalid_score", 422)
    return t(f"share_{kind}", lang, correct=match[1], total=match[2])


def share_url(settings: Settings) -> str:
    """Link under the message; startapp marks where newcomers came from (stored as source)."""
    if settings.bot_username:
        return f"{settings.app_link}?startapp=share"
    return settings.app_link


def share_article(lang: str, text: str, url: str) -> InlineQueryResultArticle:
    """The message friends receive, with a button that opens the app (QM-16)."""
    return InlineQueryResultArticle(
        id=uuid.uuid4().hex,
        title=t("share_title", lang),
        description=text,
        input_message_content=InputTextMessageContent(message_text=text),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t("open_app", lang), url=url)]]
        ),
    )


def inline_query_for(kind: ShareKind, object_id: str | None) -> str:
    """Query typed after @bot by switchInlineQuery on clients without shareMessage."""
    return f"{kind} {object_id}" if object_id else kind


def parse_inline_query(query: str) -> tuple[ShareKind, str | None]:
    kind, _, object_id = query.strip().partition(" ")
    if kind not in SHARE_KINDS:
        return "progress", None
    return kind, object_id.strip() or None  # type: ignore[return-value]
