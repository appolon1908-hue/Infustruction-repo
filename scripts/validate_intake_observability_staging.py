#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy/staging/intake-observability"
EXPECTED_DIGEST = "sha256:695fa3ce3f50ba4d0ae0784976b946a0a683ca731155e4bd3bd9e90a4670b820"


def main() -> None:
    lock = json.loads((DEPLOY / "runtime-lock.v1.json").read_text())
    assert lock["schema_version"] == "1.0" and lock["environment"] == "staging"
    assert lock["middleware"]["image_digest"] == EXPECTED_DIGEST
    assert lock["middleware"]["image_reference"].endswith("@" + EXPECTED_DIGEST)
    assert lock["network"]["middleware_host_ports"] == []
    assert lock["network"]["private_network_internal"] is True
    assert lock["identity"]["maximum_token_ttl_seconds"] == 300
    assert lock["activation"] == {"prometheus_target": "pending", "blackbox_target": "pending", "production_authorized": False}
    assert lock["external_effects_enabled"] is False
    for value in lock["support_images"].values():
        assert re.fullmatch(r"[^\s]+@sha256:[0-9a-f]{64}", value)

    compose = yaml.safe_load((DEPLOY / "compose.yaml").read_text())
    services = compose["services"]
    assert set(services) == {"postgres", "redis", "middleware-migrate", "middleware"}
    assert services["middleware"]["image"] == lock["middleware"]["image_reference"]
    assert services["middleware-migrate"]["image"] == lock["middleware"]["image_reference"]
    assert "ports" not in services["middleware"]
    assert services["middleware"]["expose"] == ["8080"]
    assert compose["networks"]["private"]["internal"] is True
    assert services["postgres"]["image"] == lock["support_images"]["postgres"]
    assert services["redis"]["image"] == lock["support_images"]["redis"]

    script = (ROOT / "scripts/deploy_intake_observability_staging.sh").read_text()
    for required in (
        "compose down --volumes --remove-orphans",
        "docker pull \"$EXPECTED_IMAGE\"",
        "host ports are prohibited",
        "STAGING_DEPLOYMENT=PASS",
        "OUTBOX_DISPATCH_ENABLED=false",
        "LIVE_PSTN_DIALING=false",
    ):
        assert required in script
    assert "production-activation" not in script
    print("INFRASTRUCTURE_STAGING_INTAKE_OBSERVABILITY=PASS")


if __name__ == "__main__":
    main()
