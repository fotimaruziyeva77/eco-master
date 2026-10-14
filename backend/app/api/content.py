"""Learning content: waste types, projects (video lessons), knowledge cards, tip of the day."""

from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import track
from app.api.daily import daily_state
from app.badges import award_badges, badges_out
from app.content_media import step_picture_urls
from app.daily import tip_of_the_day
from app.deps import CurrentUser, SessionDep
from app.models import (
    ActivityLog,
    Category,
    ClassMember,
    ClassTask,
    ContentStatus,
    KnowledgeCard,
    Project,
    SchoolClass,
)
from app.points import PROJECT_DONE_POINTS, award
from app.schemas import (
    CardDetailOut,
    CardSummaryOut,
    CategoryDetailOut,
    CategoryOut,
    DoneIn,
    DoneOut,
    HomeClassTaskOut,
    HomeOut,
    ProjectDetailOut,
    ProjectSummaryOut,
    TipOut,
    UserOut,
    VideoCardOut,
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
            examples=c.examples,
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


async def featured_project(
    session: AsyncSession, user_id: int, day: date
) -> ProjectSummaryOut | None:
    """A project the user has not done yet, changing every day (home screen card)."""
    done = await done_project_ids(session, user_id)
    rows = (
        await session.execute(
            select(Project, Category)
            .join(Category, Category.id == Project.category_id)
            .where(Project.status == PUBLISHED)
            .order_by(Project.sort_order, Project.id)
        )
    ).all()
    todo = [(p, c) for p, c in rows if str(p.id) not in done]
    if not todo:
        return None
    project, category = todo[day.toordinal() % len(todo)]
    return project_summary(project, category, done)


# The feed plays files only: a link to another site (YouTube) can not run in it.
FEED_SIZE = 30


async def video_cards(session: AsyncSession, user_id: int) -> list[VideoCardOut]:
    """Published projects with a video file, the ones not made yet first."""
    done = await done_project_ids(session, user_id)
    rows = (
        await session.execute(
            select(Project, Category)
            .join(Category, Category.id == Project.category_id)
            .where(Project.status == PUBLISHED, Project.video_url.ilike("%.mp4"))
            .order_by(Project.sort_order, Project.id)
        )
    ).all()
    cards = [
        VideoCardOut(
            **project_summary(p, c, done).model_dump(),
            video_url=p.video_url,
            category_icon=c.icon,
        )
        for p, c in rows
    ]
    cards.sort(key=lambda card: card.done)  # stable: keeps the editors' order within each part
    return cards[:FEED_SIZE]


async def class_task(session: AsyncSession, user_id: int, today: date) -> HomeClassTaskOut | None:
    """The class task due soonest that the pupil has not done; overdue ones are left out."""
    done = await done_project_ids(session, user_id)
    rows = await session.execute(
        select(ClassTask, Project, Category, SchoolClass)
        .join(ClassMember, ClassMember.class_id == ClassTask.class_id)
        .join(SchoolClass, SchoolClass.id == ClassTask.class_id)
        .join(Project, Project.id == ClassTask.project_id)
        .join(Category, Category.id == Project.category_id)
        .where(
            ClassMember.user_id == user_id,
            ClassTask.due_date >= today,
            Project.status == PUBLISHED,
        )
        .order_by(ClassTask.due_date, ClassTask.id)
    )
    for task, project, category, school_class in rows.all():
        if str(project.id) not in done:
            return HomeClassTaskOut(
                project_slug=project.slug,
                title=project.title,
                icon=category.icon,
                due_date=task.due_date,
                class_name=school_class.name,
            )
    return None


@router.get("/home")
async def home(user: CurrentUser, session: SessionDep) -> HomeOut:
    today = local_today()
    tip = await tip_of_the_day(session, today)
    categories = [c for c in await list_categories(session) if c.has_projects]
    return HomeOut(
        user=UserOut.model_validate(user),
        daily=await daily_state(session, user),
        tip=TipOut(id=tip.id, text=tip.text) if tip else None,
        categories=categories,
        featured=await featured_project(session, user.id, today),
        class_task=await class_task(session, user.id, today),
        videos=await video_cards(session, user.id),
    )


@router.get("/videos")
async def videos(user: CurrentUser, session: SessionDep) -> list[VideoCardOut]:
    """The home screen's video feed, for opening it on its own."""
    return await video_cards(session, user.id)


@router.get("/categories")
async def categories(user: CurrentUser, session: SessionDep) -> list[CategoryOut]:
    return await list_categories(session)


@router.get("/projects")
async def projects(user: CurrentUser, session: SessionDep) -> list[ProjectSummaryOut]:
    """Every published project, by waste type (the teacher's task picker)."""
    done = await done_project_ids(session, user.id)
    rows = await session.execute(
        select(Project, Category)
        .join(Category, Category.id == Project.category_id)
        .where(Project.status == PUBLISHED)
        .order_by(Category.sort_order, Project.sort_order, Project.id)
    )
    return [project_summary(p, c, done) for p, c in rows.all()]


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
    # How many times people have made it — a little social proof on the card.
    done_count = await session.scalar(
        select(func.count())
        .select_from(ActivityLog)
        .where(ActivityLog.action == "project_done", ActivityLog.object_id == str(project.id))
    )
    # "Most viewed lessons" in the admin statistics (TZ 8.12).
    track(session, user, "project_view", project=project.slug)
    await session.commit()
    return ProjectDetailOut(
        **summary.model_dump(),
        category_name=category.name,
        category_icon=category.icon,
        materials=project.materials,
        steps=project.steps,
        safety_text=project.safety_text,
        video_url=project.video_url,
        done_count=done_count,
        step_times=project.step_times,
        step_pictures=(
            step_picture_urls(project.video_url, project.step_times) if project.step_times else None
        ),
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
    if awarded:
        track(session, user, "project_done", project=project.slug)
    await session.commit()
    await session.refresh(user)
    return DoneOut(
        awarded=awarded,
        points=PROJECT_DONE_POINTS if awarded else 0,
        points_total=user.points_total,
        new_badges=badges_out(new_badges),
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
