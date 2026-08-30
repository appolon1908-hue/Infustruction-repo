# Stage 6 Runtime Reconciliation Decision

Timestamp: 2026-08-30 (America/Santo_Domingo)

## Decision

`SOURCE_LOCK=FAIL`

`STAGE6_PREFLIGHT=FAIL`

The reconciliation stopped fail-closed before backup or runtime mutation. No
container was replaced or restarted, no database was changed, and no production
deployment or external-write activation occurred.

## Established inventory

The companion CSV records all 101 containers observed on the host, including
classification, image reference and local image ID, discovered Git revision,
environment, Compose service and file paths, configuration authority, mounted
secret-source paths, current rollback image, startup command, and explicit
safety-state read-back.

Classification totals:

- Codestra release workload: 22
- observability/security workload: 24
- provider workload: 7
- legacy workload: 47
- unrelated workload: 0
- unknown: 1

The unknown workload is `private-integration-gateway-1`. It was not modified.
Production and legacy workloads were inventory-only and were not modified.

## Blocking drift

1. No `STAGE6-SOURCE-LOCK.yaml` exists in the infrastructure authority. The
   available exact-source-lock JSON contains repository SHAs but no immutable
   application image digests.
2. The available lock specifies Kong SHA
   `344684872fd9737efe7841a773288a703a1dcb3a`, while the original release
   authority identified merged Kong release point
   `186630b40c19d72aa9bdf9ef1f64e8a17bd0e33e`. Selecting either without a new
   reviewed lock would silently reinterpret release authority.
3. Of 22 classified staging release containers, only 13 have digest-pinned image
   references and only 3 expose an established Git revision. Vendor database and
   Redis images are pinned, but their Git-controlled Compose provenance is not
   established on the host.
4. All 17 safety-applicable staging release containers fail the complete explicit
   safety-set read-back. The five remaining release containers are PostgreSQL or
   Redis and were correctly treated as infrastructure to which business-write
   switches do not apply.
5. `codestra-middleware-staging-middleware-staging-1` runs
   `alembic upgrade head` in normal application startup.
6. `codestra-odoo19-staging-odoo19-master-staging-1` and
   `codestra-odoo19-staging-odoo19-staging-1` run module `--init` operations in
   normal application startup.
7. The source lock includes Marketing, AI, Communication, Social Control and
   Social Runtime, but no corresponding unambiguous Stage 6 staging release
   workloads were identifiable among the 101 running containers.
8. No reviewed digest-pinned replacement artifact and complete per-service
   rollback mapping exists for all affected staging workloads. Building or
   selecting replacements automatically would violate the source-lock gate.

## Proposed reconciliation sequence after authority is repaired

1. Review and merge one `STAGE6-SOURCE-LOCK.yaml` containing every repository
   SHA and deployable image digest, resolving the Kong revision conflict.
2. Record Git provenance for every staging Compose/configuration tree and bind
   each workload to its component lock entry.
3. Add capability-scoped fail-closed variables to application/workflow/provider
   workloads; do not add them to PostgreSQL, Redis, or observability exporters.
4. Add a dedicated Middleware one-shot Alembic service and change the API command
   to application-only startup.
5. Add dedicated Odoo one-shot module install/upgrade services and remove
   `--init`/`--update` from long-running Odoo services.
6. Verify rollback images and commands, then back up each affected staging
   database and configuration and verify checksums/restorability.
7. Reconcile only staging, one dependency tier at a time, with health/read-back
   and rollback readiness after each service.
8. Re-capture this inventory and require zero unresolved provenance, digest,
   startup-migration, and applicable safety drift before OpenBao work resumes.

## Safety outcome

Observed switches that were present were false/disabled, but missing switches
remain ambiguous and therefore do not certify the runtime. This run made no
production business write and did not enable any external write capability.

```text
SOURCE_LOCK=FAIL
STAGE6_PREFLIGHT=FAIL
PRODUCTION_BUSINESS_WRITES=DISABLED
```
