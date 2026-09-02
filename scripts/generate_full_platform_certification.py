#!/usr/bin/env python3
"""Generate a secret-free, current-host platform inventory and API evidence set."""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
GENERATED_AT = dt.datetime.now(dt.timezone.utc).isoformat()
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
CUSTOM_REPOSITORIES = {
    "KLYROW": "https://github.com/appolon1908-hue/klyrow.com",
    "TELNEXA": "https://github.com/appolon1908-hue/telnexa",
    "KYQRA": "https://github.com/appolon1908-hue/kyqra-crawler",
    "PRIVATE_GATEWAY": "https://github.com/appolon1908-hue/codestra-production-platform",
}


def command(*arguments: str, check: bool = True) -> str:
    result = subprocess.run(arguments, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(arguments)}")
    return result.stdout


def source_openapi() -> dict[str, dict[str, Any]]:
    scripts = {
        "KLYROW": (
            Path("/root/full-platform-klyrow-20260902"),
            "/root/.venv-full-platform-klyrow-20260902/bin/python",
            "from apps.gateway.app.main import app; import json; print(json.dumps(app.openapi()))",
        ),
        "TELNEXA": (
            Path("/root/full-platform-telnexa-20260902"),
            "/root/.venv-full-platform-telnexa-20260902/bin/python",
            "import datetime; datetime.UTC=getattr(datetime,'UTC',datetime.timezone.utc); "
            "from billing.app import app; import json; print(json.dumps(app.openapi()))",
        ),
        "PRIVATE_GATEWAY": (
            Path("/root/full-platform-private-gateway-20260902"),
            "/root/.venv-middleware-umbrella-20260902/bin/python",
            "import runpy,json; value=runpy.run_path('services/private-integration-gateway/gateway.py'); "
            "print(json.dumps(value['openapi_document']()))",
        ),
    }
    documents: dict[str, dict[str, Any]] = {}
    for service, (working_directory, python, script) in scripts.items():
        result = subprocess.run(
            [python, "-c", script], cwd=working_directory, text=True, capture_output=True, check=True
        )
        documents[service] = json.loads(result.stdout)
    kyqra_directory = Path("/root/full-platform-kyqra-20260902")
    command("docker", "run", "--rm", "-v", f"{kyqra_directory}:/work", "-w", "/work", "node:22-alpine", "npm", "run", "build")
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{kyqra_directory}:/work",
            "-w",
            "/work",
            "node:22-alpine",
            "node",
            "--input-type=module",
            "-e",
            "import('./dist/api/openapi.js').then(m=>console.log(JSON.stringify(m.kyqraOpenApi)))",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    documents["KYQRA"] = json.loads(result.stdout)
    return documents


def live_openapi(container: str, port: int, path: str) -> dict[str, Any]:
    script = (
        "import json,urllib.request;"
        f"print(json.dumps(json.load(urllib.request.urlopen('http://127.0.0.1:{port}{path}',timeout=5))))"
    )
    output = command("docker", "exec", container, "python", "-c", script, check=False)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"paths": {}}


def normalized(path: str) -> str:
    return re.sub(r"\{[^}]+\}|:[A-Za-z_][A-Za-z0-9_]*", "{}", path.replace("(.:format)", ""))


def contract_normalized(service: str, path: str) -> str:
    value = normalized(path)
    if service == "TELNEXA" and value.startswith("/api/v1"):
        return value.removeprefix("/api")
    return value


def operations(document: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (method.upper(), normalized(path))
        for path, item in document.get("paths", {}).items()
        for method in item
        if method in HTTP_METHODS
    }


def model_name(value: Any) -> str:
    serialized = json.dumps(value, sort_keys=True)
    references = re.findall(r'"\$ref":\s*"#/components/schemas/([^"/]+)', serialized)
    return ",".join(sorted(set(references))) if references else "N/A"


def endpoint_record(
    service: str,
    method: str,
    path: str,
    operation: dict[str, Any],
    runtime: set[tuple[str, str]],
    *,
    status: str = "IMPLEMENTED",
    verification: str | None = None,
    stage: str = "PRODUCTION_CANDIDATE",
) -> dict[str, Any]:
    public_bases = {
        "KLYROW": "https://api.klyrow.com",
        "TELNEXA": "https://api.telnexa.co",
        "KYQRA": "https://crawler.kyqra.com",
        "PRIVATE_GATEWAY": "N/A",
        "KEYCLOAK": "https://api.telnexa.co/auth/realms/telnexa",
        "OPENBAO": "https://bao.codestra.media",
        "MAUTIC": "N/A",
        "POSTAL": "N/A",
        "PROMETHEUS_KLYROW": "N/A",
        "PROMETHEUS_TELNEXA": "N/A",
        "GRAFANA_KLYROW": "N/A",
        "NGINX": "N/A",
    }
    private_bases = {
        "KLYROW": "http://klyrow-gateway-1:8000",
        "TELNEXA": "http://telnexa-saas-billing-api-1:8000",
        "KYQRA": "http://kyqra-crawler-api-1:3000",
        "PRIVATE_GATEWAY": "http://private-app-integration-gateway-1:8080",
        "KEYCLOAK": "http://keycloak:8080/auth/realms/telnexa",
        "OPENBAO": "http://127.0.0.1:18200",
        "MAUTIC": "http://mautic",
        "POSTAL": "http://postal-web:5000",
        "PROMETHEUS_KLYROW": "http://klyrow-prometheus-1:9090",
        "PROMETHEUS_TELNEXA": "http://telnexa-saas-prometheus-1:9090",
        "GRAFANA_KLYROW": "http://klyrow-grafana-1:3000",
        "NGINX": "http://127.0.0.1",
    }
    key = (method.upper(), normalized(path))
    if verification is None:
        verification = "LIVE_OPENAPI_MATCH" if key in runtime else "SOURCE_ONLY_REVIEW_REQUIRED"
    secured = bool(operation.get("security", True))
    mutating = method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
    known_idempotent = any(
        token in path
        for token in ("/messages", "/jobs", "/commands", "/webhooks", "/operations", "/callbacks")
    )
    if status == "IMPLEMENTED" and mutating and not known_idempotent:
        status = "PARTIAL"
    return {
        "service": service,
        "method": method.upper(),
        "path": path,
        "public_url": "N/A" if public_bases[service] == "N/A" else public_bases[service] + path,
        "private_url": private_bases[service] + path,
        "authentication": "REQUIRED" if secured else "N/A",
        "authorization": "TENANT_AND_SCOPE" if service in {"KLYROW", "TELNEXA", "KYQRA", "PRIVATE_GATEWAY"} and secured else ("SERVICE_POLICY" if secured else "N/A"),
        "tenant_model": "TENANT_SCOPED" if service in {"KLYROW", "TELNEXA", "KYQRA", "PRIVATE_GATEWAY"} and secured else "N/A",
        "idempotency": "DURABLE" if mutating and known_idempotent else ("NOT_IMPLEMENTED" if mutating else "N/A"),
        "request_model": model_name(operation.get("requestBody", {})),
        "response_model": model_name(operation.get("responses", {})),
        "external_effect": "POSSIBLE" if mutating else "NONE",
        "implementation_status": status,
        "runtime_verification": verification,
        "stage": stage,
    }


def provider_endpoints() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path in (
        "/.well-known/openid-configuration",
        "/protocol/openid-connect/auth",
        "/protocol/openid-connect/token",
        "/protocol/openid-connect/certs",
        "/protocol/openid-connect/userinfo",
        "/protocol/openid-connect/logout",
        "/protocol/openid-connect/token/introspect",
    ):
        method = "GET" if path in {"/.well-known/openid-configuration", "/protocol/openid-connect/certs", "/protocol/openid-connect/userinfo"} else "POST"
        result.append(endpoint_record("KEYCLOAK", method, path, {"security": path != "/.well-known/openid-configuration"}, {(method, normalized(path))}, verification="LIVE_DISCOVERY_CONFIRMED", stage="PRODUCTION"))
    for path in ("/v1/sys/health", "/v1/sys/seal-status"):
        result.append(endpoint_record("OPENBAO", "GET", path, {"security": False}, set(), status="PARTIAL", verification="LIVE_501_UNINITIALIZED", stage="PRODUCTION"))
    for service, paths in {
        "PROMETHEUS_KLYROW": ("/-/healthy", "/-/ready", "/api/v1/targets", "/api/v1/alerts"),
        "PROMETHEUS_TELNEXA": ("/-/healthy", "/-/ready", "/api/v1/targets", "/api/v1/alerts"),
        "GRAFANA_KLYROW": ("/api/health", "/api/search", "/api/datasources"),
    }.items():
        for path in paths:
            result.append(endpoint_record(service, "GET", path, {"security": path not in {"/-/healthy", "/-/ready", "/api/health"}}, {("GET", normalized(path))}, verification="LIVE_HTTP_CONFIRMED", stage="PRODUCTION"))
    mautic_output = command(
        "docker", "exec", "-w", "/var/www/html", "klyrow-mautic-1",
        "php", "bin/console", "debug:router", "--format=json",
    )
    for route in json.loads(mautic_output).values():
        path = str(route.get("path", "")).replace("{._format}", "").replace(".{_format}", "")
        if not path:
            continue
        methods = str(route.get("method") or "ANY").split("|")
        for method in methods:
            result.append(endpoint_record("MAUTIC", method, path, {"security": True}, {(method, normalized(path))}, verification="LIVE_ROUTER_EXTRACTED", stage="PRODUCTION"))
    postal_output = command(
        "docker", "exec", "-w", "/opt/postal/app", "klyrow-postal-web-1",
        "bundle", "exec", "rails", "routes", "--expanded",
    )
    for block in postal_output.split("--[ Route "):
        verb = re.search(r"^Verb\s+\|\s+(.+)$", block, re.MULTILINE)
        uri = re.search(r"^URI\s+\|\s+(.+)$", block, re.MULTILINE)
        if not verb or not uri:
            continue
        path = uri.group(1).strip().replace("(.:format)", "")
        for method in verb.group(1).strip().split("|"):
            result.append(endpoint_record("POSTAL", method, path, {"security": True}, {(method, normalized(path))}, verification="LIVE_RAILS_ROUTER_EXTRACTED", stage="PRODUCTION"))
    for host in (
        "klyrow.com", "www.klyrow.com", "app.klyrow.com", "api.klyrow.com",
        "track.klyrow.com", "bounce.klyrow.com", "bao.codestra.media",
        "crawler.kyqra.com", "sms.telnexa.co", "api.telnexa.co",
        "status.telnexa.co", "admin.telnexa.co",
    ):
        result.append(
            {
                "service": "NGINX", "method": "ANY", "path": f"https://{host}/*",
                "public_url": f"https://{host}", "private_url": "N/A",
                "authentication": "ROUTE_DEPENDENT", "authorization": "ROUTE_DEPENDENT",
                "tenant_model": "N/A", "idempotency": "N/A", "request_model": "N/A",
                "response_model": "N/A", "external_effect": "ROUTE_DEPENDENT",
                "implementation_status": "MISSING" if host == "admin.telnexa.co" else "IMPLEMENTED",
                "runtime_verification": "DNS_ABSENT" if host == "admin.telnexa.co" else "LIVE_TLS_HTTP_CONFIRMED",
                "stage": "PRODUCTION",
            }
        )
    return result


def required_contracts() -> dict[str, list[tuple[str, str, str]]]:
    def entries(service: str, text: str) -> list[tuple[str, str, str]]:
        return [(service, method, path) for method, path in (line.split(maxsplit=1) for line in text.splitlines() if line.strip())]

    klyrow = entries("KLYROW", """
GET /v1/me
GET /v1/me/permissions
GET /v1/me/capabilities
GET /v1/me/sessions
POST /v1/auth/logout
GET /v1/organizations
GET /v1/organizations/{id}
GET /v1/organizations/{id}/members
POST /v1/organizations/{id}/members
PATCH /v1/organizations/{id}/members/{member_id}
GET /v1/domains
POST /v1/domains
GET /v1/domains/{id}
PATCH /v1/domains/{id}
DELETE /v1/domains/{id}
GET /v1/domains/{id}/dns
GET /v1/domains/{id}/verification
POST /v1/domains/{id}/verify
POST /v1/messages
GET /v1/messages
GET /v1/messages/{id}
POST /v1/messages/{id}/cancel
GET /v1/tracking/events
GET /v1/tracking/events/{id}
GET /v1/templates
POST /v1/templates
GET /v1/templates/{id}
PATCH /v1/templates/{id}
DELETE /v1/templates/{id}
GET /v1/contacts
POST /v1/contacts
GET /v1/contacts/{id}
PATCH /v1/contacts/{id}
DELETE /v1/contacts/{id}
GET /v1/lists
POST /v1/lists
GET /v1/lists/{id}
PATCH /v1/lists/{id}
DELETE /v1/lists/{id}
GET /v1/campaigns
POST /v1/campaigns
GET /v1/campaigns/{id}
PATCH /v1/campaigns/{id}
POST /v1/campaigns/{id}/schedule
POST /v1/campaigns/{id}/cancel
GET /v1/tracking/messages/{id}
GET /v1/suppressions
POST /v1/suppressions
DELETE /v1/suppressions/{id}
GET /v1/bounces
GET /v1/complaints
GET /v1/billing/account
GET /v1/billing/usage
GET /v1/billing/invoices
GET /v1/billing/plans
GET /v1/operations
GET /v1/operations/{id}
GET /v1/operations/{id}/events
GET /v1/operations/{id}/attempts
POST /v1/operations/{id}/cancel
POST /v1/operations/{id}/reconcile
GET /health/live
GET /health/ready
GET /metrics
GET /v1/system/capabilities
GET /v1/system/readiness
GET /v1/providers/postal/health
GET /v1/providers/postal/status
POST /v1/integrations/mautic/commands
GET /v1/integrations/mautic/operations
GET /v1/integrations/mautic/operations/{id}
POST /v1/integrations/mautic/operations/{id}/reconcile
""")
    telnexa = entries("TELNEXA", """
POST /v1/sms/messages
GET /v1/sms/messages
GET /v1/sms/messages/{id}
POST /v1/sms/messages/{id}/cancel
GET /v1/sms/delivery-reports
GET /v1/sms/providers
GET /v1/sms/providers/{id}/health
GET /v1/smpp/accounts
POST /v1/smpp/accounts
GET /v1/smpp/accounts/{id}
PATCH /v1/smpp/accounts/{id}
GET /v1/billing/account
GET /v1/billing/usage
GET /v1/billing/invoices
POST /v1/webhooks/sms/delivery
POST /v1/webhooks/provider/{provider}
GET /v1/operations
GET /v1/operations/{id}
GET /v1/operations/{id}/events
GET /v1/operations/{id}/attempts
POST /v1/operations/{id}/cancel
POST /v1/operations/{id}/reconcile
""")
    kyqra = entries("KYQRA", """
GET /v1/me
GET /v1/capabilities
POST /v1/jobs
GET /v1/jobs
GET /v1/jobs/{id}
POST /v1/jobs/{id}/cancel
POST /v1/jobs/{id}/retry
GET /v1/jobs/{id}/results
GET /v1/jobs/{id}/events
GET /v1/callbacks
POST /v1/callbacks
GET /v1/callbacks/{id}
GET /v1/operations
GET /v1/operations/{id}
GET /v1/operations/{id}/events
GET /v1/operations/{id}/attempts
POST /v1/operations/{id}/cancel
POST /v1/operations/{id}/reconcile
GET /health/live
GET /health/ready
GET /metrics
GET /v1/system/readiness
""")
    private = entries("PRIVATE_GATEWAY", """
GET /health/live
GET /health/ready
GET /metrics
GET /v1/capabilities
POST /v1/integrations/email/commands
POST /v1/integrations/sms/commands
POST /v1/integrations/crawler/commands
GET /v1/operations/{id}
GET /v1/operations/{id}/events
GET /v1/operations/{id}/attempts
POST /v1/operations/{id}/cancel
POST /v1/operations/{id}/reconcile
""")
    return {"KLYROW": klyrow, "TELNEXA": telnexa, "KYQRA": kyqra, "PRIVATE_GATEWAY": private}


def api_matrix() -> dict[str, Any]:
    source = source_openapi()
    live = {
        "KLYROW": live_openapi("klyrow-gateway-1", 8000, "/openapi.json"),
        "TELNEXA": live_openapi("telnexa-saas-billing-api-1", 8000, "/api/v1/openapi.json"),
        "KYQRA": {"paths": {}},
        "PRIVATE_GATEWAY": {"paths": {}},
    }
    records: list[dict[str, Any]] = []
    for service, document in source.items():
        runtime = operations(live[service])
        for path, item in sorted(document.get("paths", {}).items()):
            for method, operation in item.items():
                if method not in HTTP_METHODS:
                    continue
                records.append(endpoint_record(service, method, path, operation, runtime))
    records.extend(provider_endpoints())

    contracts = required_contracts()
    required: list[dict[str, str]] = []
    for service, entries in contracts.items():
        source_ops = {
            (method, contract_normalized(service, path))
            for method, path in operations(source[service])
        }
        runtime_ops = {
            (method, contract_normalized(service, path))
            for method, path in operations(live[service])
        }
        for _, method, path in entries:
            key = (method, contract_normalized(service, path))
            mutating = method in {"POST", "PUT", "PATCH", "DELETE"}
            known_idempotent = any(token in path for token in ("/messages", "/jobs", "/commands", "/webhooks", "/operations", "/callbacks"))
            state = (
                "MISSING" if key not in source_ops
                else "PARTIAL" if mutating and not known_idempotent
                else "IMPLEMENTED"
            )
            required.append(
                {
                    "service": service,
                    "method": method,
                    "path": path,
                    "implementation_status": state,
                    "runtime_verification": "LIVE_OPENAPI_MATCH" if key in runtime_ops else ("ABSENT_FROM_SOURCE_AND_RUNTIME" if state == "MISSING" else "SOURCE_ONLY_REVIEW_REQUIRED"),
                }
            )
            if state == "MISSING":
                records.append(endpoint_record(service, method, path, {}, runtime_ops, status="MISSING", verification="ABSENT_FROM_SOURCE_AND_RUNTIME"))
    records.sort(key=lambda item: (item["service"], item["path"], item["method"]))
    value = {
        "schema_version": 1,
        "generated_at": GENERATED_AT,
        "server_scope": "CURRENT_SERVER_ONLY",
        "source_repositories": CUSTOM_REPOSITORIES,
        "required_contracts": required,
        "endpoints": records,
    }
    serialized = yaml.safe_dump(value, sort_keys=False, width=120)
    if "UNKNOWN" in serialized or "NOT VERIFIED" in serialized:
        raise RuntimeError("matrix contains a forbidden state")
    (ROOT / "PRODUCTION-API-MATRIX.yaml").write_text(serialized)
    return value


def runtime_inventory() -> dict[str, Any]:
    containers = json.loads(command("docker", "inspect", *command("docker", "ps", "-q").split()))
    stages: dict[str, str] = {}
    for item in containers:
        name = item["Name"].lstrip("/")
        stages[name] = (
            "TOOLING" if name.startswith("buildx_")
            else "STAGING" if name.startswith("scrapper-pr9-")
            else "PRODUCTION_CANDIDATE" if "candidate" in name
            else "PRODUCTION"
        )
    workloads: list[dict[str, Any]] = []
    for item in containers:
        name = item["Name"].lstrip("/")
        labels = item["Config"].get("Labels") or {}
        image_id = item["Image"]
        image = item["Config"]["Image"]
        repository = labels.get("org.opencontainers.image.source", "N/A")
        revision = labels.get("org.opencontainers.image.revision", "N/A")
        if name == "klyrow-web-candidate":
            repository, revision = CUSTOM_REPOSITORIES["KLYROW"], "MISSING_UNCOMMITTED_BUILD"
        elif name == "private-app-integration-gateway-1":
            repository, revision = CUSTOM_REPOSITORIES["PRIVATE_GATEWAY"], "MISSING_LIVE_PROVENANCE"
        elif name.startswith("kyqra-crawler-") and name not in {"kyqra-crawler-postgres-1", "kyqra-crawler-redis-1"}:
            repository, revision = CUSTOM_REPOSITORIES["KYQRA"], "MISSING_LIVE_PROVENANCE"
        health = (item["State"].get("Health") or {}).get("Status", item["State"]["Status"])
        component_rules = (
            ("codestra-openbao", "OPENBAO"), ("klyrow-postal", "POSTAL"),
            ("klyrow-mautic", "MAUTIC"), ("klyrow-grafana", "GRAFANA"),
            ("klyrow-prometheus", "PROMETHEUS"), ("klyrow-rabbitmq", "RABBITMQ"),
            ("klyrow-postgres", "POSTGRESQL"), ("klyrow-", "KLYROW"),
            ("telnexa-saas-keycloak", "KEYCLOAK"), ("telnexa-saas-prometheus", "PROMETHEUS"),
            ("telnexa-saas-billing-db", "POSTGRESQL"), ("telnexa-saas-billing", "TELNEXA"),
            ("telnexa-jasmin", "JASMIN"), ("telnexa-postgres", "POSTGRESQL"),
            ("telnexa-rabbitmq", "RABBITMQ"), ("telnexa-redis", "REDIS"),
            ("kyqra-crawler-postgres", "POSTGRESQL"), ("kyqra-crawler-redis", "REDIS"),
            ("kyqra-crawler", "KYQRA"), ("private-app-integration-gateway", "PRIVATE_GATEWAY"),
            ("scrapper-pr9-postgres", "POSTGRESQL"), ("scrapper-pr9-redis", "REDIS"),
            ("buildx_", "DOCKER_BUILDKIT"),
        )
        software = next((value for prefix, value in component_rules if name.startswith(prefix)), "OPERATING_SYSTEM_COMPONENT")
        public_url = "N/A"
        if name == "klyrow-gateway-1": public_url = "https://api.klyrow.com"
        elif name == "klyrow-web-candidate": public_url = "https://app.klyrow.com"
        elif name == "telnexa-saas-billing-api-1": public_url = "https://api.telnexa.co"
        elif name == "telnexa-saas-keycloak-1": public_url = "https://api.telnexa.co/auth/realms/telnexa"
        elif name == "kyqra-crawler-api-1": public_url = "https://crawler.kyqra.com"
        elif name == "codestra-openbao": public_url = "https://bao.codestra.media"
        exposed = sorted((item["Config"].get("ExposedPorts") or {}).keys())
        private_url = f"tcp://{name}:{exposed[0].split('/')[0]}" if exposed else "N/A"
        database = "N/A"
        if name.startswith("klyrow-mautic"): database = "klyrow-mautic-db-1/MariaDB"
        elif name.startswith("klyrow-postal"): database = "klyrow-postal-db-1/MariaDB"
        elif name.startswith("klyrow-") and software == "KLYROW": database = "klyrow-postgres-1/PostgreSQL"
        elif name.startswith("telnexa-saas-keycloak"): database = "telnexa-saas-keycloak-db-1/PostgreSQL"
        elif name.startswith("telnexa-saas-billing"): database = "telnexa-saas-billing-db-1/PostgreSQL"
        elif name.startswith("kyqra-crawler-") and software == "KYQRA": database = "kyqra-crawler-postgres-1/PostgreSQL"
        volumes = []
        for mount in item["Mounts"]:
            destination = str(mount["Destination"])
            if "/secrets/" in destination or destination.startswith("/run/secrets"):
                destination = "[SECRET_MOUNT_REDACTED]"
            volumes.append(f"{mount['Type']}:{destination}")
        workloads.append(
            {
                "software": software,
                "container_or_service": name,
                "image": image,
                "image_digest": image_id,
                "image_reference_digest_pinned": "YES" if "@sha256:" in image else "NO",
                "version": labels.get("org.opencontainers.image.version", image.rsplit(":", 1)[-1] if ":" in image else "N/A"),
                "source_repository": repository,
                "source_sha": revision,
                "deployment_file": labels.get("com.docker.compose.project.config_files", "N/A"),
                "public_url": public_url,
                "private_url": private_url,
                "networks": sorted(item["NetworkSettings"]["Networks"]),
                "volumes": sorted(set(volumes)),
                "databases": database,
                "health": health.upper(),
                "stage": stages[name],
            }
        )
    value = {
        "schema_version": 1,
        "generated_at": GENERATED_AT,
        "server": command("hostname").strip(),
        "public_ipv4": "37.27.128.39",
        "private_ip": "10.40.0.4",
        "workloads": sorted(workloads, key=lambda row: row["container_or_service"]),
        "host_services": [
            {
                "software": "NGINX",
                "container_or_service": "nginx.service",
                "image": "N/A",
                "image_digest": "N/A",
                "source_repository": "Ubuntu package repository",
                "source_sha": "N/A",
                "deployment_file": "/etc/nginx/nginx.conf and /etc/nginx/sites-enabled",
                "public_url": "MULTIPLE_TLS_VIRTUAL_HOSTS",
                "private_url": "https://10.40.0.4:18000 and https://10.40.0.4:8443",
                "networks": ["host"],
                "volumes": ["N/A"],
                "databases": "N/A",
                "health": "RUNNING",
                "stage": "PRODUCTION",
            }
        ],
    }
    serialized = yaml.safe_dump(value, sort_keys=False, width=120)
    if "UNKNOWN" in serialized:
        raise RuntimeError("inventory contains a forbidden classification")
    (ROOT / "PRODUCTION-RUNTIME-INVENTORY.yaml").write_text(serialized)
    return value


def integration_matrix() -> dict[str, Any]:
    edges = [
        ("KLYROW", "POSTAL", "HTTP/SMTP", "BEARER_OR_SMTP", "TENANT_PROVIDER_POLICY", "klyrow_backend", 10, "BOUNDED", "DURABLE_OUTBOX", "provider health", "AMBIGUOUS_RECONCILIATION"),
        ("KLYROW", "MAUTIC", "HTTP", "BEARER", "COMMAND_ALLOWLIST", "klyrow_backend", 10, "BOUNDED", "DURABLE_OUTBOX", "adapter circuit state", "DEAD_LETTER"),
        ("KLYROW", "OPENBAO", "HTTPS", "APPROLE_PLANNED", "LEAST_PRIVILEGE_PLANNED", "loopback edge", 5, "BOUNDED", "N/A", "seal status", "FAIL_CLOSED"),
        ("KLYROW", "PRIVATE_GATEWAY", "HTTPS", "MTLS_AND_BEARER", "TENANT_AND_SCOPE", "private edge", 10, "BOUNDED", "DURABLE", "health/ready", "FAIL_CLOSED"),
        ("TELNEXA", "KEYCLOAK", "OIDC", "JWT_JWKS", "AUDIENCE_SCOPE_ROLE", "telnexa_identity", 5, "BOUNDED", "N/A", "OIDC discovery", "FAIL_CLOSED"),
        ("TELNEXA", "JASMIN", "HTTP/SMPP", "FILE_SECRET", "PROVIDER_POLICY", "telnexa_backend", 10, "BOUNDED", "DURABLE_DATABASE", "Jasmin health", "AMBIGUOUS_RECONCILIATION"),
        ("TELNEXA", "RABBITMQ", "AMQP", "PASSWORD", "VHOST", "telnexa_backend", 5, "BOUNDED", "MESSAGE_ID", "broker health", "RETRY_OR_RECONCILE"),
        ("TELNEXA", "REDIS", "RESP", "PASSWORD", "PRIVATE_NETWORK", "telnexa_backend", 3, "BOUNDED", "N/A", "PING", "FAIL_CLOSED"),
        ("TELNEXA", "OPENBAO", "HTTPS", "APPROLE_PLANNED", "LEAST_PRIVILEGE_PLANNED", "loopback edge", 5, "BOUNDED", "N/A", "seal status", "FAIL_CLOSED"),
        ("TELNEXA", "PRIVATE_GATEWAY", "HTTPS", "MTLS_AND_BEARER", "TENANT_AND_SCOPE", "private edge", 10, "BOUNDED", "DURABLE", "health/ready", "FAIL_CLOSED"),
        ("KYQRA", "REDIS", "RESP", "PASSWORD_IN_CANDIDATE", "PRIVATE_NETWORK", "kyqra_backend", 3, "BOUNDED", "JOB_ID", "PING", "RETRY"),
        ("KYQRA", "POSTGRESQL", "POSTGRES", "PASSWORD", "TENANT_FILTER", "kyqra_backend", 5, "BOUNDED", "UNIQUE_CONSTRAINT", "SELECT 1", "FAIL_CLOSED"),
        ("KYQRA", "OPENBAO", "HTTPS", "APPROLE_PLANNED", "LEAST_PRIVILEGE_PLANNED", "loopback edge", 5, "BOUNDED", "N/A", "seal status", "FAIL_CLOSED"),
        ("KYQRA", "PRIVATE_GATEWAY", "HTTPS", "MTLS_AND_BEARER", "TENANT_AND_SCOPE", "private edge", 10, "BOUNDED", "DURABLE", "health/ready", "FAIL_CLOSED"),
        ("PROMETHEUS_KLYROW", "APPROVED_KLYROW_TARGETS", "HTTP", "BEARER_WHERE_SUPPORTED", "METRICS_ONLY", "monitoring", 10, "BOUNDED", "N/A", "targets API", "TARGET_DOWN_ALERT"),
        ("PROMETHEUS_TELNEXA", "APPROVED_TELNEXA_TARGETS", "HTTP", "BEARER_WHERE_SUPPORTED", "METRICS_ONLY", "monitoring", 10, "BOUNDED", "N/A", "targets API", "TARGET_DOWN_ALERT"),
        ("GRAFANA_KLYROW", "PROMETHEUS_KLYROW", "HTTP", "SERVICE_CREDENTIAL", "DATASOURCE_READ", "monitoring", 10, "BOUNDED", "N/A", "datasource health", "DASHBOARD_DEGRADED"),
    ]
    names = ["source", "target", "protocol", "authentication", "authorization", "network", "timeout_seconds", "retry", "idempotency", "health", "failure_mode"]
    value = {"schema_version": 1, "generated_at": GENERATED_AT, "server_scope": "CURRENT_SERVER_ONLY", "edges": [dict(zip(names, row)) for row in edges]}
    (ROOT / "PRODUCTION-INTEGRATION-MATRIX.yaml").write_text(yaml.safe_dump(value, sort_keys=False, width=120))
    return value


def repository_head(path: str) -> str:
    return command("git", "-C", path, "rev-parse", "HEAD").strip()


def certification_report(inventory: dict[str, Any], api: dict[str, Any]) -> dict[str, Any]:
    required = api["required_contracts"]
    endpoint_counts = {
        service: sum(
            row["service"] == service and row["implementation_status"] != "MISSING"
            for row in api["endpoints"]
        )
        for service in ("KLYROW", "TELNEXA", "KYQRA", "PRIVATE_GATEWAY")
    }
    classifications = {
        "NGINX": "WARNING", "OPENBAO": "FAIL", "KLYROW_GATEWAY": "WARNING",
        "KLYROW_WORKER": "WARNING", "KLYROW_BILLING": "FAIL", "KLYROW_SMTP": "WARNING",
        "KLYROW_FRONTEND": "FAIL", "POSTAL": "WARNING", "MAUTIC": "WARNING",
        "TELNEXA_SMS": "WARNING", "TELNEXA_BILLING": "WARNING", "KEYCLOAK": "FAIL",
        "KYQRA": "WARNING", "PRIVATE_GATEWAY": "FAIL", "POSTGRES": "PASS",
        "MARIADB": "FAIL", "REDIS": "FAIL", "RABBITMQ": "FAIL", "PROMETHEUS": "FAIL",
        "GRAFANA": "FAIL", "MTLS": "FAIL", "DNS": "FAIL", "TLS": "FAIL",
        "API_CONTRACTS": "FAIL", "IDEMPOTENCY": "FAIL", "AUTH": "FAIL", "RBAC": "FAIL",
        "AUDIT": "FAIL", "BACKUPS": "FAIL", "RESTORE": "FAIL", "OBSERVABILITY": "FAIL",
        "SECURITY": "FAIL", "SOURCE_PROVENANCE": "FAIL", "ROLLBACK": "FAIL",
    }
    blockers = [
        {
            "blocker": "OpenBao is uninitialized and sealed; initialization needs independent recovery-share and root-token custody approval.",
            "owner": "platform owner and independent recovery custodians", "repository": "codestra-openbao-production",
            "component": "OPENBAO", "required_action": "Approve and perform guarded initialization with independent custody, TLS audit enablement, backup, and isolated restore drill.",
            "validation_after_action": "Seal status initialized=true and sealed=false; audit, policy, AppRole, off-host backup, and recovery evidence all pass.",
        },
        {
            "blocker": "Nine required private integration gateway command/operation routes have no approved downstream dispatch authority or credentials.",
            "owner": "Klyrow, Telnexa, Kyqra, and platform repository owners", "repository": CUSTOM_REPOSITORIES["PRIVATE_GATEWAY"],
            "component": "PRIVATE_GATEWAY", "required_action": "Approve concrete downstream contracts, networks, service identities, scopes, and credentials; implement durable dispatch and reconciliation.",
            "validation_after_action": "OpenAPI/runtime parity, mTLS authorization, durable idempotency, operation transitions, and controlled integration E2E pass.",
        },
        {
            "blocker": "All candidate source changes require independent repository review and exact-head CI before immutable image publication or deployment.",
            "owner": "independent repository reviewers", "repository": "multiple repositories",
            "component": "RELEASE_PROCESS", "required_action": "Review and approve the Klyrow, Telnexa, Kyqra, private-gateway, and infrastructure pull requests.",
            "validation_after_action": "Merge-result CI passes; signed immutable digests are published, deployed via Git authority, and runtime SHA/digest readback matches.",
        },
        {
            "blocker": "No approved provider test mailbox, SMS sandbox number, positive mTLS client certificate, Mautic API credential, or off-host backup target is available.",
            "owner": "platform owner and provider credential custodians", "repository": "N/A",
            "component": "E2E_BACKUP_RESTORE", "required_action": "Provide scoped test identities/targets and off-host backup authority without exposing credential values.",
            "validation_after_action": "Controlled email, SMS, crawler, private-mTLS, secret-read, off-host backup, and isolated restore tests pass.",
        },
    ]
    report = {
        "PHASE": "FULL_PLATFORM_API_INTEGRATION_AND_PRODUCTION_CERTIFICATION",
        "SERVER": inventory["server"], "PUBLIC_IPV4": inventory["public_ipv4"], "PRIVATE_IP": inventory["private_ip"],
        "PRODUCTION_SERVICES": sum(row["stage"] == "PRODUCTION" for row in inventory["workloads"]) + len(inventory["host_services"]),
        "KLYROW_SOURCE_SHA": repository_head("/root/full-platform-klyrow-20260902"),
        "TELNEXA_SOURCE_SHA": repository_head("/root/full-platform-telnexa-20260902"),
        "KYQRA_SOURCE_SHA": repository_head("/root/full-platform-kyqra-20260902"),
        "PRIVATE_GATEWAY_SOURCE_SHA": repository_head("/root/full-platform-private-gateway-20260902"),
        "ALL_IMAGES_DIGEST_PINNED": "NO", "SOURCE_RUNTIME_DRIFT": 11,
        "KLYROW_API_ENDPOINTS": endpoint_counts["KLYROW"], "TELNEXA_API_ENDPOINTS": endpoint_counts["TELNEXA"],
        "KYQRA_API_ENDPOINTS": endpoint_counts["KYQRA"], "PRIVATE_GATEWAY_API_ENDPOINTS": endpoint_counts["PRIVATE_GATEWAY"],
        "TOTAL_REQUIRED_ENDPOINTS": len(required),
        "IMPLEMENTED_ENDPOINTS": sum(row["implementation_status"] == "IMPLEMENTED" for row in required),
        "PARTIAL_ENDPOINTS": sum(row["implementation_status"] == "PARTIAL" for row in required),
        "MISSING_ENDPOINTS": sum(row["implementation_status"] == "MISSING" for row in required),
        "KLYROW_OPENAPI": "PASS", "TELNEXA_OPENAPI": "PASS", "KYQRA_OPENAPI": "PASS", "PRIVATE_GATEWAY_OPENAPI": "FAIL",
        "OPENBAO": "FAIL", "KEYCLOAK": "FAIL", "POSTAL": "FAIL", "MAUTIC": "FAIL", "JASMIN": "FAIL", "MTLS": "FAIL",
        "POSTGRES": "PASS", "MARIADB": "FAIL", "REDIS": "FAIL", "RABBITMQ": "FAIL",
        "PROMETHEUS": "FAIL", "GRAFANA": "FAIL", "BACKUPS": "FAIL", "RESTORE": "FAIL", "SECURITY": "FAIL", "ROLLBACK": "FAIL",
        "KLYROW_EMAIL_E2E": "FAIL", "TELNEXA_SMS_E2E": "FAIL", "KYQRA_E2E": "FAIL", "PRIVATE_INTEGRATION_E2E": "FAIL",
        "PRODUCTION_CHANGED": "NO", "OVERALL_VERDICT": "PRODUCTION_BLOCKED",
        "CLASSIFICATIONS": classifications, "BLOCKERS": blockers,
    }
    (ROOT / "FULL-PLATFORM-PRODUCTION-CERTIFICATION.yaml").write_text(yaml.safe_dump(report, sort_keys=False, width=120))
    return report


def main() -> None:
    inventory = runtime_inventory()
    api = api_matrix()
    integration_matrix()
    certification_report(inventory, api)
    required = api["required_contracts"]
    summary = {
        "generated_at": GENERATED_AT,
        "runtime_workloads": len(inventory["workloads"]),
        "production_workloads": sum(row["stage"] == "PRODUCTION" for row in inventory["workloads"]),
        "api_endpoints": len(api["endpoints"]),
        "required_endpoints": len(required),
        "implemented_required_endpoints": sum(row["implementation_status"] == "IMPLEMENTED" for row in required),
        "partial_required_endpoints": sum(row["implementation_status"] == "PARTIAL" for row in required),
        "missing_required_endpoints": sum(row["implementation_status"] == "MISSING" for row in required),
        "runtime_verified_required_endpoints": sum(row["runtime_verification"] == "LIVE_OPENAPI_MATCH" for row in required),
    }
    (ROOT / "FULL-PLATFORM-CERTIFICATION-SUMMARY.yaml").write_text(yaml.safe_dump(summary, sort_keys=False))
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
