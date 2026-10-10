"""Signed quiz/game rounds.

The server picks the questions or items and signs the list, so an answer is only accepted
for something the server actually showed — and the correct answer never leaves the server.
"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt

ROUND_TTL = timedelta(hours=1)


class RoundError(Exception):
    pass


def create_round_token(secret: str, user_id: int, kind: str, ids: list[int]) -> str:
    now = datetime.now(UTC)
    payload = {
        "typ": f"{kind}_round",
        "sub": str(user_id),
        "rid": uuid.uuid4().hex,
        "ids": ids,
        "iat": now,
        "exp": now + ROUND_TTL,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def read_round_token(secret: str, token: str, user_id: int, kind: str) -> tuple[str, list[int]]:
    """Return (round id, object ids) or raise RoundError."""
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        raise RoundError("invalid round") from exc
    if payload.get("typ") != f"{kind}_round" or payload.get("sub") != str(user_id):
        raise RoundError("round belongs to another user or game")
    return payload["rid"], [int(i) for i in payload["ids"]]


def answer_event_id(round_id: str, object_id: int) -> uuid.UUID:
    """One answer per item per round: the same pair always maps to the same idempotency key."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"ekoustoz:{round_id}:{object_id}")
