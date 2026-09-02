# Infrastructure repository-name migration record

```text
REPOSITORY_ID=1350724865
CURRENT_FULL_NAME=appolon1908-hue/Infustruction-repo
TARGET_FULL_NAME=appolon1908-hue/Codestra-Infrastructure
STATUS=PREPARED_NOT_RENAMED
RUNTIME_CRITICAL=YES
```

The approved target corrects the legacy spelling and preserves this repository's role as the Codestra infrastructure, topology, GitOps, backup/recovery, observability-composition, and release-governance authority.

## Operational rule

The current full name remains authoritative for checkouts, workflows, source locks, deployment manifests, server remotes, GitHub Apps, webhooks, packages, and links until an authorized rename is completed and repository ID `1350724865` is read back at the target name.

The local machine-readable authority is [`config/repository-name-aliases.v1.json`](config/repository-name-aliases.v1.json). Validate it with:

```bash
python3 scripts/validate_repository_name_aliases.py
```

## Required cutover evidence

Inventory and preserve:

- default-branch and release SHAs;
- rulesets, branch protection, required checks, CODEOWNERS, and Environments;
- every active source lock, BOM, image lock, rollback manifest, and deployment reference;
- reusable Actions, submodules, Terraform/OpenTofu/Ansible module sources, and Compose/Kubernetes references;
- deploy-key fingerprints, GitHub Apps, and webhooks without secret values;
- GHCR/package identities, SBOMs, provenance, and image labels;
- every server checkout and current Git remote;
- every current and previous runtime digest required for rollback.

Dated release, incident, certification, and source-lock evidence remains unchanged. New current-state manifests supersede it; history is not rewritten.

## Rename sequence

1. Merge alias-awareness into all active consumers.
2. Freeze infrastructure merges, releases, and deployment dispatches.
3. Prove all production and staging deployments use exact SHAs and immutable digests.
4. Rename only this GitHub repository through an authorized owner/admin action.
5. Require the same repository ID, visibility, default branch, protected SHA, history, issues, PRs, tags, releases, rulesets, Environments, and package inventory.
6. Update mutable active source locks, workflow references, module sources, package metadata, badges, server remotes, and current documentation.
7. Run every infrastructure validator and deployment preflight without applying runtime changes.
8. Prove running images, networks, databases, secrets, and traffic are unchanged.
9. Rehearse rollback to the prior slug.

Required metadata-only result:

```text
WORKLOADS_RESTARTED=0
IMAGES_REBUILT=0
CONFIG_APPLIES=0
DATABASE_MIGRATIONS=0
SECRETS_ROTATED=0
DNS_CHANGES=0
PRODUCTION_TRAFFIC_CHANGED=NO
```

The account-wide runbook is maintained in `appolon1908-hue/documentaions` until the documentation repository completes its own controlled rename.