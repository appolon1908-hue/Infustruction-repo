#!/usr/bin/env python3
"""Fail-closed source validation for the reusable offline OCI evidence workflow."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile
from types import ModuleType

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "reusable-observability-offline-oci-evidence.yml"
RENDERER = ROOT / "scripts" / "render-observability-offline-oci-evidence.py"
DOC = ROOT / "docs" / "OBSERVABILITY-OFFLINE-OCI-EVIDENCE.md"

ACTION_PINS = {
    "actions/checkout": "11d5960a326750d5838078e36cf38b85af677262",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
    "docker/setup-buildx-action": "8d2750c68a42422c14e847fe6c8ac0403b4cbd6f",
    "docker/build-push-action": "10e90e3645eae34f1e60eeb005ba3a3d33f178e8",
    "anchore/sbom-action": "e22c389904149dbc22b58101806040fa8d37a610",
    "actions/attest-build-provenance": "977bb373ede98d70efdf65b84cb5f73e068dcc2a",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
}
FORBIDDEN_WORKFLOW_FRAGMENTS = (
    "docker/login-action",
    "packages: write",
    "push: true",
    "push-to-registry: true",
    "network: host",
    "network.host",
    "security.insecure",
    "privileged: true",
    "secret-envs:",
    "secret-files:",
    "secrets:",
    "ssh:",
    "docker push",
    "docker login",
    "kubectl ",
    "helm ",
    "systemctl ",
    "caddy reload",
    "ufw ",
    "nft add",
    "iptables -",
)
REQUIRED_WORKFLOW_FRAGMENTS = (
    "workflow_call:",
    "contents: read",
    "id-token: write",
    "attestations: write",
    "ref: ${{ inputs.source_sha }}",
    "persist-credentials: false",
    "load: true",
    "pull: true",
    "push: false",
    "provenance: false",
    "sbom: false",
    "dependency-snapshot: false",
    "upload-artifact: false",
    "upload-release-assets: false",
    "subject-checksums: evidence/SHA256SUMS",
    "push-to-registry: false",
    "compression-level: 0",
    "registryPushed",
    "packagesPermissionRequired",
    "deploymentAuthorized",
)


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_renderer() -> ModuleType:
    spec = importlib.util.spec_from_file_location("codestra_offline_oci_renderer", RENDERER)
    if spec is None or spec.loader is None:
        fail("unable to load offline OCI evidence renderer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_workflow() -> None:
    if not WORKFLOW.is_file() or WORKFLOW.is_symlink():
        fail("reusable workflow must be a regular non-symlink file")
    text = WORKFLOW.read_text(encoding="utf-8")
    for action, sha in ACTION_PINS.items():
        expected = f"uses: {action}@{sha}"
        if text.count(expected) != 1:
            fail(f"workflow must use exactly one pinned {action} action")
    for fragment in FORBIDDEN_WORKFLOW_FRAGMENTS:
        if fragment in text:
            fail(f"workflow contains forbidden publishing or deployment capability: {fragment}")
    for fragment in REQUIRED_WORKFLOW_FRAGMENTS:
        if fragment not in text:
            fail(f"workflow is missing required offline evidence behavior: {fragment}")
    if "packages:" in text:
        fail("workflow may not request any packages permission")
    if text.count("github_attestation:") != 1 or "default: false" not in text:
        fail("GitHub attestation must remain an explicit opt-in")
    if text.count("retention-days: ${{ inputs.retention_days }}") != 1:
        fail("artifact retention must remain caller-controlled within GitHub policy")


def validate_renderer() -> None:
    if not RENDERER.is_file() or RENDERER.is_symlink():
        fail("renderer must be a regular non-symlink file")
    text = RENDERER.read_text(encoding="utf-8")
    for fragment in (
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http.client",
        "os.system",
        "exec(",
        "eval(",
    ):
        if fragment in text:
            fail(f"renderer may not execute commands or perform network access: {fragment}")
    for fragment in (
        '"registryPush": False',
        '"runtimeDeployment": False',
        '"registryPushed": False',
        '"packagesPermissionRequired": False',
        '"registryLoginPerformed": False',
        '"registryPushPerformed": False',
        '"imagePublished": False',
        '"serverChanged": False',
        '"deploymentAuthorized": False',
        '"productionAuthorized": False',
        "configuration_checksum",
        "validate_build_args",
        "os.O_EXCL",
        "0o600",
    ):
        if fragment not in text:
            fail(f"renderer is missing required evidence or safety behavior: {fragment}")

    module = load_renderer()
    safe_args = "\n".join(
        (
            "GO_BUILDER_IMAGE=golang:1.26@sha256:" + "0" * 64,
            "RUNTIME_IMAGE=gcr.io/distroless/static-debian12:nonroot@sha256:" + "1" * 64,
            "BUILD_MODE=offline-evidence",
        )
    )
    if module.validate_build_args(safe_args) != ["GO_BUILDER_IMAGE", "RUNTIME_IMAGE", "BUILD_MODE"]:
        fail("renderer did not preserve validated build argument order")
    unsafe_args = (
        "PASSWORD=unsafe",
        "API_TOKEN=unsafe",
        "BASE_IMAGE=alpine:latest",
        "BASE_IMAGE=alpine:3.22",
        "VALUE=${{ secrets.VALUE }}",
        "DUPLICATE=one\nDUPLICATE=two",
    )
    for sample in unsafe_args:
        try:
            module.validate_build_args(sample)
        except module.EvidenceError:
            continue
        fail(f"unsafe build argument unexpectedly passed: {sample}")

    with tempfile.TemporaryDirectory() as temporary:
        repository = pathlib.Path(temporary)
        (repository / "context").mkdir()
        (repository / "context" / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
        (repository / "config").mkdir()
        (repository / "config" / "runtime.json").write_text('{"enabled":false}\n', encoding="utf-8")
        context = module.existing_path(repository, "context", label="context", directory=True)
        dockerfile = module.existing_path(
            repository,
            "context/Dockerfile",
            label="dockerfile",
            directory=False,
        )
        if not context.is_dir() or not dockerfile.is_file():
            fail("safe repository-relative build paths were not accepted")
        roots = module.configuration_roots(repository, "context/Dockerfile\nconfig")
        checksum, files = module.configuration_checksum(repository, roots)
        if not module.DIGEST.fullmatch(checksum) or files != ["config/runtime.json", "context/Dockerfile"]:
            fail("configuration checksum is not deterministic")
        (repository / "escape").symlink_to(pathlib.Path("/tmp"))
        try:
            module.configuration_roots(repository, "escape")
        except module.EvidenceError:
            pass
        else:
            fail("configuration symlink escape unexpectedly passed")


def validate_docs() -> None:
    if not DOC.is_file() or DOC.is_symlink():
        fail("offline OCI evidence documentation is missing")
    text = DOC.read_text(encoding="utf-8")
    for phrase in (
        "No registry login or push",
        "exact 40-character source SHA",
        "digest-pinned image build arguments",
        "SPDX JSON SBOM",
        "SLSA-compatible provenance",
        "configuration checksum",
        "optional GitHub attestation",
        "does not authorize deployment",
    ):
        if phrase not in text:
            fail(f"offline OCI evidence documentation is missing: {phrase}")


def main() -> int:
    validate_workflow()
    validate_renderer()
    validate_docs()
    print("OFFLINE_OCI_ACTION_PIN_COUNT=7")
    print("REGISTRY_LOGIN_CAPABILITY=ABSENT")
    print("REGISTRY_PUSH_CAPABILITY=ABSENT")
    print("PACKAGES_WRITE_PERMISSION=ABSENT")
    print("DEPLOYMENT_CAPABILITY=ABSENT")
    print("OFFLINE_OCI_WORKFLOW_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"OFFLINE_OCI_WORKFLOW_ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
