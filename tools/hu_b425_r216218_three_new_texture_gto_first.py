#!/usr/bin/env python3
"""B425 independently recover original B413 true Rust GTO sources for three still APPROX models; no solve.
Only original exact GTO actor/line/SPR + 40/70 reach can authorize new NL2 partial locks.
"""
import argparse,hashlib,json,pathlib
from hu_sequential_cfr_reach import game_reach
D=pathlib.Path("data")
FLOPS=("Ac8d4h","7c5h2d","9s9h3d")
RANKS={
 216:("ln-ipfr-r_model-7kv23r","x b50 c/x b50 c/x"),
 218:("ln-ipfr-r_model-h0c7q7","x b50 c/x b50 c/x")}
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
OUT=D/"nl2_hu_b425_r216218_three_new_texture_gto_sources.json"
DOC=pathlib.Path("docs/NL2_HU_B425_R216218_THREE_NEW_TEXTURE_GTO_SOURCES.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def main():
 p=argparse.ArgumentParser();p.add_argument("--downloads",type=pathlib.Path,required=True);p.add_argument("--run-id",type=int,required=True)
 a=p.parse_args()
 status=read(D/"nl2_hu_multiboard_status_v50_b417_rank166.json")
 assert (status["CERT_MULTIBOARD"],status["APPROX"],status["EST"],status["TOTAL"])==(163,229,0,392)
 triage=read(D/"nl2_hu_b370_first10_approx_source_triage.json")
 b377=read(D/"nl2_hu_b377_co_bb_five_approx_two_fresh_true_gto_nl2_ip_strict_source.json")
 previous2=read(D/"nl2_hu_b400_five_cobb_gto_second_three_flops.json")
 assert not(set(FLOPS)&set(previous2["predeclared_flops"])),"B425 source flops must differ from B400"
 prevB413=read(D/"nl2_hu_b416_three_remaining_cobb_original_gto_flops.json")
 assert not(set(FLOPS)&set(prevB413["predeclared_flops"])),"B425 must not reuse B413 flops"
 assert len(set(FLOPS))==3
 previous=read(D/"nl2_hu_b393_five_cobb_gto_first_three_flops.json")
 previous3=read(D/"nl2_hu_b418_r216218_three_frozen_true_gto_sources.json")
 assert not(set(FLOPS)&set(previous3["predeclared_flops"])),"B425 must use new boards after B418"
 assert not (set(FLOPS)&(set(b377["source_flops"])|set(previous["predeclared_flops"]))),"B413 GTO flops must be new"
 assert set(RANKS).issubset({int(k) for k in b377["models_and_frozen_lines"]})
 assert all(not z for z in b377["matched_new_distinct_flops_by_model"].values())
 ms={}
 for rank,(mid,line) in RANKS.items():
  s=status["records"][mid]
  assert (s["label"],s["frequency_rank"],s["solver_profile"],s["family"],s["street"])==(
   "APPROX",rank,"CO_BB","SRP",2)
  assert s["abstract_action_history"]
  old=next(z for z in triage["source_blind_selected_ten"] if z["frequency_rank"]==rank)
  assert old["model_id"]==mid and old["true_paired_measured_NL2_hero_lock_flops"]==1
  assert old["strictly_measured_pairs"][0]["flop"]=="Js9h4d"
  ms[rank]=s
 sources=[];positive={str(k):[] for k in RANKS}
 for flop in FLOPS:
  name=f"nl2-multiboard-B425_R216218_GTO_FIRST-CO_BB-{flop}-gto"
  root=a.downloads/name;mp=root/"evidence"/f"CO_BB-{flop}-gto.json"
  result=dict(flop=flop,artifact_name=name,original_Rust_manifest_present=mp.is_file(),
    genuine_solved_original_cases=0,source_status="NO_ACTUAL_ORIGINAL_SOLVER_JOB",cases=[])
  if not mp.is_file():
   sources.append(result);continue
  assert (root/"evidence/poker-solver-pin.txt").read_text().strip()==PIN
  assert (root/"evidence/rust-pin.txt").read_text().strip()==RUST
  m=read(mp)
  assert (m["schema"],m["spot"],m["pot_family"],m["flop"],m["version"])==(
    "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","CO_BB","SRP",flop,"gto")
  assert (m["root_pot_bb"],m["root_remaining_bb"])==(5.5,97.5)
  assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
  assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
  assert (m["flop_action_sizes"],m["flop_line_policy"],m["selected_lines"])==(
   ["33%","50%","75%","100%"],"checked-b50b100only",["x b50 c","x b100 c"])
  assert len(m["turns"])==1 and m["solved_cases"]==len(m["cases"])
  result.update(original_manifest_SHA256=sha(mp),source_failures=m["failures"],source_skips=m["skipped"])
  if m["failures"]:
   result["source_status"]="ACTUAL_RUST_ERROR_EXCLUDE"
   sources.append(result);continue
  if not m["cases"]:
   result["source_status"]="ACTUAL_ZERO_SUBGAME_EXCLUDE"
   sources.append(result);continue
  fp=root/"solver/postflop"/m["file_flop"]
  assert fp.is_file() and sha(fp)==m["file_flop_sha256"]
  fr=read(fp);assert (fr["flop"],fr["pot"],fr["stack"])==(flop,550,9750)
  result.update(original_root_SHA256=sha(fp),original_root_job_SHA256=sha(fp.with_suffix(".job.json")),
    genuine_solved_original_cases=len(m["cases"]))
  for c in m["cases"]:
   assert c["line"] in ("x b50 c","x b100 c") and c["turn"] in m["turns"]
   assert c["status"]=="GTO_EXACT_ONLY" and c["hero_gap_pct"] is None
   assert c["gto_gap_pct"] is not None and 0<=c["gto_gap_pct"]<=.5
   sub=root/"solver/postflop"/c["source_path"]
   assert sub.is_file() and sha(sub)==c["source_sha256"]
   d=read(sub)
   assert (d["flop"],d["turn"],d["line0"])==(flop,c["turn"],c["line"])
   seq,stats=game_reach(fr,d)
   targets=[]
   for n in d["nodes"]:
    if n["player"]!=1 or len(n["board"])!=10:continue
    which=[rank for rank,(_,line) in RANKS.items() if n["line"]==line]
    if not which:continue
    q=seq["|".join((n["board"],n["line"],"1"))]
    spr=(d["stack"]-max(n["bets"]))/n["pot"]
    row=dict(flop=flop,turn=c["turn"],public_board=n["board"],
     exact_action_line=n["line"],actor="CO_IP",
     legal_full_street_40_70_combos=q["count"],actual_SPR=round(spr,6),
     original_GTO_sha256=c["source_sha256"],original_GTO_gap_pct=c["gto_gap_pct"],
     original_source_run_id=a.run_id)
    targets.append(row)
    for rank in which:
     if q["count"]>0 and abs(spr-ms[rank]["assumed_model_node_spr"])/max(1,spr)<=.05:
      positive[str(rank)].append(row)
   result["cases"].append(dict(turn=c["turn"],original_GTO_sha256=c["source_sha256"],
     GTO_gap_pct=c["gto_gap_pct"],strict_reach_stats=dict(stats),
     actual_GTO_actor_IP_target_river_nodes=targets))
  result["source_status"]="ORIGINAL_GTO_ANY_TARGET_POSITIVE" if any(x["flop"]==flop for v in positive.values() for x in v) else "ORIGINAL_GTO_TARGET_STRICT_ZERO"
  sources.append(result)
 assert len(sources)==3
 distinct={k:sorted({x["flop"] for x in v}) for k,v in positive.items()}
 report=dict(schema="NL2_B425_R216218_THREE_NEW_TEXTURE_GENUINE_GTO_FIRST_V1",
  models={str(rank):dict(model_id=MID,exact_line=LINE,estimated_SPR=ms[rank]["assumed_model_node_spr"]) for rank,(MID,LINE) in RANKS.items()},
  original_run_id=a.run_id,predeclared_flops=list(FLOPS),
  source_poker_solver_pin=PIN,source_Rust_pin=RUST,
  real_original_GTO_only_solve_sources=sources,
  original_source_run_B425=a.run_id,
  original_Rust_source_artifacts_from_this_run=True,
  exact_actor_IP_positive_river_nodes_by_model=positive,
  distinct_new_GTO_positive_flops_by_rank=distinct,
  previous_B377_two_source_flops_zero_real_40_70_target=True,
  only_GTO_positive_flops_eligible_for_future_real_NL2_IP_partial_lock=True,
  pinned_solver_preflop_CFR_not_observed_private_NL2_combo_actions=True,
  no_CERT_from_single_GTO_source_no_generic_texture_label=True,
  no_2026_private_opponent_hero_action_data_used=True,
  CERT_MULTIBOARD=163,APPROX=229,EST=0,TOTAL=392,PR2_draft_never_merge=True)
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B425 original GTO-first source: ranks216 and 218 only\n\n"
  +"Pre-registered B425 three new original flops QsJh6d, Th8d4c, 8s6h2c, with actual Rust full flop "
  +"50% or 100% CO-IP bet histories, exact actor/SPR and 40/70 legal full-street combo gate. "
  +"Only positive GTO exact-board results authorize actual partial NL2 hero-IP follow-on solves. "
  +"; ".join(f"rank{k}: {len(v)} distinct GTO-positive flops" for k,v in distinct.items())
  +". No CERT from a GTO-only run or generic textures; 163 CERT /229 APPROX unchanged.\n")
 print("PASS B425 independent cached B413 true Rust GTO triage",distinct,"GTO-positive flops; no early CERT")
if __name__=="__main__":main()
