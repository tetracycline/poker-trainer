#!/usr/bin/env python3
"""B387 rank107 frozen GTO-first probe: only genuine exact original 100bb Rust CFR sources.
No NL2 EXP solve or CERT is allowed from a GTO-only source, regardless of reach.
"""
import argparse,hashlib,json,pathlib
from hu_sequential_cfr_reach import game_reach
D=pathlib.Path("data")
FLOPS=("As9h2d","Js9h4d","QsJh4d")
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
LINE="b33 c/x b50 c/x"
MID="ln-ipfr-r_model-ujl14x"
OUT=D/"nl2_hu_b387_rank107_gto_first_three_frozen_flops.json"
DOC=pathlib.Path("docs/NL2_HU_B387_RANK107_GTO_FIRST_THREE_PROBE.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--downloads",type=pathlib.Path,required=True);ap.add_argument("--run-id",type=int,required=True)
 args=ap.parse_args()
 plan=D/"nl2_hu_b386_first10_postsource_frozen_audit.json"
 parent=read(plan)
 proposed=parent["selected_next_for_original_GTO_first"]
 assert proposed["rank"]==107 and proposed["exact_line"]==LINE
 assert proposed["GTO_first_flops"]==list(FLOPS)
 assert proposed["NL2_EXP_ONLY_AFTER_AUTHENTIC_GTO_STRICT_POSITIVE"]
 s=read(D/"nl2_hu_multiboard_status_v47_b364_rank96.json")
 assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(159,233,0,392)
 model=s["records"][MID]
 assert (model["frequency_rank"],model["label"],model["solver_profile"])==(107,"APPROX","BTN_BB")
 evidence=[]
 positives=[]
 for flop in FLOPS:
  name="nl2-multiboard-B387_R107_GTO_FIRST-BTN_BB-"+flop+"-gto"
  root=args.downloads/name
  mp=root/"evidence"/("BTN_BB-"+flop+"-gto.json")
  item=dict(flop=flop,source_artifact_name=name,original_manifest_present=mp.is_file(),
   actual_solved_gto_cases=0,full_street_positive_actor_IP_river_nodes=[],source_scope="GTO_ONLY_NEVER_NL2_LOCK")
  if not mp.is_file():
   item["source_status"]="ORIGINAL_SOLVER_JOB_MISSING_NOT_CERT"
   evidence.append(item);continue
  assert (root/"evidence/poker-solver-pin.txt").read_text().strip()==PIN
  assert (root/"evidence/rust-pin.txt").read_text().strip()==RUST
  m=read(mp)
  assert (m["schema"],m["spot"],m["pot_family"],m["flop"],m["version"])==(
   "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","BTN_BB","SRP",flop,"gto")
  assert (m["root_pot_bb"],m["root_remaining_bb"])==(5.5,97.5)
  assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
  assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
  assert m["flop_action_sizes"]==["33%","50%","75%","100%"]
  assert (m["flop_line_policy"],m["selected_lines"])==("oop-b33only",["b33 c"])
  assert len(m["turns"])==1 and m["solved_cases"]==len(m["cases"])
  item.update(original_manifest_sha256=sha(mp),errors=m["failures"],explicit_skips=m["skipped"])
  if m["failures"]:
   item["source_status"]="REAL_RUST_SOLVER_ERROR_NOT_GTO_CERT"
   evidence.append(item);continue
  if not m["cases"]:
   item["source_status"]="ZERO_VALID_ORIGINAL_TURN_CASE_NOT_CERT"
   evidence.append(item);continue
  fp=root/"solver/postflop"/m["file_flop"]
  assert fp.is_file() and sha(fp)==m["file_flop_sha256"]
  job=fp.with_suffix(".job.json")
  assert job.is_file()
  fr=read(fp)
  assert (fr["flop"],fr["pot"],fr["stack"])==(flop,550,9750)
  item.update(real_original_flop_sha256=sha(fp),original_flop_job_sha256=sha(job),
    original_preflop_CFR_data_SHA256=m["preflop_ranges"]["full_sha256"])
  item["actual_solved_gto_cases"]=len(m["cases"])
  for c in m["cases"]:
   assert (c["line"],c["turn"])==("b33 c",m["turns"][0])
   assert c["gto_gap_pct"] is not None and c["gto_gap_pct"]<=0.5
   assert c["hero_gap_pct"] is None and c["status"]=="GTO_EXACT_ONLY"
   sub=root/"solver/postflop"/c["source_path"]
   assert sub.is_file() and sha(sub)==c["source_sha256"]
   raw=read(sub)
   assert (raw["flop"],raw["turn"],raw["line0"])==(flop,c["turn"],"b33 c")
   mask,stats=game_reach(fr,raw)
   target=[]
   for n in raw["nodes"]:
    if n["player"]!=1 or n["line"]!=LINE or len(n["board"])!=10:continue
    strict=mask["|".join((n["board"],n["line"],"1"))]
    row=dict(flop=flop,turn=c["turn"],exact_public_board=n["board"],
      actor="BTN_IP",exact_line=LINE,strict_40_70_hero_IP_combos=strict["count"],
      exact_SPR=round((raw["stack"]-max(n["bets"]))/n["pot"],6),
      real_GTO_gap_pct=c["gto_gap_pct"],original_turn_subgame_sha256=c["source_sha256"],
      original_run_id=args.run_id)
    target.append(row)
    if row["strict_40_70_hero_IP_combos"]>0 and abs(row["exact_SPR"]-model["assumed_model_node_spr"])/max(1,row["exact_SPR"])<=.05:
     positives.append(row)
   item.setdefault("source_cases",[]).append(dict(turn=c["turn"],original_sha256=c["source_sha256"],
     GTO_gap_pct=c["gto_gap_pct"],full_street_40_70_stats=dict(stats),
     genuine_named_river_actor_IP_targets=target))
  item["source_status"]="GENUINE_GTO_SOURCE_POSITIVE_TARGET" if any(x["flop"]==flop for x in positives) else "GENUINE_GTO_SOURCE_BUT_ZERO_LEGAL_TARGET"
  item["full_street_positive_actor_IP_river_nodes"]=[x for x in positives if x["flop"]==flop]
  evidence.append(item)
 assert len(evidence)==3 and len({x["flop"] for x in evidence})==3
 qualifying_flops=sorted({x["flop"] for x in positives})
 report=dict(schema="NL2_HU_B387_RANK107_PREREG_GTO_FIRST_THREE_TRUE_SOURCES_V1",
  run_id=args.run_id,model_id=MID,frequency_rank=107,spot="BTN_BB",
  engine_pin=RUST,preflop_solver_pin=PIN,
  preregistered_B386_source_eligibility_SHA256=sha(plan),
  preregistered_candidate_flops=list(FLOPS),frozen_exact_actor="BTN_IP",frozen_exact_line=LINE,
  actual_genuine_GTO_only_sources=evidence,strict_positive_exact_board_GTO_sources=positives,
  candidate_flops_eligible_for_future_matching_real_NL2_IP_partial_lock=qualifying_flops,
  no_early_CERT_label=True,need_actual_hero_NL2_lock_for_each_certifying_named_board=True,
  no_empirical_villain_private_card_conditional_NL2_frequencies_claim=True,
  no_2026_data_loaded=True,no_generic_handclass_texture_GTO_claim=True,
  no_source_reuse_as_multiple_distinct_flops=True,
  CERT_MULTIBOARD=159,APPROX=233,EST=0,TOTAL=392,PR2_remains_draft_never_merge=True)
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B387 frozen GTO-first rank107 exact source triage\n\n"
  +"Frozen in B386 before original Rust solve: As9h2d, Js9h4d, QsJh4d (different public flops). "
  +"Three GTO-only true 100bb Rust source jobs, never substitute a generic texture or assume an NL2 villain private-card rate. "
  +f"Source-gated positive exact BTN-IP river nodes: {len(positives)}; qualifying distinct flops: {', '.join(qualifying_flops) if qualifying_flops else 'none'}. "
  +"Only those flops may be scheduled for matched actual EXP_IP Rust lock; no CERT status upgraded in B387. "
  +"159 CERT / 233 APPROX / 0 EST remains unchanged.\n")
 print("PASS B387 genuine GTO-first source triage",len(positives),"eligible river nodes",qualifying_flops,"flops; 159/233")
if __name__=="__main__":main()
