"""Learning content: waste types, projects (video lessons), knowledge cards, tip of the day."""

from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.badges import award_badges
from app.deps import CurrentUser, SessionDep
from app.models import (
    ActivityLog,
    Category,
    ContentStatus,
    KnowledgeCard,
    Project,
    Tip,
    TipSchedule,
)
from app.points import PROJECT_DONE_POINTS, award
from app.schemas import (
    BadgeOut,
    CardDetailOut,
    CardSummaryOut,
    CategoryDetailOut,
    CategoryOut,
    DoneIn,
    DoneOut,
    HomeOut,
    ProjectDetailOut,
    ProjectSummaryOut,
    TipOut,
    UserOut,
)
from app.timeutil import local_today

router = APIRouter(tags=["content"])

PUBLISHED = ContentStatus.PUBLISHED


async def list_categories(session: AsyncSession) -> list[CategoryOut]:
    counts = (
        select(Project.category_id, func.count().label("n"))
        .where(Project.status == PUBLISHED)
        .group_by(Project.category_id)
        .subquery()
    )
    rows = await session.execute(
        select(Category, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.category_id == Category.id)
        .order_by(Category.sort_order, Category.id)
    )
    return [
        CategoryOut(
            code=c.code,
            name=c.name,
            icon=c.icon,
            color=c.color,
            has_projects=c.has_projects,
            is_game_bin=c.is_game_bin,
            project_count=n,
        )
        for c, n in rows.all()
    ]


async def done_project_ids(session: AsyncSession, user_id: int) -> set[str]:
    rows = await session.scalars(
        select(ActivityLog.object_id).where(
            ActivityLog.user_id == user_id, ActivityLog.action == "project_done"
        )
    )
    return set(rows.all())


def project_summary(project: Project, category: Category, done: set[str]) -> ProjectSummaryOut:
    return ProjectSummaryOut(
        slug=project.slug,
        category_code=category.code,
        title=project.title,
        difficulty=project.difficulty,
        safety_level=project.safety_level,
        duration_min=project.duration_min,
        poster_url=project.poster_url,
        has_video=bool(project.video_url),
        done=str(project.id) in done,
    )


async def tip_of_the_day(session: AsyncSession, day: date) -> Tip | None:
    """A tip scheduled for this date in the admin panel, otherwise the next one in rotation."""
    scheduled = await session.scalar(
        select(Tip)
        .join(TipSchedule, TipSchedule.tip_id == Tip.id)
        .where(TipSchedule.day == day, Tip.status == PUBLISHED)
    )
    if scheduled is not None:
        return scheduled
    tips = (
        await session.scalars(
            select(Tip).where(Tip.status == PUBLISHED).order_by(Tip.sort_order, Tip.id)
        )
    ).all()
    return tips[day.toordinal() % len(tips)] if tips else None


@router.get("/home")
async def home(user: CurrentUser, session: SessionDep) -> HomeOut:
    tip = await tip_of_the_day(session, local_today())
    categories = [c for c in await list_categories(session) if c.has_projects]
    return HomeOut(
        user=UserOut.model_validate(user),
        tip=TipOut(id=tip.id, text=tip.text) if tip else None,
        categories=categories,
    )


@router.get("/categories")
async def categories(user: CurrentUser, session: SessionDep) -> list[CategoryOut]:
    return await list_categories(session)


@router.get("/categories/{code}")
async def category_detail(code: str, user: CurrentUser, session: SessionDep) -> CategoryDetailOut:
    category = await session.scalar(select(Category).where(Category.code == code))
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "category_not_found")
    projects = (
        await session.scalars(
            select(Project)
            .where(Project.category_id == category.id, Project.status == PUBLISHED)
            .order_by(Project.sort_order, Project.id)
        )
    ).all()
    done = await done_project_ids(session, user.id)
    summaries = [project_summary(p, category, done) for p in projects]
    category_out = next(c for c in await list_categories(session) if c.code == code)
    return CategoryDetailOut(category=category_out, projects=summaries)


async def get_published_project(session: AsyncSession, slug: str) -> tuple[Project, Category]:
    row = (
        await session.execute(
            select(Project, Category)
            .join(Category, Category.id == Project.category_id)
            .where(Project.slug == slug, Project.status == PUBLISHED)
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project_not_found")
    return row[0], row[1]


@router.get("/projects/{slug}")
async def project_detail(slug: str, user: CurrentUser, session: SessionDep) -> ProjectDetailOut:
    project, category = await get_published_project(session, slug)
    done = await done_project_ids(session, user.id)
    summary = project_summary(project, category, done)
    return ProjectDetailOut(
        **summary.model_dump(),
        category_name=category.name,
        category_icon=category.icon,
        materials=project.materials,
        steps=project.steps,
        safety_text=project.safety_text,
        video_url=project.video_url,
    )


@router.post("/projects/{slug}/done")
async def project_done(slug: str, body: DoneIn, user: CurrentUser, session: SessionDep) -> DoneOut:
    """15 points, once per project (TZ 8.6, QM-06). Retries with the same event id are no-ops."""
    project, _ = await get_published_project(session, slug)
    awarded = await award(
        session,
        user.id,
        "project_done",
        PROJECT_DONE_POINTS,
        object_id=str(project.id),
        client_event_id=body.client_event_id,
    )
    new_badges = await award_badges(session, user.id) if awarded else []
    await session.commit()
    await session.refresh(user)
    return DoneOut(
        awarded=awarded,
        points=PROJECT_DONE_POINTS if awarded else 0,
        points_total=user.points_total,
        new_badges=[
            BadgeOut(code=b.code, name=b.name, description=b.description, icon=b.icon)
            for b in new_badges
        ],
    )


@router.get("/cards")
async def cards(user: CurrentUser, session: SessionDep) -> list[CardSummaryOut]:
    rows = await session.scalars(
        select(KnowledgeCard)
        .where(KnowledgeCard.status == PUBLISHED)
        .order_by(KnowledgeCard.sort_order, KnowledgeCard.id)
    )
    return [CardSummaryOut(slug=c.slug, title=c.title, image_url=c.image_url) for c in rows.all()]


@router.get("/cards/{slug}")
async def card_detail(slug: str, user: CurrentUser, session: SessionDep) -> CardDetailOut:
    card = await session.scalar(
        select(KnowledgeCard).where(KnowledgeCard.slug == slug, KnowledgeCard.status == PUBLISHED)
    )
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "card_not_found")
    return CardDetailOut(
        slug=card.slug, title=card.title, image_url=card.image_url, sections=card.sections
    )
