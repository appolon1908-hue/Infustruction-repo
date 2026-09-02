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


if __name__ == "__main__":
    unittest.main()
