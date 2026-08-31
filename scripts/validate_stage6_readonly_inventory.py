#!/usr/bin/env python3
"""Static fail-closed checks for the Stage 6 read-only inventory workflow."""

from pathlib import Path
import ast
import re


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "stage6-readonly-inventory.yml"
COLLECTOR = ROOT / "scripts" / "collect_stage6_hetzner_inventory.py"
workflow = WORKFLOW.read_text()
collector = COLLECTOR.read_text()


def require(condition: bool, label: str) -> None:
    if not condition:
        raise SystemExit(f"STAGE6_READONLY_INVENTORY_ERROR={label}")


require(re.search(r"(?m)^on:\n  workflow_dispatch:\s*$", workflow) is not None, "dispatch_only")
require("pull_request:" not in workflow and "push:" not in workflow and "schedule:" not in workflow, "automatic_trigger")
require("environment: stage6-infrastructure-provisioning" in workflow, "protected_environment")
require("github.ref_protected" in workflow and "refs/heads/main" in workflow, "protected_main")
require("secrets.HETZNER_CLOUD_TOKEN" in workflow, "token_source")
require("permissions:\n  contents: read" in workflow, "permissions")
require("persist-credentials: false" in workflow, "checkout_credentials")

for target_name, target in (("workflow", workflow), ("collector", collector)):
    require(re.search(r"(?i)\bhcloud\s+(server|network|firewall|ssh-key)\s+(create|update|delete|attach|detach|power|reboot|reset|rebuild)", target) is None, f"hcloud_mutation_{target_name}")
    require(re.search(r"(?i)curl[^\n]*(--request|-X)\s*(POST|PUT|PATCH|DELETE)", target) is None, f"curl_mutation_{target_name}")

tree = ast.parse(collector)
request_methods = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Request":
        method = next((kw.value for kw in node.keywords if kw.arg == "method"), None)
        require(isinstance(method, ast.Constant) and method.value == "GET", "request_not_explicit_get")
        request_methods.append(method.value)
require(request_methods == ["GET"], "request_count")
require('COLLECTIONS = ("locations", "servers", "networks", "ssh_keys", "firewalls")' in collector, "endpoint_allowlist")
require("HETZNER_CLOUD_TOKEN" not in collector.split("print(")[-1], "token_print")
require("STAGE6_TFVARS_JSON" not in workflow, "incomplete_tfvars_write")

print("STAGE6_READONLY_INVENTORY_STATIC=PASS")
print("API_METHODS=GET_ONLY")
print("CLOUD_MUTATION=NO")
print("PRODUCTION_CHANGED=NO")

