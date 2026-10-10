#!/bin/sh
# Daily database backup at 03:00 Tashkent time, kept for KEEP_DAYS days (TZ 11.1).
# Runs inside the "backup" service; the files appear in deploy/backups on the server.
# One backup right away, e.g. before an update:
#   docker compose exec backup sh /usr/local/bin/backup.sh now
set -eu
KEEP_DAYS="${KEEP_DAYS:-14}"
# The dumps hold user data: readable by root only.
umask 077

dump() {
    file="/backups/ekoustoz-$(date -u +%Y%m%d-%H%M%S).dump"
    if pg_dump --format=custom --file="$file.part"; then
        mv "$file.part" "$file"
        echo "backup: saved $file ($(du -h "$file" | cut -f1))"
    else
        rm -f "$file.part"
        echo "backup: FAILED" >&2
        return 1
    fi
}

if [ "${1:-}" = "now" ]; then
    dump
    exit
fi

while true; do
    now=$(date -u +%s)
    # 03:00 in Tashkent is 22:00 UTC.
    next=$(date -u -d "$(date -u +%Y-%m-%d) 22:00:00" +%s)
    if [ "$next" -le "$now" ]; then
        next=$((next + 86400))
    fi
    sleep $((next - now))

    dump || true
    find /backups -name 'ekoustoz-*.dump' -mtime +"$KEEP_DAYS" -delete
done
