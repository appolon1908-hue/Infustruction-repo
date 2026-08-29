# Codestra observability integration

## Decision

The 14 supplied component repositories are principal source authorities, while this repository
owns their shared topology, environment composition, and release coordination. Component
configuration must be implemented in its principal repository and consumed here by immutable
artifact identity; it must not be copied into this repository.

The review snapshot is recorded in `observability/integration-manifest.v1.json`. It is source
evidence only:

```text
OBSERVABILITY_DEPLOYMENT_ENABLED=false
STAGING_ACCEPTED=NO
ROLLBACK_REHEARSED=NO
GO_LIVE=NO_GO
```

## Audit outcome

All accessible component `main` branches are upstream source mirrors with
`deployment_enabled=false`. Validated but unaccepted private-bind/OIDC candidates exist for
Grafana, Superset, and OpenBao, and draft infrastructure PR #2 supplies proposed network and
firewall controls. No accepted lineage currently contains the full component-owned production
configuration and immutable release artifacts required by its authority document.

### Blocking findings

| ID | Severity | Finding | Required disposition |
| --- | --- | --- | --- |
| OBS-H1 | High | The upstream-sync workflows replace `upstream/` from mutable `main`/`master` refs and write directly to persistent branches. Several also push `staging` and `production`. | Pin an reviewed upstream commit or signed release, validate license/SBOM/secret scan, and update through a protected PR. Sync automation must never promote to production. |
| OBS-H2 | High | Exporter and Alloy sync workflows use mutable `actions/checkout@v4`; the core mirrors use a full commit. | Pin every Action to a full reviewed commit SHA and enforce the rule in CI. |
| OBS-H3 | High | No accepted component lineage has a digest-pinned image, complete config bundle, release manifest, or rollback artifact. | Each authority repository must publish a signed, scanned artifact and component config contract before this manifest can reference it. |
| OBS-H4 | High | Private services are assigned public DNS records targeting one address, but firewall/private-network enforcement is not proven. | Bind native ports only to private interfaces or internal container networks and prove public denial from an external runner. DNS is not an access control. |
| OBS-H5 | High | OpenBao has no upstream lock/snapshot and no initialization, unseal/recovery, workload-auth, policy, audit, backup, or rotation implementation. | Complete and rehearse the OpenBao security lifecycle before any runtime secret is authoritative. |
| OBS-H6 | High | The canonical crawler does not yet expose the required internal metrics endpoint or reviewed OTLP pipeline. | Add bounded-cardinality metrics, trace propagation, redaction tests, and a private `/internal/metrics` path in `kyqra-crawler`. |
| OBS-H7 | High | No staging environment proves ingestion, storage, queries, alerts, retention, backup, restore, or rollback across the stack. | Build isolated staging, execute the acceptance matrix below, and record immutable evidence before production approval. |
| OBS-M1 | Medium | `appolon1908-hue/Codestra-Postgres-Exporter` returns 404. | Create/restore the principal repository and record its upstream and hostname authority. |
| OBS-M2 | Medium | `temp.codestra.media` is the declared Tempo hostname and may be an unintended abbreviation. | The repository owner must explicitly accept it or correct the authority documents before certificates and dashboards depend on it. |
| OBS-M3 | Medium | Singleton exporter DNS names do not model per-host/per-database target discovery. | Use private service discovery or `file_sd`; keep exporter endpoints instance-specific and private. |

## Target data paths

```text
Application OTLP (mTLS)
  -> OpenTelemetry Collector
      -> Tempo (traces)
      -> Loki (redacted application logs)
      -> Prometheus scrape endpoint (bounded application metrics)

Hosts / containers
  -> Node Exporter + cAdvisor + Alloy
      -> Prometheus (metrics)
      -> Loki (redacted infrastructure logs)

PostgreSQL / Redis / approved endpoints
  -> PostgreSQL Exporter / Redis Exporter / Blackbox Exporter
      -> Prometheus
          -> Alertmanager
          -> Grafana

Grafana -> read-only Prometheus, Loki, and Tempo data sources
Superset -> curated least-privilege analytics read models only
OpenBao -> workload secrets and short-lived credentials, never telemetry payload storage
```

OpenTelemetry Collector owns application OTLP processing. Alloy owns host/container discovery
and infrastructure telemetry. This boundary prevents duplicate collection and double billing.

## Required component-owned artifacts

Each principal repository must add and validate these artifact classes:

| Repository role | Required artifacts |
| --- | --- |
| Grafana | server config; OIDC/RBAC template; provisioned read-only data sources; dashboard providers; crawler and platform dashboards; backup/restore and upgrade runbooks |
| Prometheus | scrape and service-discovery config; recording/alert rules; label/cardinality policy; retention/storage config; config tests |
| Alertmanager | routing, grouping, inhibition, receiver templates, OpenBao references, config tests; a null receiver remains default until approved receivers exist |
| Loki | tenancy, schema, storage, limits, retention, compaction, query limits, backup/restore plan |
| Tempo | OTLP ingest, storage, retention, compaction, query, metrics-generator policy, backup/restore plan |
| OpenTelemetry | OTLP mTLS receivers; memory/batch/resource processors; attribute redaction; tail/head sampling decision; exporters; self-telemetry |
| Alloy | private discovery, relabeling, log redaction, positions persistence, export queues, backpressure limits |
| Exporters | least-privilege access, collector/query policy, private binding, health checks, per-instance discovery metadata |
| Superset | OIDC/RBAC, curated analytics databases, least-privilege read roles, migration, backup/restore and audit policy |
| OpenBao | TLS, integrated storage, initialization ceremony, recovery/unseal, workload auth, environment-scoped policies, audit devices, backup/restore, rotation/revocation |

## Crawler telemetry contract

The canonical crawler integration must provide:

- a private `/internal/metrics` endpoint that is not routed by Kong;
- OpenTelemetry context propagation through HTTP and BullMQ payloads;
- trace spans for API acceptance, queue delay, fetch tier, extraction, persistence, and delivery;
- bounded metric labels—no tenant IDs, job IDs, URLs, or raw domains as unbounded labels;
- structured logs correlated by generated request/job/trace IDs;
- redaction tests covering authorization, cookies, credentials, HMAC material, database URLs, and page content;
- SLO metrics for acceptance, queue latency, crawl success, delivery latency, outbox backlog, and resource saturation.

## Staged rollout

1. **Governance:** close OBS-H1/H2, protect branches, and publish signed component artifacts.
2. **Secrets and network:** establish OpenBao, private networking, mTLS, and external denial tests.
3. **Backends:** deploy empty Prometheus, Alertmanager-null, Loki, and Tempo in isolated staging.
4. **Collectors:** add OpenTelemetry and Alloy with export queues and no application credentials.
5. **Exporters:** add one target class at a time; verify least privilege and cardinality.
6. **Crawler canary:** enable telemetry for one write-disabled crawler replica and prove zero secret leakage.
7. **Views:** provision Grafana; connect Superset only to curated read models.
8. **Alerts:** add receivers after route, inhibition, duplicate, retry, and dead-receiver tests.
9. **Resilience:** rehearse backup/restore, backend outage buffering, certificate rotation, and rollback.
10. **Production:** promote immutable accepted identities with a 24-hour canary and explicit approval.

## Acceptance matrix

Production remains blocked until all rows pass with committed evidence:

| Gate | Required proof |
| --- | --- |
| Supply chain | exact source commits, image digests, signatures, SBOMs, vulnerability and secret scans |
| Network | native ports denied publicly; only Grafana/Superset authenticated HTTPS is exposed |
| Identity | environment-scoped workload identities; least-privilege OpenBao policies; rotation rehearsed |
| Data safety | telemetry redaction tests; no secrets/PII in labels, logs, spans, dashboards, or datasets |
| Function | metrics/logs/traces visible end-to-end; synthetic probes and alerts reach a test receiver |
| Cardinality | label/attribute budgets pass at 3x expected load |
| Retention | automated deletion verified for metrics, logs, traces, dashboards, and analytics caches |
| Resilience | collector buffering, backend outage, full disk, restart, backup/restore, and rollback rehearsed |
| Crawler | write-disabled canary emits telemetry without changing external systems |

## Explicit non-goals

- Grafana and Superset do not mutate business systems.
- Observability identities do not receive provider, broker, Odoo-write, or crawler credential-vault secrets.
- Public DNS does not authorize public access to native service ports.
- Upstream-source synchronization does not authorize deployment or environment promotion.
