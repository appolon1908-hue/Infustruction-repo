#!/usr/bin/env python3
"""Collect a deliberately narrow, sanitized Hetzner Cloud inventory."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ROOT = "https://api.hetzner.cloud/v1"
COLLECTIONS = ("locations", "servers", "networks", "ssh_keys", "firewalls")
FIELDS = (
    "location",
    "network_cidr",
    "staging_subnet_cidr",
    "private_ip",
    "egress_gateway_private_ip",
    "approved_ssh_key_ids",
    "approved_ssh_source_cidrs",
    "approved_egress_fqdns",
    "approved_egress_ports",
    "approved_ntp_fqdns",
    "known_internal_production_deny_cidrs",
)


def sanitized_labels(labels: dict[str, Any]) -> dict[str, str]:
    sensitive_markers = ("secret", "token", "password", "credential", "private_key", "api_key")
    return {
        str(key): "REDACTED" if any(marker in str(key).lower() for marker in sensitive_markers) else str(value)
        for key, value in labels.items()
    }


def get_collection(token: str, collection: str) -> list[dict[str, Any]]:
    if collection not in COLLECTIONS:
        raise SystemExit(f"INVENTORY_ERROR=endpoint_not_allowlisted:{collection}")
    records: list[dict[str, Any]] = []
    page = 1
    while True:
        query = urlencode({"page": page, "per_page": 50})
        request = Request(
            f"{API_ROOT}/{collection}?{query}",
            headers={"Authorization": f"Bearer {token}", "User-Agent": "codestra-stage6-readonly-inventory/1"},
            method="GET",
        )
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
        records.extend(payload.get(collection, []))
        pagination = payload.get("meta", {}).get("pagination", {})
        if not pagination.get("next_page"):
            return records
        page = int(pagination["next_page"])


def labels_mark(value: dict[str, Any], *terms: str) -> bool:
    labels = {str(k).lower(): str(v).lower() for k, v in value.get("labels", {}).items()}
    text = " ".join([str(value.get("name", "")).lower(), *labels.keys(), *labels.values()])
    return all(term in text for term in terms)


def candidate_ip(cidr: str, used: set[str]) -> str | None:
    network = ipaddress.ip_network(cidr, strict=False)
    for offset, address in enumerate(network.hosts()):
        if offset == 0:  # reserve the conventional subnet gateway
            continue
        if str(address) not in used:
            return str(address)
        if offset >= 1024:
            break
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get("HETZNER_CLOUD_TOKEN", "")
    if not token:
        raise SystemExit("INVENTORY_ERROR=missing_token")

    raw = {name: get_collection(token, name) for name in COLLECTIONS}
    used_private_ips = {
        attachment["ip"]
        for server in raw["servers"]
        for attachment in server.get("private_net", [])
        if attachment.get("ip")
    }

    locations = [{"id": x["id"], "name": x["name"], "city": x.get("city"), "country": x.get("country")} for x in raw["locations"]]
    servers = []
    for server in raw["servers"]:
        public_net = server.get("public_net", {})
        servers.append(
            {
                "id": server["id"],
                "name": server["name"],
                "status": server.get("status"),
                "labels": sanitized_labels(server.get("labels", {})),
                "location": server.get("datacenter", {}).get("location", {}).get("name"),
                "public_ipv4": public_net.get("ipv4", {}).get("ip"),
                "public_ipv6": public_net.get("ipv6", {}).get("ip"),
                "private_network_attachments": [
                    {"network_id": x.get("network"), "private_ip": x.get("ip"), "aliases": x.get("alias_ips", [])}
                    for x in server.get("private_net", [])
                ],
            }
        )

    networks = []
    for network in raw["networks"]:
        subnets = [
            {"type": x.get("type"), "ip_range": x.get("ip_range"), "network_zone": x.get("network_zone"), "gateway": x.get("gateway")}
            for x in network.get("subnets", [])
        ]
        candidates = [candidate_ip(x["ip_range"], used_private_ips) for x in subnets if x.get("ip_range")]
        networks.append(
            {
                "id": network["id"],
                "name": network["name"],
                "labels": sanitized_labels(network.get("labels", {})),
                "ip_range": network.get("ip_range"),
                "subnets": subnets,
                "routes": [{"destination": x.get("destination"), "gateway": x.get("gateway")} for x in network.get("routes", [])],
                "unused_candidate_private_ips": [x for x in candidates if x],
            }
        )

    ssh_keys = [{"id": x["id"], "name": x["name"], "labels": sanitized_labels(x.get("labels", {}))} for x in raw["ssh_keys"]]
    firewalls = [
        {
            "id": x["id"],
            "name": x["name"],
            "labels": sanitized_labels(x.get("labels", {})),
            "applied_to": x.get("applied_to", []),
            "rules": [
                {
                    "direction": rule.get("direction"),
                    "protocol": rule.get("protocol"),
                    "port": rule.get("port"),
                    "source_ips": rule.get("source_ips", []),
                    "destination_ips": rule.get("destination_ips", []),
                }
                for rule in x.get("rules", [])
            ],
        }
        for x in raw["firewalls"]
    ]

    production_servers = [x for x in servers if labels_mark(x, "production")]
    approved_keys = [x["id"] for x in raw["ssh_keys"] if labels_mark(x, "stage6", "approved")]
    fields: dict[str, Any] = {name: None for name in FIELDS}
    staging_networks = [x for x in raw["networks"] if labels_mark(x, "staging")]
    if approved_keys:
        fields["approved_ssh_key_ids"] = sorted(approved_keys)

    known_production_ips = sorted(
        {f"{x['public_ipv4']}/32" for x in production_servers if x.get("public_ipv4")}
        | {str(ipaddress.ip_network(x["public_ipv6"], strict=False)) for x in production_servers if x.get("public_ipv6")}
    )
    inventory = {
        "schema_version": "1.0",
        "source": "Hetzner Cloud API GET-only",
        "locations": locations,
        "servers": servers,
        "networks": networks,
        "ssh_keys": ssh_keys,
        "firewalls": firewalls,
        "known_production_server_cidrs": known_production_ips,
        "known_staging_only_network_ids": [x["id"] for x in staging_networks],
    }
    unresolved = [name for name, value in fields.items() if value is None]
    resolution = {"schema_version": "1.0", "fields": fields, "unresolved": unresolved, "complete": not unresolved}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "hetzner-inventory.sanitized.json").write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n")
    (args.output_dir / "stage6-input-resolution.json").write_text(json.dumps(resolution, indent=2, sort_keys=True) + "\n")
    print("HETZNER_INVENTORY=PASS")
    print(f"UNRESOLVED_NON_SECRET_FIELDS={','.join(unresolved) if unresolved else 'NONE'}")


if __name__ == "__main__":
    main()
