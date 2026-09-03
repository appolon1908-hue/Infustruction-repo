#!/usr/bin/env python3
"""Enforce staging -> rollback -> canary sequence and controller receipts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "operations" / "staging-readonly"
WORKFLOW = ROOT / ".github" / "workflows" / "staging-readonly-certification.yml"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    if source.count(old) != 1:
        raise SystemExit(f"{label}: expected one marker, found {source.count(old)}")
    return source.replace(old, new, 1)


def patch_controller() -> None:
    path = OPS / "release_control_v2.py"
    source = path.read_text(encoding="utf-8")

    receipt_marker = '''def _probe_samples(
    url: str, token: str, count: int
) -> tuple[list[float], int]:
'''
    receipt_helpers = '''def validate_canary_receipt(
    payload: Any,
    candidate: Mapping[str, Any],
    candidate_sha256: str,
    requested_percent: float,
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise core.GateError("canary controller did not return a JSON object")
    required = {
        "schema",
        "candidate_id",
        "source_lock_sha",
        "candidate_manifest_sha256",
        "percent",
        "methods",
        "read_only",
        "workloads",
    }
    core.ensure_exact_keys(payload, required, required, "canary controller receipt")
    if payload.get("schema") != "codestra.readonly-canary-receipt.v1":
        raise core.GateError("canary controller receipt schema mismatch")
    if payload.get("candidate_id") != candidate["candidate_id"]:
        raise core.GateError("canary controller receipt candidate mismatch")
    if payload.get("source_lock_sha") != candidate["candidate_source_lock_sha"]:
        raise core.GateError("canary controller receipt source-lock mismatch")
    if payload.get("candidate_manifest_sha256") != candidate_sha256:
        raise core.GateError("canary controller receipt manifest SHA-256 mismatch")
    percent = payload.get("percent")
    if isinstance(percent, bool) or not isinstance(percent, (int, float)):
        raise core.GateError("canary controller receipt percent is invalid")
    if abs(float(percent) - requested_percent) > 0.000001 or float(percent) > 1:
        raise core.GateError("canary controller applied an unexpected percentage")
    if payload.get("methods") != ["GET", "HEAD"] or payload.get("read_only") is not True:
        raise core.GateError("canary controller did not prove GET/HEAD-only read-only mode")
    expected = [
        {
            "service": item["service"],
            "source_sha": item["source_sha"],
            "image": item["image"],
        }
        for item in candidate["workloads"]
    ]
    if payload.get("workloads") != expected:
        raise core.GateError("canary controller receipt workload identities mismatch")
    return dict(payload)


def validate_rollback_receipt(
    payload: Any,
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise core.GateError("canary rollback controller did not return a JSON object")
    required = {"schema", "candidate_id", "source_lock_sha", "rolled_back"}
    core.ensure_exact_keys(payload, required, required, "canary rollback receipt")
    if payload.get("schema") != "codestra.readonly-canary-rollback.v1":
        raise core.GateError("canary rollback receipt schema mismatch")
    if payload.get("candidate_id") != candidate["candidate_id"]:
        raise core.GateError("canary rollback receipt candidate mismatch")
    if payload.get("source_lock_sha") != candidate["candidate_source_lock_sha"]:
        raise core.GateError("canary rollback receipt source-lock mismatch")
    if payload.get("rolled_back") is not True:
        raise core.GateError("canary rollback receipt did not confirm rollback")
    return dict(payload)


def _parse_controller_json(output: bytes, label: str) -> Any:
    if not output or len(output) > 1024 * 1024:
        raise core.GateError(f"{label} output is absent or oversized")
    try:
        return json.loads(output.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise core.GateError(f"{label} output is not one exact JSON document") from exc


def _probe_samples(
    url: str, token: str, count: int
) -> tuple[list[float], int]:
'''
    source = replace_once(
        source,
        receipt_marker,
        receipt_helpers,
        "canary receipt helpers",
    )

    source = replace_once(
        source,
        '''    baseline_latencies, baseline_errors = _probe_samples(
        probe["baseline_url"], bearer, probe["requests"]
    )
    core.run(
''',
        '''    baseline_latencies, baseline_errors = _probe_samples(
        probe["baseline_url"], bearer, probe["requests"]
    )
    if baseline_errors:
        raise core.GateError("baseline monitoring probe failed before canary apply")
    apply_result = core.run(
''',
        "baseline precondition and apply receipt capture",
    )
    source = replace_once(
        source,
        '''        capture=True,
    )
    canary_applied = True
    try:
''',
        '''        capture=True,
    )
    controller_receipt = validate_canary_receipt(
        _parse_controller_json(apply_result.stdout, "canary controller"),
        candidate,
        candidate_sha256,
        requested_percent,
    )
    canary_applied = True
    try:
''',
        "canary receipt verification",
    )
    source = replace_once(
        source,
        '''        total = probe["requests"] * 2
        errors = baseline_errors + canary_errors
        error_rate = (errors / total) * 100.0
''',
        '''        error_rate = (canary_errors / probe["requests"]) * 100.0
''',
        "canary-only error rate",
    )
    source = replace_once(
        source,
        '''                "staging_evidence_run_id": int(
                    os.environ["STAGING_EVIDENCE_RUN_ID"]
                ),
''',
        '''                "staging_evidence_run_id": int(
                    os.environ["STAGING_EVIDENCE_RUN_ID"]
                ),
                "rollback_evidence_run_id": int(
                    os.environ["ROLLBACK_EVIDENCE_RUN_ID"]
                ),
                "controller_receipt": controller_receipt,
''',
        "canary prerequisite and controller evidence",
    )
    source = replace_once(
        source,
        '''            core.run(
                [
                    str(controller),
                    "rollback",
                    "--candidate",
                    candidate["candidate_id"],
                    "--source-lock-sha",
                    candidate["candidate_source_lock_sha"],
                ],
                capture=True,
            )
            evidence.rollback_performed = True
''',
        '''            rollback_result = core.run(
                [
                    str(controller),
                    "rollback",
                    "--candidate",
                    candidate["candidate_id"],
                    "--source-lock-sha",
                    candidate["candidate_source_lock_sha"],
                ],
                capture=True,
            )
            rollback_receipt = validate_rollback_receipt(
                _parse_controller_json(
                    rollback_result.stdout,
                    "canary rollback controller",
                ),
                candidate,
            )
            evidence.measurements["canary_rollback_receipt"] = rollback_receipt
            evidence.rollback_performed = True
''',
        "canary rollback receipt",
    )

    source = replace_once(
        source,
        '''        elif args.mode == "rollback-rehearsal":
            execute_rollback_rehearsal(candidate, manifest, evidence)
        else:
''',
        '''        elif args.mode == "rollback-rehearsal":
            if args.staging_evidence is None:
                raise core.GateError(
                    "rollback rehearsal requires exact staging evidence"
                )
            staging = core.load_json(args.staging_evidence)
            validate_run_evidence(
                staging,
                candidate,
                candidate_sha256,
                expected_mode="staging",
                environment_prefix="STAGING",
                required_gates={
                    "paired-local-off-host-and-restore-verified-backup",
                    "source-digest-readiness-capabilities-metrics-migrations",
                    "keycloak-issuer",
                    "kong-29-route-smoke",
                    "zero-calls-emails-sms",
                },
            )
            evidence.record(
                "exact-successful-staging-prerequisite",
                "PASS",
                run_id=int(os.environ["STAGING_EVIDENCE_RUN_ID"]),
            )
            initial = run_all_checks(candidate, manifest)
            evidence.measurements["initial_candidate_checks"] = initial
            evidence.record("initial-candidate-readback", "PASS")
            execute_rollback_rehearsal(candidate, manifest, evidence)
        else:
''',
        "rollback staging prerequisite",
    )
    path.write_text(source, encoding="utf-8")


def patch_workflow() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    marker = "  rollback-rehearsal:\n"
    next_marker = "  production-readonly-canary:\n"
    if source.count(marker) != 1 or source.count(next_marker) != 1:
        raise SystemExit("rollback workflow boundaries not found")
    prefix, rest = source.split(marker, 1)
    rollback, suffix = rest.split(next_marker, 1)

    rollback = replace_once(
        rollback,
        '      CONFIRM_CANDIDATE_SHA256: ${{ inputs.confirm_candidate_sha256 }}\n',
        '      CONFIRM_CANDIDATE_SHA256: ${{ inputs.confirm_candidate_sha256 }}\n      STAGING_EVIDENCE_RUN_ID: ${{ inputs.staging_evidence_run_id }}\n',
        "rollback staging run input",
    )
    rollback = replace_once(
        rollback,
        '          [[ "${CONFIRM_CANDIDATE_SHA256}" =~ ^[0-9a-f]{64}$ ]]\n',
        '          [[ "${CONFIRM_CANDIDATE_SHA256}" =~ ^[0-9a-f]{64}$ ]]\n          [[ "${STAGING_EVIDENCE_RUN_ID}" =~ ^[1-9][0-9]*$ ]]\n',
        "rollback staging run validation",
    )
    auth_and_download = '''      - name: Authenticate exact successful staging run
        id: staging-run
        env:
          GH_TOKEN: ${{ github.token }}
          STAGING_RUN_ID: ${{ inputs.staging_evidence_run_id }}
        run: |
          set -Eeuo pipefail
          python3 - <<'PY'
          import json
          import os
          import re
          import urllib.request

          run_id = os.environ["STAGING_RUN_ID"]
          repository = os.environ["GITHUB_REPOSITORY"]
          request = urllib.request.Request(
              f"https://api.github.com/repos/{repository}/actions/runs/{run_id}",
              headers={
                  "Accept": "application/vnd.github+json",
                  "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
                  "User-Agent": "codestra-staging-run-verifier/1",
                  "X-GitHub-Api-Version": "2022-11-28",
              },
          )
          with urllib.request.urlopen(request, timeout=30) as response:
              payload = json.load(response)
          if payload.get("id") != int(run_id):
              raise SystemExit("staging run identity mismatch")
          if payload.get("status") != "completed" or payload.get("conclusion") != "success":
              raise SystemExit("staging run is not completed successfully")
          if payload.get("event") != "workflow_dispatch" or payload.get("head_branch") != "main":
              raise SystemExit("staging run is not a protected-main dispatch")
          if payload.get("path") != ".github/workflows/staging-readonly-certification.yml":
              raise SystemExit("staging run workflow path mismatch")
          head_sha = payload.get("head_sha")
          attempt = payload.get("run_attempt")
          if not isinstance(head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", head_sha):
              raise SystemExit("staging run head SHA is invalid")
          if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt <= 0:
              raise SystemExit("staging run attempt is invalid")
          with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
              output.write(f"head_sha={head_sha}\\n")
              output.write(f"run_attempt={attempt}\\n")
          PY
      - name: Download exact successful staging evidence
        uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c
        with:
          github-token: ${{ github.token }}
          run-id: ${{ inputs.staging_evidence_run_id }}
          name: codestra-staging-readonly-${{ inputs.confirm_candidate_id }}
          path: ${{ steps.materialize.outputs.work }}/staging-evidence
      - name: Select one non-symlink staging evidence document
        id: staging-evidence
        run: |
          set -Eeuo pipefail
          mapfile -t files < <(find "${{ steps.materialize.outputs.work }}/staging-evidence" -type f -name '*.json' -print)
          [[ "${#files[@]}" -eq 1 ]] || { echo "Expected exactly one staging evidence JSON" >&2; exit 1; }
          if find "${{ steps.materialize.outputs.work }}/staging-evidence" -type l -print -quit | grep -q .; then
            echo "Staging evidence artifact contains a symbolic link" >&2
            exit 1
          fi
          echo "path=${files[0]}" >> "$GITHUB_OUTPUT"
'''
    login_marker = "      - name: Authenticate to GHCR\n"
    rollback = replace_once(
        rollback,
        login_marker,
        auth_and_download + login_marker,
        "rollback staging evidence steps",
    )
    old_run = '''      - name: Rehearse previous exact release and candidate restoration
        run: |
'''
    new_run = '''      - name: Rehearse previous exact release and candidate restoration
        env:
          STAGING_EVIDENCE_RUN_ATTEMPT: ${{ steps.staging-run.outputs.run_attempt }}
          STAGING_EVIDENCE_HEAD_SHA: ${{ steps.staging-run.outputs.head_sha }}
        run: |
'''
    rollback = replace_once(
        rollback,
        old_run,
        new_run,
        "rollback evidence environment",
    )
    rollback = replace_once(
        rollback,
        '''            --mode rollback-rehearsal \\
            --confirm-candidate-id "$CONFIRM_CANDIDATE_ID" \\
''',
        '''            --mode rollback-rehearsal \\
            --staging-evidence "${{ steps.staging-evidence.outputs.path }}" \\
            --confirm-candidate-id "$CONFIRM_CANDIDATE_ID" \\
''',
        "rollback staging evidence CLI",
    )
    WORKFLOW.write_text(
        prefix + marker + rollback + next_marker + suffix,
        encoding="utf-8",
    )


def patch_tests() -> None:
    path = OPS / "test_release_control_v2.py"
    source = path.read_text(encoding="utf-8")
    marker = '''def test_safe_archive_extraction_rejects_links_and_traversal() -> None:
'''
    tests = '''def test_canary_controller_receipt_binds_percent_methods_and_digests() -> None:
    candidate = valid_candidate()
    digest = "8" * 64
    receipt = {
        "schema": "codestra.readonly-canary-receipt.v1",
        "candidate_id": candidate["candidate_id"],
        "source_lock_sha": candidate["candidate_source_lock_sha"],
        "candidate_manifest_sha256": digest,
        "percent": 1.0,
        "methods": ["GET", "HEAD"],
        "read_only": True,
        "workloads": [
            {
                "service": item["service"],
                "source_sha": item["source_sha"],
                "image": item["image"],
            }
            for item in candidate["workloads"]
        ],
    }
    release.validate_canary_receipt(receipt, candidate, digest, 1.0)
    broken = copy.deepcopy(receipt)
    broken["percent"] = 1.1
    expect_gate_error(
        release.validate_canary_receipt,
        broken,
        candidate,
        digest,
        1.0,
    )
    broken = copy.deepcopy(receipt)
    broken["methods"] = ["GET", "POST"]
    expect_gate_error(
        release.validate_canary_receipt,
        broken,
        candidate,
        digest,
        1.0,
    )


def test_canary_rollback_receipt_is_exact() -> None:
    candidate = valid_candidate()
    receipt = {
        "schema": "codestra.readonly-canary-rollback.v1",
        "candidate_id": candidate["candidate_id"],
        "source_lock_sha": candidate["candidate_source_lock_sha"],
        "rolled_back": True,
    }
    release.validate_rollback_receipt(receipt, candidate)
    receipt["rolled_back"] = False
    expect_gate_error(release.validate_rollback_receipt, receipt, candidate)


def test_safe_archive_extraction_rejects_links_and_traversal() -> None:
'''
    source = replace_once(source, marker, tests, "controller receipt tests")
    path.write_text(source, encoding="utf-8")


def patch_readme() -> None:
    path = OPS / "README.md"
    source = path.read_text(encoding="utf-8")
    addition = '''

## Enforced execution sequence and canary receipt

The rollback-rehearsal dispatch now requires the exact successful staging run
ID. GitHub authenticates that run as a completed successful protected-main
workflow dispatch, downloads its named artifact, and the controller verifies the
candidate ID, source lock, candidate SHA-256, workload source/image identities,
producer run/attempt/head, and every required staging gate before changing the
candidate.

The canary controller must return one JSON document using
`codestra.readonly-canary-receipt.v1`. The receipt must echo the exact candidate,
source lock, candidate SHA-256, applied percentage, `["GET", "HEAD"]`,
`read_only: true`, and every workload's exact source SHA and image digest. A
successful process exit without that receipt is a failure. A rollback command
must likewise return `codestra.readonly-canary-rollback.v1` with
`rolled_back: true`; the attempted rollback is never silently represented as
successful.
'''
    if "## Enforced execution sequence and canary receipt" not in source:
        source += addition
    path.write_text(source, encoding="utf-8")


def main() -> int:
    patch_controller()
    patch_workflow()
    patch_tests()
    patch_readme()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
