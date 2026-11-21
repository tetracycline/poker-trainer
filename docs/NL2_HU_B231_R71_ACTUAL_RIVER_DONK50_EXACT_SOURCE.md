# B231 rank71 exact board, new permitted river-donk50 subgame

Original full-flop LMP 100bb GTO root from B216 run 44884042851 SHA pinned. The original target OOP river action was missing because the turn/river tree had no 50%-pot river donk. This separate experiment permits exactly one 50%-pot river donk, while retaining the original GTO flop state byte-identical.

Unrestricted opponent GTO turn/river and separately pooled-NL2-marginal-locked turn/river were recomputed in genuine pinned Rust; this does NOT reoptimize earlier streets or prove a fully game-tree GTO flop under the expanded river menu. Limped preflop 169-class ranges remain assumed, not measured.

Exact actor-OOP river match (GTO/EXP): 0/0 combos; paired=False. Never substitute unknown hole-card NL2 frequencies with pooled marginals.

PR#2 remains Draft, NEVER MERGE. V38 remains 151 CERT/241 APPROX/0 EST pending an independent three-board promotion gate and original/tree comparability.
