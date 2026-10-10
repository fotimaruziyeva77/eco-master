"""Statistics, suspicious activity and CSV export (TZ 8.12, 11.1, 19)."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response

from app.admin.deps import AdminOnly
from app.admin.moderation import fast_flags, points_flags
from app.admin.schemas import FastFlagOut, FlagsOut, PointsFlagOut
from app.admin.stats import (
    USERS_CSV_HEADER,
    AdminStatsOut,
    QuestionStatOut,
    day_start,
    overview,
    project_stats,
    question_stats,
    to_csv,
    users_csv_rows,
)
from app.deps import SessionDep
from app.timeutil import local_today

router = APIRouter(prefix="/stats", tags=["admin-stats"])

Days = Annotated[int, Query(ge=1, le=365)]


def since(days: int) -> datetime:
    return day_start(local_today() - timedelta(days=days - 1))


@router.get("")
async def stats(admin: AdminOnly, session: SessionDep, days: Days = 30) -> AdminStatsOut:
    return await overview(session, days)


@router.get("/questions")
async def questions(
    admin: AdminOnly, session: SessionDep, days: Days | None = None
) -> list[QuestionStatOut]:
    """Correct-answer rate per question; without `days`, over all time."""
    return await question_stats(session, since(days) if days else None)


@router.get("/flags")
async def flags(admin: AdminOnly, session: SessionDep, days: Days = 14) -> FlagsOut:
    """Suspicious activity (TZ 11.1): > 300 points a day, or rounds answered too fast."""
    first = local_today() - timedelta(days=days - 1)
    return FlagsOut(
        points=[
            PointsFlagOut(user_id=u, nickname=n, day=d, points=p)
            for u, n, d, p in await points_flags(session, first)
        ],
        fast=[
            FastFlagOut(
                user_id=u,
                nickname=n,
                game="quiz" if name == "quiz_answer" else "sort",
                day=d,
                answers=answers,
                avg_seconds=round(avg, 2),
            )
            for u, n, name, d, answers, avg in await fast_flags(
                session, datetime.now(UTC) - timedelta(days=days)
            )
        ],
    )


def csv_response(name: str, body: str) -> Response:
    stamp = local_today().isoformat()
    return Response(
        content=body.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="ekoustoz-{name}-{stamp}.csv"'},
    )


@router.get("/export/{kind}")
async def export_csv(
    kind: Literal["daily", "questions", "projects", "users"],
    admin: AdminOnly,
    session: SessionDep,
    days: Days = 30,
) -> Response:
    """CSV for spreadsheets (TZ 8.12). The user list has no Telegram ids (TZ 11.2)."""
    if kind == "daily":
        data = await overview(session, days)
        header = ["day", "new_users", "dau", "daily_tasks", "projects_done", "quiz_answers"]
        rows = [
            [d.day.isoformat(), d.new_users, d.dau, d.daily_tasks, d.projects_done, d.quiz_answers]
            for d in data.daily
        ]
    elif kind == "questions":
        header = ["id", "category", "question", "answers", "correct", "correct_rate", "flag"]
        rows = [
            [
                q.id,
                q.category,
                q.text,
                q.answers,
                q.correct,
                q.rate if q.rate is not None else "",
                q.flag or "",
            ]
            for q in await question_stats(session, since(days))
        ]
    elif kind == "projects":
        header = ["id", "slug", "title", "views", "viewers", "video_plays", "done"]
        rows = [
            [p.id, p.slug, p.title, p.views, p.viewers, p.video_plays, p.done]
            for p in await project_stats(session, since(days))
        ]
    else:
        header = USERS_CSV_HEADER
        rows = await users_csv_rows(session)
    return csv_response(kind, to_csv(header, rows))
