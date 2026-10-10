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

    reminders_enabled: Mapped[bool] = mapped_column(server_default=text("true"))
    reminder_time: Mapped[time] = mapped_column(server_default=text("'18:00'"))
    # True once the user has started the bot or granted requestWriteAccess.
    write_access: Mapped[bool] = mapped_column(server_default=text("false"))

    is_blocked: Mapped[bool] = mapped_column(server_default=text("false"))
    nickname_hidden: Mapped[bool] = mapped_column(server_default=text("false"))
    nickname_changed_at: Mapped[datetime | None]

    # Cache of values derived from activity_log.
    points_total: Mapped[int] = mapped_column(server_default=text("0"))
    streak_current: Mapped[int] = mapped_column(server_default=text("0"))
    streak_best: Mapped[int] = mapped_column(server_default=text("0"))
    last_task_date: Mapped[date | None]

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


class BannedWord(Base):
    """Profanity (uz/ru/en) and reserved nicknames, managed in the admin panel."""

    __tablename__ = "banned_words"

    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(String(64), unique=True)
    kind: Mapped[WordKind] = mapped_column(str_enum(WordKind))


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    totp_secret: Mapped[str | None] = mapped_column(String(64))
    role: Mapped[AdminRole] = mapped_column(str_enum(AdminRole))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
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
    name: Mapped[str] = mapped_column(String(48), index=True)
    props: Mapped[dict[str, Any] | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
