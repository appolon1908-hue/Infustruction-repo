# Independent build-context regression evidence

The coordinated infrastructure PR #85 added explicit container layout in commit
`7db424a47c5556dd473268fa484665c0bb5ee215` while this session was reviewing the
same failure. That implementation is adopted unchanged. This PR now adds only
independent tests, their CI job and this evidence; it does not introduce a
second workflow input contract. Earlier local implementation history is
superseded by the canonical workflow at that commit.

Observed failure: Vicidialer-Codestra run `33960984914`, attempt 1, job
`101292726625`, source `d2165e0615953de296dc80edab989f17137f7f45`.
Docker COPY could not find `/vicidial/docker/security_regression.py` or other
repository-root inputs because context was `vicidial/docker`. The failure
preceded scanning, publishing, signing and attestation. It was not a libuuid
scan failure. The same build path omitted required SOURCE_SHA and BUILD_DATE.

Canonical inputs are `dockerfile_path: vicidial/docker/Dockerfile` and
`docker_build_context: .`. The repair supplies exact Git-derived build metadata.
Review and protected promotion of PR #85 and the consumer pin remain necessary.
No earlier PR image substitutes for a signed protected-source release.

These tests execute the actual immutable-candidate workflow shell with a fake
Docker binary, checking root context, exact metadata, backward-compatible
layout discovery, missing paths, URL rejection, traversal and symlink escape.
No Docker build, registry mutation, signing, deployment or account operation
occurs. The historical source-CI build path is not certified by these tests.

Run: `python3.11 -m unittest discover -s tests -p test_deploy_readiness_build_context.py -v`.

Failure evidence: https://github.com/appolon1908-hue/Vicidialer-Codestra/actions/runs/33960984914/job/101292726625
