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
   and set `BOT_USERNAME`. The frontend needs the username too, for the class invite QR code
   and the feedback link: put `VITE_BOT_USERNAME=...` into `frontend/.env.development.local`
   (git-ignored; `frontend/.env.production` for builds).
3. Start a tunnel to the Vite server, e.g. `cloudflared tunnel --url http://localhost:5180`
   or `ngrok http 5180`, and set `WEBAPP_URL` to the HTTPS address it prints
   (also use it as the Mini App URL in BotFather).
4. Run the bot: `cd backend && .venv/Scripts/python -m app.bot`, then send `/start` to it.
   The same process sends the daily reminders (TZ 8.5), so keep it running.

The Vite server proxies `/api` to the backend, so one tunnel is enough.

Optional bot settings in @BotFather:

- `/setinline` turns on inline mode. Telegram 8.0+ shares results as a prepared message
  with an "Open the app" button; with inline mode on, older clients get the same message
  through the bot (TZ 8.11). Without it they fall back to Telegram's plain share link.
- Feedback: set `FEEDBACK_CHAT_ID` in `.env` to a private team group with the bot in it;
  everything users write to the bot is forwarded there with an internal user id only
  (no names or usernames, TZ 11.2).

## Admin panel

Content, moderation, statistics and the audit log (TZ 8.12) live at **/admin/**
(locally http://localhost:5180/admin/). Sign-in is a login and password plus a code from an
authenticator app (Google Authenticator, Authy, 2FAS...); the app is connected on the first sign-in.

- **Administrator**: everything. **Content editor**: content and the daily schedule only.
- Local development: `python -m app.seed --demo` creates a test admin (login `admin`, password
  in `backend/app/seed.py`; only with `ENV=dev`).
- Production: create the first administrator on the server (the password is asked at a hidden
  prompt), then add the team in the panel under "Adminlar":

  ```bash
  cd backend && .venv/Scripts/python -m app.admin_cli create --login ali --name "Ali" --role admin
  ```

- Lost phone: another administrator presses "2FA ni tiklash", or
  `python -m app.admin_cli reset-2fa --login ali`.
- Five wrong passwords or codes lock an account for 15 minutes; every admin action is written
  to the audit log.
- The admin page is a separate build entry (`frontend/admin/index.html`), so the Mini App
  never loads its code. A web server must answer `/admin/*` with `dist/admin/index.html`.

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
