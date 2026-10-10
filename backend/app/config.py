from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Used only outside production when BOT_TOKEN is empty, so initData can be signed and
# checked locally without a real bot.
DEV_BOT_TOKEN = "0:dev-only-token"
INSECURE_JWT_SECRET = "dev-only-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    env: Literal["dev", "test", "prod"] = "dev"
    database_url: str = "postgresql+asyncpg://ekoustoz:ekoustoz@127.0.0.1:55440/ekoustoz"

    bot_token: str = ""
    bot_username: str = ""
    webapp_short_name: str = "app"
    webapp_url: str = "http://localhost:5180"

    jwt_secret: str = INSECURE_JWT_SECRET
    jwt_ttl_hours: int = 24
    init_data_max_age_hours: int = 24

    cors_origins: str = "http://localhost:5180"
    dev_auth: bool = False

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"

    @property
    def effective_bot_token(self) -> str:
        if self.bot_token:
            return self.bot_token
        if self.is_prod:
            raise RuntimeError("BOT_TOKEN must be set in production")
        return DEV_BOT_TOKEN

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def dev_auth_enabled(self) -> bool:
        return self.env == "dev" and self.dev_auth

    def check_production(self) -> None:
        """Refuse to start in production with development defaults."""
        if not self.is_prod:
            return
        problems = []
        if not self.bot_token:
            problems.append("BOT_TOKEN is empty")
        if self.jwt_secret == INSECURE_JWT_SECRET or len(self.jwt_secret) < 32:
            problems.append("JWT_SECRET is missing or too short")
        if not self.webapp_url.startswith("https://"):
            problems.append("WEBAPP_URL must be https")
        if problems:
            raise RuntimeError("Unsafe production config: " + "; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()
