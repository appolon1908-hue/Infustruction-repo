#!/usr/bin/env python3
"""Verify the immutable release chain and invoke a fixed production traffic controller."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import portfolio_release_dispatch as stage

SCHEMA = "codestra.production-traffic-promotion.v1"
CONTROLLER_PATH = Path("/usr/local/sbin/codestra-production-traffic-controller")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
RELEASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")


class PromotionError(RuntimeError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise PromotionError(message)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, name: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PromotionError(f"invalid {name}: {error}") from error
    require(isinstance(value, dict), f"{name} must be a JSON object")
    return value


def require_secure_controller(path: Path, expected_sha256: str) -> None:
    require(path == CONTROLLER_PATH, "production traffic controller path is not the fixed authority")
    require(HEX64.fullmatch(expected_sha256) is not None and expected_sha256 != "0" * 64, "invalid controller SHA-256")
    linked = path.lstat()
    require(stat.S_ISREG(linked.st_mode), "production traffic controller is not a regular file")
    require(linked.st_uid == 0, "production traffic controller must be root-owned")
    require(linked.st_nlink == 1, "production traffic controller must have one hard link")
    require(not linked.st_mode & (stat.S_IWGRP | stat.S_IWOTH), "production traffic controller is group/world writable")
    require(file_sha256(path) == expected_sha256, "production traffic controller SHA-256 mismatch")


def parse_completed_at(value: object) -> dt.datetime:
    require(isinstance(value, str), "canary evidence completed_at is missing")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise PromotionError("canary evidence completed_at is invalid") from error
    require(parsed.tzinfo is not None, "canary evidence completed_at must be timezone-aware")
    return parsed.astimezone(dt.timezone.utc)


def validate_candidate_file(path: Path, *, candidate_id: str, source_lock_sha: str, candidate_sha256: str) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), "protected production candidate is missing or unsafe")
    require(file_sha256(path) == candidate_sha256, "protected production candidate SHA-256 mismatch")
    candidate = load_json(path, "protected production candidate")
    require(candidate.get("schema") == "codestra.release-control.v1", "unexpected production candidate schema")
    require(candidate.get("candidate_id") == candidate_id, "protected production candidate ID mismatch")
    require(candidate.get("candidate_source_lock_sha") == source_lock_sha, "protected production source-lock mismatch")
    safety = candidate.get("safety")
    require(isinstance(safety, dict) and safety, "production candidate safety controls are missing")
    for key, value in safety.items():
        if isinstance(value, bool):
            require(value is False, f"production candidate safety control {key} must remain false")
        elif key == "PRODUCTION_DIALING":
            require(value == "DISABLED", "PRODUCTION_DIALING must remain DISABLED")
    workloads = candidate.get("workloads")
    require(isinstance(workloads, list) and workloads, "production candidate has no workloads")
    for workload in workloads:
        require(isinstance(workload, dict), "production candidate workload must be an object")
        require(re.fullmatch(r"[^@\s]+@sha256:[0-9a-f]{64}", str(workload.get("image", ""))) is not None, "production candidate contains a mutable image")
        require(HEX40.fullmatch(str(workload.get("source_sha", ""))) is not None, "production candidate workload source SHA is invalid")
    canary = candidate.get("canary")
    require(isinstance(canary, dict), "production candidate canary policy is missing")
    require(float(canary.get("max_percent", 0)) <= 1, "production candidate canary ceiling exceeds one percent")
    require(canary.get("allowed_methods") == ["GET", "HEAD"], "production candidate canary methods are not GET/HEAD only")
    return candidate


def validate_endpoint_file(path: Path, candidate_id: str) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), "protected production endpoint manifest is missing or unsafe")
    endpoints = load_json(path, "protected production endpoint manifest")
    require(endpoints.get("schema") == "codestra.staging-endpoints.v1", "unexpected production endpoint schema")
    require(endpoints.get("candidate_id") == candidate_id, "production endpoint candidate ID mismatch")
    require(endpoints.get("environment") == "production-readonly-canary", "production endpoint manifest is not the certified canary target")
    routes = endpoints.get("kong", {}).get("smoke_routes")
    require(isinstance(routes, list) and len(routes) == 29, "production endpoint manifest must contain exactly 29 Kong smoke routes")
    return endpoints


def validate_controller_evidence(path: Path, *, candidate_id: str, source_lock_sha: str, candidate_sha256: str, controller_sha256: str) -> dict[str, Any]:
    evidence = load_json(path, "production traffic evidence")
    require(evidence.get("schema_version") == SCHEMA, "production traffic evidence schema mismatch")
    require(evidence.get("candidate_id") == candidate_id, "production traffic candidate ID mismatch")
    require(evidence.get("candidate_source_lock_sha") == source_lock_sha, "production traffic source-lock mismatch")
    require(evidence.get("candidate_manifest_sha256") == candidate_sha256, "production traffic candidate digest mismatch")
    require(evidence.get("controller_sha256") == controller_sha256, "production traffic controller identity mismatch")
    require(evidence.get("previous_traffic_percent") <= 1, "production traffic evidence did not start from the approved canary")
    require(evidence.get("traffic_percent") == 100, "production traffic evidence does not prove 100 percent")
    require(evidence.get("same_candidate") is True, "production traffic evidence reports candidate drift")
    require(evidence.get("source_and_digest_match") is True, "production traffic evidence reports source/digest drift")
    require(evidence.get("readiness") == "PASS", "production readiness did not pass")
    require(evidence.get("monitoring") == "PASS", "production monitoring did not pass")
    require(evidence.get("kong_routes") == "29/29", "production Kong route readback did not pass 29/29")
    require(evidence.get("rollback_controller_verified") is True, "production rollback controller was not verified")
    require(evidence.get("external_effects_enabled") is False, "production traffic evidence enables external effects")
    require(evidence.get("verdict") == "GO", "production traffic promotion verdict is not GO")
    require(not evidence.get("error"), "production traffic evidence contains an error")
    return evidence


def run(arguments: argparse.Namespace) -> dict[str, Any]:
    require(RELEASE_ID.fullmatch(arguments.candidate_id) is not None, "invalid candidate ID")
    require(HEX40.fullmatch(arguments.source_lock_sha) is not None and arguments.source_lock_sha != "0" * 40, "invalid source-lock SHA")
    require(HEX64.fullmatch(arguments.candidate_sha256) is not None and arguments.candidate_sha256 != "0" * 64, "invalid candidate SHA-256")
    require(arguments.staging_run_id.isdigit(), "staging wrapper run ID is required")
    require(arguments.rollback_run_id.isdigit(), "rollback wrapper run ID is required")
    require(arguments.canary_run_id.isdigit(), "canary wrapper run ID is required")
    require(15 <= arguments.observation_minutes <= 180, "observation window must be 15-180 minutes")
    require(arguments.traffic_percent == 100, "final traffic percentage must be exactly 100")
    require(arguments.confirmation == f"PROMOTE {arguments.candidate_id} TO 100 PERCENT", "production confirmation mismatch")
    require(os.environ.get("GITHUB_REPOSITORY") == stage.REPOSITORY, "unexpected repository")
    require(os.environ.get("GITHUB_REF") == "refs/heads/main", "production promotion must run from main")
    head_sha = os.environ.get("GITHUB_SHA", "")
    require(HEX40.fullmatch(head_sha) is not None, "invalid production workflow head SHA")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == head_sha, "production workflow checkout mismatch")
    require(not subprocess.check_output(["git", "status", "--porcelain"], text=True).strip(), "production workflow workspace is dirty")

    candidate_path = Path(arguments.candidate).resolve()
    endpoints_path = Path(arguments.endpoint_manifest).resolve()
    output_path = Path(arguments.evidence).resolve()
    work = Path(arguments.work_directory).resolve()
    require(not work.exists(), "production promotion work directory already exists")
    work.mkdir(parents=True, mode=0o700)
    candidate = validate_candidate_file(
        candidate_path,
        candidate_id=arguments.candidate_id,
        source_lock_sha=arguments.source_lock_sha,
        candidate_sha256=arguments.candidate_sha256,
    )
    validate_endpoint_file(endpoints_path, arguments.candidate_id)

    github = stage.GitHub()
    branch = github.get(f"/repos/{stage.REPOSITORY}/branches/main")
    require(branch.get("protected") is True, "infrastructure main is not protected")
    require(branch.get("commit", {}).get("sha") == head_sha, "production workflow is not current protected main")

    _, staging_binding, _ = stage.validate_prior_wrapper(
        github,
        work,
        run_id=int(arguments.staging_run_id),
        mode="staging",
        candidate_id=arguments.candidate_id,
        source_lock_sha=arguments.source_lock_sha,
        candidate_sha256=arguments.candidate_sha256,
        head_sha=head_sha,
    )
    _, rollback_binding, rollback_evidence = stage.validate_prior_wrapper(
        github,
        work,
        run_id=int(arguments.rollback_run_id),
        mode="rollback-rehearsal",
        candidate_id=arguments.candidate_id,
        source_lock_sha=arguments.source_lock_sha,
        candidate_sha256=arguments.candidate_sha256,
        head_sha=head_sha,
    )
    _, canary_binding, canary_evidence = stage.validate_prior_wrapper(
        github,
        work,
        run_id=int(arguments.canary_run_id),
        mode="production-readonly-canary",
        candidate_id=arguments.candidate_id,
        source_lock_sha=arguments.source_lock_sha,
        candidate_sha256=arguments.candidate_sha256,
        head_sha=head_sha,
    )
    require(rollback_binding.get("prior", {}).get("staging_wrapper_run_id") == int(arguments.staging_run_id), "rollback is not bound to the selected staging run")
    require(canary_binding.get("prior", {}).get("staging_wrapper_run_id") == int(arguments.staging_run_id), "canary is not bound to the selected staging run")
    require(canary_binding.get("prior", {}).get("rollback_wrapper_run_id") == int(arguments.rollback_run_id), "canary is not bound to the selected rollback run")
    require(rollback_evidence.get("rollback_performed") is True, "rollback evidence is incomplete")
    require(0 < float(canary_binding.get("canary_percent", 0)) <= 1, "canary evidence exceeds one percent")

    completed_at = parse_completed_at(canary_evidence.get("completed_at"))
    elapsed = dt.datetime.now(dt.timezone.utc) - completed_at
    require(elapsed >= dt.timedelta(minutes=arguments.observation_minutes), "required canary observation window has not elapsed")

    controller_path = Path(os.environ.get("PRODUCTION_TRAFFIC_CONTROLLER_PATH", ""))
    controller_sha256 = os.environ.get("PRODUCTION_TRAFFIC_CONTROLLER_SHA256", "")
    require_secure_controller(controller_path, controller_sha256)
    canary_copy = work / "canary-evidence.json"
    canary_copy.write_text(json.dumps(canary_evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    canary_copy.chmod(0o600)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "sudo",
        "-n",
        str(controller_path),
        "observe-and-promote",
        "--candidate",
        str(candidate_path),
        "--endpoint-manifest",
        str(endpoints_path),
        "--canary-evidence",
        str(canary_copy),
        "--traffic-percent",
        "100",
        "--controller-sha256",
        controller_sha256,
        "--evidence",
        str(output_path),
    ]
    result = subprocess.run(command, check=False, text=True, capture_output=True, timeout=arguments.controller_timeout_seconds)
    require(result.returncode == 0, f"production traffic controller failed with exit {result.returncode}")
    evidence = validate_controller_evidence(
        output_path,
        candidate_id=arguments.candidate_id,
        source_lock_sha=arguments.source_lock_sha,
        candidate_sha256=arguments.candidate_sha256,
        controller_sha256=controller_sha256,
    )
    evidence["chain"] = {
        "staging_wrapper_run_id": int(arguments.staging_run_id),
        "staging_child_run_id": staging_binding["child_run_id"],
        "rollback_wrapper_run_id": int(arguments.rollback_run_id),
        "rollback_child_run_id": rollback_binding["child_run_id"],
        "canary_wrapper_run_id": int(arguments.canary_run_id),
        "canary_child_run_id": canary_binding["child_run_id"],
        "observation_minutes": arguments.observation_minutes,
    }
    evidence["protected_candidate_workloads"] = len(candidate["workloads"])
    output_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_path.chmod(0o600)
    return evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--source-lock-sha", required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--staging-run-id", required=True)
    parser.add_argument("--rollback-run-id", required=True)
    parser.add_argument("--canary-run-id", required=True)
    parser.add_argument("--observation-minutes", type=int, required=True)
    parser.add_argument("--traffic-percent", type=int, required=True)
    parser.add_argument("--confirmation", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--endpoint-manifest", required=True)
    parser.add_argument("--work-directory", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--controller-timeout-seconds", type=int, default=1800)
    return parser


def main() -> int:
    try:
        evidence = run(build_parser().parse_args())
    except (PromotionError, stage.GateError, OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        print(f"production traffic promotion: FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
