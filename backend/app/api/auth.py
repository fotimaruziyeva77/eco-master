from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.analytics import track
from app.badges import award_badges
from app.deps import SessionDep, SettingsDep
from app.i18n import pick_language
from app.models import User
from app.schemas import AuthOut, TelegramAuthIn, UserOut
from app.security import InitDataError, create_session_token, validate_init_data

router = APIRouter(tags=["auth"])


@router.post("/auth/telegram")
async def auth_telegram(
    body: TelegramAuthIn, session: SessionDep, settings: SettingsDep
) -> AuthOut:
    """Exchange signed Mini App initData for a session token (TZ 11.1)."""
    try:
        data = validate_init_data(
            body.init_data,
            settings.effective_bot_token,
            max_age=timedelta(hours=settings.init_data_max_age_hours),
        )
    except InitDataError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_init_data") from exc

    tg_user = data.user
    source = data.start_param[:64] if data.start_param else None
    # Telegram's name, username and photo are deliberately not stored (TZ 8.1, 10).
    created = await session.scalar(
        insert(User)
        .values(
            telegram_id=tg_user.id,
            language=pick_language(tg_user.language_code),
            source=source,
        )
        .on_conflict_do_nothing(index_elements=[User.telegram_id])
        .returning(User.id)
    )
    user = await session.scalar(select(User).where(User.telegram_id == tg_user.id))
    if user.is_blocked:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "user_blocked")
    user.last_active_at = datetime.now(UTC)
    # Every launch of the Mini App signs in again, so this is the app_open event (TZ 14).
    track(session, user, "app_open", source=source, new=created is not None)
    if source == "reminder":
        track(session, user, "reminder_open")
    elif source == "weekly":
        track(session, user, "weekly_open")
    # Catch up on badges whose rules were met before they existed (or changed since).
    await award_badges(session, user.id)
    await session.commit()

    token = create_session_token(
        user.id, settings.jwt_secret, timedelta(hours=settings.jwt_ttl_hours)
    )
    return AuthOut(token=token, user=UserOut.model_validate(user))
