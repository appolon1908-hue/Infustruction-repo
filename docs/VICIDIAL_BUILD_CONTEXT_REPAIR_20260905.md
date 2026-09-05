# VICIdial immutable-candidate build contract repair

Observed failure: Vicidialer-Codestra run `33960984914`, attempt 1, job
`101292726625`, source `d2165e0615953de296dc80edab989f17137f7f45`.
The build failed before vulnerability scanning, publishing, signing or attestation.
Docker COPY could not find `/vicidial/docker/security_regression.py` and other
repository-root inputs. This was a build-context failure, not a libuuid scan result.

The consumer pins reusable authority `1b4a90810eb03db3eae2b676b2d418daa434ec16`,
which selects the first Dockerfile and uses its parent directory as context.
The VICIdial Dockerfile lives in `vicidial/docker` but COPY references repository
root paths. It also requires SOURCE_SHA and BUILD_DATE, which this build path
did not pass. The existing dedicated container workflow passes those correctly.

This repair adds explicit Dockerfile/context inputs, preserving defaults for
existing callers, and derives build metadata from the exact checked-out commit.
Resolved paths must stay within the checkout. Both source-test and protected
candidate build paths use the same selection and metadata contract. Scanner
severity/exit codes, exact-source/clean-tree checks, signing, attestation and
protected deployment jobs are unchanged. Provenance records the new inputs.

VICIdial must select `dockerfile: vicidial/docker/Dockerfile` and
`build_context: .` at the repaired immutable workflow revision. Do not substitute
an earlier PR image for a newly built, scanned, signed protected-source release.

The reusable workflow is still under infrastructure PR #85; this fix is stacked
on its inspected head `f509d61a6207c7cd9e5f2562de0c2b32a85b6cca`. Both the
reusable authority and consumer changes need their review/protected-merge path.
No merge, deployment, workflow dispatch or production activation is performed.

Validation executes actual workflow shell through the Docker command with a
fake Docker executable. It checks root context, metadata, backward-compatible
discovery, missing paths, URLs, traversal and symlink escapes before build.
It does not claim an OCI build, scanner pass, digest or protected release.

```bash
python3.11 -m unittest discover -s tests -p test_deploy_readiness_build_context.py -v
```

Source evidence: https://github.com/appolon1908-hue/Vicidialer-Codestra/actions/runs/33960984914/job/101292726625
