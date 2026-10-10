"""Nickname rules (TZ 8.1): 3–20 characters, Latin or Cyrillic letters, digits and "_",
unique regardless of case, no profanity or reserved names."""

import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BannedWord, User, WordKind

MIN_LENGTH, MAX_LENGTH = 3, 20

# One script per nickname: mixing scripts allows look-alike tricks
# such as a Cyrillic "а" inside "admin".
LATIN = re.compile(r"[A-Za-z0-9_]+")
CYRILLIC = re.compile(r"[А-Яа-яЁёЎўҚқҒғҲҳ0-9_]+")
LETTER = re.compile(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ]")

LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"})
CYRILLIC_LEET = str.maketrans({"0": "о", "3": "з", "6": "б"})


class NicknameError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def check_format(raw: str) -> str:
    nickname = raw.strip()
    if not MIN_LENGTH <= len(nickname) <= MAX_LENGTH:
        raise NicknameError("nickname_length")
    if not (LATIN.fullmatch(nickname) or CYRILLIC.fullmatch(nickname)):
        raise NicknameError("nickname_chars")
    if not LETTER.search(nickname):
        raise NicknameError("nickname_chars")
    return nickname


def simplify(text: str) -> str:
    return text.lower().replace("_", "")


def undo_leet(text: str) -> str:
    """Undo common digit-for-letter swaps ("sh1t" -> "shit")."""
    table = CYRILLIC_LEET if re.search("[а-яёўқғҳ]", text) else LEET
    return text.translate(table)


def is_banned(nickname: str, words: list[tuple[str, WordKind]]) -> bool:
    value = simplify(nickname)
    deleeted = undo_leet(value)
    core = value.strip("0123456789")  # "admin2024" still counts as "admin"
    for word, kind in words:
        banned = simplify(word)
        if kind is WordKind.PROFANITY and (banned in value or banned in deleeted):
            return True
        # Reserved names only match at the edges, so "badminton" stays allowed.
        if kind is WordKind.RESERVED and (core.startswith(banned) or core.endswith(banned)):
            return True
    return False


async def validate_nickname(
    session: AsyncSession, raw: str, *, exclude_user_id: int | None = None
) -> str:
    """Return the cleaned nickname or raise NicknameError with a code the UI can translate."""
    nickname = check_format(raw)
    words = (await session.execute(select(BannedWord.word, BannedWord.kind))).all()
    if is_banned(nickname, [(w, k) for w, k in words]):
        raise NicknameError("nickname_forbidden")

    query = select(User.id).where(func.lower(User.nickname) == nickname.lower())
    if exclude_user_id is not None:
        query = query.where(User.id != exclude_user_id)
    if await session.scalar(query) is not None:
        raise NicknameError("nickname_taken")
    return nickname
