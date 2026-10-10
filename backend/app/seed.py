"""Load reference data (and optionally demo content): python -m app.seed [--demo]

Safe to run repeatedly: rows are matched by their natural keys and updated in place.
"""

import argparse
import asyncio

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models import BannedWord, Category, ContentStatus, KnowledgeCard, Project, Tip, WordKind
from app.seed_data import (
    CATEGORIES,
    DEMO_CARDS,
    DEMO_PROJECTS,
    DEMO_TIPS,
    PROFANITY,
    RESERVED_WORDS,
)


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

    # Tips have no natural key; add the demo set only to an empty table.
    if not await session.scalar(select(func.count()).select_from(Tip)):
        session.add_all(
            Tip(text=text, sort_order=i, status=ContentStatus.PUBLISHED)
            for i, text in enumerate(DEMO_TIPS, start=1)
        )


async def run(demo: bool) -> None:
    async with SessionLocal() as session:
        await seed_categories(session)
        await seed_banned_words(session)
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
