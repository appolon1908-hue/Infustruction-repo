# Independent build-context regression evidence

The coordinated infrastructure PR #85 added explicit container layout in commit
`7db424a47c5556dd473268fa484665c0bb5ee215` while this session was reviewing the
same failure. That build-context implementation is adopted unchanged. This PR adds
independent tests, their CI job, this evidence and the UTC timestamp correction
described below; it does not introduce a second workflow input contract. Earlier local implementation history is
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

## Subsequent protected-build failure and minimal repair

The coordinated consumer fix merged as VICIdial PR #20 at
`c3f34f4f5adf23c1175c3c18a039a958f43ed4e3`. Its run `33962326270`, job
`101296261576`, passed COPY and failed `build_release_document` with:
`ValueError: built_at must be a UTC ISO-8601 timestamp ending in Z`.
The input was `2026-09-05T07:04:08-04:00` from Git `%cI`.

This follow-up now includes one additional production-workflow correction:
derive the same commit instant from `%ct` and format it in UTC ending in Z.
The release validator remains strict; no scanning or protection changes occur.
The regression fixture uses an explicit -04:00 commit, failed before the repair,
and passes afterward with `BUILD_DATE=2026-09-05T11:04:08Z`.

New failure: https://github.com/appolon1908-hue/Vicidialer-Codestra/actions/runs/33962326270/job/101296261576

Run: `python3.11 -m unittest discover -s tests -p test_deploy_readiness_build_context.py -v`.

Failure evidence: https://github.com/appolon1908-hue/Vicidialer-Codestra/actions/runs/33960984914/job/101292726625
