from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "repository_name_aliases",
    ROOT / "scripts" / "validate_repository_name_aliases.py",
)
assert SPEC is not None and SPEC.loader is not None
AUTHORITY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUTHORITY)


class RepositoryNameAliasTests(unittest.TestCase):
    def test_runtime_critical_classification_is_exact(self) -> None:
        data = AUTHORITY.load()
        changed = copy.deepcopy(data)
        changed["mappings"][0]["runtime_critical"] = False
        with patch.object(AUTHORITY, "load", return_value=changed):
            with self.assertRaises(SystemExit):
                AUTHORITY.validate()

    def test_planned_target_is_denied_in_operational_source(self) -> None:
        target = "appolon1908-hue/restaurant-frontend"
        fake_path = ROOT / "release" / "synthetic-lock.json"
        with patch.object(
            Path,
            "read_text",
            return_value='{"repository":"' + target + '"}',
        ):
            with self.assertRaises(SystemExit):
                AUTHORITY.validate_planned_targets_absent(
                    [fake_path],
                    {target},
                )

    def test_operational_scan_includes_workflows_infra_scripts_and_submodules(self) -> None:
        expected = (
            ROOT / ".github" / "workflows" / "release.yml",
            ROOT / "infra" / "modules" / "source.tf",
            ROOT / "scripts" / "checkout-release.sh",
            ROOT / ".gitmodules",
        )
        for path in expected:
            with self.subTest(path=path):
                self.assertTrue(AUTHORITY.is_operational_source(path))

    def test_governed_repository_id_requires_current_name(self) -> None:
        fake_path = ROOT / "release" / "synthetic-source-lock.json"
        payload = (
            '{"repository_id":1351353723,'
            '"repository":"appolon1908-hue/unapproved-social-fork"}'
        )
        with patch.object(Path, "read_text", return_value=payload):
            with self.assertRaises(SystemExit):
                AUTHORITY.validate_repository_id_current_name_pairing([fake_path])

    def test_known_release_binding_rejects_unapproved_repository(self) -> None:
        release_matrix = ROOT / "release" / "stage6-8-release-matrix.yaml"
        originals = {
            path: path.read_text(encoding="utf-8")
            for path in (
                ROOT / "STAGE6-SOURCE-LOCK.yaml",
                release_matrix,
                ROOT / "config" / "marketing-stage9-readiness.json",
                ROOT
                / "releases"
                / "STAGE6-STAGING-EXACT-SOURCE-LOCK-2026-08-30.json",
                ROOT / "scripts" / "certify_marketing_stage9.py",
            )
        }

        def fake_require(path: Path) -> str:
            text = originals[path]
            if path == release_matrix:
                return text.replace(
                    "appolon1908-hue/Codesrea-Social-",
                    "appolon1908-hue/unapproved-social-fork",
                )
            return text

        with patch.object(AUTHORITY, "require_file", side_effect=fake_require):
            with self.assertRaises(SystemExit):
                AUTHORITY.validate_known_operational_bindings()

    def test_exporter_host_port_publication_is_denied(self) -> None:
        fake_path = ROOT / "deploy" / "compose.yaml"
        payload = (
            "services:\n"
            "  postgres-exporter:\n"
            "    ports:\n"
            "      - '9187:9187'\n"
        )
        with patch.object(Path, "read_text", return_value=payload):
            with self.assertRaises(SystemExit):
                AUTHORITY.validate_postgres_exporter_privacy([fake_path])

    def test_exporter_gateway_route_is_denied(self) -> None:
        fake_path = ROOT / "operations" / "caddy" / "postgres-exporter.caddy"
        payload = "metrics.example.test { reverse_proxy postgres-exporter:9187 }\n"
        with patch.object(Path, "read_text", return_value=payload):
            with self.assertRaises(SystemExit):
                AUTHORITY.validate_postgres_exporter_privacy([fake_path])


if __name__ == "__main__":
    unittest.main()
