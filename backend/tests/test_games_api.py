import uuid

import pytest
from sqlalchemy import select, update

from app.badges import award_badges
from app.models import ActivityLog, Category, GameItem, Question, User
from app.seed import seed_badges, seed_categories, seed_demo
from app.timeutil import local_today
from tests.conftest import login


@pytest.fixture
async def headers(client, session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_demo(session)
    await session.commit()
    body = await login(client, telegram_id=900)
    return {"Authorization": f"Bearer {body['token']}"}


async def correct_index(session, question_id: int) -> int:
    return (await session.get(Question, question_id)).correct_index


async def correct_bin(session, item_id: int) -> str:
    return await session.scalar(
        select(Category.code)
        .join(GameItem, GameItem.correct_category_id == Category.id)
        .where(GameItem.id == item_id)
    )


async def test_overview(client, headers):
    body = (await client.get("/api/games", headers=headers)).json()
    assert body["quiz_total"] == 12
    assert [b["code"] for b in body["bins"]] == [
        "plastic",
        "glass",
        "paper",
        "organic",
        "metal",
        "hazardous",
    ]
    assert body["game_daily_cap"] == 40
    assert body["game_points_today"] == 0


async def test_quiz_round_does_not_leak_answers(client, headers):
    r = await client.post("/api/quiz/rounds", json={}, headers=headers)
    body = r.json()
    assert len(body["questions"]) == 10
    assert "correct_index" not in r.text
    assert "explanation" not in r.text


async def test_quiz_points_only_for_first_correct_answer(client, headers, session):
    # QM-07: a repeated correct answer gives no points; an explanation always follows.
    for expected_points in (5, 0):
        rnd = (
            await client.post("/api/quiz/rounds", json={"category": "glass"}, headers=headers)
        ).json()
        question = rnd["questions"][0]
        answer = await client.post(
            "/api/quiz/answer",
            json={
                "round_token": rnd["round_token"],
                "question_id": question["id"],
                "option_index": await correct_index(session, question["id"]),
            },
            headers=headers,
        )
        body = answer.json()
        assert body["correct"] is True
        assert body["points"] == expected_points
        assert body["explanation"]["uz"]
    assert body["points_total"] == 5


async def test_wrong_quiz_answer(client, headers, session):
    rnd = (
        await client.post("/api/quiz/rounds", json={"category": "metal"}, headers=headers)
    ).json()
    question = rnd["questions"][0]
    right = await correct_index(session, question["id"])
    answer = await client.post(
        "/api/quiz/answer",
        json={
            "round_token": rnd["round_token"],
            "question_id": question["id"],
            "option_index": (right + 1) % 3,
        },
        headers=headers,
    )
    body = answer.json()
    assert body["correct"] is False
    assert body["correct_index"] == right
    assert body["points"] == 0


async def test_cannot_change_answer_after_seeing_it(client, headers, session):
    rnd = (
        await client.post("/api/quiz/rounds", json={"category": "paper"}, headers=headers)
    ).json()
    question = rnd["questions"][0]
    right = await correct_index(session, question["id"])
    payload = {"round_token": rnd["round_token"], "question_id": question["id"]}
    await client.post(
        "/api/quiz/answer", json={**payload, "option_index": (right + 1) % 4}, headers=headers
    )
    second = await client.post(
        "/api/quiz/answer", json={**payload, "option_index": right}, headers=headers
    )
    assert second.status_code == 409


async def test_round_is_bound_to_user_and_questions(client, headers):
    rnd = (
        await client.post("/api/quiz/rounds", json={"category": "glass"}, headers=headers)
    ).json()
    other = await login(client, telegram_id=901)
    other_headers = {"Authorization": f"Bearer {other['token']}"}
    payload = {
        "round_token": rnd["round_token"],
        "question_id": rnd["questions"][0]["id"],
        "option_index": 0,
    }

    assert (
        await client.post("/api/quiz/answer", json=payload, headers=other_headers)
    ).status_code == 400
    wrong_question = {**payload, "question_id": 999999}
    assert (
        await client.post("/api/quiz/answer", json=wrong_question, headers=headers)
    ).status_code == 400
    forged = {**payload, "round_token": "abc"}
    assert (await client.post("/api/quiz/answer", json=forged, headers=headers)).status_code == 400


async def play_game_round(client, headers, session, *, correctly: bool) -> list[dict]:
    rnd = (await client.post("/api/game/rounds", headers=headers)).json()
    results = []
    for item in rnd["items"]:
        right = await correct_bin(session, item["id"])
        answer = await client.post(
            "/api/game/answer",
            json={
                "round_token": rnd["round_token"],
                "item_id": item["id"],
                "bin": right if correctly else "glass" if right != "glass" else "paper",
            },
            headers=headers,
        )
        results.append(answer.json())
    return results


async def test_game_daily_cap(client, headers, session):
    # QM-08: no more than 40 points a day from the game.
    results = []
    for _ in range(3):
        results += await play_game_round(client, headers, session, correctly=True)
    assert all(r["correct"] for r in results)
    assert sum(r["points"] for r in results) == 40
    assert results[-1]["points_today"] == 40
    assert results[-1]["points"] == 0

    # Correct sorts beyond the cap are still recorded (they count towards a badge).
    count = len(
        (
            await session.scalars(
                select(ActivityLog.id).where(ActivityLog.action == "game_correct")
            )
        ).all()
    )
    assert count == 30
    overview = (await client.get("/api/games", headers=headers)).json()
    assert overview["game_points_today"] == 40


async def test_wrong_sort_and_timeout(client, headers, session):
    rnd = (await client.post("/api/game/rounds", headers=headers)).json()
    first, second = rnd["items"][:2]
    wrong = await client.post(
        "/api/game/answer",
        json={"round_token": rnd["round_token"], "item_id": first["id"], "bin": "nonsense"},
        headers=headers,
    )
    assert wrong.json()["correct"] is False
    assert wrong.json()["correct_bin"] == await correct_bin(session, first["id"])
    assert wrong.json()["explanation"]["ru"]

    timeout = await client.post(
        "/api/game/answer",
        json={"round_token": rnd["round_token"], "item_id": second["id"], "bin": None},
        headers=headers,
    )
    assert timeout.json()["correct"] is False
    again = await client.post(
        "/api/game/answer",
        json={"round_token": rnd["round_token"], "item_id": second["id"], "bin": "glass"},
        headers=headers,
    )
    assert again.status_code == 409


async def test_first_step_and_category_master_badges(client, headers):
    r = await client.post(
        "/api/projects/dry-leaves-compost/done",
        json={"client_event_id": str(uuid.uuid4())},
        headers=headers,
    )
    codes = [b["code"] for b in r.json()["new_badges"]]
    # The only demo organic project is done, so the compost badge comes with the first points.
    assert codes == ["first_step", "master_organic"]

    badges = (await client.get("/api/me/badges", headers=headers)).json()
    assert len(badges) == 9
    earned = {b["code"] for b in badges if b["earned_at"]}
    assert earned == {"first_step", "master_organic"}


async def test_counter_badges(client, headers, session):
    user_id = (await client.get("/api/me", headers=headers)).json()["id"]
    today = local_today()
    session.add_all(
        ActivityLog(
            user_id=user_id, action="quiz_correct", object_id=str(i), points=0, local_date=today
        )
        for i in range(50)
    )
    session.add_all(
        ActivityLog(
            user_id=user_id, action="game_correct", object_id="1", points=0, local_date=today
        )
        for _ in range(100)
    )
    await session.commit()
    new = {b.code for b in await award_badges(session, user_id)}
    assert {"quiz_champion", "sorting_master"} <= new
    assert not await award_badges(session, user_id)  # never granted twice


async def test_login_catches_up_on_badges(client, headers, session):
    """Users who earned points before badges existed get them at their next login."""
    user_id = (await client.get("/api/me", headers=headers)).json()["id"]
    session.add(
        ActivityLog(
            user_id=user_id, action="legacy", object_id=None, points=10, local_date=local_today()
        )
    )
    await session.execute(update(User).where(User.id == user_id).values(points_total=10))
    await session.commit()

    await login(client, telegram_id=900)
    badges = (await client.get("/api/me/badges", headers=headers)).json()
    assert {b["code"] for b in badges if b["earned_at"]} == {"first_step"}
