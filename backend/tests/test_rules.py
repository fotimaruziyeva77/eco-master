from datetime import UTC, datetime

import pytest

from app.levels import level_for
from app.models import WordKind
from app.nickname import NicknameError, check_format, is_banned
from app.timeutil import local_today

WORDS = [
    ("admin", WordKind.RESERVED),
    ("ekoustoz", WordKind.RESERVED),
    ("админ", WordKind.RESERVED),
    ("fuck", WordKind.PROFANITY),
    ("shit", WordKind.PROFANITY),
    ("сука", WordKind.PROFANITY),
]


@pytest.mark.parametrize("nickname", ["Eco_Boy", "anvar2012", "Ойбек", "Ўктам_7", "abc"])
def test_valid_nicknames(nickname):
    assert check_format(f"  {nickname} ") == nickname


@pytest.mark.parametrize(
    ("nickname", "code"),
    [
        ("ab", "nickname_length"),
        ("a" * 21, "nickname_length"),
        ("eco boy", "nickname_chars"),
        ("eco-boy", "nickname_chars"),
        ("Ali😀", "nickname_chars"),
        ("Aлишер", "nickname_chars"),  # Latin "A" + Cyrillic: mixed scripts
        ("12345", "nickname_chars"),  # needs at least one letter
        ("___", "nickname_chars"),
    ],
)
def test_invalid_nicknames(nickname, code):
    with pytest.raises(NicknameError) as exc:
        check_format(nickname)
    assert exc.value.code == code


@pytest.mark.parametrize(
    "nickname",
    [
        "admin",
        "Admin_2024",
        "the_admin",
        "ekoustoz_uz",
        "f_u_c_k",
        "sh1tty",
        "xFUCKx",
        "Сука99",
        "админ1",
    ],
)
def test_banned_nicknames(nickname):
    assert is_banned(nickname, WORDS)


@pytest.mark.parametrize("nickname", ["badminton", "Ecolover", "Dilnoza", "Ойбек"])
def test_allowed_nicknames(nickname):
    assert not is_banned(nickname, WORDS)


@pytest.mark.parametrize(
    ("points", "code", "next_min"),
    [
        (0, "seed", 100),
        (99, "seed", 100),
        (100, "beginner", 500),
        (499, "beginner", 500),
        (500, "young_ecologist", 1000),
        (1000, "helper", 2500),
        (2500, "ekoustoz", None),
        (99999, "ekoustoz", None),
    ],
)
def test_levels(points, code, next_min):
    level = level_for(points)
    assert level.code == code
    assert level.next_min_points == next_min


def test_tashkent_day_boundary():
    # Tashkent is UTC+5: 18:59:59 UTC is still 23:59:59 the same day there.
    assert local_today(datetime(2026, 10, 10, 18, 59, 59, tzinfo=UTC)).isoformat() == "2026-10-10"
    assert local_today(datetime(2026, 10, 10, 19, 0, 0, tzinfo=UTC)).isoformat() == "2026-10-11"
