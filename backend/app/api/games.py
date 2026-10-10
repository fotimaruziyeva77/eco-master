"""Quiz and sorting game (TZ 8.4)."""

import random

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content import list_categories
from app.badges import award_badges
from app.deps import CurrentUser, SessionDep, SettingsDep
from app.models import AnalyticsEvent, Badge, Category, ContentStatus, GameItem, Question
from app.points import (
    GAME_CORRECT_POINTS,
    GAME_DAILY_CAP,
    QUIZ_CORRECT_POINTS,
    award,
    lock_user,
    points_today,
)
from app.rounds import RoundError, answer_event_id, create_round_token, read_round_token
from app.schemas import (
    BadgeOut,
    GameAnswerIn,
    GameAnswerOut,
    GameItemOut,
    GameRoundOut,
    GamesOut,
    QuizAnswerIn,
    QuizAnswerOut,
    QuizCategoryOut,
    QuizQuestionOut,
    QuizRoundIn,
    QuizRoundOut,
)
from app.timeutil import local_today

router = APIRouter(tags=["games"])

ROUND_SIZE = 10
PUBLISHED = ContentStatus.PUBLISHED


def badge_out(badges: list[Badge]) -> list[BadgeOut]:
    return [
        BadgeOut(code=b.code, name=b.name, description=b.description, icon=b.icon) for b in badges
    ]


async def already_answered(session: AsyncSession, user_id: int, event: str, props: dict) -> bool:
    """One answer per question/item per round: a second try after seeing the answer is refused."""
    return bool(
        await session.scalar(
            select(func.count())
            .select_from(AnalyticsEvent)
            .where(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.name == event,
                AnalyticsEvent.props.contains(props),
            )
        )
    )


def read_round(settings, token: str, user_id: int, kind: str) -> tuple[str, list[int]]:
    try:
        return read_round_token(settings.jwt_secret, token, user_id, kind)
    except RoundError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid_round") from exc


@router.get("/games")
async def games_overview(user: CurrentUser, session: SessionDep) -> GamesOut:
    counts = dict(
        (
            await session.execute(
                select(Question.category_id, func.count())
                .where(Question.status == PUBLISHED)
                .group_by(Question.category_id)
            )
        ).all()
    )
    categories = await session.scalars(select(Category).order_by(Category.sort_order))
    quiz_categories = [
        QuizCategoryOut(code=c.code, name=c.name, icon=c.icon, question_count=counts[c.id])
        for c in categories.all()
        if counts.get(c.id)
    ]
    item_count = await session.scalar(
        select(func.count()).select_from(GameItem).where(GameItem.status == PUBLISHED)
    )
    return GamesOut(
        quiz_categories=quiz_categories,
        quiz_total=sum(counts.values()),
        bins=[c for c in await list_categories(session) if c.is_game_bin],
        game_item_count=item_count,
        game_points_today=await points_today(session, user.id, "game_correct", local_today()),
        game_daily_cap=GAME_DAILY_CAP,
    )


# ------------------------------------------------------------------------ quiz


@router.post("/quiz/rounds")
async def start_quiz(
    body: QuizRoundIn, user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> QuizRoundOut:
    query = (
        select(Question, Category.code)
        .outerjoin(Category, Category.id == Question.category_id)
        .where(Question.status == PUBLISHED)
    )
    if body.category:
        query = query.where(Category.code == body.category)
    pool = (await session.execute(query)).all()
    if not pool:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no_questions")

    seen = set(
        (
            await session.scalars(
                select(AnalyticsEvent.props["question_id"].as_integer()).where(
                    AnalyticsEvent.user_id == user.id, AnalyticsEvent.name == "quiz_answer"
                )
            )
        ).all()
    )
    # Questions the user has not answered yet come first (TZ 8.4), each group shuffled.
    fresh = [row for row in pool if row[0].id not in seen]
    old = [row for row in pool if row[0].id in seen]
    random.shuffle(fresh)
    random.shuffle(old)
    picked = (fresh + old)[:ROUND_SIZE]

    token = create_round_token(settings.jwt_secret, user.id, "quiz", [q.id for q, _ in picked])
    return QuizRoundOut(
        round_token=token,
        questions=[
            QuizQuestionOut(
                id=q.id,
                category_code=code,
                text=q.text,
                options=q.options,
                image_url=q.image_url,
            )
            for q, code in picked
        ],
    )


@router.post("/quiz/answer")
async def answer_quiz(
    body: QuizAnswerIn, user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> QuizAnswerOut:
    round_id, ids = read_round(settings, body.round_token, user.id, "quiz")
    if body.question_id not in ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "not_in_round")
    question = await session.get(Question, body.question_id)
    if question is None or question.status != PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "question_not_found")

    await lock_user(session, user.id)
    props = {"round": round_id, "question_id": question.id}
    if await already_answered(session, user.id, "quiz_answer", props):
        raise HTTPException(status.HTTP_409_CONFLICT, "already_answered")

    correct = body.option_index == question.correct_index
    points = 0
    if correct and await award(
        session,
        user.id,
        "quiz_correct",
        QUIZ_CORRECT_POINTS,
        object_id=str(question.id),
        client_event_id=answer_event_id(round_id, question.id),
    ):
        # Only the first correct answer to a question ever earns points (TZ 8.6).
        points = QUIZ_CORRECT_POINTS
    session.add(
        AnalyticsEvent(user_id=user.id, name="quiz_answer", props={**props, "correct": correct})
    )
    new_badges = await award_badges(session, user.id) if points else []
    await session.commit()
    await session.refresh(user)
    return QuizAnswerOut(
        correct=correct,
        correct_index=question.correct_index,
        explanation=question.explanation,
        points=points,
        points_total=user.points_total,
        new_badges=badge_out(new_badges),
    )


# ------------------------------------------------------------------- sort game


@router.post("/game/rounds")
async def start_game(user: CurrentUser, session: SessionDep, settings: SettingsDep) -> GameRoundOut:
    items = (await session.scalars(select(GameItem).where(GameItem.status == PUBLISHED))).all()
    if not items:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no_items")
    picked = random.sample(list(items), min(ROUND_SIZE, len(items)))
    token = create_round_token(settings.jwt_secret, user.id, "game", [i.id for i in picked])
    return GameRoundOut(
        round_token=token,
        items=[
            GameItemOut(id=i.id, name=i.name, icon=i.icon, image_url=i.image_url) for i in picked
        ],
    )


@router.post("/game/answer")
async def answer_game(
    body: GameAnswerIn, user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> GameAnswerOut:
    round_id, ids = read_round(settings, body.round_token, user.id, "game")
    if body.item_id not in ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "not_in_round")
    row = (
        await session.execute(
            select(GameItem, Category.code)
            .join(Category, Category.id == GameItem.correct_category_id)
            .where(GameItem.id == body.item_id, GameItem.status == PUBLISHED)
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "item_not_found")
    item, correct_bin = row

    await lock_user(session, user.id)
    props = {"round": round_id, "item_id": item.id}
    if await already_answered(session, user.id, "game_answer", props):
        raise HTTPException(status.HTTP_409_CONFLICT, "already_answered")

    today = local_today()
    earned_today = await points_today(session, user.id, "game_correct", today)
    correct = body.bin == correct_bin
    points = 0
    if correct:
        # Every correct sort is recorded (it counts for a badge); points stop at the daily cap.
        points = min(GAME_CORRECT_POINTS, max(0, GAME_DAILY_CAP - earned_today))
        recorded = await award(
            session,
            user.id,
            "game_correct",
            points,
            object_id=str(item.id),
            client_event_id=answer_event_id(round_id, item.id),
            day=today,
        )
        points = points if recorded else 0
    session.add(
        AnalyticsEvent(user_id=user.id, name="game_answer", props={**props, "correct": correct})
    )
    new_badges = await award_badges(session, user.id) if correct else []
    await session.commit()
    await session.refresh(user)
    return GameAnswerOut(
        correct=correct,
        correct_bin=correct_bin,
        explanation=item.explanation,
        points=points,
        points_today=earned_today + points,
        daily_cap=GAME_DAILY_CAP,
        points_total=user.points_total,
        new_badges=badge_out(new_badges),
    )
