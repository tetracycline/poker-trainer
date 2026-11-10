# Definitions + bb f_vs_xr fix — state (Taipei)
## Done
- defs.js (all label definitions; examples verified against common.hcls / vclass.texture / common.ctype), nl2.js tap-to-define + 定義 panel (lines page + drill answer), nl2.html CSS/script tags, sw.js list includes defs.js (cache name not bumped), tools/defs_check.js + qa_all.py check_defs().
- Found label bug: site showed 「J–9 高面」「8 以下低牌面」 but code: mid_high = top card J or T; low = 9 or lower. Codex run 10 changed TX labels in build_lines.py to 「J/T 高面」「9 以下低牌面」.
- HW table = bb f_vs_xr 「翻牌：你下注後被加注」 (run 6): mixed donk->raised-3x with check-raise->re-raised all-in; strategies from near-zero-reach donk nodes. Codex run 10 split into f_vs_xr / f_vs_3b (all spots), locked BB donk to HW rates, unified classifier (J+ kicker) for legacy rows. Run 10 stopped at Codex usage limit at final rebuild (reset ~16:11 Taipei).
- 13:10 I fixed build_lines.py cond_lab to label mw role (c.hr) -> 你是開池者/你是跟注者 (run 10 lost it -> 63 duplicate-cell QA failures).
## Remaining after run 10
- 3 blank cells: bb f_vs_3b 單色面 AIR, ipc f_vs_3b A 高面 TPG, opfr f_vs_3b 9 以下 AIR (no reliable/locked sample).
## Next
1. Rerun run10_finish.py myself (plain script, no Codex) -> check QA/e2e.
2. Decide on 3 gaps; review bb f_vs_xr before/after; action context visible.
3. Full QA, browser check, sw bump, commit, push, live check, report.
- 13:2x reran run10_finish.py myself: mw duplicate failures gone (cond_lab fix); defs_check 0 failures (29 labels); remaining = the 3 blank f_vs_3b cells (needs a locked solve -> Codex, out until ~16:11 Taipei).
- Added faceHtml in nl2.js: every node in the lines table shows 「你面對（例）：…，你要跟 Xbb（底池 Ybb）」 from its first complete example.
- STOPPED per instruction (Codex limit). Hand-off brief: /workspace/outputs/poker_lines_v2/BRIEF11_handoff.md. Nothing committed; live site still 83fe644.
- 13:16 parent: finish BRIEF11 myself (no Codex). Starting: study run10_rare/pair3b to run 3 locked solves.
- 13:18 running run11_gaps.py (nohup, log poker_lines_v2/results/run11_gaps.log): cold As8d3c re-raise tree + 4 locked solves (ipc cold, opfr 7s6h4d, bb CO_BB 8s7s2s & 7s6s3s).
- node title fix in run10_apply.py (vs_xr: flop/turn 「你先下注被加注（加注 3 倍或全下）」, river 「…（尺寸見題目）」).
- 13:5x REVIEW FINDING (serious): run10_river_extract published hero river nodes that were themselves locked to HW's own rates (731/744 river variants locked; e.g. bb r_vs_bet 強聽未中 "call 67.7%" = HW's own (33+.5)/(48+1.5)). Fix: for a locked variant, a node whose hist is in its lock set now takes the unlocked GTO ("original") node of the same river solve; only nodes downstream of the locks keep the locked model. Backup results/run11/run10_river_extract.py.bak. Flop/turn locked solves checked: targets are never locked nodes (ok).
- 13:28 run11 solves done: opfr low AIR filled (7s6h4d x b75 r a, fold 100%, joint 243); bb mono AIR filled (CO_BB 8s7s2s, fold 100%, joint tiny 0.0024). ipc A_high TPG: cold As8d3c re-solve with jam option — UTG never jams over CO's raise (joint 0). Fallback: exact equity of TPG combos vs the jam range of nearest locked solve f8f73e40d8fd (AsJh4h ipc) — run11_tpg_jam.py running.
- 13:38 ipc A_high TPG filled via exact all-in equity vs nearest solves' jam ranges (AK/AQ vs locked AsJh4h: 68–73% vs need 44–48%; HW's real TPG AJ vs GTO AsTh4d/AsTs7h: 44–51% vs 44–48%) → 跟 78%, with stated note; example AJ in UTG/CO cold spot. run10_finish: grid gaps 0, all 5 checks 0. Titles fixed (flop 3x/allin, turn mostly allin, river pot-size/allin). sw.js → poker-v9-1106c. Next: full qa_all (nohup), commit, push, live check.
- 06:06 full qa_all: 1 failure only = 4 快捷鍵 counted the 136 tappable definition spans (.df[data-df], role=button) as buttons without shortcuts. Definition taps are info popovers (same text in the keyboard-reachable 定義 panel), so qa_all now skips .df[data-df] in that check. Rerunning full QA (nohup /workspace/scratch/qa_full_1106c2.log).
- 06:07 local pre-checks: live_check.py on local server 0 failures (every tab, every drill filter); defs_check 0 failures. Waiting for full QA.
- 06:33 full QA 0 failures (17166 questions). Committed+pushed 533ffb8.
- 06:35 LIVE 533ffb8 verified: sha1 match 5 files; live_check 0 failures (all tabs/drill filters, cache poker-v9-1106c); e2e_lines 0; defs_check 0 (29 labels, 270 answers); 390×844 tap test 12/12 popovers; 16/16 facing-action lines visible; new titles live. BRIEF11 DONE.
