"""The Monday class report for teachers (app/class_report.py, sent by app/reminders.py)."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.class_report import ClassWeek, TaskLine, report_text
from app.models import ClassMember, ClassTask, ContentStatus, Project, SchoolClass, UserPath
from app.points import award
from app.reminders import send_due_reminders
from app.seed import seed_badges, seed_categories, seed_demo
from tests.test_phase5 import DAY, FakeBot, at, make_user

# DAY is a Monday.
LAST_MONDAY = DAY - timedelta(days=7)
LONG_AGO = datetime(2026, 9, 1, tzinfo=UTC)


@pytest.fixture
async def content(session):
    await seed_categories(session)
    await seed_badges(session)
    await seed_demo(session)
    await session.commit()


async def projects(session, count: int) -> list[Project]:
    rows = await session.scalars(
        select(Project).where(Project.status == ContentStatus.PUBLISHED).order_by(Project.id)
    )
    found = list(rows.all())[:count]
    assert len(found) == count
    return found


async def make_class(session, teacher_id: int, name: str, code: str, created_at=LONG_AGO):
    school_class = SchoolClass(teacher_id=teacher_id, name=name, code=code, created_at=created_at)
    session.add(school_class)
    await session.commit()
    return school_class


async def join(session, school_class: SchoolClass, *users) -> None:
    session.add_all(ClassMember(class_id=school_class.id, user_id=u.id) for u in users)
    await session.commit()


async def earn(session, user_id: int, points: int, day, **values) -> None:
    await award(session, user_id, values.pop("action", "test"), points, day=day, **values)
    await session.commit()


def teachers_message(bot: FakeBot, chat_id: int) -> str:
    [text] = [text for chat, text in bot.messages if chat == chat_id]
    return text


async def test_teacher_gets_the_week_of_the_class(content, session):
    teacher = await make_user(session, 81, nickname="Ustoz", path=UserPath.TEACHER)
    lola = await make_user(session, 82, nickname="Lola")
    hidden = await make_user(session, 83, nickname="Bulbul", nickname_hidden=True)
    quiet = await make_user(session, 84, nickname="Chinor")
    blocked = await make_user(session, 85, nickname="Yomon", is_blocked=True)
    school_class = await make_class(session, teacher.id, "7-B & 7-V", "ABC234")
    await join(session, school_class, lola, hidden, quiet, blocked)

    late, open_, old = await projects(session, 3)
    session.add_all(
        [
            ClassTask(
                class_id=school_class.id,
                project_id=late.id,
                due_date=LAST_MONDAY + timedelta(days=3),
            ),
            ClassTask(
                class_id=school_class.id, project_id=open_.id, due_date=DAY + timedelta(days=5)
            ),
            ClassTask(
                class_id=school_class.id,
                project_id=old.id,
                due_date=LAST_MONDAY - timedelta(days=3),
            ),
        ]
    )
    await session.commit()
    await earn(session, lola.id, 30, LAST_MONDAY + timedelta(days=1))
    await earn(
        session,
        lola.id,
        15,
        LAST_MONDAY + timedelta(days=2),
        action="project_done",
        object_id=str(late.id),
    )
    await earn(session, hidden.id, 50, LAST_MONDAY + timedelta(days=4))
    await earn(session, blocked.id, 100, LAST_MONDAY + timedelta(days=4))

    bot = FakeBot()
    await send_due_reminders(session, bot, now=at(18, 5))
    text = teachers_message(bot, 81)
    assert "7-B &amp; 7-V" in text
    assert "3 o'quvchidan 2 tasi faol" in text  # the blocked pupil is left out
    assert "🏆 Eco-Master a'zosi (50), @Lola (45)" in text  # a hidden nickname stays hidden
    assert "Yomon" not in text
    assert f"⏰ «{late.title['uz']}»: 3 tadan 1 tasi bajardi, muddat o'tdi" in text
    assert f"📌 «{open_.title['uz']}»: 3 tadan 0 tasi bajardi" in text
    assert old.title["uz"] not in text  # due before last week

    # The report is the teacher's Monday message: no reminder on top of it.
    await session.refresh(teacher)
    assert (teacher.last_weekly_date, teacher.last_reminder_date) == (DAY, DAY)
    assert await send_due_reminders(session, bot, now=at(19, 0)) == 0


async def test_no_report_without_pupils_or_for_a_class_opened_today(content, session):
    teacher = await make_user(session, 86, path=UserPath.TEACHER)
    await make_class(session, teacher.id, "Bo'sh", "EMP234")
    newcomer = await make_user(session, 87)
    today_class = await make_class(session, teacher.id, "Yangi", "NEW234", created_at=at(9, 0))
    await join(session, today_class, newcomer)
    # The teacher played last week: their own summary, as for everyone else.
    await earn(session, teacher.id, 20, LAST_MONDAY)

    bot = FakeBot()
    await send_due_reminders(session, bot, now=at(18, 5))
    text = teachers_message(bot, 86)
    assert "Sinflaringiz" not in text
    assert "o'tgan haftadagi natijangiz" in text


def test_report_lines():
    quiet = ClassWeek(
        name="9-A",
        members=2,
        active=0,
        top=[],
        tasks=[TaskLine(title="Qalamdon <yangi>", done=2, total=2, overdue=False)],
    )
    text = report_text("en", [quiet])
    assert "0 of 2 pupils were active" in text
    assert "Nobody earned points" in text
    assert "✅ «Qalamdon &lt;yangi&gt;»: everyone did it" in text
