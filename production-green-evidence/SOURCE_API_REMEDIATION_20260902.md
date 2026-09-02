# Source API remediation — 2026-09-02

Production business writes and external effects remain disabled. These source
changes are not runtime or deployment evidence.

| Repository | Branch | PR | Exact head | Local test | Review | Runtime result | Remaining blocker |
|---|---|---:|---|---|---|---|---|
| `Codestra-SRL/codestra-middleware` | `production/api-runtime-completion-20260902` | [282](https://github.com/Codestra-SRL/codestra-middleware/pull/282) | `a397f6084703472ae2fbfb1995cc5508bddabe39` | 15 PASS; ruff and staged gitleaks PASS | requested | NOT_DEPLOYED | exact-head CI, approval, merge, immutable build, staging/runtime evidence |
| `appolon1908-hue/Codestra-AI` | `production-api-runtime-completion-20260902` | [5](https://github.com/appolon1908-hue/Codestra-AI/pull/5) | `ba09d25618e1d73f29cd76a51d658f2b0b0d09a6` | 9 PASS, PostgreSQL test requires CI service; gitleaks PASS | requested | NOT_DEPLOYED | exact-head CI, approval, merge, immutable build, staging/runtime evidence |
| `appolon1908-hue/Codestra-Communication-CC` | `production-api-runtime-completion-20260902` | [5](https://github.com/appolon1908-hue/Codestra-Communication-CC/pull/5) | `ec56638cbf543f02ad960c3647e74481d5a5bbb1` | 7 PASS, PostgreSQL test requires CI service; gitleaks PASS | requested | NOT_DEPLOYED | exact-head CI, approval, merge, immutable build, staging/runtime evidence |
| `appolon1908-hue/Codestra-Marketing-` | `production-api-runtime-completion-20260902` | [5](https://github.com/appolon1908-hue/Codestra-Marketing-/pull/5) | `4a7c0277d831e658ed3ed77ef9bf331171c0b819` | 10 PASS, PostgreSQL test requires CI service; gitleaks PASS | requested | NOT_DEPLOYED | exact-head CI, approval, merge, immutable build, staging/runtime evidence and off-host TLS repair |
| `appolon1908-hue/Codesrea-Social-` | `production-api-runtime-completion-20260902` | [5](https://github.com/appolon1908-hue/Codesrea-Social-/pull/5) | `c55ae6dad3f7fc143abda1c94c25dac4c62b050e` | 7 PASS; gitleaks PASS | requested | NOT_DEPLOYED | exact-head CI, approval, merge, immutable build, staging/runtime evidence |

Each PR adds canonical `GET /health`, `GET /ready`, `GET /version`, and
`GET /capabilities` behavior with correlation/no-store headers, bounded
database readiness, non-secret attribution fields, preserved compatibility
aliases, and fail-closed capability readback.

Klyrow restricted deployment PR
[66](https://github.com/appolon1908-hue/klyrow.com/pull/66) is at exact head
`f46b92cb279f0299a8d8e7a9bdbecb6ad077e04d`. The focused restricted-deploy
and reproducible-image contract suite passes 11/11. Exact-head CI is running;
independent approval and merge remain required. No Klyrow runtime action has
been performed.
