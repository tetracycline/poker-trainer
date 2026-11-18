# NL2 HU lines — scope and unresolved acceptance gates

Baseline: `d5c4932` (2026-11-18). This change is intentionally **not** a claim of full acceptance.

## Implemented
- The NL2 in-browser dataset excludes `sp === 'mw'` before reachability/title rendering, removing multiplayer pot tables and multiplayer drill choices.
- Fixed columns: 頂對好 / 頂對弱 / 中小對 / 強聽 / 弱聽, including empty cells where the source class is unreachable. No 兩對+ or 空氣 column.
- Existing board rows remain in this exact sequence: 9 以下低牌面 / J/T 高面 / K/Q 高面 / A 高面 / 成對面 / 單色面.
- Preserves existing next-street main links, same-street secondary links and source-based reachability rules; changes do not fabricate strategy data.

## Review requirements still open
1. **100% river coverage is not achieved.** The supplied baseline `LINK_AUDIT_2112.md` reported 2,971 / 9,338 (31.8%) continuing flop/turn cells reaching a river table. Those baseline values include multiplayer and are **not** the filtered HU-only result. Re-run audits for this branch before asserting a new ratio.
2. Missing HU nodes (examples): `ipfr/t_delay` bet/check-to-river, `opfr/t_delay`, `bb/t_first` bet/call-to-river, and several post-raise-call paths. These need authentic `tetracycline/poker-solver` solutions, not guessed links.
3. Exact combo-weight reachability by bet size requires a solver-derived hand-range transition, not solely `small/big` bucket checks. 40%-and-70%-of-max threshold is already encoded in the baseline approximation, but cannot establish exact GTO reachability by itself.
4. Facing-size boundaries on flop/turn remain unavailable where the source dataset lacks sized response rows.
5. Low-confidence exploitation cells in both reviews remain unsupported by new solver runs and should not be certified as solved.

## Independent checks required for final PASS
- `node tools/link_audit.js --md /tmp/nl2_link_audit.md --json /tmp/nl2_links.json`
- `node tools/reach_verify.js --log /tmp/nl2_reach.md --json /tmp/nl2_reach.json`
- Verify every table contains exactly six board rows in order, five fixed hand columns, zero `mw` nodes.
- Calculate denominator from *reachable, nonterminal, HU flop/turn cell-actions*; require 100% actual next-street-to-river coverage; count missing solver nodes as failures, not terminals.
- Inspect main-link street/pot lineage, same-street raise links, back-links, board reclassification for K72→A, K72→7 and 862→T.
- Store solver config, convergence/exploitability, exact node and combo reachability, output hashes, and source provenance with each newly solved node.

Do not merge as accepted until missing official solver runs, exact reachability and 100% river linkage are demonstrated.
