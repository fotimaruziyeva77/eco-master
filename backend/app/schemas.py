import uuid
from datetime import datetime, time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.levels import level_for
from app.models import Difficulty, OnboardingStep, SafetyLevel, UserPath

Language = Literal["uz", "ru", "en"]
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


class CategoryDetailOut(BaseModel):
    category: CategoryOut
    projects: list[ProjectSummaryOut]


class BadgeOut(BaseModel):
    code: str
    name: I18nText
    description: I18nText
    icon: str
    earned_at: datetime | None = None


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


class HomeOut(BaseModel):
    user: UserOut
    tip: TipOut | None
    categories: list[CategoryOut]


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
