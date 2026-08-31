#!/usr/bin/env python3
"""Build sanitized Phase 0/1 evidence from read-only host observations."""
import csv, json, os, re, socket, subprocess
from datetime import datetime, timezone
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/runtime-reconciliation"

def out(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()

def main():
    now = datetime.now(timezone.utc).isoformat()
    rows = list(csv.DictReader((REPORT / "STAGE6-RUNTIME-INVENTORY.csv").open()))
    release = [r for r in rows if r["classification"] == "Codestra release workload"]
    unknown_provenance = sum(r["git_sha"] == "UNESTABLISHED" for r in release)
    unpinned = sum("@sha256:" not in r["image"] for r in release)
    safety_fail = sum(r["safety_result"] == "FAIL" for r in release)
    migration = [r for r in release if "alembic upgrade" in r["startup_command"] or "--init=" in r["startup_command"] or "--update=" in r["startup_command"]]

    # Exact supporting inventories. These contain names/metadata only, never secrets.
    git_rows = []
    for line in Path("/tmp/stage6-gitdirs.txt").read_text().splitlines():
        repo = str(Path(line).parent)
        def git(*a):
            try: return out("git", "-C", repo, *a)
            except Exception: return "UNRESOLVED"
        origin = git("remote", "get-url", "origin")
        origin = re.sub(r"(https?://)[^/@]+@", r"\1REDACTED@", origin)
        git_rows.append((repo, git("rev-parse", "HEAD"), git("branch", "--show-current") or "DETACHED", origin))
    REPORT.mkdir(parents=True, exist_ok=True)
    with (REPORT / "STAGE6-GIT-REPOSITORY-INVENTORY.csv").open("w", newline="") as f:
        w=csv.writer(f); w.writerow(("path","sha","branch","origin")); w.writerows(git_rows)
    with (REPORT / "STAGE6-DEPLOYMENT-FILE-INVENTORY.txt").open("w") as f:
        f.write(Path("/tmp/stage6-deployment-files.txt").read_text())
    networks=[]
    for nid in out("docker","network","ls","-q").splitlines():
        n=json.loads(out("docker","network","inspect",nid))[0]
        subnets=",".join(x.get("Subnet","") for x in n.get("IPAM",{}).get("Config",[]) or [])
        networks.append((n["Name"],n["Driver"],str(n["Internal"]).lower(),subnets,len(n.get("Containers") or {})))
    with (REPORT / "STAGE6-DOCKER-NETWORK-INVENTORY.csv").open("w",newline="") as f:
        w=csv.writer(f); w.writerow(("name","driver","internal","subnets","attached_containers")); w.writerows(sorted(networks))
    volumes=out("docker","volume","ls","--format","{{.Name}}").splitlines()
    (REPORT / "STAGE6-DOCKER-VOLUME-INVENTORY.txt").write_text("\n".join(sorted(volumes))+"\n")
    systemd=out("systemctl","list-units","--type=service","--state=running","--no-legend","--plain").splitlines()
    (REPORT / "STAGE6-SYSTEMD-RUNNING.txt").write_text("\n".join(systemd)+"\n")

    lock=yaml.safe_load((ROOT/"STAGE6-SOURCE-LOCK.yaml").read_text())
    lock["locked_at"] = now
    lock["runtime_revalidated_at"] = now
    lock["status"] = "FAIL_CLOSED_RUNTIME_DRIFT"
    lock["runtime_mutation_authorized"] = False
    lock["core_host_readback"] = {
        "host": socket.gethostname(), "public_ip": "65.109.65.169", "private_ip": "10.40.0.1",
        "environment": "staging", "running_containers": len(rows),
        "release_workloads": len(release), "unknown_provenance_release_workloads": unknown_provenance,
        "unpinned_release_images": unpinned, "safety_incomplete_release_workloads": safety_fail,
        "startup_migration_violations": len(migration), "explicit_allowlisted_dangerous_true": 0,
    }
    lock["repositories"].setdefault("infrastructure", {
        "repository": "appolon1908-hue/Infustruction-repo",
        "revision": "b71f922a8d878a47c5a41f6b1cf9e8b47f9fba68",
        "artifact": "deployment_authority",
    })
    for v in lock["repositories"].values():
        v.setdefault("branch_source_lineage", "main")
        v.setdefault("image", "UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE")
        if "image_digest" not in v and "runtime_image_digest" not in v:
            v["image_digest"] = "UNRESOLVED_NO_REVIEWED_RUNTIME_IMAGE"
        v.setdefault("host", "65.109.65.169")
        v.setdefault("environment", "staging")
        v.setdefault("rollback_git_sha", "UNRESOLVED")
        v.setdefault("rollback_image_digest", "UNRESOLVED")
    (ROOT/"STAGE6-SOURCE-LOCK.yaml").write_text(yaml.safe_dump(lock,sort_keys=False))

    md=["# Codestra Stage 6 Runtime Preflight Inventory","",f"Captured: `{now}`", "",
        "Scope: read-only inspection of the core/staging host. No container, systemd unit, database, network, volume, secret, gateway, or application was changed.","",
        "## Gate result","","`PREFLIGHT=FAIL`","","`SOURCE_LOCK=FAIL`","","`RUNTIME_DRIFT=YES`","",
        f"- Running containers: {len(rows)} (exact inventory: `reports/runtime-reconciliation/STAGE6-RUNTIME-INVENTORY.csv`).",
        f"- Release workloads: {len(release)}; Git SHA unestablished: {unknown_provenance}; mutable image references: {unpinned}.",
        f"- Safety-applicable release workloads with incomplete explicit controls: {safety_fail}.",
        f"- Normal-startup migration/module-init violations: {len(migration)}.",
        "- Unexpected public Docker exposure findings: 0. Expected host ingress is SSH plus Caddy HTTP/HTTPS; all observed container publications are loopback or private-VLAN scoped.",
        "- Backup files exist, including the Stage 6 dump set under `/opt/codestra/backups/stage6-staging/20260830T233931Z-65018df`, but restore verification was not performed in this phase.","",
        "## Host and runtime","",
        "| Item | Observed |","|---|---|",
        "| Host | `middleware` (`65.109.65.169`, private `10.40.0.1`) |",
        "| OS/kernel | Ubuntu 22.04.5 LTS; Linux 5.15.0-187-generic x86_64 |",
        "| Docker / Compose | 29.7.2 / v5.5.0 |",
        f"| Docker objects | {len(rows)} running containers; 237 total containers; {len(networks)} networks; {len(volumes)} volumes |",
        "| Routes | Default via `65.109.65.129`; private VLAN `10.40.0.0/24`; Docker bridge routes present |",
        "| Public listeners | SSH 22; Caddy TCP 80/443 and UDP 443 |",
        "| Private/loopback listeners | Caddy/private gateway and application admin endpoints; exact bind evidence retained in preflight transcript |",
        "| systemd | Caddy, Docker/containerd, NATS, SSH, fail2ban, cron, and Keycloak GitHub runner active; exact list in `STAGE6-SYSTEMD-RUNNING.txt` |","",
        "## Exact inventory authorities","",
        f"- {len(rows)} containers: `STAGE6-RUNTIME-INVENTORY.csv`.",
        f"- {len(networks)} Docker networks: `STAGE6-DOCKER-NETWORK-INVENTORY.csv`.",
        f"- {len(volumes)} Docker volumes: `STAGE6-DOCKER-VOLUME-INVENTORY.txt`.",
        f"- {len(git_rows)} Git worktrees/repositories under the requested roots: `STAGE6-GIT-REPOSITORY-INVENTORY.csv`.",
        "- 5,704 Compose/deployment/unit/Caddy files under the requested roots: `STAGE6-DEPLOYMENT-FILE-INVENTORY.txt`.","",
        "## Stateful and platform read-back","",
        "PostgreSQL database names were read from the staging Middleware, Odoo, n8n, identity, SMS, reseller and websocket instances without credentials being printed. One legacy PostgreSQL container and the exporter do not permit the generic read-back and remain unresolved. Redis staging instances are running and healthy. Odoo, Middleware, n8n, Keycloak, Kong, Caddy, Prometheus, Alertmanager, Node Exporter, cAdvisor, Blackbox, Redis Exporter and PostgreSQL Exporter are running. No running OpenBao, Grafana, Loki, Tempo, Alloy or Superset container was observed on this host.","",
        "Marketing, AI, Communication, Social control-plane, and `social.codestra.co` have reviewed Git source identities but no unambiguous running Stage 6 workload on this host.","",
        "## Source-lock table","","| Component | Repository | Lineage | Locked SHA | Image digest | Runtime disposition |","|---|---|---|---|---|---|" ]
    for name,v in lock["repositories"].items():
        digest=v.get("image_digest",v.get("runtime_image_digest","UNRESOLVED"))
        md.append(f"| {name} | `{v['repository']}` | `{v['branch_source_lineage']}` | `{v['revision']}` | `{digest}` | {'locked' if not str(digest).startswith('UNRESOLVED') else 'source locked; image unresolved'} |")
    md += ["","Kong `3594fe25...` is one approved commit ahead of required merge `186630b4...`. Social runtime remains exactly `4f7817f6...`.","",
        "## Drift and blockers","",
        f"1. {unknown_provenance} of 22 release workloads do not expose an exact Git SHA.",
        f"2. {unpinned} of 22 release workloads use a mutable runtime image reference.",
        f"3. {safety_fail} safety-applicable release workloads lack the complete explicit false/disabled set; absence is ambiguous even though no inspected allowlisted flag was explicitly true.",
        "4. Middleware still runs `alembic upgrade head` at normal startup; two long-running Odoo services still use `--init`.",
        "5. Several participating source repositories have no reviewed published runtime image/digest, rollback SHA, or rollback digest; the YAML records these as unresolved rather than inventing identities.",
        "6. `private-integration-gateway-1` remains unknown/frozen: root-owned `/opt/middleware/integration-gateway/compose.yaml`, private-VLAN port 8095, shared edge network, and unproved Git owner.",
        "7. Prior evidence on host `37.27.128.39` recorded live email delivery; this core-host read-back does not erase that independent fail-closed finding.","",
        "## Proposed Phase 2 backup plan (not executed)","",
        "1. Freeze the exact affected staging scope and record current image/config rollback identities.",
        "2. Export every staging PostgreSQL database with checksums; separately archive Odoo filestore and n8n data.",
        "3. Capture Redis persistence/config where required, Keycloak export, Kong declarative/database state, Caddy config, OpenBao policies/config, Compose definitions, and sanitized environment key names.",
        "4. Store outside live volumes with owner-only permissions; record source, destination, timestamp, checksum and exact restore command.",
        "5. Verify archives and perform isolated restore tests before any reconciliation. The existing dump set is evidence of files, not a substitute for this verification gate.","",
        "Phase 2 has not begun."]
    (ROOT/"RUNTIME-PREFLIGHT-INVENTORY.md").write_text("\n".join(md)+"\n")

if __name__ == "__main__": main()
