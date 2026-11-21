# B232: B231 authentic GTO vs NL2 river-donk50 actor/line zero-combo root cause

B216 original full GTO flop remains SHA-fixed, LMP 169-class preflop ranges ASSUMED.
B231 true GTO and NL2 partially locked turn/river differ from original river tree by a preregistered 50%-pot donk option.
Full per-combo ancestry uses the maximum-frequency action or alternative >=40% and >=70% of the highest; never silently relax this gate.

## gto
Rust nodes 28, raw correct actor target nodes 2, source combos 514, strict combos 0.
Diagnostic: **TARGET_SOURCE_COMBOS_REMOVED_BY_40_70_PREVIOUS_ACTION_GATE**.

## exp_oop
Rust nodes 28, raw correct actor target nodes 2, source combos 247, strict combos 0.
Diagnostic: **TARGET_SOURCE_COMBOS_REMOVED_BY_40_70_PREVIOUS_ACTION_GATE**.

See JSON for all exact lines, seats and nearest turn-to-river nodes.
No source data was fabricated or relabeled as measured conditional NL2 hand frequencies.
B232 is a diagnostic checkpoint, not a new solve or a third certified flop.
V38 151 CERT/241 APPROX/0 EST unchanged; all 581 existing locks and HU 2475/2475 must pass.
PR #2 stays Draft, NEVER MERGE.
