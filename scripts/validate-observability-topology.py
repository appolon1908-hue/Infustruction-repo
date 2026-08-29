#!/usr/bin/env python3
"""Validate Codestra observability topology and firewall desired state."""

from __future__ import annotations

import ipaddress
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = ROOT / "config" / "observability" / "topology.v1.json"
FIREWALL = ROOT / "config" / "observability" / "firewall.v1.json"

EXPECTED = {
    "grafana": "graf.codestra.media",
    "prometheus": "prom.codestra.media",
    "alertmanager": "aler.codestra.media",
    "loki": "loki.codestra.media",
    "tempo": "temp.codestra.media",
    "otel-collector": "otel.codestra.media",
    "superset": "supe.codestra.media",
    "node-exporter": "node.codestra.media",
    "cadvisor": "cadv.codestra.media",
    "postgres-exporter": "pgex.codestra.media",
    "redis-exporter": "rdex.codestra.media",
    "blackbox-exporter": "blac.codestra.media",
    "alloy": "allo.codestra.media",
    "openbao": "bao.codestra.media",
}
BROWSER = {
    "graf.codestra.media",
    "supe.codestra.media",
    "bao.codestra.media",
}
PRIVATE = set(EXPECTED.values()) - BROWSER


def fail(message: str) -> None:
    print(f"OBSERVABILITY_TOPOLOGY_VALIDATION_ERROR={message}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot load {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path} must contain a JSON object")
    return value


def main() -> None:
    topology = load(TOPOLOGY)
    firewall = load(FIREWALL)

    if topology.get("version") != 1 or firewall.get("version") != 1:
        fail("both documents must use version 1")
    if topology.get("dnsTarget") != "37.27.128.39":
        fail("DNS target mismatch")
    ipaddress.ip_address(topology["dnsTarget"])

    components = topology.get("components")
    if not isinstance(components, list) or len(components) != 14:
        fail("exactly 14 components are required")

    ids = [component.get("id") for component in components]
    if set(ids) != set(EXPECTED) or len(ids) != len(set(ids)):
        fail("component IDs are incomplete or duplicated")

    hosts = {component["id"]: component.get("hostname") for component in components}
    if hosts != EXPECTED:
        fail("component hostname mapping is not canonical")

    for component in components:
        listeners: list[str] = []
        if isinstance(component.get("nativeListener"), str):
            listeners.append(component["nativeListener"])
        listeners.extend(component.get("nativeListeners", []))
        listeners.extend(component.get("ingestListeners", []))
        if any("0.0.0.0" in listener for listener in listeners):
            fail(f"{component['id']} contains a public wildcard listener")

    rules = topology.get("rules", {})
    if rules.get("publicNativePorts") is not False:
        fail("native service ports must not be public")
    if rules.get("caddyOnlyPublicListeners") != [80, 443]:
        fail("Caddy must be the only public web listener")
    if rules.get("productionActivationAuthorized") is not False:
        fail("topology source must not authorize production activation")

    public_ingress = firewall.get("publicIngress")
    public_ports = sorted(entry.get("port") for entry in public_ingress)
    if public_ports != [22, 80, 443]:
        fail("only SSH and Caddy web ports may be public")

    if set(firewall.get("browserFacingThroughCaddy", [])) != BROWSER:
        fail("browser-facing host set mismatch")
    if set(firewall.get("publicDnsButNoPublicProxy", [])) != PRIVATE:
        fail("private-only host set mismatch")

    private_entries = firewall.get("loopbackOrPrivateOnly")
    if not isinstance(private_entries, list) or len(private_entries) != 14:
        fail("firewall must classify all 14 components")
    if {entry.get("component") for entry in private_entries} != set(EXPECTED):
        fail("firewall component coverage mismatch")

    forbidden = set(firewall.get("forbidden", []))
    required_forbidden = {
        "bind-native-service-to-public-0.0.0.0",
        "open-prometheus-to-internet",
        "open-exporter-to-internet",
        "open-loki-or-tempo-ingest-to-internet",
        "open-otel-receiver-to-internet",
        "open-openbao-native-port-to-internet",
        "trust-public-dns-as-access-control",
    }
    if not required_forbidden.issubset(forbidden):
        fail("required deny rules are missing")

    activation = firewall.get("activation", {})
    if any(value is True for value in activation.values()):
        fail("firewall contract branch must remain unapplied")

    print("OBSERVABILITY_TOPOLOGY_VALID=1")


if __name__ == "__main__":
    main()
