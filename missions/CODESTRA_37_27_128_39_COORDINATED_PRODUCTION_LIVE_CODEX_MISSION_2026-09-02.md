# CODESTRA 37.27.128.39 — COORDINATED REPOSITORY-TO-PRODUCTION CODEX MISSION

```text
PHASE=CODESTRA_37_27_128_39_COORDINATED_REPOSITORY_RELEASE_SERVER_INTEGRATION_PRODUCTION_LIVE
MISSION_DATE=2026-09-02
TARGET_HOST=37.27.128.39
HOST_ROLE=CODESTRA_OBSERVABILITY_SECURITY_EMAIL_PROVIDER_HOST
PRIMARY_ADMIN_USERNAME=appolon
PRIMARY_ADMIN_EMAIL=appolon@codestra.co
COORDINATION_AUTHORITY=appolon1908-hue/Infustruction-repo
EXECUTION_MODE=CONTINUOUS_REMEDIATE_VALIDATE_RELEASE_DEPLOY_CERTIFY
BYPASS_USED=NONE
SSH_CONFIGURATION_CHANGES=FORBIDDEN
```

## 1. Objective

Complete the work, not merely the plan.

Starting from the current GitHub and runtime state, Codex must:

1. discover the current authoritative source, branches, pull requests, checks, releases, images, deployment manifests and runtime identities for every repository in scope;
2. reconcile overlapping or stale work into one authoritative production candidate per repository;
3. implement every missing production-critical source, test, API, deployment, integration, backup, restore, rollback and evidence requirement;
4. commit and push every logical source change to the owning repository;
5. drive each repository through exact-head validation, review resolution, protected merge and immutable release publication without weakening repository protections;
6. write the exact protected merge SHA, immutable image digest, configuration checksum, migration/schema identity and rollback digest into the central production BOM;
7. pull only those exact released identities to `37.27.128.39`;
8. deploy in dependency order with one-shot migrations, private networking, OpenBao-injected secrets, Keycloak identity, Caddy protection and no public native ports;
9. synchronize the observability host with the core application host, Middleware, Keycloak, Klyrow/Postal and every approved integration;
10. prove metrics, logs, traces, dashboards, alerts, durable delivery, backup, restore and rollback;
11. perform one bounded operational-alert firing transition and one matching resolved transition only after every preceding gate passes;
12. issue `OVERALL_VERDICT=PRODUCTION LIVE` only when all required gates are PASS.

Do not stop after inventory, documentation, branch creation, pull-request creation, CI failure, merge conflict, partial implementation, container startup, HTTP 200, or a provider acceptance response. Continue through implementation, correction, retest, release, deployment, read-back and certification.

## 2. Continuous execution and no-bypass policy

`NO STOP` means:

- do not stop at the first fixable failure;
- repair source defects in the owning repository, push the repair and rerun the failed gate;
- resolve merge conflicts against current protected base branches;
- update tests, generated contracts, manifests, runbooks and evidence with the code;
- continue independent workstreams while one workstream waits on CI or a genuinely external authority;
- roll back a failed component and continue repairing it without disturbing unrelated healthy services;
- preserve a resumable status ledger after every material action.

`NO BYPASS` means:

- no force-push to protected branches;
- no direct unreviewed edits to `main`, `production`, live Compose files or live databases;
- no disabling required checks, branch protection, signature checks, TLS verification, authentication, authorization, tenant isolation, backups, restore checks or rollback gates;
- no `latest`, `main`, mutable production tags, local-only images or branch checkouts in production;
- no `--no-verify`, skipped tests, fabricated PASS evidence or manual status overrides;
- no secret values in Git, logs, PRs, evidence, command history or chat;
- no Docker socket or Docker-group grant to application identities or `appolon`;
- no unrestricted sudo, unrestricted shell, new root SSH path or change to `sshd_config`;
- no direct n8n-to-provider bypass;
- no direct Alertmanager-to-SMTP normal route;
- no automatic repeat of an operation with an ambiguous provider outcome;
- no broad host restart, Docker prune, volume deletion, database reset or queue reset.

When a human security-owner input is genuinely required, mark only that gate `BLOCKED_EXTERNAL_AUTHORITY`, continue every independent workstream, preserve exact evidence, and never convert the blocked gate to PASS by assumption.

## 3. Scope and repository ownership

### 3.1 Primary observability and security repositories

| Component | Principal repository | Production responsibility |
|---|---|---|
| Prometheus | `appolon1908-hue/Codestra-Prometheus` | production targets, recording rules, SLOs, alerts, snapshots and restore |
| Grafana | `appolon1908-hue/Codestra-Grafana-` | protected portal, private datasources, dashboards and RBAC |
| Alertmanager | `appolon1908-hue/Codestra-Alertmanager` | grouping, inhibition, durable Middleware route and resolved notifications |
| Loki | `appolon1908-hue/Codestra-Loki` | tenant-bound structured logs, retention, compaction and restore |
| Tempo | `appolon1908-hue/Codestra-Tempo` | tenant-bound traces, retention, metrics generation and restore |
| OpenTelemetry | `appolon1908-hue/Codestra-Telemetry` | central metrics/logs/traces processing, redaction and export |
| Alloy | `appolon1908-hue/Codestra-Alloy` | host/container collection and private mTLS forwarding |
| Node Exporter | `appolon1908-hue/Codestra-Node-Exporter` | least-privilege host metrics |
| cAdvisor | `appolon1908-hue/Codestra-cAdvisor` | read-only container metrics |
| Redis Exporter | `appolon1908-hue/Codestra-Redis-Exporter` | aggregate read-only Redis metrics |
| PostgreSQL Exporter | `appolon1908-hue/Codestra-Postgres-Exporter` | aggregate least-privilege PostgreSQL metrics; no public hostname |
| Blackbox Exporter | `appolon1908-hue/Codestra-Blackbox-Exporter` | allowlisted HTTP, TCP, TLS, DNS and SMTP STARTTLS probes |
| Superset | `appolon1908-hue/Superset` | Keycloak-protected, tenant-restricted analytics |
| OpenBao | `appolon1908-hue/Codestra-OpenBao` | secret injection, dynamic credentials, PKI, audit and snapshots |

### 3.2 Required integration repositories

| Component | Principal repository | Production responsibility |
|---|---|---|
| Caddy | `appolon1908-hue/Caddy` | TLS, protected public interfaces, headers and controlled denials |
| Keycloak | `appolon1908-hue/Keycloak` | browser and service identities, scopes, audiences, groups and roles |
| Middleware | `appolon1908-hue/Middleware-` | native Alertmanager ingress, durable command/operation, idempotency, audit and outbox |
| Host authority | `appolon1908-hue/Infustruction-repo` | BOM, topology, deployment waves, backups, restore, rollback and certification |

### 3.3 External provider dependencies that must be reconciled when required

- `appolon1908-hue/klyrow.com` — approved email API, Postal integration, delivery callback and provider read-back;
- `appolon1908-hue/Kong` — only where an API boundary is actually owned by Kong;
- `appolon1908-hue/N8N` — orchestration only; no provider authority;
- the authoritative Postal/Klyrow runtime source and its immutable release;
- the canonical core application deployment authority for `65.109.65.169`.

Do not duplicate source ownership in `Infustruction-repo`. Update a dependency repository only when the production contract requires a real source correction there.

## 4. Server and integration topology

```text
37.27.128.39
  Codestra observability, security and email/provider host

65.109.65.169
  core application host
  Kong -> Middleware -> Odoo/n8n/business applications

65.21.67.207
  VICIdial/telephony host

2.29.17.172
  isolated staging and preferred independent production observer

49.12.145.107
  web/POS/scraper workloads where already authoritative
```

The production alert path must be:

```text
Prometheus
  -> Alertmanager
  -> private Middleware-owned Alertmanager ingress
  -> deterministic Idempotency-Key and X-Correlation-ID
  -> short-lived Keycloak service token
  -> canonical Middleware durable operation
  -> transactional outbox
  -> approved Klyrow/Postal SMTP adapter
  -> appolon@codestra.co
```

The normal path must not send SMTP directly from Alertmanager.

## 5. Central coordination artifacts

Create and continuously update these files in `Infustruction-repo`:

```text
observability/37.27.128.39/PRODUCTION-BOM.yaml
observability/37.27.128.39/DEPLOYMENT-WAVE.yaml
observability/37.27.128.39/INTEGRATION-CONTRACT-LOCK.yaml
observability/37.27.128.39/CURRENT-RUNTIME-INVENTORY.json
observability/37.27.128.39/PRECHANGE-BACKUP-MANIFEST.json
observability/37.27.128.39/RESTORE-EVIDENCE.json
observability/37.27.128.39/ROLLBACK-MATRIX.yaml
observability/37.27.128.39/PRODUCTION-CERTIFICATION.md
observability/37.27.128.39/POST-LIVE-READBACK.json
```

For every deployable component, the BOM must include:

```text
principal_repository
protected_base_branch
production_pr
protected_merge_sha
immutable_release_tag
image_repository_at_sha256
oci_source_label
oci_revision_label
configuration_sha256
schema_or_migration_head
sbom_sha256
provenance_sha256
signature_identity
vulnerability_gate
current_runtime_digest
previous_runtime_digest
rollback_source_sha
rollback_configuration_sha256
backup_artifact
restore_evidence
health_path
readiness_path
version_path
capabilities_path_or_NA
public_hostname_or_NONE
private_service_identity
owner
status
```

A deployment wave is immutable after activation begins. Any source, digest, configuration or migration change creates a new wave and invalidates downstream certification evidence.

Use one change ID and one correlation root for the wave:

```text
CHANGE_ID=CHG-20260902-CODESTRA-37-27-128-39-PRODUCTION-LIVE
CORRELATION_ROOT=generated UUID recorded in DEPLOYMENT-WAVE.yaml
```

## 6. Mission division and dependency order

### MISSION 00 — Coordinator and truth ledger

Executor: one Codex coordinator process.

1. Read this mission and the existing host/repository evidence.
2. Inspect the current default branches, branch protections, rulesets, open PRs, reviews, unresolved threads, checks, releases and deployment workflows for every repository.
3. Inspect the live host read-only before mutation.
4. Build the initial BOM and dependency graph from observed facts only.
5. Classify each repository candidate as `USE_EXISTING`, `UPDATE_EXISTING`, `CONSOLIDATE`, `SUPERSEDE`, or `CREATE_NEW`.
6. Never open duplicate PRs when a compatible authoritative candidate already exists.
7. Record all blockers and continue the independent lanes.

Required output:

```text
COORDINATOR_LEDGER=PASS
REPOSITORIES_CLASSIFIED=<count>/<count>
UNKNOWN_SOURCE_AUTHORITIES=0
SERVER_MUTATIONS=0
```

### MISSION 01 — Repository completion and convergence

Run this lane for every principal repository.

1. Fetch protected base and all relevant open candidates.
2. Identify one production candidate containing all required production work.
3. Rebase or merge the protected base without rewriting independently reviewed history.
4. Resolve overlapping candidates with an explicit supersession map.
5. Implement missing runtime configuration, API contract, health/readiness/version/capabilities surface, security, tests, deployment manifests, backup, restore, rollback and evidence.
6. Update generated OpenAPI, schemas, SDKs, target files, dashboards and runbooks whenever source changes.
7. Run formatting, lint, unit, integration, contract, security, secret, dependency, container, migration and negative tests appropriate to the repository.
8. Commit each logical repair and push it to the authoritative candidate branch.
9. Resolve every review thread with code or evidence.
10. Keep external effects disabled throughout repository certification.

Do not call documentation-only or configuration-only work production complete when the repository owns a runtime.

Required per repository:

```text
SOURCE_COMPLETE=PASS
TESTS=PASS
SECURITY_SCAN=PASS
SECRET_SCAN=PASS
GENERATED_CONTRACT_DRIFT=0
UNRESOLVED_THREADS=0
EXACT_HEAD_CI=PASS
```

### MISSION 02 — Protected merge and immutable release

For each repository after Mission 01 passes:

1. Merge only through the repository’s protected process.
2. Do not disable or bypass required checks or approvals.
3. Verify the exact protected merge SHA.
4. Build the production image from that detached SHA.
5. Use the repository’s documented immutable release convention; create or repair a release workflow when none exists.
6. Publish an immutable image by digest with OCI source and revision labels.
7. Produce SBOM, provenance/attestation, signed checksums and vulnerability evidence.
8. Reject fixable HIGH or CRITICAL vulnerabilities unless the repository’s stricter policy applies.
9. Verify release assets independently from the published release.
10. Record the exact release tuple and previous rollback tuple in the central BOM.

Required per component:

```text
PROTECTED_MERGE=PASS
RELEASE_IMMUTABLE=YES
IMAGE_DIGEST_VERIFIED=PASS
OCI_SOURCE_LABEL=PASS
OCI_REVISION_LABEL=PASS
SBOM=PASS
PROVENANCE=PASS
SIGNATURE=PASS
VULNERABILITY_GATE=PASS
ROLLBACK_TUPLE=PASS
```

### MISSION 03 — Server preflight, freeze, backup and restore

Target: `37.27.128.39`.

Use the existing authorized access path. Do not change SSH configuration.

Before any replacement:

1. capture hostname, time synchronization, uptime, OS/kernel, pending updates, disk, inodes, memory, swap and failed units;
2. capture all containers, health, restarts, images, RepoDigests, OCI labels, Compose projects/files, networks, ports, volumes and mounts;
3. capture current Caddy, OpenBao, Prometheus, Alertmanager, Loki, Tempo, Grafana, Superset, exporter, Postal/Klyrow and Middleware-gateway state;
4. identify staging, preview, test, candidate, abandoned and unknown workloads;
5. freeze production configuration changes outside this wave;
6. keep business email, campaign email, marketing email, SMS, dialing, social publishing and external provider effects at their approved existing safe state;
7. create fresh encrypted backups and checksums;
8. copy required backups off host;
9. restore the exact backup set into an isolated environment and validate representative data and application startup;
10. record current and previous rollback identities before cleanup or deployment.

Never delete an old image, volume, database, queue, release directory or backup until the rollback dependency graph proves it is unnecessary.

Required:

```text
HOST_PREFLIGHT=PASS
TIME_SYNC=PASS
CAPACITY=PASS
CURRENT_RUNTIME_CAPTURED=PASS
PRODUCTION_CHANGE_FREEZE=PASS
BACKUP=PASS
OFF_HOST_BACKUP=PASS
ISOLATED_RESTORE=PASS
ROLLBACK_PREPARED=PASS
```

### MISSION 04 — OpenBao and Keycloak foundation

OpenBao must be operational before application secrets are activated.

1. Validate or establish the independent release trust anchor. When the existing signer cannot be independently approved, rotate through the approved security-owner/HSM or secret-custody process and publish a new signed release; do not trust the signer merely because a release verifies with its included key.
2. Deploy OpenBao from its exact protected SHA and digest.
3. Perform the controlled initialization/unseal or auto-unseal ceremony without exposing recovery material.
4. enable audit before issuing workload credentials;
5. configure Raft snapshots, encrypted off-host backup and isolated restore;
6. create one policy and identity per workload, including separate normal and emergency Alertmanager identities;
7. configure observability PKI and short-lived service certificates;
8. create dynamic or tightly controlled PostgreSQL and Redis monitoring credentials;
9. apply the exact Keycloak observability group, roles and clients;
10. bind the existing `appolon` user only when username and verified email exactly equal `appolon` and `appolon@codestra.co`;
11. do not create or reset that user automatically;
12. do not grant realm-management, host root, Docker, database-superuser or OpenBao-root authority;
13. verify positive and negative browser/service tokens, audience, scope, tenant, expiry and revocation.

Required:

```text
INDEPENDENT_SIGNER_AUTHORITY=PASS
OPENBAO_INITIALIZED=YES
OPENBAO_UNSEALED=YES
OPENBAO_AUDIT=PASS
OPENBAO_SNAPSHOT=PASS
OPENBAO_RESTORE=PASS
WORKLOAD_POLICIES=PASS
SERVICE_PKI=PASS
KEYCLOAK_OBSERVABILITY_IDENTITY=PASS
APPOLON_BINDING=PASS
OVERPRIVILEGED_GRANTS=0
```

### MISSION 05 — Private data and collection plane

Deploy in this order:

```text
Node Exporter
cAdvisor
Redis Exporter
PostgreSQL Exporter
Blackbox Exporter
Loki
Tempo
OpenTelemetry Collector
Alloy
```

For every service:

- exact SHA and image digest only;
- non-root where supported;
- read-only filesystem and mounts where supported;
- no added capabilities unless documented and narrowly justified;
- no Docker socket write authority;
- private native port;
- health/readiness and self-metrics;
- bounded memory, CPU, queues, retries, labels and attributes;
- secret and sensitive-field redaction;
- tenant isolation;
- no public egress except explicitly approved destinations;
- rollback available before proceeding.

PostgreSQL Exporter must remain private at `postgres-exporter:9187` and have no public hostname. Prove that its role cannot write, create databases or roles, replicate, bypass RLS, read business row values or export statement/parameter text.

Redis Exporter must prove that its identity cannot write, execute admin commands, expose key values or use arbitrary multi-target credentials.

Blackbox Exporter must accept only approved modules and generated target allowlists. The SMTP probe may perform banner/EHLO/STARTTLS/TLS/EHLO/QUIT only; it must not authenticate or send mail.

Required:

```text
EXPORTERS=PASS
LOKI=PASS
TEMPO=PASS
OTEL=PASS
ALLOY=PASS
PUBLIC_NATIVE_PORTS=0
CROSS_TENANT_ACCESS=DENIED
SENSITIVE_FIELD_LEAKS=0
```

### MISSION 06 — Prometheus, Alertmanager and durable delivery integration

1. Deploy Prometheus from exact release identity.
2. load only production targets for this wave;
3. validate targets, rules and tests with `promtool`;
4. prove Watchdog, host, container, storage, OpenBao, telemetry, SMTP and alert-delivery rules evaluate correctly;
5. deploy the Middleware-owned private native Alertmanager ingress and canonical operation API;
6. require fixed private ingress authentication from an OpenBao-rendered file;
7. validate and minimize native Alertmanager payloads;
8. derive idempotency from sorted alert fingerprint/status pairs, receiver, production environment and fixed recipient;
9. derive deterministic correlation ID;
10. acquire a short-lived Keycloak token as `alertmanager-observability` for audience `middleware-api`, tenant `codestra-platform` and required scopes;
11. atomically persist the operation, payload digest, inbox/audit evidence and transactional outbox intent before returning `202`;
12. route normal email through the reviewed Klyrow/Postal adapter;
13. require provider Message-ID/provider operation ID and authoritative read-back;
14. return the original operation for same-key/same-payload replay;
15. return `409` for same-key/different-payload;
16. move ambiguous outcomes to reconciliation and do not automatically submit again;
17. deploy Alertmanager with grouping, inhibition, resolved notifications and only the Middleware gateway as its normal receiver;
18. keep the direct SMTP emergency overlay disabled.

Fixed policy:

```text
sender=alerts@codestra.co
recipient=appolon@codestra.co
recipient_override_allowed=false
sender_override_allowed=false
business_email_allowed=false
marketing_email_allowed=false
campaign_email_allowed=false
```

Required:

```text
PROMETHEUS_TARGETS=PASS
PROMETHEUS_RULES=PASS
WATCHDOG=PASS
MIDDLEWARE_ALERT_INGRESS=PASS
MIDDLEWARE_DURABLE_OPERATION=PASS
IDEMPOTENCY=PASS
TRANSACTIONAL_OUTBOX=PASS
ALERTMANAGER=PASS
DIRECT_SMTP_NORMAL_ROUTE=ABSENT
EMAILS_SENT_BEFORE_CANARY=0
```

### MISSION 07 — Grafana, Superset and Caddy edge

1. Deploy Grafana and Superset with exact digests and OpenBao-injected secrets.
2. provision Prometheus, Loki, Tempo and Alertmanager datasources through private service identities;
3. bind Loki and Tempo tenant headers through protected runtime values;
4. provision dashboards from Git and prevent silent UI drift;
5. apply Keycloak Authorization Code + PKCE and exact redirect URIs;
6. enforce verified email, group/role mapping, secure cookies, CSRF and session expiry;
7. configure Superset read-only datasource users and row-level security;
8. prove negative cross-tenant and unauthorized access;
9. render and validate Caddy configuration with the exact released Caddy binary before reload;
10. expose only protected human interfaces:

```text
graf.codestra.media
prom.codestra.media
aler.codestra.media
supe.codestra.media
bao.codestra.media
```

11. keep Loki, Tempo, OTLP, Alloy and exporters private or return controlled denial;
12. keep PostgreSQL Exporter without a public hostname;
13. apply security headers, bounded request bodies, authentication and source restriction;
14. reload Caddy only after upstream health and rollback validation;
15. verify authoritative DNS, public resolvers, TLS SAN/chain/expiry and real application authorization.

Required:

```text
GRAFANA=PASS
SUPERSET=PASS
DASHBOARDS=PASS
PRIVATE_DATASOURCES=PASS
KEYCLOAK_LOGIN=PASS
AUTHORIZED_APPOLON=PASS
UNAUTHORIZED_ACCESS=DENIED
CROSS_TENANT_ANALYTICS=DENIED
CADDY_VALIDATE=PASS
CADDY_RELOAD=PASS
DNS=PASS
TLS=PASS
PUBLIC_NATIVE_PORTS=0
```

### MISSION 08 — Cross-server integration synchronization

Synchronize `37.27.128.39` with `65.109.65.169` without moving unrelated workloads.

1. verify private routing, DNS/service identity, mTLS, Keycloak audiences/scopes and tenant claims;
2. verify core Middleware can accept the exact alert command contract;
3. verify provider-host gateway can reach only the approved Middleware endpoint;
4. verify Middleware can reach only the approved Klyrow/Postal adapter endpoint;
5. verify callback signatures, timestamp bounds, replay protection and durable inbox processing;
6. verify n8n does not possess direct SMTP/provider authority;
7. verify monitoring agents on the core host export metrics/logs/traces to the central host without public native ports;
8. verify production and staging identities, networks, databases, streams, queues and targets cannot cross;
9. verify `65.21.67.207` telephony and other provider hosts are monitored without enabling dialing or unrelated effects;
10. record both sides’ exact source SHA, digest, configuration checksum and integration-contract checksum.

Do not declare synchronization complete based only on TCP connectivity. Require authenticated request, durable acceptance, status read-back, telemetry correlation and negative unauthorized tests.

Required:

```text
PRIVATE_CONNECTIVITY=PASS
MTLS=PASS
KEYCLOAK_SERVICE_AUTH=PASS
TENANT_ISOLATION=PASS
MIDDLEWARE_CONTRACT_SYNC=PASS
KLYROW_POSTAL_CONTRACT_SYNC=PASS
CALLBACK_REPLAY_PROTECTION=PASS
N8N_PROVIDER_BYPASS=ABSENT
CROSS_ENVIRONMENT_ACCESS=DENIED
```

### MISSION 09 — Production certification and bounded activation

Before the canary, prove:

```text
SOURCE_LOCK=PASS
IMMUTABLE_IMAGES=PASS
CONFIGURATION_LOCK=PASS
MIGRATION_LOCK=PASS
OPENBAO=PASS
KEYCLOAK=PASS
PRIVATE_NETWORKS=PASS
BACKUP=PASS
ISOLATED_RESTORE=PASS
ROLLBACK=PASS
EXPORTERS=PASS
METRICS=PASS
LOGS=PASS
TRACES=PASS
DASHBOARDS=PASS
ALERTS=PASS
MIDDLEWARE=PASS
KLYROW_POSTAL=PASS
DNS=PASS
TLS=PASS
REMOTE_WATCHDOG=PASS
EMAILS_SENT=0
```

Then perform exactly one approved synthetic operational alert:

1. create one synthetic alert with `synthetic=true` and a unique fingerprint;
2. verify one firing operation and one external email submission at most;
3. verify durable operation ID, idempotency key, correlation ID, audit record and outbox attempt;
4. verify recipient-side delivery to `appolon@codestra.co`;
5. verify provider Message-ID, SPF, DKIM and DMARC results where available;
6. verify matching Grafana, Loki and Tempo evidence;
7. resolve the same synthetic alert;
8. verify one resolved operation and one resolved notification according to policy;
9. do not send another canary to replace missing evidence; reconcile the existing operation;
10. keep emergency direct SMTP disabled.

Required:

```text
SYNTHETIC_FIRING_CANARY=PASS
FIRING_EXTERNAL_SUBMISSIONS=1
FIRING_RECIPIENT_DELIVERIES=1
SYNTHETIC_RESOLVED_CANARY=PASS
RESOLVED_EXTERNAL_SUBMISSIONS=1
RECIPIENT=appolon@codestra.co
UNAPPROVED_RECIPIENTS=0
DUPLICATE_EXTERNAL_EFFECTS=0
AMBIGUOUS_EFFECTS_RECONCILED=PASS
```

### MISSION 10 — Post-live observation and final handoff

After activation:

1. observe all services through at least two normal health, scrape, collection and alert intervals;
2. verify restart counts remain stable;
3. verify no new authentication, authorization, tenant, queue, storage, memory, cardinality, certificate or delivery failures;
4. verify the independent observer on `2.29.17.172` or `65.109.65.169` can detect complete loss of `37.27.128.39` and notify through a path not exclusively dependent on that host;
5. verify backups and snapshots continue after deployment;
6. verify rollback commands and previous images remain present;
7. capture the final live read-back and compare it byte-for-byte to the BOM where applicable;
8. update every owning repository and central evidence document with the final released and running identities;
9. close superseded PRs only after their replacement is merged and documented;
10. leave no dirty production worktree or `/tmp` deployment dependency.

Required:

```text
POST_LIVE_SOAK=PASS
RESTART_REGRESSION=0
TARGETS_DOWN=0
TELEMETRY_EXPORT_FAILURES=0
ALERT_DELIVERY_FAILURES=0
TOTAL_HOST_OUTAGE_ALERTING=PASS
POST_DEPLOY_BACKUP=PASS
LIVE_BOM_READBACK=PASS
DIRTY_PRODUCTION_WORKTREES=0
```

## 7. Component rollback rule

On a failed component deployment:

1. stop the new component only;
2. preserve its logs, health output, source SHA, digest, configuration checksum and failed migration/read-back evidence;
3. restore the previous exact image/configuration and, when required, the prechange data snapshot;
4. verify the previous release is healthy;
5. repair the defect in the owning repository;
6. push the repair, rerun repository gates, publish a new immutable release and create a new deployment wave;
7. never patch the live container or production file as the source of truth.

Do not roll back unrelated healthy services unless the dependency graph proves compatibility requires it.

## 8. Required progress output

After every mission and after every material remediation cycle, print and persist:

```text
MISSION=<00-10>
COMPONENT=<name>
REPOSITORY=<owner/repo>
BRANCH=<branch>
HEAD_SHA=<sha>
PR=<url-or-NONE>
CHECKS=<PASS|FAIL|PENDING>
PROTECTED_MERGE_SHA=<sha-or-NONE>
RELEASE_TAG=<tag-or-NONE>
IMAGE=<repository@sha256-or-NONE>
CONFIG_SHA256=<sha-or-NONE>
MIGRATION_HEAD=<value-or-NA>
SERVER_STATE=<NOT_TOUCHED|PREPARED|DEPLOYED|ROLLED_BACK|LIVE>
INTEGRATION_STATE=<NOT_TESTED|PASS|FAIL|BLOCKED>
BACKUP=<PASS|FAIL|NOT_RUN>
RESTORE=<PASS|FAIL|NOT_RUN>
ROLLBACK=<PASS|FAIL|NOT_RUN>
EXTERNAL_EFFECTS=<DISABLED|BOUNDED_CANARY|AUTHORIZED_LIVE>
EMAILS_SENT=<count>
BYPASS_USED=NONE
BLOCKER=<exact blocker or NONE>
NEXT_ACTION=<exact next action>
```

## 9. Final certification rule

Issue:

```text
OVERALL_VERDICT=PRODUCTION LIVE
```

only when every Mission 00-10 required output is PASS, every running component matches the exact central BOM, one firing and one resolved alert are proven, independent total-host-outage alerting works, backup/restore/rollback are proven, and no unapproved external effect occurred.

Otherwise issue:

```text
OVERALL_VERDICT=NO-GO
```

with exact component-level blockers, rollback state and next repository action. A `NO-GO` is not permission to abandon the mission: continue fixing every repository-controlled or server-controlled blocker and rerun the failed wave until all controllable gates pass.

## 10. Final output template

```text
PHASE=CODESTRA_37_27_128_39_COORDINATED_REPOSITORY_RELEASE_SERVER_INTEGRATION_PRODUCTION_LIVE
TARGET_HOST=37.27.128.39
CHANGE_ID=CHG-20260902-CODESTRA-37-27-128-39-PRODUCTION-LIVE

REPOSITORIES_DISCOVERED=<count>/<count>
REPOSITORIES_COMPLETED=<count>/<count>
PRS_MERGED=<count>
IMMUTABLE_RELEASES=<count>/<count>
RUNNING_EXACT_DIGESTS=<count>/<count>
CONFIGURATION_LOCK=PASS
MIGRATION_LOCK=PASS

OPENBAO=<PASS|FAIL|BLOCKED>
KEYCLOAK=<PASS|FAIL|BLOCKED>
EXPORTERS=<PASS|FAIL>
LOKI=<PASS|FAIL>
TEMPO=<PASS|FAIL>
OTEL=<PASS|FAIL>
ALLOY=<PASS|FAIL>
PROMETHEUS=<PASS|FAIL>
ALERTMANAGER=<PASS|FAIL>
GRAFANA=<PASS|FAIL>
SUPERSET=<PASS|FAIL>
CADDY=<PASS|FAIL>
MIDDLEWARE_ALERT_PATH=<PASS|FAIL>
KLYROW_POSTAL_ALERT_PATH=<PASS|FAIL>

PRIVATE_NETWORKS=<PASS|FAIL>
PUBLIC_NATIVE_PORTS=0
DNS=<PASS|FAIL>
TLS=<PASS|FAIL>
METRICS=<PASS|FAIL>
LOGS=<PASS|FAIL>
TRACES=<PASS|FAIL>
DASHBOARDS=<PASS|FAIL>
ALERTS=<PASS|FAIL>

BACKUP=<PASS|FAIL>
OFF_HOST_BACKUP=<PASS|FAIL>
ISOLATED_RESTORE=<PASS|FAIL>
ROLLBACK=<PASS|FAIL>
REMOTE_WATCHDOG=<PASS|FAIL>
TOTAL_HOST_OUTAGE_ALERTING=<PASS|FAIL>

FIRING_CANARY=<PASS|FAIL|NOT_RUN>
RESOLVED_CANARY=<PASS|FAIL|NOT_RUN>
EMAILS_SENT=<count>
UNAPPROVED_RECIPIENTS=0
DUPLICATE_EXTERNAL_EFFECTS=0

SSH_CONFIGURATION_CHANGED=NO
DOCKER_GROUP_GRANTS=0
UNRESTRICTED_SUDO_GRANTED=NO
SECRETS_EXPOSED=0
BYPASS_USED=NONE
DIRTY_PRODUCTION_WORKTREES=0

OVERALL_VERDICT=<PRODUCTION LIVE|NO-GO>
BLOCKERS=<exact blockers or NONE>
```
