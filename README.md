# Ekoustoz

Telegram Mini App that teaches children and adults to sort waste and give it a second life.
Specification: [docs/Ekoustoz_TZ_v0.2.docx](docs/Ekoustoz_TZ_v0.2.docx).

| Part | Stack | Folder |
|---|---|---|
| API, bot, admin | Python 3.13, FastAPI, SQLAlchemy 2 (async), Alembic, aiogram 3 | `backend/` |
| Mini App | React 19, TypeScript, Vite, i18next | `frontend/` |
| Database | PostgreSQL 17 (Docker) | `docker-compose.yml` |

## Run locally

Requirements: Docker, Python 3.12+, Node.js 22+.

```bash
cp .env.example .env              # then edit values if needed
docker compose up -d db           # PostgreSQL on 127.0.0.1:55440

cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"    # Linux/macOS: .venv/bin/python
.venv/Scripts/alembic upgrade head
.venv/Scripts/python -m app.seed --demo                 # waste types, banned words, demo content
.venv/Scripts/python -m uvicorn app.main:app --port 8090    # restart after backend changes

cd ../frontend
npm install
npm run dev                       # http://localhost:5180
```

In a normal browser the Mini App logs in with a fake Telegram user
(`ENV=dev` + `DEV_AUTH=true` in `.env`, `VITE_DEV_AUTH=true` in `frontend/.env.development`).
API docs: http://localhost:8090/api/docs

### Opening it inside Telegram

Telegram only opens Mini Apps over HTTPS.

1. Create a bot with @BotFather, then a Mini App with `/newapp`.
2. Put the token into `.env` as `BOT_TOKEN` yourself (never share it in chats or commits),
   and set `BOT_USERNAME`.
3. Start a tunnel to the Vite server, e.g. `cloudflared tunnel --url http://localhost:5180`
   or `ngrok http 5180`, and set `WEBAPP_URL` to the HTTPS address it prints
   (also use it as the Mini App URL in BotFather).
4. Run the bot: `cd backend && .venv/Scripts/python -m app.bot`, then send `/start` to it.

The Vite server proxies `/api` to the backend, so one tunnel is enough.

## Checks

```bash
cd backend && .venv/Scripts/python -m pytest && .venv/Scripts/ruff check app tests
cd frontend && npm run typecheck && npm test && npm run build
npm run gen:api   # regenerate src/api/schema.ts after API changes (backend must be running)
```

## Database migrations

```bash
cd backend
.venv/Scripts/alembic revision --autogenerate -m "describe change"
.venv/Scripts/alembic upgrade head
```

Tests use the separate `ekoustoz_test` database (created by `backend/scripts/create-test-db.sql`).
