from fastapi import APIRouter

from app.deps import CurrentUser, SessionDep
from app.schemas import MeUpdate, UserOut, WriteAccessIn

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
