#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "operations/staging-readonly/portfolio_release_dispatch.py"
SPEC = importlib.util.spec_from_file_location("portfolio_release_dispatch", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PortfolioReleaseDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run = {
            "id": 123,
            "head_sha": "1" * 40,
        }
        self.evidence = {
            "candidate_id": "codestra-20260903-001",
            "candidate_source_lock_sha": "2" * 40,
            "candidate_manifest_sha256": "3" * 64,
            "mode": "staging",
            "producer": {
                "repository": MODULE.REPOSITORY,
                "workflow": MODULE.CHILD_WORKFLOW,
                "head_sha": self.run["head_sha"],
                "run_id": self.run["id"],
            },
            "verdict": "GO",
            "gates": [
                {"gate": "source", "status": "PASS"},
                {"gate": "readiness", "status": "PASS"},
            ],
            "rollback_performed": False,
            "error": None,
        }

    def write_evidence(self, value: dict) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "evidence.json"
        path.write_text(json.dumps(value))
        return path

    def validate(self, value: dict, mode: str = "staging") -> dict:
        return MODULE.validate_child_evidence(
            self.write_evidence(value),
            mode=mode,
            candidate_id=self.evidence["candidate_id"],
            source_lock_sha=self.evidence["candidate_source_lock_sha"],
            candidate_sha256=self.evidence["candidate_manifest_sha256"],
            child_run=self.run,
        )

    def test_valid_staging_evidence_passes(self) -> None:
        self.assertEqual(self.validate(self.evidence)["verdict"], "GO")

    def test_non_go_evidence_is_rejected(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["verdict"] = "NO_GO"
        with self.assertRaises(MODULE.GateError):
            self.validate(value)

    def test_candidate_identity_mismatch_is_rejected(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["candidate_manifest_sha256"] = "4" * 64
        with self.assertRaises(MODULE.GateError):
            self.validate(value)

    def test_producer_run_mismatch_is_rejected(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["producer"]["run_id"] = 999
        with self.assertRaises(MODULE.GateError):
            self.validate(value)

    def test_non_passing_gate_is_rejected(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["gates"].append({"gate": "metrics", "status": "FAIL"})
        with self.assertRaises(MODULE.GateError):
            self.validate(value)

    def test_rollback_requires_execution_proof(self) -> None:
        value = copy.deepcopy(self.evidence)
        value["mode"] = "rollback-rehearsal"
        with self.assertRaises(MODULE.GateError):
            self.validate(value, mode="rollback-rehearsal")
        value["rollback_performed"] = True
        self.assertTrue(
            self.validate(value, mode="rollback-rehearsal")["rollback_performed"]
        )

    def test_safe_extract_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("../escape.json", "{}")
            with self.assertRaises(MODULE.GateError):
                MODULE.safe_extract(archive, root / "output")

    def test_wrapper_binding_is_exact(self) -> None:
        binding = {
            "schema_version": "codestra.portfolio-infrastructure-stage.v1",
            "mode": "staging",
            "candidate_id": self.evidence["candidate_id"],
            "source_lock_sha": self.evidence["candidate_source_lock_sha"],
            "candidate_sha256": self.evidence["candidate_manifest_sha256"],
            "status": "PASS",
            "external_effects_enabled": False,
            "child_run_id": 123,
        }
        parsed = MODULE.validate_wrapper_evidence(
            self.write_evidence(binding),
            mode="staging",
            candidate_id=binding["candidate_id"],
            source_lock_sha=binding["source_lock_sha"],
            candidate_sha256=binding["candidate_sha256"],
        )
        self.assertEqual(parsed["child_run_id"], 123)
        binding["external_effects_enabled"] = True
        with self.assertRaises(MODULE.GateError):
            MODULE.validate_wrapper_evidence(
                self.write_evidence(binding),
                mode="staging",
                candidate_id=binding["candidate_id"],
                source_lock_sha=binding["source_lock_sha"],
                candidate_sha256=binding["candidate_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
