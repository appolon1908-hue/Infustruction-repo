#!/usr/bin/env python3
"""Finalize the v2 immutable release controller and workflow exactly once."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "operations" / "staging-readonly"
WORKFLOW = ROOT / ".github" / "workflows" / "staging-readonly-certification.yml"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    if source.count(old) != 1:
        raise SystemExit(f"{label}: expected one source marker, found {source.count(old)}")
    return source.replace(old, new, 1)


def patch_v2_controller() -> None:
    path = OPS / "release_control_v2.py"
    source = path.read_text(encoding="utf-8")
    source = replace_once(
        source,
        'import copy\nimport contextlib\n',
        'import argparse\nimport copy\nimport contextlib\n',
        "argparse import",
    )
    source = replace_once(
        source,
        'ZERO_DIGEST = "sha256:" + ZERO_HASH\nALLOWED_KONG_RESULTS',
        'ZERO_DIGEST = "sha256:" + ZERO_HASH\nDIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")\nALLOWED_KONG_RESULTS',
        "local digest pattern",
    )
    source = source.replace("core.DIGEST_RE", "DIGEST_RE")

    marker = '''def execute_staging(
    candidate: Mapping[str, Any],
'''
    helper = '''def previous_image_workloads(
    candidate: Mapping[str, Any],
) -> list[dict[str, str]]:
    current = {item["service"]: item for item in candidate["workloads"]}
    return [
        {
            "name": current[item["service"]]["name"],
            "service": item["service"],
            "repository": current[item["service"]]["repository"],
            "source_sha": item["source_sha"],
            "image": item["image"],
        }
        for item in candidate["rollback"]["workloads"]
    ]


def execute_staging(
    candidate: Mapping[str, Any],
'''
    source = replace_once(source, marker, helper, "previous image helper")
    source = replace_once(
        source,
        '        core.verify_images(candidate["rollback"]["workloads"])\n',
        '        core.verify_images(previous_image_workloads(candidate))\n',
        "previous image label verification",
    )

    old_validation = '''def validate_staging_evidence(
    staging: Mapping[str, Any],
    candidate: Mapping[str, Any],
    candidate_sha256: str,
) -> None:
'''
    new_validation = '''def validate_run_evidence(
    payload: Mapping[str, Any],
    candidate: Mapping[str, Any],
    candidate_sha256: str,
    *,
    expected_mode: str,
    environment_prefix: str,
    required_gates: set[str],
) -> None:
'''
    source = replace_once(source, old_validation, new_validation, "generic run evidence")
    source = source.replace(
        '    if staging.get("candidate_id") != candidate["candidate_id"]:\n',
        '    if payload.get("candidate_id") != candidate["candidate_id"]:\n',
        1,
    )
    source = source.replace(
        '    if staging.get("candidate_source_lock_sha") != candidate["candidate_source_lock_sha"]:\n',
        '    if payload.get("candidate_source_lock_sha") != candidate["candidate_source_lock_sha"]:\n',
        1,
    )
    source = source.replace(
        '    if staging.get("candidate_manifest_sha256") != candidate_sha256:\n',
        '    if payload.get("candidate_manifest_sha256") != candidate_sha256:\n',
        1,
    )
    source = source.replace(
        '    if staging.get("workload_identities") != _identity_projection(candidate):\n',
        '    if payload.get("workload_identities") != _identity_projection(candidate):\n',
        1,
    )
    source = source.replace(
        '    if staging.get("mode") != "staging" or staging.get("verdict") != "GO":\n        raise core.GateError("staging evidence is not an exact GO result")\n    gates = staging.get("gates")\n',
        '    if payload.get("mode") != expected_mode or payload.get("verdict") != "GO":\n        raise core.GateError(f"{expected_mode} evidence is not an exact GO result")\n    gates = payload.get("gates")\n',
        1,
    )
    source = source.replace(
        '        raise core.GateError("staging evidence contains an absent or non-PASS gate")\n    producer = staging.get("producer")\n',
        '        raise core.GateError(f"{expected_mode} evidence contains an absent or non-PASS gate")\n    gate_names = {str(gate.get("gate")) for gate in gates}\n    if not required_gates <= gate_names:\n        raise core.GateError(\n            f"{expected_mode} evidence is missing required gates: "\n            + ", ".join(sorted(required_gates - gate_names))\n        )\n    producer = payload.get("producer")\n',
        1,
    )
    source = source.replace(
        '    expected_run = os.environ.get("STAGING_EVIDENCE_RUN_ID")\n    expected_attempt = os.environ.get("STAGING_EVIDENCE_RUN_ATTEMPT")\n    expected_head = os.environ.get("STAGING_EVIDENCE_HEAD_SHA")\n',
        '    expected_run = os.environ.get(f"{environment_prefix}_EVIDENCE_RUN_ID")\n    expected_attempt = os.environ.get(f"{environment_prefix}_EVIDENCE_RUN_ATTEMPT")\n    expected_head = os.environ.get(f"{environment_prefix}_EVIDENCE_HEAD_SHA")\n',
        1,
    )

    old_canary_signature = '''def execute_canary(
    candidate: Mapping[str, Any],
    manifest: Mapping[str, Any],
    evidence: Evidence,
    staging_evidence_path: Path,
    requested_percent: float,
    candidate_path: Path,
    candidate_sha256: str,
) -> None:
'''
    new_canary_signature = '''def execute_canary(
    candidate: Mapping[str, Any],
    manifest: Mapping[str, Any],
    evidence: Evidence,
    staging_evidence_path: Path,
    rollback_evidence_path: Path,
    requested_percent: float,
    candidate_path: Path,
    candidate_sha256: str,
) -> None:
'''
    source = replace_once(
        source,
        old_canary_signature,
        new_canary_signature,
        "canary rollback evidence signature",
    )
    source = replace_once(
        source,
        '''    staging = core.load_json(staging_evidence_path)
    validate_staging_evidence(staging, candidate, candidate_sha256)
''',
        '''    staging = core.load_json(staging_evidence_path)
    validate_run_evidence(
        staging,
        candidate,
        candidate_sha256,
        expected_mode="staging",
        environment_prefix="STAGING",
        required_gates={
            "paired-local-off-host-and-restore-verified-backup",
            "source-digest-readiness-capabilities-metrics-migrations",
            "keycloak-issuer",
            "kong-29-route-smoke",
            "zero-calls-emails-sms",
        },
    )
    rollback_evidence = core.load_json(rollback_evidence_path)
    validate_run_evidence(
        rollback_evidence,
        candidate,
        candidate_sha256,
        expected_mode="rollback-rehearsal",
        environment_prefix="ROLLBACK",
        required_gates={
            "rollback-to-previous-exact-identities",
            "candidate-redeployment",
            "database-filestore-configuration-integrity",
            "rollback-health-readiness-version-digest",
            "zero-live-effects-during-rehearsal",
        },
    )
''',
        "canary prerequisite evidence",
    )

    old_parse = '''def parse_args(argv: Sequence[str] | None = None) -> Any:
    return core.parse_args(argv)
'''
    new_parse = '''def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--endpoint-manifest", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=(
            "validate",
            "staging",
            "rollback-rehearsal",
            "production-readonly-canary",
        ),
        required=True,
    )
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--staging-evidence", type=Path)
    parser.add_argument("--rollback-evidence", type=Path)
    parser.add_argument("--canary-percent", type=float, default=1.0)
    parser.add_argument("--confirm-candidate-id")
    parser.add_argument("--confirm-source-lock-sha")
    return parser.parse_args(argv)
'''
    source = replace_once(source, old_parse, new_parse, "v2 CLI parser")
    source = replace_once(
        source,
        '''            if args.staging_evidence is None:
                raise core.GateError(
                    "production canary requires --staging-evidence"
                )
            execute_canary(
                candidate,
                manifest,
                evidence,
                args.staging_evidence,
                args.canary_percent,
''',
        '''            if args.staging_evidence is None or args.rollback_evidence is None:
                raise core.GateError(
                    "production canary requires staging and rollback evidence"
                )
            execute_canary(
                candidate,
                manifest,
                evidence,
                args.staging_evidence,
                args.rollback_evidence,
                args.canary_percent,
''',
        "canary CLI evidence inputs",
    )
    path.write_text(source, encoding="utf-8")


def patch_entrypoint() -> None:
    (OPS / "release_control_entry.py").write_text(
        '''#!/usr/bin/env python3
"""Stable entry point for the hardened immutable release controller."""

from __future__ import annotations

from release_control_v2 import main


if __name__ == "__main__":
    raise SystemExit(main())
''',
        encoding="utf-8",
    )


def patch_candidate_and_templates() -> None:
    candidate_path = OPS / "release-control.template.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    for route in candidate["kong"]["smoke_routes"]:
        route["expected_statuses"] = [
            status for status in route["expected_statuses"] if status != 404
        ]
    for item in candidate["rollback"]["workloads"]:
        item["expected_migration"] = "REPLACE_WITH_PREVIOUS_MIGRATION_HEAD"
    candidate_path.write_text(
        json.dumps(candidate, indent=2) + "\n",
        encoding="utf-8",
    )

    staging = {
        "schema": "codestra.staging-endpoints.v1",
        "candidate_id": candidate["candidate_id"],
        "environment": "staging-readonly",
        "bearer_token_environment": "STAGING_READONLY_BEARER_TOKEN",
        "metrics_token_environment": "STAGING_METRICS_BEARER_TOKEN",
        "workloads": [
            {
                key: value
                for key, value in workload.items()
                if key
                in {
                    "name",
                    "version_endpoint",
                    "readiness_endpoint",
                    "capabilities_endpoint",
                    "metrics_endpoint",
                    "migration_endpoint",
                }
            }
            for workload in candidate["workloads"]
        ],
        "keycloak": candidate["keycloak"],
        "kong": {"smoke_routes": candidate["kong"]["smoke_routes"]},
        "counters": [
            {
                "name": name,
                "url": f"https://REPLACE_WITH_PROTECTED_COUNTER_HOST/api/v1/safety/counters/{name}",
                "json_pointer": "/value",
                "expected": 0,
            }
            for name in ("calls", "emails", "sms")
        ],
        "probe": {
            "requests": 50,
            "maximum_error_rate": 0,
            "maximum_p95_ms": 500,
            "maximum_regression_percent": 10,
        },
    }
    (OPS / "staging-endpoints.template.json").write_text(
        json.dumps(staging, indent=2) + "\n",
        encoding="utf-8",
    )


def patch_schemas() -> None:
    candidate_path = OPS / "release-control.schema.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    rollback_properties = (
        candidate["properties"]["rollback"]["properties"]["workloads"]["items"]["properties"]
    )
    rollback_properties["expected_migration"] = {
        "type": ["string", "null"],
        "maxLength": 128,
    }
    route_status = candidate["$defs"]["smokeRoute"]["properties"]["expected_statuses"]["items"]
    route_status["not"] = {"const": 404}
    candidate_path.write_text(
        json.dumps(candidate, indent=2) + "\n",
        encoding="utf-8",
    )

    endpoint = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://codestra.co/schemas/staging-endpoints.v2.json",
        "title": "Codestra protected environment target and zero-effect manifest",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema",
            "candidate_id",
            "environment",
            "bearer_token_environment",
            "metrics_token_environment",
            "workloads",
            "keycloak",
            "kong",
            "counters",
            "probe",
        ],
        "properties": {
            "schema": {"const": "codestra.staging-endpoints.v1"},
            "candidate_id": {
                "type": "string",
                "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$",
            },
            "environment": {
                "enum": ["staging-readonly", "production-readonly-canary"]
            },
            "bearer_token_environment": {
                "type": "string",
                "pattern": "^[A-Z][A-Z0-9_]{2,63}$",
            },
            "metrics_token_environment": {
                "type": "string",
                "pattern": "^[A-Z][A-Z0-9_]{2,63}$",
            },
            "workloads": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/workload"},
            },
            "keycloak": {
                "type": "object",
                "additionalProperties": False,
                "required": ["discovery_endpoint", "expected_issuer"],
                "properties": {
                    "discovery_endpoint": {"$ref": "#/$defs/endpoint"},
                    "expected_issuer": {"$ref": "#/$defs/endpoint"},
                },
            },
            "kong": {
                "type": "object",
                "additionalProperties": False,
                "required": ["smoke_routes"],
                "properties": {
                    "smoke_routes": {
                        "type": "array",
                        "minItems": 29,
                        "maxItems": 29,
                        "items": {"$ref": "#/$defs/route"},
                    }
                },
            },
            "counters": {
                "type": "array",
                "minItems": 3,
                "items": {"$ref": "#/$defs/counter"},
            },
            "probe": {"$ref": "#/$defs/probe"},
        },
        "allOf": [
            {
                "if": {
                    "properties": {"environment": {"const": "staging-readonly"}}
                },
                "then": {
                    "properties": {
                        "bearer_token_environment": {
                            "const": "STAGING_READONLY_BEARER_TOKEN"
                        },
                        "metrics_token_environment": {
                            "const": "STAGING_METRICS_BEARER_TOKEN"
                        },
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "environment": {"const": "production-readonly-canary"}
                    }
                },
                "then": {
                    "properties": {
                        "bearer_token_environment": {
                            "const": "PRODUCTION_READONLY_BEARER_TOKEN"
                        },
                        "metrics_token_environment": {
                            "const": "PRODUCTION_METRICS_BEARER_TOKEN"
                        },
                        "probe": {
                            "required": ["baseline_url", "canary_url"]
                        },
                    }
                },
            },
        ],
        "$defs": {
            "endpoint": {
                "type": "string",
                "format": "uri",
                "pattern": "^https://[^?#]+$",
            },
            "workload": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "name",
                    "version_endpoint",
                    "readiness_endpoint",
                    "capabilities_endpoint",
                ],
                "properties": {
                    "name": {
                        "type": "string",
                        "pattern": "^[a-z0-9][a-z0-9._-]{1,63}$",
                    },
                    "version_endpoint": {"$ref": "#/$defs/endpoint"},
                    "readiness_endpoint": {"$ref": "#/$defs/endpoint"},
                    "capabilities_endpoint": {"$ref": "#/$defs/endpoint"},
                    "metrics_endpoint": {"$ref": "#/$defs/endpoint"},
                    "migration_endpoint": {"$ref": "#/$defs/endpoint"},
                },
            },
            "route": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "url", "expected_statuses"],
                "properties": {
                    "name": {
                        "type": "string",
                        "pattern": "^[a-z0-9][a-z0-9._-]{1,63}$",
                    },
                    "url": {"$ref": "#/$defs/endpoint"},
                    "expected_statuses": {
                        "type": "array",
                        "minItems": 1,
                        "uniqueItems": True,
                        "items": {
                            "type": "integer",
                            "enum": [
                                200,
                                201,
                                202,
                                204,
                                301,
                                302,
                                307,
                                308,
                                400,
                                401,
                                403,
                                405,
                                409,
                                410,
                                415,
                                422,
                                429,
                            ],
                        },
                    },
                },
            },
            "counter": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "url", "json_pointer", "expected"],
                "properties": {
                    "name": {
                        "type": "string",
                        "pattern": "^[a-z0-9][a-z0-9._-]{1,63}$",
                    },
                    "url": {"$ref": "#/$defs/endpoint"},
                    "json_pointer": {"type": "string", "pattern": "^/"},
                    "expected": {"const": 0},
                },
            },
            "probe": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "requests",
                    "maximum_error_rate",
                    "maximum_p95_ms",
                    "maximum_regression_percent",
                ],
                "properties": {
                    "requests": {
                        "type": "integer",
                        "minimum": 10,
                        "maximum": 1000,
                    },
                    "maximum_error_rate": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "maximum_p95_ms": {
                        "type": "number",
                        "exclusiveMinimum": 0,
                    },
                    "maximum_regression_percent": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "baseline_url": {"$ref": "#/$defs/endpoint"},
                    "canary_url": {"$ref": "#/$defs/endpoint"},
                },
            },
        },
    }
    (OPS / "staging-endpoints.schema.json").write_text(
        json.dumps(endpoint, indent=2) + "\n",
        encoding="utf-8",
    )


def patch_workflow() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    source = replace_once(
        source,
        '      staging_evidence_run_id:\n        description: "Successful staging run ID required for production canary"\n        required: false\n        type: string\n      canary_percent:',
        '      staging_evidence_run_id:\n        description: "Successful staging run ID required for production canary"\n        required: false\n        type: string\n      rollback_evidence_run_id:\n        description: "Successful rollback-rehearsal run ID required for production canary"\n        required: false\n        type: string\n      canary_percent:',
        "rollback workflow input",
    )
    source = replace_once(
        source,
        '''          python3 -m py_compile \\
            operations/staging-readonly/release_control.py \\
            operations/staging-readonly/release_control_entry.py \\
            operations/staging-readonly/test_release_control.py
          python3 operations/staging-readonly/test_release_control.py
''',
        '''          python3 -m py_compile \\
            operations/staging-readonly/release_control.py \\
            operations/staging-readonly/release_control_v2.py \\
            operations/staging-readonly/release_control_entry.py \\
            operations/staging-readonly/test_release_control.py \\
            operations/staging-readonly/test_release_control_v2.py
          python3 operations/staging-readonly/test_release_control.py
          python3 operations/staging-readonly/test_release_control_v2.py
''',
        "v2 policy tests",
    )
    source = replace_once(
        source,
        '          python3 -m json.tool operations/staging-readonly/staging-endpoints.template.json >/dev/null\n',
        '          python3 -m json.tool operations/staging-readonly/staging-endpoints.template.json >/dev/null\n          python3 -m json.tool operations/staging-readonly/production-endpoints.template.json >/dev/null\n',
        "production template parse",
    )

    marker = "  production-readonly-canary:\n"
    if source.count(marker) != 1:
        raise SystemExit("production canary workflow marker not found")
    prefix, tail = source.split(marker, 1)
    tail = tail.replace(
        '      STAGING_CANONICAL_CANDIDATE_B64: ${{ secrets.STAGING_CANONICAL_CANDIDATE_B64 }}',
        '      PRODUCTION_CANONICAL_CANDIDATE_B64: ${{ secrets.PRODUCTION_CANONICAL_CANDIDATE_B64 }}',
    )
    tail = tail.replace(
        '      STAGING_ENDPOINT_MANIFEST_B64: ${{ secrets.STAGING_ENDPOINT_MANIFEST_B64 }}',
        '      PRODUCTION_ENDPOINT_MANIFEST_B64: ${{ secrets.PRODUCTION_ENDPOINT_MANIFEST_B64 }}',
    )
    tail = tail.replace(
        '      STAGING_READONLY_BEARER_TOKEN: ${{ secrets.STAGING_READONLY_BEARER_TOKEN }}',
        '      PRODUCTION_READONLY_BEARER_TOKEN: ${{ secrets.PRODUCTION_READONLY_BEARER_TOKEN }}',
    )
    tail = tail.replace(
        '      STAGING_METRICS_BEARER_TOKEN: ${{ secrets.STAGING_METRICS_BEARER_TOKEN }}',
        '      PRODUCTION_METRICS_BEARER_TOKEN: ${{ secrets.PRODUCTION_METRICS_BEARER_TOKEN }}',
    )
    tail = tail.replace(
        '      STAGING_GHCR_READ_TOKEN: ${{ secrets.STAGING_GHCR_READ_TOKEN }}',
        '      PRODUCTION_GHCR_READ_TOKEN: ${{ secrets.PRODUCTION_GHCR_READ_TOKEN }}',
    )
    tail = tail.replace(
        '      STAGING_EVIDENCE_RUN_ID: ${{ inputs.staging_evidence_run_id }}\n',
        '      STAGING_EVIDENCE_RUN_ID: ${{ inputs.staging_evidence_run_id }}\n      ROLLBACK_EVIDENCE_RUN_ID: ${{ inputs.rollback_evidence_run_id }}\n',
    )
    tail = tail.replace(
        '          [[ "${STAGING_EVIDENCE_RUN_ID}" =~ ^[1-9][0-9]*$ ]]\n',
        '          [[ "${STAGING_EVIDENCE_RUN_ID}" =~ ^[1-9][0-9]*$ ]]\n          [[ "${ROLLBACK_EVIDENCE_RUN_ID}" =~ ^[1-9][0-9]*$ ]]\n',
    )
    tail = tail.replace(
        '          for name in STAGING_CANONICAL_CANDIDATE_B64 STAGING_ENDPOINT_MANIFEST_B64 STAGING_READONLY_BEARER_TOKEN STAGING_METRICS_BEARER_TOKEN STAGING_GHCR_READ_TOKEN CONFIRM_CANDIDATE_ID; do',
        '          for name in PRODUCTION_CANONICAL_CANDIDATE_B64 PRODUCTION_ENDPOINT_MANIFEST_B64 PRODUCTION_READONLY_BEARER_TOKEN PRODUCTION_METRICS_BEARER_TOKEN PRODUCTION_GHCR_READ_TOKEN CONFIRM_CANDIDATE_ID; do',
    )
    tail = tail.replace(
        '          printf \'%s\' "$STAGING_CANONICAL_CANDIDATE_B64" | base64 --decode >"$work/candidate.json"\n          printf \'%s\' "$STAGING_ENDPOINT_MANIFEST_B64" | base64 --decode >"$work/endpoints.json"',
        '          printf \'%s\' "$PRODUCTION_CANONICAL_CANDIDATE_B64" | base64 --decode >"$work/candidate.json"\n          printf \'%s\' "$PRODUCTION_ENDPOINT_MANIFEST_B64" | base64 --decode >"$work/endpoints.json"',
    )
    tail = tail.replace(
        '        run: printf \'%s\' "$STAGING_GHCR_READ_TOKEN" | docker login ghcr.io --username "$GHCR_USER" --password-stdin >/dev/null',
        '        run: printf \'%s\' "$PRODUCTION_GHCR_READ_TOKEN" | docker login ghcr.io --username "$GHCR_USER" --password-stdin >/dev/null',
    )

    authentication = '''      - name: Authenticate prerequisite workflow runs
        id: prerequisite-runs
        env:
          GH_TOKEN: ${{ github.token }}
          STAGING_RUN_ID: ${{ inputs.staging_evidence_run_id }}
          ROLLBACK_RUN_ID: ${{ inputs.rollback_evidence_run_id }}
        run: |
          set -Eeuo pipefail
          python3 - <<'PY'
          import json
          import os
          import re
          import urllib.request

          token = os.environ["GH_TOKEN"]
          repository = os.environ["GITHUB_REPOSITORY"]
          output = os.environ["GITHUB_OUTPUT"]
          expected_path = ".github/workflows/staging-readonly-certification.yml"
          values = {}
          for prefix, variable in (("staging", "STAGING_RUN_ID"), ("rollback", "ROLLBACK_RUN_ID")):
              run_id = os.environ[variable]
              request = urllib.request.Request(
                  f"https://api.github.com/repos/{repository}/actions/runs/{run_id}",
                  headers={
                      "Accept": "application/vnd.github+json",
                      "Authorization": f"Bearer {token}",
                      "User-Agent": "codestra-prerequisite-run-verifier/1",
                      "X-GitHub-Api-Version": "2022-11-28",
                  },
              )
              with urllib.request.urlopen(request, timeout=30) as response:
                  payload = json.load(response)
              if payload.get("id") != int(run_id):
                  raise SystemExit(f"{prefix} run identity mismatch")
              if payload.get("status") != "completed" or payload.get("conclusion") != "success":
                  raise SystemExit(f"{prefix} run is not completed successfully")
              if payload.get("event") != "workflow_dispatch" or payload.get("head_branch") != "main":
                  raise SystemExit(f"{prefix} run is not a protected-main dispatch")
              if payload.get("path") != expected_path:
                  raise SystemExit(f"{prefix} run came from an unexpected workflow")
              head_sha = payload.get("head_sha")
              attempt = payload.get("run_attempt")
              if not isinstance(head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", head_sha):
                  raise SystemExit(f"{prefix} run head SHA is invalid")
              if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt <= 0:
                  raise SystemExit(f"{prefix} run attempt is invalid")
              values[f"{prefix}_head_sha"] = head_sha
              values[f"{prefix}_run_attempt"] = str(attempt)
          with open(output, "a", encoding="utf-8") as destination:
              for key, value in values.items():
                  destination.write(f"{key}={value}\\n")
          PY
'''
    download_marker = "      - name: Download exact successful staging evidence\n"
    tail = replace_once(
        tail,
        download_marker,
        authentication + download_marker,
        "prerequisite run authentication",
    )
    rollback_download = '''      - name: Download exact successful rollback evidence
        uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c
        with:
          github-token: ${{ github.token }}
          run-id: ${{ inputs.rollback_evidence_run_id }}
          name: codestra-rollback-rehearsal-${{ inputs.confirm_candidate_id }}
          path: ${{ steps.materialize.outputs.work }}/rollback-evidence
'''
    staging_requirement_marker = "      - name: Require one GO staging evidence document\n"
    tail = replace_once(
        tail,
        staging_requirement_marker,
        rollback_download + staging_requirement_marker,
        "rollback artifact download",
    )
    old_requirement = '''          echo "path=${files[0]}" >> "$GITHUB_OUTPUT"
'''
    new_requirement = '''          mapfile -t rollback_files < <(find "${{ steps.materialize.outputs.work }}/rollback-evidence" -type f -name '*.json' -print)
          [[ "${#rollback_files[@]}" -eq 1 ]] || { echo "Expected exactly one rollback evidence JSON" >&2; exit 1; }
          if find "${{ steps.materialize.outputs.work }}/rollback-evidence" -type l -print -quit | grep -q .; then
            echo "Rollback evidence artifact contains a symbolic link" >&2
            exit 1
          fi
          echo "path=${files[0]}" >> "$GITHUB_OUTPUT"
          echo "rollback_path=${rollback_files[0]}" >> "$GITHUB_OUTPUT"
'''
    tail = replace_once(
        tail,
        old_requirement,
        new_requirement,
        "rollback evidence selection",
    )
    canary_run_marker = '''      - name: Apply and certify maximum one-percent GET/HEAD-only canary
        run: |
'''
    canary_run_replacement = '''      - name: Apply and certify maximum one-percent GET/HEAD-only canary
        env:
          STAGING_EVIDENCE_RUN_ATTEMPT: ${{ steps.prerequisite-runs.outputs.staging_run_attempt }}
          STAGING_EVIDENCE_HEAD_SHA: ${{ steps.prerequisite-runs.outputs.staging_head_sha }}
          ROLLBACK_EVIDENCE_RUN_ATTEMPT: ${{ steps.prerequisite-runs.outputs.rollback_run_attempt }}
          ROLLBACK_EVIDENCE_HEAD_SHA: ${{ steps.prerequisite-runs.outputs.rollback_head_sha }}
        run: |
'''
    tail = replace_once(
        tail,
        canary_run_marker,
        canary_run_replacement,
        "canary evidence environment",
    )
    tail = replace_once(
        tail,
        '''            --staging-evidence "${{ steps.staging-evidence.outputs.path }}" \\
            --canary-percent "$CANARY_PERCENT" \\
''',
        '''            --staging-evidence "${{ steps.staging-evidence.outputs.path }}" \\
            --rollback-evidence "${{ steps.staging-evidence.outputs.rollback_path }}" \\
            --canary-percent "$CANARY_PERCENT" \\
''',
        "canary rollback evidence CLI",
    )
    WORKFLOW.write_text(prefix + marker + tail, encoding="utf-8")


def patch_readme() -> None:
    path = OPS / "README.md"
    source = path.read_text(encoding="utf-8")
    addition = '''

## Environment isolation and authenticated prerequisites

The production canary must **not** reuse staging URLs or credentials. Configure
`production-readonly-canary` with these separately scoped secrets:

- `PRODUCTION_CANONICAL_CANDIDATE_B64` — byte-for-byte identical to the staging candidate;
- `PRODUCTION_ENDPOINT_MANIFEST_B64` — completed production canary target manifest;
- `PRODUCTION_READONLY_BEARER_TOKEN` — production read-only check identity;
- `PRODUCTION_METRICS_BEARER_TOKEN` — production protected-metrics identity;
- `PRODUCTION_GHCR_READ_TOKEN` — package-read-only identity.

The candidate SHA-256 confirmation must match both environment copies. The
production endpoint manifest carries production URLs, the canonical Keycloak
issuer, production zero-effect counters, and distinct baseline/canary probe
URLs. The controller rejects a staging manifest in the production environment
and rejects production credentials or URLs in staging.

A canary dispatch requires **both** a successful staging run ID and a successful
rollback-rehearsal run ID. The workflow authenticates each through the GitHub
Actions API, requiring a completed successful `workflow_dispatch` from `main`
and the exact release-control workflow path. The downloaded JSON is then bound
to the candidate ID, source-lock SHA, candidate SHA-256, exact workload source
and image identities, run ID, run attempt, producer head SHA, and required PASS
gates. A staging-only artifact cannot authorize the canary.

Every version endpoint must return both the exact source SHA and the exact
runtime image digest. HTTP redirects are not followed, and HTTP 404 is never an
acceptable Kong route result. Recovery points are accepted only after local
checksums, safe archive extraction, Odoo filestore byte-hash comparison, and a
PostgreSQL restore into a disposable no-network container all pass.
'''
    if "## Environment isolation and authenticated prerequisites" not in source:
        source += addition
    path.write_text(source, encoding="utf-8")


def main() -> int:
    patch_v2_controller()
    patch_entrypoint()
    patch_candidate_and_templates()
    patch_schemas()
    patch_workflow()
    patch_readme()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
