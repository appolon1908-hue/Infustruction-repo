# Server B observability authority

This directory is the sole repository authority for the twelve-product
observability mission on `37.27.128.39`. Generate and validate its sanitized
evidence with:

```bash
python3 hosts/37.27.128.39/observability/generate_evidence.py
python3 hosts/37.27.128.39/observability/validate.py
```

The current record is deliberately fail-closed. It commits no credential,
private key, recovery material, environment file, runtime state, or customer
data. No deployment may consume this authority until `activation_allowed` is
true in a reviewed protected release and all referenced source/image locks are
exact and immutable.

The approved future release layout is recorded in `release-layout.json`.
Direct edits beneath `/opt/codestra/current`, live Compose/configuration paths,
or application source directories are forbidden.
