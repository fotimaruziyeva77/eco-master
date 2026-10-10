import pytest

from app.config import INSECURE_JWT_SECRET, Settings


def test_blank_optional_values_mean_not_set(monkeypatch):
    # deploy/.env.example leaves the optional values blank.
    monkeypatch.setenv("FEEDBACK_CHAT_ID", "")
    monkeypatch.setenv("WEBAPP_SHORT_NAME", "")
    settings = Settings(_env_file=None)
    assert settings.feedback_chat_id is None
    assert settings.webapp_short_name == "app"


def test_production_refuses_development_defaults():
    settings = Settings(
        _env_file=None,
        env="prod",
        bot_token="",
        jwt_secret=INSECURE_JWT_SECRET,
        webapp_url="http://example.org",
    )
    with pytest.raises(RuntimeError) as error:
        settings.check_production()
    message = str(error.value)
    assert "BOT_TOKEN" in message and "JWT_SECRET" in message and "https" in message


def test_production_config_passes():
    Settings(
        _env_file=None,
        env="prod",
        bot_token="123:abc",
        jwt_secret="x" * 32,
        webapp_url="https://ekoustoz.example.uz",
    ).check_production()
