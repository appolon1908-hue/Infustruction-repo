# Stage 6 Source Lock Gate Evidence

Captured: `2026-08-31T14:36:23Z`

This is source and read-only evidence. It performed no deployment, restart,
migration, secret change, monitoring activation, production activation, or
Klyrow/Postal mutation.

## Preserved pre-rebase state

The original uncommitted evidence remains preserved at
`/root/stage6-evidence-pre-rebase-20260831T130546Z`.

| Evidence | SHA-256 |
|---|---|
| Original Git status | `7db1598c8e882c5542feac9cd7daf7619331738ddd0e7327b0b6ca829f1d2c19` |
| Original four-file checksum list | `26d2f5b0a4c62d1126b8f86841969243325e9832d5dc3d50d42f1a77c3f9f220` |
| Original uncommitted patch | `a3814b55d62654737ad1da154b0866e76a0ad1cf306bfb12e66d8e1ea12b612f` |
| Original resolved YAML | `01e1ed2cf2fd72c9aadac413cc031784575d7229f99d4d8e4ee2bbe51e283c2b` |

The original branch remains
`release/stage6-stage8-runtime-certification-20260831-rerun` at
`0328efbbd55ea5de32d8f3e4aba8600afb8a68e1`, with the same four untracked
files. The reconciliation branch was created independently from exact
Infrastructure `main` at
`244a743a771d1f93c1445392bb45f8325908ca72`.

## Protected-head refresh

All 23 component repositories were fetched into dedicated detached checkouts.
Every checkout is clean, its `HEAD` equals the lock, and the lock equals the
freshly fetched authoritative `main` head.

Seven heads advanced relative to the Infrastructure evidence base lock:

| Component | Current authoritative `main` | Rollback Git SHA |
|---|---|---|
| Middleware | `eaf3967ee050a5beb3400ae50fe2ba5fe0ab2a94` | `81c50c7447a87f7c83544cdc4ff9d27c5059a524` |
| n8n | `b620860c04bf0fe6998c5fc25857262aa5c89d74` | `4d35472772f60c5af616ffac1f902d626643d02d` |
| Kong | `961edbf56e29ce78f305273c3efeec386a2bba62` | `3594fe25b8fe36633c1de95a8e485c72f32a60f8` |
| Keycloak | `6ce1806c5d3ba63fd89c3b0168181f944c0d7c4f` | `303e2edef2219c5eb3ac167c309a9717a766d079` |
| SDK | `833b79207b59a8451ea6e7dbfafe8fb64cdb33c0` | `ee8cec5d19cc5c3e03a12f5714031b86b58b4efb` |
| Prometheus | `12b79875cf01033d1a5bd29462fc70bed0e4bbfb` | `eec6ea7d7a63d7debef16de92ef5b6d34395d013` |
| Grafana | `ab06c5c42352a2d14f6b54fe6bf13b6cebdfaca6` | `30b736f98e7bbf16f54280251c6d51a877ff2d8a` |

No newer development or floating head replaced an authoritative `main` SHA.
The exact-head CI re-queries all 23 GitHub refs. Kong and Keycloak are private,
so the workflow requires a least-privilege `STAGE6_SOURCE_READ_TOKEN` with
read-only Contents access to those repositories; the repository-scoped default
token cannot certify them. CI remains fail-closed while that credential is
absent.
The workflow also runs for merge-queue candidates and on a 15-minute drift
schedule, so an external protected-head advance cannot rely indefinitely on a
stale pull-request result.

## Independent gates

| Gate | Result | Evidence |
|---|---|---|
| Repository integrity | `PASS` | `23/23` authoritative-head matches and clean detached checkouts |
| Artifact provenance | `FAIL_PARTIAL` | `10/23` source-only or immutable artifacts pass; unresolved runtime artifacts remain |
| Runtime read-back | `FAIL_INCOMPLETE_CORE_READBACK` | one fresh OpenBao digest match; fresh core-host inventory remains blocked |
| Activation eligibility | `FAIL` | Middleware staging held, Prometheus review pending, Blackbox pending, production disabled |

`SOURCE_LOCK=FAIL`. Repository integrity passing does not promote the combined
source lock while the other three gates remain incomplete.

## Component classifications

- Source-only: Marketing, AI, Communication, Social Control, SDK, Telemetry,
  and this Infrastructure evidence base.
- Custom signed image: Middleware. Exact-head release run `33401833572`
  produced `sha256:cacf169b00cfd95928d192935592a39bcc759f0da7424531a8ba29e7e36c09f0`.
  Independent Cosign verification confirms the image signature, digest-bound
  SPDX attestation, and signed release-manifest bundle against the pinned
  GitHub Actions certificate identity and OIDC issuer.
- Official upstream image plus Codestra config: Odoo, n8n, Prometheus, Grafana,
  Loki, Tempo, Alloy, Node Exporter, cAdvisor, Redis Exporter, Blackbox
  Exporter, Superset, and OpenBao. A class does not pass provenance when its
  immutable upstream digest is still unresolved.
- Unresolved blocking artifact: Social Runtime, Kong, and Keycloak.
- Frozen observed digest: the 22 historical core staging workloads until a
  fresh bounded read-back supplies current container IDs and digest matches.
- Out-of-batch: Klyrow/Postal on `37.27.128.39`.

## OpenBao provenance

The running container is
`389d7605c2a62685e70ac5834121eda9b0919d51eafed51077e51f25749eb4b6`
on `37.27.128.39`. Docker read-back shows
`ghcr.io/openbao/openbao@sha256:5b2486ab0fb90bbc788cc345b0a08616dfb375873ee8be5df3a2fd4d378a67e0`.
Its OCI revision is upstream OpenBao
`ba7ad8861d0578cd4da4f7b9e5a6756d30484f8f`. The separate Codestra
configuration authority remains
`appolon1908-hue/Codestra-OpenBao@5f5e3583585081e450f945440a1fab503bfa8399`.
The digest matches the running upstream artifact, but binding of that runtime
to the locked Codestra configuration is unproven and recorded as drift. The
rollback target is absent runtime plus Nginx backup
`/root/openbao-runtime-backups/20260831T120111Z`.

## Bounded inventory and Klyrow/Postal isolation

The local bounded Docker inventory inspected running container identity,
configured image digest, OCI revision, Compose identity, networks, and named
safety flags. Every Docker read is explicitly bound to the verified local
`unix:///var/run/docker.sock` endpoint; remote contexts and conflicting
`DOCKER_HOST` values are rejected. It found one verified digest match:
OpenBao. This satisfies the nonzero-match floor but not the complete runtime
read-back gate.

The core host `65.109.65.169` still returns
`DENIED: unsupported forced command` for the available bounded credential, so
the 22 Stage 6 core workloads remain frozen historical observations. Their
current container IDs cannot be certified by this run.

Klyrow/Postal is isolated from the Stage 6 source path by a distinct host, a
distinct Compose project, an internal private network, no Middleware host
ports, no declared Klyrow/Postal endpoint in the Stage 6 runtime lock,
`external_effects_enabled=false`, and `production_authorized=false`. The deploy
script creates an inbound Klyrow webhook secret name, but declares no outbound
Klyrow/Postal route. All observed Klyrow/Postal containers were left untouched.

## Held operations

- Private Middleware staging remains held. Its deployment lock still points to
  older digest `sha256:695fa3ce3f50ba4d0ae0784976b946a0a683ca731155e4bd3bd9e90a4670b820`,
  and fresh scoped runtime safety read-back is unavailable.
- The reviewed kernel-maintenance source is present on `main`, but
  `execution_authorized=false`. The owner explicitly withdrew the earlier
  conditional authorization in PR #36 pending package-causality review and
  prohibited reboot, console-access work, kernel changes, and execution of the
  merged plan. No approved window or working console rollback has been
  evidenced. No reboot or host change was attempted.
- Prometheus activation must be a separate PR changing only the private staging
  target from pending to active. Blackbox remains pending and production remains
  unchanged.
- Stage 6 remains staging integration. Stage 7 observability and operational
  readiness is separate. Controlled production activation remains prohibited.

The machine-generated package checksums are in
`reports/runtime-reconciliation/STAGE6-EVIDENCE-SHA256SUMS`.
