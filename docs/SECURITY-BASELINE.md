# Observability and secrets security baseline

## Secrets

Git contains secret references only. Runtime material belongs in environment-separated OpenBao
namespaces such as:

```text
codestra/<environment>/observability/grafana/*
codestra/<environment>/observability/superset/*
codestra/<environment>/observability/alertmanager/*
codestra/<environment>/observability/exporters/postgresql/*
codestra/<environment>/observability/exporters/redis/*
codestra/<environment>/observability/otel/*
codestra/<environment>/crawler/telemetry/*
```

Each workload receives one environment, one identity, exact path prefixes, exact operations, a
short TTL, and audited renewal. Observability workloads never receive unrelated provider or
business-write credentials.

## Telemetry data policy

Reject or redact these values before export:

- authorization, cookie, API-key, password, and private-key material;
- database/Redis URLs containing credentials;
- webhook/HMAC secrets and OpenBao tokens;
- raw request/response bodies and crawled page content by default;
- customer PII unless a classified, reviewed use case requires a bounded field;
- job, tenant, URL, email, phone, or full-domain identifiers in metric labels.

Redaction happens at the application logger and again in the OpenTelemetry/Alloy processing
layer. A planted-secret test must fail CI if any value reaches captured logs or spans.

## Supply chain

- Upstream imports use an explicitly reviewed commit or signed release, never a mutable branch at
  activation time.
- Synchronization produces a PR and cannot push to staging or production.
- Actions are pinned to full commit SHAs.
- Images are pinned by digest, signed, scanned, and accompanied by SBOM/provenance.
- Component authority repositories own their config and release artifacts; this repository pins
  accepted identities only.

## Runtime hardening

- non-root containers, read-only root filesystems, dropped capabilities, and explicit seccomp;
- resource, query, ingestion, cardinality, and retention limits;
- encrypted storage and transport where telemetry classification requires it;
- audit logs for Grafana, Superset, and OpenBao administrative changes;
- immutable backups with restore rehearsals and measured RTO/RPO;
- no public admin, debug, pprof, metrics, readiness-detail, or native service endpoint.

## Activation rule

`observability/integration-manifest.v1.json` remains fail-closed while any critical/high finding,
missing digest, unready component config, failed staging gate, or unrehearsed rollback exists.
