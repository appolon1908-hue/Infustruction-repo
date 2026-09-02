from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mission_validator",
    ROOT / "scripts/validate_observability_repository_first_mission.py",
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class MissionValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = VALIDATOR.MISSION.read_text(encoding="utf-8")

    def test_committed_authority_passes(self) -> None:
        VALIDATOR.validate(self.source)

    def test_server_install_authorization_is_rejected_with_any_line_suffix(self) -> None:
        variants = (
            "SERVER_INSTALL_AUTHORIZED=YES",
            "SERVER_INSTALL_AUTHORIZED=YES\n",
            "SERVER_INSTALL_AUTHORIZED=YES  \n",
            "SERVER_INSTALL_AUTHORIZED=YES\r\n",
        )
        for marker in variants:
            with self.subTest(marker=repr(marker)):
                with self.assertRaisesRegex(ValueError, "activation claim"):
                    VALIDATOR.validate(self.source + "\n" + marker)


if __name__ == "__main__":
    unittest.main()
