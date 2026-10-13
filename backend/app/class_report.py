"""The Monday report for teachers, sent with the Monday summary (app/reminders.py).

For each class that existed last week and has pupils: how many of them earned points, the three
with the most, and the class tasks due last week or later with how many pupils did them. Only
what the teacher already sees in the app: nicknames, points and tasks. Blocked users are left
out, as everywhere they would be shown.
"""

import html
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import DEFAULT_LANGUAGE, t
from app.models import ActivityLog, ClassMember, ClassTask, Project, SchoolClass, User
from app.timeutil import TASHKENT

TOP = 3
# A class has at most five open tasks (app/api/classes.py); older ones are left out.
MAX_TASKS = 5


@dataclass(frozen=True)
class TaskLine:
    title: str
    done: int
    total: int
    overdue: bool


@dataclass(frozen=True)
class ClassWeek:
    name: str
    members: int
    # Pupils who earned points last week.
    active: int
    # (nickname or None when hidden, points), the most points first.
    top: list[tuple[str | None, int]]
    tasks: list[TaskLine]


async def class_weeks(
    session: AsyncSession, teacher_id: int, language: str, last_monday: date, today: date
) -> list[ClassWeek]:
    """Last week of each of the teacher's classes; empty if there is nothing to report."""
    this_week = datetime.combine(today, time.min, TASHKENT)
    classes = (
        await session.scalars(
            select(SchoolClass)
            .where(SchoolClass.teacher_id == teacher_id, SchoolClass.created_at < this_week)
            .order_by(SchoolClass.id)
        )
    ).all()
    weeks = []
    for school_class in classes:
        week = await _class_week(session, school_class, language, last_monday, today)
        if week is not None:
            weeks.append(week)
    return weeks


async def _class_week(
    session: AsyncSession, school_class: SchoolClass, language: str, last_monday: date, today: date
) -> ClassWeek | None:
    members = (
        await session.execute(
            select(User.id, User.nickname, User.nickname_hidden)
            .join(ClassMember, ClassMember.user_id == User.id)
            .where(ClassMember.class_id == school_class.id, User.is_blocked.is_(False))
            .order_by(User.id)
        )
    ).all()
    if not members:
        return None
    ids = [m.id for m in members]
    points = {
        user_id: int(total or 0)
        for user_id, total in (
            await session.execute(
                select(ActivityLog.user_id, func.sum(ActivityLog.points))
                .where(
                    ActivityLog.user_id.in_(ids),
                    ActivityLog.local_date.between(last_monday, last_monday + timedelta(days=6)),
                )
                .group_by(ActivityLog.user_id)
            )
        ).all()
    }
    active = sorted(
        (m for m in members if points.get(m.id, 0) > 0), key=lambda m: (-points[m.id], m.id)
    )
    top = [(None if m.nickname_hidden else m.nickname, points[m.id]) for m in active[:TOP]]

    tasks = (
        await session.execute(
            select(ClassTask.due_date, Project.id, Project.title)
            .join(Project, Project.id == ClassTask.project_id)
            .where(ClassTask.class_id == school_class.id, ClassTask.due_date >= last_monday)
            .order_by(ClassTask.due_date, ClassTask.id)
            .limit(MAX_TASKS)
        )
    ).all()
    done: dict[str, int] = {}
    if tasks:
        done = dict(
            (
                await session.execute(
                    select(ActivityLog.object_id, func.count(func.distinct(ActivityLog.user_id)))
                    .where(
                        ActivityLog.user_id.in_(ids),
                        ActivityLog.action == "project_done",
                        ActivityLog.object_id.in_([str(project_id) for _, project_id, _ in tasks]),
                    )
                    .group_by(ActivityLog.object_id)
                )
            ).all()
        )
    lines = []
    for due, project_id, title in tasks:
        did = done.get(str(project_id), 0)
        lines.append(
            TaskLine(
                title=title.get(language) or title.get(DEFAULT_LANGUAGE, ""),
                done=did,
                total=len(ids),
                overdue=due < today and did < len(ids),
            )
        )
    return ClassWeek(school_class.name, len(ids), len(active), top, lines)


def _name(language: str, nickname: str | None) -> str:
    return f"@{html.escape(nickname)}" if nickname else t("anonymous", language)


def report_text(language: str, weeks: list[ClassWeek]) -> str:
    lines = [t("class_report_title", language)]
    for week in weeks:
        lines += [
            "",
            t(
                "class_report_class",
                language,
                name=html.escape(week.name),
                active=week.active,
                members=week.members,
            ),
        ]
        if week.top:
            names = ", ".join(f"{_name(language, nick)} ({pts})" for nick, pts in week.top)
            lines.append(t("class_report_top", language, names=names))
        else:
            lines.append(t("class_report_quiet", language))
        for task in week.tasks:
            if task.done >= task.total:
                key = "class_report_task_done"
            elif task.overdue:
                key = "class_report_task_late"
            else:
                key = "class_report_task_open"
            lines.append(
                t(key, language, title=html.escape(task.title), done=task.done, total=task.total)
            )
    return "\n".join(lines)
