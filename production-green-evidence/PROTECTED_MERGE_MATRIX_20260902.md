# Protected merge matrix — 2026-09-02

Captured at `2026-09-02T16:45:12Z` from GitHub. All eight heads are current
with their protected base (`behind=0`). Repository auto-merge is disabled for
all eight repositories, so no auto-merge request can be queued. No commit in
the PR set has a GitHub signature object; current rules do not report signature
failure as a merge-state blocker.

| Repository | PR | Exact head | Base SHA | Merge state | Checks | Review | Threads | Blocker |
|---|---:|---|---|---|---|---|---:|---|
| `Codestra-SRL/codestra-middleware` | 282 | `a397f6084703472ae2fbfb1995cc5508bddabe39` | `61e5948f9c800f4dd587cce75a332b617f418a0c` | MERGED `c8c8d6fad442e7a65eeac353a0f0853797ea84a8` | no protected contexts reported | gates satisfied | 0 | NONE |
| `appolon1908-hue/Odoo` | 58 | `c438011f9945c823174574cd82e4e355df22dfdc` | `2015c682c0b6e37b306d8a2b75ee025578637b2e` | BLOCKED | 4 pass, runtime pending | `kazan555` requested; no exact-head approval | 0 | CHECKS_PENDING |
| `appolon1908-hue/Codestra-AI` | 5 | `9d141379a9f355c8dbbee56214be4129e9c9f66b` | `94d990e269b3a8cdc8176088be65dd02fdac37ea` | MERGED `1832d19eb779146beaf7aa9ead17aac4f502beb7` | 2 pass | findings fixed | 0 | NONE |
| `appolon1908-hue/Codestra-Communication-CC` | 5 | `ec56638cbf543f02ad960c3647e74481d5a5bbb1` | `0ee0dcbd3d4a9405ffc7d14019bf4a1105f91113` | MERGED `cceb1fd7462f765e6ac36db154086d56a88ba712` | 2 pass | gates satisfied | 0 | NONE |
| `appolon1908-hue/Codestra-Marketing-` | 5 | `4a7c0277d831e658ed3ed77ef9bf331171c0b819` | `460ff98f64ef9f0724fe4d2afc51a1a6c5b053dd` | MERGED `3f78cbdeccbdd69f1dfa7f4d31232b43e798047a` | 2 pass | gates satisfied | 0 | NONE |
| `appolon1908-hue/Codesrea-Social-` | 5 | `9479a3bc59bd8f809e052c191fe138f72da4531c` | `7bc0dd9ee8a13abbd1463ca106629ad63d957145` | MERGED `1323a7335e1724a00406aeadd1fec4c8e8af5f1a` | 2 pass | findings fixed | 0 | NONE |
| `appolon1908-hue/klyrow.com` | 66 | `f46b92cb279f0299a8d8e7a9bdbecb6ad077e04d` | `27c920957e116ae7fe998395393adc3c3dfdb6be` | BLOCKED | 4 pass | `kazan555` requested; no exact-head approval | 0 | CODEOWNER_APPROVAL_PENDING |
| `appolon1908-hue/Infustruction-repo` | 60 | `dba2544ba458bf042c4db0f8fbb077839645eb2c` | `cae843886a6ece21025b730de458dd14a47a9f51` | BLOCKED | 2 pass | `kazan555` requested; no exact-head approval | 0 | CODEOWNER_APPROVAL_PENDING |

The Odoo head changed after the starting evidence SHA through two externally
authored commits that address the valid deployed-gate review finding. This
matrix records the live GitHub head and does not overwrite or rewrite it.

`PRODUCTION_BUSINESS_WRITES_ENABLED=NO`

`PRODUCTION_EXTERNAL_EFFECTS_ENABLED=NONE`
