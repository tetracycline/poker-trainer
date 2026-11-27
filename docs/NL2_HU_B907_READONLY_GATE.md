# B907 — failed read-only gate repair (2026-11-27)

B906 recovery independently passed source verification and full audits. Its 13-file detached archive was fast-forwarded as 08082a78b781c80a7df83108dd5ba0f67296aaa9, leaving the registry blob unchanged. The original B905 full audit succeeded; its mixed plan run failed on two inventory pages. The mixed B906 run had one successful screen and two failed readers. Do not describe either mixed run as PASS.

* B905 rank92: 8h7h3c/2c and /4c are frozen preflight jobs, **not cleared for native dispatch**. Other two plans failed with offset pagination changes. Repair those readers only, reusing saved roots.
* B906 rank104/105: 7d5c4c/8c has no common prior physical pair and original menu excludes b75. 5h4h3s failed on an incorrectly copied GTO SHA-256; pin exact artifact metadata (14792264343). 8h7h5c failed on changing artifact pagination. Repair only these two failed readers, not the successful screen.
* A moving offset list is explicitly incomplete; duplicates and count changes are recorded. Even stable metadata cannot clear expired/unnamed sources. No native solve, no promotion, no dispatch clearance, no successful native work rerun. Archive individual successful ZIPs with metadata and verified job bytes. Detached archive candidate requires full audit and a later external expected_sha fast-forward.

Prior baseline: 158 CERT / 234 APPROX; 84.700987% model opportunity coverage (not unique hands); 30 >=0.2% per-hand candidates. B907 has no new formal cert/lock/nonpolarized result. Preserve draft/open PR #2.
