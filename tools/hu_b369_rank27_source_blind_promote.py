#!/usr/bin/env python3
"""B369: source-blind rank27 promotion only after three paired original 100bb GTO/NL2 OOP flops."""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,texture
from hu_cert_lock_medium_coverage_matrix import create
from hu_cert_lock_medium_audit import audit

D=pathlib.Path("data")
MID="ln-iso-lmp_r_model-1aov4pd"
LINE="b33 c/b50 c/"
SPR=11.53
EXPECTED=("KsQh4d","7s5h3d","9s6h3d")
PARENT=D/"nl2_hu_multiboard_status_v47_b364_rank96.json"
STATUS=D/"nl2_hu_multiboard_status_v48_b369_rank27.json"
MATRIX=D/"nl2_hu_cert_lock_medium_matrix_v48_b369.json"
PROOF=D/"nl2_hu_b369_rank27_three_new_true_original_GTO_NL2_OOP_source_gate.json"
AUDIT=D/"nl2_hu_cert_lock_medium_audit_v48_b369.json"
DOC=pathlib.Path("docs/NL2_HU_B369_RANK27_THREE_TRUE_GTO_NL2_OOP_CERT.md")
SOLVER_PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST_PIN="9d1509fe5077d019825f833eed04b16d342dfda1"
BATCHES={
 "B365":dict(proof=D/"nl2_hu_b365_rank27_two_new_true_source_proofs.json",
  partition=D/"solver_evidence/NL2_B365_R27_AUTHENTIC_SOLVE_MANIFESTS.json",
  gzip=D/"solver_evidence/NL2_MULTIBOARD_B365_R27_VERIFIED.json.gz",
  index=D/"solver_evidence/NL2_MULTIBOARD_B365_R27_VERIFIED.index.json",
  flops=("KsQh4d","7s5h3d"),batch="B365_R27_TWO_NEW_TRUE_RUST_ORIGINAL"),
 "B367":dict(proof=D/"nl2_hu_b367_rank27_two_new_true_source_proofs.json",
  partition=D/"solver_evidence/NL2_B367_R27_AUTHENTIC_SOLVE_MANIFESTS.json",
  gzip=D/"solver_evidence/NL2_MULTIBOARD_B367_R27_VERIFIED.json.gz",
  index=D/"solver_evidence/NL2_MULTIBOARD_B367_R27_VERIFIED.index.json",
  flops=("9s6h3d",),batch="B367_R27_THIRD_NEW_TRUE_RUST_ORIGINAL")
}
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def case_for(archive,flop,version,turn):
 rows=[c for a in archive["artifacts"] if (a["spot"],a["flop"],a["version"])==("LMP_CO_BB",flop,version)
       for c in a["cases"] if (c["flop_line"],c["turn"])==("b33 c",turn)]
 assert len(rows)==1,(flop,version,turn,len(rows))
 c=rows[0]
 assert (c["flop_root_pot_bb"],c["flop_root_stack_bb"])==(2.5,99.0)
 assert c["flop_size_menu"]==["33%","50%","75%","100%"]
 assert str(c["empirical_scope"]).startswith("ASSUMED")
 assert c["gto_exploitability_pct"] is not None and c["gto_exploitability_pct"]<=.5
 if version=="exp_oop":assert c["locked_hero_gap_pct"] is not None and c["locked_hero_gap_pct"]<=.5
 return c
def validate_batch(name,cfg):
 for p in (cfg["proof"],cfg["partition"],cfg["gzip"],cfg["index"]):
  if not p.is_file():raise FileNotFoundError(f"{name}: original source artifact missing: {p}")
 proof,part,index=read(cfg["proof"]),read(cfg["partition"]),read(cfg["index"])
 raw=gzip.decompress(cfg["gzip"].read_bytes());archive=json.loads(raw)
 assert index["schema"]=="NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1" and index["batch"]==cfg["batch"]
 assert index["run_id"]==proof["source_run_id"]==archive["source_run_id"]
 assert index["gzip_sha256"]==sha(cfg["gzip"]) and index["raw_sha256"]==sha_bytes(raw)
 assert proof["true_verified_case_count"]==index["verified_cases"]==archive["new_authentic_board_cases"]
 assert archive["schema"]=="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1" and not archive["errors"]
 assert archive["source_poker_solver_pin"]==SOLVER_PIN and archive["authentic_rust_engine_pin"]==RUST_PIN
 assert part["original_run_id"]==proof["source_run_id"] and part["positive_solved_jobs"]
 assert len(part["positive_solved_jobs"])+len(part["explicit_zero_case_negative_jobs"])==(4 if name=="B365" else 2)
 # The verified per-case empirical_scope is checked as ASSUMED_PREFLOP_RANGES in case_for().
 assert proof.get("rank27_remains_APPROX_pending_independent_3_board_gate",
                  proof.get("rank27_remains_APPROX_until_three_distinct_flop_pairs")) is True
 assert len(proof.get("raw_jobs_partitions_sha256",""))==64
 pairs={x["flop"]:x for x in proof["candidate_pairs"]}
 assert set(pairs)==set(cfg["flops"])
 source_rows={}
 for flop,pair in pairs.items():
  assert pair["strict_authenticated_pair"] is True
  allowed=set(pair["new_exact_matched_GTO_NL2_OOP_river_boards"]);assert allowed
  for version in ("gto","exp_oop"):
   matches=[x for x in proof["source_proofs"] if (x["flop"],x["version"])==(flop,version)]
   assert len(matches)==1
   row=matches[0]
   assert row["verified_case_count"]==1 and row["flop_b33_strict_combos"]>0
   assert row["strict_UTG_OOP_combo_rows"]>0
   assert all(len(row[k])==64 for k in ("root_gto_sha256","root_job_sha256","source_manifest_sha256","turn_river_sha256"))
   assert set(row["strict_UTG_OOP_exact_river_public_nodes"])>=allowed
   c=case_for(archive,flop,version,row["turn"]);assert c["source_sha256"]==row["turn_river_sha256"]
   for board in allowed:
    node=next((n for n in c["nodes"] if n["acting_seat"]==0 and n["exact_node_line"]==LINE
      and n["public_board"]==board and n["strictly_reachable_combos"]>0
      and abs(n["node_spr"]-SPR)/SPR<=.05),None)
    assert node is not None,(name,flop,version,board)
    q=row["strict_UTG_OOP_exact_river_public_nodes"][board]
    assert q["combos"]==node["strictly_reachable_combos"] and abs(q["SPR"]-node["node_spr"])<1e-5
   source_rows[(flop,version)]=row
 return proof,part,index,archive,pairs,source_rows

def main():
 if not all(c["proof"].is_file() for c in BATCHES.values()):
  raise RuntimeError("B369 waits for both B365 and B367 source-proof commits; no partial promotion.")
 parent=read(PARENT)
 assert parent["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96"
 assert (parent["CERT_MULTIBOARD"],parent["APPROX"],parent["EST"],parent["TOTAL"])==(159,233,0,392)
 target=parent["records"][MID]
 assert (target["label"],target["frequency_rank"],target["family"],target["solver_profile"],target["street"],target["assumed_model_node_spr"])==("APPROX",27,"LMP","LMP_CO_BB",2,SPR)
 assert target["source_model_id"]=="ln-iso-lmp_t_model-19hfq8v" and target["high_frequency_preregistered"] is False
 assert 27 in parent["source_blind_next6_prereg_ranks"] and 27 not in parent["source_blind_expansion_ranks"]
 batch_data={};expected_runs=set();allowed_boards={}
 for name,cfg in BATCHES.items():
  proof,part,index,archive,pairs,source_rows=validate_batch(name,cfg)
  batch_data[name]=dict(proof=proof,part=part,index=index,archive=archive,pairs=pairs,source_rows=source_rows)
  expected_runs.add(proof["source_run_id"])
  for flop,pair in pairs.items():allowed_boards[flop]=set(pair["new_exact_matched_GTO_NL2_OOP_river_boards"])
 assert set(allowed_boards)==set(EXPECTED)
 by_exact,by_locked,source_summary=build_source_index(D,[BATCHES["B365"]["gzip"],BATCHES["B367"]["gzip"]])
 model=dict(family=target["family"],spot=target["solver_profile"],street=target["street"],
  preflop_text=target["preflop_text"],abstract_action_history=target["abstract_action_history"],
  approx_spr=target["assumed_model_node_spr"])
 rows,reason=candidates(model,by_exact,by_locked,None);assert reason is None,reason
 boards=[];pins=[]
 for flop in EXPECTED:
  name="B365" if flop in BATCHES["B365"]["flops"] else "B367"
  proof=batch_data[name]["proof"];run=proof["source_run_id"]
  turn=next(x["turn"] for x in proof["source_proofs"] if x["flop"]==flop and x["version"]=="gto")
  eligible=[x for x in rows if x["flop"]==flop and x["turn"]==turn and x["public_board"] in allowed_boards[flop]
    and x["source_run_id"]==run and x["actual_exact_action_line"]==LINE and x["acting_seat"]==0
    and x["source_kind"].startswith("ASSUMED") and x["assumed_preflop_ranges"] is True and x["nl2_locked_variants"]]
  assert eligible,f"No exact paired GTO/NL2 OOP candidate for {flop}"
  b=sorted(eligible,key=lambda x:(x["relative_spr_error_pct"],-x["strict_full_street_combo_reachable"],x["public_board"]))[0]
  lock=b["nl2_locked_variants"][0]
  assert lock["version"]=="exp_oop" and lock["run_id"]==run and len(b["source_sha256"])==64 and len(lock["sha256"])==64
  assert b["strict_full_street_combo_reachable"]>0 and b["genuine_gto_exploitability_pct"]<=.5 and b["relative_spr_error_pct"]<=5
  assert lock["observed_marginal_source_nodes"]>0
  assert all(isinstance(lock[k],int) and lock[k]>=0 for k in ("observed_marginal_source_nodes","assumed_default_source_nodes","unlocked_source_nodes"))
  assert "PARTIALLY" in lock["source_scope"]
  b["flop_texture"]=texture(flop);boards.append(b)
  g=batch_data[name]["source_rows"][(flop,"gto")];e=batch_data[name]["source_rows"][(flop,"exp_oop")]
  board=b["public_board"];gn=g["strict_UTG_OOP_exact_river_public_nodes"][board];en=e["strict_UTG_OOP_exact_river_public_nodes"][board]
  assert gn["combos"]==b["strict_full_street_combo_reachable"] and en["combos"]>0 and abs(en["SPR"]-b["actual_spr"])<1e-5
  pins.append(dict(batch=name,flop=flop,turn=turn,public_board=board,run_id=run,
   original_GTO_turn_sha256=g["turn_river_sha256"],true_NL2_OOP_turn_sha256=e["turn_river_sha256"],
   original_GTO_root_sha256=g["root_gto_sha256"],original_GTO_job_sha256=g["root_job_sha256"],
   original_source_manifest_sha256=g["source_manifest_sha256"],strict_GTO_actor_combos=gn["combos"],
   strict_NL2_OOP_actor_combos=en["combos"],observed_marginal_source_nodes=lock["observed_marginal_source_nodes"],
   assumed_default_source_nodes=lock["assumed_default_source_nodes"],unmatched_unlocked_source_nodes=lock["unlocked_source_nodes"],
   actual_SPR=b["actual_spr"],model_SPR=SPR,gto_exploitability_pct=b["genuine_gto_exploitability_pct"],
   relative_SPR_error_pct=b["relative_spr_error_pct"],medium_50pct_eligible_combos=b["medium_50pct_eligible_combos"],
   b50_nonpolarized_relative_equity_research_candidate=b["b50_nonpolarized_relative_equity_research_candidate"],
   pin=dict(archive_index_sha256=sha(BATCHES[name]["index"]),archive_gzip_sha256=sha(BATCHES[name]["gzip"]),
    source_proof_sha256=sha(BATCHES[name]["proof"]),solve_partition_sha256=sha(BATCHES[name]["partition"]))))
 assert len(boards)==3 and len({x["flop"] for x in boards})==3 and [x["flop"] for x in boards]==list(EXPECTED)
 textures=sorted({x["flop_texture"] for x in boards});assert len(textures)>=2
 assert all(x["assumed_preflop_ranges"] is True for x in boards)
 new=copy.deepcopy(parent);rec=copy.deepcopy(target)
 rec.update(label="CERT-MULTIBOARD",high_frequency_preregistered=True,original_top24_high_frequency_preregistered=False,
  source_blind_expansion_rank=27,source_blind_expansion_preregistered=True,
  prereg_cohort="source_blind_next6_prereg_ranks_27_28_29_30_31_32__B365_B367",
  certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,blocked_reason=None,
  source_credibility="GITHUB_ACTIONS_AUTHENTIC_CFR_SHA256_AND_FULL_STREET_COMBO_REACH_ASSUMED_PREFLOP_169CLASS_NL2_OOP_PARTIAL_LOCK")
 new["records"][MID]=rec
 new.update(schema="NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B369_RANK27",CERT_MULTIBOARD=160,APPROX=232,EST=0,TOTAL=392,
  original_v47_cert=159,original_v47_approx=233,parent_v47_sha256=sha(PARENT),
  supplementary_cert_count=parent["supplementary_cert_count"]+1,
  source_blind_expansion_ranks=sorted(set(parent["source_blind_expansion_ranks"]+[27])),
  original_top24_cutoff_unchanged=True,
  B369_rank27_three_new_true_original_GTO_NL2_OOP_flops=dict(rank=27,model_id=MID,spot="LMP_CO_BB",actor="BB_OOP",
   exact_line=LINE,model_SPR=SPR,flops=list(EXPECTED),textures=textures,source_blind_expansion_rank=27,
   source_blind_expansion_preregistered=True,preregistered_before_solves=True,original_top24_high_frequency_preregistered=False,
   original_flop_size_menu_all_33_50_75_100=True,preflop_169_class_assumed_not_observed_NL2=True,
   no_observed_private_combo_NL2_frequencies=True,exact_named_boards_only_no_texture_generalization=True,
   genuine_sources=pins,source_run_ids=sorted(expected_runs),
   B365_source_proof_sha256=sha(BATCHES["B365"]["proof"]),B367_source_proof_sha256=sha(BATCHES["B367"]["proof"]),
   no_generic_texture_GTO=True),
  no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,PR2_remains_draft_never_merge=True)
 if "LOWER_FREQUENCY_BELOW_PREREGISTERED_TOP24_CUTOFF" in new.get("nonupgrade_reasons",{}):
  new["nonupgrade_reasons"]["LOWER_FREQUENCY_BELOW_PREREGISTERED_TOP24_CUTOFF"]=max(0,new["nonupgrade_reasons"]["LOWER_FREQUENCY_BELOW_PREREGISTERED_TOP24_CUTOFF"]-1)
 new["source_evidence"]["new_subgames"]+=source_summary["new_subgames"]
 for name in ("B365","B367"):
  cfg=BATCHES[name];idx=read(cfg["index"]);proof=batch_data[name]["proof"]
  new["source_evidence"]["source_files"].append(str(cfg["gzip"]))
  new["independently_verified_completed_batches"][name+"_R27"] = dict(
   status="VERIFIED",run_id=proof["source_run_id"],authentic_jobs=len(batch_data[name]["part"]["positive_solved_jobs"]),
   gto_cases=idx["gto_cases"],locked_cases=idx["locked_cases"],new_subgames=idx["verified_cases"],
   gzip_sha256=idx["gzip_sha256"])
 report=audit(new)
 assert (report["cert_multiboard"],report["approx"],report["EST"])==(160,232,0)
 assert report["aggregate"]["named_board_proofs"]==609 and report["aggregate"]["paired_hero_locked_source_variants"]==701
 STATUS.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n")
 matrix=create(new)
 assert (len(matrix["models"]),len(matrix["boards"]))==(160,609)
 unknown=sum(1 for b in matrix["boards"] for l in b["hero_lock_proofs"] if l["node_rate_data_status"]=="HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN")
 assert unknown==0
 b368=read(D/"nl2_hu_b368_lock_denominator_recovery.json")
 assert b368["recovered_lock_variants"]==334 and b368["remaining_unknown_variants"]==0
 matrix.update(schema="NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V48_B369",
  parent_v47_status_sha256=sha(PARENT),V48_status_sha256=sha(STATUS),
  B368_lock_denominator_recovery_sha256=sha(D/"nl2_hu_b368_lock_denominator_recovery.json"),
  source_unknown_variants_before=334,source_unknown_variants_after=0,
  source_denominator_recovery_method="PINNED_POOL_STATS_AND_PER_RUN_HISTORICAL_HELPER_HEAD_SHA",
  B369_rank27_source_run_ids=sorted(expected_runs),no_inferred_or_fabricated_counts=True,PR2_Draft_NEVER_MERGE=True)
 MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+"\n")
 AUDIT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 proof_out=dict(schema="NL2_HU_B369_RANK27_THREE_NEW_TRUE_ORIGINAL_GTO_NL2_OOP_SOURCE_PROOF_V1",
  source_blind_expansion_preregistered=True,source_blind_expansion_rank=27,preregistered_before_solves=True,
  prereg_cohort="27,28,29,30,31,32",original_top24_high_frequency_preregistered=False,
  source_runs=sorted(expected_runs),source_proofs=pins,distinct_flops=list(EXPECTED),textures=textures,
  three_distinct_paired_flops=True,original_full_100bb_Rust_CFR=True,full_flop_size_menu=["33%","50%","75%","100%"],
  preflop_range_assumed_169_class_not_observed_NL2=True,
  NL2_source_is_partial_OOP_pool_marginal_not_private_card_policy=True,no_generic_texture_GTO=True,
  no_inferred_or_fabricated_counts=True,B368_recovered_variants=334,B368_remaining_UNKNOWN=0,
  CERT_before=159,CERT_after=160,APPROX_before=233,APPROX_after=232,EST=0,
  named_boards_before=606,named_boards_after=609,hero_lock_variants_before=698,hero_lock_variants_after=701,
  status_sha256=sha(STATUS),matrix_sha256=sha(MATRIX),audit_sha256=sha(AUDIT),parent_v47_status_sha256=sha(PARENT),
  PR2_Draft_NEVER_MERGE=True)
 PROOF.write_text(json.dumps(proof_out,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B369 rank27: three original full-100bb GTO + NL2 OOP paired flops\n\n"
  "Rank27 was preregistered in the existing source-blind next-six cohort before these solves. It is a supplementary source-blind expansion; the original top-24 cutoff remains unchanged. "
  "All three boards use the original pinned Rust CFR and exact BB-OOP line b33 c/b50 c/, model SPR 11.53, with GTO exploitability and SPR gates. "
  "The preflop limp/169-class range is ASSUMED, not an observed NL2 preflop distribution. NL2 evidence is a genuine partial OOP pool-marginal lock, not private-card-conditional action rates.\n\n"
  +"\n".join(f"- {x['flop']} turn {x['turn']}: board {x['public_board']}; GTO combos {x['strict_GTO_actor_combos']}; NL2 OOP combos {x['strict_NL2_OOP_actor_combos']}; measured/assumed/unlocked source nodes {x['observed_marginal_source_nodes']}/{x['assumed_default_source_nodes']}/{x['unmatched_unlocked_source_nodes']}; SPR {x['actual_SPR']:.3f}" for x in pins)
  +"\n\nOnly exact named boards are certified. Generic hand-class/texture model remains APPROX outside these three boards. Medium 50% research tags remain limited to exact boards with supporting source evidence. B368 denominator recovery is 334/334 with UNKNOWN=0. Full V48 source audit and HU2475/2475 audit are required. PR #2 remains Draft; never merge.\n")
 print(json.dumps(dict(CERT=160,APPROX=232,EST=0,rank27_flops=list(EXPECTED),textures=textures,
  boards=609,locks=701,b50=matrix["strict_aggregate"]["b50_research_candidate_boards"],
  unknown_denominators=0,source_runs=sorted(expected_runs)),ensure_ascii=False))
if __name__=="__main__":main()
