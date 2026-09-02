# Source API remediation — 2026-09-02

Production business writes and external effects remain disabled. These source
changes are not runtime or deployment evidence.

| Repository | Branch | PR | Exact head | Local test | Review | Runtime result | Remaining blocker |
|---|---|---:|---|---|---|---|---|
| `appolon1908-hue/Codestra-AI` | `production-api-runtime-completion-20260902` | [5](https://github.com/appolon1908-hue/Codestra-AI/pull/5) | `710e6e1327013f5633c1ee2a9cdf933d118f3653` | 9 PASS, PostgreSQL test requires CI service; gitleaks PASS | requested | NOT_DEPLOYED | exact-head CI, approval, merge, immutable build, staging/runtime evidence |
| `appolon1908-hue/Codestra-Communication-CC` | `production-api-runtime-completion-20260902` | [5](https://github.com/appolon1908-hue/Codestra-Communication-CC/pull/5) | `341e253ccc28f92dc8c2f769328a9996b450d540` | 7 PASS, PostgreSQL test requires CI service; gitleaks PASS | requested | NOT_DEPLOYED | exact-head CI, approval, merge, immutable build, staging/runtime evidence |
| `appolon1908-hue/Codestra-Marketing-` | `production-api-runtime-completion-20260902` | [5](https://github.com/appolon1908-hue/Codestra-Marketing-/pull/5) | `cb0343fb78176dea66ab3e1ee95853127ed66b2d` | 10 PASS, PostgreSQL test requires CI service; gitleaks PASS | requested | NOT_DEPLOYED | exact-head CI, approval, merge, immutable build, staging/runtime evidence and off-host TLS repair |
| `appolon1908-hue/Codesrea-Social-` | `production-api-runtime-completion-20260902` | [5](https://github.com/appolon1908-hue/Codesrea-Social-/pull/5) | `f1337324b8000c7908c074ab037dd6e312b9de95` | 7 PASS; gitleaks PASS | requested | NOT_DEPLOYED | exact-head CI, approval, merge, immutable build, staging/runtime evidence |

Each PR adds canonical `GET /health`, `GET /ready`, `GET /version`, and
`GET /capabilities` behavior with correlation/no-store headers, bounded
database readiness, non-secret attribution fields, preserved compatibility
aliases, and fail-closed capability readback.
