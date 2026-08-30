# Stage 6 Staging Certification

Timestamp: 2026-08-31 (Europe/Berlin)

## Decision

`STAGING_CERTIFIED=NO`

Promotion stopped during the mandatory read-only preflight. No deployment,
restart, migration, backup, identity apply, gateway apply, workflow activation,
failure injection, rollback, or production canary was performed by this run.

## Fail-closed blockers

1. `klyrow-gateway-1`, `klyrow-smtp-relay-1`, and `klyrow-worker-1` report
   `LIVE_EMAIL_DELIVERY=true` on `37.27.128.39`. Public SMTP port 25 is active.
   Production business writes therefore cannot be certified disabled.
2. The documented observability/security server instead runs production email,
   SMS/billing, crawler, and provider-integration workloads. OpenBao, Loki,
   Tempo, Alloy, cAdvisor, Redis Exporter, Blackbox Exporter, and Superset are
   absent from the running container set.
3. General-purpose shell access to core/staging server `65.109.65.169` is
   unavailable. A bounded forced-command key can report only provider-credential
   state and cannot produce the mandatory fresh runtime inventory.
4. The current protected-main source lock authorizes backup preparation only.
   The backup-gate candidate remains unmerged and was not executed.

The previous source lock remains valid as Git evidence. Every downstream gate
is `FAIL` here because it was not safely executable or certifiable after the
preflight stop; this does not claim that a runtime mutation was attempted.

```text
SOURCE_LOCK=PASS
BACKUPS=FAIL
STAGING_DEPLOYMENT=FAIL
OPENBAO_BINDING=FAIL
KEYCLOAK_CERTIFICATION=FAIL
MIGRATIONS=FAIL
APPLICATION_HEALTH=FAIL
KONG_CERTIFICATION=FAIL
N8N_BINDINGS=FAIL
OBSERVABILITY=FAIL
E2E_STAGING=FAIL
FAILURE_TESTS=FAIL
ROLLBACK=FAIL
STAGING_CERTIFIED=NO
PRODUCTION_READ_ONLY_CANARY=FAIL

PRODUCTION_BUSINESS_WRITES=NOT_PROVEN_DISABLED
```

Required remediation is to disable and independently read back the production
email-delivery path, provide an authorized core-server inventory shell, and then
restart from Phase 0. Do not infer `DISABLED` from missing settings.
