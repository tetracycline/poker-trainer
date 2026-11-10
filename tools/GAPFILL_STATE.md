# NL2 gap-fill state (updated by Grok Bot; times Taipei)
Logs/briefs: /workspace/outputs/poker_lines_v2 (BRIEF6-8.md, codex_run6-8.log, CODEX_LOG.md, results/run6_report.md, run7_report.md)
Live check script: /workspace/scratch/live_check.py <url> <N per filter>

## Done
- Run 6 (Codex, ~09:08-09:55): HU turn/river nodes solved; 431 -> 1177 rows; HW cov 56.6% -> 72.3%; QA gates added (tools/lines_contract.py, qa_all.py, tools/e2e_lines.js). Side effect: mw emptied, 80 pool rows dropped.
- Run 7 (~10:00-10:30): 37 HU pool rows restored with GTO baseline -> 1179 rows (gto 1109 / pool 70). mw still 0 rows.
- Reviewer local browser check (working tree, run-7 state): all HU spots + all + riv: 0 blank cells, every question shows every street. Only failure: mw has no question.

## Done (cont.)
- Run 8 DONE ~10:50: 1185 rows; mw 6 river rows (pool, closing calls); mw flop/turn not rendered (note shown); ev text fixed; data QA 0, e2e 0. Header text already updated.

## Running
- (none) — was: Run 8 (Codex, nohup, pid in `pgrep -f "codex exec"`, log codex_run8.log, started 10:36): mw river facing-bet rows via HU rvW pool method; mw unrendered-node note; spot-specific ev text; QA+e2e 0 failures; results/run8_report.md.

## Next
1. Reviewer: local browser check + full qa_all.py (browser) on working tree.
3. DONE: sw poker-v9-1106a, full qa_all 0 failures, local browser check 0 failures, commit 5b50e05 pushed.
4. Verify live files match local (sha), run live_check.py on live URL (N=40), e2e_lines.js with live URL.
5. Report to parent.

## FINAL (11:xx Taipei): live files sha-match; live browser check (40 q/filter, 9 filters) 0 failures; e2e_lines.js on live URL 0 failures. Open item: mw flop/turn + most mw river classes not rendered (no multiway solver; HW-only samples n<40). Awaiting HW decision.

## Phase 2 — multiway approximation (HW chose 11/6 11:02: fill mw with 2-player solver approximations, labelled 「GTO 近似（兩人 solver）」)
- Run 9c DONE ~12:2x: 126 mw cells (role-split, realistic SPR 10–13), 4 pool; cov 2910/2910. Reviewed OK. Next: full QA + local browser check, sw bump, commit, live check.
- Next: review run 9 -> full qa_all + local browser check -> bump sw -> commit/push -> live sha check -> live_check.py (40 q/filter) + e2e_lines.js live -> report
- 11:52 local browser check (40 q/filter incl mw) 0 failures. Full qa_all.py running nohup -> /tmp/qa_full2.log (pid 3316970).
- full qa_all 0 failures (17186 q). sw poker-v9-1106b, commit 83fe644 pushed. Next: live sha + live checks.
- 12:10 DONE: live sha match; live browser 40q x 9 filters 0 failures; e2e live 0 failures. Reported.

## Phase 3 — definitions (HW t652u) + bb f_vs_xr sanity (parent steering 12:23)
- Found: site labels 「J–9 高面」「8 以下低牌面」 disagree with code (mid_high = T/J high, low = 9-high or lower). Two hand classifiers mixed: legacy ~321 GTO + 23 LD pool rows use handclass.py (TPG kicker T+, A-top 9+); run6+ rows use common.hcls (J+).
- HW's pasted table = bb f_vs_xr; mixes donk->raised with check-raise->jammed; near-zero-reach suspicion.
- Running: Codex run 10 (BRIEF10.md, nohup, /workspace/outputs/poker_lines_v2/codex_run10.log) for A (vs-raise nodes) + B (one classifier, classifier_spec.md). Codex must not touch nl2.js/qa_all.py.
- Me (in parallel): definitions panel + tap tooltips in nl2.js, QA label-definition check in qa_all.py.
- Next: after run 10 -> fill definitions from classifier_spec.md, QA full, browser check, sw bump, commit, live check.
- DONE (me): defs.js (all definitions, verified examples against common.hcls/vclass.texture/ctype), nl2.js tap-to-define (data-df spans on th/cond parts/basis tags, bottom popover #dfp, 定義 <details> on lines page + drill answer), nl2.html CSS + script tags (defs.js, v=1106c), sw.js file list + defs.js (cache name not bumped yet), tools/defs_check.js + qa_all.py check_defs(). QA currently fails only on 「J–9 高面」「8 以下低牌面」 (wrong labels; fix TX in build_lines.py to 「J/T 高面」「9 以下低牌面」 after run 10 finishes, then rebuild).
- 13:04 run 10 still running (BB donk lock subgames done, 372 river reaggregations done; legacy rows reclassified; 3bp turn-barrel pool claim falls back to GTO).
