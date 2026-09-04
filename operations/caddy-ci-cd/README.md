# Caddy CI/CD runner bootstrap

This package closes the repository-to-runner handoff for the protected Caddy
release chain without turning an untrusted pull request into a host command.

The Caddy repository already builds, scans, signs, attests, and publishes an
exact production image. Its bounded runtime workflow then requires two separate
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
- starts, reloads, replaces, or retags Caddy;
- authorizes application writes or production traffic movement.

The target host must already provide the reviewed Docker authorization for the
dedicated runner identity. The installer fails before registration when that
authorization is absent. This preserves the existing host security boundary
instead of silently granting root-equivalent Docker access.

Before registering a runner, the controller reads the exact ruleset JSON from
the current Caddy `production` SHA, validates zero bypass actors, zero human
approvals, merge-only promotion, the five governed branches, and the four
required CI checks, then applies it and reads it back. Only after that succeeds
may it retire the two exact legacy rulesets named `AI automated production
gates` and `Protect main`.

## Protected bootstrap environments

Create these environments on `appolon1908-hue/Infustruction-repo` and restrict
them to protected `main`:

- `caddy-staging-runner-bootstrap`
- `caddy-production-canary-runner-bootstrap`

Both require:

### Secrets

- `CODESTRA_GITHUB_ADMIN_TOKEN`: fine-grained token restricted to the Caddy
  repository with **Administration: read and write**, **Environments: read
  and write**, and **Actions: read**. Administration is required for the
  repository runner token and ruleset; Environments is required only for the
  Caddy environment variables; Actions read binds the one-job runner to the
  exact queued workflow job.
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

Production additionally:

- `CADDY_PRODUCTION_MTLS_CLIENT_CERT`
- `CADDY_PRODUCTION_MTLS_CLIENT_KEY`
- `CADDY_PRODUCTION_MTLS_CA_CERT`

Every path must be absolute. The bootstrap verifies every target path before it
mints a one-hour repository runner-registration token.

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

Register the staging runner only while the exact bounded staging job is
already queued. Register the production canary runner only after that same run
has queued `production-readonly-canary`; speculative runner registration is
rejected. The production job still performs only the existing
GET/HEAD/handshake checks and requires byte-identical production runtime
readback before and after.

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
installer checksum, environment, and security assertions, but no credential
values.
