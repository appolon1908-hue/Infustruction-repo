#!/usr/bin/env python3
"""Dispatch and bind one protected immutable release stage.

This wrapper never holds runtime credentials. It validates prior wrapper and
child evidence, dispatches the existing protected runtime workflow, waits for
its exact main-SHA run, validates its sanitized evidence, and emits a compact
binding artifact for the portfolio controller.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

REPOSITORY = "appolon1908-hue/Infustruction-repo"
WRAPPER_WORKFLOW = ".github/workflows/portfolio-release-stage.yml"
CHILD_WORKFLOW = ".github/workflows/staging-readonly-certification.yml"
CHILD_WORKFLOW_NAME = "Codestra immutable staging and read-only canary"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
RELEASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
MODES = ("staging", "rollback-rehearsal", "production-readonly-canary")
CHILD_ARTIFACT_PREFIX = {
    "staging": "codestra-staging-readonly-",
    "rollback-rehearsal": "codestra-rollback-rehearsal-",
    "production-readonly-canary": "codestra-production-readonly-canary-",
}
WRAPPER_ARTIFACT_PREFIX = {
    "staging": "portfolio-infrastructure-staging-",
    "rollback-rehearsal": "portfolio-infrastructure-rollback-rehearsal-",
    "production-readonly-canary": "portfolio-infrastructure-production-readonly-canary-",
}


class GateError(RuntimeError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise GateError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class GitHub:
    def __init__(self) -> None:
        token = os.environ.get("GITHUB_TOKEN", "")
        require(bool(token), "GITHUB_TOKEN is required")
        require(os.environ.get("GITHUB_REPOSITORY") == REPOSITORY, "unexpected repository")
        self.token = token
        self.base = "https://api.github.com"

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = path if path.startswith("https://") else self.base + path
        data = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "codestra-portfolio-release-stage/1",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")
            raise GateError(f"GitHub API {method} {path} returned HTTP {error.code}: {body[:500]}") from error
        except urllib.error.URLError as error:
            raise GateError(f"GitHub API {method} {path} failed: {error}") from error

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        return self.request("POST", path, payload)

    def download_artifact(self, artifact_id: int, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "gh",
            "api",
            f"repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip",
        ]
        environment = dict(os.environ)
        environment["GH_TOKEN"] = self.token
        with destination.open("wb") as output:
            result = subprocess.run(command, env=environment, stdout=output, stderr=subprocess.PIPE, check=False)
        if result.returncode != 0:
            destination.unlink(missing_ok=True)
            raise GateError(f"artifact {artifact_id} download failed: {result.stderr.decode('utf-8', 'replace')[:500]}")


def parse_timestamp(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def safe_extract(zip_path: Path, destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=False)
    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        require(len(archive.infolist()) <= 20, "artifact contains too many entries")
        total = sum(item.file_size for item in archive.infolist())
        require(total <= 5 * 1024 * 1024, "artifact exceeds the evidence size limit")
        for item in archive.infolist():
            name = PurePosixPath(item.filename)
            require(not name.is_absolute() and ".." not in name.parts, "artifact path traversal detected")
            mode = item.external_attr >> 16
            require(not stat.S_ISLNK(mode), "artifact symbolic link detected")
            target = destination.joinpath(*name.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            with archive.open(item) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            extracted.append(target)
    return extracted


def exact_artifact(github: GitHub, run_id: int, name: str, work: Path) -> tuple[dict[str, Any], Path]:
    artifacts = github.get(f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100").get("artifacts", [])
    matches = [item for item in artifacts if item.get("name") == name and item.get("expired") is False]
    require(len(matches) == 1, f"run {run_id}: evidence artifact {name!r} missing or ambiguous")
    artifact = matches[0]
    zip_path = work / f"artifact-{artifact['id']}.zip"
    extract_path = work / f"artifact-{artifact['id']}"
    github.download_artifact(int(artifact["id"]), zip_path)
    files = safe_extract(zip_path, extract_path)
    json_files = [path for path in files if path.suffix == ".json"]
    require(len(json_files) >= 1, f"artifact {name!r} has no JSON evidence")
    return artifact, extract_path


def validate_run(github: GitHub, run_id: int, *, workflow_path: str, head_sha: str) -> dict[str, Any]:
    run = github.get(f"/repos/{REPOSITORY}/actions/runs/{run_id}")
    require(run.get("event") == "workflow_dispatch", f"run {run_id}: unexpected event")
    require(run.get("head_branch") == "main", f"run {run_id}: unexpected branch")
    require(run.get("head_sha") == head_sha, f"run {run_id}: exact-head mismatch")
    require(run.get("path") == workflow_path, f"run {run_id}: unexpected workflow path")
    require(run.get("status") == "completed" and run.get("conclusion") == "success", f"run {run_id}: workflow not successful")
    return run


def validate_child_evidence(path: Path, *, mode: str, candidate_id: str, source_lock_sha: str, candidate_sha256: str, child_run: dict[str, Any]) -> dict[str, Any]:
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateError(f"invalid child evidence {path}: {error}") from error
    require(isinstance(evidence, dict), "child evidence must be an object")
    require(evidence.get("candidate_id") == candidate_id, "child evidence candidate ID mismatch")
    require(evidence.get("candidate_source_lock_sha") == source_lock_sha, "child evidence source-lock mismatch")
    require(evidence.get("candidate_manifest_sha256") == candidate_sha256, "child evidence candidate digest mismatch")
    require(evidence.get("mode") == mode, "child evidence mode mismatch")
    require(evidence.get("verdict") == "GO", "child evidence verdict is not GO")
    require(not evidence.get("error"), "child evidence records an error")
    producer = evidence.get("producer")
    require(isinstance(producer, dict), "child producer identity missing")
    require(producer.get("repository") == REPOSITORY, "child producer repository mismatch")
    require(producer.get("workflow") == CHILD_WORKFLOW, "child producer workflow mismatch")
    require(producer.get("head_sha") == child_run.get("head_sha"), "child producer head mismatch")
    require(producer.get("run_id") == child_run.get("id"), "child producer run ID mismatch")
    gates = evidence.get("gates")
    require(isinstance(gates, list) and gates, "child evidence has no gates")
    failed = [gate for gate in gates if isinstance(gate, dict) and gate.get("status") not in {"PASS", "GO", "N/A"}]
    require(not failed, f"child evidence contains non-passing gates: {failed[:3]}")
    if mode == "rollback-rehearsal":
        require(evidence.get("rollback_performed") is True, "rollback evidence does not prove rollback execution")
    return evidence


def one_child_json(extract_path: Path) -> Path:
    matches = [path for path in extract_path.rglob("*.json") if path.is_file() and not path.is_symlink()]
    require(len(matches) == 1, "expected exactly one child evidence JSON")
    return matches[0]


def validate_wrapper_evidence(path: Path, *, mode: str, candidate_id: str, source_lock_sha: str, candidate_sha256: str) -> dict[str, Any]:
    try:
        binding = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateError(f"invalid wrapper evidence {path}: {error}") from error
    require(isinstance(binding, dict), "wrapper binding must be an object")
    require(binding.get("schema_version") == "codestra.portfolio-infrastructure-stage.v1", "wrapper evidence schema mismatch")
    require(binding.get("mode") == mode, "wrapper evidence mode mismatch")
    require(binding.get("candidate_id") == candidate_id, "wrapper evidence candidate ID mismatch")
    require(binding.get("source_lock_sha") == source_lock_sha, "wrapper evidence source-lock mismatch")
    require(binding.get("candidate_sha256") == candidate_sha256, "wrapper evidence candidate digest mismatch")
    require(binding.get("status") == "PASS", "wrapper evidence status is not PASS")
    require(binding.get("external_effects_enabled") is False, "wrapper evidence enables external effects")
    require(isinstance(binding.get("child_run_id"), int) and binding["child_run_id"] > 0, "wrapper child run ID missing")
    return binding


def validate_prior_wrapper(
    github: GitHub,
    work: Path,
    *,
    run_id: int,
    mode: str,
    candidate_id: str,
    source_lock_sha: str,
    candidate_sha256: str,
    head_sha: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    wrapper_run = validate_run(github, run_id, workflow_path=WRAPPER_WORKFLOW, head_sha=head_sha)
    artifact_name = WRAPPER_ARTIFACT_PREFIX[mode] + candidate_id
    wrapper_artifact, extract_path = exact_artifact(github, run_id, artifact_name, work / f"prior-{mode}")
    bindings = [path for path in extract_path.rglob("binding.json") if path.is_file() and not path.is_symlink()]
    require(len(bindings) == 1, f"prior {mode}: expected one binding.json")
    binding = validate_wrapper_evidence(
        bindings[0],
        mode=mode,
        candidate_id=candidate_id,
        source_lock_sha=source_lock_sha,
        candidate_sha256=candidate_sha256,
    )
    child_run_id = int(binding["child_run_id"])
    child_run = validate_run(github, child_run_id, workflow_path=CHILD_WORKFLOW, head_sha=head_sha)
    child_name = CHILD_ARTIFACT_PREFIX[mode] + candidate_id
    _, child_extract = exact_artifact(github, child_run_id, child_name, work / f"prior-{mode}-child")
    child_evidence = validate_child_evidence(
        one_child_json(child_extract),
        mode=mode,
        candidate_id=candidate_id,
        source_lock_sha=source_lock_sha,
        candidate_sha256=candidate_sha256,
        child_run=child_run,
    )
    return wrapper_run, binding, child_evidence


def wait_for_child(github: GitHub, *, started_at: dt.datetime, head_sha: str, timeout_seconds: int) -> dict[str, Any]:
    encoded = urllib.parse.quote(CHILD_WORKFLOW, safe="")
    deadline = time.monotonic() + timeout_seconds
    selected: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        runs = github.get(
            f"/repos/{REPOSITORY}/actions/workflows/{encoded}/runs?event=workflow_dispatch&branch=main&per_page=20"
        ).get("workflow_runs", [])
        candidates = []
        for run in runs:
            created = run.get("created_at")
            if not isinstance(created, str):
                continue
            if parse_timestamp(created) >= started_at and run.get("head_sha") == head_sha:
                candidates.append(run)
        if candidates:
            candidates.sort(key=lambda run: parse_timestamp(run["created_at"]))
            selected = candidates[0]
            break
        time.sleep(5)
    require(selected is not None, "dispatched child run was not observed")
    run_id = int(selected["id"])
    while time.monotonic() < deadline:
        run = github.get(f"/repos/{REPOSITORY}/actions/runs/{run_id}")
        if run.get("status") == "completed":
            require(run.get("conclusion") == "success", f"child run {run_id} concluded {run.get('conclusion')}")
            return run
        time.sleep(10)
    raise GateError(f"child run {run_id} timed out")


def run(arguments: argparse.Namespace) -> dict[str, Any]:
    mode = arguments.mode
    require(mode in MODES, "unsupported mode")
    require(RELEASE_ID.fullmatch(arguments.candidate_id) is not None, "invalid candidate ID")
    require(HEX40.fullmatch(arguments.source_lock_sha) is not None and arguments.source_lock_sha != "0" * 40, "invalid source-lock SHA")
    require(HEX64.fullmatch(arguments.candidate_sha256) is not None and arguments.candidate_sha256 != "0" * 64, "invalid candidate SHA-256")
    require(os.environ.get("GITHUB_REF") == "refs/heads/main", "wrapper must run from main")
    head_sha = os.environ.get("GITHUB_SHA", "")
    require(HEX40.fullmatch(head_sha) is not None, "invalid wrapper head SHA")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == head_sha, "wrapper checkout mismatch")
    require(not subprocess.check_output(["git", "status", "--porcelain"], text=True).strip(), "wrapper workspace is dirty")

    try:
        canary_percent = float(arguments.canary_percent)
    except ValueError as error:
        raise GateError("invalid canary percent") from error
    require(0 < canary_percent <= 1, "canary percent must be greater than zero and no more than one")
    if mode != "production-readonly-canary":
        require(canary_percent == 1, "non-canary stage must retain the default one-percent ceiling")

    work = Path(arguments.work_directory).resolve()
    require(not work.exists(), "work directory already exists")
    work.mkdir(parents=True, mode=0o700)
    github = GitHub()
    branch = github.get(f"/repos/{REPOSITORY}/branches/main")
    require(branch.get("protected") is True, "infrastructure main must be protected")
    require(branch.get("commit", {}).get("sha") == head_sha, "wrapper is not running from current protected main")

    staging_child_run_id = 0
    prior: dict[str, Any] = {}
    if mode in {"rollback-rehearsal", "production-readonly-canary"}:
        require(arguments.staging_run_id.isdigit(), "staging wrapper run ID is required")
        _, staging_binding, _ = validate_prior_wrapper(
            github,
            work,
            run_id=int(arguments.staging_run_id),
            mode="staging",
            candidate_id=arguments.candidate_id,
            source_lock_sha=arguments.source_lock_sha,
            candidate_sha256=arguments.candidate_sha256,
            head_sha=head_sha,
        )
        staging_child_run_id = int(staging_binding["child_run_id"])
        prior["staging_wrapper_run_id"] = int(arguments.staging_run_id)
        prior["staging_child_run_id"] = staging_child_run_id
    if mode == "production-readonly-canary":
        require(arguments.rollback_run_id.isdigit(), "rollback wrapper run ID is required")
        _, rollback_binding, _ = validate_prior_wrapper(
            github,
            work,
            run_id=int(arguments.rollback_run_id),
            mode="rollback-rehearsal",
            candidate_id=arguments.candidate_id,
            source_lock_sha=arguments.source_lock_sha,
            candidate_sha256=arguments.candidate_sha256,
            head_sha=head_sha,
        )
        prior["rollback_wrapper_run_id"] = int(arguments.rollback_run_id)
        prior["rollback_child_run_id"] = int(rollback_binding["child_run_id"])

    inputs = {
        "mode": mode,
        "confirm_candidate_id": arguments.candidate_id,
        "confirm_source_lock_sha": arguments.source_lock_sha,
        "confirm_candidate_sha256": arguments.candidate_sha256,
        "staging_evidence_run_id": str(staging_child_run_id) if staging_child_run_id else "",
        "canary_percent": format(canary_percent, ".15g"),
    }
    started_at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=2)
    github.post(
        f"/repos/{REPOSITORY}/actions/workflows/{urllib.parse.quote(CHILD_WORKFLOW, safe='')}/dispatches",
        {"ref": "main", "inputs": inputs},
    )
    child_run = wait_for_child(
        github,
        started_at=started_at,
        head_sha=head_sha,
        timeout_seconds=arguments.timeout_seconds,
    )
    child_artifact_name = CHILD_ARTIFACT_PREFIX[mode] + arguments.candidate_id
    child_artifact, child_extract = exact_artifact(
        github,
        int(child_run["id"]),
        child_artifact_name,
        work / "child-output",
    )
    child_json = one_child_json(child_extract)
    child_evidence = validate_child_evidence(
        child_json,
        mode=mode,
        candidate_id=arguments.candidate_id,
        source_lock_sha=arguments.source_lock_sha,
        candidate_sha256=arguments.candidate_sha256,
        child_run=child_run,
    )

    output = Path(arguments.output_directory).resolve()
    require(not output.exists(), "output directory already exists")
    output.mkdir(parents=True, mode=0o700)
    shutil.copy2(child_json, output / "child-evidence.json")
    binding = {
        "schema_version": "codestra.portfolio-infrastructure-stage.v1",
        "repository": REPOSITORY,
        "wrapper_workflow": WRAPPER_WORKFLOW,
        "wrapper_run_id": int(os.environ.get("GITHUB_RUN_ID", "0") or "0"),
        "wrapper_run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "0") or "0"),
        "wrapper_head_sha": head_sha,
        "child_workflow": CHILD_WORKFLOW,
        "child_run_id": int(child_run["id"]),
        "child_run_attempt": child_run.get("run_attempt"),
        "child_artifact_id": int(child_artifact["id"]),
        "child_artifact_name": child_artifact_name,
        "child_artifact_digest": child_artifact.get("digest"),
        "child_evidence_sha256": sha256(output / "child-evidence.json"),
        "candidate_id": arguments.candidate_id,
        "source_lock_sha": arguments.source_lock_sha,
        "candidate_sha256": arguments.candidate_sha256,
        "mode": mode,
        "canary_percent": canary_percent if mode == "production-readonly-canary" else 0,
        "prior": prior,
        "status": "PASS",
        "runtime_contacted_by_wrapper": False,
        "production_changed_by_wrapper": False,
        "external_effects_enabled": False,
        "child_verdict": child_evidence["verdict"],
    }
    (output / "binding.json").write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return binding


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--source-lock-sha", required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--staging-run-id", default="")
    parser.add_argument("--rollback-run-id", default="")
    parser.add_argument("--canary-percent", default="1")
    parser.add_argument("--work-directory", required=True)
    parser.add_argument("--output-directory", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=14400)
    return parser


def main() -> int:
    try:
        binding = run(build_parser().parse_args())
    except (GateError, OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(f"portfolio release stage: FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(binding, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
