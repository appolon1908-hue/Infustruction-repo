# Codestra Observability/Security Setup Evidence — 2026-08-29

## Decision

Repository setup for the secure `codestra.media` observability/security edge is **source-ready for review**. Live server installation and production activation remain blocked.

## DNS evidence supplied by the operator

All 14 A records resolve to `37.27.128.39` with TTL 600:

```text
graf  prom  aler  loki  temp  otel  supe
node  cadv  pgex  rdex  blac  allo  bao
```

The operator reported 56/56 checks passing across both GoDaddy authoritative nameservers, Cloudflare, and Google.

Recorded DNS backups:

```text
klyrow-backups/godaddy-codestra-media-observability-20260829T180439Z
klyrow-backups/godaddy-codestra-media-observability-postchange-20260829T180556Z
```

DNS evidence does not prove service exposure, authentication, TLS, private binding, or runtime health.

## Exact repository evidence

| Responsibility | Repository / branch | Exact head | CI evidence | Result |
|---|---|---|---|---|
| Caddy edge | `appolon1908-hue/Caddy:feature/observability-edge-routing-v1` | `d73da73aad27c7ef4847b6e8a1dc248cddbd8ea2` | `Validate Caddy source authority` run `33268547473` | PASS |
| Keycloak OIDC contract | `appolon1908-hue/Keycloak:feature/observability-oidc-clients-v1` | `a06f14faba71d3f5527dff85abad36ba23d580f6` | `Validate Keycloak GitOps` run `33268936856` | PASS |
| Private network/firewall | `appolon1908-hue/Infustruction-repo:feature/observability-private-network-v1` | predecessor `2de4d561910329a5f389429574ef8bfbc0d64ac9` | `Validate observability topology` run `33268560713` | PASS before this evidence-only commit |
| Grafana app contract | `appolon1908-hue/Codestra-Grafana-:feature/private-bind-keycloak-oidc-v1` | `f83e8235d01ec9c5d8a89f064170872923a5f8f6` | `Validate Codestra Grafana integration` run `33269022076` | PASS |
| Superset app contract | `appolon1908-hue/Superset:feature/private-bind-keycloak-oidc-v1` | `7ddf9932caaf50fff406220739eb08844990c489` | `Validate Codestra Superset integration` run `33269031021` | PASS |
| OpenBao app contract | `appolon1908-hue/Codestra-OpenBao:feature/private-bind-keycloak-oidc-v1` | `a3f6c4469cdf7acee032b024fcc3c707b7e71645` | `Validate Codestra OpenBao integration` run `33269083948` | PASS |

## Source-ready behavior

The reviewed source now defines:

- Caddy TLS sites for all 14 hostnames;
- private upstream proxies only for Grafana, Superset, and source-restricted OpenBao;
- controlled public `403` responses for the eleven native monitoring/telemetry hostnames;
- exact Keycloak OIDC client IDs, callbacks, PKCE, role separation, and external secret ownership;
- Grafana loopback binding, Keycloak OIDC, strict role mapping, anonymous access denial, and private datasources;
- Superset loopback binding, Keycloak OIDC, approved-role extraction, secure proxy/cookie settings, and curated-read-model-only policy;
- OpenBao loopback listeners, Caddy source restrictions, plan-only OIDC roles, exact callbacks/audience, and native-policy requirements;
- a machine-readable private service graph and default-deny firewall intent;
- DNS/TLS/HTTP/private-denial/external-port smoke-test tooling.

## Live activation blockers

The following remain mandatory before a production change:

1. Promote the three OIDC client contracts into Keycloak's protected managed/creatable client engine, export allowlists, plan/apply, and rollback coverage.
2. Generate/retrieve client secrets through the approved protected process and inject them into service secret files/environment; never commit them.
3. Install each service from its accepted immutable source/image with native listeners bound to loopback/private networks.
4. Select and certify OpenBao storage, HA, seal, initialization custody, audit, backup/restore, DR, and narrow policy design.
5. Inventory the target server's current listeners, Docker networks, firewall, Caddy config/checksum, resources, and rollback state.
6. Apply a separately reviewed firewall plan preserving restricted SSH and Caddy 80/443 while denying native service ports publicly.
7. Validate Caddy against the exact accepted source, back up the live config, rehearse rollback, and only then reload.
8. Prove TLS certificate issuance and hostname SANs for all 14 names.
9. Prove Grafana/Superset OIDC login and role denial; prove OpenBao network, OIDC, and policy isolation.
10. Run post-deploy and genuinely external port smoke tests.
11. Record post-change exact SHAs, image digests, configuration checksums, smoke evidence, and explicit approval.

## Current activation state

```text
DNS_CONFIGURED=YES
REPOSITORY_SOURCE_READY_FOR_REVIEW=YES
CADDY_RELOADED=NO
TLS_CERTIFICATES_PROVEN=NO
KEYCLOAK_CLIENTS_APPLIED=NO
SERVICE_SECRETS_INSTALLED=NO
SERVICES_INSTALLED_OR_CHANGED_BY_THIS_WORK=NO
FIREWALL_APPLIED=NO
OPENBAO_INITIALIZED=NO
EXTERNAL_PORT_SCAN_PASSED=NO
PRODUCTION_ACTIVATED=NO
```
