from fastapi import APIRouter
from sqlalchemy import and_, select

from app.deps import CurrentUser, SessionDep
from app.models import Badge, UserBadge
from app.schemas import BadgeOut, MeUpdate, UserOut, WriteAccessIn

router = APIRouter(tags=["me"])


@router.get("/me")
async def get_me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me")
async def update_me(body: MeUpdate, user: CurrentUser, session: SessionDep) -> UserOut:
    if body.language is not None:
        user.language = body.language
    await session.commit()
    return UserOut.model_validate(user)


@router.post("/me/write-access")
async def set_write_access(body: WriteAccessIn, user: CurrentUser, session: SessionDep) -> UserOut:
    """Result of Telegram's requestWriteAccess: whether the bot may send reminders (TZ 8.1)."""
    if body.granted and not user.write_access:
        user.write_access = True
        await session.commit()
    return UserOut.model_validate(user)


@router.get("/me/badges")
async def my_badges(user: CurrentUser, session: SessionDep) -> list[BadgeOut]:
    """All badges; earned ones carry earned_at, the rest are shown greyed out with the rule."""
    rows = await session.execute(
        select(Badge, UserBadge.earned_at)
        .outerjoin(UserBadge, and_(UserBadge.badge_id == Badge.id, UserBadge.user_id == user.id))
        .order_by(Badge.sort_order)
    )
    return [
        BadgeOut(
            code=b.code, name=b.name, description=b.description, icon=b.icon, earned_at=earned_at
        )
        for b, earned_at in rows.all()
    ]
