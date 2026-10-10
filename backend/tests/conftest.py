import json
import os
import time

# Must be set before the app (and its settings/engine) is imported.
os.environ.update(
    {
        "ENV": "test",
        "DATABASE_URL": "postgresql+asyncpg://ekoustoz:ekoustoz@127.0.0.1:55440/ekoustoz_test",
        "BOT_TOKEN": "123456:test-token",
        # Pinned so values from a developer's .env never leak into tests.
        "BOT_USERNAME": "",
        "WEBAPP_SHORT_NAME": "app",
        "WEBAPP_URL": "http://localhost:5180",
        "JWT_SECRET": "test-secret-0123456789-0123456789",
        "DEV_AUTH": "false",
    }
)

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app import models  # noqa: E402, F401
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.deps import bot_dep  # noqa: E402
from app.main import app  # noqa: E402
from app.security import sign_init_data  # noqa: E402

BOT_TOKEN = os.environ["BOT_TOKEN"]


@pytest.fixture(scope="session", autouse=True)
async def schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_tables(schema):
    yield
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
def no_telegram():
    """Tests never call the real Telegram API; tests that need a bot install a fake one."""
    app.dependency_overrides[bot_dep] = lambda: None
    yield
    app.dependency_overrides.pop(bot_dep, None)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def session():
    async with SessionLocal() as s:
        yield s


def make_init_data(
    telegram_id: int = 42,
    language_code: str | None = "ru",
    auth_date: int | None = None,
    start_param: str | None = None,
    token: str = BOT_TOKEN,
) -> str:
    user = {"id": telegram_id, "first_name": "Test"}
    if language_code is not None:
        user["language_code"] = language_code
    fields = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "AAH-test",
        "user": json.dumps(user, separators=(",", ":")),
    }
    if start_param:
        fields["start_param"] = start_param
    return sign_init_data(token, fields)


async def login(client: AsyncClient, **kwargs) -> dict:
    response = await client.post("/api/auth/telegram", json={"init_data": make_init_data(**kwargs)})
    assert response.status_code == 200, response.text
    return response.json()
