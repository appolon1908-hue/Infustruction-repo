# Stage 6 Python 3.10 Compatibility and Resume Evidence

Captured: 2026-08-31 (America/Santo_Domingo)

Change: `CHG-20260831-STAGE6-PYTHON310-COMPAT-01`

## Source correction

- Keycloak PR: `appolon1908-hue/Keycloak#56`
- Exact approved PR head: `f387ed6d1d0fa8eda545c49a06fa302b61b9aa79`
- Squash merge SHA: `303e2edef2219c5eb3ac167c309a9717a766d079`
- Exact-head `validate-source`: PASS
- Exact-head `validate-merge-result`: PASS
- CODEOWNER approval after last push: PASS
- Unresolved review threads: 0
- Post-merge main CI run: `33345604265`, PASS
- Compatibility correction: `datetime.UTC` replaced by `timezone.utc`
- Python 3.10 dynamic source validation and reconciliation tests: PASS

## Rebuilt execution authority

- Old execution SHA: `56f1bc37857096c9378f72830079af1bb2291f30`
- New execution SHA: `f1d4da406a3c2ff34e54cb7bd7c4b2b1f8e7908c`
- Parent: `303e2edef2219c5eb3ac167c309a9717a766d079`
- Parent count: 1
- Execution payload is limited to `config/executions/stage6-intake-observability.v1.json`
- Infrastructure: `61787bd39515b775ba6b22c3e7af5862b44b3dad`
- Prometheus: `4230ec1c398db69e8ca95848135b13dd84e03c94`
- OpenBao: `2c199ee38ce372af4e0355c83e018f417e3afc8f`
- Middleware source: `f6748a58f8d2590520a4f28776770957061cdea1`
- Middleware digest: `sha256:695fa3ce3f50ba4d0ae0784976b946a0a683ca731155e4bd3bd9e90a4670b820`
- Prometheus target: pending
- Blackbox target: pending
- Production authorized: false
- External effects enabled: false

## Protected staging run

- Run: `33386709296`, attempt 1
- Source-lock verification: PASS
- Registry authentication: PASS
- Failed step: `Deploy the exact immutable Middleware digest privately`
- Failure: the `keycloak-deploy` runner identity lacks access to `/var/run/docker.sock`
- Runner groups: `keycloak-deploy` only
- Docker socket: mode `0660`, owner `root`, group `docker`
- Deployment reached: true (step entered)
- Middleware container started: false
- Keycloak mutation reached: false
- Tokens issued: false
- Evidence generated: false
- Rollback: PASS; no deployment objects existed to remove
- Raw token/client-secret files remaining: 0
- Stored GHCR auth entries remaining: 0

## Decision

`KEYCLOAK_PYTHON310_FIX=PASS`

`SOURCE_LOCK_VERIFICATION=PASS`

`STAGE6_MIDDLEWARE_STAGING=FAIL`

The mission is stopped at the explicit server-access condition. Do not rerun
until a separately reviewed operator change grants the self-hosted runner the
minimum Docker deployment authority and verifies that authority without
weakening socket or host security controls.

`PROMETHEUS_TARGET_STATE=pending`

`BLACKBOX_TARGET_STATE=pending`

`PRODUCTION_CHANGED=false`
