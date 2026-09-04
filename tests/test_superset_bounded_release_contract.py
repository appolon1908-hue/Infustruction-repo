from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "operations/superset-bounded-release/contract.v1.json"
VALIDATOR = ROOT / "scripts/validate_superset_bounded_release_contract.py"


class SupersetBoundedReleaseContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_canonical_contract_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("SUPERSET_BOUNDED_RELEASE_CONTRACT=PASS", completed.stdout)

    def test_release_cannot_activate_runtime(self) -> None:
        self.assertFalse(self.data["release"]["runtime_activation_by_release"])
        self.assertFalse(self.data["safety_state"]["deployment_authorized"])
        self.assertFalse(self.data["safety_state"]["production_certified"])

    def test_runner_and_environment_contract_is_exact(self) -> None:
        staging = self.data["staging"]
        production = self.data["production_readonly_canary"]
        self.assertEqual(staging["runner_labels"], ["self-hosted", "codestra-staging"])
        self.assertEqual(staging["environment"], "staging-readonly")
        self.assertEqual(
            production["runner_labels"],
            ["self-hosted", "codestra-production-canary"],
        )
        self.assertEqual(production["environment"], "production-readonly-canary")

    def test_canary_is_one_percent_get_head_only_and_rolls_back(self) -> None:
        canary = self.data["production_readonly_canary"]
        self.assertEqual(canary["maximum_percent"], 1)
        self.assertEqual(canary["methods"], ["GET", "HEAD"])
        self.assertTrue(canary["read_only"])
        self.assertTrue(canary["runtime_must_be_restored_after_canary"])
        self.assertEqual(canary["controller"]["required_owner_uid"], 0)
        self.assertFalse(canary["controller"]["group_world_writable"])

    def test_pending_candidate_has_no_fabricated_identity(self) -> None:
        candidate = self.data["candidate"]
        self.assertEqual(candidate["status"], "PENDING_PROTECTED_SUPERSET_RELEASE")
        for key, value in candidate.items():
            if key != "status":
                self.assertIsNone(value, key)

    def test_every_external_binding_and_live_effect_is_fail_closed(self) -> None:
        self.assertTrue(self.data["required_external_bindings"])
        self.assertTrue(self.data["safety_state"])
        self.assertTrue(all(value is False for value in self.data["required_external_bindings"].values()))
        self.assertTrue(all(value is False for value in self.data["safety_state"].values()))


if __name__ == "__main__":
    unittest.main()
