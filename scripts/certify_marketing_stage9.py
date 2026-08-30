#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'config/marketing-stage9-readiness.json'

EXPECTED_REPOS = {
    'Codestra-Marketing-', 'Codestra-AI', 'Codestra-Communication-CC', 'Codesrea-Social-',
    'Middleware-', 'Odoo', 'SDK-repository', 'N8N', 'Kong', 'Keycloak', 'social.codestra.co'
}
EXPECTED_FLOW = [
    'provider.test_lead',
    'kong.authenticated_ingress',
    'middleware.inbox.accepted',
    'marketing.attribution.recorded',
    'odoo.crm.lead_upserted',
    'n8n.workflow.received',
    'communication.dry_run_created',
    'odoo.outcome.recorded',
    'marketing.conversion_feedback_recorded',
]


def event(event_type: str, tenant_id: str, correlation_id: str, payload: dict) -> dict:
    semantic = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return {
        'event_id': hashlib.sha256(f'{event_type}:{tenant_id}:{semantic}'.encode()).hexdigest()[:32],
        'tenant_id': tenant_id,
        'event_type': event_type,
        'idempotency_key': hashlib.sha256(f'{tenant_id}:{event_type}:{semantic}'.encode()).hexdigest(),
        'correlation_id': correlation_id,
        'payload': payload,
    }


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert data['productionWritesAuthorized'] is False
    assert all(value is False for value in data['capabilities'].values()), 'all live capabilities must remain false'
    repos = {entry['repo'] for entry in data['repositories']}
    assert EXPECTED_REPOS == repos, f'repository manifest mismatch: {sorted(EXPECTED_REPOS ^ repos)}'
    assert data['syntheticFlow'] == EXPECTED_FLOW, 'stage9 flow order changed'
    assert len(data['stage9ExitRequiresExternalEvidence']) >= 7, 'external evidence blockers must remain explicit'

    tenant = 'tenant-stage9-synthetic'
    correlation = 'corr-stage9-synthetic-0001'
    lead = event('provider.test_lead', tenant, correlation, {'email': 'synthetic@example.invalid', 'source': 'meta-test'})
    ingress = event('kong.authenticated_ingress', tenant, correlation, {'source_event_id': lead['event_id']})
    inbox = event('middleware.inbox.accepted', tenant, correlation, {'source_event_id': ingress['event_id']})
    attribution = event('marketing.attribution.recorded', tenant, correlation, {'source_event_id': inbox['event_id'], 'campaign': 'synthetic'})
    crm = event('odoo.crm.lead_upserted', tenant, correlation, {'source_event_id': attribution['event_id'], 'external_writes': False})
    workflow = event('n8n.workflow.received', tenant, correlation, {'source_event_id': crm['event_id'], 'active': False})
    dry_run = event('communication.dry_run_created', tenant, correlation, {'source_event_id': workflow['event_id'], 'external_delivery': False})
    outcome = event('odoo.outcome.recorded', tenant, correlation, {'source_event_id': dry_run['event_id'], 'status': 'synthetic-qualified'})
    feedback = event('marketing.conversion_feedback_recorded', tenant, correlation, {'source_event_id': outcome['event_id'], 'provider_write': False})
    events = [lead, ingress, inbox, attribution, crm, workflow, dry_run, outcome, feedback]

    assert all(e['tenant_id'] == tenant for e in events)
    assert all(e['correlation_id'] == correlation for e in events)
    assert len({e['idempotency_key'] for e in events}) == len(events)
    assert dry_run['payload']['external_delivery'] is False
    assert feedback['payload']['provider_write'] is False
    print('MARKETING_STAGE9_SYNTHETIC_CERTIFICATION=PASS')
    print('PRODUCTION_WRITES_AUTHORIZED=NO')
    print('EXTERNAL_RUNTIME_EVIDENCE_REQUIRED=YES')


if __name__ == '__main__':
    main()
