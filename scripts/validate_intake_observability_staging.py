#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy/staging/intake-observability"
EXPECTED_DIGEST = "sha256:0e00d04d8e898463d4c59341d5ccaae02052914fb9ad69aefd0952e0f7f3ed5b"
EXPECTED_PROFILE = "codestra-middleware-staging-v1"
EXPECTED_KEYCLOAK_PUBLIC_URL = "https://auth-staging.codestra.co"
EXPECTED_KEYCLOAK_ISSUER = EXPECTED_KEYCLOAK_PUBLIC_URL + "/realms/codestra"
EXPECTED_KEYCLOAK_JWKS_URI = EXPECTED_KEYCLOAK_ISSUER + "/protocol/openid-connect/certs"
POSTGRES_HOST = "postgresql.middleware-staging.svc.cluster.local"
REDIS_HOST = "redis.middleware-staging.svc.cluster.local"


def main() -> None:
    lock = json.loads((DEPLOY / "runtime-lock.v1.json").read_text())
    assert lock["schema_version"] == "1.2" and lock["environment"] == "staging"
    assert lock["middleware"]["image_digest"] == EXPECTED_DIGEST
    assert lock["middleware"]["image_reference"].endswith("@" + EXPECTED_DIGEST)
    assert lock["middleware"]["runtime_profile_id"] == EXPECTED_PROFILE
    assert lock["embedded_profile_identities"] == {
        "postgres_host": POSTGRES_HOST,
        "postgres_port": 5432,
        "postgres_database": "codestra_staging",
        "postgres_username": "middleware_staging",
        "postgres_sslmode": "verify-full",
        "redis_host": REDIS_HOST,
        "redis_port": 6379,
        "redis_database": 14,
        "redis_username": "middleware-staging",
        "redis_scheme": "rediss",
    }
    assert lock["transport"] == {
        "private_ca_generated_outside_git": True,
        "postgres_tls": True,
        "redis_tls": True,
        "hostname_verification": True,
        "middleware_trust_bundle_mounted_read_only": True,
    }
    assert lock["network"]["middleware_host_ports"] == []
    assert lock["network"]["private_network_internal"] is True
    assert lock["persistence"] == {
        "named_volumes": ["postgres_data", "redis_data"],
        "preserve_on_redeploy": True,
        "preserve_on_failure_rollback": True,
        "destructive_reset_requires_explicit_confirmation": True,
    }
    assert lock["identity"] == {
        "public_url": EXPECTED_KEYCLOAK_PUBLIC_URL,
        "admin_api_base_url": EXPECTED_KEYCLOAK_PUBLIC_URL,
        "issuer": EXPECTED_KEYCLOAK_ISSUER,
        "jwks_uri": EXPECTED_KEYCLOAK_JWKS_URI,
        "realm": "codestra",
        "admin_authentication_realm": "master",
        "client_id": "monitoring-readonly",
        "audience": "middleware-api",
        "metrics_scope": "metrics.read",
        "health_scope": "health.read",
        "maximum_token_ttl_seconds": 300,
        "token_values_committed": False,
        "production_identity_endpoint_allowed": False,
    }
    assert lock["activation"] == {
        "prometheus_target": "pending",
        "blackbox_target": "pending",
        "production_authorized": False,
    }
    assert lock["external_effects_enabled"] is False
    for value in lock["support_images"].values():
        assert re.fullmatch(r"[^\s]+@sha256:[0-9a-f]{64}", value)

    compose = yaml.safe_load((DEPLOY / "compose.yaml").read_text())
    services = compose["services"]
    assert set(services) == {"postgres", "redis", "middleware-migrate", "middleware"}
    assert services["middleware"]["image"] == lock["middleware"]["image_reference"]
    assert services["middleware-migrate"]["image"] == lock["middleware"]["image_reference"]
    assert "ports" not in services["middleware"]
    assert services["middleware"]["expose"] == ["8080"]
    assert compose["networks"]["private"]["internal"] is True
    assert services["postgres"]["image"] == lock["support_images"]["postgres"]
    assert services["redis"]["image"] == lock["support_images"]["redis"]
    assert set(compose["volumes"]) == {"postgres_data", "postgres_tls", "redis_data"}

    for name in ("postgres", "redis"):
        service = services[name]
        assert service["cap_drop"] == ["ALL"]
        assert set(service["cap_add"]) == {"CHOWN", "DAC_OVERRIDE", "FOWNER", "SETGID", "SETUID"}
        assert service["read_only"] is True
        assert "no-new-privileges:true" in service["security_opt"]
    assert POSTGRES_HOST in services["postgres"]["networks"]["private"]["aliases"]
    assert REDIS_HOST in services["redis"]["networks"]["private"]["aliases"]
    postgres_command = services["postgres"]["command"][0]
    redis_command = services["redis"]["command"][0]
    for required in ("ssl=on", "ssl_cert_file", "ssl_key_file", "hba_file", "docker-entrypoint.sh"):
        assert required in postgres_command
    for required in ("--tls-port 6379", "--port 0", "--aclfile /data/users.acl", "setpriv --reuid=redis"):
        assert required in redis_command
    middleware_mounts = services["middleware"]["volumes"]
    assert any("ca-certificates.crt:ro" in value for value in middleware_mounts)

    script = (ROOT / "scripts/deploy_intake_observability_staging.sh").read_text()
    for required in (
        "docker pull \"$image\"",
        "host ports are prohibited",
        "STAGING_DEPLOYMENT=PASS",
        "RUNTIME_PROFILE_ID=$EXPECTED_PROFILE",
        "sslmode=verify-full",
        "rediss://middleware-staging:",
        "openssl x509 -in \"$cert\" -noout -checkhost",
        "OUTBOX_DISPATCH_ENABLED=false",
        "LIVE_PSTN_DIALING=false",
        "DATA_VOLUMES=PRESERVED",
        "DELETE_CODESTRA_STAGE6_STAGING_DATA",
        "EXPECTED_KEYCLOAK_PUBLIC_URL='https://auth-staging.codestra.co'",
        "EXPECTED_KEYCLOAK_ISSUER=\"${EXPECTED_KEYCLOAK_PUBLIC_URL}/realms/codestra\"",
        "EXPECTED_KEYCLOAK_JWKS_URI=\"${EXPECTED_KEYCLOAK_ISSUER}/protocol/openid-connect/certs\"",
        "KEYCLOAK_ISSUER=$EXPECTED_KEYCLOAK_ISSUER",
        "KEYCLOAK_JWKS_URI=$EXPECTED_KEYCLOAK_JWKS_URI",
        "keycloak_public_url",
        "keycloak_issuer",
    ):
        assert required in script, required
    assert "https://auth.codestra.co" not in script
    assert script.count("compose down --volumes --remove-orphans") == 1
    assert script.count("compose down --remove-orphans") >= 3
    assert "compose down --volumes --remove-orphans >/dev/null 2>&1 || true" not in script
    assert "production-activation" not in script
    assert script.count("WEBHOOK_SECRET_") >= 7
    assert "REDIS_ACL_FILE" not in script
    print("INFRASTRUCTURE_STAGING_INTAKE_OBSERVABILITY=PASS")


if __name__ == "__main__":
    main()
