# Server 37 isolated restore evidence

Observed at `2026-09-02T23:10:45Z` on `37.27.128.39`.

The root-only encrypted archives below passed checksum validation and restored
into temporary isolated targets with no public ports and no residual resources:

- Klyrow `20260902T225310Z`: application PostgreSQL, Mautic MariaDB, Postal
  MariaDB, configuration, release evidence, boot controls, and root-owned
  runtime configuration.
- Telnexa `20260902T203714Z`: core PostgreSQL, billing PostgreSQL, Keycloak
  PostgreSQL, Redis, RabbitMQ definitions, Jasmin state, and configuration.
- Kyqra `20260902T202803Z`: PostgreSQL, Redis, and configuration.

All restore commands returned `RESTORE_TEST=PASS`. This evidence does not claim
off-host coverage; that remains a separate failing gate.
