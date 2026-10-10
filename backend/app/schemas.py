import uuid
from datetime import date, datetime, time, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from app.levels import level_for
from app.models import Difficulty, OnboardingStep, SafetyLevel, UserPath
from app.sharing import ShareKind
from app.timeutil import local_today

Language = Literal["uz", "ru", "en"]
NICKNAME_CHANGE_INTERVAL = timedelta(days=30)
I18nText = dict[str, Any]  # {"uz": ..., "ru": ..., "en": ...}; the Mini App picks the language


class TelegramAuthIn(BaseModel):
    init_data: str = Field(min_length=1, max_length=4096)


class LevelOut(BaseModel):
    code: str
    min_points: int
    next_min_points: int | None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str | None
    language: Language
    path: UserPath | None
    onboarding_step: OnboardingStep
    points_total: int
    streak_current: int
    streak_best: int
    reminders_enabled: bool
    reminder_time: time
    write_access: bool
    last_task_date: date | None
    nickname_changed_at: datetime | None

    @model_validator(mode="after")
    def _live_streak(self) -> "UserOut":
        # The stored streak is stale once a whole day has been missed.
        today = local_today()
        if self.last_task_date is None or self.last_task_date < today - timedelta(days=1):
            self.streak_current = 0
        return self

    @computed_field
    @property
    def done_today(self) -> bool:
        return self.last_task_date == local_today()

    @computed_field
    @property
    def nickname_change_available_at(self) -> datetime | None:
        if self.nickname_changed_at is None:
            return None
        return self.nickname_changed_at + NICKNAME_CHANGE_INTERVAL

    @computed_field
    @property
    def level(self) -> LevelOut:
        lvl = level_for(self.points_total)
        return LevelOut(
            code=lvl.code, min_points=lvl.min_points, next_min_points=lvl.next_min_points
        )


class AuthOut(BaseModel):
    token: str
    user: UserOut


class MeUpdate(BaseModel):
    language: Language | None = None
    path: UserPath | None = None
    reminders_enabled: bool | None = None
    reminder_time: time | None = None

    @field_validator("reminder_time")
    @classmethod
    def _reminder_window(cls, value: time | None) -> time | None:
        # Reminders go out between 08:00 and 20:00, on the hour or half hour (TZ 8.5).
        if value is None:
            return value
        if not (time(8, 0) <= value <= time(20, 0)) or value.minute not in (0, 30) or value.second:
            raise ValueError("reminder time must be 08:00–20:00 in 30-minute steps")
        return value


class WriteAccessIn(BaseModel):
    granted: bool


class DevInitDataOut(BaseModel):
    init_data: str


# ------------------------------------------------------------------ onboarding


class OnboardingLanguageIn(BaseModel):
    language: Language


class OnboardingPathIn(BaseModel):
    path: UserPath


class NicknameIn(BaseModel):
    # Longer than the 20-character limit so the server can answer with a clear error code.
    nickname: str = Field(max_length=64)


class NicknameCheckOut(BaseModel):
    ok: bool
    error: str | None = None


# --------------------------------------------------------------------- content


class CategoryOut(BaseModel):
    code: str
    name: I18nText
    examples: I18nText | None = None
    icon: str
    color: str
    has_projects: bool
    is_game_bin: bool
    project_count: int = 0


class ProjectSummaryOut(BaseModel):
    slug: str
    category_code: str
    title: I18nText
    difficulty: Difficulty
    safety_level: SafetyLevel
    duration_min: int
    poster_url: str | None
    has_video: bool
    done: bool


class ProjectDetailOut(ProjectSummaryOut):
    category_name: I18nText
    category_icon: str
    materials: I18nText
    steps: I18nText
    safety_text: I18nText | None
    video_url: str | None
    done_count: int = 0


class CategoryDetailOut(BaseModel):
    category: CategoryOut
    projects: list[ProjectSummaryOut]


class BadgeOut(BaseModel):
    code: str
    name: I18nText
    description: I18nText
    icon: str
    earned_at: datetime | None = None
    progress_current: int | None = None
    progress_target: int | None = None


class DoneIn(BaseModel):
    client_event_id: uuid.UUID


class DoneOut(BaseModel):
    awarded: bool
    points: int
    points_total: int
    new_badges: list[BadgeOut] = []


class CardSummaryOut(BaseModel):
    slug: str
    title: I18nText
    image_url: str | None


class CardDetailOut(CardSummaryOut):
    sections: I18nText


class TipOut(BaseModel):
    id: int
    text: I18nText


class DailyTaskOut(BaseModel):
    id: int
    text: I18nText
    points: int


class DailyOut(BaseModel):
    task: DailyTaskOut | None
    done_today: bool
    streak_current: int
    streak_best: int
    days_to_bonus: int
    bonus_points: int


class DailyDoneOut(BaseModel):
    awarded: bool
    points: int
    bonus_points: int
    streak_current: int
    streak_best: int
    points_total: int
    new_badges: list["BadgeOut"] = []


class HomeOut(BaseModel):
    user: UserOut
    daily: DailyOut
    tip: TipOut | None
    categories: list[CategoryOut]
    featured: ProjectSummaryOut | None = None


# ---------------------------------------------------------------- profile, rating


class StatsOut(BaseModel):
    streak_current: int
    streak_best: int
    tasks_done: int
    projects_done: int
    projects_total: int
    quiz_correct: int
    quiz_answered: int
    sorted_correct: int
    sorted_total: int
    badges_earned: int
    badges_total: int
    rank_all: int | None


class LeaderboardEntryOut(BaseModel):
    rank: int
    user_id: int
    nickname: str
    level_code: str
    points: int
    is_me: bool


class LeaderboardOut(BaseModel):
    period: Literal["week", "all"]
    week_start: date | None
    entries: list[LeaderboardEntryOut]
    me: LeaderboardEntryOut | None


class ReportIn(BaseModel):
    target_user_id: int
    reason: Literal["nickname"] = "nickname"


# ----------------------------------------------------------------------- games


class QuizCategoryOut(BaseModel):
    code: str
    name: I18nText
    icon: str
    question_count: int


class GamesOut(BaseModel):
    quiz_categories: list[QuizCategoryOut]
    quiz_total: int
    bins: list[CategoryOut]
    game_item_count: int
    game_points_today: int
    game_daily_cap: int


class QuizRoundIn(BaseModel):
    category: str | None = None  # None = mixed, including general ecology questions


class QuizQuestionOut(BaseModel):
    id: int
    category_code: str | None
    text: I18nText
    options: I18nText
    image_url: str | None


class QuizRoundOut(BaseModel):
    round_token: str
    questions: list[QuizQuestionOut]


class QuizAnswerIn(BaseModel):
    round_token: str = Field(max_length=4096)
    question_id: int
    option_index: int = Field(ge=0, le=9)


class QuizAnswerOut(BaseModel):
    correct: bool
    correct_index: int
    explanation: I18nText
    points: int
    points_total: int
    new_badges: list[BadgeOut] = []


class GameItemOut(BaseModel):
    id: int
    name: I18nText
    icon: str | None
    image_url: str | None


class GameRoundOut(BaseModel):
    round_token: str
    items: list[GameItemOut]


class GameAnswerIn(BaseModel):
    round_token: str = Field(max_length=4096)
    item_id: int
    bin: str | None = Field(default=None, max_length=32)  # None = time ran out


class GameAnswerOut(BaseModel):
    correct: bool
    correct_bin: str
    explanation: I18nText
    points: int
    points_today: int
    daily_cap: int
    points_total: int
    new_badges: list[BadgeOut] = []


# ---------------------------------------------------------------- teachers, share


class LessonSummaryOut(BaseModel):
    slug: str
    title: I18nText
    grade: str


class LessonOut(LessonSummaryOut):
    body: I18nText  # {"uz": {"goal": ..., "materials": [...], "plan": [...], ...}, ...}


class LessonSendIn(BaseModel):
    language: Language | None = None


class ShareIn(BaseModel):
    kind: ShareKind = "progress"
    # project slug, badge code, or "correct/total" for game results
    object_id: str | None = Field(default=None, max_length=64)


class ShareOut(BaseModel):
    text: str
    url: str
    # Telegram 8.0+: id for WebApp.shareMessage.
    prepared_message_id: str | None = None
    # Older clients: query for WebApp.switchInlineQuery (only when inline mode is on).
    inline_query: str | None = None
