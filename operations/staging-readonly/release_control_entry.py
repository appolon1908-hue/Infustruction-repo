#!/usr/bin/env python3
"""Hardened entry point for release_control.

The core controller intentionally uses one deployment function for candidate and
rollback overrides. This entry point permits only the two complete immutable
image sets declared in the candidate and rejects every partial, mixed, mutable,
or unlisted rendered image set.
"""

from __future__ import annotations

from pathlib import Path

import release_control as controller


def verify_candidate_or_previous_images(candidate, override: Path) -> None:
    working = Path(candidate["compose"]["working_directory"])
    rendered = controller.run(
        controller.compose_command(candidate, override, "config", "--images"),
        cwd=working,
    ).stdout.decode("utf-8", errors="strict").splitlines()
    actual = sorted(line.strip() for line in rendered if line.strip())
    candidate_images = sorted(item["image"] for item in candidate["workloads"])
    previous_images = sorted(item["image"] for item in candidate["rollback"]["workloads"])
    if actual not in (candidate_images, previous_images):
        raise controller.GateError(
            "rendered Compose images are not the complete candidate or previous "
            f"immutable set: {actual}"
        )


controller.verify_compose_images = verify_candidate_or_previous_images


if __name__ == "__main__":
    raise SystemExit(controller.main())
