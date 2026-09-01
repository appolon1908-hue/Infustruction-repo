#!/usr/bin/env python3
import pathlib
import re
import yaml

path = pathlib.Path("PRODUCTION-SOURCE-AUTHORITY-MATRIX.yaml")
data = yaml.safe_load(path.read_text())
workloads = data["workloads"]
assert len(workloads) == 23
statuses = {"PROVEN", "AMBIGUOUS", "SOURCE_AUTHORITY_ABSENT", "VENDOR_ONLY", "DIVERGENT", "INVALID_REVISION_METADATA"}
remediations = set("ABCDEF")
expected = {"PROVEN": 2, "AMBIGUOUS": 5, "SOURCE_AUTHORITY_ABSENT": 8, "VENDOR_ONLY": 4, "DIVERGENT": 2, "INVALID_REVISION_METADATA": 2}
actual = {status: 0 for status in statuses}
for name, item in workloads.items():
    assert item["status"] in statuses, name
    assert item["remediation_type"] in remediations, name
    actual[item["status"]] += 1
    sha = str(item.get("source_sha", "UNKNOWN"))
    assert sha == "UNKNOWN" or re.fullmatch(r"[0-9a-f]{40}", sha), (name, sha)
    if item["status"] == "PROVEN":
        for field in ("runtime_image", "runtime_image_id", "compose_file", "build_context", "dockerfile", "repository", "protected_branch", "source_sha"):
            assert item.get(field) not in (None, "", "UNKNOWN"), (name, field)
        assert re.fullmatch(r"[0-9a-f]{40}", item["source_sha"])
assert actual == expected, (actual, expected)
assert data["acceptance_rule"] == "runtime_to_compose_to_build_context_to_dockerfile_to_protected_git_exact_sha"
print("SOURCE_AUTHORITY_MATRIX=PASS")
