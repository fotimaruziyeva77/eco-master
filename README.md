# Eco-Master

Telegram Mini App that teaches children and adults to sort waste and give it a second life.
Specification: [docs/Eco-Master_TZ_v0.4.docx](docs/Eco-Master_TZ_v0.4.docx); earlier versions
(working name Ekoustoz) stay in `docs/` for history. Bot: [@eco_master_bot](https://t.me/eco_master_bot).
Logo and icons: `docs/brand/`. Internal names (database, packages, storage keys) still say
`ekoustoz`: nobody sees them, and renaming them would break existing data.

| Part | Stack | Folder |
|---|---|---|
| API, bot, admin | Python 3.13, FastAPI, SQLAlchemy 2 (async), Alembic, aiogram 3 | `backend/` |
| Mini App | React 19, TypeScript, Vite, i18next | `frontend/` |
| Database | PostgreSQL 17 (Docker) | `docker-compose.yml` |
| Production | Docker Compose, Caddy (HTTPS), daily backups | `deploy/` |

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
.venv/Scripts/python -m app.seed --content              # version 1 content for review (docs/content)
.venv/Scripts/python -m uvicorn app.main:app --port 8090    # restart after backend changes

cd ../frontend
npm install
npm run dev                       # http://localhost:5180
```

Uploading videos in the admin panel needs ffmpeg on the PATH (`winget install Gyan.FFmpeg`,
`apt install ffmpeg`); pictures work without it. Uploaded files go to `backend/media/`.

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

**Icons.** Emoji are drawn as pictures from Microsoft Fluent Emoji (flat style, MIT license),
not with the phone's emoji font, so they look the same on every phone. `npm run dev` and
`npm run build` write them to `frontend/public/emoji/` from the `@iconify-json/fluent-emoji-flat`
package (`frontend/scripts/emoji.mjs`); an emoji the set lacks shows as the phone's own. Badges
are drawn as medals around their emoji.

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

- **Administrator**: everything. **Content editor**: content, the daily schedule and market
  moderation. **Handover point staff**: only the handover desk of their point (see Market).
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
- **Pictures and videos are uploaded from the computer**, not linked from other sites. A picture
  (JPG, PNG, WebP up to 15 MB) is redrawn without camera data and saved as WebP at once; game
  item pictures keep a transparent background. A video (MP4, MOV and the like, up to 3 minutes and
  500 MB) is converted on the server by ffmpeg into an H.264 MP4 of at most 1280 px that every
  phone plays, without metadata such as the place it was filmed; the cover picture is taken from
  it. That takes a minute or two, one video at a time. Files live in `MEDIA_DIR`
  (`deploy/media` on the server), not in the database; their names are hashes of the files.
- The admin page is a separate build entry (`frontend/admin/index.html`), so the Mini App
  never loads its code. A web server must answer `/admin/*` with `dist/admin/index.html`.

## Market (phase 9)

Children show things they made from waste, or give away things they no longer need. Added on
the project lead's decision on 2026-10-10 and specified in TZ v0.3, section 8.13. TZ v0.2
(sections 11.3 and 16) had left photo uploads and a market for a later version because of
moderation and children's privacy, so the design below keeps those risks small. Photo uploads
belong in the lawyer's review (TZ 11.4).

- **Moderation first.** A new or changed listing is seen by nobody but its author until an
  administrator or content editor approves it (admin panel → "E'lonlar moderatsiyasi").
  Rejections carry a reason that the child gets from the bot in their language. Three reports
  from different users take a listing down until a moderator decides.
- **No contacts.** Only nicknames are shown; there is no chat. Phone numbers, @usernames and
  links in titles or descriptions are refused, so are words from the profanity list.
- **Photos.** 1–3 per listing, shrunk on the phone, then decoded and re-encoded on the server
  (WebP, at most 1280 px), so no GPS position or camera data is stored. They live in PostgreSQL
  (`listing_photos`), so backups, restores and account deletion cover them. They are served
  through signed, expiring links (`/api/media/...`): photos of listings not in the market open
  only for their author and moderators.
- **Handover only at a point.** "Handover points" (schools, eco-centres) are content in the
  admin panel. When the owner agrees to give an item away, both children get six-digit codes;
  the owner brings the item and says their code, the new owner collects it with theirs.
  Children never meet. Staff of a point get an admin account with the role "Topshirish joyi
  xodimi" and see only their point's desk ("Topshirish pulti"). Items not brought within
  7 days, or not collected within 14, are released automatically (the bot process does this).
- **No points** for listings (project lead's decision); "Zo'r!" likes only.
- Limits: 3 listings in review and 5 new listings a day per child, 3 open requests at a time.

## Production

Everything runs with Docker Compose on one Linux server (`deploy/`): PostgreSQL, the API,
the bot (long polling, also sends reminders), Caddy (Mini App, admin panel, automatic HTTPS
from Let's Encrypt) and a daily database backup. Sized for TZ 13: up to 5,000 users and
500 daily users; the API is stateless apart from in-memory rate limits.

1. A server with Docker, a domain whose DNS A record points to it, ports 80 and 443 open.
2. Settings — fill in the secrets yourself, never share them in chats:

   ```bash
   cp deploy/.env.example deploy/.env
   ```

3. Start (the API writes uploaded pictures and videos to `deploy/media` as user 10001):

   ```bash
   cd deploy && mkdir -p media && chown 10001:10001 media
   docker compose up -d --build
   ```

   Updating later: make a backup (below), `git pull`, the same command again. The API applies
   new database migrations itself on start.

4. Reference data, content drafts for review and the first administrator:

   ```bash
   docker compose exec api python -m app.seed --content
   docker compose exec api python -m app.admin_cli create --login ali --name "Ali" --role admin
   ```

   `--demo` would also publish the sample content right away — only after the team has
   reviewed it.
5. In @BotFather: `/newapp` with the URL `https://<DOMAIN>`, optionally `/setinline`.
   The bot sets its commands and menu button itself on start.

**A server that already runs nginx** (several sites on one machine, certbot for HTTPS):
the containers stay on `127.0.0.1:<port>`, a new nginx site points the domain there and certbot
adds the certificate; other sites are not touched. As root on the server:

```bash
git clone https://github.com/fotimaruziyeva77/eco-master.git /srv/eco-master
cd /srv/eco-master/deploy && sh install-behind-nginx.sh eco-master.sifatdev.uz 8130
```

The script fills in `deploy/.env` (secrets generated on the server; values already there, such
as a token added first, are kept) and stops until the bot token is there: add it yourself, for example from the project folder on your computer (the token is not shown):

```bash
grep '^BOT_TOKEN=' .env | ssh root@<server> "cat >> /srv/eco-master/deploy/.env"
```

Run the script again: it builds and starts everything, loads the content (sample content is
published right away; `SEED_ARGS=--content` keeps it as drafts), adds the nginx site, gets the
certificate and checks `https://<domain>/api/health`. The nginx site takes uploads of up to
600 MB (videos in the admin panel; Caddy keeps every other request to 20 MB); on a site made by an
older version of the script the update raises the old 10 MB limit itself. To update later: `git pull` and the same
command (it makes a backup first). Then create the first administrator and register the Mini App
in @BotFather as the script prints. Stop a bot started on a developer's computer with the same
token first: Telegram lets only one copy receive updates.

**Backups (TZ 11.1).** Every day at 03:00 Tashkent time into `deploy/backups/` (readable by
root only), kept for 14 days. Market photos are in the database too, so the dumps grow with the
market: keep an eye on the disk. Pictures and videos uploaded in the admin panel are files in
`deploy/media`; new ones are copied to `deploy/backups/media` with every backup (they never
change, so nothing is copied twice). To restore them, copy that folder back into `deploy/media`. Copy that folder to another machine or storage as well. A
backup right away, e.g. before an update, and the monthly check that the newest backup
restores (into a scratch database, the live one is not touched):

```bash
cd deploy && docker compose exec backup sh /usr/local/bin/backup.sh now
sh deploy/restore-test.sh
```

Restoring for real: `sh deploy/restore.sh deploy/backups/<file>.dump`. The backup goes into
a new database first and replaces the live one only if that worked; the old one is kept as
`ekoustoz_before_restore`. The API and the bot are stopped for the switch.

**Monitoring.** Point an uptime checker at `https://<DOMAIN>/api/health` (TZ 13: 99% a month).
`docker compose logs -f api bot` shows the logs; they contain internal ids only, no
initData, names or message texts (TZ 11.1).

**Security.** HTTPS with HSTS; Content-Security-Policy that allows only Telegram's script
and lets only Telegram Web frame the Mini App; the admin panel can not be framed at all.
Per-user request limit (TZ 11.1), admin sign-in with password + authenticator code and
lockout, secrets only in `deploy/.env`.

## Checks

```bash
cd backend && .venv/Scripts/python -m pytest && .venv/Scripts/ruff check .
cd frontend && npm run typecheck && npm test && npm run build && npm run size
npm run gen:api   # regenerate src/api/schema.ts after API changes (backend must be running)
```

GitHub Actions runs the same on every push (`.github/workflows/ci.yml`) and builds both
Docker images. `npm run size` fails when the first-load JavaScript goes over the TZ 13
budget of 250 KB (gzip). Acceptance criteria and how each is checked:
[docs/qa/QM-checklist.md](docs/qa/QM-checklist.md).

## Database migrations

```bash
cd backend
.venv/Scripts/alembic revision --autogenerate -m "describe change"
.venv/Scripts/alembic upgrade head
```

Tests use the separate `ekoustoz_test` database (created by `backend/scripts/create-test-db.sql`).
