#!/usr/bin/env python3
"""Fail-closed validation for Server B observability host authority."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "Loki",
    "Prometheus",
    "Grafana",
    "Tempo",
    "OpenTelemetry Collector",
    "Alloy",
    "Node Exporter",
    "cAdvisor",
    "Redis Exporter",
    "Blackbox Exporter",
    "Superset",
    "OpenBao",
}
SHA = re.compile(r"[0-9a-f]{40}")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
REQUIRED = {
    "repository-inventory.json",
    "production-source-lock.json",
    "production-image-lock.json",
    "authority-matrix.yaml",
    "api-certification.json",
    "runtime-inventory.json",
    "network-inventory.json",
    "backup-restore-matrix.json",
    "rollback-matrix.json",
    "certification-report.md",
    "current-blockers.md",
    "release-layout.json",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"server_b_observability_authority=FAIL reason={message}")


def load(name: str) -> dict:
    value = json.loads((ROOT / name).read_text())
    require(value.get("server") == "37.27.128.39", f"server_mismatch:{name}")
    return value


def component_names(rows: list[dict]) -> set[str]:
    return {row["component"] for row in rows}


def main() -> None:
    require(
        REQUIRED <= {path.name for path in ROOT.iterdir()},
        "required_file_missing",
    )
    source = load("production-source-lock.json")
    images = load("production-image-lock.json")
    runtime = load("runtime-inventory.json")
    api = load("api-certification.json")
    network = load("network-inventory.json")
    recovery = load("backup-restore-matrix.json")
    rollback = load("rollback-matrix.json")
    for value in (source, images, runtime, api, recovery, rollback):
        require(
            component_names(value["components"]) == EXPECTED,
            "component_inventory_mismatch",
        )
    require(source.get("lock_status") == "FAIL", "source_lock_not_fail_closed")
    require(images.get("lock_status") == "FAIL", "image_lock_not_fail_closed")
    require(
        all(not row["activation_allowed"] for row in source["components"]),
        "source_activation_unexpectedly_allowed",
    )
    require(
        all(SHA.fullmatch(row["source_sha"]) for row in source["components"]),
        "invalid_source_sha",
    )
    require(
        all(SHA.fullmatch(row["staging_sha"]) for row in source["components"]),
        "invalid_staging_sha",
    )
    for row in images["components"]:
        digest = row["runtime_image_digest"]
        require(
            digest is None or bool(DIGEST.fullmatch(digest)), "invalid_image_digest"
        )
        require(
            row["activation_allowed"] is False, "image_activation_unexpectedly_allowed"
        )
    require(runtime["running_unhealthy_containers"] == 0, "unhealthy_container_count")
    require(runtime["restarting_containers"] == 0, "restarting_container_count")
    require(len(runtime["critical_alerts"]) == 2, "critical_alert_inventory_drift")
    require(api["api_contracts_complete"] == 0, "api_contract_count_drift")
    require(api["apis_runtime_verified"] == 0, "runtime_api_count_drift")
    require(network["network_gate"] == "FAIL", "network_gate_not_fail_closed")
    require(
        sum(row["status"] == "FAIL" for row in network["tls"]) == 11,
        "tls_failure_count_drift",
    )
    require(
        recovery["backup_gate"] == recovery["restore_gate"] == "FAIL",
        "recovery_gate_not_fail_closed",
    )
    require(rollback["rollback_gate"] == "FAIL", "rollback_gate_not_fail_closed")
    require(rollback["production_changed"] is False, "production_change_mismatch")
    matrix = (ROOT / "authority-matrix.yaml").read_text()
    require("activation_allowed: false" in matrix, "activation_matrix_not_fail_closed")
    require(
        "overall_verdict: NOT_PRODUCTION_CERTIFIED" in matrix,
        "verdict_matrix_not_fail_closed",
    )
    for name in REQUIRED:
        text = (ROOT / name).read_text(errors="ignore").lower()
        require(":latest" not in text, f"mutable_latest_reference:{name}")
    print("server_b_observability_authority=PASS activation_allowed=false")


if __name__ == "__main__":
    main()
