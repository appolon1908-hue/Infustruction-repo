#!/usr/bin/env python3
"""Validate the repository-only observability mission authority."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSION = ROOT / "CODESTRA_OBSERVABILITY_REPO_FIRST_CODEX_MISSION_2026-09-02.md"

COMPONENT_REPOSITORIES = {
    "appolon1908-hue/Codestra-Grafana-",
    "appolon1908-hue/Codestra-Prometheus",
    "appolon1908-hue/Codestra-Alertmanager",
    "appolon1908-hue/Codestra-Loki",
    "appolon1908-hue/Codestra-Tempo",
    "appolon1908-hue/Codestra-Telemetry",
    "appolon1908-hue/Codestra-Alloy",
    "appolon1908-hue/Codestra-Node-Exporter",
    "appolon1908-hue/Codestra-cAdvisor",
    "appolon1908-hue/Codestra-Postgres-Exporter",
    "appolon1908-hue/Codestra-Redis-Exporter",
    "appolon1908-hue/Codestra-Blackbox-Exporter",
    "appolon1908-hue/Superset",
    "appolon1908-hue/Codestra-OpenBao",
}

SUPPORTING_REPOSITORIES = {
    "appolon1908-hue/Infustruction-repo",
    "appolon1908-hue/codestra-production-runtime-authority",
    "appolon1908-hue/Keycloak",
    "appolon1908-hue/Caddy",
    "appolon1908-hue/Middleware-",
    "appolon1908-hue/communication-platform-",
}


def require(source: str, token: str) -> None:
    if token not in source:
        raise ValueError(f"mission authority missing: {token}")


def main() -> None:
    source = MISSION.read_text(encoding="utf-8")
    require(source, "**Mission ID:** `CODESTRA_OBSERVABILITY_REPO_FIRST_2026-09-02`")
    require(source, "**Execution mode:** repository, CI, release-registry, and artifact work only")
    require(source, "This is a repository-only mission.")
    require(source, "It must not alter the production host or any external runtime.")
    require(source, "Do not claim production was changed, deployed, or certified")

    repositories = set(re.findall(r"`(appolon1908-hue/[^`]+)`", source))
    missing_components = sorted(COMPONENT_REPOSITORIES - repositories)
    missing_support = sorted(SUPPORTING_REPOSITORIES - repositories)
    if missing_components or missing_support:
        raise ValueError(
            f"repository authority incomplete: components={missing_components}, support={missing_support}"
        )

    require(source, "PostgreSQL Exporter: no public DNS hostname at all")
    require(source, "`workload_instance` label only when it is derived from a bounded replica slot")
    require(source, "never retain raw container IDs, names, pod UIDs, or arbitrary labels")
    require(source, "webhook v4 suppresses those notifications")
    require(source, "separately authenticated, read-only Alertmanager status reconciliation source")
    require(source, "must not infer it from a missing webhook")

    forbidden = (
        "MODE=PRODUCTION_LIVE",
        "PRODUCTION_HOST_CONTACTED=YES",
        "PRODUCTION_CHANGED=YES",
        "deployment_enabled=true",
        "SERVER_INSTALL_AUTHORIZED=YES\n",
    )
    present = [token for token in forbidden if token in source]
    if present:
        raise ValueError(f"repository-only mission contains activation claim: {present}")

    print("CODESTRA_OBSERVABILITY_REPOSITORY_FIRST_MISSION=PASS")
    print("COMPONENT_AUTHORITIES=14")
    print("SUPPORTING_AUTHORITIES=6")
    print("PRODUCTION_HOST_CONTACT_AUTHORIZED=NO")


if __name__ == "__main__":
    main()
