"""Events the Mini App reports itself (TZ 14): video plays and client-side errors."""

from fastapi import APIRouter, HTTPException, Response, status

from app.analytics import track
from app.deps import CurrentUser, SessionDep
from app.ratelimit import RateLimiter
from app.schemas import EventsIn

router = APIRouter(tags=["events"])

# A normal session sends a few events a minute; this only stops runaway loops and abuse.
event_limit = RateLimiter(limit=120, window=60)


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT)
async def record_events(body: EventsIn, user: CurrentUser, session: SessionDep) -> Response:
    if not event_limit.allow(user.id, cost=len(body.events)):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_events")
    for event in body.events:
        track(session, user, event.name, **event.props)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
