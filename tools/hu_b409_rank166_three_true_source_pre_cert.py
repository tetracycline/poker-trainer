#!/usr/bin/env python3
"""B409 rank166 exact three-original-flop source-blind readiness; never promotes.
Original 100bb true GTO and actual pooled-NL2 IP Rust hero-lock same board/line,
strict full street 40%-70% legal combo reach and source SPR tolerance.
"""
import hashlib,json,pathlib
D=pathlib.Path("data")
PARENT=D/"nl2_hu_multiboard_status_v49_b405_rank214_219.json"
TRIAGE=D/"nl2_hu_b370_first10_approx_source_triage.json"
GTO=D/"nl2_hu_b400_five_cobb_gto_second_three_flops.json"
NL2=D/"nl2_hu_b407_r166_two_real_nl2_ip_original_pairs.json"
OUT=D/"nl2_hu_b409_rank166_three_true_source_flops_pre_cert.json"
DOC=pathlib.Path("docs/NL2_HU_B409_R166_THREE_TRUE_SOURCE_PRECERT.md")
RANK=166;MID="ln-ipfr-r_model-1spq1ko"
FLOPS=("Js9h4d","KcJh7d","QhTc5d")
LINE="x b100 c/x x/x"
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=read(PARENT);t=read(TRIAGE);g=read(GTO);n=read(NL2)
 assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(162,230,0,392)
 m=s["records"][MID]
 assert (m["label"],m["frequency_rank"],m["solver_profile"],m["family"],m["street"])==(
  "APPROX",166,"CO_BB","SRP",2)
 assert g["schema"]=="NL2_B400_FIVE_COBB_APPROX_THREE_FROZEN_ORIGINAL_GTO_ONLY_V1"
 assert (g["original_run_id"],g["models"]["166"]["exact_line"])==(45028060598,LINE)
 assert n["schema"]=="NL2_B407_RANK166_TWO_NEW_ACTUAL_RUST_GTO_NL2_IP_PAIRS_V1"
 assert n["B400_frozen_original_GTO_source_sha256"]==sha(GTO)
 assert (n["original_GTO_run"],n["new_NL2_IP_run"])==(45028060598,45029267778)
 assert (n["spot"],n["actor"],n["exact_line"])==("CO_BB","CO_IP",LINE)
 assert n["opponent_NL2_is_pool_marginal_proxy_not_exact_private_hand"]
 old=next(x for x in t["source_blind_selected_ten"] if x["frequency_rank"]==166)
 assert old["model_id"]==MID and old["true_paired_measured_NL2_hero_lock_flops"]==1
 historical=old["strictly_measured_pairs"][0]
 assert (historical["flop"],historical["exact_line"])==(FLOPS[0],LINE)
 assert historical["strict_legal_combo_count"]>0
 assert len(historical["gto_source_sha256"])==len(historical["nl2_hero_lock_sha256"])==64
 assert abs(historical["actual_spr"]-m["assumed_model_node_spr"])/historical["actual_spr"]<=.05
 eligible=n["new_distinct_qualifying_flops_by_rank"]["166"]
 assert set(eligible)==set(FLOPS[1:]),("No rank166 three-source promotion without 2 paired real Rust NL2 sources",eligible)
 pins=[dict(flop=historical["flop"],turn=historical.get("turn"),exact_public_board=historical["exact_public_board"],
    actor="CO_IP",exact_action_line=LINE,real_GTO_run=historical["gto_source_run_id"],
    actual_NL2_IP_run=historical["nl2_hero_lock_run_id"],
    genuine_GTO_sha256=historical["gto_source_sha256"],actual_NL2_IP_sha256=historical["nl2_hero_lock_sha256"],
    genuine_GTO_strict_40_70_combos=historical["strict_legal_combo_count"],
    actual_NL2_IP_strict_40_70_combos=historical["strict_legal_combo_count"],
    actual_spr=historical["actual_spr"],historical_immutable_verified_V47_source=True)]
 pairs=n["positive_40_70_named_river_pairs_by_rank"]["166"]
 for flop in FLOPS[1:]:
  eligible_pairs=[x for x in pairs if x["flop"]==flop]
  assert eligible_pairs
  best=sorted(eligible_pairs,key=lambda z:(-min(z["GTO_strict_40_70_combos"],z["actual_NL2_IP_strict_40_70_combos"]),
     -z["GTO_strict_40_70_combos"]*z["actual_NL2_IP_strict_40_70_combos"],z["exact_public_board"]))[0]
  assert (best["actor"],best["exact_history"])==("CO_IP",LINE)
  assert best["GTO_strict_40_70_combos"]>0 and best["actual_NL2_IP_strict_40_70_combos"]>0
  assert (best["original_GTO_source_run"],best["new_NL2_IP_source_run"])==(45028060598,45029267778)
  assert len(best["original_GTO_sha256"])==len(best["new_NL2_IP_sha256"])==64
  assert abs(best["actual_SPR"]-m["assumed_model_node_spr"])/max(1,best["actual_SPR"])<=.05
  assert any(q["flop"]==flop and q["public_board"]==best["exact_public_board"]
   and q["original_GTO_sha256"]==best["original_GTO_sha256"]
   and q["legal_full_street_40_70_combos"]==best["GTO_strict_40_70_combos"]
   for q in g["exact_actor_IP_positive_river_nodes_by_model"]["166"])
  pins.append(dict(flop=flop,turn=best["turn"],exact_public_board=best["exact_public_board"],
    actor="CO_IP",exact_action_line=LINE,real_GTO_run=45028060598,
    actual_NL2_IP_run=45029267778,genuine_GTO_sha256=best["original_GTO_sha256"],
    actual_NL2_IP_sha256=best["new_NL2_IP_sha256"],
    genuine_GTO_strict_40_70_combos=best["GTO_strict_40_70_combos"],
    actual_NL2_IP_strict_40_70_combos=best["actual_NL2_IP_strict_40_70_combos"],
    actual_spr=best["actual_SPR"],historical_immutable_verified_V47_source=False))
 assert [x["flop"] for x in pins]==list(FLOPS)
 out=dict(schema="NL2_B409_RANK166_THREE_TRUE_GTO_NL2_IP_SOURCE_READY_V1",
  source_V49_status_sha256=sha(PARENT),original_B370_historical_pair_sha256=sha(TRIAGE),
  original_B400_GTO_source_sha256=sha(GTO),new_B407_NL2_Rust_source_sha256=sha(NL2),
  model_id=MID,frequency_rank=166,spot="CO_BB",actor="CO_IP",exact_line=LINE,
  genuine_distinct_original_flops=list(FLOPS),original_paired_source_pins=pins,
  all_same_original_100bb_root_and_strict_actor_IP_40_70=True,
  source_blind_first10_preregistered=True,
  no_private_hand_conditional_NL2_observations_claim=True,
  no_generic_texture_or_unverified_50pct_sizing_claim=True,
  independent_raw_artifact_SHA_matrix_frontend_HU2475_gate_still_required=True,
  no_premature_Cert_upgrade=True,
  CERT_MULTIBOARD=162,APPROX=230,EST=0,TOTAL=392,PR2_Draft_NEVER_MERGE=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B409 rank166 original-three-flop pre-CERT evidence\n\n"
  "The three public flops Js9h4d, KcJh7d, QhTc5d are distinct and SHA-traced "
  "to actual full 100bb GTO and genuine partial NL2 IP Rust solvers with identical "
  "x b100 c/x x/x and 40%-70% full-street legal combo reach, matching actor CO-IP and SPR. "
  "B409 is source pre-cert ONLY, not a generic board/handclass GTO promotion. "
  "Opponent NL2 data are aggregate pool marginals with disclosed assumptions, not private-card conditional measurements. "
  "Independent root SHA reinspection and full HU2475 required for any future 163/229 registry change.\n")
 print("PASS B409 three truly paired original rank166 flops; no early promotion 162 CERT/230 APPROX")
if __name__=="__main__":main()
