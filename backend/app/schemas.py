from datetime import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import OnboardingStep, UserPath

Language = Literal["uz", "ru", "en"]


class TelegramAuthIn(BaseModel):
    init_data: str = Field(min_length=1, max_length=4096)


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


class AuthOut(BaseModel):
    token: str
    user: UserOut


class MeUpdate(BaseModel):
    language: Language | None = None


class DevInitDataOut(BaseModel):
    init_data: str
