"""Request and response bodies of the admin API."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import (
    AdminRole,
    ContentStatus,
    ListingKind,
    ListingStatus,
    ReportStatus,
    RequestStatus,
    VideoStatus,
    WordKind,
)

# ----------------------------------------------------------------------- auth


class LoginIn(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TotpSetupOut(BaseModel):
    secret: str
    uri: str


class LoginOut(BaseModel):
    # Short-lived; exchanged for the session together with the authenticator code.
    token: str
    # First sign-in: connect an authenticator app before the code can be checked.
    setup: TotpSetupOut | None = None


class CodeIn(BaseModel):
    token: str = Field(max_length=2048)
    code: str = Field(min_length=6, max_length=8)


class AdminMeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    name: str
    role: AdminRole
    # Handover point staff: the point they work at.
    pickup_point_id: int | None = None


class PasswordChangeIn(BaseModel):
    current: str = Field(max_length=128)
    new: str = Field(max_length=128)


# --------------------------------------------------------------------- admins


class AdminOut(AdminMeOut):
    is_active: bool
    totp_enabled: bool
    locked: bool
    last_login_at: datetime | None
    created_at: datetime


class AdminCreateIn(BaseModel):
    login: str = Field(pattern=r"^[a-z0-9._-]{3,64}$")
    name: str = Field(min_length=1, max_length=64)
    role: AdminRole
    password: str = Field(max_length=128)
    pickup_point_id: int | None = None


class AdminUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    role: AdminRole | None = None
    is_active: bool | None = None
    pickup_point_id: int | None = None


class PasswordSetIn(BaseModel):
    password: str = Field(max_length=128)


# -------------------------------------------------------------------- content


class FieldOptionOut(BaseModel):
    value: str
    label: str


class FieldSpecOut(BaseModel):
    name: str
    label: str
    kind: str
    required: bool
    nullable: bool
    fixed: bool
    help: str | None = None
    options: list[FieldOptionOut] | None = None
    min: int | None = None
    max: int | None = None
    max_length: int | None = None


class ContentTypeOut(BaseModel):
    key: str
    title: str
    has_status: bool
    deletable: bool
    preview: str
    counts: dict[str, int]


class ContentMetaOut(ContentTypeOut):
    fields: list[FieldSpecOut]
    defaults: dict[str, Any]


class IssueOut(BaseModel):
    level: Literal["error", "warning"]
    message: str
    field: str | None = None
    lang: str | None = None


class ContentRowOut(BaseModel):
    id: int
    title: str
    subtitle: str
    status: ContentStatus | None
    updated_at: datetime | None
    errors: int
    warnings: int


class ContentItemOut(BaseModel):
    id: int
    status: ContentStatus | None
    values: dict[str, Any]
    issues: list[IssueOut]
    created_at: datetime | None
    updated_at: datetime | None


class ContentValuesIn(BaseModel):
    values: dict[str, Any]


class StatusIn(BaseModel):
    status: ContentStatus


# ------------------------------------------------------------------- schedule


class ScheduleOptionOut(BaseModel):
    id: int
    title: str


class ScheduleDayOut(BaseModel):
    day: date
    item_id: int | None
    item_title: str | None
    # What the rotation picks when nothing is scheduled (TZ 8.5).
    auto_item_id: int | None
    auto_item_title: str | None


class ScheduleOut(BaseModel):
    kind: Literal["daily", "tips"]
    days: list[ScheduleDayOut]
    items: list[ScheduleOptionOut]


class ScheduleSetIn(BaseModel):
    item_id: int | None


# ---------------------------------------------------------------------- users


class AdminUserRowOut(BaseModel):
    id: int
    nickname: str | None
    language: str
    path: str | None
    source: str | None
    points_total: int
    streak_current: int
    onboarding_done: bool
    is_blocked: bool
    nickname_hidden: bool
    open_reports: int
    created_at: datetime
    last_active_at: datetime


class ActivityRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    object_id: str | None
    points: int
    local_date: date
    created_at: datetime
    voided: dict[str, Any] | None


class ReportOut(BaseModel):
    id: int
    reporter_id: int | None
    target_user_id: int
    target_nickname: str | None
    reason: str
    status: ReportStatus
    resolution: str | None
    created_at: datetime
    resolved_at: datetime | None
    resolved_by: str | None


class UserFlagOut(BaseModel):
    kind: Literal["points", "fast"]
    message: str
    day: date


class BadgeRefOut(BaseModel):
    code: str
    name: str
    icon: str


class AdminUserDetailOut(AdminUserRowOut):
    telegram_id: int
    streak_best: int
    last_task_date: date | None
    reminders_enabled: bool
    write_access: bool
    badges: list[BadgeRefOut]
    counts: dict[str, int]
    flags: list[UserFlagOut]
    reports: list[ReportOut]
    activity: list[ActivityRowOut]


class BlockIn(BaseModel):
    blocked: bool
    reason: str | None = Field(default=None, max_length=200)


class NicknameActionIn(BaseModel):
    # hide: off the leaderboard; reset: the user must choose a new nickname.
    action: Literal["hide", "show", "reset"]
    reason: str | None = Field(default=None, max_length=200)


class VoidIn(BaseModel):
    entry_ids: list[int] = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=3, max_length=200)


# -------------------------------------------------------------------- reports


class ReportGroupOut(BaseModel):
    target: AdminUserRowOut
    count: int
    reasons: list[str]
    first_at: datetime
    last_at: datetime


class ResolveIn(BaseModel):
    target_user_id: int
    action: Literal["dismiss", "hide", "reset", "block"]
    note: str | None = Field(default=None, max_length=200)


# ---------------------------------------------------------------------- words


class WordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    word: str
    kind: WordKind


class WordIn(BaseModel):
    word: str = Field(min_length=2, max_length=64)
    kind: WordKind

    @field_validator("word")
    @classmethod
    def normalise(cls, value: str) -> str:
        value = value.strip().lower()
        if not value or any(c.isspace() for c in value):
            raise ValueError("one word without spaces")
        return value


# ---------------------------------------------------------------------- audit


class AuditRowOut(BaseModel):
    id: int
    created_at: datetime
    admin_id: int | None
    admin_name: str | None
    action: str
    object_type: str
    object_id: str | None
    details: dict[str, Any] | None


class AuditPageOut(BaseModel):
    rows: list[AuditRowOut]
    next_before_id: int | None


# --------------------------------------------------------------------- flags


class PointsFlagOut(BaseModel):
    user_id: int
    nickname: str | None
    day: date
    points: int


class FastFlagOut(BaseModel):
    user_id: int
    nickname: str | None
    game: Literal["quiz", "sort"]
    day: date
    answers: int
    avg_seconds: float


class FlagsOut(BaseModel):
    points: list[PointsFlagOut]
    fast: list[FastFlagOut]


# --------------------------------------------------------------------- market


class MarketCountsOut(BaseModel):
    pending: int
    reported: int


class MarketRowOut(BaseModel):
    id: int
    title: str
    kind: ListingKind
    status: ListingStatus
    giveaway: bool
    owner_id: int | None
    owner_nickname: str | None
    thumb_url: str | None
    reports_open: int
    submitted_at: datetime
    created_at: datetime


class MarketPhotoOut(BaseModel):
    id: int
    url: str
    thumb_url: str
    width: int
    height: int


class MarketRequestRowOut(BaseModel):
    id: int
    requester_id: int
    nickname: str | None
    status: RequestStatus
    created_at: datetime
    decided_at: datetime | None
    dropped_at: datetime | None
    given_at: datetime | None


class MarketReportRowOut(BaseModel):
    id: int
    reason: str
    status: ReportStatus
    created_at: datetime


class MarketListingOut(MarketRowOut):
    description: str
    category: str
    category_name: str
    condition: str | None
    point_name: str | None
    stored_at_point: bool
    reject_reason: str | None
    moderator_note: str | None
    likes: int
    published_at: datetime | None
    reviewed_at: datetime | None
    reviewed_by: str | None
    photos: list[MarketPhotoOut]
    requests: list[MarketRequestRowOut]
    reports: list[MarketReportRowOut]


class MarketDecisionIn(BaseModel):
    reason: Literal["personal_info", "face", "not_eco", "forbidden", "bad_photo", "other"]
    # Goes to the child with the bot message: kind and simple words.
    note: str | None = Field(default=None, max_length=300)


class HandoverPointOut(BaseModel):
    id: int
    name: str


class HandoverItemOut(BaseModel):
    # None for an item waiting at the point with nobody to collect it.
    request_id: int | None
    listing_id: int
    title: str
    thumb_url: str | None
    owner_nickname: str | None
    requester_nickname: str | None
    status: RequestStatus | None
    since: datetime | None
    deadline: datetime | None


class HandoverDeskOut(BaseModel):
    point: HandoverPointOut
    # The owner will bring these.
    waiting_drop: list[HandoverItemOut]
    # At the point; the requester will collect them.
    waiting_pick: list[HandoverItemOut]
    # At the point with nobody to collect them yet.
    stored: list[HandoverItemOut]


class HandoverCodeIn(BaseModel):
    code: str = Field(pattern=r"^[0-9]{6}$")
    point_id: int | None = None


class HandoverMatchOut(BaseModel):
    action: Literal["receive", "give"]
    item: HandoverItemOut


# ---------------------------------------------------------------------- media


class MediaStatusOut(BaseModel):
    # False when ffmpeg is missing: the admin page says so before sending a big file.
    video: bool


class PictureOut(BaseModel):
    url: str
    width: int
    height: int


class VideoOut(BaseModel):
    id: int
    status: VideoStatus
    name: str
    url: str | None = None
    poster_url: str | None = None
    width: int | None = None
    height: int | None = None
    duration_ms: int | None = None
    size_bytes: int | None = None
    error: str | None = None
