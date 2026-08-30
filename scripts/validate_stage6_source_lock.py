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
    assert gates["stage6_preflight"] == "FAIL"
    assert gates["backup_preparation_allowed"] is False
    assert gates["runtime_reconciliation_allowed"] is False
    assert gates["production_business_writes"] == "NOT_PROVEN_DISABLED"
    runtime_safety = lock["current_runtime_safety"]
    assert runtime_safety["status"] == "FAIL"
    assert runtime_safety["production_business_writes"] == "NOT_PROVEN_DISABLED"
    assert runtime_safety["LIVE_EMAIL_DELIVERY"] is True
    assert runtime_safety["core_runtime_readback"] == "BLOCKED_NO_GENERAL_SSH"
    print("SOURCE_LOCK=PASS")
    print("STAGE6_PREFLIGHT=FAIL")
    print("PRODUCTION_BUSINESS_WRITES=NOT_PROVEN_DISABLED")
    print("STAGE6_SOURCE_LOCK_VALIDATION=PASS")


if __name__ == "__main__":
    main()
