"""Teachers' classes.

A teacher (a user on the teacher path) makes a class and shows its QR code. A pupil who scans
it sees the class name and the teacher's nickname and joins with one tap: nobody is put into a
class by someone else, and a pupil can leave at any time. The teacher sees the pupils'
nicknames, levels and points and can give the class a project to do by a date; the pupils see
their class board and the tasks. Nothing else about a pupil is shown, and nobody can write to
anybody.
"""

import secrets
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import track
from app.config import Settings
from app.deps import CurrentUser, SessionDep, SettingsDep
from app.levels import level_for
from app.market import MarketError, check_text
from app.models import (
    ActivityLog,
    Category,
    ClassMember,
    ClassTask,
    ContentStatus,
    Project,
    SchoolClass,
    User,
    UserPath,
)
from app.ratelimit import RateLimiter
from app.schemas import (
    ClassDetailOut,
    ClassIn,
    ClassJoinIn,
    ClassMemberOut,
    ClassOut,
    ClassPreviewOut,
    ClassTaskIn,
    ClassTaskOut,
    MyClassOut,
    RankedMemberOut,
)
from app.timeutil import local_today, week_start

router = APIRouter(tags=["classes"])

# No 0/O or 1/I: the code is read off a board.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6
MAX_CLASSES = 10
MAX_MEMBERS = 60
MAX_OPEN_TASKS = 5
# Looking up codes is limited, so nobody can try codes until a class turns up.
code_limit = RateLimiter(limit=30, window=3600)


def require_teacher(user: User) -> None:
    if user.path != UserPath.TEACHER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "teachers_only")


def class_link(settings: Settings, code: str) -> str:
    return f"{settings.app_link}?startapp=class_{code}"


async def checked_name(session: AsyncSession, name: str) -> str:
    try:
        await check_text(session, name)
    except MarketError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, exc.code) from exc
    return name


async def own_class(session: AsyncSession, user: User, class_id: int) -> SchoolClass:
    school_class = await session.get(SchoolClass, class_id)
    if school_class is None or school_class.teacher_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "class_not_found")
    return school_class


async def new_code(session: AsyncSession) -> str:
    while True:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
        if await session.scalar(select(SchoolClass.id).where(SchoolClass.code == code)) is None:
            return code


async def member_counts(session: AsyncSession, class_ids: list[int]) -> dict[int, int]:
    if not class_ids:
        return {}
    rows = await session.execute(
        select(ClassMember.class_id, func.count())
        .join(User, User.id == ClassMember.user_id)
        .where(ClassMember.class_id.in_(class_ids), User.is_blocked.is_(False))
        .group_by(ClassMember.class_id)
    )
    return dict(rows.all())


async def member_ids(session: AsyncSession, class_id: int) -> list[int]:
    """Pupils of the class; blocked users are left out everywhere they would be shown (QM-13)."""
    rows = await session.scalars(
        select(ClassMember.user_id)
        .join(User, User.id == ClassMember.user_id)
        .where(ClassMember.class_id == class_id, User.is_blocked.is_(False))
    )
    return list(rows.all())


async def week_points(session: AsyncSession, user_ids: list[int]) -> dict[int, int]:
    if not user_ids:
        return {}
    monday = week_start(local_today())
    rows = await session.execute(
        select(ActivityLog.user_id, func.sum(ActivityLog.points))
        .where(
            ActivityLog.user_id.in_(user_ids),
            ActivityLog.local_date.between(monday, monday + timedelta(days=6)),
        )
        .group_by(ActivityLog.user_id)
    )
    return {user_id: int(points or 0) for user_id, points in rows.all()}


async def projects_done(session: AsyncSession, user_ids: list[int]) -> dict[int, set[str]]:
    """Ids (as text) of the projects each user did."""
    if not user_ids:
        return {}
    rows = await session.execute(
        select(ActivityLog.user_id, ActivityLog.object_id).where(
            ActivityLog.user_id.in_(user_ids), ActivityLog.action == "project_done"
        )
    )
    done: dict[int, set[str]] = {}
    for user_id, object_id in rows.all():
        done.setdefault(user_id, set()).add(object_id)
    return done


async def tasks_out(
    session: AsyncSession, class_id: int, members: list[int], done: dict[int, set[str]]
) -> list[ClassTaskOut]:
    rows = await session.execute(
        select(ClassTask, Project, Category)
        .join(Project, Project.id == ClassTask.project_id)
        .join(Category, Category.id == Project.category_id)
        .where(ClassTask.class_id == class_id)
        .order_by(ClassTask.due_date, ClassTask.id)
    )
    out = []
    for task, project, category in rows.all():
        done_by = [m for m in members if str(project.id) in done.get(m, set())]
        out.append(
            ClassTaskOut(
                id=task.id,
                project_slug=project.slug,
                title=project.title,
                icon=category.icon,
                due_date=task.due_date,
                done_count=len(done_by),
                member_count=len(members),
                done_by=done_by,
            )
        )
    return out


def class_out(settings: Settings, school_class: SchoolClass, count: int) -> ClassOut:
    return ClassOut(
        id=school_class.id,
        name=school_class.name,
        code=school_class.code,
        member_count=count,
        link=class_link(settings, school_class.code),
    )


# ------------------------------------------------------------------- teacher


@router.get("/classes")
async def my_classes(
    user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> list[ClassOut]:
    require_teacher(user)
    rows = await session.scalars(
        select(SchoolClass).where(SchoolClass.teacher_id == user.id).order_by(SchoolClass.id)
    )
    classes = list(rows.all())
    counts = await member_counts(session, [c.id for c in classes])
    return [class_out(settings, c, counts.get(c.id, 0)) for c in classes]


@router.post("/classes", status_code=status.HTTP_201_CREATED)
async def create_class(
    body: ClassIn, user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> ClassOut:
    require_teacher(user)
    count = await session.scalar(
        select(func.count()).select_from(SchoolClass).where(SchoolClass.teacher_id == user.id)
    )
    if count >= MAX_CLASSES:
        raise HTTPException(status.HTTP_409_CONFLICT, "too_many_classes")
    school_class = SchoolClass(
        teacher_id=user.id,
        name=await checked_name(session, body.name),
        code=await new_code(session),
    )
    session.add(school_class)
    track(session, user, "class_created")
    await session.commit()
    return class_out(settings, school_class, 0)


@router.get("/classes/{class_id}")
async def class_detail(
    class_id: int, user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> ClassDetailOut:
    require_teacher(user)
    school_class = await own_class(session, user, class_id)
    ids = await member_ids(session, class_id)
    users = (await session.scalars(select(User).where(User.id.in_(ids)))).all() if ids else []
    points = await week_points(session, ids)
    done = await projects_done(session, ids)
    members = sorted(
        (
            ClassMemberOut(
                user_id=u.id,
                nickname=None if u.nickname_hidden else u.nickname,
                avatar=u.avatar,
                level_code=level_for(u.points_total).code,
                points_week=points.get(u.id, 0),
                points_total=u.points_total,
                projects_done=len(done.get(u.id, set())),
            )
            for u in users
        ),
        key=lambda m: (-m.points_week, -m.points_total, m.user_id),
    )
    return ClassDetailOut(
        **class_out(settings, school_class, len(ids)).model_dump(),
        members=members,
        tasks=await tasks_out(session, class_id, ids, done),
    )


@router.patch("/classes/{class_id}")
async def rename_class(
    class_id: int, body: ClassIn, user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> ClassOut:
    require_teacher(user)
    school_class = await own_class(session, user, class_id)
    school_class.name = await checked_name(session, body.name)
    await session.commit()
    counts = await member_counts(session, [class_id])
    return class_out(settings, school_class, counts.get(class_id, 0))


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(class_id: int, user: CurrentUser, session: SessionDep) -> None:
    require_teacher(user)
    await session.delete(await own_class(session, user, class_id))
    await session.commit()


@router.delete("/classes/{class_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    class_id: int, user_id: int, user: CurrentUser, session: SessionDep
) -> None:
    require_teacher(user)
    await own_class(session, user, class_id)
    await session.execute(
        delete(ClassMember).where(ClassMember.class_id == class_id, ClassMember.user_id == user_id)
    )
    await session.commit()


@router.post("/classes/{class_id}/tasks", status_code=status.HTTP_201_CREATED)
async def add_task(
    class_id: int, body: ClassTaskIn, user: CurrentUser, session: SessionDep
) -> ClassTaskOut:
    require_teacher(user)
    await own_class(session, user, class_id)
    today = local_today()
    if not today <= body.due_date <= today + timedelta(days=60):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "bad_due_date")
    project = await session.scalar(
        select(Project).where(
            Project.slug == body.project_slug, Project.status == ContentStatus.PUBLISHED
        )
    )
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project_not_found")
    open_tasks = await session.scalar(
        select(func.count())
        .select_from(ClassTask)
        .where(ClassTask.class_id == class_id, ClassTask.due_date >= today)
    )
    if open_tasks >= MAX_OPEN_TASKS:
        raise HTTPException(status.HTTP_409_CONFLICT, "too_many_tasks")
    if await session.scalar(
        select(ClassTask.id).where(
            ClassTask.class_id == class_id, ClassTask.project_id == project.id
        )
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "task_exists")
    session.add(ClassTask(class_id=class_id, project_id=project.id, due_date=body.due_date))
    track(session, user, "class_task_created", project=project.slug)
    await session.commit()
    ids = await member_ids(session, class_id)
    tasks = await tasks_out(session, class_id, ids, await projects_done(session, ids))
    return next(t for t in tasks if t.project_slug == project.slug)


@router.delete("/classes/{class_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(class_id: int, task_id: int, user: CurrentUser, session: SessionDep) -> None:
    require_teacher(user)
    await own_class(session, user, class_id)
    await session.execute(
        delete(ClassTask).where(ClassTask.id == task_id, ClassTask.class_id == class_id)
    )
    await session.commit()


# --------------------------------------------------------------------- pupil


async def class_by_code(session: AsyncSession, user: User, code: str) -> SchoolClass:
    if not code_limit.allow(user.id):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_attempts")
    # A blocked teacher's classes can not be joined.
    school_class = await session.scalar(
        select(SchoolClass)
        .join(User, User.id == SchoolClass.teacher_id)
        .where(SchoolClass.code == code.strip().upper(), User.is_blocked.is_(False))
    )
    if school_class is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "class_not_found")
    return school_class


async def teacher_nickname(session: AsyncSession, school_class: SchoolClass) -> str | None:
    teacher = await session.get(User, school_class.teacher_id)
    if teacher is None or teacher.nickname_hidden or teacher.is_blocked:
        return None
    return teacher.nickname


@router.get("/classes/preview/{code}")
async def preview_class(code: str, user: CurrentUser, session: SessionDep) -> ClassPreviewOut:
    """What the join screen shows before the pupil decides."""
    school_class = await class_by_code(session, user, code)
    counts = await member_counts(session, [school_class.id])
    is_member = await session.get(ClassMember, (school_class.id, user.id)) is not None
    return ClassPreviewOut(
        name=school_class.name,
        teacher_nickname=await teacher_nickname(session, school_class),
        member_count=counts.get(school_class.id, 0),
        is_member=is_member,
    )


@router.post("/classes/join")
async def join_class(body: ClassJoinIn, user: CurrentUser, session: SessionDep) -> MyClassOut:
    """Join with the code; a pupil is in one class at a time, so another class is left."""
    school_class = await class_by_code(session, user, body.code)
    if school_class.teacher_id == user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "own_class")
    if await session.get(ClassMember, (school_class.id, user.id)) is None:
        count = (await member_counts(session, [school_class.id])).get(school_class.id, 0)
        if count >= MAX_MEMBERS:
            raise HTTPException(status.HTTP_409_CONFLICT, "class_full")
        await session.execute(delete(ClassMember).where(ClassMember.user_id == user.id))
        session.add(ClassMember(class_id=school_class.id, user_id=user.id))
        track(session, user, "class_joined")
        await session.commit()
    return await my_class_out(session, user, school_class)


async def my_class_out(session: AsyncSession, user: User, school_class: SchoolClass) -> MyClassOut:
    ids = await member_ids(session, school_class.id)
    users = (await session.scalars(select(User).where(User.id.in_(ids)))).all() if ids else []
    points = await week_points(session, ids)
    ranked = sorted(users, key=lambda u: (-points.get(u.id, 0), -u.points_total, u.id))
    done = await projects_done(session, [user.id])
    tasks = await tasks_out(session, school_class.id, [user.id], done)
    for task in tasks:
        task.done = bool(task.done_by)
        task.done_by = []
        task.done_count = 0
        task.member_count = 0
    return MyClassOut(
        id=school_class.id,
        name=school_class.name,
        teacher_nickname=await teacher_nickname(session, school_class),
        week_start=week_start(local_today()),
        members=[
            RankedMemberOut(
                rank=i,
                user_id=u.id,
                nickname=None if u.nickname_hidden else u.nickname,
                avatar=u.avatar,
                level_code=level_for(u.points_total).code,
                points=points.get(u.id, 0),
                is_me=u.id == user.id,
            )
            for i, u in enumerate(ranked, start=1)
        ],
        tasks=tasks,
    )


@router.get("/my-class")
async def my_class(user: CurrentUser, session: SessionDep) -> MyClassOut | None:
    member = await session.scalar(select(ClassMember).where(ClassMember.user_id == user.id))
    if member is None:
        return None
    return await my_class_out(session, user, await session.get(SchoolClass, member.class_id))


@router.delete("/my-class", status_code=status.HTTP_204_NO_CONTENT)
async def leave_class(user: CurrentUser, session: SessionDep) -> None:
    await session.execute(delete(ClassMember).where(ClassMember.user_id == user.id))
    track(session, user, "class_left")
    await session.commit()
