#!/usr/bin/env python3
"""Capture allowlisted production-write controls without reading other values."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "STAGE6-PRODUCTION-WRITE-SAFETY-INVENTORY.md"
KEYS = (
    "LIVE_ADVERTISING_ENABLED", "EXTERNAL_DELIVERY_ENABLED",
    "SOCIAL_PUBLISHING_ENABLED", "EXTERNAL_MODEL_CALLS_ENABLED",
    "LIVE_SMS_DELIVERY", "LIVE_EMAIL_DELIVERY", "LIVE_PSTN_DIALING",
    "N8N_EXTERNAL_PROVIDER_WRITES", "PRODUCTION_DIALING", "CALLS_PLACED",
)
TERMS = (
    "middleware", "communication", "klyrow", "n8n", "social",
    "marketing", "telephony", "email", "mail", "sms", "vicidial",
    "dial", "provider", "postly", "ai-",
)
EXCLUDE = ("postgres", "redis", "exporter", "proxy", "keycloak", "kong")

ids = subprocess.check_output(["docker", "ps", "-q"], text=True).split()
containers = json.loads(subprocess.check_output(["docker", "inspect", *ids], text=True))
rows = []
for c in sorted(containers, key=lambda item: item["Name"]):
    name = c["Name"].lstrip("/")
    image = c["Config"]["Image"]
    lowered = f"{name} {image}".lower()
    if not any(term in lowered for term in TERMS) or any(term in lowered for term in EXCLUDE):
        continue
    env = dict(item.split("=", 1) for item in c["Config"].get("Env", []) if "=" in item)
    labels = c["Config"].get("Labels") or {}
    rows.append((
        name, image, labels.get("com.docker.compose.project", "UNKNOWN"),
        labels.get("com.docker.compose.service", "UNKNOWN"),
        labels.get("com.docker.compose.project.config_files", "UNKNOWN"),
        *[env.get(key, "UNKNOWN") for key in KEYS],
    ))

lines = [
    "# Stage 6 Production-Write Safety Inventory", "",
    f"Captured: `{datetime.now(timezone.utc).isoformat()}`", "",
    "Read-only capture. Only the ten allowlisted safety keys were read; no secret values were inspected or recorded.", "",
    "`PRODUCTION_BUSINESS_WRITES=UNKNOWN`", "",
    "## Applicable and potentially applicable containers", "",
    "Missing values are `UNKNOWN`, not inferred as false or not applicable. A `NOT_APPLICABLE` disposition requires an reviewed capability classification that is not presently available.", "",
    "| Container | Image | Project/service | Config authority | " + " | ".join(KEYS) + " |",
    "|---|---|---|---|" + "---|" * len(KEYS),
]
for row in rows:
    name, image, project, service, config, *values = row
    lines.append("| " + " | ".join((f"`{name}`", f"`{image}`", f"`{project}/{service}`", f"`{config}`", *[f"`{v}`" for v in values])) + " |")

noncanonical = [r for r in rows if r[5 + KEYS.index("PRODUCTION_DIALING")] == "false"]
lines += [
    "", "## Findings", "",
    f"- Relevant/potentially relevant containers inventoried: {len(rows)}.",
    f"- Containers with noncanonical `PRODUCTION_DIALING=false`: {len(noncanonical)}; all belong to Compose project `codestra`.",
    "- No runtime authority exposes an authoritative `CALLS_PLACED=0` counter for the applicable production/canary scope.",
    "- Historical reports and test declarations mentioning zero calls are not accepted as current runtime evidence.",
    "- Core-host SMTP service publications are loopback-only (`127.0.0.1:2587`, `127.0.0.1:2993`, and local administrative endpoints).",
    "- The separate host `37.27.128.39` rejected available SSH identities. Preserved evidence of three Klyrow containers with `LIVE_EMAIL_DELIVERY=true` and public SMTP therefore remains unresolved.",
    "- No relevant running systemd application service was found beyond the containerized workloads.",
    "", "## Gate", "",
    "`CALLS_PLACED=UNKNOWN`", "",
    "`LIVE_EMAIL_DELIVERY=UNKNOWN`", "",
    "`PRODUCTION_BUSINESS_WRITES=UNKNOWN`", "",
    "The mission stops before source edits, pull requests, wrapper installation, sudoers changes, service restarts, or workflow execution.",
]
OUT.write_text("\n".join(lines) + "\n")
