# B936 — B484 historical assembler version correction (no native dispatch)

B935 source audit 46137198199 and full batch audit 46137198176 succeeded, with two of four historical scopes proven (9 → 7); detached archive f388ef712d706d52264ad4ba01ffa894ebffad22 was fast-forwarded. Two historical runs remained blocked by the exact assembler blob mismatch.

- 45174796805: original checkout 6e305c61b113b36b54cba8fbaee404f57b3b1d69 and logged live-publish checkout a72af7df23b03fc00494fb0c38fe7582080b1ef4.
- 45151346459: original and live-publish checkout 7b31aa925fdb8747370595ae970bf7c5f82d10f8.

All three historical revisions were read directly and have assembler blob d06f54c24b89e1a5a52dc4b05e15cf07706cae40, not the later c73452c131d268e0d2b64ffb1565f0d06f186c33. Exact source comparison shows only earlier construction of the existing route contract and propagation of priced model SPR into registry and reference rows in the later version. This is a registry reconciliation difference, not native solver dispatch. The new gate requires the exact legacy blob at the three pinned revisions, checks the complete delta and all other original pins, and repeats original job, checkout, log, step, and artifact checks. Any mismatch stays blocked. No other historical run or candidate native identity is cleared. No promotion, lock, b50 addition or native rerun.

Still unresolved: B710 publication, native river import, B619, B595 and B331 workflows. All six continuation targets remain blocked until their respective boundaries and global historical deduplication are verified. Current model-weighted coverage is 84.700987% (158 CERT / 234 APPROX), not unique-hand coverage. Full static/model/route audit runs before any detached archive candidate. PR #2 remains open draft.
