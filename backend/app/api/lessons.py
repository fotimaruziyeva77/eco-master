"""Ready-made lessons for teachers (TZ 8.9, QM-15)."""

import html
from typing import Annotated, NamedTuple

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError
from aiogram.types import BufferedInputFile
from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import track
from app.deps import BotDep, CurrentUser, SessionDep
from app.i18n import DEFAULT_LANGUAGE, t
from app.models import ContentStatus, TeacherLesson
from app.pdf import lesson_pdf
from app.schemas import Language, LessonOut, LessonSendIn, LessonSummaryOut

router = APIRouter(prefix="/lessons", tags=["lessons"])


async def get_lesson(session: AsyncSession, slug: str) -> TeacherLesson:
    lesson = await session.scalar(
        select(TeacherLesson).where(
            TeacherLesson.slug == slug, TeacherLesson.status == ContentStatus.PUBLISHED
        )
    )
    if lesson is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "lesson_not_found")
    return lesson


class RenderedPdf(NamedTuple):
    content: bytes
    filename: str
    title: str
    lang: str  # the language actually used


def render(lesson: TeacherLesson, lang: str) -> RenderedPdf:
    """The lesson PDF in the requested language (Uzbek as a fallback)."""
    if lang not in (lesson.body or {}):
        lang = DEFAULT_LANGUAGE
    title = lesson.title.get(lang) or lesson.title.get(DEFAULT_LANGUAGE) or lesson.slug
    pdf = lesson_pdf(
        lesson.slug,
        lesson.updated_at.isoformat(),
        lang,
        title,
        lesson.grade,
        (lesson.body or {}).get(lang) or {},
    )
    return RenderedPdf(pdf, f"eco-master-{lesson.slug}-{lang}.pdf", title, lang)


@router.get("")
async def lessons(user: CurrentUser, session: SessionDep) -> list[LessonSummaryOut]:
    rows = await session.scalars(
        select(TeacherLesson)
        .where(TeacherLesson.status == ContentStatus.PUBLISHED)
        .order_by(TeacherLesson.sort_order, TeacherLesson.id)
    )
    return [LessonSummaryOut(slug=r.slug, title=r.title, grade=r.grade) for r in rows.all()]


@router.get("/{slug}")
async def lesson(slug: str, user: CurrentUser, session: SessionDep) -> LessonOut:
    row = await get_lesson(session, slug)
    return LessonOut(slug=row.slug, title=row.title, grade=row.grade, body=row.body)


@router.get("/{slug}/pdf")
async def lesson_pdf_file(
    slug: str,
    user: CurrentUser,
    session: SessionDep,
    lang: Annotated[Language | None, Query()] = None,
) -> Response:
    lesson = await get_lesson(session, slug)
    pdf = render(lesson, lang or user.language)
    track(session, user, "teacher_pdf", lesson=lesson.slug, lang=pdf.lang, via="download")
    await session.commit()
    return pdf_response(pdf)


def pdf_response(pdf: RenderedPdf) -> Response:
    return Response(
        content=pdf.content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf.filename}"'},
    )


@router.post("/{slug}/send")
async def send_lesson_pdf(
    slug: str, body: LessonSendIn, user: CurrentUser, session: SessionDep, bot: BotDep
) -> dict:
    """The bot sends the PDF to the user's Telegram chat — the most reliable way inside Telegram."""
    if bot is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "bot_not_configured")
    lesson = await get_lesson(session, slug)
    pdf = render(lesson, body.language or user.language)
    try:
        await bot.send_document(
            chat_id=user.telegram_id,
            document=BufferedInputFile(pdf.content, filename=pdf.filename),
            caption=t("pdf_caption", pdf.lang, title=html.escape(pdf.title)),
        )
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        # Blocked bot, or the user never opened the bot chat: they need to press /start.
        user.write_access = False
        await session.commit()
        raise HTTPException(status.HTTP_409_CONFLICT, "bot_not_started") from exc
    except TelegramAPIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "telegram_error") from exc
    track(session, user, "teacher_pdf", lesson=lesson.slug, lang=pdf.lang, via="chat")
    await session.commit()
    return {"sent": True}
