#!/usr/bin/env python3
"""Validate stable Codestra repository identities and planned slug migrations."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "repository-name-aliases.v1.json"
RUNBOOK = ROOT / "REPOSITORY_NAME_MIGRATION.md"
EXPECTED = {
    1221155447: (
        "appolon1908-hue/Frontend-Resturant-",
        "appolon1908-hue/restaurant-frontend",
        True,
    ),
    1343761049: (
        "appolon1908-hue/transportaion-Frontend",
        "appolon1908-hue/freight-platform-frontend",
        True,
    ),
    1343962199: (
        "appolon1908-hue/LARIM-A-Fornt-end",
        "appolon1908-hue/LARIM-A-Frontend",
        True,
    ),
    1351353723: (
        "appolon1908-hue/Codesrea-Social-",
        "appolon1908-hue/Codestra-Social-Control-Plane",
        False,
    ),
    1350724356: (
        "appolon1908-hue/documentaions",
        "appolon1908-hue/Codestra-Documentation",
        False,
    ),
    1350724865: (
        "appolon1908-hue/Infustruction-repo",
        "appolon1908-hue/Codestra-Infrastructure",
        True,
    ),
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load() -> dict[str, Any]:
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid manifest: {exc}")
    if not isinstance(data, dict):
        fail("manifest root must be an object")
    return data


def operational_sources() -> list[Path]:
    paths: set[Path] = set()
    for pattern in (
        "PRODUCTION-*.yaml",
        "PRODUCTION-*.json",
        "STAGE6-SOURCE-LOCK.yaml",
        "release/**/*.yaml",
        "release/**/*.yml",
        "release/**/*.json",
        "releases/**/*.yaml",
        "releases/**/*.yml",
        "releases/**/*.json",
        "deploy/**/*.yaml",
        "deploy/**/*.yml",
        "deploy/**/*.json",
        "operations/**/*.yaml",
        "operations/**/*.yml",
        "config/**/*.yaml",
        "config/**/*.yml",
        "config/**/*.json",
    ):
        paths.update(path for path in ROOT.glob(pattern) if path.is_file())
    paths.discard(MANIFEST)
    return sorted(paths)


def validate_planned_targets_absent(
    paths: list[Path],
    planned_targets: set[str],
) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for target in planned_targets:
            if target in text:
                fail(
                    "planned repository target appears in active operational "
                    f"source before cutover: {target} in {path.relative_to(ROOT)}"
                )


def validate() -> None:
    data = load()
    if data.get("schema_version") != "1.0":
        fail("schema_version must be 1.0")
    if data.get("status") != "PREPARED_NOT_RENAMED":
        fail("manifest must remain PREPARED_NOT_RENAMED until a reviewed cutover")
    if data.get("identity_key") != "repository_id":
        fail("repository_id must be the stable identity key")

    documentation = data.get("documentation_authority", {})
    if documentation.get("repository_id") != 1350724356:
        fail("documentation authority repository ID is incorrect")
    if documentation.get("current_repository") != "appolon1908-hue/documentaions":
        fail("documentation authority current repository is incorrect")
    if documentation.get("target_repository_after_cutover") != (
        "appolon1908-hue/Codestra-Documentation"
    ):
        fail("documentation authority target repository is incorrect")

    infrastructure = data.get("infrastructure_authority", {})
    if infrastructure.get("repository_id") != 1350724865:
        fail("infrastructure authority repository ID is incorrect")
    if infrastructure.get("current_repository") != "appolon1908-hue/Infustruction-repo":
        fail("infrastructure current repository is incorrect")
    if infrastructure.get("target_repository_after_cutover") != (
        "appolon1908-hue/Codestra-Infrastructure"
    ):
        fail("infrastructure target repository is incorrect")
    if infrastructure.get("status") != "PREPARED_NOT_RENAMED":
        fail("infrastructure rename state changed without reviewed cutover")
    if infrastructure.get("runtime_state") != "REQUIRES_PRE_CUTOVER_DISCOVERY":
        fail("infrastructure runtime state must be rediscovered before cutover")

    postgres = data.get("postgres_exporter_authority", {})
    if postgres.get("repository_id") != 1350839865:
        fail("PostgreSQL Exporter repository ID is incorrect")
    if postgres.get("repository") != "appolon1908-hue/Codestra-Postgres-Exporter":
        fail("PostgreSQL Exporter principal repository is incorrect")
    if postgres.get("public_hostname") is not None:
        fail("PostgreSQL Exporter must not have a public hostname")
    if postgres.get("private_service_identity") != "postgres-exporter:9187":
        fail("PostgreSQL Exporter private service identity is incorrect")
    if postgres.get("forbidden_public_hostname") != "pgex.codestra.media":
        fail("retired public hostname must remain explicitly forbidden")
    if postgres.get("exposure") != "PRIVATE_INTERNAL_ONLY":
        fail("PostgreSQL Exporter must remain private/internal only")
    for field in (
        "caddy_publication_allowed",
        "kong_publication_allowed",
        "host_public_port_allowed",
    ):
        if postgres.get(field) is not False:
            fail(f"PostgreSQL Exporter {field} must remain false")

    mappings = data.get("mappings")
    if not isinstance(mappings, list) or len(mappings) != len(EXPECTED):
        fail("manifest must contain exactly the six approved mappings")

    seen_ids: set[int] = set()
    seen_current: set[str] = set()
    seen_target: set[str] = set()
    actual: dict[int, tuple[str, str, bool]] = {}

    for item in mappings:
        if not isinstance(item, dict):
            fail("each mapping must be an object")
        repository_id = item.get("repository_id")
        current = item.get("current_repository")
        target = item.get("target_repository_after_cutover")
        status = item.get("status")
        runtime_critical = item.get("runtime_critical")

        if not isinstance(repository_id, int) or repository_id <= 0:
            fail("mapping contains an invalid repository ID")
        if repository_id in seen_ids:
            fail(f"duplicate repository ID: {repository_id}")
        if not isinstance(current, str) or not current.startswith("appolon1908-hue/"):
            fail(f"invalid current repository for ID {repository_id}")
        if not isinstance(target, str) or not target.startswith("appolon1908-hue/"):
            fail(f"invalid target repository for ID {repository_id}")
        if current == target:
            fail(f"current and target repository are identical for ID {repository_id}")
        if current in seen_current or target in seen_target:
            fail("duplicate current or target repository name")
        if status != "PREPARED_NOT_RENAMED":
            fail(f"mapping changed state without cutover: {current}")
        if not isinstance(runtime_critical, bool):
            fail(f"mapping runtime_critical must be boolean: {current}")

        seen_ids.add(repository_id)
        seen_current.add(current)
        seen_target.add(target)
        actual[repository_id] = (current, target, runtime_critical)

    if actual != EXPECTED:
        fail("repository mappings do not exactly match the approved migration set")

    policy = data.get("policy", {})
    required_true = {
        "current_names_required_before_cutover",
        "target_names_forbidden_as_operational_sources_before_cutover",
        "historical_evidence_immutable",
        "one_repository_per_cutover",
        "same_repository_id_required_after_rename",
        "all_inventoried_integrations_require_post_rename_readback",
        "runtime_digest_must_remain_unchanged_when_deployed",
        "absent_runtime_digest_must_be_recorded_as_not_applicable",
        "success_path_must_restore_freeze_state",
        "rollback_path_must_restore_freeze_state",
    }
    for key in required_true:
        if policy.get(key) is not True:
            fail(f"required fail-closed policy is not true: {key}")
    if policy.get("rename_authorizes_deployment") is not False:
        fail("repository rename must not authorize deployment")

    runbook = RUNBOOK.read_text(encoding="utf-8")
    for required in (
        "POST_RENAME_INTEGRATION_READBACK=PASS",
        "CURRENT_RUNTIME_STATE=DEPLOYED|NOT_DEPLOYED",
        "DEPLOYED_IMAGE_DIGEST=<immutable-digest>|N/A",
        "RUNTIME_DIGEST_UNCHANGED=PASS|N/A",
        "MERGES_UNFROZEN=PASS",
        "WORKFLOW_DISPATCH_UNFROZEN=PASS|N/A",
        "ROLLBACK_UNFREEZE=PASS|N/A",
        "Do not leave the infrastructure authority frozen.",
        "do not fabricate runtime evidence.",
        "WORKLOADS_RESTARTED=0",
        "IMAGES_REBUILT=0",
        "CONFIG_APPLIES=0",
        "DATABASE_MIGRATIONS=0",
        "SECRETS_ROTATED=0",
        "DNS_CHANGES=0",
        "PRODUCTION_TRAFFIC_CHANGED=NO",
    ):
        if required not in runbook:
            fail(f"infrastructure rename runbook is missing required evidence: {required}")

    validate_planned_targets_absent(
        operational_sources(),
        {mapping[1] for mapping in EXPECTED.values()},
    )


def main() -> None:
    validate()
    print("Codestra repository-name authority validation: PASS")


if __name__ == "__main__":
    main()
