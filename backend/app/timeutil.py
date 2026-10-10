from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

# All "per day" rules (daily task, streak, limits, weekly board) use Tashkent time (TZ 4).
TASHKENT = ZoneInfo("Asia/Tashkent")


def utc_now() -> datetime:
    """The current time. Tests replace it to check what happens around Tashkent midnight."""
    return datetime.now(UTC)


def local_today(now: datetime | None = None) -> date:
    return (now or utc_now()).astimezone(TASHKENT).date()
