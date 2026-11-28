# B937 — historical witness import and B331 publication (no native dispatch)

B936 source audit 46142163297 and full audit 46142163220 both succeeded; immutable archive 9ccf01a8d2eec91587a473c7e26cc38f017543eb was fast-forwarded under its expected parent. Two B484 replay scopes cleared, 7 → 5.

This batch verifies only two historical workflows:
- 45195896854: read-only witness import at 5d4cc240b6a8ccddd95a78915c45539f80db6d90. Three replay logs (B613/B617/B624), exact importer and source pins, four source worker ZIPs and published archive members, original root artifact digests. B617 rank58 original native job identities remain in the denylist; no solve is rerun.
- 44961393736: B331 rank60 CO-IP existing publication at 12729fa2afbb8c20387f97b3fbdaf7f5468e7281, originally published b15ab39aa5b6bd43b6c3ecffee1915ae727a3172. Check immutable input pins, successful original runs, exact output artifact and source digests, rank60-only fourth-board update, and historical job log. This is not a rank58 SB-OOP continuation.

Failures remain blocked, including unavailable original ZIPs or unexpected archive member names. B710, B619, B595 remain open; all six candidate continuations stay blocked, including two with failed boundary checks. No native dispatch, no promotion, no lock or half-pot addition. Current 158 CERT / 234 APPROX; 84.700987% modeled node opportunity coverage, not unique-hand coverage. The full current audit runs before a detached archive candidate, which must be separately accepted with expected_sha. PR #2 stays open draft.
