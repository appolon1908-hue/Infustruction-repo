# Caddy CI/CD runner bootstrap

This package closes the repository-to-runner handoff for the protected Caddy
release chain without turning an untrusted pull request into a host command.

The Caddy repository builds, scans, signs, attests, and publishes an exact
production image. Its bounded runtime workflow then requires two separate,
one-job runner identities:

| Target | Required label | Caddy environment |
|---|---|---|
| isolated staging | `codestra-staging` | `staging-readonly` |
| production read-only canary | `codestra-production-canary` | `production-readonly-canary` |

## Security model

The runner is repository-scoped to `appolon1908-hue/Caddy`, configured with
`--ephemeral`, and accepts one job. The runner application is pinned to version
`2.337.0` and the reviewed Linux x64 archive SHA-256 in
`runner-contract.v1.json`.

The bootstrap never:

- accepts the GitHub registration token as a command-line argument;
- stores that token in Git, Terraform state, cloud-init, an artifact, or a file;
- disables SSH host-key validation;
- adds a user to the Docker group;
- creates a broad sudo rule;
- runs the Actions runner as root;
- creates, updates, retires, or deletes a repository ruleset;
- starts, reloads, replaces, or retags Caddy;
- authorizes application writes or production traffic movement.

The target host must already provide the reviewed Docker authorization for the
dedicated runner identity. The installer fails before registration when that
authorization is absent. This preserves the existing host security boundary
instead of silently granting root-equivalent Docker access.

Before registering a runner, the controller reads the exact canonical ruleset
JSON from the current Caddy `production` SHA and independently reads the live
`Protect Caddy promotion branches` ruleset. Both must agree on:

- all five protected branches;
- no bypass actors;
- one exact-head approval;
- stale-review dismissal and last-push approval;
- resolved review conversations;
- squash-only merging and linear history;
- deletion and non-fast-forward protection;
- the four actual required CI contexts.

A mismatch is a hard failure. Ruleset application belongs to the separate,
protected Caddy governance workflow. The runner bootstrap does not change
canonical or legacy rulesets and does not represent ruleset verification as an
account mutation.

## Protected bootstrap environments

Create these environments on `appolon1908-hue/Infustruction-repo` and restrict
them to protected `main`:

- `caddy-staging-runner-bootstrap`
- `caddy-production-canary-runner-bootstrap`

Both require:

### Secrets

- `CODESTRA_REPOSITORY_ADMIN_TOKEN`: fine-grained token restricted to the Caddy
  repository with **Administration: read and write**, **Environments: read and
  write**, and **Actions: read**. Administration is required for the repository
  runner registration token and governance readback; Environments is required
  for the Caddy environment variables; Actions read binds the one-job runner to
  the exact queued workflow job.
- `CADDY_RUNNER_SSH_PRIVATE_KEY`: private key for the existing restricted
  operator identity.
- `CADDY_RUNNER_KNOWN_HOSTS`: pinned known-hosts line for the exact target.

### Variables

Both environments:

- `CADDY_RUNNER_HOST`
- `CADDY_RUNNER_SSH_USER`
- `CADDY_RUNNER_SSH_PORT`

Staging additionally:

- `CADDY_STAGING_ENV_FILE`
- `CADDY_STAGING_DATA_SOURCE`
- `CADDY_STAGING_MTLS_CLIENT_CERT`
- `CADDY_STAGING_MTLS_CLIENT_KEY`
- `CADDY_STAGING_MTLS_CA_CERT`
- `CADDY_STAGING_N8N_CLIENT_SECRET_FILE` — absolute path to the root-owned,
  non-symlink client-secret file used only to mint a maximum-five-minute
  `n8n-automation` token during bounded staging. When omitted, the reviewed
  fixed path is `/etc/codestra/caddy/secrets/n8n-automation-client-secret`.

The client-secret file must exist before runner registration, be owned by root,
have mode `0400` or `0600`, contain the exact secret with no leading/trailing
whitespace, and never be added to Git, Actions variables, workflow inputs,
artifacts, logs, or command-line arguments. The Caddy proof passes only the
**path** to the ephemeral runner. The runtime test uses the secret through
curl's file-reading form, validates the resulting Keycloak token claims, sends
one authenticated GET through Caddy and Kong, requires Middleware's distinctive
`404 command_not_found` response, and verifies Middleware `/version` against the
pinned protected-main SHA, immutable image digest, and configuration checksum.
It sends zero application mutations and enables no provider effects.

Production additionally:

- `CADDY_PRODUCTION_MTLS_CLIENT_CERT`
- `CADDY_PRODUCTION_MTLS_CLIENT_KEY`
- `CADDY_PRODUCTION_MTLS_CA_CERT`

Every path must be absolute. The bootstrap verifies every target path before it
mints a short-lived repository runner-registration token.

## Execution

Dispatch `Caddy CI/CD runner bootstrap` from protected `main`.

For staging:

```text
target=staging
confirmation=BOOTSTRAP_CADDY_STAGING_RUNNER
bounded_runtime_run_id=<exact queued Caddy bounded-runtime run>
```

For the production read-only canary:

```text
target=production-readonly-canary
confirmation=BOOTSTRAP_CADDY_PRODUCTION_CANARY_RUNNER
bounded_runtime_run_id=<same run after its production canary job is queued>
```

Register the staging runner only while the exact bounded staging job is already
queued for the current Caddy `production` SHA. Register the production canary
runner only after that same run has queued `production-readonly-canary`;
speculative runner registration is rejected. The production job still performs
only the existing GET/HEAD/handshake checks and requires byte-identical
production runtime readback before and after. It also downloads and verifies the
staging packet that binds the exact Caddy source/image/configuration to the
Keycloak-authenticated Caddy -> Kong -> Middleware proof.

`replace_stale_registration=true` deletes only the exact named, non-busy Caddy
runner record. It never deletes a differently named runner and refuses a busy
runner.

## Direct restricted-operator use

Where GitHub-hosted SSH is intentionally blocked, run
`scripts/configure_caddy_ci_cd_runner.sh` from the pre-approved management
station using owner-only credential files. The command contract is printed by:

```bash
scripts/configure_caddy_ci_cd_runner.sh --help
```

The generated evidence contains runner identity, labels, online status,
installer checksum, environment, exact queued job, and governance-readback
assertions. It records that the canonical ruleset, unrelated rulesets, and Caddy
runtime were not changed by the bootstrap, and contains no credential values.
