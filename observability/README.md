# Observability integration control plane

This directory coordinates accepted artifacts from the principal component repositories. It
does not vendor their runtime source or duplicate component-owned configuration.

`integration-manifest.v1.json` is deliberately fail-closed. A component becomes deployable only
after its authority repository supplies reviewed configuration, an immutable image digest,
validation evidence, and an empty blocker list. The top-level deployment switch remains `false`
until staging acceptance and rollback evidence exist.

Validation:

```bash
node scripts/validate-observability-manifest.mjs
```

See `docs/OBSERVABILITY.md`, `docs/NETWORKING.md`, and `docs/SECURITY-BASELINE.md` for the
integration contract and rollout gates.
