from fastapi import APIRouter

from app.deps import CurrentUser, SessionDep
from app.schemas import MeUpdate, UserOut

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
