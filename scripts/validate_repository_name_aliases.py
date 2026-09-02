#!/usr/bin/env python3
"""Validate stable repository identities, planned renames, and exporter privacy."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "repository-name-aliases.v1.json"
RUNBOOK = ROOT / "REPOSITORY_NAME_MIGRATION.md"
VALIDATOR = Path(__file__).resolve()

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

TEXT_SUFFIXES = {
    ".bash",
    ".cfg",
    ".conf",
    ".env",
    ".hcl",
    ".ini",
    ".js",
    ".json",
    ".mjs",
    ".cjs",
    ".properties",
    ".ps1",
    ".py",
    ".sh",
    ".tf",
    ".tfvars",
    ".toml",
    ".ts",
    ".xml",
    ".yaml",
    ".yml",
    ".zsh",
}
OPERATIONAL_ROOTS = {
    "ansible",
    "compose",
    "config",
    "deploy",
    "deployment",
    "helm",
    "hosts",
    "infra",
    "infrastructure",
    "k8s",
    "kubernetes",
    "manifests",
    "operations",
    "opentofu",
    "release",
    "releases",
    "scripts",
    "terraform",
}
EXCLUDED_ROOTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "backups",
    "build",
    "coverage",
    "dist",
    "docs",
    "evidence",
    "node_modules",
    "reports",
    "tests",
    "vendor",
}
ROOT_OPERATIONAL_NAMES = {
    ".gitmodules",
    "Caddyfile",
    "Dockerfile",
    "Makefile",
    "STAGE6-SOURCE-LOCK.yaml",
}
STAGE9_EXPECTED_REPOS = {
    "Codestra-Marketing-",
    "Codestra-AI",
    "Codestra-Communication-CC",
    "Codesrea-Social-",
    "Middleware-",
    "Odoo",
    "SDK-repository",
    "N8N",
    "Kong",
    "Keycloak",
    "social.codestra.co",
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


def is_operational_source(path: Path) -> bool:
    """Return whether a text file can control a current checkout or deployment."""

    try:
        relative = path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return False

    if path.resolve() in {MANIFEST.resolve(), RUNBOOK.resolve(), VALIDATOR}:
        return False
    if any(part in EXCLUDED_ROOTS for part in relative.parts):
        return False
    if relative.name in ROOT_OPERATIONAL_NAMES:
        return True
    if relative.parts[:2] == (".github", "workflows"):
        return relative.suffix.lower() in {".yaml", ".yml"}
    if not relative.parts:
        return False
    if relative.parts[0] in OPERATIONAL_ROOTS:
        return relative.suffix.lower() in TEXT_SUFFIXES or relative.name in {
            "Caddyfile",
            "Dockerfile",
            "Makefile",
        }
    if len(relative.parts) == 1:
        name = relative.name.lower()
        return relative.suffix.lower() in {".json", ".yaml", ".yml", ".toml"} and (
            "compose" in name
            or "lock" in name
            or "manifest" in name
            or "matrix" in name
            or "production" in name
            or "release" in name
        )
    return False


def operational_sources() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and is_operational_source(path)
    )


def validate_planned_targets_absent(
    paths: list[Path],
    planned_targets: set[str],
) -> None:
    lowered_targets = {target.lower() for target in planned_targets}
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for target in lowered_targets:
            if target in text:
                fail(
                    "planned repository target appears in active operational "
                    f"source before cutover: {target} in {path.relative_to(ROOT)}"
                )


def validate_repository_id_current_name_pairing(paths: list[Path]) -> None:
    """Bind explicit repository-ID fields to the approved current pre-cutover slug."""

    for path in paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        for repository_id, (current, _target, _critical) in EXPECTED.items():
            # Match only an explicit JSON/YAML/Python/shell-style field assignment.
            # Do not let whitespace or punctuation bridge unrelated source text.
            id_pattern = re.compile(
                rf"(?<![A-Za-z0-9_])[\"']?(?:github_)?repository_id[\"']?"
                rf"\s*[:=]\s*{repository_id}\b",
                re.IGNORECASE,
            )
            if id_pattern.search(text) and current.lower() not in lowered:
                fail(
                    "operational source binds a governed repository ID without its "
                    f"required current name: {repository_id} in {path.relative_to(ROOT)}"
                )


def require_file(path: Path) -> str:
    if not path.is_file():
        fail(f"required operational authority file is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def require_regex_binding(
    path: Path,
    pattern: str,
    expected_repository: str,
    description: str,
) -> None:
    text = require_file(path)
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if match is None:
        fail(f"required operational binding is missing: {description}")
    if match.group(1) != expected_repository:
        fail(f"{description} must use {expected_repository}, found {match.group(1)}")


def assigned_string_set(source: str, variable: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        fail(f"invalid Python source while checking {variable}: {exc}")
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == variable for target in targets):
            continue
        value = node.value
        if not isinstance(value, (ast.Set, ast.List, ast.Tuple)):
            fail(f"{variable} must be a literal string collection")
        result: set[str] = set()
        for item in value.elts:
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                fail(f"{variable} must contain only literal strings")
            result.add(item.value)
        return result
    fail(f"required Python authority collection is missing: {variable}")
    return set()


def validate_known_operational_bindings() -> None:
    """Protect current source-lock entries that do not yet carry stable IDs."""

    social_current = EXPECTED[1351353723][0]
    infrastructure_current = EXPECTED[1350724865][0]

    require_regex_binding(
        ROOT / "STAGE6-SOURCE-LOCK.yaml",
        r"^\s*social_control:\s*\{[^}\n]*\brepository:\s*([^,\s}]+)",
        social_current,
        "STAGE6 social-control repository",
    )
    require_regex_binding(
        ROOT / "STAGE6-SOURCE-LOCK.yaml",
        r"^\s*authority_issue:\s*https://github\.com/([^/]+/[^/]+)/issues/\d+",
        infrastructure_current,
        "STAGE6 infrastructure authority issue repository",
    )
    require_regex_binding(
        ROOT / "release" / "stage6-8-release-matrix.yaml",
        r"^\s*-\s+name:\s*social_control\s*$.*?^\s+repo:\s*(\S+)",
        social_current,
        "Stage 6-8 social-control release repository",
    )

    stage9 = json.loads(require_file(ROOT / "config" / "marketing-stage9-readiness.json"))
    stage9_social = [
        item
        for item in stage9.get("repositories", [])
        if isinstance(item, dict) and item.get("role") == "social control plane"
    ]
    expected_social_slug = social_current.split("/", 1)[1]
    if len(stage9_social) != 1 or stage9_social[0].get("repo") != expected_social_slug:
        fail("marketing Stage 9 social-control repository is not the required current slug")

    historical = json.loads(
        require_file(
            ROOT / "releases" / "STAGE6-STAGING-EXACT-SOURCE-LOCK-2026-08-30.json"
        )
    )
    historical_social = historical.get("repositories", {}).get("social_control", {}).get("repo")
    if historical_social != social_current:
        fail("historical Stage 6 source lock social-control repository changed")

    certifier = require_file(ROOT / "scripts" / "certify_marketing_stage9.py")
    if assigned_string_set(certifier, "EXPECTED_REPOS") != STAGE9_EXPECTED_REPOS:
        fail("marketing Stage 9 certifier repository set drifted from current authority")


def compose_ports_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    for index, line in enumerate(lines):
        match = re.match(r"^(\s*)ports\s*:\s*(?:#.*)?$", line, re.IGNORECASE)
        if match is None:
            continue
        indent = len(match.group(1))
        selected = [line]
        for following in lines[index + 1 :]:
            if not following.strip() or following.lstrip().startswith("#"):
                selected.append(following)
                continue
            following_indent = len(following) - len(following.lstrip())
            if following_indent <= indent:
                break
            selected.append(following)
        blocks.append("\n".join(selected))
    return blocks


def is_gateway_source(path: Path, text: str) -> bool:
    lowered_parts = {part.lower() for part in path.relative_to(ROOT).parts}
    gateway_tokens = {"caddy", "kong", "ingress", "nginx", "proxy", "traefik"}
    if lowered_parts & gateway_tokens:
        return True
    name = path.name.lower()
    if any(token in name for token in gateway_tokens):
        return True
    lowered = text.lower()
    return "reverse_proxy" in lowered or (
        "_format_version:" in lowered and "services:" in lowered
    )


def validate_postgres_exporter_privacy(paths: list[Path]) -> None:
    """Reject public routing or host publication of PostgreSQL Exporter."""

    forbidden_hostname = "pgex.codestra.media"
    private_identity = "postgres-exporter:9187"

    for path in paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        relative = path.relative_to(ROOT)

        if forbidden_hostname in lowered:
            fail(f"retired PostgreSQL Exporter hostname appears in {relative}")

        for block in compose_ports_blocks(text):
            if re.search(r"\b9187\b", block):
                fail(f"PostgreSQL Exporter port is host-published in {relative}")

        if re.search(
            r"(?:docker|podman)\s+(?:run|create)[^\n]*(?:-p|--publish)(?:=|\s+)"
            r"[^\n]*\b9187\b",
            lowered,
        ):
            fail(f"PostgreSQL Exporter port is published by a runtime command in {relative}")

        if "9187" in lowered and re.search(
            r"\btype\s*:\s*(?:loadbalancer|nodeport)\b", lowered
        ):
            fail(f"PostgreSQL Exporter is exposed by a public Kubernetes Service in {relative}")

        if (
            "9187" in lowered
            and ("0.0.0.0/0" in lowered or "::/0" in lowered)
            and re.search(r"(?:from_port|to_port|port|port_range)[^\n]*9187", lowered)
        ):
            fail(f"PostgreSQL Exporter is allowed by a public network rule in {relative}")

        if (private_identity in lowered or "postgres-exporter" in lowered) and is_gateway_source(
            path, text
        ):
            fail(f"PostgreSQL Exporter is referenced by public gateway source in {relative}")


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

    sources = operational_sources()
    validate_planned_targets_absent(
        sources,
        {mapping[1] for mapping in EXPECTED.values()},
    )
    validate_repository_id_current_name_pairing(sources)
    validate_known_operational_bindings()
    validate_postgres_exporter_privacy(sources)


def main() -> None:
    validate()
    print("Codestra repository-name authority validation: PASS")


if __name__ == "__main__":
    main()
