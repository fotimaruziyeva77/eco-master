"""Admin sign-in (TZ 8.12, 11.1): a password plus a mandatory authenticator-app code.

Passwords are hashed with Argon2id. Codes are standard TOTP (RFC 6238: SHA-1, 6 digits,
30-second steps), so any authenticator app works (Google Authenticator, Authy, 2FAS...).
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# OWASP minimum for Argon2id: 19 MiB of memory, 2 iterations, 1 lane.
_hasher = PasswordHasher(time_cost=2, memory_cost=19 * 1024, parallelism=1)
# Checked against when the login is unknown, so the response time does not reveal it.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128
MAX_FAILED_LOGINS = 5
LOCKOUT = timedelta(minutes=15)
SESSION_TTL = timedelta(hours=12)
CODE_STEP_TTL = timedelta(minutes=5)

SESSION_COOKIE = "ekoustoz_admin"
SESSION_TOKEN = "admin_session"
CODE_TOKEN = "admin_code"

TOTP_PERIOD = 30
TOTP_DIGITS = 6
ISSUER = "Ekoustoz"


# ------------------------------------------------------------------ passwords


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and bool(password_hash)
    except (VerificationError, InvalidHashError):
        return False


def password_problem(password: str) -> str | None:
    """Error code for a password that is too weak, or None."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return "password_too_short"
    if len(password) > MAX_PASSWORD_LENGTH:
        return "password_too_long"
    if len(set(password)) < 5:
        return "password_too_simple"
    return None


# ----------------------------------------------------------------------- TOTP


def new_totp_secret() -> str:
    """160 random bits in base32, as authenticator apps expect."""
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def hotp(secret: str, counter: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(value % 10**TOTP_DIGITS).zfill(TOTP_DIGITS)


def totp_now(secret: str, at: float | None = None) -> str:
    return hotp(secret, int((time.time() if at is None else at) // TOTP_PERIOD))


def verify_totp(
    secret: str, code: str, last_step: int | None, at: float | None = None
) -> int | None:
    """The matching time step, or None. One step of clock drift either way is accepted;
    a step at or before `last_step` is refused, so an observed code can not be replayed."""
    code = code.replace(" ", "")
    if len(code) != TOTP_DIGITS or not code.isdigit():
        return None
    now = int((time.time() if at is None else at) // TOTP_PERIOD)
    for step in (now - 1, now, now + 1):
        if last_step is not None and step <= last_step:
            continue
        if hmac.compare_digest(hotp(secret, step), code):
            return step
    return None


def provisioning_uri(secret: str, login: str) -> str:
    """otpauth:// link shown as a QR code when the authenticator app is set up."""
    label = quote(f"{ISSUER}:{login}", safe=":@")
    return (
        f"otpauth://totp/{label}?secret={secret}&issuer={ISSUER}"
        f"&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_PERIOD}"
    )


# --------------------------------------------------------------------- tokens


def create_token(secret: str, admin_id: int, kind: str, version: int, ttl: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {"typ": kind, "sub": str(admin_id), "ver": version, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, secret, algorithm="HS256")


def read_token(secret: str, token: str, kind: str) -> tuple[int, int]:
    """(admin id, session version); raises jwt.InvalidTokenError."""
    payload = jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["exp", "sub"]})
    if payload.get("typ") != kind:
        raise jwt.InvalidTokenError("wrong token type")
    return int(payload["sub"]), int(payload.get("ver", -1))
