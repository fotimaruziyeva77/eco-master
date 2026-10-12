"""Database schema (TZ section 10).

Multilingual fields are JSONB objects keyed by language: {"uz": ..., "ru": ..., "en": ...}.
Points, level and streak are derived from activity_log; the columns on users are a cache.
"""

import enum
import uuid
from datetime import date, datetime, time
from typing import Any

from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    Index,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

I18n = dict[str, Any]


def str_enum(cls: type[enum.Enum], length: int = 16) -> Enum:
    """Store enums as plain strings so adding a value never needs an ALTER TYPE."""
    return Enum(
        cls,
        native_enum=False,
        create_constraint=False,
        length=length,
        values_callable=lambda e: [m.value for m in e],
    )


class UserPath(enum.StrEnum):
    STUDENT = "student"
    TEACHER = "teacher"
    GENERAL = "general"


class OnboardingStep(enum.StrEnum):
    LANGUAGE = "language"
    PATH = "path"
    NICKNAME = "nickname"
    INTRO = "intro"
    DONE = "done"


class ContentStatus(enum.StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Difficulty(enum.StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SafetyLevel(enum.StrEnum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class ReportStatus(enum.StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class AdminRole(enum.StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    # Staff of a market handover point: sees only the handover desk of that point.
    POINT = "point"


class WordKind(enum.StrEnum):
    PROFANITY = "profanity"
    RESERVED = "reserved"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class ContentMixin(TimestampMixin):
    status: Mapped[ContentStatus] = mapped_column(
        str_enum(ContentStatus), server_default=ContentStatus.DRAFT.value, index=True
    )
    sort_order: Mapped[int] = mapped_column(server_default=text("0"))


# --------------------------------------------------------------------------- users


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    nickname: Mapped[str | None] = mapped_column(String(20))
    language: Mapped[str] = mapped_column(String(2), server_default="uz")
    path: Mapped[UserPath | None] = mapped_column(str_enum(UserPath))
    onboarding_step: Mapped[OnboardingStep] = mapped_column(
        str_enum(OnboardingStep), server_default=OnboardingStep.LANGUAGE.value
    )
    onboarded_at: Mapped[datetime | None]
    # Deep-link start parameter of the first visit (school / teacher link), for analytics.
    source: Mapped[str | None] = mapped_column(String(64))
    # Chosen animal picture (app/avatars.py); None shows the one the app picks from the id.
    avatar: Mapped[str | None] = mapped_column(String(16))

    reminders_enabled: Mapped[bool] = mapped_column(server_default=text("true"))
    reminder_time: Mapped[time] = mapped_column(server_default=text("'18:00'"))
    # True once the user has started the bot or granted requestWriteAccess.
    write_access: Mapped[bool] = mapped_column(server_default=text("false"))
    # Tashkent date of the last reminder, so a restart never sends a second one that day.
    last_reminder_date: Mapped[date | None]
    # Tashkent date (a Monday) of the last weekly summary, sent once a week.
    last_weekly_date: Mapped[date | None]

    is_blocked: Mapped[bool] = mapped_column(server_default=text("false"))
    nickname_hidden: Mapped[bool] = mapped_column(server_default=text("false"))
    nickname_changed_at: Mapped[datetime | None]

    # Cache of values derived from activity_log.
    points_total: Mapped[int] = mapped_column(server_default=text("0"))
    streak_current: Mapped[int] = mapped_column(server_default=text("0"))
    streak_best: Mapped[int] = mapped_column(server_default=text("0"))
    last_task_date: Mapped[date | None]
    # Weekly league (app/leagues.py): 0 bronze, 1 silver, 2 gold, 3 diamond.
    league_tier: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_active_at: Mapped[datetime] = mapped_column(server_default=func.now())


# Nicknames are unique regardless of letter case (TZ 8.1).
Index("uq_users_nickname_lower", func.lower(User.nickname), unique=True)


# ----------------------------------------------------------------------- content


class Category(Base):
    """Waste type. One list for the whole app (TZ 8.3)."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[I18n]
    # Typical items, shown under the bin in the sorting game ("bottles, cups…").
    examples: Mapped[I18n | None]
    icon: Mapped[str] = mapped_column(String(16))
    color: Mapped[str] = mapped_column(String(7))
    sort_order: Mapped[int] = mapped_column(server_default=text("0"))
    has_projects: Mapped[bool] = mapped_column(server_default=text("false"))
    is_game_bin: Mapped[bool] = mapped_column(server_default=text("false"))


class Project(ContentMixin, Base):
    """Craft project = video lesson card (TZ 8.3)."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    title: Mapped[I18n]
    difficulty: Mapped[Difficulty] = mapped_column(str_enum(Difficulty))
    safety_level: Mapped[SafetyLevel] = mapped_column(str_enum(SafetyLevel))
    duration_min: Mapped[int]
    materials: Mapped[I18n]  # {"uz": ["...", ...], ...}
    steps: Mapped[I18n]  # {"uz": ["...", ...], ...}
    safety_text: Mapped[I18n | None]
    video_url: Mapped[str | None] = mapped_column(String(512))
    poster_url: Mapped[str | None] = mapped_column(String(512))
    tested_by: Mapped[str | None] = mapped_column(String(128))
    tested_at: Mapped[datetime | None]


class Question(ContentMixin, Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NULL means a general ecology question.
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), index=True)
    text: Mapped[I18n]
    options: Mapped[I18n]  # {"uz": ["a", "b", ...], ...} — same order in every language
    correct_index: Mapped[int] = mapped_column(SmallInteger)
    explanation: Mapped[I18n]
    image_url: Mapped[str | None] = mapped_column(String(512))


class GameItem(ContentMixin, Base):
    __tablename__ = "game_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[I18n]
    image_url: Mapped[str | None] = mapped_column(String(512))
    # Emoji shown until (or instead of) a photo is uploaded.
    icon: Mapped[str | None] = mapped_column(String(16))
    correct_category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    explanation: Mapped[I18n]


class DailyTask(ContentMixin, Base):
    __tablename__ = "daily_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[I18n]
    points: Mapped[int] = mapped_column(server_default=text("20"))


class DailyTaskSchedule(Base):
    __tablename__ = "daily_task_schedule"

    day: Mapped[date] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("daily_tasks.id", ondelete="CASCADE"))


class Tip(ContentMixin, Base):
    __tablename__ = "tips"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[I18n]


class TipSchedule(Base):
    __tablename__ = "tip_schedule"

    day: Mapped[date] = mapped_column(primary_key=True)
    tip_id: Mapped[int] = mapped_column(ForeignKey("tips.id", ondelete="CASCADE"))


class KnowledgeCard(ContentMixin, Base):
    """Problem → cause → effect → solution → what I can do (TZ 8.10)."""

    __tablename__ = "knowledge_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[I18n]
    sections: Mapped[I18n]  # {"uz": {"problem": "...", "cause": "...", ...}, ...}
    image_url: Mapped[str | None] = mapped_column(String(512))


class TeacherLesson(ContentMixin, Base):
    __tablename__ = "teacher_lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[I18n]
    grade: Mapped[str] = mapped_column(String(32))
    body: Mapped[I18n]  # lesson text per language
    pdf: Mapped[I18n | None]  # {"uz": "<file url or telegram file_id>", ...}


class VideoStatus(enum.StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class VideoUpload(Base):
    """A video uploaded in the admin panel, converted in the background (app.content_media).

    Pictures are ready at once and need no row; a video takes a minute or two, and the admin
    page asks for its state here until the files are ready.
    """

    __tablename__ = "video_uploads"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[VideoStatus] = mapped_column(str_enum(VideoStatus))
    original_name: Mapped[str] = mapped_column(String(200))
    # The uploaded file in the media folder's tmp/, kept until the conversion is over.
    source_name: Mapped[str | None] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(String(128))
    poster_url: Mapped[str | None] = mapped_column(String(128))
    width: Mapped[int | None]
    height: Mapped[int | None]
    duration_ms: Mapped[int | None]
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    error: Mapped[str | None] = mapped_column(String(32))
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    finished_at: Mapped[datetime | None]


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[I18n]
    description: Mapped[I18n]
    icon: Mapped[str] = mapped_column(String(16))
    sort_order: Mapped[int] = mapped_column(server_default=text("0"))


class UserBadge(Base):
    __tablename__ = "user_badges"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id"), primary_key=True)
    earned_at: Mapped[datetime] = mapped_column(server_default=func.now())


# ------------------------------------------------------------------ activity & ops


class ActivityLog(Base):
    """Source of truth for points. Rows survive account deletion with user_id = NULL."""

    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(32))
    object_id: Mapped[str | None] = mapped_column(String(64))
    points: Mapped[int] = mapped_column(server_default=text("0"))
    # Calendar day in Asia/Tashkent — used for daily limits, streaks and the weekly board.
    local_date: Mapped[date]
    # Idempotency key sent by the client; a retried request never adds points twice.
    client_event_id: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # Points cancelled by an admin (TZ 8.12): the row stays for the record, but its action
    # becomes "voided" and points 0, so every sum and count leaves it out.
    # {"action": ..., "points": ..., "at": ..., "admin_id": ..., "reason": ...}
    voided: Mapped[dict[str, Any] | None]

    __table_args__ = (
        UniqueConstraint("user_id", "client_event_id", name="uq_activity_log_client_event"),
        Index(
            "uq_activity_log_once_per_object",
            "user_id",
            "action",
            "object_id",
            unique=True,
            postgresql_where=text("action IN ('project_done', 'quiz_correct')"),
        ),
        Index(
            "uq_activity_log_daily_task",
            "user_id",
            "local_date",
            unique=True,
            postgresql_where=text("action = 'daily_task'"),
        ),
        Index("ix_activity_log_user_date", "user_id", "local_date"),
        Index("ix_activity_log_date", "local_date"),
    )


class Report(Base):
    """Complaint about a nickname on the leaderboard (TZ 8.7)."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    target_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    reason: Mapped[str] = mapped_column(String(64))
    status: Mapped[ReportStatus] = mapped_column(
        str_enum(ReportStatus), server_default=ReportStatus.OPEN.value, index=True
    )
    resolution: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    resolved_at: Mapped[datetime | None]
    resolved_by: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL")
    )


class BannedWord(Base):
    """Profanity (uz/ru/en) and reserved nicknames, managed in the admin panel."""

    __tablename__ = "banned_words"

    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(String(64), unique=True)
    kind: Mapped[WordKind] = mapped_column(str_enum(WordKind))


class AdminUser(Base):
    """Admin panel account: login, password and a mandatory authenticator code (TZ 8.12)."""

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(64), unique=True)
    # Shown in the audit log and as the default "tested by" name.
    name: Mapped[str] = mapped_column(String(64))
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    totp_secret: Mapped[str | None] = mapped_column(String(64))
    # Set once the authenticator app is confirmed; until then login asks to set it up.
    totp_confirmed_at: Mapped[datetime | None]
    # Last accepted 30-second step: the same code can not be used twice.
    totp_last_step: Mapped[int | None] = mapped_column(BigInteger)
    role: Mapped[AdminRole] = mapped_column(str_enum(AdminRole))
    # The handover point a "point" account works at.
    pickup_point_id: Mapped[int | None] = mapped_column(
        ForeignKey("pickup_points.id", ondelete="SET NULL")
    )
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    failed_logins: Mapped[int] = mapped_column(server_default=text("0"))
    locked_until: Mapped[datetime | None]
    # Part of every session token; raising it signs the admin out everywhere.
    session_version: Mapped[int] = mapped_column(server_default=text("0"))
    last_login_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(64))
    object_type: Mapped[str] = mapped_column(String(64))
    object_id: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[dict[str, Any] | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)


class AnalyticsEvent(Base):
    """Product analytics events (TZ 14). user_id is the internal id, never the Telegram id."""

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(48))
    props: Mapped[dict[str, Any] | None]
    # The user's language and path when the event happened (TZ 14).
    language: Mapped[str | None] = mapped_column(String(2))
    path: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_analytics_events_name_created", "name", "created_at"),
        Index("ix_analytics_events_user_name", "user_id", "name"),
    )


# ------------------------------------------------------------------------ market


class ListingKind(enum.StrEnum):
    HANDMADE = "handmade"  # made by the user, usually from waste
    UNNEEDED = "unneeded"  # something the user no longer needs, to give away


class ListingStatus(enum.StrEnum):
    PENDING = "pending"  # waiting for a moderator; nobody else sees it
    APPROVED = "approved"  # in the market
    REJECTED = "rejected"
    RESERVED = "reserved"  # promised to a requester, to be brought to the handover point
    AT_POINT = "at_point"  # at the handover point, waiting to be collected
    GIVEN = "given"
    HIDDEN = "hidden"  # taken down by a moderator


class RequestStatus(enum.StrEnum):
    PENDING = "pending"  # waiting for the owner
    ACCEPTED = "accepted"  # the owner agreed; the item is on its way to the point
    AT_POINT = "at_point"
    DONE = "done"  # collected
    DECLINED = "declined"
    CANCELLED = "cancelled"
    EXPIRED = "expired"  # never brought to the point in time


class PickupPoint(ContentMixin, Base):
    """Handover point (school, eco-centre): adults take market items in and hand them out,
    so children never have to meet or contact each other."""

    __tablename__ = "pickup_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[I18n]
    address: Mapped[I18n]
    hours: Mapped[I18n]


class Listing(TimestampMixin, Base):
    """A thing in the market. Visible to others only after a moderator approved it."""

    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NULL only for an item already at a handover point when its owner deleted the account.
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[ListingKind] = mapped_column(str_enum(ListingKind))
    title: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(Text, server_default="")
    # Waste category code for handmade things, item type (books, toys…) for unneeded ones.
    category: Mapped[str] = mapped_column(String(32))
    condition: Mapped[str | None] = mapped_column(String(16))
    # Offered to others through a handover point; otherwise only shown.
    giveaway: Mapped[bool] = mapped_column(server_default=text("false"))
    pickup_point_id: Mapped[int | None] = mapped_column(ForeignKey("pickup_points.id"), index=True)
    # The item is at the handover point with nobody to collect it (the requester did not come
    # or withdrew): the next accepted request skips bringing it there.
    stored_at_point: Mapped[bool] = mapped_column(server_default=text("false"))
    status: Mapped[ListingStatus] = mapped_column(
        str_enum(ListingStatus), server_default=ListingStatus.PENDING.value
    )
    reject_reason: Mapped[str | None] = mapped_column(String(32))
    moderator_note: Mapped[str | None] = mapped_column(String(300))
    likes_count: Mapped[int] = mapped_column(server_default=text("0"))
    submitted_at: Mapped[datetime] = mapped_column(server_default=func.now())
    published_at: Mapped[datetime | None]
    reviewed_at: Mapped[datetime | None]
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL")
    )

    __table_args__ = (Index("ix_listings_status_published", "status", "published_at"),)


class ListingPhoto(Base):
    """A listing photo, already re-encoded without metadata (app.media). Kept in the database,
    so backups, restores and account deletion cover it like any other row."""

    __tablename__ = "listing_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Uploaded first and attached when the listing is saved; loose ones are removed after a day.
    listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    width: Mapped[int]
    height: Mapped[int]
    full: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    thumb: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ListingLike(Base):
    __tablename__ = "listing_likes"

    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ListingRequest(Base):
    """«I would like it»: a request for a listing that is given away, and its handover."""

    __tablename__ = "listing_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[RequestStatus] = mapped_column(
        str_enum(RequestStatus), server_default=RequestStatus.PENDING.value
    )
    # Said to the staff at the point: the owner's code when bringing the item,
    # the requester's code when collecting it.
    drop_code: Mapped[str | None] = mapped_column(String(6))
    pick_code: Mapped[str | None] = mapped_column(String(6))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    decided_at: Mapped[datetime | None]
    dropped_at: Mapped[datetime | None]
    given_at: Mapped[datetime | None]
    handled_by: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL")
    )

    __table_args__ = (
        # One open request per person and listing, one handover per listing.
        Index(
            "uq_listing_requests_open",
            "listing_id",
            "requester_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'accepted', 'at_point')"),
        ),
        Index(
            "uq_listing_requests_handover",
            "listing_id",
            unique=True,
            postgresql_where=text("status IN ('accepted', 'at_point')"),
        ),
    )


class ListingReport(Base):
    """Complaint about a listing; enough of them take it down until a moderator decides."""

    __tablename__ = "listing_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reason: Mapped[str] = mapped_column(String(32))
    status: Mapped[ReportStatus] = mapped_column(
        str_enum(ReportStatus), server_default=ReportStatus.OPEN.value, index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    resolved_at: Mapped[datetime | None]
    resolved_by: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL")
    )


# ---------------------------------------------------------- classes and leagues


class SchoolClass(Base):
    """A teacher's class (app/classes.py). Pupils join with its code; nobody joins unasked."""

    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(40))
    code: Mapped[str] = mapped_column(String(8), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ClassMember(Base):
    __tablename__ = "class_members"

    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # A pupil is in one class at a time.
    __table_args__ = (Index("uq_class_members_user", "user_id", unique=True),)


class ClassTask(Base):
    """A project the teacher gave the class, to be done by a day (Tashkent time)."""

    __tablename__ = "class_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    due_date: Mapped[date]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (UniqueConstraint("class_id", "project_id", name="uq_class_tasks_project"),)


class LeagueGroup(Base):
    """Up to 30 players of one tier who compete for one week (app/leagues.py)."""

    __tablename__ = "league_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_start: Mapped[date]
    tier: Mapped[int] = mapped_column(SmallInteger)

    __table_args__ = (Index("ix_league_groups_week_tier", "week_start", "tier"),)


class LeagueMember(Base):
    __tablename__ = "league_members"

    week_start: Mapped[date] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("league_groups.id", ondelete="CASCADE"), index=True
    )
    # The tier the week was played in; the result moves users.league_tier for the next week.
    tier: Mapped[int] = mapped_column(SmallInteger)
