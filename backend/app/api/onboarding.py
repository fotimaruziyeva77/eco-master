"""First-run flow (TZ 8.1): language → path → nickname → intro screens → done.

Each step is saved, so a user who closes the app halfway continues where they stopped.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.deps import CurrentUser, SessionDep
from app.models import OnboardingStep, User
from app.nickname import NicknameError, validate_nickname
from app.schemas import (
    NicknameCheckOut,
    NicknameIn,
    OnboardingLanguageIn,
    OnboardingPathIn,
    UserOut,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

STEP_ORDER = list(OnboardingStep)


def advance(user: User, step: OnboardingStep) -> None:
    """Move forward only; going back to an earlier screen never resets progress."""
    if STEP_ORDER.index(step) > STEP_ORDER.index(user.onboarding_step):
        user.onboarding_step = step


@router.post("/language")
async def set_language(
    body: OnboardingLanguageIn, user: CurrentUser, session: SessionDep
) -> UserOut:
    user.language = body.language
    advance(user, OnboardingStep.PATH)
    await session.commit()
    return UserOut.model_validate(user)


@router.post("/path")
async def set_path(body: OnboardingPathIn, user: CurrentUser, session: SessionDep) -> UserOut:
    user.path = body.path
    advance(user, OnboardingStep.NICKNAME)
    await session.commit()
    return UserOut.model_validate(user)


@router.get("/nickname-check")
async def check_nickname(
    user: CurrentUser, session: SessionDep, value: str = Query(max_length=64)
) -> NicknameCheckOut:
    try:
        await validate_nickname(session, value, exclude_user_id=user.id)
    except NicknameError as exc:
        return NicknameCheckOut(ok=False, error=exc.code)
    return NicknameCheckOut(ok=True)


@router.post("/nickname")
async def set_nickname(body: NicknameIn, user: CurrentUser, session: SessionDep) -> UserOut:
    if user.onboarding_step is OnboardingStep.DONE:
        # After onboarding the nickname is changed in settings, with its own limits.
        raise HTTPException(status.HTTP_409_CONFLICT, "onboarding_finished")
    try:
        nickname = await validate_nickname(session, body.nickname, exclude_user_id=user.id)
    except NicknameError as exc:
        code = status.HTTP_409_CONFLICT if exc.code == "nickname_taken" else 422
        raise HTTPException(code, exc.code) from exc

    user.nickname = nickname
    advance(user, OnboardingStep.INTRO)
    try:
        await session.commit()
    except IntegrityError as exc:  # someone took the same nickname a moment ago
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "nickname_taken") from exc
    return UserOut.model_validate(user)


@router.post("/complete")
async def complete(user: CurrentUser, session: SessionDep) -> UserOut:
    if user.path is None or user.nickname is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "onboarding_incomplete")
    if user.onboarding_step is not OnboardingStep.DONE:
        user.onboarding_step = OnboardingStep.DONE
        user.onboarded_at = datetime.now(UTC)
        await session.commit()
    return UserOut.model_validate(user)
