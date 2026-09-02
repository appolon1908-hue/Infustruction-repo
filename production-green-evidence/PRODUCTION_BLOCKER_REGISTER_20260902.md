# Production blocker register — 2026-09-02

| ID | Severity | Scope | Blocker | Acceptance test | External |
|---|---|---|---|---|---|
| P0-01 | CRITICAL | 15 workloads | Runtime identity/digest/revision attribution is 0/15 | sanctioned inventory plus ingress/internal GET evidence matches protected SHAs and digests | yes: authorized SSH/runtime identity |
| P0-02 | CRITICAL | platform | Staging end-to-end release and rollback rehearsal absent | exact protected release deployed to isolated staging; rollback PASS | yes: staging authority |
| P0-03 | CRITICAL | stateful workloads | Fresh isolated restores are incomplete, including Keycloak | checksum-bound fresh backups restored to isolated empty targets | yes: backup/restore credentials and hosts |
| P0-04 | CRITICAL | Klyrow | Restricted operator PRs unmerged; server key rejected | PRs 66/58 merged and exact restricted preflight/deploy evidence PASS | yes: CODEOWNER and SSH/root authority |
| P1-01 | HIGH | 15 workloads | Canonical operational endpoint runtime coverage is 1/0/0/0 | health/ready/version/capabilities each 15/15 | partly |
| P1-02 | HIGH | APIs | Canonical business route/OpenAPI/Kong/Caddy/frontend/SDK alignment is unmeasured | generated route inventory and drift CI PASS for every API service | no |
| P1-03 | HIGH | source lock | Deployed immutable digests and rollback tuples are unknown | protected merge/image/SBOM/provenance/runtime tuple recorded for all deployables | partly |
| P1-04 | HIGH | migrations | Database upgrade/rollback/runtime heads are not fully certified | one-shot migration rehearsals and post-migration readiness PASS | partly |
| P1-05 | HIGH | production | Backup, staging, observability and attribution prerequisites prevent deployment | every production gate in release record PASS | yes |
| P2-01 | MEDIUM | Marketing | Off-host TLS failure blocks all runtime probes | valid TLS and attributable GET endpoints | yes: off-host owner/DNS/TLS |
| P2-02 | MEDIUM | social runtime | operational endpoints redirect to authentication | approved internal authenticated evidence path returns attributable status | yes: off-host access |

`CRITICAL_BLOCKERS=4`

`HIGH_BLOCKERS=5`

`MEDIUM_BLOCKERS=2`

`PRODUCTION_BUSINESS_WRITES_ENABLED=NO`
