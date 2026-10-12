from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

# All "per day" rules (daily task, streak, limits, weekly board) use Tashkent time (TZ 4).
TASHKENT = ZoneInfo("Asia/Tashkent")


def utc_now() -> datetime:
    """The current time. Tests replace it to check what happens around Tashkent midnight."""
    return datetime.now(UTC)


def local_today(now: datetime | None = None) -> date:
    return (now or utc_now()).astimezone(TASHKENT).date()


def week_start(day: date) -> date:
    """Monday of the week (weeks run Monday 00:00 – Sunday 23:59, Tashkent time)."""
    return day - timedelta(days=day.weekday())
