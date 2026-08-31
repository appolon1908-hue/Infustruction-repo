# Stage 6 Docker Authorization Decision

Captured: 2026-08-31 (America/Santo_Domingo)

## Decision

`DOCKER_AUTHORIZATION_MODEL=B`

No authorization change was applied. The current workflow requires Docker
operations that include registry login, immutable image pulls, image and
container inspection, network inspection and creation, temporary container
create/copy/remove, Compose render/up/run/logs/down, migration execution, and
the isolated evidence collector's pull/run operations.

Adding `keycloak-deploy` to the `docker` group would provide unrestricted,
root-equivalent host control. That is broader than the requested minimum
privilege. The minimum acceptable design is a root-owned fixed deployment
wrapper with a dedicated sudoers rule that:

- accepts only the reviewed `deploy`, `rollback`, `status`, and evidence-read
  operations;
- pins the staging project, internal network, container names, Compose file,
  state root, and all three immutable image digests;
- rejects arbitrary Docker arguments, mounts, commands, images, projects,
  networks, ports, production environments, and shell escapes;
- preserves named data volumes during failure rollback;
- emits sanitized status only;
- is invoked by the reviewed protected workflow rather than exposing the
  Docker socket directly to the runner.

This model requires reviewed Infrastructure and Keycloak workflow changes
before installing the wrapper or sudoers rule. No competing Docker-group
authorization was installed.

## Current runner boundary

- Service: `actions.runner.appolon1908-hue-Keycloak.kazan555.service`
- User: `keycloak-deploy`
- Primary group: `keycloak-deploy`
- Supplementary groups: none
- Working directory: `/opt/actions-runner`
- Docker socket: `root:docker`, mode `0660`
- Existing sudo authorization: none

## Safety gate

The required production-write gate does not pass:

- 101 running containers inspected on the core host;
- zero containers expose the complete required ten-field safety read-back;
- 44 expose only a partial read-back;
- nine Middleware containers report `PRODUCTION_DIALING=false` rather than the
  required canonical `DISABLED` state;
- `CALLS_PLACED=0` is not established across the applicable runtime;
- prior preserved evidence from `37.27.128.39` records
  `LIVE_EMAIL_DELIVERY=true` on three Klyrow containers and a public SMTP
  listener.

Therefore `PRODUCTION_BUSINESS_WRITES=DISABLED` cannot be proven. Per the
mission stop conditions, Docker authorization, service restart, permission
testing, workflow rerun, and target promotion were not performed.

```text
DOCKER_SOCKET_ACCESS=FAIL_NOT_AUTHORIZED
DOCKER_SOCKET_MODE_UNCHANGED=true
UNRELATED_USERS_GRANTED_DOCKER_ACCESS=false
PRODUCTION_BUSINESS_WRITES=UNKNOWN
PROMETHEUS_TARGET_STATE=pending
BLACKBOX_TARGET_STATE=pending
PRODUCTION_CHANGED=false
```
