#!/usr/bin/env python3
"""Prove the staging inventory collector remains non-mutating and redacted."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType

ROOT = pathlib.Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "scripts" / "collect-observability-readonly-inventory.py"
EXPECTED_PROBES = {
    "kernel": ("uname", "-a"),
    "identity": ("id",),
    "filesystems": ("df", "-PT"),
    "inodes": ("df", "-Pi"),
    "listeners": ("ss", "-H", "-lntup"),
    "time": ("timedatectl", "show", "--no-pager"),
    "docker_version": ("docker", "version", "--format", "{{json .}}"),
    "docker_containers": ("docker", "ps", "-a", "--format", "{{json .}}"),
    "docker_networks": ("docker", "network", "ls", "--format", "{{json .}}"),
    "docker_volumes": ("docker", "volume", "ls", "--format", "{{json .}}"),
    "systemd_services": (
        "systemctl",
        "list-units",
        "--type=service",
        "--all",
        "--no-pager",
        "--no-legend",
    ),
    "caddy_version": ("caddy", "version"),
    "ufw_status": ("ufw", "status", "verbose"),
    "nftables_rules": ("nft", "--numeric", "list", "ruleset"),
    "iptables_rules": ("iptables-save",),
}
FORBIDDEN_SOURCE = (
    "shell=True",
    "subprocess.Popen",
    "os.system(",
    "docker inspect",
    "docker exec",
    "docker run",
    "docker start",
    "docker stop",
    "docker restart",
    "docker rm",
    "docker pull",
    "docker push",
    "systemctl start",
    "systemctl stop",
    "systemctl restart",
    "systemctl enable",
    "systemctl disable",
    "caddy reload",
    "ufw enable",
    "ufw disable",
    "ufw reset",
    "nft add",
    "nft delete",
    "nft flush",
)


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_collector() -> ModuleType:
    spec = importlib.util.spec_from_file_location("codestra_readonly_inventory", COLLECTOR)
    if spec is None or spec.loader is None:
        fail("unable to load inventory collector")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if not COLLECTOR.is_file() or COLLECTOR.is_symlink():
        fail("collector must be a regular non-symlink file")
    text = COLLECTOR.read_text(encoding="utf-8")
    for fragment in FORBIDDEN_SOURCE:
        if fragment in text:
            fail(f"collector contains forbidden mutation capability: {fragment}")
    for required in (
        "capture_output=True",
        "timeout=probe.timeout",
        "env=minimal_environment()",
        "os.O_EXCL",
        "0o600",
        '"sudoUsed": False',
        '"processEnvironmentRead": False',
        '"containerEnvironmentRead": False',
        '"logsRead": False',
        '"configurationContentsRecorded": False',
        '"secretValuesRecorded": False',
        '"serviceStateChanged": False',
        '"networkStateChanged": False',
        '"firewallStateChanged": False',
    ):
        if required not in text:
            fail(f"collector is missing required safety behavior: {required}")

    module = load_collector()
    actual = {probe.name: tuple(probe.argv) for probe in module.PROBES}
    if actual != EXPECTED_PROBES:
        missing = sorted(set(EXPECTED_PROBES) - set(actual))
        unexpected = sorted(set(actual) - set(EXPECTED_PROBES))
        changed = sorted(
            name
            for name in set(actual) & set(EXPECTED_PROBES)
            if actual[name] != EXPECTED_PROBES[name]
        )
        fail(f"probe allowlist changed; missing={missing}, unexpected={unexpected}, changed={changed}")
    if module.minimal_environment().keys() != {"PATH", "LANG", "LC_ALL"}:
        fail("collector subprocess environment must remain minimal")
    if len(module.CANONICAL_HOSTS) != 14 or len(set(module.CANONICAL_HOSTS)) != 14:
        fail("collector must resolve exactly fourteen unique canonical hosts")
    if any(not host.endswith(".codestra.media") for host in module.CANONICAL_HOSTS):
        fail("collector contains a hostname outside codestra.media")

    print("READONLY_INVENTORY_PROBE_COUNT=15")
    print("SUDO_CAPABILITY=ABSENT")
    print("MUTATING_COMMANDS=ABSENT")
    print("PROCESS_OR_CONTAINER_ENVIRONMENT_COLLECTION=ABSENT")
    print("READONLY_INVENTORY_COLLECTOR_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"READONLY_INVENTORY_COLLECTOR_ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
