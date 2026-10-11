#!/bin/sh
# Install or update Eco-Master on a server whose nginx already serves other sites.
# Run as root from this folder of a clone of the repository:
#
#   sh install-behind-nginx.sh eco-master.example.uz 8130
#
# The domain's DNS A record must point to this server. Steps: settings (secrets are generated
# here and never printed) → backup before an update → containers → content → nginx site →
# HTTPS certificate → check. Other sites are not touched; running it again updates the app.
set -eu

DOMAIN="${1:?usage: sh install-behind-nginx.sh <domain> [port]}"
PORT="${2:-8130}"
BOT_USERNAME="${BOT_USERNAME:-eco_master_bot}"
# Sample content published right away (for testing); SEED_ARGS=--content leaves only drafts.
SEED_ARGS="${SEED_ARGS:---demo --content}"
SITE="/etc/nginx/sites-available/$DOMAIN"
cd "$(dirname "$0")"

say() { printf '\n== %s\n' "$*"; }

say "Checks"
for tool in docker nginx certbot openssl curl; do
    command -v "$tool" >/dev/null || { echo "$tool is not installed"; exit 1; }
done
docker compose version

say "Settings: $(pwd)/.env"
# Missing settings are added (secrets generated here, never printed); existing values,
# such as a bot token added by hand, are never changed. Readable by root only.
touch .env
chmod 600 .env
add() { grep -q "^$1=" .env || printf '%s=%s\n' "$1" "$2" >> .env; }
add COMPOSE_FILE docker-compose.yml:docker-compose.behind-proxy.yml
add DOMAIN "$DOMAIN"
add WEB_PORT "$PORT"
add POSTGRES_PASSWORD "$(openssl rand -hex 24)"
add JWT_SECRET "$(openssl rand -hex 32)"
add BOT_USERNAME "$BOT_USERNAME"
add WEBAPP_SHORT_NAME app
add FEEDBACK_CHAT_ID ""
if ! grep -q '^BOT_TOKEN=.' .env; then
    echo
    echo "The bot token is missing. Add the line BOT_TOKEN=<token from @BotFather> to"
    echo "  $(pwd)/.env"
    echo "and run this script again."
    exit 1
fi

if [ -n "$(docker compose ps -q db 2>/dev/null)" ]; then
    say "Backup before the update"
    docker compose exec -T backup sh /usr/local/bin/backup.sh now
fi

say "Containers (the first build takes a few minutes)"
docker compose up -d --build

say "Waiting for the API on 127.0.0.1:$PORT"
ok=""
for _ in $(seq 1 60); do
    if curl -fsS "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
        ok=1
        break
    fi
    sleep 3
done
[ -n "$ok" ] || { echo "The API did not start; see: docker compose logs api"; exit 1; }

say "Reference data and content ($SEED_ARGS)"
# shellcheck disable=SC2086
docker compose exec -T api python -m app.seed $SEED_ARGS

if [ ! -e "/etc/nginx/sites-enabled/$DOMAIN" ]; then
    say "nginx site $DOMAIN → 127.0.0.1:$PORT"
    sed -e "s/DOMAIN_NAME/$DOMAIN/" -e "s/WEB_PORT/$PORT/" nginx-site.conf > "$SITE"
    ln -s "$SITE" "/etc/nginx/sites-enabled/$DOMAIN"
    if ! nginx -t; then
        # Never leave nginx with a broken configuration: the other sites depend on it.
        rm -f "/etc/nginx/sites-enabled/$DOMAIN" "$SITE"
        echo "nginx rejected the new site; it was removed again. Nothing else was changed."
        exit 1
    fi
    systemctl reload nginx
fi

if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    say "HTTPS certificate (Let's Encrypt, certbot's existing account)"
    certbot --nginx -d "$DOMAIN" --redirect --non-interactive
fi

say "Check"
curl -fsS "https://$DOMAIN/api/health" && echo
docker compose ps

cat <<EOF

Ready: https://$DOMAIN  (admin panel: https://$DOMAIN/admin/)

Next steps:
1. First administrator (asks for a password at a hidden prompt):
     docker compose exec api python -m app.admin_cli create --login <login> --name "<name>" --role admin
2. @BotFather → /newapp → @$BOT_USERNAME → Web App URL: https://$DOMAIN , short name: app
3. Update later: git pull && sh install-behind-nginx.sh $DOMAIN $PORT
EOF
