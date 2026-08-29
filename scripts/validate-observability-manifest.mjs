import assert from 'node:assert/strict';
import fs from 'node:fs';

const manifestPath = 'observability/integration-manifest.v1.json';
const manifestText = fs.readFileSync(manifestPath, 'utf8');
const manifest = JSON.parse(manifestText);
JSON.parse(fs.readFileSync('schemas/observability-integration-manifest.schema.json', 'utf8'));

const expectedComponents = [
  'grafana',
  'prometheus',
  'alertmanager',
  'loki',
  'tempo',
  'opentelemetry_collector',
  'superset',
  'node_exporter',
  'cadvisor',
  'postgres_exporter',
  'redis_exporter',
  'blackbox_exporter',
  'alloy',
  'openbao',
];

assert.equal(manifest.schema_version, '1.0');
assert.equal(manifest.deployment_enabled, false, 'the integration foundation must remain disabled');
assert.equal(manifest.infrastructure_authority, 'appolon1908-hue/Infustruction-repo');
assert.equal(manifest.application_authority, 'appolon1908-hue/kyqra-crawler');
assert.deepEqual(manifest.environments, ['development', 'test', 'staging', 'production']);
assert.deepEqual(Object.keys(manifest.components), expectedComponents);
for (const dependency of manifest.review_dependencies) {
  assert.match(dependency.repository, /^appolon1908-hue\/[A-Za-z0-9._-]+$/);
  assert.match(dependency.commit, /^[0-9a-f]{40}$/);
  assert.notEqual(dependency.status, 'accepted');
}

const hostnames = new Set();
let blockerCount = 0;

for (const [name, component] of Object.entries(manifest.components)) {
  assert.match(component.authority_repository, /^appolon1908-hue\/[A-Za-z0-9._-]+$/);
  assert.ok(['private_only', 'authenticated_https'].includes(component.exposure));
  assert.equal(component.configuration_ready, false, `${name} cannot be ready in the source-mirror audit`);
  assert.equal(component.image_digest, null, `${name} has no reviewed immutable image yet`);
  assert.equal(component.deployment_enabled, false, `${name} must remain disabled`);
  assert.ok(component.blockers.length > 0, `${name} must retain its concrete blockers`);
  blockerCount += component.blockers.length;

  if (component.source_commit !== null) {
    assert.match(component.source_commit, /^[0-9a-f]{40}$/, `${name} source commit is invalid`);
  }
  if (component.upstream_commit !== null) {
    assert.match(component.upstream_commit, /^[0-9a-f]{40}$/, `${name} upstream commit is invalid`);
  }
  if (component.candidate) {
    assert.match(component.candidate.commit, /^[0-9a-f]{40}$/, `${name} candidate commit is invalid`);
    assert.notEqual(component.candidate.status, 'accepted');
  }
  if (component.canonical_hostname !== null) {
    assert.match(component.canonical_hostname, /^[a-z0-9-]+\.codestra\.media$/);
    assert.ok(!hostnames.has(component.canonical_hostname), `${name} reuses a canonical hostname`);
    hostnames.add(component.canonical_hostname);
  }
}

assert.equal(manifest.components.postgres_exporter.source_commit, null);
assert.equal(manifest.components.openbao.upstream_commit, null);

const externalSources = new Set(['kyqra_crawler']);
for (const connection of manifest.connections) {
  assert.ok(
    Object.hasOwn(manifest.components, connection.from) || externalSources.has(connection.from),
    `unknown connection source: ${connection.from}`,
  );
  assert.ok(Object.hasOwn(manifest.components, connection.to), `unknown connection target: ${connection.to}`);
  assert.equal(connection.enabled, false, `${connection.from} -> ${connection.to} is not accepted yet`);
  assert.ok(connection.protocol.length > 0);
  assert.ok(connection.purpose.length > 0);
}

assert.ok(manifest.activation_gate.critical_or_high_findings_open > 0);
assert.equal(manifest.activation_gate.go_live, 'NO_GO');
for (const [key, value] of Object.entries(manifest.activation_gate)) {
  if (typeof value === 'boolean') {
    assert.equal(value, false, `${key} cannot be true in the preparation-only manifest`);
  }
}

for (const requiredPath of [
  'schemas/observability-integration-manifest.schema.json',
  'docs/OBSERVABILITY.md',
  'docs/NETWORKING.md',
  'docs/SECURITY-BASELINE.md',
]) {
  assert.ok(fs.existsSync(requiredPath), `${requiredPath} is required`);
}

const prohibitedSecretShapes = [
  /gh[oprsu]_[A-Za-z0-9]{20,}/,
  /AKIA[0-9A-Z]{16}/,
  /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
  /https:\/\/hooks\.slack\.com\/services\//,
  /(?:hvs|hvr|hvb|hvp)\.[A-Za-z0-9_-]{12,}/,
];
for (const pattern of prohibitedSecretShapes) {
  assert.doesNotMatch(manifestText, pattern, `manifest contains prohibited secret-shaped material: ${pattern}`);
}

console.log(`OBSERVABILITY_MANIFEST=PASS components=${expectedComponents.length} blockers=${blockerCount}`);
console.log('DEPLOYMENT_ENABLED=false');
console.log('GO_LIVE=NO_GO');
