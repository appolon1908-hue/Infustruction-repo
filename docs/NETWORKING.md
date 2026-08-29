# Observability networking contract

## Exposure policy

Only Caddy may bind public `80/443`. Grafana and Superset may be reachable through authenticated
HTTPS ingress after OIDC/RBAC acceptance. Every other observability and secrets endpoint is
private-only even when a public DNS record exists.

| Component | Native ports | Exposure |
| --- | --- | --- |
| Grafana | `3000/tcp` | private behind Caddy; authenticated HTTPS only |
| Superset | `8088/tcp` | private behind Caddy; authenticated HTTPS only |
| Prometheus | `9090/tcp` | private monitoring network |
| Alertmanager | `9093/tcp`, `9094/tcp` | private monitoring network |
| Loki | `3100/tcp` | private monitoring network |
| Tempo | `3200/tcp`, `4317/tcp`, `4318/tcp` | private monitoring network |
| OpenTelemetry Collector | `4317/tcp`, `4318/tcp`, self-metrics ports | private application/monitoring networks; mTLS ingestion |
| Node Exporter | `9100/tcp` | per-host private binding; Prometheus only |
| cAdvisor | `8080/tcp` | per-host private binding; Prometheus only |
| PostgreSQL Exporter | `9187/tcp` | private database/monitoring networks; Prometheus only |
| Redis Exporter | `9121/tcp` | private data/monitoring networks; Prometheus only |
| Blackbox Exporter | `9115/tcp` | private monitoring network; Prometheus only |
| Alloy | component-specific listeners and admin UI | private sources/monitoring network only |
| OpenBao | `8200/tcp`, cluster port | private workload/secrets networks; TLS required |

## Network zones

```text
public-edge:        Caddy only
application:        Kyqra and other product runtimes
telemetry-ingest:   OpenTelemetry / Alloy receivers
observability:      Prometheus, Alertmanager, Loki, Tempo, Grafana
analytics:          Superset and curated read models
secrets:            OpenBao and approved workload identities
data:               PostgreSQL/Redis and monitoring-only exporters
```

Default-deny rules must be enforced between zones. Staging and production use separate hosts or
equivalent independently controlled network planes; sharing a Docker network is not isolation.

## Required verification

- External probes prove every private native port is unreachable.
- Internal probes prove only documented source-to-destination flows.
- Exporter targets use private addresses/service discovery, not public service DNS.
- OTLP ingestion requires a reviewed workload identity and mTLS.
- Blackbox targets pass an allowlist and private-address/redirect-chain SSRF guard.
- Grafana/Superset ingress rejects unauthenticated requests and does not forward identity headers
  from untrusted clients.
- DNS and certificate changes are recorded separately from deployment activation.
