# CODESTRA OBSERVABILITY REPOSITORY-FIRST CODEX MISSION

**Mission ID:** `CODESTRA_OBSERVABILITY_REPO_FIRST_2026-09-02`
**Execution mode:** repository, CI, release-registry, and artifact work only
**Production host reserved for the later installation mission:** `37.27.128.39`
**Infrastructure authority:** `appolon1908-hue/Infustruction-repo`
**Runtime authority for later server reconciliation:** `appolon1908-hue/codestra-production-runtime-authority`
**Initial production alert administrator:** `appolon@codestra.co`

## 1. Mission outcome

Complete the repository-first remediation, integration, release, and certification of the Codestra observability, telemetry, infrastructure-monitoring, analytics, and secrets suite.

This mission must leave the repositories ready for a separate, evidence-bound server pull/install/live operation. It must not alter the production host or any external runtime.

Do not stop after producing an assessment. Fix every source-side issue that can be fixed with repository access. Continue independent repositories when another repository is blocked. A blocker is an output only when it requires an external approval, credential, registry permission, or unavailable third-party identity that cannot safely be created in source.

The final repository state must provide:

1. one unambiguous authority for every component and cross-component contract;
2. reconciled branches and pull requests;
3. production-grade configuration, tests, documentation, deployment manifests, health/readiness checks, backup/restore instructions, and rollback instructions;
4. protected merge SHAs and immutable, verified release identities;
5. a central source lock and production bill of materials;
6. a complete installation and rollback bundle;
7. the generated `CODESTRA-OBSERVABILITY-SERVER-PULL-INSTALL-LIVE-MISSION.md`, containing only actual verified release data.

## 2. Absolute safety boundary

This is a repository-only mission.

You must not:

- SSH to `37.27.128.39` or any other server;
- use a server console, Docker socket, container exec, systemd, or remote shell;
- deploy, start, stop, restart, replace, or inspect production containers;
- change DNS, public IP records, private DNS, firewall rules, or Hetzner networking;
- reload, restart, or apply Caddy;
- apply a Keycloak realm, client, role, group, user, or secret;
- initialize, unseal, rekey, or write a secret to OpenBao;
- connect to an SMTP server or provider API;
- send email, SMS, voice, social, Odoo, n8n, financial, trading, or other external writes;
- run a production or external canary;
- retrieve, print, commit, upload, or expose credentials, tokens, private keys, recovery shares, certificates, database contents, customer data, or production `.env` files;
- weaken branch protection, required checks, independent review, signature verification, or security gates;
- label source-only, staging-only, disabled, render-only, or plan-only work as production ready.

Allowed work is limited to Git repositories, pull requests, review threads, GitHub Actions, release metadata, OCI registries, generated source artifacts, deterministic configuration validation, and disposable local/CI test environments that have no route to production providers.

A GitHub release or OCI artifact may be published only by an approved repository workflow and only when it does not deploy or contact production. Publishing an immutable artifact is not production authorization.

## 3. Repository authority

### 3.1 Fourteen component authorities

Review and remediate all fourteen repositories. Do not silently drop a repository because it already has passing tests or a previous Stage 7 PR.

| # | Component authority | Principal repository | Required boundary |
|---:|---|---|---|
| 1 | Grafana | `appolon1908-hue/Codestra-Grafana-` | Read-only operational presentation and correlation |
| 2 | Prometheus | `appolon1908-hue/Codestra-Prometheus` | Metrics ingestion, recording rules, SLOs, and alert evaluation |
| 3 | Alertmanager | `appolon1908-hue/Codestra-Alertmanager` | Alert grouping, inhibition, silencing, and routing to Middleware only |
| 4 | Loki | `appolon1908-hue/Codestra-Loki` | Governed log storage and query |
| 5 | Tempo | `appolon1908-hue/Codestra-Tempo` | Governed trace storage and query |
| 6 | OpenTelemetry | `appolon1908-hue/Codestra-Telemetry` | OTLP collection, normalization, redaction, buffering, and export |
| 7 | Alloy | `appolon1908-hue/Codestra-Alloy` | Host/application collection and routing into the observability backends |
| 8 | Node Exporter | `appolon1908-hue/Codestra-Node-Exporter` | Host metrics only |
| 9 | cAdvisor | `appolon1908-hue/Codestra-cAdvisor` | Container resource metrics only |
| 10 | PostgreSQL Exporter | `appolon1908-hue/Codestra-Postgres-Exporter` | Least-privilege PostgreSQL metrics; private-only; no public hostname |
| 11 | Redis Exporter | `appolon1908-hue/Codestra-Redis-Exporter` | Least-privilege Redis metrics; private-only |
| 12 | Blackbox Exporter | `appolon1908-hue/Codestra-Blackbox-Exporter` | Side-effect-free synthetic HTTP/TLS/DNS/TCP probes only |
| 13 | Superset | `appolon1908-hue/Superset` | Read-only governed business analytics |
| 14 | OpenBao | `appolon1908-hue/Codestra-OpenBao` | Secrets, PKI, policy, audit, and recovery configuration authority |

### 3.2 Supporting authorities required by this mission

Update these repositories only for the observability integration they own. Do not expand into unrelated business features.

| Authority | Principal repository | Required mission work |
|---|---|---|
| Shared infrastructure and release governance | `appolon1908-hue/Infustruction-repo` | Mission authority, topology, installation bundle, source lock, BOM, validators, URL contract, final certification, and later server mission |
| Production runtime source reconciliation | `appolon1908-hue/codestra-production-runtime-authority` | Reference the accepted immutable observability release train without duplicating component source; prepare later runtime reconciliation inputs only |
| Human identity desired state | `appolon1908-hue/Keycloak` | Source-controlled, validate-only OIDC clients, roles, groups, scopes, redirect URIs, and rollback plan; no live apply |
| Edge exposure desired state | `appolon1908-hue/Caddy` | Source-controlled, render-and-validate-only routes and TLS/security policy; no reload or DNS change |
| Cross-system alert/incident boundary | `appolon1908-hue/Middleware-` | Alertmanager webhook ingestion, durable incident state, idempotency, audit, notification outbox, and SMTP recipient policy; no live delivery |
| Communication architecture boundary | `appolon1908-hue/communication-platform-` | Confirm that alert email delivery is invoked by Middleware through the governed communication boundary, never directly by Alertmanager |

`Infustruction-repo` may orchestrate and lock exact component artifacts, but it must not copy or become a second source for component application/runtime code.

If another repository contains compatibility documentation that contradicts one of these principal authorities, fix the stale compatibility reference in a focused PR. Do not create a second implementation.

## 4. Known authority correction that must be completed

The PostgreSQL Exporter principal repository wins over stale central validators or manifests.

The required final contract is:

- `Codestra-Postgres-Exporter` is private-only;
- it has no public Caddy route;
- it has no public DNS hostname;
- it is scraped through an internal Docker/private-network service identity;
- remove or correct stale production claims for `pgex.codestra.media` wherever they imply a public or protected public hostname;
- update all central registries, validators, documentation, Caddy desired state, service catalogs, and tests to agree with the principal repository;
- preserve a private internal service name such as the Compose service name when needed, but do not represent that name as public DNS.

Search the complete owner repository set and all open PR branches for the stale hostname. Do not limit the search to default branches.

## 5. Source discovery and repository baseline

For every named repository:

1. Read `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, release policy, workflow files, branch protection/rulesets, open issues, open PRs, review threads, releases, tags, package/OCI publications, and repository-specific authority documents.
2. Fetch every maintained branch and tag. Determine which branch is the accepted development, test, staging, production, and final authority. Do not assume that `main` contains the Codestra overlay when the repository intentionally preserves an upstream mirror.
3. Record exact branch heads before making changes.
4. Inventory the Codestra-owned source/configuration separately from vendored or mirrored upstream source.
5. Verify upstream project/version/license and the exact upstream source or image digest.
6. Detect duplicated configuration, dead manifests, stale hostnames, unpinned images, `latest` tags, floating GitHub Actions, secrets, generated files, test-only files presented as production files, and source/runtime authority conflicts.
7. Produce or update a repository profile that states:
   - canonical repository and owner;
   - component purpose and non-goals;
   - upstream project and version;
   - accepted branch model;
   - build and runtime entrypoints;
   - configuration authority;
   - dependencies and consumers;
   - health/readiness contract;
   - backup/restore scope;
   - public/private exposure;
   - release and rollback process;
   - current production-readiness verdict.
8. Run the existing baseline tests before editing and record failures without masking them.

Do not use a failed search command as proof that a file does not exist. Use the GitHub API, repository trees, branch-aware code search, and local `git grep` across fetched refs.

## 6. Pull-request reconciliation

Before creating a new implementation PR in any repository:

1. List every open PR and all recently closed/unmerged PRs that overlap the mission.
2. Compare changed files and commits, not just PR titles.
3. Classify each PR as:
   - canonical and active;
   - independent and safe to continue;
   - overlapping and requiring consolidation;
   - superseded after preserving valid work;
   - unrelated and out of scope.
4. Use one canonical PR per logical change. Do not mass-merge overlapping PRs.
5. Preserve valid source, tests, documentation, review fixes, and release work by rebasing, cherry-picking, or manually porting it before closing a superseded PR.
6. Resolve every actionable inline review thread with code and tests. Do not resolve a thread merely by replying.
7. Never dismiss a valid review to make a gate green.
8. Record the old PR, preserved commits/files, canonical replacement PR, and final disposition in the central reconciliation report.
9. Continue independent repositories while approvals or checks block another repository.

Create or update:

`Infustruction-repo/release/CODESTRA-OBSERVABILITY-OPEN-PR-RECONCILIATION.md`

The report must cover all fourteen component repositories and all supporting-authority repositories.

## 7. Branch, commit, review, and merge rules

For every logical change:

1. Create a focused branch from the correct current integration base.
2. Keep unrelated remediation in separate commits or PRs.
3. Update source, configuration, tests, documentation, release evidence, deployment manifests, health/readiness checks, backup/restore instructions, and rollback instructions together when they are part of one logical change.
4. Run local validation and `git diff --check` before committing.
5. Commit and push the exact change.
6. Open or update the canonical PR with:
   - problem and authority;
   - files changed;
   - safety boundary;
   - tests and exact results;
   - migration/compatibility impact;
   - release impact;
   - rollback;
   - remaining blockers.
7. Run exact-head CI on the PR head SHA.
8. Re-run exact-head CI after every corrective commit.
9. Require merge-result CI where the repository supports it.
10. Merge only through the protected process after required checks, required independent approvals, unresolved-thread count, security gates, and branch freshness all pass.
11. Never force-push a protected branch or bypass required checks.
12. Record the protected merge SHA, not merely the PR head SHA.
13. Build/publish only from that protected merge SHA or an immutable tag that points exactly to it.
14. Verify artifact revision readback equals the protected merge SHA.

A passing workflow on an earlier SHA is not evidence for a later SHA.

## 8. Common production repository standard

Each component repository must contain or clearly reference the following production-grade material, adapted to the component rather than copied mechanically:

- a real `README.md`, not an upstream/default template;
- `REPOSITORY_PROFILE.md` or equivalent authority profile;
- `SECURITY.md` and vulnerability-reporting policy;
- `CODEOWNERS` or documented review ownership;
- production architecture and operating model;
- production configuration source with no embedded secrets;
- deterministic configuration validator;
- production deployment manifest or configuration-bundle manifest;
- health and readiness contract with executable tests;
- metrics/logs/traces contract applicable to the component;
- capacity, retention, persistence, and data-loss behavior;
- backup, restore, disaster-recovery, and recovery verification instructions;
- upgrade and upstream synchronization procedure;
- rollback procedure that uses an actual previous accepted digest;
- CI workflow;
- protected release workflow;
- dependency and secret scanning;
- SBOM generation;
- provenance generation;
- signature generation and verification;
- vulnerability policy;
- release evidence manifest;
- license and upstream attribution;
- a statement that source preparation does not activate production.

All Docker images and GitHub Actions must be immutable. Replace `latest`, floating major tags, mutable tags, and unpinned third-party actions with exact digests or full commit SHAs. Where a tool cannot operate correctly under a fully read-only filesystem or non-root user, document the smallest required exception and test that no broader privilege is granted.

## 9. Supply-chain and immutable-release gate

For every component, choose one of these valid artifact models:

### Model A — Codestra-built image

Use when Codestra source, plugins, packaging, or hardening requires a custom image.

The protected release workflow must:

- build from the protected merge SHA;
- pin the base image by digest;
- use a deterministic build context;
- include OCI labels for source, revision, version, created time, title, description, and licenses;
- generate an SPDX or CycloneDX SBOM;
- generate SLSA-compatible provenance;
- scan dependencies, filesystem, and final image;
- fail on unresolved critical vulnerabilities and on high vulnerabilities not covered by an approved, expiring exception;
- publish an immutable OCI image;
- sign the image and attestations with the approved GitHub OIDC/keyless process or another reviewed non-exported signing authority;
- pull the exact `repository@sha256:...` identity after publication;
- inspect `org.opencontainers.image.revision` and prove it equals the protected merge SHA;
- verify signature, SBOM attestation, and provenance attestation against the exact digest.

### Model B — verified upstream image plus signed Codestra configuration artifact

Use when no custom binary/image is necessary.

The protected release workflow must:

- pin the upstream image by digest and record its upstream version;
- verify upstream provenance/signature when available;
- scan the exact upstream digest under Codestra policy;
- package the reviewed Codestra configuration, dashboards, rules, probes, policies, and scripts as an immutable signed OCI artifact or release archive;
- generate an SBOM/manifest for the configuration bundle and its dependencies;
- sign and verify the configuration artifact;
- record both the upstream runtime image digest and the Codestra configuration artifact digest.

Do not create an unnecessary fork image merely to satisfy a checklist.

For either model, a mutable release tag is only a human label. The production identity is the exact digest.

## 10. Observability data-governance contract

Across Prometheus, Loki, Tempo, OpenTelemetry, Alloy, Grafana, Superset, and all exporters:

Required bounded dimensions are:

- `codestra_business`
- `application`
- `service`
- `environment`
- `server`
- `region`
- `deployment`

The following must not be metric labels or Loki stream labels:

- customer, tenant, account, user, email, phone, message, order, request, correlation, or trace identifiers; raw runtime container IDs; pod UIDs or names; and arbitrary runtime-generated instance identifiers;
- raw URLs, query strings, SQL statements, exception text, request/response bodies, credentials, tokens, cookies, authorization headers, private keys, DSNs, broker credentials, financial payloads, communication payloads, or personal data.

Trace and correlation IDs may be protected log fields and trace search attributes when operationally required, but not unbounded metric/log-stream labels. Redaction must occur before export. Tests must inject representative secrets and personal-data patterns and prove they do not reach exported metrics, log streams, spans, dashboards, or Superset datasets.

Container metrics may use one deployment-controlled `workload_instance` label only when it is derived from a bounded replica slot in the reviewed deployment manifest, cannot contain a raw container/pod identifier or caller value, and is covered by a cardinality-limit test. Otherwise aggregate replica metrics before ingestion so distinct containers cannot produce duplicate Prometheus series.

Grafana, Prometheus, Loki, Tempo, Alertmanager, OpenTelemetry, Alloy, exporters, and Superset must not have authority to execute business writes, Odoo mutations, n8n workflows, provider delivery, PSTN dialing, social publishing, lending/financial actions, or trading orders.

## 11. Component-specific completion requirements

### 11.1 Grafana

- Production mode; no SQLite for accepted production state.
- External PostgreSQL metadata database through a least-privilege role.
- Strong application secret from a runtime secret file/OpenBao reference.
- Anonymous access disabled.
- Keycloak Authorization Code + PKCE integration.
- Source-controlled role mapping for `observability-viewer`, `observability-operator`, and `observability-admin`.
- Secure cookies, HTTPS root URL, CSRF/origin controls, security headers, and proxy awareness.
- Immutable datasource provisioning for Prometheus, Loki, and Tempo using private service addresses and secret files.
- Source-controlled dashboards, folders, and read-only corporate incident views.
- Grafana-managed alerting disabled unless a separately reviewed migration explicitly makes it authoritative; Prometheus evaluates alerts and Alertmanager routes them.
- No dashboard button, plugin, or data source may perform business mutations.
- Validate dashboard JSON, datasource provisioning, alert links, trace/log correlation, and duplicate UIDs.

### 11.2 Prometheus

- Pin the accepted Prometheus version/image digest.
- Validate with `promtool check config` and `promtool check rules` or the exact version-equivalent tools.
- Add unit tests for every critical alert and SLO/burn-rate rule.
- Use bounded labels and relabeling; reject high-cardinality target metadata.
- Scrape all fourteen relevant services where applicable through private addresses.
- Use TLS/mTLS and secret files where the target contract requires them.
- Configure retention, persistent storage, WAL behavior, resource limits, and corruption recovery.
- Record target ownership and an HTTPS runbook for every actionable alert.
- Ensure dangerous capability activation, backup failure, restore failure, source/runtime drift, telemetry loss, disk exhaustion, authentication failure, and exporter failure have tested alert coverage.

### 11.3 Alertmanager

- Pin the accepted Alertmanager version/image digest.
- Validate configuration with the exact-version tooling.
- Group by bounded operational labels and implement severity routing, inhibition, repeat intervals, resolved notifications, and expiring silence policy.
- Route to Middleware only through a TLS-protected private webhook using a bearer credential file and/or reviewed mTLS identity.
- Keep direct email, SMS, voice, Slack, PagerDuty, Odoo, n8n privileged writes, provider writes, and business mutations disabled.
- Store no SMTP credentials.
- Required labels: `alertname`, `severity`, `environment`, `service`, `codestra_business`, `owner`.
- Required annotations: `summary`, `description`, `runbook_url`.
- Test firing, grouped, inhibited, silenced, resolved, duplicate, malformed, and missing-label cases against a local in-process/mock Middleware receiver with no network delivery.

### 11.4 Loki

- Pin the accepted version/image digest.
- Configure durable storage, retention, compaction, limits, query fairness, ingestion limits, and recovery behavior.
- Enforce bounded stream labels and reject secret/PII-bearing labels.
- Keep ingestion/query endpoints private.
- Require authenticated/mTLS ingestion where supported by the selected topology.
- Add configuration validation and disposable ingestion/query tests.
- Provide backup/restore and object-store recovery documentation appropriate to the chosen storage mode.

### 11.5 Tempo

- Pin the accepted version/image digest.
- Configure durable storage, retention, compaction, query limits, sampling, and recovery behavior.
- Keep OTLP and query endpoints private.
- Prohibit raw bodies, credentials, personal identifiers, financial signing material, and unbounded IDs as span attributes.
- Validate metrics-generator/service-graph use without turning traces into high-cardinality metrics.
- Add disposable write/read and redaction tests.

### 11.6 OpenTelemetry Collector

- Pin the accepted Collector distribution/version/image digest.
- Use explicit receivers, processors, exporters, extensions, and pipelines; disable unused listeners.
- Require OTLP authentication and TLS/mTLS on non-loopback/non-private-trusted boundaries.
- Include memory limiter, batching, retry, persistent or bounded sending queues, backpressure, health check, and self-telemetry.
- Enforce resource identity and deterministic attribute normalization.
- Redact secrets, credentials, personal data, and prohibited payload fields before any exporter.
- Test configuration, startup, health, queue/retry behavior, and redaction in a disposable environment.

### 11.7 Alloy

- Pin the accepted Alloy version/image digest.
- Use source-controlled modules for metrics, logs, traces, host identity, and routing.
- Keep host mounts read-only and minimal.
- Do not grant an unrestricted Docker socket. Use cAdvisor, a reviewed read-only proxy, or another least-privilege mechanism when container discovery is required.
- Apply redaction and bounded-label normalization before forwarding.
- Configure WAL/queue/retry behavior and resource limits.
- Test configuration syntax, private endpoint routing, secret redaction, duplicate collection prevention, and failure recovery.

### 11.8 Node Exporter

- Private-only; no public Caddy route or public DNS.
- Pin the version/image digest.
- Mount only required host filesystems read-only.
- Enable only reviewed collectors and exclude sensitive/pseudo filesystems.
- Run with the least privileges compatible with required host metrics.
- Add metric-presence, filesystem-exclusion, and private-exposure tests.

### 11.9 cAdvisor

- Private-only; no public Caddy route or public DNS.
- Pin the version/image digest.
- Minimize mounts, capabilities, devices, and runtime privileges; document any unavoidable exception.
- Disable storage drivers and features not used by Codestra.
- Apply container-label allowlisting/relabeling to prevent cardinality and secret leakage.
- Preserve series uniqueness through either the bounded deployment-controlled `workload_instance` label defined in section 10 or a tested pre-ingestion aggregation rule; never retain raw container IDs, names, pod UIDs, or arbitrary labels.
- Test health, metrics, container discovery, and prohibited label removal.

### 11.10 PostgreSQL Exporter

- Private-only and no public hostname, including no `pgex.codestra.media` public contract.
- Pin the version/image digest.
- Use a dedicated least-privilege monitoring role and secret file/OpenBao reference.
- Do not embed a DSN or password in Compose, command arguments, workflow logs, or Git.
- Review custom queries for lock cost, data exposure, extension assumptions, and cardinality.
- Export operational aggregates only; no row data or customer identifiers.
- Test exporter startup, `pg_up`, required metric families, permission denial for prohibited reads, and failure behavior.

### 11.11 Redis Exporter

- Private-only; no public Caddy route or public DNS.
- Pin the version/image digest.
- Use a dedicated least-privilege Redis ACL identity and secret file/OpenBao reference.
- Require TLS where the Redis boundary requires it.
- Do not expose key names, values, customer identifiers, or arbitrary `check-keys` patterns.
- Test `redis_up`, memory/connection/replication metrics, auth failure, and private exposure.

### 11.12 Blackbox Exporter

- Private-only; no public Caddy route or public DNS.
- Pin the version/image digest.
- Permit only approved side-effect-free HTTP GET/HEAD, TLS, DNS, ICMP where explicitly approved, and TCP handshake probes.
- No POST, mutation endpoint, login action, provider write, email/SMS/voice action, or production canary.
- Enforce target allowlists and egress/SSRF controls; never allow arbitrary user-supplied targets.
- Keep authentication material in runtime secret files only.
- Validate every module and test that forbidden schemes, hosts, ports, redirects, and mutation paths fail closed.

### 11.13 Superset

- Pin the accepted version/image digest.
- Production metadata database, cache, and worker topology as required by the selected version.
- Strong application secret from OpenBao/runtime secret file.
- Keycloak Authorization Code + PKCE integration with explicit role mapping.
- Anonymous access disabled.
- Use read-only database roles, curated datasets, row-level security, least privilege, and query time/resource limits.
- Disable or strictly restrict SQL Lab, database creation, credential display, and arbitrary write-capable connections for non-admin users.
- No business-system writes.
- Validate dataset ownership, row-level security, dashboards, migrations, health, and restore behavior in disposable CI.

### 11.14 OpenBao

- Pin the accepted OpenBao version/image digest.
- Repository work is configuration/review only. Do not initialize, unseal, rekey, write secrets, or contact a live OpenBao instance.
- Provide reviewed TLS/mTLS, storage, seal/recovery, audit-device, listener, telemetry, policy, auth-method, namespace/path, token-TTL, and lease-revocation desired state.
- Define least-privilege secret paths for Grafana, Superset, Prometheus/Alertmanager, exporters, OpenTelemetry/Alloy, Middleware webhook identity, and later SMTP provider credentials.
- No shared universal token.
- Provide initialization custody, recovery-share custody, backup/snapshot, isolated restore, disaster recovery, rotation, revocation, and break-glass runbooks.
- Test syntax/policy behavior in a disposable initialized CI instance using generated ephemeral test shares that are destroyed with the job and never treated as production credentials.

## 12. Keycloak desired-state contract

In `appolon1908-hue/Keycloak`, create or reconcile validate-only desired state for:

- `grafana-observability`;
- `superset-analytics`;
- `openbao-secrets` when the accepted OpenBao OIDC architecture requires a browser client.

Required controls:

- Authorization Code flow with PKCE for browser users;
- exact HTTPS redirect URIs and post-logout redirect URIs;
- no wildcard origins or redirects;
- no Resource Owner Password Credentials grant;
- confidential/public client type chosen according to the actual application and proxy pattern;
- client secrets referenced from OpenBao/runtime secret files, never committed;
- explicit audience and scope mapping;
- short sessions and reviewed refresh behavior;
- group/role mappings for `observability-viewer`, `observability-operator`, and `observability-admin`;
- equivalent least-privilege Superset analytics roles;
- strong admin separation and no automatic elevation from an email address alone;
- export validator and semantic tests;
- rollback desired state and unchanged/live-apply prohibition.

Produce a rendered plan and checksum. Do not call the Keycloak Admin API and do not apply the plan.

## 13. URL and exposure contract

Create the authoritative file:

`Infustruction-repo/release/CODESTRA-OBSERVABILITY-URL-EXPOSURE-CONTRACT.yaml`

The desired exposure is:

- `graf.codestra.media`: HTTPS edge route allowed only to Grafana, protected by Keycloak and application RBAC;
- `supe.codestra.media`: HTTPS edge route allowed only to Superset, protected by Keycloak and application RBAC;
- `bao.codestra.media`: private/VPN or otherwise strongly restricted management exposure only; never anonymous or broad internet exposure;
- Prometheus, Alertmanager, Loki, Tempo, OpenTelemetry, Alloy, Node Exporter, cAdvisor, PostgreSQL Exporter, Redis Exporter, and Blackbox Exporter: private service addresses only; no public native ports;
- PostgreSQL Exporter: no public DNS hostname at all;
- any retained names such as `prom.codestra.media`, `aler.codestra.media`, `loki.codestra.media`, `temp.codestra.media`, `otel.codestra.media`, `allo.codestra.media`, `node.codestra.media`, `cadv.codestra.media`, `rdex.codestra.media`, or `blac.codestra.media` must be classified explicitly as private DNS/admin-plane names and must not create public exposure.

In `appolon1908-hue/Caddy`, prepare only the allowed UI/restricted-management routes. Add route rendering, formatting, config validation, upstream mapping tests, auth-header tests, security-header tests, websocket/streaming tests where required, public-route denial tests, and rollback. Do not reload Caddy and do not alter DNS.

The URL contract must fail CI if a private component acquires a public route or if `pgex.codestra.media` reappears as a public hostname.

## 14. Middleware alert and incident contract

Alertmanager does not send email directly. Middleware is the durable cross-system authority.

In `appolon1908-hue/Middleware-`, implement or reconcile one canonical Alertmanager integration. The preferred canonical ingestion path is:

`POST /v1/integrations/alertmanager/events`

If an already accepted route has equivalent semantics under a different path, preserve one canonical route, document it, and provide a tested compatibility/deprecation path rather than duplicate business logic.

Required API surface:

- webhook ingestion;
- list incidents with bounded filters and pagination;
- get one incident and its timeline;
- acknowledge an incident;
- resolve/reopen through an authorized operator command when applicable;
- inspect notification attempts and reconciliation state through authorized read APIs.

Webhook requirements:

- private-network origin plus TLS;
- bearer credential from a file and/or reviewed mTLS workload identity;
- constant-time credential validation;
- schema validation for Alertmanager webhook v4-compatible payloads;
- required labels/annotations enforcement;
- body-size and alert-count limits;
- replay and abuse controls;
- stable idempotency identity derived from `groupKey`, alert fingerprint, alert status, and `startsAt`;
- one transaction for incident create/update, event timeline, audit entry, and notification outbox intent;
- durable unique constraints so retries do not create duplicate incidents or notifications;
- firing, resolved, reopened, and acknowledged state handling from webhook/operator events;
- inhibited and silenced state remains authoritative in Alertmanager because webhook v4 suppresses those notifications; Middleware may record it only from a separately authenticated, read-only Alertmanager status reconciliation source with stable group/fingerprint mapping, and must not infer it from a missing webhook;
- correlation ID and source deployment metadata;
- no synchronous provider call inside the ingestion transaction;
- no automatic business-system mutation.

Notification delivery must use a durable outbox/worker and the governed communication adapter. Provider ambiguity must transition to reconciliation-required; it must not blindly resend.

All OpenAPI, migrations, models, repository/service layers, tests, metrics, audit events, runbooks, failure modes, and rollback migrations must be complete.

## 15. SMTP recipient policy

Create one canonical policy owned by Middleware and referenced by Alertmanager and the central BOM.

Initial production recipient:

`appolon@codestra.co`

Required policy:

- direct Alertmanager SMTP is forbidden;
- only Middleware may request the governed communication adapter to deliver an alert email;
- repository-only defaults keep delivery disabled;
- the initial production allowlist contains only `appolon@codestra.co` unless a later protected change adds reviewed recipients;
- tenant/user-supplied email addresses cannot become alert recipients;
- critical and high alerts may generate immediate grouped notifications;
- warning alerts use grouping/deduplication and a reviewed repeat interval;
- informational alerts do not email by default;
- resolved notifications are supported and deduplicated;
- subject/body contain severity, environment, business, service, summary, incident ID, first-seen time, current status, and HTTPS runbook/dashboard links;
- no credentials, raw log bodies, request bodies, customer data, phone numbers, message payloads, or unrestricted exception text;
- sender identity, SMTP/API credentials, and provider endpoints are runtime secret/config references, not committed values;
- each notification has a durable idempotency key and audit evidence;
- retry uses bounded backoff and dead-letter/reconciliation state;
- delivery metrics and alerts must not expose the recipient as a metric label.

Tests must use an in-process fake adapter, not an SMTP socket or external provider. No email may be sent during this mission.

## 16. CI and exact-head validation

Every repository must have exact-head checks appropriate to its content. At minimum:

- formatting/lint;
- schema/config validation;
- unit tests;
- component-specific integration tests in disposable CI;
- health/readiness test;
- secret scan;
- dependency audit;
- license/upstream metadata validation;
- GitHub Actions pin validation;
- Dockerfile/Compose/manifest policy validation;
- vulnerability scan;
- SBOM generation test;
- provenance/signing workflow validation;
- release-manifest validation;
- configuration checksum validation;
- documentation link/path validation;
- `git diff --check`.

Use least-privilege workflow permissions. Pin third-party actions by full commit SHA. Do not execute untrusted PR code with write tokens or secrets. Do not use `pull_request_target` to build untrusted changes. Separate build/test from protected release jobs. Environment approvals must remain intact.

A skipped required check is not a pass unless the skip is explicitly expected for an inapplicable component and the central validator records the reason as `N/A`.

## 17. Disposable cross-repository integration lab

Create a CI-only, non-production integration lab that uses exact candidate artifacts and generated ephemeral credentials. It must not resolve or route to production provider endpoints.

Prove at least:

1. Prometheus scrapes component self-metrics and exporter metrics.
2. A synthetic metric causes a tested Prometheus alert.
3. Alertmanager groups and routes the alert to the in-process/mock Middleware receiver.
4. Middleware authenticates, validates, deduplicates, persists the incident/timeline/audit/outbox atomically, and returns a stable response.
5. The fake communication adapter records exactly one notification request to `appolon@codestra.co` when the test policy enables it.
6. A retry does not create a second incident or delivery request.
7. A resolved event updates the incident and creates at most one resolved notification intent.
8. Grafana provisioning loads Prometheus, Loki, and Tempo datasources and dashboards without write credentials.
9. A synthetic log and trace can be correlated without leaking seeded secrets/PII.
10. Superset connects through a read-only test role and cannot perform a write.
11. PostgreSQL and Redis exporters cannot access prohibited data/commands.
12. Blackbox rejects an unapproved target and a mutation endpoint.
13. OpenBao policies grant only the intended ephemeral test paths.
14. All private services are unreachable from the lab's simulated public network.

Destroy all generated test credentials and state at job completion. Do not reuse them as production material.

## 18. Backup, restore, and rollback preparation

Repository release readiness requires tested recovery design, not merely a backup script.

For each stateful component, define:

- what data is authoritative;
- storage path/volume/object-store/database scope;
- consistency method;
- encryption and access boundary;
- retention and off-host requirement;
- backup command/script;
- integrity checksum;
- isolated restore procedure;
- restore verification queries/health checks;
- recovery point and recovery time objectives;
- failure and partial-restore behavior.

At minimum cover Grafana metadata, Superset metadata, Prometheus TSDB, Alertmanager silences/state where retained, Loki storage, Tempo storage, OpenBao storage/snapshots, and Middleware incident/audit/outbox state.

Run disposable backup/restore tests in CI where technically possible. Do not claim production backup or restore PASS from a CI-only test; label it repository recovery design/test evidence. The later server mission must perform real pre-change backup and isolated restore evidence before production activation.

Every component must have a rollback bundle containing:

- previous accepted protected merge SHA;
- previous immutable image/config artifact digest;
- previous deterministic configuration checksum;
- data/schema compatibility statement;
- rollback order and command template;
- rollback health/readiness tests;
- forward-recovery path when rollback is unsafe.

The final server mission may include a rollback digest only after the registry proves that digest actually exists and is pullable.

## 19. Central source lock and production BOM

In `appolon1908-hue/Infustruction-repo`, create or replace with one canonical set:

- `release/CODESTRA-OBSERVABILITY-SOURCE-LOCK.yaml`
- `release/CODESTRA-OBSERVABILITY-PRODUCTION-BOM.json`
- `release/CODESTRA-OBSERVABILITY-CONFIG-CHECKSUMS.sha256`
- `release/CODESTRA-OBSERVABILITY-RELEASE-EVIDENCE.md`
- `release/CODESTRA-OBSERVABILITY-REPOSITORY-CERTIFICATION.md`
- machine-readable validators and CI.

Each component/support entry must include as applicable:

- repository;
- authority role;
- accepted branch/ref;
- protected merge SHA;
- PR number and URL;
- release tag;
- upstream project/version/digest;
- custom image or upstream image identity as `repository@sha256:...`;
- Codestra configuration artifact identity/digest;
- OCI revision readback;
- SBOM digest;
- provenance digest;
- signature identity and verification result;
- vulnerability-gate result and approved exceptions with expiry;
- deterministic configuration checksum;
- required secret references by name only;
- desired exposure classification;
- health/readiness tests;
- data/persistence scope;
- previous rollback SHA/digest/checksum;
- remaining blocker;
- `REPO_RELEASE_READY` verdict.

The validator must fail on:

- a missing repository;
- a duplicate authority;
- a mutable or malformed image identity;
- a protected merge SHA that does not match the release revision;
- a missing/pending/unverified signature, SBOM, provenance, scan, or checksum;
- `latest` or another floating tag;
- a placeholder such as `TBD`, `TODO`, `UNKNOWN`, `UNRESOLVED`, `NOT_BUILT`, `NOT_PUBLISHED`, `N/A` where evidence is required, or an empty string;
- a private component classified as publicly exposed;
- `pgex.codestra.media` classified as public DNS;
- a direct Alertmanager email/SMS/provider receiver;
- an SMTP recipient other than the protected allowlist;
- a server command referring to an artifact not present in the BOM;
- a rollback digest that is absent or unverified.

Do not overwrite historical evidence. Version or archive superseded locks and identify the new canonical lock.

## 20. Installation bundle

Create a deterministic source-controlled installation bundle under:

`Infustruction-repo/deploy/observability/`

It must include:

- exact-digest production Compose/manifest source;
- networks, volumes, resource limits, restart policy, security options, capabilities, read-only mounts, tmpfs, and health checks;
- secret-file/OpenBao reference map containing no secret values;
- environment example containing no credentials;
- deterministic config rendering and checksum verification;
- preflight validation;
- image/config-artifact pull and signature verification;
- configuration validation using exact component versions;
- dependency order;
- migration/initialization separation from normal service startup;
- backup prerequisite gate;
- start/health/readiness verification functions;
- smoke tests that make no external writes;
- rollback script/bundle;
- uninstall/recovery documentation;
- evidence capture with secret redaction.

No service may run a database migration, OpenBao initialization, secret generation, or destructive initialization implicitly during routine container startup.

Validated dependency order must account for:

1. approved storage/databases and private networks;
2. OpenBao only after its separate custody/initialization gate;
3. Loki, Tempo, Prometheus, and Alertmanager backends;
4. exporters;
5. OpenTelemetry and Alloy collection/routing;
6. Grafana and Superset metadata migrations as explicit one-shot jobs, then applications;
7. Keycloak desired-state application only in the later authorized server mission;
8. Caddy route application only after private upstream health passes;
9. Middleware alert integration and controlled notification activation only after all earlier gates pass.

The repository-only mission validates this bundle in disposable CI. It does not execute it on `37.27.128.39`.

## 21. Completion gates

Finish only when all applicable values are backed by inspectable evidence:

```text
REPOSITORY_AUTHORITY=PASS
OPEN_PRS_RECONCILED=PASS
EXACT_HEAD_CI=PASS
PROTECTED_MERGES=PASS
SOURCE_LOCK=PASS
IMMUTABLE_IMAGES=PASS
SIGNED_RELEASES=PASS
SBOM=PASS
PROVENANCE=PASS
VULNERABILITY_GATE=PASS
PRODUCTION_CONFIGS=PASS
URL_EXPOSURE_CONTRACT=PASS
KEYCLOAK_DESIRED_STATE=PASS
MIDDLEWARE_ALERT_CONTRACT=PASS
SMTP_RECIPIENT_POLICY=PASS
INSTALLATION_BUNDLE=PASS
ROLLBACK_BUNDLE=PASS
REPO_RELEASE_READY=PASS
```

Rules:

- `PASS` requires actual evidence.
- Use `N/A` only when the component genuinely has no applicable requirement and explain why.
- Use `BLOCKED` or `FAIL` for unmet requirements; never use `NOT VERIFIED` for a production-critical area.
- `CONFIG_PREPARED_NOT_DEPLOYED`, `SOURCE_PREPARED_NOT_DEPLOYED`, `deployment_enabled=false`, staging-only Compose, a green old SHA, a draft PR, or an unsigned/mutable image cannot satisfy a production gate.
- The mission is not complete while any named repository has an unresolved high/critical source defect, an unresolved review thread, an overlapping unreconciled PR, a missing required release identity, or a central-lock mismatch.
- Independent approval remains mandatory where protected process requires it. Do not self-approve or bypass it.

If external credentials or independent approvals remain, continue every source, test, documentation, packaging, release, and validation task that does not require them. Report the exact final external blockers with owner, requested action, and validation-after-action.

## 22. Final repository report

Create:

`Infustruction-repo/release/CODESTRA-OBSERVABILITY-FINAL-REPOSITORY-REPORT.md`

It must include one row for every fourteen component repository and every supporting authority with:

- repository;
- role;
- canonical branch;
- canonical PR;
- PR state;
- exact PR head SHA;
- exact-head CI result;
- unresolved review-thread count;
- protected merge SHA;
- release tag;
- immutable image/config artifact identity;
- image/config digest;
- OCI revision verification;
- SBOM digest;
- provenance digest;
- signature verification;
- vulnerability result;
- configuration checksum;
- exposure classification;
- rollback SHA/digest/checksum;
- remaining blocker;
- explicit `REPO_RELEASE_READY=PASS|FAIL|BLOCKED`.

Also include:

- PR reconciliation narrative;
- PostgreSQL Exporter hostname correction evidence;
- Keycloak rendered desired-state checksum;
- Caddy rendered plan checksum;
- Middleware OpenAPI/migration/test evidence;
- SMTP recipient-policy checksum;
- cross-repository lab results;
- installation-bundle validation;
- all external blockers.

Do not claim production was changed, deployed, or certified by this repository-only mission.

## 23. Generate the later server mission

Only after every repository gate above is PASS, generate:

`CODESTRA-OBSERVABILITY-SERVER-PULL-INSTALL-LIVE-MISSION.md`

Place the canonical copy in `Infustruction-repo/missions/` and reference it from `codestra-production-runtime-authority` without duplicating application source.

The server mission must contain only actual, registry-verified values:

- protected merge SHAs;
- immutable release tags;
- exact OCI `repository@sha256:...` identities;
- exact configuration artifact digests;
- deterministic configuration checksums;
- actual previous rollback digests and checksums;
- validated dependency order;
- reviewed health/readiness tests;
- actual backup/restore prerequisites;
- actual Keycloak and Caddy desired-state plan checksums;
- actual Middleware endpoint/OpenAPI version;
- actual alert recipient policy checksum.

It must not contain placeholders, guessed release identities, mutable tags, unresolved values, example digests, or commands that refer to artifacts not verified in the BOM.

If any required value is absent, do not generate a falsely executable server mission. Keep `REPO_RELEASE_READY=FAIL|BLOCKED` and identify the exact remaining owner/action.

## 24. Required final Codex response

The final response must be concise but complete and include:

```text
PHASE=CODESTRA_OBSERVABILITY_REPO_FIRST
MODE=REPOSITORY_ONLY
PRODUCTION_HOST_CONTACTED=NO
PRODUCTION_CHANGED=NO

COMPONENT_REPOSITORIES_REVIEWED=<actual>/14
SUPPORTING_AUTHORITIES_REVIEWED=<actual>/6
OPEN_PRS_RECONCILED=<actual>/<total>
PROTECTED_MERGES=<actual>/<required>
IMMUTABLE_RELEASES=<actual>/<required>
SIGNED_RELEASES=<actual>/<required>
SOURCE_LOCK=<PASS|FAIL|BLOCKED>
INSTALLATION_BUNDLE=<PASS|FAIL|BLOCKED>
ROLLBACK_BUNDLE=<PASS|FAIL|BLOCKED>
SERVER_MISSION_GENERATED=<YES|NO>
REPO_RELEASE_READY=<PASS|FAIL|BLOCKED>
```

Then provide the complete repository table with PRs, protected merge SHAs, release tags, digests, checksums, blockers, and evidence paths.

Do not end with a generic request to provide the mission file. This file is the mission authority. Execute it.
