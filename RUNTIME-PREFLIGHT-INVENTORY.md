# Codestra Stage 6 Runtime Preflight Inventory

Captured: `2026-08-31T00:19:51.126908+00:00`

Scope: read-only inspection of the core/staging host. No container, systemd unit, database, network, volume, secret, gateway, or application was changed.

## Gate result

`PREFLIGHT=FAIL`

`SOURCE_LOCK=FAIL`

`RUNTIME_DRIFT=YES`

- Running containers: 101 (exact inventory: `reports/runtime-reconciliation/STAGE6-RUNTIME-INVENTORY.csv`).
- Release workloads: 22; Git SHA unestablished: 17; mutable image references: 9.
- Safety-applicable release workloads with incomplete explicit controls: 17.
- Normal-startup migration/module-init violations: 3.
- Unexpected public Docker exposure findings: 0. Expected host ingress is SSH plus Caddy HTTP/HTTPS; all observed container publications are loopback or private-VLAN scoped.
- Backup files exist, including the Stage 6 dump set under `/opt/codestra/backups/stage6-staging/20260830T233931Z-65018df`, but restore verification was not performed in this phase.

## Host and runtime

| Item | Observed |
|---|---|
| Host | `middleware` (`65.109.65.169`, private `10.40.0.1`) |
| OS/kernel | Ubuntu 22.04.5 LTS; Linux 5.15.0-187-generic x86_64 |
| Docker / Compose | 29.7.2 / v5.5.0 |
| Docker objects | 101 running containers; 237 total containers; 47 networks; 985 volumes |
| Routes | Default via `65.109.65.129`; private VLAN `10.40.0.0/24`; Docker bridge routes present |
| Public listeners | SSH 22; Caddy TCP 80/443 and UDP 443 |
| Private/loopback listeners | Caddy/private gateway and application admin endpoints; exact bind evidence retained in preflight transcript |
| systemd | Caddy, Docker/containerd, NATS, SSH, fail2ban, cron, and Keycloak GitHub runner active; exact list in `STAGE6-SYSTEMD-RUNNING.txt` |

## Exact inventory authorities

- 101 containers: `STAGE6-RUNTIME-INVENTORY.csv`.
- 47 Docker networks: `STAGE6-DOCKER-NETWORK-INVENTORY.csv`.
- 985 Docker volumes: `STAGE6-DOCKER-VOLUME-INVENTORY.txt`.
- 222 Git worktrees/repositories under the requested roots: `STAGE6-GIT-REPOSITORY-INVENTORY.csv`.
- 5,704 Compose/deployment/unit/Caddy files under the requested roots: `STAGE6-DEPLOYMENT-FILE-INVENTORY.txt`.

## Stateful and platform read-back

PostgreSQL database names were read from the staging Middleware, Odoo, n8n, identity, SMS, reseller and websocket instances without credentials being printed. One legacy PostgreSQL container and the exporter do not permit the generic read-back and remain unresolved. Redis staging instances are running and healthy. Odoo, Middleware, n8n, Keycloak, Kong, Caddy, Prometheus, Alertmanager, Node Exporter, cAdvisor, Blackbox, Redis Exporter and PostgreSQL Exporter are running. No running OpenBao, Grafana, Loki, Tempo, Alloy or Superset container was observed on this host.

Marketing, AI, Communication, Social control-plane, and `social.codestra.co` have reviewed Git source identities but no unambiguous running Stage 6 workload on this host.

## Source-lock table

| Component | Repository | Lineage | Locked SHA | Image digest | Runtime disposition |
|---|---|---|---|---|---|
| marketing | `appolon1908-hue/Codestra-Marketing-` | `main` | `460ff98f64ef9f0724fe4d2afc51a1a6c5b053dd` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| ai | `appolon1908-hue/Codestra-AI` | `main` | `94d990e269b3a8cdc8176088be65dd02fdac37ea` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| communication | `appolon1908-hue/Codestra-Communication-CC` | `main` | `0ee0dcbd3d4a9405ffc7d14019bf4a1105f91113` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| social_control | `appolon1908-hue/Codesrea-Social-` | `main` | `7bc0dd9ee8a13abbd1463ca106629ad63d957145` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| social_runtime | `appolon1908-hue/social.codestra.co` | `main` | `4f7817f6c6d1bb38fa7d85bb1656eb41865283d5` | `UNRESOLVED_NO_REVIEWED_PUBLISHED_IMAGE` | source locked; image unresolved |
| middleware | `appolon1908-hue/Middleware-` | `main` | `c720e529ea89f1f0d5d035d4ac12a1d5aa30ab62` | `sha256:92954f809e811487f8ac15bde3ba636f3bdb1c37547838e9579bb1fd9567f8da` | locked |
| odoo | `appolon1908-hue/Odoo` | `main` | `3eeb17f8b7efcd9bd90487e5e8e9888717f51138` | `sha256:f54272f31d5f77e4146b887efb3761c98480317daf687e4b4b5e76ed8bcc08c5` | locked |
| n8n | `appolon1908-hue/N8N` | `main` | `4d35472772f60c5af616ffac1f902d626643d02d` | `sha256:cfe2704ff858395503d42548206c2c99ea351a205e941063a9d9b77b0f404478` | locked |
| kong | `appolon1908-hue/Kong` | `main` | `3594fe25b8fe36633c1de95a8e485c72f32a60f8` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| keycloak | `appolon1908-hue/Keycloak` | `main` | `80fc33c7159440e357219903f62ea7fb84914d59` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| sdk | `appolon1908-hue/SDK-repository` | `main` | `ee8cec5d19cc5c3e03a12f5714031b86b58b4efb` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| prometheus | `appolon1908-hue/Codestra-Prometheus` | `main` | `eec6ea7d7a63d7debef16de92ef5b6d34395d013` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| grafana | `appolon1908-hue/Codestra-Grafana-` | `main` | `30b736f98e7bbf16f54280251c6d51a877ff2d8a` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| loki | `appolon1908-hue/Codestra-Loki` | `main` | `75a5deb555547b557466c418af18c99f3cef5556` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| tempo | `appolon1908-hue/Codestra-Tempo` | `main` | `4d91ab83d702c5892a8521804abfe32a57a6825f` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| telemetry | `appolon1908-hue/Codestra-Telemetry` | `main` | `d42d866072ce86175ca03209bd866b3452d606fe` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| alloy | `appolon1908-hue/Codestra-Alloy` | `main` | `104966b2cac822d2cc61f058e53a9dff4a10e03e` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| node_exporter | `appolon1908-hue/Codestra-Node-Exporter` | `main` | `c18166741f36fc05193187dfd614fbde7f8f9253` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| cadvisor | `appolon1908-hue/Codestra-cAdvisor` | `main` | `add839da944d1f213e978b862f22e856008cf52d` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| redis_exporter | `appolon1908-hue/Codestra-Redis-Exporter` | `main` | `784e03d8151136195b3b23c58fe50b68b12cf94f` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| blackbox_exporter | `appolon1908-hue/Codestra-Blackbox-Exporter` | `main` | `acfe1e83dd05a7d8a45cd70f7661fe414fae39b1` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| superset | `appolon1908-hue/Superset` | `main` | `9e9b5a347e1a52cf43f8c6ec2a967379e723d31a` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| openbao | `appolon1908-hue/Codestra-OpenBao` | `main` | `5f5e3583585081e450f945440a1fab503bfa8399` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |
| infrastructure | `appolon1908-hue/Infustruction-repo` | `main` | `b71f922a8d878a47c5a41f6b1cf9e8b47f9fba68` | `UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE` | source locked; image unresolved |

Kong `3594fe25...` is one approved commit ahead of required merge `186630b4...`. Social runtime remains exactly `4f7817f6...`.

## Drift and blockers

1. 17 of 22 release workloads do not expose an exact Git SHA.
2. 9 of 22 release workloads use a mutable runtime image reference.
3. 17 safety-applicable release workloads lack the complete explicit false/disabled set; absence is ambiguous even though no inspected allowlisted flag was explicitly true.
4. Middleware still runs `alembic upgrade head` at normal startup; two long-running Odoo services still use `--init`.
5. Several participating source repositories have no reviewed published runtime image/digest, rollback SHA, or rollback digest; the YAML records these as unresolved rather than inventing identities.
6. `private-integration-gateway-1` remains unknown/frozen: root-owned `/opt/middleware/integration-gateway/compose.yaml`, private-VLAN port 8095, shared edge network, and unproved Git owner.
7. Prior evidence on host `37.27.128.39` recorded live email delivery; this core-host read-back does not erase that independent fail-closed finding.

## Proposed Phase 2 backup plan (not executed)

1. Freeze the exact affected staging scope and record current image/config rollback identities.
2. Export every staging PostgreSQL database with checksums; separately archive Odoo filestore and n8n data.
3. Capture Redis persistence/config where required, Keycloak export, Kong declarative/database state, Caddy config, OpenBao policies/config, Compose definitions, and sanitized environment key names.
4. Store outside live volumes with owner-only permissions; record source, destination, timestamp, checksum and exact restore command.
5. Verify archives and perform isolated restore tests before any reconciliation. The existing dump set is evidence of files, not a substitute for this verification gate.

Phase 2 has not begun.
