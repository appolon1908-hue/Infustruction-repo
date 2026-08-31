#!/usr/bin/env python3
"""Fail-closed validation for Stage 6 source authority."""

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "STAGE6-SOURCE-LOCK.yaml"
COMPOSE_DIR = ROOT / "deploy/staging/runtime-reconciliation"
SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
SAFETY = {
    "LIVE_ADVERTISING_ENABLED": "false",
    "EXTERNAL_DELIVERY_ENABLED": "false",
    "SOCIAL_PUBLISHING_ENABLED": "false",
    "EXTERNAL_MODEL_CALLS_ENABLED": "false",
    "LIVE_SMS_DELIVERY": "false",
    "LIVE_EMAIL_DELIVERY": "false",
    "LIVE_PSTN_DIALING": "false",
    "PRODUCTION_DIALING": "DISABLED",
}


def main() -> None:
    lock = yaml.safe_load(LOCK.read_text())
    assert lock["production_write_activation"] is False
    assert lock["runtime_mutation_authorized"] is False
    assert len(lock["runtime_workloads"]) == 22
    for name, repo in lock["repositories"].items():
        assert SHA.fullmatch(repo["revision"]), (name, repo)
    for name, workload in lock["runtime_workloads"].items():
        assert DIGEST.fullmatch(workload["image_digest"]), (name, "image_digest")
        assert DIGEST.fullmatch(workload["rollback_digest"]), (name, "rollback_digest")
        value = workload.get("git_sha")
        assert value in {"UNVERIFIED", "NOT_APPLICABLE_VENDOR_IMAGE"} or SHA.fullmatch(value), (name, value)

    for filename in (
        "compose.middleware-source-remediation.yaml",
        "compose.odoo-source-remediation.yaml",
        "compose.n8n-safety-remediation.yaml",
        "compose.legacy-application-safety-hold.yaml",
    ):
        compose = yaml.safe_load((COMPOSE_DIR / filename).read_text())
        for service, definition in compose["services"].items():
            environment = definition.get("environment", {})
            for key, expected in SAFETY.items():
                assert str(environment[key]) == expected, (filename, service, key)

    source_services = set()
    for filename in (
        "compose.middleware-source-remediation.yaml",
        "compose.odoo-source-remediation.yaml",
        "compose.n8n-safety-remediation.yaml",
        "compose.legacy-application-safety-hold.yaml",
    ):
        compose = yaml.safe_load((COMPOSE_DIR / filename).read_text())
        source_services.update(
            name for name in compose["services"]
            if "migration" not in name
        )
    assert len(source_services) == 17, source_services

    middleware = yaml.safe_load((COMPOSE_DIR / "compose.middleware-source-remediation.yaml").read_text())
    app_command = " ".join(middleware["services"]["middleware-staging"]["command"])
    assert "migrat" not in app_command.lower() and "alembic" not in app_command.lower()
    assert middleware["services"]["middleware-migration"]["restart"] == "no"

    odoo = yaml.safe_load((COMPOSE_DIR / "compose.odoo-source-remediation.yaml").read_text())
    for service in ("odoo19-staging", "odoo19-master-staging"):
        command = " ".join(odoo["services"][service]["command"])
        assert "--init" not in command and "--update" not in command
    for service in ("odoo19-module-migration", "odoo19-master-module-migration"):
        assert odoo["services"][service]["restart"] == "no"
        assert "--stop-after-init" in odoo["services"][service]["command"]
    gates = lock["gates"]
    assert gates["dispositions_resolved"] is True
    assert gates["all_planned_replacement_images_reviewed_and_digest_pinned"] is True
    assert gates["unverified_workloads_frozen_from_automatic_replacement"] is True
    assert gates["rollback_digests_recorded_for_all_workloads"] is True
    assert gates["source_lock"] == "PASS"
    assert gates["stage6_preflight"] == "FAIL_SCOPED_RUNTIME_READBACK"
    assert gates["backup_preparation_allowed"] is False
    assert gates["runtime_reconciliation_allowed"] is False
    assert gates["stage6_path_business_writes"] == "NOT_PROVEN_DISABLED"
    assert gates["out_of_scope_production_writes"] == "ACTIVE_DO_NOT_TOUCH"
    scope = lock["safety_scope"]
    assert scope["decision"] == "APPROVED"
    assert scope["in_scope_host"] == "65.109.65.169"
    assert scope["in_scope_workloads"] == 22
    assert scope["out_of_scope_active_production"]["disposition"] == "OUT_OF_SCOPE_ACTIVE_PRODUCTION_DO_NOT_TOUCH"
    runtime_safety = lock["current_runtime_safety"]
    assert runtime_safety["status"] == "FAIL_SCOPED_RUNTIME_READBACK"
    assert runtime_safety["stage6_path_business_writes"] == "NOT_PROVEN_DISABLED"
    assert runtime_safety["scoped_runtime_readback"] == "FAIL"
    assert runtime_safety["workloads_present"] == 22
    assert runtime_safety["workload_digests_matching"] == 22
    assert runtime_safety["safety_complete_workloads"] == 0
    assert runtime_safety["unsafe_true_values_observed"] == 0
    assert runtime_safety["out_of_scope_active_production"] == "OUT_OF_SCOPE_ACTIVE_PRODUCTION_DO_NOT_TOUCH"
    print("SOURCE_LOCK=PASS")
    print("STAGE6_PREFLIGHT=FAIL_SCOPED_RUNTIME_READBACK")
    print("STAGE6_PATH_BUSINESS_WRITES=NOT_PROVEN_DISABLED")
    print("OUT_OF_SCOPE_PRODUCTION=ACTIVE_DO_NOT_TOUCH")
    print("STAGE6_SOURCE_LOCK_VALIDATION=PASS")


if __name__ == "__main__":
    main()
