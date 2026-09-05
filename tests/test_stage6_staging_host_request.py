#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "config" / "stage6-staging-host-provisioning-request.v1.json"
VALIDATOR = ROOT / "tools" / "validate_stage6_staging_host_request.py"


class StagingHostRequestTests(unittest.TestCase):
    def run_validator(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def test_repository_request_is_fail_closed_and_valid(self) -> None:
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("STAGE6_STAGING_HOST_REQUEST_AUTHORITY=PASS", result.stdout)
        self.assertIn("BLOCKED_ACCOUNT_CREDENTIALS_REQUIRED", result.stdout)

    def test_request_cannot_claim_creation_without_evidence(self) -> None:
        data = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertFalse(data["host_created"])
        self.assertFalse(data["host_verified"])
        self.assertFalse(data["deployment_authorized"])
        self.assertNotIn("observed_evidence", data)

    def test_required_outputs_bind_identity_and_provenance(self) -> None:
        data = json.loads(REQUEST.read_text(encoding="utf-8"))
        outputs = set(data["required_provisioning_outputs"])
        self.assertTrue(
            {
                "provider_resource_id",
                "private_ip",
                "ssh_host_key_fingerprint",
                "workflow_run_id",
                "workflow_source_sha",
                "configuration_checksum",
            }.issubset(outputs)
        )

    def test_safety_controls_are_all_false(self) -> None:
        data = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertTrue(data["safety_controls"])
        self.assertTrue(all(value is False for value in data["safety_controls"].values()))


if __name__ == "__main__":
    unittest.main()
