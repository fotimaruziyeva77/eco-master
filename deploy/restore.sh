#!/bin/sh
# Restore a backup into the live database:
#   sh deploy/restore.sh deploy/backups/ekoustoz-YYYYMMDD-HHMMSS.dump
# The file must be in deploy/backups. It is restored into a new database first; only when
# that succeeds does it replace the live one, which is kept as ekoustoz_before_restore.
# The API and the bot are stopped for the switch.
set -eu
name=$(basename "$1")
cd "$(dirname "$0")"
run() { docker compose exec -T backup "$@"; }

run test -f "/backups/$name" || { echo "No such file: deploy/backups/$name" >&2; exit 1; }
run dropdb --if-exists ekoustoz_restore
run createdb ekoustoz_restore
run pg_restore --no-owner --exit-on-error -d ekoustoz_restore "/backups/$name"

docker compose stop api bot
run dropdb --if-exists ekoustoz_before_restore
run psql -d postgres -v ON_ERROR_STOP=1 \
    -c "alter database ekoustoz rename to ekoustoz_before_restore" \
    -c "alter database ekoustoz_restore rename to ekoustoz"
docker compose start api bot

echo "Restored $name. The previous database is kept; once all is well, remove it with:"
echo "  docker compose exec backup dropdb ekoustoz_before_restore"
