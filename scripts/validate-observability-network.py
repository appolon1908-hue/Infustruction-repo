#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "observability"


def load(name: str) -> dict:
    return json.loads((CONFIG / name).read_text(encoding="utf-8"))


exposure = load("service-exposure.v1.json")
communication = load("communication-map.v1.json")
firewall = load("firewall-policy.v1.json")

expected_hosts = {
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
browser_ids = {"grafana", "superset", "openbao"}
private_ids = set(expected_hosts) - browser_ids

services = exposure.get("services") or []
by_id = {item.get("id"): item for item in services}
if len(services) != 14 or set(by_id) != set(expected_hosts):
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=service_set")
if len({item.get("hostname") for item in services}) != 14:
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=duplicate_hostname")
for service_id, hostname in expected_hosts.items():
    item = by_id[service_id]
    if item.get("hostname") != hostname:
        raise SystemExit(f"OBSERVABILITY_NETWORK_ERROR=hostname:{service_id}")
    if item.get("publicNativePort") is not False:
        raise SystemExit(f"OBSERVABILITY_NETWORK_ERROR=public_native_port:{service_id}")
    if not item.get("referenceNativePorts"):
        raise SystemExit(f"OBSERVABILITY_NETWORK_ERROR=missing_reference_port:{service_id}")
    scopes = set(item.get("approvedBindScopes") or [])
    if not scopes or not scopes <= {"loopback", "private_vlan", "private_docker_network"}:
        raise SystemExit(f"OBSERVABILITY_NETWORK_ERROR=bind_scope:{service_id}")
for service_id in private_ids:
    if by_id[service_id].get("exposure") != "private_internal_caddy_deny_only":
        raise SystemExit(f"OBSERVABILITY_NETWORK_ERROR=private_exposure:{service_id}")
if by_id["grafana"].get("exposure") != "authenticated_browser_via_caddy":
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=grafana_exposure")
if by_id["superset"].get("exposure") != "authenticated_browser_via_caddy":
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=superset_exposure")
if by_id["openbao"].get("exposure") != "restricted_authenticated_browser_via_caddy":
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=openbao_exposure")
if by_id["postgres-exporter"].get("repositoryAuthority") != "blocked_missing_principal_repository":
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=postgres_exporter_authority_gate")

expected_flows = {
    ("caddy", "grafana", 3000),
    ("caddy", "superset", 8088),
    ("caddy", "openbao", 8200),
    ("grafana", "prometheus", 9090),
    ("grafana", "loki", 3100),
    ("grafana", "tempo", 3200),
    ("prometheus", "alertmanager", 9093),
    ("prometheus", "node-exporter", 9100),
    ("prometheus", "cadvisor", 8080),
    ("prometheus", "postgres-exporter", 9187),
    ("prometheus", "redis-exporter", 9121),
    ("prometheus", "blackbox-exporter", 9115),
    ("alloy", "loki", 3100),
    ("alloy", "tempo", 4317),
    ("alloy", "otel-collector", 4317),
    ("otel-collector", "tempo", 4317),
    ("otel-collector", "prometheus", 9090),
    ("otel-collector", "loki", 3100),
    ("superset", "curated-analytics-read-model", 5432),
    ("authorized-application", "openbao", 8200),
}
flows = communication.get("flows") or []
actual_flows = {(item.get("source"), item.get("destination"), item.get("referencePort")) for item in flows}
if communication.get("defaultEastWestPolicy") != "deny" or actual_flows != expected_flows:
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=communication_map")
if len(flows) != len(actual_flows):
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=duplicate_flow")

public = firewall.get("publicIngress") or []
public_identity = {(item.get("owner"), item.get("port")) for item in public}
if public_identity != {("caddy", 80), ("caddy", 443), ("host-ssh", 22)}:
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=public_ingress")
ssh = next(item for item in public if item.get("port") == 22)
if ssh.get("sources") != ["approved_admin_cidrs"] or ssh.get("restricted") is not True:
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=ssh_not_restricted")
forbidden_ports = set(firewall.get("forbiddenPublicNativePorts") or [])
required_forbidden = {3000, 8088, 9090, 9093, 3100, 3200, 4317, 4318, 9100, 8080, 9187, 9121, 9115, 12345, 8200}
if forbidden_ports != required_forbidden:
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=forbidden_public_port_set")
if {item.get("port") for item in public} & forbidden_ports:
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=native_port_public_overlap")
listener_policy = firewall.get("nativeListenerPolicy") or {}
if set(listener_policy.get("forbiddenBindAddresses") or []) != {"0.0.0.0", "::"}:
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=public_bind_guard")
if listener_policy.get("dockerPublishedPortRequiresDockerUserPolicy") is not True:
    raise SystemExit("OBSERVABILITY_NETWORK_ERROR=docker_firewall_guard")
shared_host = firewall.get("sharedHostSafety") or {}
for gate in ("preserveUnrelatedApprovedServices", "smtpPort25IsOutsideThisObservabilityPolicy", "doNotFlushExistingFirewall", "doNotReplaceHostPolicyWithoutFullInventory"):
    if shared_host.get(gate) is not True:
        raise SystemExit(f"OBSERVABILITY_NETWORK_ERROR=shared_host_gate:{gate}")

for document in (exposure, communication, firewall):
    if document.get("liveInstallationAuthorized") is not False:
        raise SystemExit("OBSERVABILITY_NETWORK_ERROR=source_must_not_authorize_installation")

print("OBSERVABILITY_SERVICE_COUNT=14")
print("BROWSER_EDGE_HOSTS=graf.codestra.media,supe.codestra.media,bao.codestra.media")
print("PRIVATE_CADDY_POLICY=DENY_ONLY")
print("EAST_WEST_DEFAULT=DENY")
print("PUBLIC_NATIVE_PORTS=DENIED")
print("POSTGRES_EXPORTER_REPOSITORY_AUTHORITY=BLOCKED")
print("PRINCIPAL_REPOSITORY_PORT_CONFIRMATION=PENDING")
print("LIVE_INSTALLATION_AUTHORIZED=NO")
print("OBSERVABILITY_NETWORK_VALIDATION=PASS")
