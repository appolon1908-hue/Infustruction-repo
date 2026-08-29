# Observability and Dashboard Infrastructure Authority

## Purpose

This infrastructure repository owns shared deployment/topology definitions for the observability and analytics software supporting the Codestra communications platform. Application-specific instrumentation stays in each principal application repository.

## Approved supporting stack

### Metrics
- Prometheus
- Alertmanager
- Node Exporter
- cAdvisor
- PostgreSQL exporters
- Redis exporters where needed
- Blackbox Exporter

### Visualization / operations
- Grafana OSS

### Logs
- Loki

### Distributed tracing
- Tempo

### Instrumentation / telemetry transport
- OpenTelemetry Collector

### Business analytics
- Apache Superset

## Environment model

Maintain separate configuration and data boundaries for:
- development
- staging
- production

Production and staging should not share the same persistent telemetry stores when avoidable. Secrets and credentials must be injected externally and never committed.

## Network policy

- Grafana and Superset should be behind authenticated ingress.
- Prometheus, Loki, Tempo, Alertmanager, exporters and OpenTelemetry Collector administrative/internal endpoints should remain private unless an explicitly reviewed use case requires otherwise.
- Database exporters use least-privilege monitoring credentials only.
- No observability component receives unrestricted provider administration credentials.

## Data security

Do not collect or persist:
- Authorization headers
- access/refresh tokens
- SMTP/SMPP/provider passwords
- private keys
- webhook signing secrets
- raw payment information
- message bodies or recordings unless separately approved and access-controlled

Standard correlation fields may include tenant-safe identifiers, correlation IDs, command/message IDs, service, environment and sanitized provider result codes.

## Availability and retention

Define explicit retention for metrics, logs, traces and analytics. Retention must be capacity-tested and compatible with backup/restore policy. High-cardinality labels must be controlled.

## Dashboard separation

- Grafana: operational monitoring, incidents, infrastructure/service health.
- Superset: business and communications analytics from curated read models.
- Purpose-built admin UI: controlled workflows and actions through Kong -> Middleware.

Grafana or Superset must never become an alternate write path to Postal, Jasmin, VICIdial/Asterisk, Odoo or provider databases.

## Deployment gates

Before production deployment:
1. validate configuration from clean checkout;
2. pin image versions/digests;
3. scan for secrets;
4. prove authentication and private-network boundaries;
5. validate data-source credentials are least privilege;
6. validate retention/capacity;
7. validate backup and restore where state is material;
8. test alert delivery;
9. verify dashboards against staging data;
10. record exact source and image identities;
11. obtain explicit production approval.

## Source ownership

This repository owns shared deployment definitions and runbooks only. Metric names, traces and service-specific log policies are defined with each owning service repository and coordinated through `communication-platform-`.