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
            "Salom! 🌱 <b>Eco-Master</b>ga xush kelibsiz.\n\n"
            "Bu yerda chiqindini to'g'ri saralashni, undan foydali buyumlar yasashni "
            "o'rganasiz, o'yin va topshiriqlar orqali ball to'playsiz."
        ),
        "ru": (
            "Привет! 🌱 Добро пожаловать в <b>Eco-Master</b>.\n\n"
            "Здесь вы научитесь правильно сортировать отходы и делать из них полезные "
            "вещи, а за игры и задания будете получать баллы."
        ),
        "en": (
            "Hi! 🌱 Welcome to <b>Eco-Master</b>.\n\n"
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
    # Telegram limits: description 512 characters, short description 120.
    "bot_description": {
        "uz": "Eco-Master — chiqindiga ikkinchi hayot berishni o'rgatadigan ilova.\n\n"
        "🌱 Chiqindini to'g'ri saralashni o'rganing\n"
        "🎨 Undan foydali buyumlar yasang\n"
        "🧠 Viktorina va o'yinlarda ball to'plang\n"
        "🛍 Eko-bozorda yasaganlaringizni ko'rsating\n\n"
        "Boshlash uchun «Start» tugmasini bosing.",
        "ru": "Eco-Master — приложение, которое учит давать отходам вторую жизнь.\n\n"
        "🌱 Учись правильно сортировать отходы\n"
        "🎨 Делай из них полезные вещи\n"
        "🧠 Набирай баллы в викторинах и играх\n"
        "🛍 Показывай свои поделки на Эко-рынке\n\n"
        "Нажми «Старт», чтобы начать.",
        "en": "Eco-Master teaches how to give waste a second life.\n\n"
        "🌱 Learn to sort waste the right way\n"
        "🎨 Make useful things from it\n"
        "🧠 Earn points in quizzes and games\n"
        "🛍 Show what you made in the Eco market\n\n"
        "Tap «Start» to begin.",
    },
    "bot_short_description": {
        "uz": "Chiqindini saralash, undan buyum yasash, viktorina, o'yinlar va eko-bozor. 🌱",
        "ru": "Сортировка отходов, поделки, викторины, игры и эко-рынок. 🌱",
        "en": "Sort waste, make things from it, play quizzes and games, visit the eco market. 🌱",
    },
}

BOT_TEXTS.update(
    {
        "reminder": {
            "uz": "🌱 Salom, {name}! Bugungi topshiriq sizni kutmoqda:\n"
            "\n"
            "<b>{task}</b>\n"
            "\n"
            "{streak}",
            "ru": "🌱 Привет, {name}! Тебя ждёт задание дня:\n\n<b>{task}</b>\n\n{streak}",
            "en": "🌱 Hi {name}! Today's task is waiting for you:\n\n<b>{task}</b>\n\n{streak}",
        },
        "reminder_streak": {
            "uz": "🔥 Streakingiz: {days} kun — uzib qo'ymang!",
            "ru": "🔥 Ваша серия: {days} дн. — не прерывайте её!",
            "en": "🔥 Your streak: {days} days — keep it going!",
        },
        "reminder_streak_start": {
            "uz": "🔥 Bugun yangi streak boshlang!",
            "ru": "🔥 Начните сегодня новую серию!",
            "en": "🔥 Start a new streak today!",
        },
        "feedback_thanks": {
            "uz": "Rahmat! Xabaringiz jamoaga yetkazildi. 💚",
            "ru": "Спасибо! Ваше сообщение передано команде. 💚",
            "en": "Thank you! Your message has been passed to the team. 💚",
        },
        "share_title": {
            "uz": "Mening Eco-Master natijam",
            "ru": "Мой результат в Eco-Master",
            "en": "My Eco-Master result",
        },
        "share_progress": {
            "uz": "Mening Eco-Master'dagi natijam: {projects} ta buyumga ikkinchi hayot "
            "berdim 🌱 va {points} ball to'pladim! Sen ham qo'shil 👇",
            "ru": "Мой результат в Eco-Master: сделано проектов — {projects} 🌱, баллов — "
            "{points}! Присоединяйся 👇",
            "en": "My Eco-Master progress: {projects} things given a second life 🌱 and "
            "{points} points! Join me 👇",
        },
        "share_points": {
            "uz": "Mening Eco-Master'dagi natijam: {points} ball! 🌱 Sen ham qo'shil 👇",
            "ru": "Мой результат в Eco-Master: баллов — {points}! 🌱 Присоединяйся 👇",
            "en": "My Eco-Master score: {points}! 🌱 Join me 👇",
        },
        "share_invite": {
            "uz": "🌱 Eco-Master — chiqindini to'g'ri saralash, eko-loyihalar va viktorinalar. "
            "Qo'shil 👇",
            "ru": "🌱 Eco-Master — учимся сортировать отходы, делаем эко-проекты и играем в "
            "викторины. Присоединяйся 👇",
            "en": "🌱 Eco-Master — learn to sort waste, make eco projects and play quizzes. "
            "Join in 👇",
        },
        "share_project": {
            "uz": "Men «{title}» loyihasini yasadim! ♻️ Sen ham urinib ko'r 👇",
            "ru": "Готов мой проект «{title}»! ♻️ Попробуй и ты 👇",
            "en": "I made «{title}»! ♻️ Give it a try 👇",
        },
        "share_badge": {
            "uz": "Eco-Master'da «{badge}» nishonini oldim! 🏅 Sen ham qo'shil 👇",
            "ru": "Получен значок «{badge}» в Eco-Master! 🏅 Присоединяйся 👇",
            "en": "I earned the «{badge}» badge in Eco-Master! 🏅 Join me 👇",
        },
        "share_quiz": {
            "uz": "Eco-Master viktorinasida {correct}/{total} to'g'ri javob berdim! 🧠 Sen-chi? 👇",
            "ru": "Мой результат в викторине Eco-Master: {correct}/{total} 🧠 А у тебя? 👇",
            "en": "I got {correct}/{total} in the Eco-Master quiz! 🧠 Can you beat it? 👇",
        },
        "share_sort": {
            "uz": "Saralash o'yinida {correct}/{total} buyumni to'g'ri saraladim! ♻️ Sen-chi? 👇",
            "ru": "Мой результат в игре-сортировке: {correct}/{total} ♻️ А у тебя? 👇",
            "en": "I sorted {correct}/{total} items correctly! ♻️ Can you beat it? 👇",
        },
        "pdf_caption": {
            "uz": "📄 {title}\nEco-Master — o'qituvchilar uchun dars",
            "ru": "📄 {title}\nEco-Master — урок для учителей",
            "en": "📄 {title}\nEco-Master — a lesson for teachers",
        },
        "pdf_header": {
            "uz": "Eco-Master — o'qituvchilar uchun dars",
            "ru": "Eco-Master — урок для учителей",
            "en": "Eco-Master — a lesson for teachers",
        },
        "pdf_grade": {"uz": "Sinf: {grade}", "ru": "Класс: {grade}", "en": "Grade: {grade}"},
        "pdf_duration": {
            "uz": "Davomiyligi: 45 daqiqa",
            "ru": "Длительность: 45 минут",
            "en": "Length: 45 minutes",
        },
        "pdf_goal": {"uz": "Darsning maqsadi", "ru": "Цель урока", "en": "Lesson goal"},
        "pdf_materials": {"uz": "Kerakli materiallar", "ru": "Что понадобится", "en": "Materials"},
        "pdf_plan": {"uz": "Dars rejasi", "ru": "План урока", "en": "Lesson plan"},
        "pdf_minutes": {"uz": "{n} daqiqa", "ru": "{n} мин", "en": "{n} min"},
        "pdf_questions": {
            "uz": "Muhokama uchun savollar",
            "ru": "Вопросы для обсуждения",
            "en": "Discussion questions",
        },
        "pdf_homework": {"uz": "Uyga vazifa", "ru": "Домашнее задание", "en": "Homework"},
        "pdf_app_task": {
            "uz": "Eco-Master ilovasi bilan",
            "ru": "С приложением Eco-Master",
            "en": "With the Eco-Master app",
        },
        "pdf_footer": {
            "uz": "Eco-Master — chiqindiga ikkinchi hayot",
            "ru": "Eco-Master — вторая жизнь для отходов",
            "en": "Eco-Master — a second life for waste",
        },
    }
)


# Market (phase 9). {reason} is replaced with a market_reason_* text, {note} with market_note.
BOT_TEXTS.update(
    {
        "market_note": {
            "uz": "\n\nModerator izohi: {note}",
            "ru": "\n\nКомментарий модератора: {note}",
            "en": "\n\nModerator's note: {note}",
        },
        "market_reason_personal_info": {
            "uz": "rasmda yoki matnda shaxsiy ma'lumot bor (ism, manzil, telefon, maktab)",
            "ru": "на фото или в тексте есть личные данные (имя, адрес, телефон, школа)",
            "en": "the photo or text shows personal details (name, address, phone, school)",
        },
        "market_reason_face": {
            "uz": "rasmda odamning yuzi ko'rinib turibdi",
            "ru": "на фото видно лицо человека",
            "en": "a person's face can be seen in the photo",
        },
        "market_reason_not_eco": {
            "uz": "bu narsa bozor mavzusiga mos emas",
            "ru": "эта вещь не подходит для рынка",
            "en": "this item does not fit the market",
        },
        "market_reason_forbidden": {
            "uz": "bunday narsalarni bozorga qo'yib bo'lmaydi",
            "ru": "такие вещи нельзя выставлять на рынок",
            "en": "such items are not allowed in the market",
        },
        "market_reason_bad_photo": {
            "uz": "rasm xira yoki buyum yaxshi ko'rinmaydi",
            "ru": "фото нечёткое или вещь плохо видно",
            "en": "the photo is blurry or the item is hard to see",
        },
        "market_reason_reports": {
            "uz": "boshqa foydalanuvchilar shikoyat qildi, moderator tekshiradi",
            "ru": "на неё пожаловались, модератор проверит",
            "en": "other users reported it; a moderator will check it",
        },
        "market_reason_other": {
            "uz": "bozor qoidalariga mos kelmadi",
            "ru": "не соответствует правилам рынка",
            "en": "it does not follow the market rules",
        },
        "market_approved": {
            "uz": "✅ «{title}» bozorga chiqdi! Endi uni hamma ko'ra oladi.",
            "ru": "✅ «{title}» теперь на Эко-рынке — его видят все!",
            "en": "✅ «{title}» is now in the market for everyone to see!",
        },
        "market_rejected": {
            "uz": "«{title}» bozorga chiqmadi: {reason}.{note}\n\n"
            "Tuzatib, qaytadan yuborishingiz mumkin.",
            "ru": "«{title}» не прошло проверку: {reason}.{note}\n\nИсправьте и отправьте снова.",
            "en": "«{title}» was not approved: {reason}.{note}\n\n"
            "You can fix it and send it again.",
        },
        "market_hidden": {
            "uz": "«{title}» bozordan olib tashlandi: {reason}.{note}",
            "ru": "«{title}» убрано с рынка: {reason}.{note}",
            "en": "«{title}» was taken down from the market: {reason}.{note}",
        },
        "market_new_request": {
            "uz": "🙋 {name} «{title}»ni olmoqchi. Ilovada rozilik bering yoki rad eting.",
            "ru": "🙋 {name} хочет забрать «{title}». Ответьте в приложении.",
            "en": "🙋 {name} would like «{title}». Answer in the app.",
        },
        "market_accepted": {
            "uz": "🎉 «{title}» siz uchun band qilindi! Egasi uni topshirish joyiga olib "
            "kelgach, xabar beramiz.",
            "ru": "🎉 «{title}» забронировано для тебя! Сообщим, когда вещь будет в пункте "
            "передачи.",
            "en": "🎉 «{title}» is reserved for you! We'll let you know when it's at the "
            "handover point.",
        },
        "market_bring": {
            "uz": "📦 «{title}»ni {days} kun ichida topshirish joyiga olib boring:\n"
            "{point}\nIsh vaqti: {hours}\n\nXodimga shu kodni ayting: <b>{code}</b>",
            "ru": "📦 Принеси «{title}» в пункт передачи в течение {days} дней:\n"
            "{point}\nВремя работы: {hours}\n\nСкажи сотруднику код: <b>{code}</b>",
            "en": "📦 Bring «{title}» to the handover point within {days} days:\n"
            "{point}\nOpening hours: {hours}\n\nTell the staff this code: <b>{code}</b>",
        },
        "market_ready": {
            "uz": "📦 «{title}» topshirish joyida sizni kutmoqda:\n{point}\nIsh vaqti: {hours}\n\n"
            "Xodimga shu kodni ayting: <b>{code}</b>\n{days} kun ichida olib keting.",
            "ru": "📦 «{title}» ждёт тебя в пункте передачи:\n{point}\nВремя работы: {hours}\n\n"
            "Скажи сотруднику код: <b>{code}</b>\nЗабери в течение {days} дней.",
            "en": "📦 «{title}» is waiting for you at the handover point:\n{point}\n"
            "Opening hours: {hours}\n\nTell the staff this code: <b>{code}</b>\n"
            "Collect it within {days} days.",
        },
        "market_received": {
            "uz": "👍 «{title}» topshirish joyida qabul qilindi. Rahmat!",
            "ru": "👍 «{title}» принято в пункте передачи. Спасибо!",
            "en": "👍 «{title}» was received at the handover point. Thank you!",
        },
        "market_given": {
            "uz": "💚 «{title}» yangi egasiga topshirildi. Buyum ikkinchi hayot topdi — rahmat!",
            "ru": "💚 «{title}» передано новому владельцу. У вещи вторая жизнь — спасибо!",
            "en": "💚 «{title}» went to its new owner. It has a second life now — thank you!",
        },
        "market_declined": {
            "uz": "«{title}» boshqa bolaga beriladigan bo'ldi. Bozorda yana qiziq narsalar ko'p!",
            "ru": "«{title}» достанется другому. На рынке есть и другие интересные вещи!",
            "en": "«{title}» is going to someone else. There's plenty more in the market!",
        },
        "market_withdrawn": {
            "uz": "«{title}» endi berilmaydi.",
            "ru": "«{title}» больше не отдаётся.",
            "en": "«{title}» is no longer being given away.",
        },
        "market_cancelled": {
            "uz": "«{title}» bo'yicha kelishuv bekor qilindi.",
            "ru": "Договорённость о «{title}» отменена.",
            "en": "The handover of «{title}» was cancelled.",
        },
        "market_requester_left": {
            "uz": "«{title}»ni olmoqchi bo'lgan bola fikridan qaytdi. Buyum yana bozorda.",
            "ru": "Тот, кто хотел забрать «{title}», передумал. Вещь снова на рынке.",
            "en": "The person who wanted «{title}» changed their mind. It's back in the market.",
        },
        "market_expired": {
            "uz": "⏰ «{title}» belgilangan muddatda topshirish joyiga keltirilmadi, "
            "kelishuv bekor qilindi.",
            "ru": "⏰ «{title}» не принесли в пункт передачи вовремя, договорённость отменена.",
            "en": "⏰ «{title}» was not brought to the handover point in time; "
            "the handover was cancelled.",
        },
        "market_not_collected": {
            "uz": "⏰ «{title}» topshirish joyidan o'z vaqtida olib ketilmadi, bron bekor qilindi.",
            "ru": "⏰ «{title}» не забрали из пункта передачи вовремя, бронь отменена.",
            "en": "⏰ «{title}» was not collected in time; the reservation was cancelled.",
        },
    }
)


def t(key: str, lang: str, **values: object) -> str:
    texts = BOT_TEXTS[key]
    text = texts.get(lang) or texts[DEFAULT_LANGUAGE]
    return text.format(**values) if values else text
