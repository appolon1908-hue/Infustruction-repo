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


def load(name: str) -> dict:
    value = json.loads((ROOT / name).read_text())
    assert value["server"] == "37.27.128.39"
    return value


def component_names(rows: list[dict]) -> set[str]:
    return {row["component"] for row in rows}


def main() -> None:
    assert REQUIRED <= {path.name for path in ROOT.iterdir()}
    source = load("production-source-lock.json")
    images = load("production-image-lock.json")
    runtime = load("runtime-inventory.json")
    api = load("api-certification.json")
    network = load("network-inventory.json")
    recovery = load("backup-restore-matrix.json")
    rollback = load("rollback-matrix.json")
    for value in (source, images, runtime, api, recovery, rollback):
        assert component_names(value["components"]) == EXPECTED
    assert source["lock_status"] == "FAIL"
    assert images["lock_status"] == "FAIL"
    assert all(not row["activation_allowed"] for row in source["components"])
    assert all(SHA.fullmatch(row["source_sha"]) for row in source["components"])
    assert all(SHA.fullmatch(row["staging_sha"]) for row in source["components"])
    for row in images["components"]:
        digest = row["runtime_image_digest"]
        assert digest is None or DIGEST.fullmatch(digest)
        assert row["activation_allowed"] is False
    assert runtime["running_unhealthy_containers"] == 0
    assert runtime["restarting_containers"] == 0
    assert len(runtime["critical_alerts"]) == 2
    assert api["api_contracts_complete"] == 0
    assert api["apis_runtime_verified"] == 0
    assert network["network_gate"] == "FAIL"
    assert sum(row["status"] == "FAIL" for row in network["tls"]) == 11
    assert recovery["backup_gate"] == recovery["restore_gate"] == "FAIL"
    assert rollback["rollback_gate"] == "FAIL"
    assert rollback["production_changed"] is False
    matrix = (ROOT / "authority-matrix.yaml").read_text()
    assert "activation_allowed: false" in matrix
    assert "overall_verdict: NOT_PRODUCTION_CERTIFIED" in matrix
    for name in REQUIRED:
        text = (ROOT / name).read_text(errors="ignore").lower()
        assert ":latest" not in text
    print("server_b_observability_authority=PASS activation_allowed=false")


if __name__ == "__main__":
    main()
