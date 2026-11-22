#!/usr/bin/env python3
"""B404 preregistration for rank214/219 exactly 3 distinct original GTO/NL2 IP flops.
Reads original source-only B393 and B396 proof; does NOT alter CERT before the
next independent raw SHA/actor/SPR/40-70/source matrix and UI audit.
"""
import hashlib,json,pathlib
D=pathlib.Path("data")
STATUS=D/"nl2_hu_multiboard_status_v48_b390_rank107.json"
B370=D/"nl2_hu_b370_first10_approx_source_triage.json"
B393=D/"nl2_hu_b393_five_cobb_gto_first_three_flops.json"
B396=D/"nl2_hu_b396_r214_219_two_real_nl2_ip_original_pairs.json"
OUT=D/"nl2_hu_b404_r214219_three_true_flop_pre_cert_gate.json"
DOC=pathlib.Path("docs/NL2_HU_B404_R214219_THREE_SOURCE_PRE_CERT.md")
TARGET={214:"ln-ipfr-r_model-1t7q0mn",219:"ln-ipfr-r_model-kp19if"}
FLOPS=("Js9h4d","KsQh4d","Js9h5d")
LINE="x b100 c/x b50 c/x"
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=read(STATUS);t=read(B370);g=read(B393);e=read(B396)
 assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(160,232,0,392)
 assert e["schema"]=="NL2_B396_RANK214_219_TWO_NEW_ACTUAL_RUST_GTO_NL2_IP_PAIRS_V1"
 assert (e["original_GTO_run"],e["new_NL2_IP_run"])==(45026396521,45027557999)
 assert e["B393_frozen_original_GTO_source_sha256"]==sha(B393)
 assert e["spot"]=="CO_BB" and e["actor"]=="CO_IP" and e["exact_line"]==LINE
 assert (e["source_poker_solver_pin"],e["original_Rust_pin"])==(
  "abe310c3aad02dd4a7c77fb2831801fd490cf51b",
  "9d1509fe5077d019825f833eed04b16d342dfda1")
 assert len(e["source_evidence"])==2
 assert {z["flop"] for z in e["source_evidence"]}==set(FLOPS[1:])
 assert e["opponent_NL2_is_pool_marginal_proxy_not_exact_private_hand"]
 source_pins={}
 for rank,model_id in TARGET.items():
  record=s["records"][model_id]
  assert (record["label"],record["frequency_rank"],record["solver_profile"],record["family"],record["street"])==(
   "APPROX",rank,"CO_BB","SRP",2)
  prior=next(z for z in t["source_blind_selected_ten"] if z["frequency_rank"]==rank)
  assert prior["model_id"]==model_id and prior["true_paired_measured_NL2_hero_lock_flops"]==1
  old=prior["strictly_measured_pairs"]
  assert len(old)==1 and old[0]["flop"]==FLOPS[0] and old[0]["exact_line"]==LINE
  assert old[0]["strict_legal_combo_count"]>0
  assert old[0]["gto_source_run_id"]>0 and old[0]["nl2_hero_lock_run_id"]>0
  assert len(old[0]["gto_source_sha256"])==len(old[0]["nl2_hero_lock_sha256"])==64
  assert abs(old[0]["actual_spr"]-record["assumed_model_node_spr"])/old[0]["actual_spr"]<=.05
  required=e["new_distinct_qualifying_flops_by_rank"][str(rank)]
  assert set(required)==set(FLOPS[1:]),("Uncertified second/third flop cannot be borrowed",rank,required)
  pairs=e["positive_40_70_named_river_pairs_by_rank"][str(rank)]
  assert pairs
  chosen=[dict(flop=old[0]["flop"],public_board=old[0]["exact_public_board"],
    GTO_run_id=old[0]["gto_source_run_id"],NL2_hero_IP_run_id=old[0]["nl2_hero_lock_run_id"],
    original_GTO_source_sha256=old[0]["gto_source_sha256"],NL2_IP_source_sha256=old[0]["nl2_hero_lock_sha256"],
    GTO_legal_40_70_hero_IP_combos=old[0]["strict_legal_combo_count"],
    NL2_IP_legal_40_70_hero_combos=old[0]["strict_legal_combo_count"],
    actual_spr=old[0]["actual_spr"],original_existing_V47_source=True)]
  for flop in FLOPS[1:]:
   variants=[z for z in pairs if z["rank"]==rank and z["flop"]==flop]
   assert variants
   z=sorted(variants,key=lambda y:(-min(y["GTO_strict_40_70_combos"],y["actual_NL2_IP_strict_40_70_combos"]),
     -y["GTO_strict_40_70_combos"]*y["actual_NL2_IP_strict_40_70_combos"],y["exact_public_board"]))[0]
   assert z["actor"]=="CO_IP" and z["exact_history"]==LINE
   assert z["GTO_strict_40_70_combos"]>0 and z["actual_NL2_IP_strict_40_70_combos"]>0
   assert (z["original_GTO_source_run"],z["new_NL2_IP_source_run"])==(45026396521,45027557999)
   assert len(z["original_GTO_sha256"])==len(z["new_NL2_IP_sha256"])==64
   assert abs(z["actual_SPR"]-record["assumed_model_node_spr"])/max(1,z["actual_SPR"])<=.05
   candidates=g["exact_actor_IP_positive_river_nodes_by_model"][str(rank)]
   assert any(v["flop"]==flop and v["public_board"]==z["exact_public_board"] and
    v["exact_action_line"]==LINE and v["original_GTO_sha256"]==z["original_GTO_sha256"] and
    v["legal_full_street_40_70_combos"]==z["GTO_strict_40_70_combos"] for v in candidates)
   chosen.append(dict(flop=flop,public_board=z["exact_public_board"],
    GTO_run_id=45026396521,NL2_hero_IP_run_id=45027557999,
    original_GTO_source_sha256=z["original_GTO_sha256"],
    NL2_IP_source_sha256=z["new_NL2_IP_sha256"],
    GTO_legal_40_70_hero_IP_combos=z["GTO_strict_40_70_combos"],
    NL2_IP_legal_40_70_hero_combos=z["actual_NL2_IP_strict_40_70_combos"],
    actual_spr=z["actual_SPR"],original_existing_V47_source=False))
  assert [p["flop"] for p in chosen]==list(FLOPS) and len({p["flop"] for p in chosen})==3
  source_pins[str(rank)]=dict(model_id=model_id,rank=rank,actor="CO_IP",spot="CO_BB",
   exact_action_line=LINE,three_authentic_distinct_flop_sources=chosen,
   certified_by_this_source_only_precheck=False)
 out=dict(schema="NL2_B404_RANK214219_THREE_AUTHENTIC_GTO_NL2_IP_SOURCE_PRECERT_V1",
  source_V48_status_sha256=sha(STATUS),B370_original_V47_sha256=sha(B370),
  B393_original_GTO_source_SHA256=sha(B393),B396_true_NL2_IP_pair_proof_sha256=sha(B396),
  eligible_rank_source_triples=source_pins,readiness_only_no_CERT_upgrade=True,
  ranks_with_three_full_street_40_70_positive_flops=[214,219],
  baseline_CERT_MULTIBOARD=160,baseline_APPROX=232,baseline_EST=0,
  original_preflop_CFR_is_not_NL2_conditional_private_hand_frequency=True,
  no_texture_level_GTO_or_blanket_50pct_strategy=True,
  separate_independent_original_archive_SHA_HU2475_UI_and_per_board_lock_audit_required=True,
  PR2_remains_draft_unmerged=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B404 CO_BB rank214/219 pre-CERT original-source triple proof\n\n"
  "Each has historical Js9h4d paired exact GTO/NL2 CO-IP plus newly sourced KsQh4d "
  "and Js9h5d on x b100 c/x b50 c/x at identical SPR. Only exact authenticated "
  "original runout source SHA and max/40%/70% legal hero combos are eligible. "
  "No promotion until independent original source artifact re-verification, "
  "160→162 CERT registry, board-by-board lock/50% sizing, frontend and full HU2475 Actions. "
  "NL2 frequencies are aggregate pool marginals, not opponent private-card decisions. "
  "PR #2 remains draft/unmerged.\n")
 print("PASS B404 two source-blind original complete 3-flop candidates, 160 CERT/232 APPROX unchanged")
if __name__=="__main__":main()
