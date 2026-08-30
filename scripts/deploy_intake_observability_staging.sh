#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deploy/staging/intake-observability/compose.yaml"
LOCK_FILE="$ROOT_DIR/deploy/staging/intake-observability/runtime-lock.v1.json"
ACTION="${1:-deploy}"
STATE_ROOT="${CODESTRA_STAGING_ROOT:-$HOME/.local/share/codestra/staging/intake-observability}"
EXPECTED_IMAGE='ghcr.io/appolon1908-hue/codestra-middleware@sha256:695fa3ce3f50ba4d0ae0784976b946a0a683ca731155e4bd3bd9e90a4670b820'
EXPECTED_DIGEST='sha256:695fa3ce3f50ba4d0ae0784976b946a0a683ca731155e4bd3bd9e90a4670b820'
EXPECTED_SOURCE='f6748a58f8d2590520a4f28776770957061cdea1'
PROJECT='codestra-intake-observability-staging'

fail() { printf 'STAGING_DEPLOYMENT=FAIL %s\n' "$*" >&2; exit 1; }
require() { command -v "$1" >/dev/null 2>&1 || fail "missing command: $1"; }
compose() { docker compose --project-name "$PROJECT" --env-file "$STATE_ROOT/deployment.env" -f "$COMPOSE_FILE" "$@"; }

for command in docker python3 jq sha256sum; do require "$command"; done
docker compose version >/dev/null
[[ "$STATE_ROOT" == /* ]] || fail 'CODESTRA_STAGING_ROOT must be an absolute path'
[[ "$STATE_ROOT" != / && "$STATE_ROOT" != /etc && "$STATE_ROOT" != /opt && "$STATE_ROOT" != /srv ]] || fail 'unsafe staging root'

mkdir -p "$STATE_ROOT" "$STATE_ROOT/secrets" "$STATE_ROOT/evidence" "$STATE_ROOT/state"
chmod 700 "$STATE_ROOT" "$STATE_ROOT/secrets" "$STATE_ROOT/evidence" "$STATE_ROOT/state"

case "$ACTION" in
  render)
    jq -e --arg image "$EXPECTED_IMAGE" --arg digest "$EXPECTED_DIGEST" --arg source "$EXPECTED_SOURCE" \
      '.environment == "staging" and .middleware.image_reference == $image and .middleware.image_digest == $digest and .middleware.source_sha == $source and .activation.prometheus_target == "pending" and .activation.blackbox_target == "pending" and .external_effects_enabled == false' \
      "$LOCK_FILE" >/dev/null
    printf 'STAGING_RUNTIME_LOCK=PASS\n'
    exit 0
    ;;
  status)
    [[ -f "$STATE_ROOT/deployment.env" ]] || fail 'deployment state is absent'
    compose ps
    exit 0
    ;;
  rollback)
    [[ -f "$STATE_ROOT/deployment.env" ]] || fail 'deployment state is absent'
    compose down --volumes --remove-orphans
    rm -f "$STATE_ROOT/runtime-context.json"
    printf 'STAGING_ROLLBACK=PASS\n'
    exit 0
    ;;
  deploy) ;;
  *) fail "unsupported action: $ACTION" ;;
esac

: "${KEYCLOAK_PUBLIC_URL:?KEYCLOAK_PUBLIC_URL is required}"
: "${KEYCLOAK_REALM:?KEYCLOAK_REALM is required}"
[[ "$KEYCLOAK_PUBLIC_URL" == https://* ]] || fail 'Keycloak public URL must be HTTPS'
[[ "$KEYCLOAK_PUBLIC_URL" != *production* && "$KEYCLOAK_PUBLIC_URL" != *prod.* ]] || fail 'production Keycloak URL is prohibited'

for secret in postgres_password redis_password; do
  path="$STATE_ROOT/secrets/$secret"
  if [[ ! -s "$path" ]]; then
    python3 - <<'PY' >"$path"
import secrets
print(secrets.token_hex(32))
PY
  fi
  [[ ! -L "$path" ]] || fail "secret path is a symlink: $path"
  chmod 600 "$path"
done
postgres_password="$(cat "$STATE_ROOT/secrets/postgres_password")"
redis_password="$(cat "$STATE_ROOT/secrets/redis_password")"

cat >"$STATE_ROOT/middleware.env" <<ENV
APP_ENV=staging
RUNTIME_PROFILE_ID=codestra-middleware-staging-intake-observability-v1
APP_VERSION=0.1.0
APP_SOURCE_SHA=$EXPECTED_SOURCE
IMAGE_DIGEST=$EXPECTED_DIGEST
SCHEMA_HEAD=0003_immutable_event_ledger
BUILD_TIME=2026-08-30T13:24:37Z
KEYCLOAK_ISSUER=${KEYCLOAK_PUBLIC_URL%/}/realms/$KEYCLOAK_REALM
KEYCLOAK_JWKS_URI=${KEYCLOAK_PUBLIC_URL%/}/realms/$KEYCLOAK_REALM/protocol/openid-connect/certs
MIDDLEWARE_AUDIENCE=middleware-api
JWKS_TIMEOUT_SECONDS=3
READINESS_TIMEOUT_SECONDS=3
DATABASE_URL=postgresql://middleware_staging:${postgres_password}@postgres:5432/codestra_middleware_staging
REDIS_URL=redis://:${redis_password}@redis:6379/14
ALLOW_IN_MEMORY_STORAGE=false
NATS_URL=
NATS_STREAM=CODESTRA_STAGING_EVENTS
NATS_SUBJECT_PREFIX=codestra.staging.events
NATS_CREDS_FILE=
NATS_DISPATCH_MODE=disabled
NATS_ALLOW_INSECURE_TEST_CONNECTION=false
TEMPORAL_ADDRESS=
TEMPORAL_NAMESPACE=codestra-staging
TEMPORAL_TASK_QUEUE=codestra-staging-critical
TEMPORAL_WORKER_MODE=disabled
TEMPORAL_SERVER_ROOT_CA_FILE=
TEMPORAL_CLIENT_CERT_FILE=
TEMPORAL_CLIENT_KEY_FILE=
TEMPORAL_TLS_SERVER_NAME=
TEMPORAL_ALLOW_INSECURE_TEST_CONNECTION=false
PRODUCTION_ACTIVATION_ID=
PRODUCTION_DIALING=DISABLED
OUTBOX_DISPATCH_ENABLED=false
SEND_EVENTS=false
ENABLE_EXTERNAL_DELIVERY=false
LIVE_WRITE=false
LIVE_WRITES=false
ODOO_WRITE=false
CALLBACK_DISPATCH=false
N8N_DELIVERY_ENABLED=false
VICIDIAL_WRITES_ENABLED=false
ENABLE_VICIDIAL_WRITES=false
EXTERNAL_DIAL_ENABLED=false
PRODUCTION_CALLBACKS_ENABLED=false
N8N_PRODUCTION_WORKFLOWS_ENABLED=false
FORM_ODOO_DELIVERY_ENABLED=false
CRAWLER_ODOO_DELIVERY_ENABLED=false
SCRAPPER_ODOO_DELIVERY_ENABLED=false
CRAWLER_EXTERNAL_CONTACT_ENABLED=false
SCRAPPER_EXTERNAL_CONTACT_ENABLED=false
SMS_DELIVERY_ENABLED=false
EMAIL_DELIVERY_ENABLED=false
LIVE_SMS_DELIVERY=false
LIVE_EMAIL_DELIVERY=false
LIVE_PSTN_DIALING=false
SOCIAL_DELIVERY_ENABLED=false
CRAWLER_EXECUTION_ENABLED=false
SCRAPPER_EXECUTION_ENABLED=false
UNRESTRICTED_CRAWLING=false
LIVE_CALL_CONTROL=false
GENERAL_AI_DIALING=false
ENV
chmod 600 "$STATE_ROOT/middleware.env"

cat >"$STATE_ROOT/deployment.env" <<ENV
MIDDLEWARE_ENV_FILE=$STATE_ROOT/middleware.env
POSTGRES_PASSWORD_FILE=$STATE_ROOT/secrets/postgres_password
REDIS_PASSWORD_FILE=$STATE_ROOT/secrets/redis_password
ENV
chmod 600 "$STATE_ROOT/deployment.env"
unset postgres_password redis_password

"$0" render

docker pull "$EXPECTED_IMAGE" >/dev/null
resolved="$(docker image inspect "$EXPECTED_IMAGE" --format '{{json .RepoDigests}}')"
printf '%s' "$resolved" | grep -Fq "$EXPECTED_IMAGE" || fail 'local Middleware image does not match locked digest'

rendered="$STATE_ROOT/state/compose.rendered.yaml"
compose config >"$rendered"
chmod 600 "$rendered"
if grep -Eq '^[[:space:]]+ports:' "$rendered"; then
  fail 'host ports are prohibited'
fi

rollback_on_error() {
  status=$?
  if [[ $status -ne 0 ]]; then
    compose logs --no-color --tail=200 >"$STATE_ROOT/state/failed-deployment.log" 2>&1 || true
    chmod 600 "$STATE_ROOT/state/failed-deployment.log" || true
    compose down --volumes --remove-orphans >/dev/null 2>&1 || true
  fi
  exit "$status"
}
trap rollback_on_error EXIT

compose down --volumes --remove-orphans >/dev/null 2>&1 || true
compose up -d postgres redis
compose run --rm middleware-migrate
compose up -d middleware

health=''
for _ in $(seq 1 60); do
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${PROJECT}-middleware-1" 2>/dev/null || true)"
  [[ "$health" == healthy ]] && break
  sleep 2
done
[[ "$health" == healthy ]] || fail 'Middleware did not become healthy'

network_internal="$(docker network inspect codestra-intake-observability-staging_private --format '{{.Internal}}')"
[[ "$network_internal" == true ]] || fail 'private network is not internal'
published="$(docker inspect --format '{{json .NetworkSettings.Ports}}' "${PROJECT}-middleware-1")"
[[ "$published" == '{"8080/tcp":null}' || "$published" == '{}' ]] || fail 'Middleware has a published port'

python3 - <<PY >"$STATE_ROOT/runtime-context.json"
import json
print(json.dumps({
  "schema_version": "1.0",
  "environment": "staging",
  "project": "$PROJECT",
  "middleware_source_sha": "$EXPECTED_SOURCE",
  "middleware_image_digest": "$EXPECTED_DIGEST",
  "middleware_container": "${PROJECT}-middleware-1",
  "private_network": "codestra-intake-observability-staging_private",
  "private_network_internal": True,
  "host_ports_published": False,
  "deployment_result": "PASS",
  "external_effects_enabled": False
}, sort_keys=True, separators=(",", ":")))
PY
chmod 600 "$STATE_ROOT/runtime-context.json"
trap - EXIT
printf 'STAGING_DEPLOYMENT=PASS\n'
printf 'STAGING_PROJECT=%s\n' "$PROJECT"
printf 'STAGING_PRIVATE_NETWORK=codestra-intake-observability-staging_private\n'
