#!/usr/bin/env python3
"""Validate the repository-to-live Codex mission for 37.27.128.39."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSION = ROOT / "missions/CODESTRA_37_27_128_39_COORDINATED_PRODUCTION_LIVE_CODEX_MISSION_2026-09-02.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    require(MISSION.is_file(), f"missing mission: {MISSION}")
    text = MISSION.read_text(encoding="utf-8")

    required_identity = (
        "TARGET_HOST=37.27.128.39",
        "HOST_ROLE=CODESTRA_OBSERVABILITY_SECURITY_EMAIL_PROVIDER_HOST",
        "PRIMARY_ADMIN_USERNAME=appolon",
        "PRIMARY_ADMIN_EMAIL=appolon@codestra.co",
        "BYPASS_USED=NONE",
        "SSH_CONFIGURATION_CHANGES=FORBIDDEN",
    )
    for value in required_identity:
        require(value in text, f"missing identity or safety value: {value}")

    repositories = {
        "appolon1908-hue/Codestra-Prometheus",
        "appolon1908-hue/Codestra-Grafana-",
        "appolon1908-hue/Codestra-Alertmanager",
        "appolon1908-hue/Codestra-Loki",
        "appolon1908-hue/Codestra-Tempo",
        "appolon1908-hue/Codestra-Telemetry",
        "appolon1908-hue/Codestra-Alloy",
        "appolon1908-hue/Codestra-Node-Exporter",
        "appolon1908-hue/Codestra-cAdvisor",
        "appolon1908-hue/Codestra-Redis-Exporter",
        "appolon1908-hue/Codestra-Postgres-Exporter",
        "appolon1908-hue/Codestra-Blackbox-Exporter",
        "appolon1908-hue/Superset",
        "appolon1908-hue/Codestra-OpenBao",
        "appolon1908-hue/Caddy",
        "appolon1908-hue/Keycloak",
        "appolon1908-hue/Middleware-",
        "appolon1908-hue/Infustruction-repo",
    }
    for repository in sorted(repositories):
        require(f"`{repository}`" in text, f"missing principal repository: {repository}")

    mission_numbers = set(re.findall(r"^### MISSION (\d{2}) —", text, flags=re.MULTILINE))
    require(mission_numbers == {f"{number:02d}" for number in range(11)},
            f"mission division mismatch: {sorted(mission_numbers)}")

    required_artifacts = (
        "PRODUCTION-BOM.yaml",
        "DEPLOYMENT-WAVE.yaml",
        "INTEGRATION-CONTRACT-LOCK.yaml",
        "CURRENT-RUNTIME-INVENTORY.json",
        "PRECHANGE-BACKUP-MANIFEST.json",
        "RESTORE-EVIDENCE.json",
        "ROLLBACK-MATRIX.yaml",
        "PRODUCTION-CERTIFICATION.md",
        "POST-LIVE-READBACK.json",
    )
    for artifact in required_artifacts:
        require(artifact in text, f"missing coordination artifact: {artifact}")

    required_gates = (
        "SOURCE_LOCK=PASS",
        "IMMUTABLE_IMAGES=PASS",
        "CONFIGURATION_LOCK=PASS",
        "MIGRATION_LOCK=PASS",
        "BACKUP=PASS",
        "ISOLATED_RESTORE=PASS",
        "ROLLBACK=PASS",
        "REMOTE_WATCHDOG=PASS",
        "TOTAL_HOST_OUTAGE_ALERTING=PASS",
        "OVERALL_VERDICT=PRODUCTION LIVE",
        "OVERALL_VERDICT=NO-GO",
    )
    for gate in required_gates:
        require(gate in text, f"missing certification gate: {gate}")

    required_alert_contract = (
        "sender=alerts@codestra.co",
        "recipient=appolon@codestra.co",
        "recipient_override_allowed=false",
        "sender_override_allowed=false",
        "business_email_allowed=false",
        "marketing_email_allowed=false",
        "campaign_email_allowed=false",
        "DIRECT_SMTP_NORMAL_ROUTE=ABSENT",
        "EMAILS_SENT_BEFORE_CANARY=0",
        "DUPLICATE_EXTERNAL_EFFECTS=0",
    )
    for value in required_alert_contract:
        require(value in text, f"missing alert-delivery control: {value}")

    forbidden_patterns = (
        r"(?i)password\s*[:=]\s*[^<{$\s][^\s]+",
        r"(?i)client_secret\s*[:=]\s*[A-Za-z0-9_-]{16,}",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"(?i)docker\s+system\s+prune\s+-a",
        r"(?i)git\s+push\s+--force",
        r"(?i)insecure_skip_verify\s*[:=]\s*true",
    )
    for pattern in forbidden_patterns:
        require(re.search(pattern, text) is None, f"forbidden pattern matched: {pattern}")

    require("no direct Alertmanager-to-SMTP normal route" in text,
            "normal direct SMTP prohibition is missing")
    require("no automatic repeat of an operation with an ambiguous provider outcome" in text,
            "unknown-outcome replay prohibition is missing")
    require("exact protected merge SHA" in text, "protected source identity is missing")
    require("image_repository_at_sha256" in text, "digest-pinned image identity is missing")
    require("one firing and one resolved alert" in text,
            "bounded firing/resolved canary contract is missing")

    print("COORDINATED_PRODUCTION_MISSION=PASS")
    print("TARGET_HOST=37.27.128.39")
    print("PRINCIPAL_REPOSITORIES=18")
    print("MISSION_SEGMENTS=11")
    print("BYPASS_USED=NONE")
    print("SERVER_CHANGED=NO")
    print("EMAILS_SENT=0")


if __name__ == "__main__":
    main()
