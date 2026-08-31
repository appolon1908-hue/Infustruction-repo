# Stage 6 Klyrow Email Safety Evidence

Captured: 2026-08-31T12:24:43Z

Remediation checkpoint: 2026-08-31

## Access and authority

- Target: `37.27.128.39`
- Documented alias/user: `klyrow-server` / `klyrow-deploy`
- Restricted interface: root-owned `klyrow-stack`
- Current access: PASS
- Direct Docker access: denied as designed
- Deployed gateway revision: `9684fd55bdbc64a971a17a291ff293a178a2ebac`
- Compose authority: `/root/klyrow.com/docker-compose.yml`
- Compose checksum: `099a03933437b5070ca095cffa122bcb894c9ed86f7ba41a53e57936491c42bf`

The earlier transition from successful authentication to an actively refused
TCP connection was transient. Current TCP and authenticated access succeed.
Available evidence does not establish whether the earlier refusal was caused
by sshd, firewall/rate protection, or provider-edge behavior, so the cause
remains UNKNOWN.

The controlling repository is `appolon1908-hue/klyrow.com`. Protected `main`
was `57678867166043c2351d56f58ad47785e9456c18` when remediation began; the
production gateway remains on `9684fd55bdbc64a971a17a291ff293a178a2ebac`.
The effective override originates from the root-owned production runtime `.env`
loaded through the Compose `env_file` contract: the gateway did not pin
`KLYROW_SAFE_MODE`, and the worker allowed `${KLYROW_SAFE_MODE:-true}`.

Fail-closed correction PR:
`appolon1908-hue/klyrow.com#57`, exact head
`9aa9cde6c28e9c19ce4b3673916d93095d3b7bbe`. It forces safe mode and gate
approval off in base production Compose and makes `LIVE_EMAIL_DELIVERY` an
independent code-level opt-in. Focused regression tests passed (17 tests), and
all protected checks later passed.

## Protected merge and deployment attempt

PR #57 received CODEOWNER approval on its exact head, passed all protected
checks, and was squash-merged as
`24619abe4e8b1b3f2c231bca5d138dd45c014a07`. Post-merge main CI run
`33393511697` passed.

Before deployment, restricted operator backup
`/var/backups/codestra-operators/klyrow/20260831T125047Z` validated. The
rollback-plan read-back identified root-maintained override checksum
`345093a338012f9d32f6d7569f20b8c62503058731e0d4c5a7765dbe667dcc6e`.

`klyrow-stack stage` passed. `klyrow-stack deploy` then failed because the
Compose candidate attempted to create `klyrow-gateway-1` while the existing
healthy container still owned that name. The restricted rollback command was
attempted and denied because its root-maintained approval marker was absent.
No direct Docker or host workaround was used.

The original gateway remained healthy on revision
`9684fd55bdbc64a971a17a291ff293a178a2ebac`. Its final GET-only read-back was:

```text
safe_mode=false
production_gate_approved=true
production_gate_open=true
outbox_active=0
```

Consequently the fail-closed correction is merged but not deployed. The live
email path remains enabled. `outbox_active=0` is not an authoritative sent-mail
counter, so emails sent during remediation remain UNKNOWN rather than being
asserted as zero.

## Current live safety read-back

Only GET requests were made over loopback on the Klyrow host. The production
gateway returned:

```text
safe_mode=false
production_gate_approved=true
production_gate_open=true
revision=9684fd55bdbc64a971a17a291ff293a178a2ebac
```

At that exact revision, the gateway creates a delivery outbox record when
`safe_mode` is false, and its outbox worker is active when `safe_mode` is
false. Therefore the effective live-email delivery capability is enabled.
The reviewed Compose content at the same revision defaults
`KLYROW_SAFE_MODE=true` and `LIVE_EMAIL_DELIVERY=false`; the live read-back is
configuration drift from those fail-closed defaults.

Historical `LIVE_EMAIL_DELIVERY=true` evidence for `klyrow-gateway-1`,
`klyrow-worker-1`, and `klyrow-smtp-relay-1` cannot be superseded because the
current production delivery gate is open.

## Runtime and SMTP surface

The restricted inventory reports 21 running containers, including:

| Container | Image | State |
|---|---|---|
| `klyrow-gateway-1` | `codestra/klyrow-gateway:webmail-20260828` | healthy |
| `klyrow-worker-1` | `codestra/klyrow-gateway:webmail-20260828` | healthy |
| `klyrow-smtp-relay-1` | `codestra/klyrow-gateway:smtp-hotfix-20260826.9` | healthy |
| `klyrow-postal-provisioner-1` | `codestra/klyrow-postal-provisioner:webmail-20260828` | healthy |
| `klyrow-postal-smtp-1` | `ghcr.io/postalserver/postal:3.3.7` | healthy |

Observed listeners:

| Listener | Exposure | Purpose/capability |
|---|---|---|
| `37.27.128.39:25` | public | Postal SMTP transport |
| `10.40.0.4:587` | private VLAN | submission path |
| `127.0.0.1:2525` | loopback | internal SMTP path |

The listener alone is not the failure. The applicable production gateway can
currently enqueue delivery and its production gate is open, so a live Stage 6
email path cannot be certified disabled.

```text
KLYROW_HOST_ACCESS=PASS
KLYROW_SSH_FAILURE_CAUSE=UNKNOWN
KLYROW_LIVE_EMAIL_DELIVERY=true
STAGE6_LIVE_EMAIL_PATH=ENABLED
```
