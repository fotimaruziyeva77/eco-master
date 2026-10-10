"""Version 1 content against TZ 9.1 (volume) and 9.2 (templates), demo sets included."""

from collections import Counter

import pytest
from sqlalchemy import select

from app.admin.content import CONTENT_TYPES, Ctx, issues_for, read_values
from app.models import (
    ContentStatus,
    DailyTask,
    GameItem,
    KnowledgeCard,
    Project,
    Question,
    Tip,
)
from app.seed import seed_badges, seed_categories, seed_demo, seed_v1_content
from app.seed_data import CATEGORIES, DEMO_CARDS, DEMO_DAILY_TASKS, DEMO_PROJECTS, DEMO_TIPS
from app.seed_data_games import DEMO_GAME_ITEMS, DEMO_QUESTIONS
from app.seed_data_lessons import DEMO_LESSONS
from app.seed_data_v1 import (
    V1_CARDS,
    V1_DAILY_TASKS,
    V1_GAME_ITEMS,
    V1_PROJECTS,
    V1_QUESTIONS,
    V1_TIPS,
)

LANGS = ("uz", "ru", "en")
PROJECTS = DEMO_PROJECTS + V1_PROJECTS
QUESTIONS = DEMO_QUESTIONS + V1_QUESTIONS
GAME_ITEMS = DEMO_GAME_ITEMS + V1_GAME_ITEMS
TASKS = DEMO_DAILY_TASKS + V1_DAILY_TASKS
TIPS = DEMO_TIPS + V1_TIPS
CARDS = DEMO_CARDS + V1_CARDS
CATEGORY = {c["code"]: c for c in CATEGORIES}


def filled(value: dict) -> bool:
    return set(value) == set(LANGS) and all(value[lang] for lang in LANGS)


def test_minimal_launch_set():
    # TZ 9.1: 8 videos, 60 questions, 40 game items, 30 tasks, 30 tips, 3 lessons, 3–4 cards.
    assert len(PROJECTS) >= 8
    assert len(QUESTIONS) >= 60
    assert len(GAME_ITEMS) >= 40
    assert len(TASKS) == 30
    assert len(TIPS) == 30
    assert len(DEMO_LESSONS) == 3
    assert 3 <= len(CARDS) <= 4


def test_everything_in_three_languages():
    for q in QUESTIONS:
        assert filled(q["text"]) and filled(q["options"]) and filled(q["explanation"]), q
    for i in GAME_ITEMS:
        assert filled(i["name"]) and filled(i["explanation"]), i
    for text in TASKS + TIPS:
        assert filled(text), text
    for p in PROJECTS:
        for field in ("title", "materials", "steps"):
            assert filled(p[field]), (p["slug"], field)
    for c in CARDS:
        assert filled(c["title"])
        for lang in LANGS:
            parts = c["sections"][lang]
            assert set(parts) == {"problem", "cause", "effect", "solution", "action"}, c["slug"]
            assert all(parts.values()), (c["slug"], lang)


@pytest.mark.parametrize("q", QUESTIONS, ids=lambda q: q["text"]["en"][:40])
def test_question_template(q):
    # TZ 9.2: question up to 150, option up to 60, explanation up to 250 characters.
    counts = {len(q["options"][lang]) for lang in LANGS}
    assert len(counts) == 1 and 2 <= counts.pop() <= 4
    assert 0 <= q["correct_index"] < len(q["options"]["uz"])
    for lang in LANGS:
        assert len(q["text"][lang]) <= 150
        assert all(len(o) <= 60 for o in q["options"][lang]), q["options"][lang]
        assert len(q["explanation"][lang]) <= 250
        assert len(set(q["options"][lang])) == len(q["options"][lang])
    assert q["category"] is None or q["category"] in CATEGORY


def test_questions_cover_every_waste_type():
    per_type = Counter(q["category"] for q in QUESTIONS)
    for code in CATEGORY:
        assert per_type[code] >= 5, code
    assert per_type[None] >= 5  # general ecology
    # The right answer is not always in the same place.
    positions = Counter(q["correct_index"] for q in QUESTIONS)
    assert max(positions.values()) <= len(QUESTIONS) * 0.5


def test_game_items_evenly_over_the_bins():
    bins = Counter(i["bin"] for i in GAME_ITEMS)
    game_bins = {code for code, c in CATEGORY.items() if c["is_game_bin"]}
    assert set(bins) == game_bins
    assert max(bins.values()) - min(bins.values()) <= 1
    assert all(i["icon"] for i in GAME_ITEMS)


def test_daily_tasks_are_short():
    for text in TASKS:
        for lang in LANGS:
            assert len(text[lang]) <= 120, text[lang]


@pytest.mark.parametrize("p", PROJECTS, ids=lambda p: p["slug"])
def test_project_template(p):
    # TZ 9.2: 3–7 steps of up to 120 characters; 🟡/🔴 need a safety text (TZ 11.3).
    assert CATEGORY[p["category"]]["has_projects"]
    for lang in LANGS:
        assert 3 <= len(p["steps"][lang]) <= 7
        assert all(len(step) <= 120 for step in p["steps"][lang]), p["steps"][lang]
    assert len({len(p["steps"][lang]) for lang in LANGS}) == 1
    assert len({len(p["materials"][lang]) for lang in LANGS}) == 1
    if p["safety_level"] in ("yellow", "red"):
        assert filled(p["safety_text"])


def test_projects_cover_the_five_waste_types():
    assert {p["category"] for p in PROJECTS} == {
        code for code, c in CATEGORY.items() if c["has_projects"]
    }


def test_no_duplicates():
    def uz(items, field=None):
        return [(i[field] if field else i)["uz"].strip().lower() for i in items]

    for values in (
        uz(QUESTIONS, "text"),
        uz(GAME_ITEMS, "name"),
        uz(TASKS),
        uz(TIPS),
        [p["slug"] for p in PROJECTS],
        [c["slug"] for c in CARDS],
    ):
        assert len(values) == len(set(values)), [v for v, n in Counter(values).items() if n > 1]


# ------------------------------------------------------------------- loading


@pytest.fixture
async def seeded(session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_demo(session)
    added = await seed_v1_content(session)
    await session.commit()
    return added


async def test_seed_adds_everything_for_review_once(session, seeded):
    assert seeded == {
        "projects": len(V1_PROJECTS),
        "cards": len(V1_CARDS),
        "questions": len(V1_QUESTIONS),
        "game_items": len(V1_GAME_ITEMS),
        "daily_tasks": len(V1_DAILY_TASKS),
        "tips": len(V1_TIPS),
    }
    review = ContentStatus.REVIEW
    for model, expected in (
        (Project, len(V1_PROJECTS)),
        (Question, len(V1_QUESTIONS)),
        (GameItem, len(V1_GAME_ITEMS)),
        (DailyTask, len(V1_DAILY_TASKS)),
        (Tip, len(V1_TIPS)),
        (KnowledgeCard, len(V1_CARDS)),
    ):
        rows = (await session.scalars(select(model).where(model.status == review))).all()
        assert len(rows) == expected, model.__name__
    # Nothing new goes live before the team's review.
    assert not await seed_v1_content(session)


async def test_drafts_pass_the_publish_checks(session, seeded):
    """After review only the human step is left: projects must be tested in practice."""
    ctx = await Ctx.load(session)
    for key in ("projects", "questions", "game-items", "daily-tasks", "tips", "cards"):
        ctype = CONTENT_TYPES[key]
        rows = (
            await session.scalars(
                select(ctype.model).where(ctype.model.status == ContentStatus.REVIEW)
            )
        ).all()
        assert rows, key
        for row in rows:
            errors = [
                i.message
                for i in issues_for(ctype, read_values(ctype, row, ctx), ctx)
                if i.level == "error"
            ]
            if key == "projects":
                assert errors == [
                    "Loyiha amalda sinab ko'rilmagan: kim va qachon sinaganini yozing"
                ], row.slug
            else:
                assert errors == [], (key, row.id, errors)
