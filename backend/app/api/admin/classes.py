"""Teachers' classes for administrators: a look at every class and removing one."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.admin.audit import audit
from app.admin.deps import AdminOnly
from app.admin.schemas import AdminClassOut
from app.deps import SessionDep
from app.models import ClassMember, ClassTask, SchoolClass, User

router = APIRouter(prefix="/classes", tags=["admin-classes"])


@router.get("")
async def list_classes(
    admin: AdminOnly, session: SessionDep, q: Annotated[str, Query(max_length=64)] = ""
) -> list[AdminClassOut]:
    members = (
        select(ClassMember.class_id, func.count().label("n"))
        .group_by(ClassMember.class_id)
        .subquery()
    )
    tasks = (
        select(ClassTask.class_id, func.count().label("n")).group_by(ClassTask.class_id).subquery()
    )
    query = (
        select(
            SchoolClass, User.nickname, func.coalesce(members.c.n, 0), func.coalesce(tasks.c.n, 0)
        )
        .join(User, User.id == SchoolClass.teacher_id)
        .outerjoin(members, members.c.class_id == SchoolClass.id)
        .outerjoin(tasks, tasks.c.class_id == SchoolClass.id)
        .order_by(SchoolClass.id.desc())
        .limit(500)
    )
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.where(
            or_(
                SchoolClass.name.ilike(like),
                User.nickname.ilike(like),
                SchoolClass.code == q.strip().upper(),
            )
        )
    rows = await session.execute(query)
    return [
        AdminClassOut(
            id=c.id,
            name=c.name,
            code=c.code,
            teacher_id=c.teacher_id,
            teacher_nickname=nickname,
            member_count=member_count,
            task_count=task_count,
            created_at=c.created_at,
        )
        for c, nickname, member_count, task_count in rows.all()
    ]


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(class_id: int, admin: AdminOnly, session: SessionDep) -> None:
    """E.g. an offensive class name: the class goes, its pupils stay in the app."""
    school_class = await session.get(SchoolClass, class_id)
    if school_class is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "class_not_found")
    audit(
        session,
        admin,
        "class_delete",
        "class",
        class_id,
        name=school_class.name,
        teacher_id=school_class.teacher_id,
    )
    await session.delete(school_class)
    await session.commit()
