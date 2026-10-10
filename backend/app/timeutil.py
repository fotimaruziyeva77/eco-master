from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

# All "per day" rules (daily task, streak, limits, weekly board) use Tashkent time (TZ 4).
TASHKENT = ZoneInfo("Asia/Tashkent")


def local_today(now: datetime | None = None) -> date:
    return (now or datetime.now(UTC)).astimezone(TASHKENT).date()
