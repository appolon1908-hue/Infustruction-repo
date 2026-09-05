"""Exercise the actual workflow shell with a fake Docker binary; no builds/deploys."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/reusable-codestra-deploy-readiness.yml"
DOCUMENT = yaml.safe_load(WORKFLOW.read_text())


def build_script(job, name):
    step = next(s for s in DOCUMENT["jobs"][job]["steps"] if s.get("name") == name)
    script = step["run"]
    if job == "immutable-candidate":
        script = script.split('  "$RUNNER_TEMP/trivy" image', 1)[0] + "\nfi\n"
    return script.replace("${{ github.event.pull_request.head.sha || github.sha }}", "${GITHUB_SHA}")


SCRIPTS = {
    "immutable-candidate": build_script("immutable-candidate", "Build once, scan, publish, sign, and attest"),
}


class BuildContextTest(unittest.TestCase):
    def run_fixture(self, job, context=".", dockerfile="vicidial/docker/Dockerfile"):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            root = parent / "checkout"
            root.mkdir()
            nested = root / "vicidial/docker"
            nested.mkdir(parents=True)
            (nested / "Dockerfile").write_text("FROM scratch\nCOPY vicidial /vicidial\n")
            (root / "escape").symlink_to(parent, target_is_directory=True)
            environment = os.environ | {
                "GIT_AUTHOR_NAME": "Synthetic", "GIT_AUTHOR_EMAIL": "test@example.invalid",
                "GIT_COMMITTER_NAME": "Synthetic", "GIT_COMMITTER_EMAIL": "test@example.invalid",
            }
            for args in (["init", "-q"], ["add", "."], ["commit", "-qm", "fixture"]):
                subprocess.run(["git", *args], cwd=root, env=environment, check=True,
                               capture_output=True)
            sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            date = subprocess.check_output(["git", "show", "-s", "--format=%cI", "HEAD"], cwd=root, text=True).strip()
            binary = parent / "docker"
            binary.write_text(f"#!{sys.executable}\nimport json,os,sys\nfrom pathlib import Path\nPath(os.environ['CAPTURE']).write_text(json.dumps(sys.argv[1:]))\n")
            binary.chmod(0o755)
            capture = parent / "captured.json"
            environment.update({
                "PATH": str(parent) + os.pathsep + os.environ["PATH"],
                "CONFIGURED_DOCKERFILE": dockerfile, "CONFIGURED_BUILD_CONTEXT": context,
                "GITHUB_SHA": sha, "GITHUB_REPOSITORY": "synthetic/repo",
                "GITHUB_RUN_ID": "1", "GITHUB_RUN_ATTEMPT": "1",
                "ARTIFACT_STRATEGY": "oci", "REPOSITORY_CLASS": "service",
                "CAPTURE": str(capture),
            })
            result = subprocess.run(["bash", "-c", SCRIPTS[job]], cwd=root,
                                    env=environment, text=True, capture_output=True)
            args = json.loads(capture.read_text()) if capture.exists() else None
            return result, args, str(root), sha, date

    def test_repository_root_context_and_immutable_build_metadata(self):
        for job in SCRIPTS:
            with self.subTest(job=job):
                result, args, root, sha, date = self.run_fixture(job)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(args[-1], ".")
                self.assertEqual(args[args.index("-f") + 1], "vicidial/docker/Dockerfile")
                self.assertIn("SOURCE_SHA=" + sha, args)
                self.assertIn("BUILD_DATE=" + date, args)

    def test_legacy_default_preserved(self):
        for job in SCRIPTS:
            result, args, root, _, _ = self.run_fixture(job, context="", dockerfile="")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(args[-1], "vicidial/docker")

    def test_invalid_and_escaping_paths_never_build(self):
        for job in SCRIPTS:
            for context in ("../", "escape", "missing", "https://example.invalid/repo", "$(touch unexpected)"):
                with self.subTest(job=job, context=context):
                    result, args, _, _, _ = self.run_fixture(job, context=context)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIsNone(args)
            result, args, _, _, _ = self.run_fixture(job, dockerfile="missing/Dockerfile")
            self.assertNotEqual(result.returncode, 0)
            self.assertIsNone(args)


if __name__ == "__main__":
    unittest.main()
