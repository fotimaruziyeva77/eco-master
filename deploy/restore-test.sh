#!/bin/sh
# Monthly restore check (TZ 11.1): restores the newest backup into a scratch database,
# counts the users and drops it again. The live database is not touched.
#   sh deploy/restore-test.sh
set -eu
cd "$(dirname "$0")"
run() { docker compose exec -T backup "$@"; }

latest=$(run sh -c 'ls -1t /backups/ekoustoz-*.dump | head -n 1')
echo "Checking $latest"
run dropdb --if-exists restore_check
run createdb restore_check
run pg_restore --no-owner --exit-on-error -d restore_check "$latest"
run psql -d restore_check -tAc "select 'users: ' || count(*) from users"
run dropdb restore_check
echo "Restore check passed"
