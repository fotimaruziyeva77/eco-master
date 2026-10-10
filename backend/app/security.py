"""Telegram initData validation and session tokens (TZ 11.1)."""

import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import jwt
from aiogram.utils.web_app import WebAppInitData, safe_parse_webapp_init_data

# Telegram clocks and ours may drift slightly; anything further in the future is forged.
MAX_CLOCK_SKEW = timedelta(minutes=5)


class InitDataError(Exception):
    pass


def validate_init_data(
    init_data: str, bot_token: str, max_age: timedelta, now: datetime | None = None
) -> WebAppInitData:
    """Check the HMAC signature and freshness of Mini App initData.

    The user id must only ever come from data that passed this check.
    """
    try:
        data = safe_parse_webapp_init_data(bot_token, init_data)
    except ValueError as exc:
        raise InitDataError("bad signature") from exc

    now = now or datetime.now(UTC)
    auth_date = data.auth_date
    if auth_date.tzinfo is None:
        auth_date = auth_date.replace(tzinfo=UTC)
    if now - auth_date > max_age:
        raise InitDataError("expired")
    if auth_date - now > MAX_CLOCK_SKEW:
        raise InitDataError("auth_date in the future")
    if data.user is None:
        raise InitDataError("no user")
    return data


def sign_init_data(bot_token: str, fields: dict[str, str]) -> str:
    """Build initData the way Telegram does. Used by the dev login endpoint and tests."""
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    hash_ = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": hash_})


def create_session_token(user_id: int, secret: str, ttl: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "iat": now, "exp": now + ttl, "typ": "session"}
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_session_token(token: str, secret: str) -> int:
    """Return the user id or raise jwt.InvalidTokenError."""
    payload = jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["exp", "sub"]})
    if payload.get("typ") != "session":
        raise jwt.InvalidTokenError("wrong token type")
    return int(payload["sub"])
