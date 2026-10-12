"""Avatars: an animal picture instead of a photo (no photos are collected, TZ 11.2).

Everyone starts with an animal the Mini App picks from their id (frontend Avatar component).
The twelve pictures of that set are free; more unlock as the level grows, so a new level brings
something to show in the rating, the league and the class.
"""

from app.levels import LEVELS, level_for

# Picture -> level code that unlocks it. Plain emoji without variation selectors.
AVATARS: dict[str, str] = {
    **dict.fromkeys(
        ("🦊", "🐼", "🐢", "🦉", "🐝", "🦋", "🐞", "🐬", "🦔", "🐸", "🐨", "🦁"), "seed"
    ),
    **dict.fromkeys(("🐧", "🐰", "🐱", "🐶"), "beginner"),
    **dict.fromkeys(("🦜", "🐳", "🦒", "🐘"), "young_ecologist"),
    **dict.fromkeys(("🦄", "🐙", "🦩", "🦚"), "helper"),
    **dict.fromkeys(("🐉", "🦕", "🦖", "🦅"), "ekoustoz"),
}

_LEVEL_RANK = {code: i for i, (_, code) in enumerate(LEVELS)}


def unlocked(avatar: str, points: int) -> bool:
    """Whether a user with these points may use the picture."""
    needed = AVATARS.get(avatar)
    if needed is None:
        return False
    return _LEVEL_RANK[level_for(points).code] >= _LEVEL_RANK[needed]
