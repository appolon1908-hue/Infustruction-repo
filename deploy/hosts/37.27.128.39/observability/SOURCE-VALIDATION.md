# Repository-phase validation

Date: 2026-09-02

Target: `37.27.128.39`

Status: `REPOSITORY_VALIDATION_PASS_RUNTIME_NOT_TOUCHED`

## Results

```text
OBSERVABILITY_SOURCE_VALIDATION=PASS
PRINCIPAL_SERVICES=14
PUBLIC_NATIVE_PORTS=0
DIRECT_NORMAL_ALERTMANAGER_SMTP=DISABLED
ALERT_ADMIN_EMAIL=appolon@codestra.co
PYTHON_COMPILE=PASS
SHELL_SYNTAX=PASS
UNIT_TESTS=8_PASS
YAML_PARSE=PASS
JSON_PARSE=PASS
SERVER_CONNECTIONS=0
DNS_MUTATIONS=0
SMTP_MESSAGES_SENT=0
RUNTIME_MUTATIONS=0
```

The local execution environment did not contain the Docker CLI, so the
repository workflow performs the authoritative `docker compose config`
validation on GitHub-hosted CI with synthetic immutable digests. Runtime
validation still fails closed until all real image and rollback digests,
external networks, secret files, backups, and OpenBao security-owner gates are
satisfied.
