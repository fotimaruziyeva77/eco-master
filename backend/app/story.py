"""The picture for Telegram Stories (WebApp.shareToStory): the user's tree, level and points.

Nothing personal is on it (no nickname), so one file serves everyone with the same points and
language. Files are named by a keyed hash of what is drawn, so the URLs can not be guessed or
used to make the server draw anything else, and they are removed after a few days.
"""

import contextlib
import hashlib
import hmac
import io
import math
import os
import secrets
import time
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageDraw, ImageFont

from app.config import Settings
from app.content_media import MEDIA_URL, media_folder
from app.i18n import t
from app.levels import level_for
from app.tree import Circle, Ellipse, Line, Part, Poly, tree_growth, tree_parts

WIDTH, HEIGHT = 1080, 1920
# Drawn twice as big and scaled down: Pillow's shapes have no smoothing of their own.
SCALE = 2
FOLDER = "s"
KEEP_SECONDS = 3 * 24 * 3600
VERSION = "1"

ASSETS = Path(__file__).parent / "assets"
BOLD = ASSETS / "fonts" / "Manrope-Bold.ttf"
REGULAR = ASSETS / "fonts" / "Manrope-Regular.ttf"
MARK = ASSETS / "brand" / "eco-master-mark.png"

SKY = (224, 242, 254)
MINT = (220, 252, 231)
INK = "#002117"
GREEN = "#047857"
AMBER = "#f59e0b"
GREY = "#3c4a42"

# The tree's square on the picture, and the part of the 200x200 drawing shown in it for each
# stage: a seed or a sprout is shown up close, so every picture is full.
TREE_LEFT, TREE_TOP, TREE_SIZE = 100, 430, 880
STAGE_VIEW = ((56, 112, 88), (45, 80, 110), (35, 60, 130), (10, 15, 180), (0, 0, 200))


def story_name(settings: Settings, language: str, points: int) -> str:
    key = f"{VERSION}|{language}|{points}|{settings.bot_username}".encode()
    digest = hmac.new(settings.jwt_secret.encode(), key, hashlib.sha256).hexdigest()
    return f"{digest[:24]}.jpg"


def story_url(settings: Settings, name: str) -> str:
    """Absolute https address: Telegram downloads the picture itself."""
    site = urlsplit(settings.webapp_url)
    return f"{site.scheme}://{site.netloc}{MEDIA_URL}/{FOLDER}/{name}"


def story_picture(settings: Settings, language: str, points: int) -> str:
    """Make (or reuse) the picture; returns its file name in the media folder."""
    folder = media_folder(FOLDER)
    name = story_name(settings, language, points)
    path = folder / name
    if path.exists():
        # Handed out again: it must outlive Telegram fetching it.
        with contextlib.suppress(OSError):
            os.utime(path)
    else:
        data = render(language, points, settings.bot_username)
        # Its own temporary name: a whole class may share the same picture at the same moment.
        tmp = folder / f".{name}.{secrets.token_hex(6)}.tmp"
        tmp.write_bytes(data)
        try:
            os.replace(tmp, path)
        except OSError:
            # Another request put the same picture there first (Windows will not replace a file
            # someone has open): theirs is just as good.
            tmp.unlink(missing_ok=True)
            if not path.exists():
                raise
    _forget_old(folder, keep=path)
    return name


def _forget_old(folder: Path, keep: Path) -> None:
    cutoff = time.time() - KEEP_SECONDS
    for old in folder.glob("*.jpg"):
        if old == keep:
            continue
        try:
            if old.stat().st_mtime < cutoff:
                old.unlink()
        except FileNotFoundError:
            pass


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size * SCALE)


def _centered(draw: ImageDraw.ImageDraw, y: int, text: str, font, fill: str) -> None:
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    draw.text(((WIDTH * SCALE - (right - left)) / 2, y * SCALE), text, font=font, fill=fill)


def _star(cx: float, cy: float, outer: float) -> list[tuple[float, float]]:
    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else outer * 0.45
        angle = math.pi / 2 + i * math.pi / 5
        points.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
    return points


def _ellipse_points(part: Ellipse, scale: float, dx: float, dy: float) -> list[tuple[float, float]]:
    turn = math.radians(part.rotate)
    points = []
    for i in range(48):
        a = 2 * math.pi * i / 48
        x, y = part.rx * math.cos(a), part.ry * math.sin(a)
        rx = x * math.cos(turn) - y * math.sin(turn)
        ry = x * math.sin(turn) + y * math.cos(turn)
        points.append((dx + (part.cx + rx) * scale, dy + (part.cy + ry) * scale))
    return points


def _draw_tree(draw: ImageDraw.ImageDraw, stage: int, parts: list[Part]) -> None:
    left, top, side = STAGE_VIEW[stage]
    scale = TREE_SIZE / side * SCALE
    dx, dy = TREE_LEFT * SCALE - left * scale, TREE_TOP * SCALE - top * scale
    for part in parts:
        if isinstance(part, Circle):
            x, y, r = dx + part.cx * scale, dy + part.cy * scale, part.r * scale
            draw.ellipse((x - r, y - r, x + r, y + r), fill=part.fill)
        elif isinstance(part, Ellipse):
            draw.polygon(_ellipse_points(part, scale, dx, dy), fill=part.fill)
        elif isinstance(part, Poly):
            draw.polygon([(dx + x * scale, dy + y * scale) for x, y in part.points], fill=part.fill)
        elif isinstance(part, Line):
            start = (dx + part.x1 * scale, dy + part.y1 * scale)
            end = (dx + part.x2 * scale, dy + part.y2 * scale)
            width = part.width * scale
            draw.line((start, end), fill=part.color, width=round(width))
            half = width / 2
            for x, y in (start, end):
                draw.ellipse((x - half, y - half, x + half, y + half), fill=part.color)


def render(language: str, points: int, bot_username: str = "") -> bytes:
    size = (WIDTH * SCALE, HEIGHT * SCALE)
    # Sky at the top, mint at the bottom.
    gradient = Image.linear_gradient("L").resize(size)
    image = Image.composite(Image.new("RGB", size, MINT), Image.new("RGB", size, SKY), gradient)
    draw = ImageDraw.Draw(image)

    # Sun and two clouds, clear of the words and the tree.
    s = SCALE
    draw.ellipse((780 * s, 120 * s, 1020 * s, 360 * s), fill="#fef3c7")
    for x, y in ((470, 60), (900, 640)):
        for ox, oy, r in ((0, 20, 46), (50, 0, 60), (105, 22, 44)):
            cx, cy = (x + ox) * s, (y + oy) * s
            draw.ellipse((cx - r * s, cy - r * s, cx + r * s, cy + r * s), fill="white")

    # Brand: the mark on a white disc, the name next to it.
    draw.ellipse((80 * s, 96 * s, 232 * s, 248 * s), fill="white")
    mark = Image.open(MARK).convert("RGB").resize((112 * s, 112 * s), Image.Resampling.LANCZOS)
    mask = Image.new("L", mark.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, mark.size[0], mark.size[1]), fill=255)
    image.paste(mark, (100 * s, 116 * s), mask)
    draw.text((256 * s, 128 * s), "Eco-Master", font=_font(BOLD, 64), fill=GREEN)

    _centered(draw, 300, t("story_title", language), _font(BOLD, 84), INK)
    growth = tree_growth(points)
    _draw_tree(draw, growth.stage, tree_parts(growth))

    level = level_for(points).code
    _centered(draw, 1350, t(f"level_{level}", language), _font(BOLD, 72), GREEN)

    # A star and the points under it.
    number = f"{points:,}".replace(",", " ")
    font = _font(BOLD, 110)
    left, _, right, _ = draw.textbbox((0, 0), number, font=font)
    star = 100 * s
    gap = 24 * s
    x = (WIDTH * s - (star + gap + right - left)) / 2
    draw.polygon(_star(x + star / 2, 1528 * s, star / 2), fill=AMBER)
    draw.text((x + star + gap, 1462 * s), number, font=font, fill=INK)

    footer = f"t.me/{bot_username}" if bot_username else "Eco-Master"
    _centered(draw, 1660, footer, _font(REGULAR, 46), GREY)

    out = io.BytesIO()
    image.reduce(SCALE).save(out, "JPEG", quality=88, optimize=True, progressive=True)
    return out.getvalue()
