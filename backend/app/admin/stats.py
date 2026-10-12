"""Statistics of the admin panel (TZ 8.12) and the success criteria (TZ 19).

Days are Tashkent calendar days (TZ 4). Activity comes from the analytics events (TZ 14)
and the activity log; deleted accounts drop out of user-based numbers.
"""

import csv
import io
from datetime import date, datetime, time, timedelta
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import Date, and_, cast, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActivityLog,
    AnalyticsEvent,
    Category,
    OnboardingStep,
    Project,
    Question,
    TeacherLesson,
    User,
)
from app.timeutil import TASHKENT, local_today, week_start

HARD_QUESTION_RATE = 0.3  # below: too hard or a wrong answer key
EASY_QUESTION_RATE = 0.95
MIN_ANSWERS_FOR_FLAG = 10


class RateOut(BaseModel):
    size: int
    value: int
    rate: float | None


class CriterionOut(BaseModel):
    key: str
    label: str
    target: float
    value: float | None
    ok: bool | None
    unit: Literal["percent", "count"]


class DayStatOut(BaseModel):
    day: date
    new_users: int
    dau: int
    daily_tasks: int
    projects_done: int
    quiz_answers: int


class SourceOut(BaseModel):
    source: str
    users: int


class FunnelOut(BaseModel):
    started: int
    language: int
    path: int
    nickname: int
    done: int


class ProjectStatOut(BaseModel):
    id: int
    slug: str
    title: str
    views: int
    viewers: int
    video_plays: int
    done: int


class LessonStatOut(BaseModel):
    slug: str
    title: str
    downloads: int
    sent_to_chat: int


class AdminStatsOut(BaseModel):
    start: date
    end: date
    users_total: int
    users_onboarded: int
    new_users: int
    dau_today: int
    wau: int
    mau: int
    d1: RateOut
    d7: RateOut
    onboarding: RateOut
    lesson_and_task: RateOut
    funnel: FunnelOut
    criteria: list[CriterionOut]
    daily: list[DayStatOut]
    sources: list[SourceOut]
    projects: list[ProjectStatOut]
    lessons: list[LessonStatOut]


class QuestionStatOut(BaseModel):
    id: int
    text: str
    category: str
    answers: int
    correct: int
    rate: float | None
    flag: Literal["hard", "easy"] | None


# A literal, not a bound parameter: GROUP BY must see the very same expression as SELECT.
TASHKENT_SQL = literal_column("'Asia/Tashkent'")


def local_day(column):
    """Tashkent calendar day of a timestamp column."""
    return cast(func.timezone(TASHKENT_SQL, column), Date)


def day_start(day: date) -> datetime:
    return datetime.combine(day, time.min, TASHKENT)


def _rate(size: int, value: int) -> RateOut:
    return RateOut(size=size, value=value, rate=round(value / size, 4) if size else None)


async def _per_day(session: AsyncSession, query) -> dict[date, int]:
    return {day: count for day, count in (await session.execute(query)).all()}


async def overview(session: AsyncSession, days: int) -> AdminStatsOut:
    today = local_today()
    start = today - timedelta(days=days - 1)
    since = day_start(start)
    opens = AnalyticsEvent.name == "app_open"

    users_total = await session.scalar(select(func.count()).select_from(User))
    users_onboarded = await session.scalar(
        select(func.count()).select_from(User).where(User.onboarding_step == OnboardingStep.DONE)
    )

    async def distinct_openers(first: date) -> int:
        return await session.scalar(
            select(func.count(func.distinct(AnalyticsEvent.user_id))).where(
                opens, AnalyticsEvent.created_at >= day_start(first)
            )
        )

    new_by_day = await _per_day(
        session,
        select(local_day(User.created_at), func.count())
        .where(User.created_at >= since)
        .group_by(local_day(User.created_at)),
    )
    dau_by_day = await _per_day(
        session,
        select(
            local_day(AnalyticsEvent.created_at), func.count(func.distinct(AnalyticsEvent.user_id))
        )
        .where(opens, AnalyticsEvent.created_at >= since)
        .group_by(local_day(AnalyticsEvent.created_at)),
    )
    quiz_by_day = await _per_day(
        session,
        select(local_day(AnalyticsEvent.created_at), func.count())
        .where(AnalyticsEvent.name == "quiz_answer", AnalyticsEvent.created_at >= since)
        .group_by(local_day(AnalyticsEvent.created_at)),
    )

    async def log_by_day(action: str) -> dict[date, int]:
        return await _per_day(
            session,
            select(ActivityLog.local_date, func.count())
            .where(ActivityLog.action == action, ActivityLog.local_date >= start)
            .group_by(ActivityLog.local_date),
        )

    tasks_by_day = await log_by_day("daily_task")
    projects_by_day = await log_by_day("project_done")
    daily = [
        DayStatOut(
            day=day,
            new_users=new_by_day.get(day, 0),
            dau=dau_by_day.get(day, 0),
            daily_tasks=tasks_by_day.get(day, 0),
            projects_done=projects_by_day.get(day, 0),
            quiz_answers=quiz_by_day.get(day, 0),
        )
        for day in (start + timedelta(days=i) for i in range(days))
    ]

    # Cohort of the period: registration day per user, launch days per user.
    cohort = dict(
        (
            await session.execute(
                select(User.id, local_day(User.created_at)).where(User.created_at >= since)
            )
        ).all()
    )
    launches: set[tuple[int, date]] = set()
    if cohort:
        rows = await session.execute(
            select(AnalyticsEvent.user_id, local_day(AnalyticsEvent.created_at))
            .where(
                opens, AnalyticsEvent.user_id.in_(list(cohort)), AnalyticsEvent.created_at >= since
            )
            .distinct()
        )
        launches = {(user_id, day) for user_id, day in rows.all()}

    def retention(offset: int) -> RateOut:
        eligible = [uid for uid, d0 in cohort.items() if d0 + timedelta(days=offset) <= today]
        kept = sum((uid, cohort[uid] + timedelta(days=offset)) in launches for uid in eligible)
        return _rate(len(eligible), kept)

    steps = dict(
        (
            await session.execute(
                select(User.onboarding_step, func.count())
                .where(User.created_at >= since)
                .group_by(User.onboarding_step)
            )
        ).all()
    )
    order = list(OnboardingStep)

    def reached(step: OnboardingStep) -> int:
        return sum(n for s, n in steps.items() if order.index(s) >= order.index(step))

    funnel = FunnelOut(
        started=sum(steps.values()),
        language=reached(OnboardingStep.PATH),
        path=reached(OnboardingStep.NICKNAME),
        nickname=reached(OnboardingStep.INTRO),
        done=reached(OnboardingStep.DONE),
    )

    # TZ 19: at least one video lesson (project) and one daily task.
    did = (
        select(ActivityLog.user_id)
        .where(ActivityLog.user_id.in_(list(cohort)))
        .group_by(ActivityLog.user_id)
        .having(
            func.count().filter(ActivityLog.action == "project_done") > 0,
            func.count().filter(ActivityLog.action == "daily_task") > 0,
        )
    )
    lesson_and_task = len((await session.scalars(did)).all()) if cohort else 0

    d1, d7 = retention(1), retention(7)
    onboarding = _rate(funnel.started, funnel.done)
    both = _rate(len(cohort), lesson_and_task)
    criteria = [
        _criterion("onboarding", "Onboardingni tugatganlar", 0.8, onboarding),
        _criterion("d1", "D1 — ertasi kuni qaytganlar", 0.3, d1),
        _criterion("d7", "D7 — 7-kuni qaytganlar", 0.15, d7),
        _criterion("lesson_and_task", "Video dars va topshiriq bajarganlar", 0.5, both),
        CriterionOut(
            key="users",
            label="Ro'yxatdan o'tganlar",
            target=100,
            value=len(cohort),
            ok=len(cohort) >= 100,
            unit="count",
        ),
    ]
    return AdminStatsOut(
        start=start,
        end=today,
        users_total=users_total,
        users_onboarded=users_onboarded,
        new_users=len(cohort),
        dau_today=dau_by_day.get(today, 0),
        wau=await distinct_openers(today - timedelta(days=6)),
        mau=await distinct_openers(today - timedelta(days=29)),
        d1=d1,
        d7=d7,
        onboarding=onboarding,
        lesson_and_task=both,
        funnel=funnel,
        criteria=criteria,
        daily=daily,
        sources=await _sources(session, since),
        projects=await project_stats(session, since),
        lessons=await _lesson_stats(session, since),
    )


def _criterion(key: str, label: str, target: float, rate: RateOut) -> CriterionOut:
    return CriterionOut(
        key=key,
        label=label,
        target=target,
        value=rate.rate,
        ok=None if rate.rate is None else rate.rate >= target,
        unit="percent",
    )


async def _sources(session: AsyncSession, since: datetime) -> list[SourceOut]:
    source = func.coalesce(User.source, "direct")
    rows = await session.execute(
        select(source, func.count())
        .where(User.created_at >= since)
        .group_by(source)
        .order_by(func.count().desc())
        .limit(15)
    )
    return [SourceOut(source=s, users=n) for s, n in rows.all()]


async def project_stats(session: AsyncSession, since: datetime) -> list[ProjectStatOut]:
    slug = AnalyticsEvent.props["project"].astext
    events = (
        select(
            slug.label("slug"),
            func.count().filter(AnalyticsEvent.name == "project_view").label("views"),
            func.count(func.distinct(AnalyticsEvent.user_id))
            .filter(AnalyticsEvent.name == "project_view")
            .label("viewers"),
            func.count().filter(AnalyticsEvent.name == "video_play").label("plays"),
        )
        .where(
            AnalyticsEvent.name.in_(("project_view", "video_play")),
            AnalyticsEvent.created_at >= since,
        )
        .group_by(slug)
        .subquery()
    )
    done = (
        select(ActivityLog.object_id, func.count().label("done"))
        .where(ActivityLog.action == "project_done", ActivityLog.created_at >= since)
        .group_by(ActivityLog.object_id)
        .subquery()
    )
    rows = await session.execute(
        select(Project, events.c.views, events.c.viewers, events.c.plays, done.c.done)
        .outerjoin(events, events.c.slug == Project.slug)
        .outerjoin(done, done.c.object_id == cast(Project.id, ActivityLog.object_id.type))
        .order_by(
            func.coalesce(events.c.views, 0).desc(),
            func.coalesce(done.c.done, 0).desc(),
            Project.sort_order,
        )
    )
    return [
        ProjectStatOut(
            id=p.id,
            slug=p.slug,
            title=p.title.get("uz", p.slug),
            views=views or 0,
            viewers=viewers or 0,
            video_plays=plays or 0,
            done=n or 0,
        )
        for p, views, viewers, plays, n in rows.all()
    ]


async def _lesson_stats(session: AsyncSession, since: datetime) -> list[LessonStatOut]:
    slug = AnalyticsEvent.props["lesson"].astext
    via = AnalyticsEvent.props["via"].astext
    counts = (
        select(
            slug.label("slug"),
            func.count().filter(via == "download").label("downloads"),
            func.count().filter(via == "chat").label("sent"),
        )
        .where(AnalyticsEvent.name == "teacher_pdf", AnalyticsEvent.created_at >= since)
        .group_by(slug)
        .subquery()
    )
    rows = await session.execute(
        select(TeacherLesson, counts.c.downloads, counts.c.sent)
        .outerjoin(counts, counts.c.slug == TeacherLesson.slug)
        .order_by(TeacherLesson.sort_order, TeacherLesson.id)
    )
    return [
        LessonStatOut(
            slug=lesson.slug,
            title=lesson.title.get("uz", lesson.slug),
            downloads=downloads or 0,
            sent_to_chat=sent or 0,
        )
        for lesson, downloads, sent in rows.all()
    ]


async def question_stats(session: AsyncSession, since: datetime | None) -> list[QuestionStatOut]:
    """Correct-answer rate per question, to find questions that are too hard or wrong."""
    qid = AnalyticsEvent.props["question_id"].as_integer()
    conditions = [AnalyticsEvent.name == "quiz_answer"]
    if since is not None:
        conditions.append(AnalyticsEvent.created_at >= since)
    answers = (
        select(
            qid.label("qid"),
            func.count().label("answers"),
            func.count()
            .filter(AnalyticsEvent.props["correct"].as_boolean().is_(True))
            .label("correct"),
        )
        .where(and_(*conditions))
        .group_by(qid)
        .subquery()
    )
    rows = await session.execute(
        select(Question, Category.name, answers.c.answers, answers.c.correct)
        .outerjoin(Category, Category.id == Question.category_id)
        .outerjoin(answers, answers.c.qid == Question.id)
        .order_by(Question.sort_order, Question.id)
    )
    out = []
    for question, category, total, correct in rows.all():
        total, correct = total or 0, correct or 0
        rate = round(correct / total, 4) if total else None
        flag = None
        if rate is not None and total >= MIN_ANSWERS_FOR_FLAG:
            flag = (
                "hard"
                if rate < HARD_QUESTION_RATE
                else "easy"
                if rate > EASY_QUESTION_RATE
                else None
            )
        out.append(
            QuestionStatOut(
                id=question.id,
                text=question.text.get("uz", ""),
                category=(category or {}).get("uz", "Umumiy ekologiya"),
                answers=total,
                correct=correct,
                rate=rate,
                flag=flag,
            )
        )
    return out


# ----------------------------------------------------------------------- CSV

FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def _cell(value: object) -> object:
    """Spreadsheet apps run cells starting with = + - @ as formulas; keep them as text."""
    if isinstance(value, str) and value.startswith(FORMULA_START):
        return "'" + value
    return value


def to_csv(header: list[str], rows: list[list[object]]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(header)
    writer.writerows([[_cell(v) for v in row] for row in rows])
    # The BOM makes Excel read the file as UTF-8 (Uzbek and Russian text).
    return "﻿" + out.getvalue()


async def users_csv_rows(session: AsyncSession) -> list[list[object]]:
    """No Telegram ids or anything else that identifies a person (TZ 11.2)."""
    rows = await session.scalars(select(User).order_by(User.id))
    return [
        [
            u.id,
            u.nickname or "",
            u.language,
            u.path.value if u.path else "",
            u.source or "",
            u.created_at.astimezone(TASHKENT).strftime("%Y-%m-%d %H:%M"),
            u.onboarding_step.value,
            u.points_total,
            u.streak_best,
            u.last_active_at.astimezone(TASHKENT).strftime("%Y-%m-%d %H:%M"),
            int(u.is_blocked),
            int(u.nickname_hidden),
        ]
        for u in rows.all()
    ]


USERS_CSV_HEADER = [
    "id",
    "nickname",
    "language",
    "path",
    "source",
    "created_at",
    "onboarding",
    "points",
    "streak_best",
    "last_active_at",
    "blocked",
    "nickname_hidden",
]


# ---------------------------------------------------------------- growth (stage 7)

COHORT_WEEKS = 8
BOT_MESSAGES = (
    ("reminder", "reminder_sent", "reminder_open"),
    ("weekly", "weekly_sent", "weekly_open"),
    ("broadcast", "broadcast_sent", "broadcast_open"),
)


class ActivationOut(BaseModel):
    """Users who registered in the period and how far they got."""

    registered: int
    onboarded: int
    first_points: int
    daily_task: int
    # Opened the app on at least two different days.
    returned: int
    # Opened it 7–13 days after registering, of those registered at least a week ago.
    second_week: RateOut


class CohortOut(BaseModel):
    week_start: date
    size: int
    # Share of the cohort that opened the app in week 1, 2, … after the one they joined in;
    # None for weeks still to come.
    weeks: list[float | None]


class BotMessageOut(BaseModel):
    kind: Literal["reminder", "weekly", "broadcast"]
    sent: int
    opened: int
    rate: float | None


class GrowthOut(BaseModel):
    activation: ActivationOut
    cohorts: list[CohortOut]
    messages: list[BotMessageOut]
    stories: int


async def growth(session: AsyncSession, days: int) -> GrowthOut:
    today = local_today()
    since = day_start(today - timedelta(days=days - 1))
    opens = AnalyticsEvent.name == "app_open"

    joined = dict(
        (
            await session.execute(
                select(User.id, local_day(User.created_at)).where(User.created_at >= since)
            )
        ).all()
    )
    ids = list(joined)
    onboarded = first_points = daily_task = returned = 0
    week_two = _rate(0, 0)
    if ids:
        onboarded = await session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.id.in_(ids), User.onboarding_step == OnboardingStep.DONE)
        )

        async def users_with(*conditions) -> int:
            return await session.scalar(
                select(func.count(func.distinct(ActivityLog.user_id))).where(
                    ActivityLog.user_id.in_(ids), *conditions
                )
            )

        first_points = await users_with(ActivityLog.points > 0)
        daily_task = await users_with(ActivityLog.action == "daily_task")
        open_days: dict[int, set[date]] = {}
        rows = await session.execute(
            select(AnalyticsEvent.user_id, local_day(AnalyticsEvent.created_at))
            .where(opens, AnalyticsEvent.user_id.in_(ids))
            .distinct()
        )
        for user_id, day in rows.all():
            open_days.setdefault(user_id, set()).add(day)
        returned = sum(len(d) >= 2 for d in open_days.values())
        # Only those whose whole second week (days 7–13) has come.
        eligible = [uid for uid, d0 in joined.items() if d0 + timedelta(days=13) <= today]
        kept = sum(
            any(7 <= (day - joined[uid]).days <= 13 for day in open_days.get(uid, ()))
            for uid in eligible
        )
        week_two = _rate(len(eligible), kept)

    return GrowthOut(
        activation=ActivationOut(
            registered=len(ids),
            onboarded=onboarded,
            first_points=first_points,
            daily_task=daily_task,
            returned=returned,
            second_week=week_two,
        ),
        cohorts=await _cohorts(session, today),
        messages=await _bot_messages(session, since),
        stories=await session.scalar(
            select(func.count()).where(
                AnalyticsEvent.name == "story_share", AnalyticsEvent.created_at >= since
            )
        ),
    )


async def _cohorts(session: AsyncSession, today: date) -> list[CohortOut]:
    """Weekly cohorts: users by the week they joined, then the weeks they came back in."""
    this_week = week_start(today)
    first = this_week - timedelta(weeks=COHORT_WEEKS - 1)
    joined = {
        user_id: week_start(day)
        for user_id, day in (
            await session.execute(
                select(User.id, local_day(User.created_at)).where(
                    User.created_at >= day_start(first)
                )
            )
        ).all()
    }
    seen: set[tuple[int, date]] = set()
    if joined:
        rows = await session.execute(
            select(AnalyticsEvent.user_id, local_day(AnalyticsEvent.created_at))
            .where(
                AnalyticsEvent.name == "app_open",
                AnalyticsEvent.user_id.in_(list(joined)),
                AnalyticsEvent.created_at >= day_start(first),
            )
            .distinct()
        )
        seen = {(user_id, week_start(day)) for user_id, day in rows.all()}
    cohorts = []
    for i in range(COHORT_WEEKS):
        monday = first + timedelta(weeks=i)
        members = [uid for uid, week in joined.items() if week == monday]
        weeks: list[float | None] = []
        for offset in range(1, COHORT_WEEKS):
            later = monday + timedelta(weeks=offset)
            if later >= this_week:  # still to come, or not over yet
                weeks.append(None)
                continue
            back = sum((uid, later) in seen for uid in members)
            weeks.append(round(back / len(members), 4) if members else None)
        cohorts.append(CohortOut(week_start=monday, size=len(members), weeks=weeks))
    return cohorts


async def _bot_messages(session: AsyncSession, since: datetime) -> list[BotMessageOut]:
    sent_names = [sent for _, sent, _ in BOT_MESSAGES]
    sent_counts = dict(
        (
            await session.execute(
                select(AnalyticsEvent.name, func.count())
                .where(AnalyticsEvent.name.in_(sent_names), AnalyticsEvent.created_at >= since)
                .group_by(AnalyticsEvent.name)
            )
        ).all()
    )
    # An open counts once per message, however often its button was pressed: per user and
    # day for reminders, per user and week for the Monday summary, per user and broadcast.
    local = func.timezone(TASHKENT_SQL, AnalyticsEvent.created_at)
    message_of = {
        "reminder_open": cast(local, Date),
        "weekly_open": func.date_trunc("week", local),
        "broadcast_open": AnalyticsEvent.props["broadcast"].astext,
    }
    result = []
    for kind, sent_name, open_name in BOT_MESSAGES:
        opens = (
            select(AnalyticsEvent.user_id, message_of[open_name])
            .where(AnalyticsEvent.name == open_name, AnalyticsEvent.created_at >= since)
            .distinct()
            .subquery()
        )
        sent = sent_counts.get(sent_name, 0)
        opened = await session.scalar(select(func.count()).select_from(opens))
        result.append(
            BotMessageOut(
                kind=kind, sent=sent, opened=opened, rate=round(opened / sent, 4) if sent else None
            )
        )
    return result
