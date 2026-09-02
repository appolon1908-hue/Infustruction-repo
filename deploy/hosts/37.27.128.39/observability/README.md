# Codestra observability production bundle — 37.27.128.39

This directory is the Git-controlled host integration authority for the central
Codestra observability, analytics, and secrets stack assigned to
`37.27.128.39`.

## Repository phase

`REPOSITORY_PREPARED_NOT_DEPLOYED`

This change prepares source, configuration, validation, installation, rollback,
and evidence contracts. It does **not** connect to a server, alter DNS, reload
Caddy, initialize OpenBao, send email, or activate any runtime.

## Included services

- Prometheus
- Alertmanager
- Grafana
- Loki
- Tempo
- OpenTelemetry Collector
- Grafana Alloy
- Node Exporter
- cAdvisor
- Redis Exporter
- PostgreSQL Exporter
- Blackbox Exporter
- Apache Superset
- OpenBao
- dedicated PostgreSQL and Redis dependencies
- dedicated OAuth2 proxies for Prometheus and Alertmanager

All service images are assembled from a repository plus a mandatory immutable
`sha256` digest. Placeholder digests make validation and installation fail
closed.

## Canonical addresses

| Service | Canonical address | Exposure |
|---|---|---|
| Grafana | `https://graf.codestra.media` | Keycloak-authenticated UI |
| Prometheus | `https://prom.codestra.media` | Keycloak-authenticated operator UI |
| Alertmanager | `https://aler.codestra.media` | Keycloak-authenticated operator UI |
| Loki | `loki.codestra.media` | private authenticated API |
| Tempo | `temp.codestra.media` | private authenticated API |
| OpenTelemetry | `otel.codestra.media` | mTLS/service-authenticated ingest |
| Alloy | `allo.codestra.media` | private collector health |
| Node Exporter | `node.codestra.media` | private metrics |
| cAdvisor | `cadv.codestra.media` | private metrics |
| Redis Exporter | `rdex.codestra.media` | private metrics |
| PostgreSQL Exporter | `postgres-exporter:9187` | private service identity only |
| Blackbox Exporter | `blac.codestra.media` | private probe service |
| Superset | `https://supe.codestra.media` | Keycloak-authenticated UI |
| OpenBao | `https://bao.codestra.media` | protected UI/API |

Native service ports are not published by this Compose project. Caddy reaches
only approved UI or ingest services through the external `codestra-edge`
network. Exporters and storage APIs remain private.

## Alert path

The normal production notification path is:

```text
Prometheus
  -> Alertmanager
  -> authenticated Middleware alert command
  -> durable inbox/outbox
  -> approved SMTP adapter
  -> appolon@codestra.co
```

Alertmanager is not an unrestricted SMTP client. The fixed sender and recipient
policy is defined in `contracts/SMTP-ALERT-POLICY.yaml`. A direct SMTP fallback
is not active in this bundle; its narrow emergency boundary must be reviewed
separately before use.

## Secrets

No secret value belongs in Git. The deployment reads protected files under
`OBSERVABILITY_SECRETS_DIR`. `manifests/OBSERVABILITY-SECRET-REFERENCE-MANIFEST.yaml`
lists every required file and owner.

OpenBao initialization, unseal/recovery custody, and root-token handling are
deliberately not automated. `scripts/bootstrap_openbao.sh` runs only after an
authorized security owner has initialized and unsealed OpenBao and provided a
short-lived bootstrap token file.

## Source and release process

1. Merge and release the component repositories identified in
   `manifests/OBSERVABILITY-PRODUCTION-BOM.yaml`.
2. Replace every placeholder source SHA, image digest, and rollback digest with
   reviewed immutable evidence.
3. Run `python3 scripts/validate_bundle.py --source`.
4. Create protected secret files outside Git.
5. On the target host run `python3 scripts/validate_bundle.py --runtime
   --env-file /etc/codestra/observability/production.env`.
6. Render and validate Compose and application configuration.
7. Create a current backup and rollback checkpoint.
8. Run `scripts/install.sh --plan`.
9. Apply only through the later approved server mission.

The installer refuses to continue when the host is not `37.27.128.39`, image
digests are unresolved, required secret files are absent, native ports are
published, OpenBao is sealed, or the rollback checkpoint is missing.

## External-effect safety

This bundle does not authorize business, marketing, campaign, customer, SMS,
voice, social, advertising, model, or financial effects. The only eventual
external effect in scope is a bounded operational alert email to
`appolon@codestra.co`, after mailbox verification and an approved canary.

## Rollback

`scripts/rollback.sh` restores only a previously captured observability release
directory and Compose declaration. It does not delete data, reset alert state,
or mutate unrelated Klyrow, Postal, Telnexa, Kyqra, Middleware, Caddy, Keycloak,
DNS, or firewall configuration.
