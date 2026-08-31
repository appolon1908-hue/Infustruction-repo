# Isolated Stage 6 staging host

This directory is the only provisioning authority for
`codestra-stage6-staging-01`. It creates one non-production Hetzner Cloud
server, attaches it to an existing staging-only private network, and applies a
dedicated deny-by-default firewall. It does not deploy applications.

## Protected inputs

The `stage6-infrastructure-provisioning` GitHub environment must be restricted
to `main`, prevent self-review, and require a trusted reviewer where the plan
supports it. It requires these names:

Secrets:

- `HETZNER_CLOUD_TOKEN` — project-scoped token permitted to manage the single
  staging server, firewall and network attachment.
- `TF_STATE_ACCESS_KEY` and `TF_STATE_SECRET_KEY` — credentials for the isolated
  state bucket only.

Variables:

- `TF_STATE_BUCKET`, `TF_STATE_ENDPOINT`, `TF_STATE_REGION`.
- `STAGE6_TFVARS_JSON` — reviewed non-secret values matching `variables.tf`.

The private network must contain staging services only. It must not route to
Klyrow, Postal, production SMTP/SMS/PSTN, advertising-write, social-publishing,
or production model-provider networks. CIDR values are explicit allowlists;
global egress CIDRs are rejected.

## Plan and apply

Pull requests run exact-head and merge-result formatting, validation, static
security checks, and a no-refresh plan using documentation-only TEST-NET
values. No push applies infrastructure.

After merge and protected-input review, manually dispatch `Stage 6 isolated
staging host` from the exact protected `main` SHA with confirmation
`APPLY_STAGE6_ISOLATED_HOST`. The apply job uses remote state and the protected
environment. It creates at most one server.

## Baseline and seccomp acceptance

Cloud-init creates separate deploy/admin identities, disables root/password
SSH, keeps deployment users out of the Docker group, and installs Docker from
the signed Ubuntu archive. Runtime packages are held after installation until
a separately reviewed update. Applications remain absent.

Before application deployment, capture exact package versions and prove:

1. `docker info` reports the default seccomp profile and no TCP Docker API;
2. a representative container has `Privileged=false`, read-only rootfs and
   `no-new-privileges=true`;
3. `docker exec <container> true` succeeds;
4. Klyrow/Postal and all production provider routes are absent or denied.

## Rollback and destroy

`prevent_destroy` blocks accidental deletion. Rollback is a reviewed revert to
the previous protected commit followed by a protected plan/apply. Destruction
requires a separate PR removing `prevent_destroy`, a backup/state review, and a
manual protected apply. Never use `tofu destroy` from a workstation.

If bootstrap fails, do not attach production credentials or reuse production
volumes. Recreate only after a reviewed fix and preserved remote-state audit.
