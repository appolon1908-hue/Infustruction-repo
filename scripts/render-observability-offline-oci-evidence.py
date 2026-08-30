#!/usr/bin/env python3
"""Validate inputs and render evidence for a local-only OCI image build."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
from typing import Any, Iterable

SHA40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
COMPONENT = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
ARG_KEY = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
SENSITIVE_KEY_PARTS = (
    "PASSWORD",
    "PASSWD",
    "SECRET",
    "TOKEN",
    "PRIVATE_KEY",
    "CREDENTIAL",
    "API_KEY",
    "CLIENT_SECRET",
    "AUTHORIZATION",
    "COOKIE",
    "DATABASE_URL",
    "DSN",
)
FORBIDDEN_VALUE_FRAGMENTS = (
    "${{",
    ":latest",
    "-----BEGIN",
    "AKIA",
)


class EvidenceError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise EvidenceError(message)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_relative(value: str, *, label: str) -> pathlib.PurePosixPath:
    if not value or value != value.strip() or "\x00" in value or "\\" in value:
        fail(f"{label} must be a normalized non-empty POSIX relative path")
    path = pathlib.PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        fail(f"{label} may not be absolute or contain dot traversal")
    return path


def existing_path(root: pathlib.Path, value: str, *, label: str, directory: bool) -> pathlib.Path:
    relative = safe_relative(value, label=label)
    candidate = root.joinpath(*relative.parts)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        fail(f"{label} must resolve inside the repository: {exc}")
    if candidate.is_symlink():
        fail(f"{label} may not be a symlink")
    if directory and not resolved.is_dir():
        fail(f"{label} must be a directory")
    if not directory and not resolved.is_file():
        fail(f"{label} must be a regular file")
    return resolved


def nonempty_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def validate_build_args(value: str) -> list[str]:
    lines = nonempty_lines(value)
    if len(lines) > 50:
        fail("build_args may contain at most 50 assignments")
    keys: list[str] = []
    for line in lines:
        if len(line) > 4096 or "=" not in line:
            fail("each build_args line must be KEY=VALUE and at most 4096 characters")
        key, item = line.split("=", 1)
        if not ARG_KEY.fullmatch(key):
            fail(f"invalid build argument key: {key!r}")
        if any(part in key for part in SENSITIVE_KEY_PARTS):
            fail(f"secret-shaped build argument key is forbidden: {key}")
        if not item or any(ord(char) < 32 for char in item):
            fail(f"build argument {key} has an empty or control-character value")
        if any(fragment in item for fragment in FORBIDDEN_VALUE_FRAGMENTS):
            fail(f"build argument {key} contains a forbidden mutable or secret-shaped value")
        if "IMAGE" in key and "@sha256:" not in item:
            fail(f"image build argument {key} must use an immutable sha256 digest")
        keys.append(key)
    if len(keys) != len(set(keys)):
        fail("build_args contains duplicate keys")
    return keys


def configuration_roots(repository: pathlib.Path, value: str) -> list[pathlib.Path]:
    lines = nonempty_lines(value)
    if not lines:
        fail("configuration_paths must identify at least one file or directory")
    if len(lines) > 100:
        fail("configuration_paths may contain at most 100 entries")
    paths: list[pathlib.Path] = []
    for index, line in enumerate(lines, start=1):
        relative = safe_relative(line, label=f"configuration_paths[{index}]")
        candidate = repository.joinpath(*relative.parts)
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(repository.resolve(strict=True))
        except (OSError, ValueError) as exc:
            fail(f"configuration path must resolve inside the repository: {line}: {exc}")
        if candidate.is_symlink():
            fail(f"configuration path may not be a symlink: {line}")
        if not resolved.is_file() and not resolved.is_dir():
            fail(f"configuration path must be a regular file or directory: {line}")
        paths.append(resolved)
    return paths


def iter_configuration_files(repository: pathlib.Path, roots: Iterable[pathlib.Path]) -> Iterable[pathlib.Path]:
    seen: set[pathlib.Path] = set()
    repository = repository.resolve(strict=True)
    for root in roots:
        candidates = [root] if root.is_file() else sorted(root.rglob("*"))
        for candidate in candidates:
            if candidate.is_symlink():
                fail(f"configuration tree contains a symlink: {candidate.relative_to(repository)}")
            if not candidate.is_file():
                continue
            relative = candidate.resolve(strict=True).relative_to(repository)
            if ".git" in relative.parts or "__pycache__" in relative.parts or candidate.suffix == ".pyc":
                continue
            if relative in seen:
                continue
            seen.add(relative)
            yield candidate.resolve(strict=True)


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def configuration_checksum(repository: pathlib.Path, roots: Iterable[pathlib.Path]) -> tuple[str, list[str]]:
    repository = repository.resolve(strict=True)
    digest = hashlib.sha256()
    files: list[str] = []
    for path in sorted(iter_configuration_files(repository, roots), key=lambda item: str(item.relative_to(repository))):
        relative = path.relative_to(repository).as_posix()
        data = path.read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(hashlib.sha256(data).digest())
        digest.update(b"\x00")
        files.append(relative)
    if not files:
        fail("configuration_paths did not select any regular files")
    return f"sha256:{digest.hexdigest()}", files


def atomic_write(path: pathlib.Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists() or temporary.is_symlink():
        temporary.unlink()
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def validate_command(args: argparse.Namespace) -> int:
    repository = pathlib.Path(args.repository).resolve(strict=True)
    if not COMPONENT.fullmatch(args.component):
        fail("component must use lowercase letters, numbers, and hyphens")
    if not SHA40.fullmatch(args.source_sha):
        fail("source_sha must be a full lowercase Git SHA")
    if args.github_sha != args.source_sha:
        fail("workflow source SHA does not match the requested exact source")
    if args.platform != "linux/amd64":
        fail("the V1 offline evidence workflow permits only linux/amd64")
    existing_path(repository, args.context, label="context", directory=True)
    existing_path(repository, args.dockerfile, label="dockerfile", directory=False)
    if args.target and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", args.target):
        fail("target contains unsupported characters")
    keys = validate_build_args(args.build_args)
    configuration_roots(repository, args.configuration_paths)
    print(f"OFFLINE_BUILD_COMPONENT={args.component}")
    print(f"OFFLINE_BUILD_SOURCE_SHA={args.source_sha}")
    print(f"OFFLINE_BUILD_ARGUMENT_KEYS={','.join(keys)}")
    print("OFFLINE_BUILD_INPUT_VALIDATION=PASS")
    return 0


def render_command(args: argparse.Namespace) -> int:
    repository = pathlib.Path(args.repository).resolve(strict=True)
    output = pathlib.Path(args.output_dir).resolve(strict=True)
    archive = pathlib.Path(args.image_archive).resolve(strict=True)
    sbom = pathlib.Path(args.sbom).resolve(strict=True)
    image_inspect = pathlib.Path(args.image_inspect).resolve(strict=True)
    for label, path in (("image archive", archive), ("SBOM", sbom), ("image inspection", image_inspect)):
        if path.is_symlink() or not path.is_file():
            fail(f"{label} must be a regular non-symlink file")

    image_digest = args.image_digest.strip()
    build_metadata_raw = args.build_metadata.strip()
    try:
        build_metadata: Any = json.loads(build_metadata_raw) if build_metadata_raw else {}
    except json.JSONDecodeError as exc:
        fail(f"Buildx metadata is invalid JSON: {exc}")
    if not image_digest and isinstance(build_metadata, dict):
        image_digest = str(build_metadata.get("containerimage.digest", ""))
    if not DIGEST.fullmatch(image_digest):
        fail("Buildx must return a full sha256 image digest")

    build_arg_keys = validate_build_args(args.build_args)
    roots = configuration_roots(repository, args.configuration_paths)
    config_digest, config_files = configuration_checksum(repository, roots)

    metadata_path = output / "buildx-metadata.json"
    atomic_write(metadata_path, (json.dumps(build_metadata, indent=2, sort_keys=True) + "\n").encode("utf-8"))

    generated_at = utc_now()
    provenance = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": args.local_image, "digest": {"sha256": image_digest.split(":", 1)[1]}}],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://codestra.media/observability/offline-oci-evidence/v1",
                "externalParameters": {
                    "component": args.component,
                    "context": args.context,
                    "dockerfile": args.dockerfile,
                    "target": args.target or None,
                    "platform": args.platform,
                    "buildArgumentKeys": build_arg_keys,
                    "configurationPaths": nonempty_lines(args.configuration_paths),
                },
                "internalParameters": {
                    "networkMode": "default-build-network-only",
                    "registryPush": False,
                    "runtimeDeployment": False,
                },
                "resolvedDependencies": [
                    {
                        "uri": f"git+https://github.com/{args.github_repository}@{args.source_sha}",
                        "digest": {"gitCommit": args.source_sha},
                    }
                ],
            },
            "runDetails": {
                "builder": {
                    "id": f"https://github.com/{args.github_repository}/actions/runs/{args.github_run_id}/attempts/{args.github_run_attempt}"
                },
                "metadata": {
                    "invocationId": f"{args.github_run_id}-{args.github_run_attempt}",
                    "startedOn": args.build_started_at,
                    "finishedOn": generated_at,
                },
            },
        },
    }
    provenance_path = output / "provenance.slsa.json"
    atomic_write(provenance_path, (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode("utf-8"))

    evidence = {
        "schemaVersion": "1.0",
        "evidenceType": "codestra-observability-offline-oci-build",
        "generatedAt": generated_at,
        "component": args.component,
        "source": {
            "repository": args.github_repository,
            "sha": args.source_sha,
            "ref": args.github_ref,
            "workflowRef": args.github_workflow_ref,
            "runId": args.github_run_id,
            "runAttempt": args.github_run_attempt,
        },
        "build": {
            "context": args.context,
            "dockerfile": args.dockerfile,
            "target": args.target or None,
            "platform": args.platform,
            "buildArgumentKeys": build_arg_keys,
            "localImage": args.local_image,
            "imageDigest": image_digest,
            "registryPushed": False,
            "packagesPermissionRequired": False,
        },
        "artifacts": {
            "imageArchive": {"name": archive.name, "sha256": sha256_file(archive), "size": archive.stat().st_size},
            "sbom": {"name": sbom.name, "format": "spdx-json", "sha256": sha256_file(sbom), "size": sbom.stat().st_size},
            "provenance": {"name": provenance_path.name, "sha256": sha256_file(provenance_path), "size": provenance_path.stat().st_size},
            "buildxMetadata": {"name": metadata_path.name, "sha256": sha256_file(metadata_path), "size": metadata_path.stat().st_size},
            "imageInspection": {"name": image_inspect.name, "sha256": sha256_file(image_inspect), "size": image_inspect.stat().st_size},
            "configurationChecksum": config_digest,
            "configurationFiles": config_files,
        },
        "safety": {
            "registryLoginPerformed": False,
            "registryPushPerformed": False,
            "imagePublished": False,
            "serverChanged": False,
            "serviceStartedOnTarget": False,
            "deploymentAuthorized": False,
            "productionAuthorized": False,
        },
    }
    evidence_path = output / "evidence.json"
    atomic_write(evidence_path, (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8"))

    subjects = sorted(
        [archive, sbom, provenance_path, metadata_path, image_inspect, evidence_path],
        key=lambda path: path.name,
    )
    checksum_lines = [f"{sha256_file(path).split(':', 1)[1]}  {path.name}" for path in subjects]
    checksums_path = output / "SHA256SUMS"
    atomic_write(checksums_path, ("\n".join(checksum_lines) + "\n").encode("utf-8"))

    print(f"OFFLINE_IMAGE_DIGEST={image_digest}")
    print(f"OFFLINE_CONFIGURATION_CHECKSUM={config_digest}")
    print(f"OFFLINE_EVIDENCE_SHA256={sha256_file(evidence_path)}")
    print(f"OFFLINE_PROVENANCE_SHA256={sha256_file(provenance_path)}")
    print(f"OFFLINE_SBOM_SHA256={sha256_file(sbom)}")
    print("OFFLINE_REGISTRY_PUSHED=NO")
    print("OFFLINE_DEPLOYMENT_AUTHORIZED=NO")
    print("OFFLINE_OCI_EVIDENCE_RENDER=PASS")
    return 0


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    subparsers = value.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--repository", default=".")
    validate.add_argument("--component", required=True)
    validate.add_argument("--source-sha", required=True)
    validate.add_argument("--github-sha", required=True)
    validate.add_argument("--context", required=True)
    validate.add_argument("--dockerfile", required=True)
    validate.add_argument("--target", default="")
    validate.add_argument("--platform", required=True)
    validate.add_argument("--build-args", default="")
    validate.add_argument("--configuration-paths", required=True)
    validate.set_defaults(handler=validate_command)

    render = subparsers.add_parser("render")
    render.add_argument("--repository", default=".")
    render.add_argument("--output-dir", required=True)
    render.add_argument("--component", required=True)
    render.add_argument("--source-sha", required=True)
    render.add_argument("--context", required=True)
    render.add_argument("--dockerfile", required=True)
    render.add_argument("--target", default="")
    render.add_argument("--platform", required=True)
    render.add_argument("--build-args", default="")
    render.add_argument("--configuration-paths", required=True)
    render.add_argument("--local-image", required=True)
    render.add_argument("--image-digest", default="")
    render.add_argument("--build-metadata", default="{}")
    render.add_argument("--image-archive", required=True)
    render.add_argument("--sbom", required=True)
    render.add_argument("--image-inspect", required=True)
    render.add_argument("--github-repository", required=True)
    render.add_argument("--github-ref", required=True)
    render.add_argument("--github-workflow-ref", required=True)
    render.add_argument("--github-run-id", required=True)
    render.add_argument("--github-run-attempt", required=True)
    render.add_argument("--build-started-at", required=True)
    render.set_defaults(handler=render_command)
    return value


def main() -> int:
    args = parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EvidenceError as exc:
        print(f"OFFLINE_OCI_EVIDENCE_ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
