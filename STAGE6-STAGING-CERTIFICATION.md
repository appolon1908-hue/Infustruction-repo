# Stage 6 Staging Certification

Timestamp: 2026-08-30 (America/Santo_Domingo)

## Decision

`STAGING_CERTIFIED=NO`

Promotion stopped during Phase 0 preflight. No deployment, restart, migration,
identity apply, gateway apply, workflow activation, failure injection, rollback,
or production canary was performed by this certification run.

## Fail-closed blockers

1. The inspected host had 101 running containers. Zero containers exposed the
   complete required safety-state set. Only 44 exposed at least one required
   switch. Missing switches are ambiguous and therefore fail the mandatory
   safety gate.
2. Multiple application workloads use mutable image tags, lack a Git revision
   label, report an unknown revision, or combine those conditions. The running
   release cannot be tied completely to reviewed Git and immutable deployment
   identities.
3. The staging middleware application command runs `alembic upgrade head`
   during normal application startup. Two staging Odoo processes use `--init`
   during normal startup. This violates the dedicated one-shot migration gate.
4. The checked-out infrastructure worktree already contained unrelated modified
   files. They were preserved and were not included in this evidence.

## Observed safe values

Where the inspected containers exposed delivery/dialing controls, the observed
values were false or disabled. This is not sufficient to pass because the
required advertising, social publishing, external-model, provider-write,
workflow-provider-write, and call-count controls were absent from effective
configuration across the runtime.

## Required remediation before a new run

- Define and expose the complete fail-closed safety contract for every relevant
  staging and production workload, including an authoritative `CALLS_PLACED=0`
  read-back.
- Replace mutable/unknown application identities with images pinned by digest
  and labeled with exact reviewed repository SHAs.
- Remove schema migration and Odoo module initialization from normal startup;
  execute them only as backed-up, recorded one-shot jobs.
- Re-run Phase 0 inventory and complete the source lock before any staging
  mutation.

## Gate status

```text
SOURCE_LOCK=FAIL
STAGING_DEPLOYMENT=FAIL
OPENBAO_BINDING=FAIL
KEYCLOAK_CERTIFICATION=FAIL
MIGRATIONS=FAIL
APPLICATION_HEALTH=FAIL
KONG_CERTIFICATION=FAIL
N8N_BINDINGS=FAIL
OBSERVABILITY=FAIL
E2E_STAGING=FAIL
ROLLBACK=FAIL
PRODUCTION_READ_ONLY_CANARY=FAIL

PRODUCTION_BUSINESS_WRITES=DISABLED
```

`FAIL` after the Phase 0 stop means not certified/not executed, not that a
mutation was attempted and failed.
