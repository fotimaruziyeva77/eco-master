"""Server-side texts (bot messages). The Mini App keeps its own locale files."""

SUPPORTED_LANGUAGES = ("uz", "ru", "en")
DEFAULT_LANGUAGE = "uz"


def pick_language(code: str | None) -> str:
    """Map Telegram's language_code to an app language (TZ 6): uz/ru/en, otherwise Uzbek."""
    if not code:
        return DEFAULT_LANGUAGE
    base = code.lower().replace("_", "-").split("-")[0]
    return base if base in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


BOT_TEXTS: dict[str, dict[str, str]] = {
    "start": {
        "uz": (
            "Salom! 🌱 <b>Ekoustoz</b>ga xush kelibsiz.\n\n"
            "Bu yerda chiqindini to'g'ri saralashni, undan foydali buyumlar yasashni "
            "o'rganasiz, o'yin va topshiriqlar orqali ball to'playsiz."
        ),
        "ru": (
            "Привет! 🌱 Добро пожаловать в <b>Ekoustoz</b>.\n\n"
            "Здесь вы научитесь правильно сортировать отходы и делать из них полезные "
            "вещи, а за игры и задания будете получать баллы."
        ),
        "en": (
            "Hi! 🌱 Welcome to <b>Ekoustoz</b>.\n\n"
            "Learn to sort waste the right way and turn it into useful things, "
            "and earn points for games and daily tasks."
        ),
    },
    "open_app": {"uz": "Ilovani ochish", "ru": "Открыть приложение", "en": "Open the app"},
    "help": {
        "uz": (
            "Ilovani ochish uchun pastdagi tugmani bosing.\n"
            "Savol yoki taklifingiz bo'lsa, shu chatga yozing — jamoamiz o'qiydi."
        ),
        "ru": (
            "Нажмите кнопку ниже, чтобы открыть приложение.\n"
            "Если есть вопрос или предложение, напишите в этот чат — команда прочитает."
        ),
        "en": (
            "Tap the button below to open the app.\n"
            "Questions or ideas? Write to this chat — our team reads every message."
        ),
    },
    "cmd_start": {"uz": "Ilovani ochish", "ru": "Открыть приложение", "en": "Open the app"},
    "cmd_help": {"uz": "Yordam", "ru": "Помощь", "en": "Help"},
}


def t(key: str, lang: str) -> str:
    texts = BOT_TEXTS[key]
    return texts.get(lang) or texts[DEFAULT_LANGUAGE]
