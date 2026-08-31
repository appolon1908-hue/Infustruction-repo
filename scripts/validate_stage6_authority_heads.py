#!/usr/bin/env python3
"""Verify every locked repository SHA is still the live authoritative main head."""

from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "STAGE6-SOURCE-LOCK.yaml"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def authority_head(component: str, definition: dict) -> tuple[str, str, str]:
    repository = definition["repository"]
    expected = definition["revision"]
    url = f"https://api.github.com/repos/{repository}/git/ref/heads/main"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "codestra-stage6-authority-head-validator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("STAGE6_SOURCE_READ_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=45) as response:
            payload = json.load(response)
    except HTTPError as exc:
        hint = (
            "; private repositories require a trusted non-PR-controlled "
            "read-only credential boundary"
            if exc.code in {401, 403, 404}
            else ""
        )
        raise RuntimeError(
            f"{component}: cannot query {repository} main: HTTP {exc.code}{hint}"
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{component}: cannot query {repository} main: {exc}") from exc
    if payload.get("ref") != "refs/heads/main":
        raise RuntimeError(f"{component}: unexpected ref response {payload.get('ref')!r}")
    observed = (payload.get("object") or {}).get("sha", "")
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
