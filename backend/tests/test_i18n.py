import pytest

from app.i18n import BOT_TEXTS, SUPPORTED_LANGUAGES, pick_language, t


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("uz", "uz"),
        ("ru", "ru"),
        ("en", "en"),
        ("ru-RU", "ru"),
        ("en_US", "en"),
        ("UZ", "uz"),
        ("kk", "uz"),
        ("de", "uz"),
        ("", "uz"),
        (None, "uz"),
    ],
)
def test_pick_language(code, expected):
    # TZ 6 / QM-02: uz, ru, en map to themselves, everything else falls back to Uzbek.
    assert pick_language(code) == expected


def test_bot_descriptions_fit_telegram_limits():
    for lang in SUPPORTED_LANGUAGES:
        assert len(t("bot_description", lang)) <= 512
        assert len(t("bot_short_description", lang)) <= 120


@pytest.mark.parametrize("key", sorted(BOT_TEXTS))
def test_every_bot_text_exists_in_all_languages(key):
    for lang in SUPPORTED_LANGUAGES:
        assert BOT_TEXTS[key].get(lang), f"{key} has no {lang} text"
