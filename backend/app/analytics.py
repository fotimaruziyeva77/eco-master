"""Product analytics (TZ 14) in our own database, with no third-party trackers (TZ 11.2).

Every event carries the internal user id (never the Telegram id), the time (UTC) and the
user's language and path at that moment. Events are queued on the session and written
with the caller's commit, so they never outlive a rolled-back action.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnalyticsEvent, User, UserPath

# Sent by the Mini App itself (POST /api/events), with the only fields each may carry.
# Everything else is recorded by the server where the action happens.
CLIENT_EVENT_PROPS: dict[str, frozenset[str]] = {
    "video_play": frozenset({"project"}),
    "video_complete": frozenset({"project"}),
    "error": frozenset({"type", "screen"}),
}


def event_row(
    user_id: int | None, language: str | None, path: UserPath | None, name: str, props: dict
) -> AnalyticsEvent:
    return AnalyticsEvent(
        user_id=user_id,
        name=name,
        props=props or None,
        language=language,
        path=path.value if path else None,
    )


def track(session: AsyncSession, user: User, name: str, **props: Any) -> None:
    session.add(event_row(user.id, user.language, user.path, name, props))
