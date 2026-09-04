#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_PATH = ROOT / "config" / "stage6-staging-host-provisioning-request.v1.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def fail(message: str) -> None:
    print(f"STAGE6_STAGING_HOST_REQUEST_ERROR={message}", file=sys.stderr)
    raise SystemExit(1)


def load() -> dict[str, Any]:
    try:
        value = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse request: {exc}")
    if not isinstance(value, dict):
        fail("request must contain an object")
    return value


def main() -> None:
    request = load()
    if request.get("schema_version") != 1:
        fail("schema_version must be 1")
    if request.get("repository") != "appolon1908-hue/Infustruction-repo":
        fail("repository authority mismatch")
    if request.get("workflow") != ".github/workflows/stage6-provision-staging-host.yml":
        fail("provisioning workflow authority mismatch")
    if request.get("protected_environment") != "stage6-infrastructure-provisioning":
        fail("protected environment mismatch")
    if request.get("network_class") != "isolated-private-staging":
        fail("staging host must use the isolated private network class")

    expected_blocked = request.get("status") == "BLOCKED_ACCOUNT_CREDENTIALS_REQUIRED"
    if expected_blocked:
        if request.get("deployment_authorized") is not False:
            fail("blocked request cannot authorize deployment")
        if request.get("host_created") is not False or request.get("host_verified") is not False:
            fail("blocked request cannot claim host creation or verification")

    source = request.get("required_source")
    if not isinstance(source, dict):
        fail("required_source is missing")
    if source.get("production_platform_repository") != "appolon1908-hue/codestra-production-platform":
        fail("production platform source authority mismatch")
    if source.get("production_platform_branch") != "release/production-activation":
        fail("production platform protected branch mismatch")
    if source.get("source_lock_status") != "PASS":
        fail("provisioning may require only a PASS production source lock")
    if source.get("candidate_matrix_deployment_authorized") is not True:
        fail("provisioning must require an authorized immutable candidate matrix")
    if source.get("endpoint_manifest_checksum_required") is not True:
        fail("endpoint manifest checksum must be required")

    outputs = request.get("required_provisioning_outputs")
    verification = request.get("required_verification")
    forbidden = request.get("forbidden_actions")
    for label, values, minimum in (
        ("required_provisioning_outputs", outputs, 10),
        ("required_verification", verification, 10),
        ("forbidden_actions", forbidden, 8),
    ):
        if not isinstance(values, list) or len(values) < minimum:
            fail(f"{label} is incomplete")
        if len(values) != len(set(values)):
            fail(f"{label} contains duplicates")

    for required in (
        "provider_resource_id",
        "private_ip",
        "ssh_host_key_fingerprint",
        "workflow_run_id",
        "workflow_source_sha",
        "configuration_checksum",
    ):
        if required not in outputs:
            fail(f"provisioning output missing: {required}")
    for required in (
        "private_network_only",
        "public_native_service_ports_absent",
        "operator_identity_least_privilege",
        "failed_systemd_units_zero",
        "destruction_and_recreation_test",
    ):
        if required not in verification:
            fail(f"verification control missing: {required}")

    safety = request.get("safety_controls")
    if not isinstance(safety, dict) or not safety:
        fail("safety_controls must be a non-empty object")
    enabled = sorted(name for name, value in safety.items() if value is not False)
    if enabled:
        fail(f"all safety controls must remain false before provisioning: {enabled}")

    if request.get("host_created") or request.get("host_verified"):
        evidence = request.get("observed_evidence")
        if not isinstance(evidence, dict):
            fail("created or verified host requires observed_evidence")
        source_sha = str(evidence.get("workflow_source_sha", ""))
        if not SHA_RE.fullmatch(source_sha):
            fail("observed workflow_source_sha must be a full Git SHA")
        missing = sorted(value for value in outputs if value not in evidence)
        if missing:
            fail(f"observed provisioning evidence is incomplete: {missing}")
        verification_results = evidence.get("verification_results")
        if not isinstance(verification_results, dict):
            fail("verification_results are missing")
        failed = sorted(name for name in verification if verification_results.get(name) != "PASS")
        if failed:
            fail(f"host verification is incomplete: {failed}")
        if request.get("status") != "CREATED_AND_VERIFIED":
            fail("complete evidence requires status CREATED_AND_VERIFIED")

    print("STAGE6_STAGING_HOST_REQUEST_AUTHORITY=PASS")
    print(f"STAGE6_STAGING_HOST_STATUS={request.get('status')}")


if __name__ == "__main__":
    main()
