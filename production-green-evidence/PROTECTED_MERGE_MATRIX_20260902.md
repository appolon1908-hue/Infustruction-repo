# Protected merge matrix — 2026-09-02

Captured at `2026-09-02T16:45:12Z` from GitHub. All eight heads are current
with their protected base (`behind=0`). Repository auto-merge is disabled for
all eight repositories, so no auto-merge request can be queued. No commit in
the PR set has a GitHub signature object; current rules do not report signature
failure as a merge-state blocker.

| Repository | PR | Exact head | Base SHA | Merge state | Checks | Review | Threads | Blocker |
|---|---:|---|---|---|---|---|---:|---|
| `Codestra-SRL/codestra-middleware` | 282 | `a397f6084703472ae2fbfb1995cc5508bddabe39` | `61e5948f9c800f4dd587cce75a332b617f418a0c` | CLEAN | no protected contexts reported | none required | 0 | NONE |
| `appolon1908-hue/Odoo` | 58 | `c438011f9945c823174574cd82e4e355df22dfdc` | `2015c682c0b6e37b306d8a2b75ee025578637b2e` | BLOCKED | 4 pass, runtime pending | `kazan555` requested; no exact-head approval | 0 | CHECKS_PENDING |
| `appolon1908-hue/Codestra-AI` | 5 | `ba09d25618e1d73f29cd76a51d658f2b0b0d09a6` | `94d990e269b3a8cdc8176088be65dd02fdac37ea` | CLEAN | 2 pass | none required | 2 | UNRESOLVED_VALID_THREAD |
| `appolon1908-hue/Codestra-Communication-CC` | 5 | `ec56638cbf543f02ad960c3647e74481d5a5bbb1` | `0ee0dcbd3d4a9405ffc7d14019bf4a1105f91113` | CLEAN | 2 pass | none required | 0 | NONE |
| `appolon1908-hue/Codestra-Marketing-` | 5 | `4a7c0277d831e658ed3ed77ef9bf331171c0b819` | `460ff98f64ef9f0724fe4d2afc51a1a6c5b053dd` | CLEAN | 2 pass | none required | 0 | NONE |
| `appolon1908-hue/Codesrea-Social-` | 5 | `c55ae6dad3f7fc143abda1c94c25dac4c62b050e` | `7bc0dd9ee8a13abbd1463ca106629ad63d957145` | CLEAN | 2 pass | none required | 3 | UNRESOLVED_VALID_THREAD |
| `appolon1908-hue/klyrow.com` | 66 | `f46b92cb279f0299a8d8e7a9bdbecb6ad077e04d` | `27c920957e116ae7fe998395393adc3c3dfdb6be` | BLOCKED | 4 pass | `kazan555` requested; no exact-head approval | 0 | CODEOWNER_APPROVAL_PENDING |
| `appolon1908-hue/Infustruction-repo` | 60 | `dba2544ba458bf042c4db0f8fbb077839645eb2c` | `cae843886a6ece21025b730de458dd14a47a9f51` | BLOCKED | 2 pass | `kazan555` requested; no exact-head approval | 0 | CODEOWNER_APPROVAL_PENDING |

The Odoo head changed after the starting evidence SHA through two externally
authored commits that address the valid deployed-gate review finding. This
matrix records the live GitHub head and does not overwrite or rewrite it.

`PRODUCTION_BUSINESS_WRITES_ENABLED=NO`

`PRODUCTION_EXTERNAL_EFFECTS_ENABLED=NONE`
