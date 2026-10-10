"""Load reference data (and optionally demo content): python -m app.seed [--demo]

Safe to run repeatedly. Content, waste types and word lists are managed in the admin panel,
so existing rows are never overwritten: only missing ones are added. Badges are defined by
code and are kept in sync.

With --demo in development (ENV=dev) a test admin is created as well; see DEV_ADMIN_* below.
With --content the version 1 content drafts (app/seed_data_v1.py) are added "In review":
they go live only after the team checks and publishes them in the admin panel (TZ 9.3).
"""

import argparse
import asyncio
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import hash_password
from app.config import get_settings
from app.db import SessionLocal
from app.models import (
    AdminRole,
    AdminUser,
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
from app.seed_data_v1 import (
    V1_CARDS,
    V1_DAILY_TASKS,
    V1_GAME_ITEMS,
    V1_PROJECTS,
    V1_QUESTIONS,
    V1_TIPS,
)

# Local development only (ENV=dev): the admin panel at http://localhost:5180/admin/.
# The first sign-in asks to connect an authenticator app (2FA is required for everyone).
DEV_ADMIN_LOGIN = "admin"
DEV_ADMIN_PASSWORD = "ekoustoz-dev-admin"


async def seed_categories(session: AsyncSession) -> None:
    for order, data in enumerate(CATEGORIES, start=1):
        await session.execute(
            insert(Category).values(**data, sort_order=order).on_conflict_do_nothing()
        )


async def seed_banned_words(session: AsyncSession) -> None:
    """Only into an empty list: words deleted in the admin panel must stay deleted."""
    if not await is_empty(session, BannedWord):
        return
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
        await session.execute(insert(Project).values(**values).on_conflict_do_nothing())

    for data in DEMO_CARDS:
        values = {**data, "status": ContentStatus.PUBLISHED}
        await session.execute(insert(KnowledgeCard).values(**values).on_conflict_do_nothing())

    for order, data in enumerate(DEMO_LESSONS, start=1):
        values = {**data, "sort_order": order, "status": ContentStatus.PUBLISHED}
        await session.execute(insert(TeacherLesson).values(**values).on_conflict_do_nothing())

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


async def _uz_texts(session: AsyncSession, column) -> set[str]:
    return set((await session.scalars(select(column["uz"].astext))).all())


async def seed_v1_content(session: AsyncSession) -> Counter:
    """Version 1 content drafts in the "In review" status. Returns what was added.

    Rows are matched by slug, or by the Uzbek text where there is no slug, so running it
    again adds nothing twice and never touches what editors have already changed.
    """
    review = ContentStatus.REVIEW
    added: Counter = Counter()
    category_ids = dict((await session.execute(select(Category.code, Category.id))).all())

    for order, data in enumerate(V1_PROJECTS, start=10):
        values = {k: v for k, v in data.items() if k != "category"}
        values |= {
            "category_id": category_ids[data["category"]],
            "status": review,
            "sort_order": order,
        }
        stmt = insert(Project).values(**values).on_conflict_do_nothing().returning(Project.id)
        if (await session.execute(stmt)).scalar_one_or_none() is not None:
            added["projects"] += 1

    for order, data in enumerate(V1_CARDS, start=10):
        values = {**data, "status": review, "sort_order": order}
        stmt = insert(KnowledgeCard).values(**values).on_conflict_do_nothing()
        if (await session.execute(stmt.returning(KnowledgeCard.id))).first() is not None:
            added["cards"] += 1

    known = await _uz_texts(session, Question.text)
    for order, q in enumerate(V1_QUESTIONS, start=100):
        if q["text"]["uz"] in known:
            continue
        session.add(
            Question(
                category_id=category_ids[q["category"]] if q["category"] else None,
                text=q["text"],
                options=q["options"],
                correct_index=q["correct_index"],
                explanation=q["explanation"],
                sort_order=order,
                status=review,
            )
        )
        added["questions"] += 1

    known = await _uz_texts(session, GameItem.name)
    for order, data in enumerate(V1_GAME_ITEMS, start=100):
        if data["name"]["uz"] in known:
            continue
        session.add(
            GameItem(
                name=data["name"],
                icon=data["icon"],
                correct_category_id=category_ids[data["bin"]],
                explanation=data["explanation"],
                sort_order=order,
                status=review,
            )
        )
        added["game_items"] += 1

    for model, rows, key in ((DailyTask, V1_DAILY_TASKS, "daily_tasks"), (Tip, V1_TIPS, "tips")):
        known = await _uz_texts(session, model.text)
        for order, text in enumerate(rows, start=100):
            if text["uz"] in known:
                continue
            session.add(model(text=text, sort_order=order, status=review))
            added[key] += 1
    await session.flush()
    return added


async def seed_dev_admin(session: AsyncSession) -> bool:
    if get_settings().env != "dev":
        return False
    if await session.scalar(select(AdminUser.id).where(AdminUser.login == DEV_ADMIN_LOGIN)):
        return False
    session.add(
        AdminUser(
            login=DEV_ADMIN_LOGIN,
            name="Dev Admin",
            role=AdminRole.ADMIN,
            password_hash=hash_password(DEV_ADMIN_PASSWORD),
        )
    )
    return True


async def run(demo: bool, content: bool) -> None:
    async with SessionLocal() as session:
        await seed_categories(session)
        await seed_banned_words(session)
        await seed_badges(session)
        if demo:
            await seed_demo(session)
            if await seed_dev_admin(session):
                print(f"Dev admin created: login {DEV_ADMIN_LOGIN!r} (password in app/seed.py)")
        if content:
            added = await seed_v1_content(session)
            summary = ", ".join(f"{k} {v}" for k, v in sorted(added.items())) or "nothing new"
            print(f"Version 1 content added for review: {summary}")
        await session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="also load demo content")
    parser.add_argument(
        "--content", action="store_true", help="also add the version 1 content drafts for review"
    )
    args = parser.parse_args()
    asyncio.run(run(args.demo, args.content))
    print("Seed complete")


if __name__ == "__main__":
    main()
