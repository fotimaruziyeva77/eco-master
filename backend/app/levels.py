"""Levels by total points (TZ 8.6). Names are translated in the Mini App by code."""

from dataclasses import dataclass

LEVELS: tuple[tuple[int, str], ...] = (
    (0, "seed"),
    (100, "beginner"),
    (500, "young_ecologist"),
    (1000, "helper"),
    (2500, "ekoustoz"),
)


@dataclass(frozen=True)
class Level:
    code: str
    min_points: int
    next_min_points: int | None  # None on the top level


def level_for(points: int) -> Level:
    current = LEVELS[0]
    next_min = None
    for i, (threshold, code) in enumerate(LEVELS):
        if points >= threshold:
            current = (threshold, code)
            next_min = LEVELS[i + 1][0] if i + 1 < len(LEVELS) else None
    return Level(code=current[1], min_points=current[0], next_min_points=next_min)
