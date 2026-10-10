"""Load reference data (and optionally demo content): python -m app.seed [--demo]

Safe to run repeatedly: rows are matched by their natural keys and updated in place.
"""

import argparse
import asyncio

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models import (
    Badge,
    BannedWord,
    Category,
    ContentStatus,
    DailyTask,
    GameItem,
    KnowledgeCard,
    Project,
    Question,
    TeacherLesson,
    Tip,
    WordKind,
)
from app.seed_data import (
    CATEGORIES,
    DEMO_CARDS,
    DEMO_DAILY_TASKS,
    DEMO_PROJECTS,
    DEMO_TIPS,
    PROFANITY,
    RESERVED_WORDS,
)
from app.seed_data_games import BADGES, DEMO_GAME_ITEMS, DEMO_QUESTIONS
from app.seed_data_lessons import DEMO_LESSONS


async def seed_categories(session: AsyncSession) -> None:
    for order, data in enumerate(CATEGORIES, start=1):
        values = {**data, "sort_order": order}
        stmt = insert(Category).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Category.code], set_={k: v for k, v in values.items() if k != "code"}
        )
        await session.execute(stmt)


async def seed_banned_words(session: AsyncSession) -> None:
    rows = [{"word": w, "kind": WordKind.RESERVED} for w in RESERVED_WORDS] + [
        {"word": w, "kind": WordKind.PROFANITY} for w in PROFANITY
    ]
    await session.execute(insert(BannedWord).values(rows).on_conflict_do_nothing())


async def seed_badges(session: AsyncSession) -> None:
    for order, data in enumerate(BADGES, start=1):
        values = {**data, "sort_order": order}
        stmt = insert(Badge).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Badge.code], set_={k: v for k, v in values.items() if k != "code"}
        )
        await session.execute(stmt)


async def is_empty(session: AsyncSession, model: type) -> bool:
    return not await session.scalar(select(func.count()).select_from(model))


async def seed_demo(session: AsyncSession) -> None:
    category_ids = dict((await session.execute(select(Category.code, Category.id))).all())
    for data in DEMO_PROJECTS:
        values = {k: v for k, v in data.items() if k != "category"}
        values["category_id"] = category_ids[data["category"]]
        values["status"] = ContentStatus.PUBLISHED
        stmt = insert(Project).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Project.slug], set_={k: v for k, v in values.items() if k != "slug"}
        )
        await session.execute(stmt)

    for data in DEMO_CARDS:
        values = {**data, "status": ContentStatus.PUBLISHED}
        stmt = insert(KnowledgeCard).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[KnowledgeCard.slug],
            set_={k: v for k, v in values.items() if k != "slug"},
        )
        await session.execute(stmt)

    for order, data in enumerate(DEMO_LESSONS, start=1):
        values = {**data, "sort_order": order, "status": ContentStatus.PUBLISHED}
        stmt = insert(TeacherLesson).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[TeacherLesson.slug],
            set_={k: v for k, v in values.items() if k != "slug"},
        )
        await session.execute(stmt)

    # Tips, questions and game items have no natural key: demo sets go only into empty tables.
    if await is_empty(session, Tip):
        session.add_all(
            Tip(text=text, sort_order=i, status=ContentStatus.PUBLISHED)
            for i, text in enumerate(DEMO_TIPS, start=1)
        )
    if await is_empty(session, DailyTask):
        session.add_all(
            DailyTask(text=text, sort_order=i, status=ContentStatus.PUBLISHED)
            for i, text in enumerate(DEMO_DAILY_TASKS, start=1)
        )
    if await is_empty(session, Question):
        session.add_all(
            Question(
                category_id=category_ids[q["category"]] if q["category"] else None,
                text=q["text"],
                options=q["options"],
                correct_index=q["correct_index"],
                explanation=q["explanation"],
                sort_order=i,
                status=ContentStatus.PUBLISHED,
            )
            for i, q in enumerate(DEMO_QUESTIONS, start=1)
        )
    if await is_empty(session, GameItem):
        session.add_all(
            GameItem(
                name=item["name"],
                icon=item["icon"],
                correct_category_id=category_ids[item["bin"]],
                explanation=item["explanation"],
                sort_order=i,
                status=ContentStatus.PUBLISHED,
            )
            for i, item in enumerate(DEMO_GAME_ITEMS, start=1)
        )


async def run(demo: bool) -> None:
    async with SessionLocal() as session:
        await seed_categories(session)
        await seed_banned_words(session)
        await seed_badges(session)
        if demo:
            await seed_demo(session)
        await session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="also load demo content")
    args = parser.parse_args()
    asyncio.run(run(args.demo))
    print("Seed complete" + (" (with demo content)" if args.demo else ""))


if __name__ == "__main__":
    main()
