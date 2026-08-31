#!/usr/bin/env python3
"""Verify every locked repository SHA is still the live authoritative main head."""

from __future__ import annotations

import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "STAGE6-SOURCE-LOCK.yaml"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def authority_head(component: str, definition: dict) -> tuple[str, str, str]:
    repository = definition["repository"]
    expected = definition["revision"]
    url = f"https://github.com/{repository}.git"
    completed = subprocess.run(
        ["git", "ls-remote", "--refs", url, "refs/heads/main"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=45,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit {completed.returncode}"
        raise RuntimeError(f"{component}: cannot query {url}: {detail}")
    rows = [line.split() for line in completed.stdout.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != "refs/heads/main":
        raise RuntimeError(
            f"{component}: expected exactly one refs/heads/main result, got {rows!r}"
        )
    observed = rows[0][0]
    if not FULL_SHA.fullmatch(observed):
        raise RuntimeError(f"{component}: invalid authoritative SHA {observed!r}")
    if observed != expected:
        raise RuntimeError(
            f"{component}: DRIFT locked={expected} authoritative_main={observed}"
        )
    return component, repository, observed


def main() -> None:
    repositories = yaml.safe_load(LOCK.read_text())["repositories"]
    results: list[tuple[str, str, str]] = []
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=min(8, len(repositories))) as executor:
        futures = {
            executor.submit(authority_head, component, definition): component
            for component, definition in repositories.items()
        }
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:  # Report every repository failure in one run.
                failures.append(str(exc))

    for component, repository, observed in sorted(results):
        print(f"AUTHORITY_HEAD component={component} repository={repository} sha={observed}")
    if failures:
        raise SystemExit("\n".join(sorted(failures)))
    required = len(repositories)
    if len(results) != required:
        raise SystemExit(f"AUTHORITY_HEADS={len(results)}/{required}")
    print(f"AUTHORITY_HEADS={required}/{required}")


if __name__ == "__main__":
    main()
