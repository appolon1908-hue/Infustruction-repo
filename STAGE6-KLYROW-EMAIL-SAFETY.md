# Stage 6 Klyrow Email Safety Evidence

Captured: 2026-08-31 (America/Santo_Domingo)

## Access result

- Target: `37.27.128.39`
- Documented alias: `klyrow-server`
- User: `klyrow-deploy`
- Documented dedicated identity: present; private-key contents were not read
- Initial SSH result: PASS
- Subsequent SSH result: `CONNECTION_REFUSED`
- Route: public route through the core host default gateway
- Port 22 was initially reachable and later actively refused connections

The initial authenticated session confirmed hostname
`Ubuntu-jammy-latest-amd64-base.zst` and the restricted `klyrow-deploy`
identity. Direct Docker access was denied as designed. The existing root-owned
`klyrow-stack` interface permitted fixed read-only `inventory`, `status`, and
`validate-runtime` operations.

## Runtime inventory

The Klyrow stack reported 21 running containers. Safety-relevant applications:

| Container | Image | State |
|---|---|---|
| `klyrow-gateway-1` | `codestra/klyrow-gateway:webmail-20260828` | healthy |
| `klyrow-worker-1` | `codestra/klyrow-gateway:webmail-20260828` | healthy |
| `klyrow-smtp-relay-1` | `codestra/klyrow-gateway:smtp-hotfix-20260826.9` | healthy |
| `klyrow-postal-provisioner-1` | `codestra/klyrow-postal-provisioner:webmail-20260828` | healthy |
| `klyrow-postal-smtp-1` | `ghcr.io/postalserver/postal:3.3.7` | healthy |

The wrapper reported Compose authority checksum
`099a03933437b5070ca095cffa122bcb894c9ed86f7ba41a53e57936491c42bf`
for `/root/klyrow.com/docker-compose.yml`. Image digests and effective
allowlisted environment values could not be read before SSH became
unavailable.

## SMTP exposure

Observed listeners before access loss:

| Listener | Exposure | Purpose/capability |
|---|---|---|
| `37.27.128.39:25` | public | Postal SMTP; live-send capability unresolved |
| `10.40.0.4:587` | private VLAN | authenticated submission purpose indicated by architecture; Stage 6 routing unresolved |
| `127.0.0.1:2525` | loopback | internal SMTP path; capability unresolved |

Preserved prior evidence records `LIVE_EMAIL_DELIVERY=true` on
`klyrow-gateway-1`, `klyrow-worker-1`, and `klyrow-smtp-relay-1`. The current
read-back could not be completed, so those values and Stage 6 applicability
remain UNKNOWN rather than being inferred.

```text
KLYROW_HOST_ACCESS=FAIL
KLYROW_LIVE_EMAIL_DELIVERY=UNKNOWN
STAGE6_LIVE_EMAIL_PATH=UNKNOWN
```
