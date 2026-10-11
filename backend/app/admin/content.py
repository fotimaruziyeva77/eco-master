"""Content types of the admin panel (TZ 8.12): fields, validation and publish checks.

Each type is described once, here. The admin UI builds its forms from these field specs,
so adding a field needs no frontend change. Multilingual values travel as
{"uz": ..., "ru": ..., "en": ...}; nested JSON (lesson body, card sections) is split into one
field per part and put back together on save.
"""

import copy
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any, Literal

from sqlalchemy import Enum, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Category,
    DailyTask,
    GameItem,
    KnowledgeCard,
    PickupPoint,
    Project,
    Question,
    SafetyLevel,
    TeacherLesson,
    Tip,
)
from app.timeutil import TASHKENT

LANGS = ("uz", "ru", "en")
LANG_NAMES = {"uz": "o'zbek", "ru": "rus", "en": "ingliz"}

Kind = Literal[
    "text",
    "textarea",
    "int",
    "bool",
    "date",
    "url",
    "video",
    "image",
    "item_image",
    "emoji",
    "color",
    "select",
    "category",
    "i18n_text",
    "i18n_textarea",
    "i18n_list",
    "i18n_plan",
]
I18N_KINDS = {"i18n_text", "i18n_textarea", "i18n_list", "i18n_plan"}

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
# Files uploaded in the admin panel (app.content_media): /media/i/<hash>.webp, /media/v/<hash>.mp4.
MEDIA_FILE = re.compile(r"/media/[iv]/[0-9a-f]{24}\.(?:webp|mp4)")
COLOR = re.compile(r"#[0-9a-fA-F]{6}")
MAX_LIST_ITEMS = 30
MAX_PLAN_STEPS = 12


@dataclass(frozen=True)
class Field:
    name: str
    label: str
    kind: Kind
    column: str | None = None  # model attribute, if it differs from the name
    nested: str | None = None  # key inside a per-language JSON column
    required: bool = False  # must be filled (in every language) to publish
    nullable: bool = True  # False: needed even in a draft (NOT NULL column)
    options: tuple[tuple[str, str], ...] = ()
    category_filter: str | None = None  # Category flag that the choices must have
    min: int | None = None
    max: int | None = None
    max_length: int = 2000
    offset: int = 0  # shown value = stored value + offset (1-based answer numbers)
    help: str | None = None
    fixed: bool = False  # slug/code: links depend on it, so it is set once

    @property
    def attr(self) -> str:
        return self.column or self.name


@dataclass
class Issue:
    level: Literal["error", "warning"]
    message: str
    field: str | None = None
    lang: str | None = None


class ContentInvalid(Exception):
    """Values that can not be saved at all, per field."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("invalid content")
        self.errors = errors


@dataclass
class Ctx:
    """Data that values refer to, loaded once per request."""

    categories: list[Category]

    @classmethod
    async def load(cls, session: AsyncSession) -> "Ctx":
        rows = await session.scalars(select(Category).order_by(Category.sort_order, Category.id))
        return cls(list(rows.all()))

    def code_of(self, category_id: int | None) -> str | None:
        return next((c.code for c in self.categories if c.id == category_id), None)

    def by_code(self, code: str) -> Category | None:
        return next((c for c in self.categories if c.code == code), None)

    def name_of(self, code: str | None) -> str:
        category = self.by_code(code) if code else None
        return category.name.get("uz", category.code) if category else ""


@dataclass
class ContentType:
    key: str
    title: str
    model: type
    fields: tuple[Field, ...]
    title_field: str
    preview: str
    has_status: bool = True
    deletable: bool = True
    checks: Callable[[dict, Ctx], list[Issue]] = lambda values, ctx: []
    subtitle: Callable[[dict, Ctx], str] = lambda values, ctx: ""
    search_columns: tuple[str, ...] = ()
    order_by: tuple[str, ...] = ("sort_order", "id")
    defaults: dict[str, Any] = field(default_factory=dict)

    def field(self, name: str) -> Field:
        return next(f for f in self.fields if f.name == name)

    def row_title(self, values: dict[str, Any]) -> str:
        title = values.get(self.title_field) or {}
        return title.get("uz") or next((t for t in title.values() if t), "") or "(nomsiz)"


# ------------------------------------------------------------------ cleaning


def _blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return not value
    return False


def _text(value: Any, f: Field) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("matn bo'lishi kerak")
    value = value.strip()
    if len(value) > f.max_length:
        raise ValueError(f"{f.max_length} belgidan oshmasin")
    return value


def _i18n(value: Any, f: Field, item: Callable[[Any], Any]) -> dict[str, Any]:
    if value is None:
        value = {}
    if not isinstance(value, dict) or set(value) - set(LANGS):
        raise ValueError("uz/ru/en qiymatlari kerak")
    return {lang: item(value.get(lang)) for lang in LANGS}


def _list(value: Any, f: Field) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > MAX_LIST_ITEMS:
        raise ValueError(f"ro'yxat ({MAX_LIST_ITEMS} tadan oshmasin)")
    items = [_text(v, f) for v in value]
    return [v for v in items if v]


def _plan(value: Any, f: Field) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > MAX_PLAN_STEPS:
        raise ValueError(f"reja ({MAX_PLAN_STEPS} bosqichdan oshmasin)")
    steps = []
    for raw in value:
        if not isinstance(raw, dict):
            raise ValueError("reja bosqichi noto'g'ri")
        title = _text(raw.get("title"), Field("", "", "text", max_length=120))
        text = _text(raw.get("text"), f)
        minutes = raw.get("minutes")
        if not title and not text:
            continue
        if not isinstance(minutes, int) or isinstance(minutes, bool) or not 1 <= minutes <= 90:
            raise ValueError("har bosqichga 1–90 daqiqa yozing")
        steps.append({"minutes": minutes, "title": title, "text": text})
    return steps


def clean(f: Field, value: Any, ctx: Ctx) -> Any:
    """Normalised value of one field, or ValueError with a message for the editor."""
    kind = f.kind
    if kind == "i18n_text" or kind == "i18n_textarea":
        return _i18n(value, f, lambda v: _text(v, f))
    if kind == "i18n_list":
        return _i18n(value, f, lambda v: _list(v, f))
    if kind == "i18n_plan":
        return _i18n(value, f, lambda v: _plan(v, f))
    if _blank(value):
        if not f.nullable:
            raise ValueError("to'ldirilishi shart")
        return None
    if kind in ("text", "textarea"):
        return _text(value, f) or None
    if kind == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("butun son kiriting")
        if f.min is not None and value < f.min or f.max is not None and value > f.max:
            raise ValueError(f"{f.min}–{f.max} oralig'ida bo'lsin")
        return value
    if kind == "bool":
        if not isinstance(value, bool):
            raise ValueError("ha/yo'q")
        return value
    if kind == "date":
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError("sana YYYY-MM-DD ko'rinishida") from None
    if kind == "url":
        value = _text(value, f)
        if not value.startswith("https://") or len(value) > 512 or " " in value:
            raise ValueError("https:// bilan boshlanadigan havola kiriting")
        return value
    if kind in ("video", "image", "item_image"):
        value = _text(value, f)
        suffix = ".mp4" if kind == "video" else ".webp"
        if MEDIA_FILE.fullmatch(value) and value.endswith(suffix):
            return value
        # Links to other sites from before uploads existed keep working until replaced.
        if value.startswith("https://") and len(value) <= 512 and " " not in value:
            return value
        raise ValueError("faylni yuklang")
    if kind == "emoji":
        value = _text(value, f)
        if len(value) > 16:
            raise ValueError("bitta emoji")
        return value
    if kind == "color":
        value = _text(value, f)
        if not COLOR.fullmatch(value):
            raise ValueError("#RRGGBB ko'rinishidagi rang")
        return value.upper()
    if kind == "select":
        if value not in {v for v, _ in f.options}:
            raise ValueError("ro'yxatdan tanlang")
        return value
    if kind == "category":
        category = ctx.by_code(value) if isinstance(value, str) else None
        if category is None or f.category_filter and not getattr(category, f.category_filter):
            raise ValueError("chiqindi turini ro'yxatdan tanlang")
        return value
    raise ValueError("noma'lum maydon")


def clean_all(ctype: ContentType, raw: dict[str, Any], ctx: Ctx) -> dict[str, Any]:
    values: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for f in ctype.fields:
        try:
            values[f.name] = clean(f, raw.get(f.name), ctx)
        except ValueError as exc:
            errors[f.name] = str(exc)
    slug = values.get("slug")
    if "slug" in values and "slug" not in errors:
        if not slug or not SLUG.fullmatch(slug) or not 3 <= len(slug) <= 64:
            errors["slug"] = "3–64 ta kichik lotin harfi, raqam va «-»"
    if errors:
        raise ContentInvalid(errors)
    return values


# --------------------------------------------------------------- ORM mapping


def _from_db(f: Field, raw: Any, ctx: Ctx) -> Any:
    if f.kind == "category":
        return ctx.code_of(raw)
    if f.kind == "date":
        if isinstance(raw, datetime):
            return raw.astimezone(TASHKENT).date().isoformat()
        return raw.isoformat() if raw else None
    if f.kind == "select" and raw is not None:
        return getattr(raw, "value", raw)
    if f.kind == "int" and raw is not None:
        return raw + f.offset
    return raw


def read_values(ctype: ContentType, obj: Any, ctx: Ctx) -> dict[str, Any]:
    """The item as the admin form shows it."""
    values: dict[str, Any] = {}
    for f in ctype.fields:
        raw = getattr(obj, f.attr)
        if f.nested:
            raw = {lang: ((raw or {}).get(lang) or {}).get(f.nested) for lang in LANGS}
        if f.kind in I18N_KINDS:
            empty: Any = "" if f.kind in ("i18n_text", "i18n_textarea") else []
            source = raw or {}
            values[f.name] = {lang: source.get(lang) or empty for lang in LANGS}
        else:
            values[f.name] = _from_db(f, raw, ctx)
    return values


def write_values(ctype: ContentType, obj: Any, values: dict[str, Any], ctx: Ctx) -> None:
    """Put cleaned values on the model; nested parts are merged into their JSON column."""
    nested: dict[str, dict[str, dict[str, Any]]] = {}
    for f in ctype.fields:
        value = values[f.name]
        if f.nested:
            column = nested.setdefault(f.attr, copy.deepcopy(getattr(obj, f.attr) or {}))
            for lang in LANGS:
                column.setdefault(lang, {})[f.nested] = value[lang]
            continue
        column_type = getattr(type(obj), f.attr).type
        if f.kind == "category":
            category = ctx.by_code(value) if value else None
            value = category.id if category else None
        elif f.kind == "date" and value is not None and column_type.python_type is datetime:
            # A day typed in the form, kept as noon in Tashkent so it never shifts a day.
            value = datetime.combine(value, time(12), TASHKENT)
        elif f.kind == "int" and value is not None:
            value -= f.offset
        elif f.kind == "select" and value is not None and isinstance(column_type, Enum):
            value = column_type.enum_class(value)
        setattr(obj, f.attr, value)
    for column, data in nested.items():
        setattr(obj, column, data)  # a new object, so the change is saved


# --------------------------------------------------------------- publish checks


def _filled(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value)
    return not _blank(value)


def completeness(ctype: ContentType, values: dict[str, Any]) -> list[Issue]:
    """Required fields, and every language of them (TZ 8.12, QM-14)."""
    issues = []
    for f in ctype.fields:
        if not f.required:
            continue
        value = values.get(f.name)
        if f.kind in I18N_KINDS:
            missing = [lang for lang in LANGS if not _filled((value or {}).get(lang))]
            if len(missing) == len(LANGS):
                issues.append(Issue("error", f"«{f.label}» to'ldirilmagan", f.name))
            else:
                issues += [
                    Issue("error", f"«{f.label}» {LANG_NAMES[lang]} tilida yo'q", f.name, lang)
                    for lang in missing
                ]
        elif not _filled(value):
            issues.append(Issue("error", f"«{f.label}» to'ldirilmagan", f.name))
    return issues


def issues_for(ctype: ContentType, values: dict[str, Any], ctx: Ctx) -> list[Issue]:
    return completeness(ctype, values) + ctype.checks(values, ctx)


def _counts_differ(value: dict[str, list]) -> bool:
    counts = {len(value.get(lang) or []) for lang in LANGS if value.get(lang)}
    return len(counts) > 1


def project_checks(values: dict, ctx: Ctx) -> list[Issue]:
    issues = []
    if values.get("safety_level") in (SafetyLevel.YELLOW, SafetyLevel.RED):
        safety = values.get("safety_text") or {}
        missing = [lang for lang in LANGS if not _filled(safety.get(lang))]
        if missing:
            langs = ", ".join(LANG_NAMES[lang] for lang in missing)
            issues.append(
                Issue(
                    "error",
                    f"🟡/🔴 loyihada xavfsizlik matni uch tilda bo'lishi shart ({langs} yo'q)",
                    "safety_text",
                )
            )
    if not values.get("tested_by") or not values.get("tested_at"):
        issues.append(
            Issue(
                "error",
                "Loyiha amalda sinab ko'rilmagan: kim va qachon sinaganini yozing",
                "tested_by",
            )
        )
    if not values.get("video_url"):
        issues.append(
            Issue("warning", "Video yuklanmagan: ilovada «Video tez orada» ko'rinadi", "video_url")
        )
    for name, label in (("materials", "Materiallar"), ("steps", "Qadamlar")):
        if _counts_differ(values.get(name) or {}):
            issues.append(Issue("warning", f"«{label}» soni tillarda har xil", name))
    return issues


def question_checks(values: dict, ctx: Ctx) -> list[Issue]:
    options = values.get("options") or {}
    counts = {lang: len(options.get(lang) or []) for lang in LANGS}
    issues = []
    if any(c and not 2 <= c <= 4 for c in counts.values()):
        issues.append(Issue("error", "Har bir tilda 2–4 ta javob varianti bo'lsin", "options"))
    if len({c for c in counts.values() if c}) > 1:
        issues.append(
            Issue("error", "Javob variantlari soni tillarda bir xil bo'lishi shart", "options")
        )
    answer = values.get("correct_answer")
    filled = [c for c in counts.values() if c]
    if answer is not None and filled and answer > min(filled):
        issues.append(
            Issue("error", f"To'g'ri javob raqami {min(filled)} dan katta", "correct_answer")
        )
    return issues


def lesson_checks(values: dict, ctx: Ctx) -> list[Issue]:
    issues = []
    plan = values.get("plan") or {}
    for lang in LANGS:
        minutes = sum(step["minutes"] for step in plan.get(lang) or [])
        if minutes and minutes != 45:
            issues.append(
                Issue(
                    "warning",
                    f"{LANG_NAMES[lang].capitalize()} rejasi {minutes} daqiqa (45 bo'lishi kerak)",
                    "plan",
                    lang,
                )
            )
    for name, label in (("plan", "Reja bosqichlari"), ("materials", "Materiallar")):
        if _counts_differ(values.get(name) or {}):
            issues.append(Issue("warning", f"«{label}» soni tillarda har xil", name))
    return issues


# ------------------------------------------------------------------ registry

DIFFICULTY = (("easy", "Oson"), ("medium", "O'rtacha"), ("hard", "Qiyin"))
SAFETY = (
    ("green", "🟢 Bolalar mustaqil qila oladi"),
    ("yellow", "🟡 Kattalar nazorati bilan"),
    ("red", "🔴 Faqat kattalar"),
)
SLUG_HELP = (
    "Havolada ishlatiladi: kichik lotin harflari, raqamlar va «-». Nashrdan keyin o'zgarmaydi."
)
SORT = Field("sort_order", "Tartib raqami", "int", nullable=False, min=0, max=10_000)


CONTENT_TYPES: dict[str, ContentType] = {
    t.key: t
    for t in (
        ContentType(
            key="projects",
            title="Loyihalar (video darslar)",
            model=Project,
            preview="project",
            title_field="title",
            search_columns=("title", "slug"),
            checks=project_checks,
            subtitle=lambda v, ctx: f"{ctx.name_of(v.get('category'))} · {v.get('slug') or ''}",
            defaults={"difficulty": "easy", "safety_level": "green", "duration_min": 30},
            fields=(
                Field(
                    "slug",
                    "Havola nomi (slug)",
                    "text",
                    nullable=False,
                    fixed=True,
                    max_length=64,
                    help=SLUG_HELP,
                ),
                Field(
                    "category",
                    "Chiqindi turi",
                    "category",
                    column="category_id",
                    nullable=False,
                    category_filter="has_projects",
                ),
                Field("title", "Nomi", "i18n_text", required=True, max_length=120),
                Field("difficulty", "Qiyinlik", "select", nullable=False, options=DIFFICULTY),
                Field(
                    "safety_level", "Xavfsizlik darajasi", "select", nullable=False, options=SAFETY
                ),
                Field(
                    "duration_min", "Davomiyligi (daqiqa)", "int", nullable=False, min=1, max=600
                ),
                Field("materials", "Materiallar", "i18n_list", required=True, max_length=200),
                Field("steps", "Qadamlar", "i18n_list", required=True, max_length=600),
                Field(
                    "safety_text",
                    "Xavfsizlik matni",
                    "i18n_textarea",
                    max_length=600,
                    help="🟡 va 🔴 loyihalarda majburiy.",
                ),
                Field(
                    "video_url",
                    "Video",
                    "video",
                    help="MP4 yoki MOV, 3 daqiqagacha, 500 MB gacha. Server o'zi siqadi.",
                ),
                Field(
                    "poster_url",
                    "Muqova rasmi",
                    "image",
                    help="Video yuklansa, muqova undan avtomatik olinadi.",
                ),
                Field(
                    "tested_by",
                    "Kim sinab ko'rdi",
                    "text",
                    max_length=128,
                    help="Loyihani amalda sinagan jamoa a'zosi (TZ 9.3).",
                ),
                Field("tested_at", "Qachon sinab ko'rildi", "date"),
                SORT,
            ),
        ),
        ContentType(
            key="questions",
            title="Viktorina savollari",
            model=Question,
            preview="question",
            title_field="text",
            search_columns=("text",),
            checks=question_checks,
            subtitle=lambda v, ctx: ctx.name_of(v.get("category")) or "Umumiy ekologiya",
            defaults={"correct_answer": 1},
            fields=(
                Field(
                    "category",
                    "Mavzu (chiqindi turi)",
                    "category",
                    column="category_id",
                    help="Bo'sh qoldirilsa — umumiy ekologiya savoli.",
                ),
                Field("text", "Savol", "i18n_textarea", required=True, max_length=300),
                Field(
                    "options",
                    "Javob variantlari",
                    "i18n_list",
                    required=True,
                    max_length=150,
                    help="2–4 ta, har tilda bir xil tartibda.",
                ),
                Field(
                    "correct_answer",
                    "To'g'ri javob (nechanchi variant)",
                    "int",
                    column="correct_index",
                    nullable=False,
                    min=1,
                    max=4,
                    offset=1,
                ),
                Field(
                    "explanation", "Tushuntirish", "i18n_textarea", required=True, max_length=400
                ),
                Field("image_url", "Rasm", "image", help="Savol ustida ko'rinadi (ixtiyoriy)."),
                SORT,
            ),
        ),
        ContentType(
            key="game-items",
            title="O'yin buyumlari",
            model=GameItem,
            preview="game_item",
            title_field="name",
            search_columns=("name",),
            subtitle=lambda v, ctx: f"{ctx.name_of(v.get('bin'))} qutisi",
            fields=(
                Field("name", "Nomi", "i18n_text", required=True, max_length=80),
                Field("icon", "Emoji", "emoji", help="Rasm bo'lmasa shu ko'rinadi."),
                Field(
                    "image_url",
                    "Rasm",
                    "item_image",
                    help="Kvadrat, fon shaffof (PNG yoki WebP). Rasm bo'lmasa emoji ko'rinadi.",
                ),
                Field(
                    "bin",
                    "To'g'ri quti",
                    "category",
                    column="correct_category_id",
                    nullable=False,
                    category_filter="is_game_bin",
                ),
                Field(
                    "explanation", "Tushuntirish", "i18n_textarea", required=True, max_length=300
                ),
                SORT,
            ),
        ),
        ContentType(
            key="daily-tasks",
            title="Kunlik topshiriqlar",
            model=DailyTask,
            preview="daily_task",
            title_field="text",
            search_columns=("text",),
            subtitle=lambda v, ctx: f"{v.get('points') or 0} ball",
            defaults={"points": 20},
            fields=(
                Field("text", "Topshiriq", "i18n_textarea", required=True, max_length=300),
                Field("points", "Ball", "int", nullable=False, min=5, max=100),
                SORT,
            ),
        ),
        ContentType(
            key="tips",
            title="Kunlik maslahatlar",
            model=Tip,
            preview="tip",
            title_field="text",
            search_columns=("text",),
            fields=(
                Field("text", "Maslahat", "i18n_textarea", required=True, max_length=400),
                SORT,
            ),
        ),
        ContentType(
            key="cards",
            title="Bilim kartochkalari",
            model=KnowledgeCard,
            preview="card",
            title_field="title",
            search_columns=("title", "slug"),
            subtitle=lambda v, ctx: v.get("slug") or "",
            fields=(
                Field(
                    "slug",
                    "Havola nomi (slug)",
                    "text",
                    nullable=False,
                    fixed=True,
                    max_length=64,
                    help=SLUG_HELP,
                ),
                Field("title", "Sarlavha", "i18n_text", required=True, max_length=120),
                *(
                    Field(
                        key,
                        label,
                        "i18n_textarea",
                        column="sections",
                        nested=key,
                        required=True,
                        max_length=800,
                    )
                    for key, label in (
                        ("problem", "Muammo"),
                        ("cause", "Sabab"),
                        ("effect", "Oqibat"),
                        ("solution", "Yechim"),
                        ("action", "Men nima qila olaman?"),
                    )
                ),
                Field("image_url", "Rasm", "image", help="Kartochka tepasida ko'rinadi."),
                SORT,
            ),
        ),
        ContentType(
            key="lessons",
            title="O'qituvchi darslari",
            model=TeacherLesson,
            preview="lesson",
            title_field="title",
            search_columns=("title", "slug"),
            checks=lesson_checks,
            subtitle=lambda v, ctx: f"{v.get('grade') or ''}-sinflar · {v.get('slug') or ''}",
            defaults={"grade": "5–7"},
            fields=(
                Field(
                    "slug",
                    "Havola nomi (slug)",
                    "text",
                    nullable=False,
                    fixed=True,
                    max_length=64,
                    help=SLUG_HELP,
                ),
                Field("title", "Mavzu", "i18n_text", required=True, max_length=120),
                Field("grade", "Sinf", "text", nullable=False, max_length=32, help="Masalan: 5–7"),
                Field(
                    "goal",
                    "Maqsad",
                    "i18n_textarea",
                    column="body",
                    nested="goal",
                    required=True,
                    max_length=600,
                ),
                Field(
                    "materials",
                    "Kerakli materiallar",
                    "i18n_list",
                    column="body",
                    nested="materials",
                    required=True,
                    max_length=200,
                ),
                Field(
                    "plan",
                    "45 daqiqalik reja",
                    "i18n_plan",
                    column="body",
                    nested="plan",
                    required=True,
                    max_length=800,
                    help="Kirish 5, asosiy qism 20, guruhli ish 15, yakun 5 daqiqa.",
                ),
                Field(
                    "questions",
                    "Savollar",
                    "i18n_list",
                    column="body",
                    nested="questions",
                    required=True,
                    max_length=300,
                ),
                Field(
                    "homework",
                    "Uyga vazifa",
                    "i18n_textarea",
                    column="body",
                    nested="homework",
                    required=True,
                    max_length=400,
                ),
                Field(
                    "app_task",
                    "Ilova bilan topshiriq",
                    "i18n_textarea",
                    column="body",
                    nested="app_task",
                    required=True,
                    max_length=400,
                ),
                SORT,
            ),
        ),
        ContentType(
            key="pickup-points",
            title="Topshirish joylari",
            model=PickupPoint,
            preview="pickup_point",
            title_field="name",
            search_columns=("name", "address"),
            subtitle=lambda v, ctx: (v.get("address") or {}).get("uz") or "",
            fields=(
                Field(
                    "name",
                    "Nomi",
                    "i18n_text",
                    required=True,
                    max_length=80,
                    help="Masalan: 12-maktab eko-burchagi. Kattalar navbatchilik qiladigan joy.",
                ),
                Field("address", "Manzil", "i18n_textarea", required=True, max_length=200),
                Field(
                    "hours",
                    "Ish vaqti",
                    "i18n_text",
                    required=True,
                    max_length=80,
                    help="Masalan: Dushanba–juma, 14:00–17:00",
                ),
                SORT,
            ),
        ),
        ContentType(
            key="categories",
            title="Chiqindi turlari",
            model=Category,
            preview="category",
            title_field="name",
            has_status=False,
            deletable=False,
            search_columns=("name", "code"),
            subtitle=lambda v, ctx: v.get("code") or "",
            defaults={"color": "#10B981", "icon": "♻️"},
            fields=(
                Field(
                    "code",
                    "Kod",
                    "text",
                    nullable=False,
                    fixed=True,
                    max_length=32,
                    help="Lotin harflarida, masalan: plastic. Keyin o'zgarmaydi.",
                ),
                Field("name", "Nomi", "i18n_text", required=True, max_length=60),
                Field("examples", "Misollar (o'yinda quti ostida)", "i18n_text", max_length=200),
                Field("icon", "Emoji", "emoji", nullable=False),
                Field("color", "Rang", "color", nullable=False),
                Field("has_projects", "Loyihalari bor", "bool", nullable=False),
                Field("is_game_bin", "O'yinda quti", "bool", nullable=False),
                SORT,
            ),
        ),
    )
}
