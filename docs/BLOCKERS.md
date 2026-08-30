# Codestra integration blockers

## I0-T1 — Email consent and suppression authority is unresolved

**Status:** R6 — owner decision required before `registry/systems.v1.json` can
assign a single tier for the email consent/suppression capability.

Two repositories currently claim and implement the same authority:

- `Codestra-Communication-CC` at
  `0ee0dcbd3d4a9405ffc7d14019bf4a1105f91113` describes itself as the
  customer-communications control plane in `README.md` and
  `docs/ARCHITECTURE.md`. Its application defines `communication_consents` and
  `communication_suppressions`, checks both before accepting marketing messages,
  and exposes consent/suppression endpoints.
- `klyrow.com` at `6ff3d5176dadf336d5b357723363bd1c171a0450`
  describes Klyrow as the commercial tenant/API control plane in
  `docs/KLYROW_CORPORATE_EMAIL_SAAS_COMPLETION_BLUEPRINT.md`. Its application
  defines and persists consent, preference, and suppression state, exposes the
  related APIs, and enforces those records in the public email submission path.

Assigning either repository `tier: control-plane` and the other `tier: runtime`
would be an architecture decision, not a fact discoverable from the current code.
Per the mission's collision doctrine, no registry entry has been invented.

### Decision required

The owner must name exactly one authoritative system for email consent,
preferences, and suppression, and define the other system's boundary. The
decision must also state how existing records, mutations, enforcement reads, and
change events are reconciled so neither send path can use stale or competing
authority.

## I0-T1 — Estate cardinality is internally inconsistent

**Status:** R6 — scope clarification required before the registry can contain the
mandated complete set.

The mission says the estate contains **16 systems plus 5 infrastructure
components** and requires **21 entries**. Its rollout lists a different total:

- I2: 5 systems;
- I3: 4 control planes;
- I4: 5 infrastructure repositories;
- I5: 11 remaining suites;
- I0 authority repository: `Infustruction-repo`.

Those groups contain 26 unique entries. The access table independently lists 10
reachable repositories and 5 private repositories, then I5 adds 11 more unique
suites, also totaling 26. There is no evidence identifying which five entries
should be excluded from a 21-entry registry.

### Decision required

Confirm either that `systems.v1.json` must contain all 26 named entries, or supply
the exact authoritative 21-entry list. No system has been silently omitted.

## Evidence and safe state

- Infrastructure baseline commit:
  `273395b07e2eba1111c9e2f6a80bf8384d104cfb`.
- `python scripts/certify_marketing_stage9.py`: pass.
- `PRODUCTION_WRITES_AUTHORIZED=NO` remains unchanged.
- No application code, registry, flag, workflow, or production setting changed.
- Work stopped during I0-T1; I0-T2 through I7 have not started.
