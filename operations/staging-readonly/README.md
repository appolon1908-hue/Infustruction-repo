# Codestra immutable staging, rollback, and read-only production canary

This directory is the repository authority for deploying one already-built,
digest-qualified Codestra candidate to isolated staging, certifying it, proving
recovery, and then allowing the same immutable identities into a production
GET/HEAD-only canary capped at one percent.

It does **not** build, tag, push, or retag an image. It does not permit live
email, SMS, PSTN, provider delivery, campaign activation, Odoo writes, n8n
external delivery, or any other business effect.

## Required GitHub environments

### `staging-readonly`

Configure the environment on the authoritative `Infustruction-repo` repository.
It must permit deployment only from protected `main` and must expose these
secrets without printing their values:

| Secret | Purpose |
|---|---|
| `STAGING_CANONICAL_CANDIDATE_B64` | Base64 of the completed `codestra.release-control.v1` candidate JSON. |
| `STAGING_ENDPOINT_MANIFEST_B64` | Base64 of the completed protected endpoint/counter manifest. |
| `STAGING_READONLY_BEARER_TOKEN` | Read-only identity for version, readiness, capabilities, migration, issuer, route, and counter checks. |
| `STAGING_METRICS_BEARER_TOKEN` | Read-only identity accepted only by protected metrics endpoints. |
| `STAGING_GHCR_READ_TOKEN` | Package-read-only credential for pulling pre-existing digest-qualified images. |
| `STAGING_RESTIC_REPOSITORY` | Off-host Restic repository URI. |
| `STAGING_RESTIC_PASSWORD_FILE` | Existing runner-host path to a protected Restic password file; the value is a path, not the password. |

The runner must have labels `self-hosted` and `codestra-staging`. It must already
have the reviewed Compose checkout beneath `/srv/codestra`, Docker authorization
for the exact release operations, read access to the Odoo filestore and
configuration roots, write access to `/var/backups/codestra`, and Restic access
to the configured off-host repository. This source does not alter SSH, sudo,
Docker socket authorization, firewall, DNS, or host users.

### `production-readonly-canary`

This separate environment is required before the final mode can run. It must be
restricted to protected `main`, use a runner labeled `codestra-production-canary`,
and contain the same candidate, endpoint, bearer, metrics, and GHCR values as
`staging-readonly`. The workflow cryptographically binds the decoded candidate
to the operator-supplied SHA-256 and consumes the exact successful staging
artifact from a named workflow run.

The host must provide the dedicated canary controller declared in the candidate.
The release controller verifies that executable's SHA-256, rejects group/world
writability, and invokes it only with:

```text
apply --candidate <candidate_id> --percent <=1 --methods GET,HEAD --read-only
rollback --candidate <candidate_id>
```

No generic shell command, arbitrary script path, write method, or percentage
greater than one is accepted.

## Protected candidate

Start from `release-control.template.json`, but do not upload the template. A
candidate is executable only after every placeholder is replaced with observed,
reviewed values and the validator accepts all of the following:

- one exact source-lock SHA;
- one exact source SHA and one `image@sha256:...` identity for every workload;
- the matching complete previous-release identities;
- OCI source-revision and repository-label readback for every pulled image;
- one fixed 29-route Kong smoke inventory;
- exact version, readiness, capability, metrics, migration, and Keycloak issuer endpoints;
- the complete all-off live-effect capability map;
- PostgreSQL, Odoo filestore, configuration, and required off-host backup authority;
- one reviewed canary controller and exact SHA-256;
- GET and HEAD as the only canary methods;
- an absolute one-percent ceiling.

Compute the confirmation value from the exact bytes that are stored in the
GitHub environment:

```bash
sha256sum canonical-candidate.json
base64 -w0 canonical-candidate.json
base64 -w0 staging-endpoints.json
```

Do not paste bearer tokens, package tokens, Restic passwords, private keys, or
live provider credentials into either JSON file.

## Execution order

Dispatch `.github/workflows/staging-readonly-certification.yml` from protected
`main` in this strict order:

1. `mode=staging`
2. `mode=rollback-rehearsal`
3. `mode=production-readonly-canary`

Every dispatch requires the exact `candidate_id`, source-lock SHA, and candidate
SHA-256. The canary additionally requires the successful staging run ID and a
percentage greater than zero and no more than one.

## Staging gates

Before changing staging, the controller:

1. validates both protected manifests and required credentials;
2. pulls exact digests only;
3. checks each image's OCI source revision and repository label;
4. renders the candidate override and rejects any image-set difference;
5. reads calls, emails, and SMS counters and requires all three to be zero;
6. produces PostgreSQL, Odoo filestore, and configuration backups;
7. hashes the local recovery point and verifies `SHA256SUMS`;
8. creates an off-host Restic snapshot and records its immutable snapshot ID.

It then runs Compose with `--no-build --pull never`, performs source-version,
readiness, all-off capabilities, protected metrics, migration, Keycloak issuer,
and all 29 Kong route checks, and reads the three live-effect counters again.
Any exception after deployment starts causes immediate deployment of the
complete previous immutable image set.

## Rollback evidence

The rehearsal creates a fresh local and off-host recovery point, deploys the
complete previous source/image set, records previous-release health, readiness,
version and migration results, restores the candidate, records the candidate
results, hashes the Odoo filestore before and after, and confirms zero counter
movement. Evidence records:

- previous-release RTO;
- candidate-restoration RTO;
- observed recovery-point age;
- the zero-write RPO statement;
- filestore file/hash agreement;
- exact previous and candidate check results;
- recovery-point path and Restic snapshot identity.

## Canary stop conditions

The canary controller rolls back immediately on any:

- source SHA or image digest mismatch;
- missing or failed staging evidence;
- readiness, capability, metrics, migration, issuer, or route failure;
- monitoring or counter endpoint loss;
- nonzero or moving call, email, or SMS counter;
- HTTP method outside GET/HEAD;
- canary percentage above the candidate ceiling or one percent;
- error-rate, absolute p95 latency, or p95 regression breach;
- missing, writable, or checksum-mismatched canary controller.

A successful read-only canary does not authorize live business writes. Email,
SMS, PSTN, provider delivery, campaigns, Odoo writes, n8n external delivery, and
other live effects require a separate protected activation candidate, separate
evidence, and separate production change.
