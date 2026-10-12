"""'My tree': the picture that grows with the points, for the Stories image.

The Mini App draws the same tree as SVG (frontend/src/components/treeDrawing.ts); keep the
two in step.
Coordinates are in a 200x200 box with the ground at y = 172.
"""

from dataclasses import dataclass

TREE_THRESHOLDS = (0, 100, 500, 1000, 2500)
POINTS_PER_FRUIT = 300

LEAF_DARK = "#15803d"
LEAF = "#22c55e"
LEAF_LIGHT = "#4ade80"
STEM = "#16a34a"
TRUNK = "#92582a"
GRASS = "#86d36b"
GRASS_DARK = "#65b84a"
SEED = "#a0632b"
SEED_SHINE = "#c58a4f"
FLOWER = "#f472b6"
FLOWER_MIDDLE = "#fde047"
FRUIT = "#ef4444"
FRUIT_SHINE = "#fca5a5"


@dataclass(frozen=True)
class Growth:
    stage: int
    progress: float
    fruits: int


@dataclass(frozen=True)
class Circle:
    cx: float
    cy: float
    r: float
    fill: str


@dataclass(frozen=True)
class Ellipse:
    cx: float
    cy: float
    rx: float
    ry: float
    fill: str
    rotate: float = 0


@dataclass(frozen=True)
class Poly:
    points: tuple[tuple[float, float], ...]
    fill: str


@dataclass(frozen=True)
class Line:
    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    color: str


Part = Circle | Ellipse | Poly | Line


def tree_growth(points: int) -> Growth:
    stage = max(i for i, low in enumerate(TREE_THRESHOLDS) if points >= low)
    low = TREE_THRESHOLDS[stage]
    if stage + 1 < len(TREE_THRESHOLDS):
        high = TREE_THRESHOLDS[stage + 1]
        return Growth(stage, min(1.0, max(0.0, (points - low) / (high - low))), 0)
    return Growth(stage, 1.0, min(8, 1 + (points - low) // POINTS_PER_FRUIT))


def tree_parts(growth: Growth) -> list[Part]:
    stage, p = growth.stage, growth.progress
    parts: list[Part] = [
        Ellipse(100, 176, 82, 14, GRASS_DARK),
        Ellipse(100, 173, 78, 11, GRASS),
    ]
    if stage == 0:
        parts += [Ellipse(100, 171, 12, 8, SEED), Ellipse(96, 168, 4, 2.2, SEED_SHINE, -20)]
        if p >= 0.05:
            s = 0.4 + 0.6 * p
            top = 166 - 26 * s
            parts += [
                Line(100, 166, 100, top, 4, STEM),
                Ellipse(100 - 9 * s, top - 2 * s, 10 * s, 5 * s, LEAF, -30),
                Ellipse(100 + 9 * s, top - 2 * s, 10 * s, 5 * s, LEAF_LIGHT, 30),
            ]
        return parts

    if stage == 1:
        height = 44 + 30 * p
        top = 172 - height
        parts.append(Line(100, 172, 100, top, 5, STEM))
        for at, side in ((0.55, -1), (0.4, 1), (0.25, -1))[: int(p * 4)]:
            fill = LEAF if side < 0 else LEAF_LIGHT
            parts.append(Ellipse(100 + side * 10, 172 - height * at, 11, 5.5, fill, side * 25))
        parts += [
            Ellipse(89, top - 3, 12, 6, LEAF, -30),
            Ellipse(111, top - 3, 12, 6, LEAF_LIGHT, 30),
        ]
        return parts

    if stage == 2:
        s = 0.8 + 0.2 * p
        top = 172 - 62 * s
        cy = top - 14 * s
        parts += [
            Poly(((95, 172), (105, 172), (103, top), (97, top)), TRUNK),
            Circle(100 - 16 * s, cy + 6 * s, 20 * s, LEAF_DARK),
            Circle(100 + 16 * s, cy + 6 * s, 20 * s, LEAF_DARK),
            Circle(100, cy - 4 * s, 24 * s, LEAF),
            Circle(100 - 14 * s, cy + 2 * s, 16 * s, LEAF),
            Circle(100 + 14 * s, cy + 2 * s, 16 * s, LEAF),
            Circle(100 - 8 * s, cy - 12 * s, 8 * s, LEAF_LIGHT),
        ]
        return parts

    if stage == 3:
        s = 0.85 + 0.15 * p
        top = 172 - 70 * s
        cy = top - 22 * s
        parts += [
            Poly(((91, 172), (109, 172), (105, top), (95, top)), TRUNK),
            Circle(100 - 34 * s, cy + 10 * s, 24 * s, LEAF_DARK),
            Circle(100 + 34 * s, cy + 10 * s, 24 * s, LEAF_DARK),
            Circle(100, cy + 16 * s, 28 * s, LEAF_DARK),
            Circle(100 - 22 * s, cy - 6 * s, 26 * s, LEAF),
            Circle(100 + 22 * s, cy - 6 * s, 26 * s, LEAF),
            Circle(100, cy - 18 * s, 30 * s, LEAF),
            Circle(100, cy + 6 * s, 26 * s, LEAF),
            Circle(100 - 14 * s, cy - 26 * s, 10 * s, LEAF_LIGHT),
            Circle(100 + 26 * s, cy - 14 * s, 7 * s, LEAF_LIGHT),
        ]
        flowers = ((-30, -4), (20, -26), (34, 8), (-8, 12), (-22, -30), (10, -2))
        for dx, dy in flowers[: int(p * 7)]:
            parts += [
                Circle(100 + dx * s, cy + dy * s, 4.5 * s, FLOWER),
                Circle(100 + dx * s, cy + dy * s, 1.8 * s, FLOWER_MIDDLE),
            ]
        return parts

    trunk = ((80, 172), (120, 172), (110, 160), (106, 94), (94, 94), (90, 160))
    parts += [
        Poly(trunk, TRUNK),
        Circle(58, 84, 28, LEAF_DARK),
        Circle(142, 84, 28, LEAF_DARK),
        Circle(100, 92, 32, LEAF_DARK),
        Circle(70, 52, 26, LEAF_DARK),
        Circle(130, 52, 26, LEAF_DARK),
        Circle(76, 66, 30, LEAF),
        Circle(124, 66, 30, LEAF),
        Circle(100, 44, 32, LEAF),
        Circle(100, 76, 30, LEAF),
        Circle(56, 76, 20, LEAF),
        Circle(144, 76, 20, LEAF),
        Circle(86, 34, 11, LEAF_LIGHT),
        Circle(128, 46, 8, LEAF_LIGHT),
        Circle(64, 58, 7, LEAF_LIGHT),
    ]
    apples = ((78, 60), (118, 40), (134, 74), (96, 84), (62, 84), (108, 62), (86, 40), (144, 58))
    for x, y in apples[: growth.fruits]:
        parts += [Circle(x, y, 6, FRUIT), Circle(x - 2, y - 2, 2, FRUIT_SHINE)]
    return parts
