# PR #30: historical Stage 6-8 failed-certification rerun

Status: **HISTORICAL_EVIDENCE_ONLY_DO_NOT_DEPLOY**

This directory preserves the failed read-only rerun recorded at
`2026-08-31T02:17:02+02:00`. It is not a current source lock, a new runtime
read-back, or an authorization to execute a deployment or change production.

## Provenance

- Original PR: https://github.com/appolon1908-hue/Infustruction-repo/pull/30
- Original evidence commit: `0328efbbd55ea5de32d8f3e4aba8600afb8a68e1`
- Historical infrastructure evidence base: `b71f922a8d878a47c5a41f6b1cf9e8b47f9fba68`
- Conflict-resolution main: `99972268792554e70f756134b544c5e49eee5398`
- Conflict-resolution date: `2026-09-05`

The three snapshots below reuse the original Git blob objects without edits.
Statements such as "current", "this run", missing access, and required
remediation inside those snapshots refer to the historical rerun only.

| Snapshot | Original Git blob SHA |
| --- | --- |
| `RUNTIME-PREFLIGHT-INVENTORY.md` | `7e63d39311213eb92eae5d93350fb3072e9a7d0e` |
| `STAGE6-SOURCE-LOCK.yaml` | `1f5d8fbc0bc6722be35458a3d202fbc981fd6d2e` |
| `STAGE6-STAGING-CERTIFICATION.md` | `054f34ea818febcaa475d21cb6567f50d28bbae4` |

The original validator change remains available in the original evidence
commit and merge ancestry. It is not installed as the active validator because
it predates the later rollback and scoped-safety checks on main.

## Historical outcome retained

The rerun refreshed a 24-repository inventory, including Infrastructure. Its
complete application artifact set was incomplete: only Middleware, Odoo, and
n8n had reviewed immutable image digests, while Marketing, AI, Communication,
Social control, and Social runtime remained unresolved. The snapshot records
`SOURCE_LOCK=FAIL`, the then-global `LIVE_EMAIL_DELIVERY=true` finding,
`STAGING_CERTIFIED=NO`, and a prohibited production read-only canary.

No failure is changed to PASS in these historical snapshots. Their
`BACKUPS=FAIL` result means no backup was executed by that rerun; it must not
replace the separate verified backup evidence subsequently merged on main.

## Conflict-resolution authority

The active source lock, validators, deployment manifests, and CI workflows
are retained byte-for-byte from the conflict-resolution main commit, including:

- [Canonical source lock](../../../STAGE6-SOURCE-LOCK.yaml) and
  [source-lock validator](../../../scripts/validate_stage6_source_lock.py).
- [Runtime inventory](../../../RUNTIME-PREFLIGHT-INVENTORY.md),
  [staging certification](../../../STAGE6-STAGING-CERTIFICATION.md), and
  [separate backup evidence](../../../STAGE6-BACKUP-EVIDENCE.md).
- [Staging plan](../../../releases/STAGE6-STAGING-DEPLOYMENT-PLAN-2026-08-30.yaml)
  and [staging-plan validator](../../../scripts/validate_stage6_staging_plan.py).

Main's later lock retains repository rollback SHAs and digests, reconciled
repository/workload identities, the Keycloak merge-56 revision, and effective
denial plus negative-read-back checks. Its approved scope covers 22 Stage 6
workloads on `65.109.65.169`; Klyrow/Postal on `37.27.128.39` remains
`OUT_OF_SCOPE_ACTIVE_PRODUCTION_DO_NOT_TOUCH`. The historical instructions to
disable that separate production email path are not a current authorization.

The active lock's scoped `SOURCE_LOCK=PASS` does not certify every application
artifact or runtime safety. It still reports
`STAGE6_PREFLIGHT=FAIL_SCOPED_RUNTIME_READBACK` and
`STAGE6_PATH_BUSINESS_WRITES=NOT_PROVEN_DISABLED`; runtime reconciliation and
production mutation remain unauthorized. The scope distinction is documented
in [the source-lock remediation evidence](../STAGE6-SOURCE-LOCK-REMEDIATION-EVIDENCE.md).

This resolution preserves historical evidence. It does not replace main's
current lock with the older snapshot, remove newer checks, refresh runtime
claims, enable external delivery, or authorize deployment.

## Exact historical Git-SHA secret-scan exception

The source-authority workflow scans the complete source tree, including these
snapshots. The canonical lock already has a path-scoped exception for its
Keycloak Git-SHA field. Archiving the historical lock does not move or broaden
that existing exception.

The sole configuration change is an additional `.gitleaks.toml` exception
requiring BOTH this exact archived lock path AND a whole-line match for the
historical `keycloak_locked_sha` value
`80fc33c7159440e357219903f62ea7fb84914d59`. That value was independently
read back as the signed Keycloak merge-48 Git commit:
https://github.com/appolon1908-hue/Keycloak/commit/80fc33c7159440e357219903f62ea7fb84914d59

Default secret-detection rules and both exact-source and merge-result scans
remain enabled. No directory, arbitrary hash, other field, or credential is
excluded by the new exception. The historical snapshots remain byte-identical.
Local TOML parsing and eight negative path/value/field matching cases passed.
