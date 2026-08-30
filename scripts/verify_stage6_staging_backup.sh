#!/usr/bin/env bash
set -Eeuo pipefail

backup="${1:-}"
[[ "$backup" == /opt/codestra/backups/stage6-staging/* ]] || {
  printf 'STAGE6_BACKUP_VERIFY_ERROR=invalid backup path\n' >&2
  exit 1
}
[[ -d "$backup" && ! -L "$backup" ]] || exit 1
[[ "$(stat -c '%a' "$backup")" == 700 ]] || exit 1
(
  cd "$backup"
  sha256sum -c SHA256SUMS >/dev/null
)
for dump in "$backup"/databases/*.dump; do
  pg_restore --list "$dump" >/dev/null
done
for archive in "$backup"/volumes/*.tar "$backup"/config/*.tar; do
  tar -tf "$archive" >/dev/null
done
grep -qx 'SECRET_VALUES_COPIED=NO' "$backup/MANIFEST"
grep -qx 'RUNTIME_RESTARTED=NO' "$backup/MANIFEST"
grep -qx 'PRODUCTION_TOUCHED=NO' "$backup/MANIFEST"
printf 'BACKUP_CHECKSUMS=PASS\n'
printf 'DATABASE_ARCHIVES=READABLE\n'
printf 'VOLUME_ARCHIVES=READABLE\n'
printf 'STAGE6_BACKUP_VERIFY=PASS\n'
