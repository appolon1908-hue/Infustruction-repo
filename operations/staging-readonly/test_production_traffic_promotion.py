#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "operations/staging-readonly/production_traffic_promotion.py"
SPEC = importlib.util.spec_from_file_location("production_traffic_promotion", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProductionTrafficPromotionTests(unittest.TestCase):
    def write_json(self, value: dict) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "evidence.json"
        path.write_text(json.dumps(value))
        return path

    def evidence(self) -> dict:
        return {
            "schema_version": MODULE.SCHEMA,
            "candidate_id": "codestra-20260903-001",
            "candidate_source_lock_sha": "1" * 40,
            "candidate_manifest_sha256": "2" * 64,
            "controller_sha256": "3" * 64,
            "previous_traffic_percent": 1,
            "traffic_percent": 100,
            "same_candidate": True,
            "source_and_digest_match": True,
            "readiness": "PASS",
            "monitoring": "PASS",
            "kong_routes": "29/29",
            "rollback_controller_verified": True,
            "external_effects_enabled": False,
            "verdict": "GO",
            "error": None,
        }

    def validate(self, value: dict) -> dict:
        baseline = self.evidence()
        return MODULE.validate_controller_evidence(
            self.write_json(value),
            candidate_id=baseline["candidate_id"],
            source_lock_sha=baseline["candidate_source_lock_sha"],
            candidate_sha256=baseline["candidate_manifest_sha256"],
            controller_sha256=baseline["controller_sha256"],
        )

    def test_complete_go_evidence_passes(self) -> None:
        self.assertEqual(self.validate(self.evidence())["traffic_percent"], 100)

    def test_candidate_drift_is_rejected(self) -> None:
        value = self.evidence()
        value["same_candidate"] = False
        with self.assertRaises(MODULE.PromotionError):
            self.validate(value)

    def test_source_digest_drift_is_rejected(self) -> None:
        value = self.evidence()
        value["source_and_digest_match"] = False
        with self.assertRaises(MODULE.PromotionError):
            self.validate(value)

    def test_missing_route_readback_is_rejected(self) -> None:
        value = self.evidence()
        value["kong_routes"] = "28/29"
        with self.assertRaises(MODULE.PromotionError):
            self.validate(value)

    def test_external_effects_are_rejected(self) -> None:
        value = self.evidence()
        value["external_effects_enabled"] = True
        with self.assertRaises(MODULE.PromotionError):
            self.validate(value)

    def test_non_go_verdict_is_rejected(self) -> None:
        value = self.evidence()
        value["verdict"] = "NO_GO"
        with self.assertRaises(MODULE.PromotionError):
            self.validate(value)

    def test_candidate_file_requires_digest_images_and_disabled_effects(self) -> None:
        candidate = {
            "schema": "codestra.release-control.v1",
            "candidate_id": "codestra-20260903-001",
            "candidate_source_lock_sha": "1" * 40,
            "workloads": [
                {
                    "source_sha": "4" * 40,
                    "image": "ghcr.io/appolon1908-hue/example@sha256:" + "5" * 64,
                }
            ],
            "safety": {
                "LIVE_WRITE": False,
                "LIVE_EMAIL_DELIVERY": False,
                "PRODUCTION_DIALING": "DISABLED",
            },
            "canary": {"max_percent": 1, "allowed_methods": ["GET", "HEAD"]},
        }
        path = self.write_json(candidate)
        digest = MODULE.file_sha256(path)
        parsed = MODULE.validate_candidate_file(
            path,
            candidate_id=candidate["candidate_id"],
            source_lock_sha=candidate["candidate_source_lock_sha"],
            candidate_sha256=digest,
        )
        self.assertEqual(len(parsed["workloads"]), 1)
        candidate["workloads"][0]["image"] = "ghcr.io/example/app:latest"
        bad_path = self.write_json(candidate)
        with self.assertRaises(MODULE.PromotionError):
            MODULE.validate_candidate_file(
                bad_path,
                candidate_id=candidate["candidate_id"],
                source_lock_sha=candidate["candidate_source_lock_sha"],
                candidate_sha256=MODULE.file_sha256(bad_path),
            )


if __name__ == "__main__":
    unittest.main()
