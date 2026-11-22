#!/usr/bin/env python3
"""B391 GTO-first two rank115/116 models, three frozen original 100bb LMP flops.
No generic texture CERT and no NL2 observed private-card claim.
"""
import argparse,hashlib,json,pathlib
from hu_sequential_cfr_reach import game_reach
D=pathlib.Path("data")
FLOPS=("As9h2d","Js9h4d","QsJh4d")
MODELS={115:"ln-iso-lmp_r_model-17dzvwx",116:"ln-iso-lmp_r_model-1c6f833"}
LINE="b33 c/x b50 c/x"
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
OUT=D/"nl2_hu_b391_r115_116_three_frozen_gto_first_flops.json"
DOC=pathlib.Path("docs/NL2_HU_B391_R115_116_THREE_GTO_FIRST_SOURCES.md")
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser()
 a.add_argument("--downloads",type=pathlib.Path,required=True)
 a.add_argument("--run-id",type=int,required=True)
 args=a.parse_args()
 s=read(D/"nl2_hu_multiboard_status_v47_b364_rank96.json")
 assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(159,233,0,392)
 targets={rank:s["records"][mid] for rank,mid in MODELS.items()}
 for rank,model in targets.items():
  assert (model["frequency_rank"],model["label"],model["family"],model["solver_profile"],model["street"])==(
    rank,"APPROX","LMP","LMP_CO_BB",2)
  assert 11<=model["assumed_model_node_spr"]<=12
  assert model["abstract_action_history"]=="對手下注、你跟|對手過、你下注、對手跟|對手過"
 b370=read(D/"nl2_hu_b370_first10_approx_source_triage.json")
 for rank,mid in MODELS.items():
  row=next(x for x in b370["source_blind_selected_ten"] if x["frequency_rank"]==rank)
  assert row["model_id"]==mid and row["true_paired_measured_NL2_hero_lock_flops"]==1
  assert row["strictly_measured_pairs"][0]["flop"]=="KsQh4d"
 negatives=read(D/"nl2_hu_b383_rank115_116_b375_two_original_gto_zero_strict_negatives.json")
 assert len(negatives["true_original_Rust_GTO_but_strict_negative"])==2
 assert negatives["no_new_qualifying_distinct_GTO_flops"]
 actual=[];positives={str(rank):[] for rank in MODELS}
 for flop in FLOPS:
  name=f"nl2-multiboard-B391_R115116_GTO_FIRST-LMP_CO_BB-{flop}-gto"
  root=args.downloads/name
  mp=root/"evidence"/f"LMP_CO_BB-{flop}-gto.json"
  item=dict(flop=flop,artifact_name=name,manifest_present=mp.is_file(),
    genuine_original_solved_cases=0,verified_exact_positive_IP_river_nodes=[],
    source_status="MISSING_OR_NOT_COMPLETED_NO_CERT")
  if not mp.is_file():
   actual.append(item);continue
  assert (root/"evidence/poker-solver-pin.txt").read_text().strip()==PIN
  assert (root/"evidence/rust-pin.txt").read_text().strip()==RUST
  m=read(mp)
  assert (m["schema"],m["spot"],m["pot_family"],m["version"],m["flop"])==(
   "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","LMP_CO_BB","LMP","gto",flop)
  assert (m["root_pot_bb"],m["root_remaining_bb"])==(2.5,99.0)
  assert (m["preflop_ranges"]["source"],m["flop_size_profile"])==("ASSUMED_EXPLICIT_169CLASS","full")
  assert m["flop_action_sizes"]==["33%","50%","75%","100%"]
  assert not m["restricted_tree_assumption"]
  assert (m["flop_line_policy"],m["selected_lines"])==("oop-b33only",["b33 c"])
  assert len(m["turns"])==1 and m["solved_cases"]==len(m["cases"])
  item.update(manifest_sha256=sha(mp),errors=m["failures"],skipped=m["skipped"])
  if m["failures"]:
   item["source_status"]="AUTHENTIC_RUST_FAILED_EXCLUDE"
   actual.append(item);continue
  if not m["cases"]:
   item["source_status"]="AUTHENTIC_ZERO_SOLVED_SUBGAME_EXCLUDE"
   actual.append(item);continue
  fp=root/"solver/postflop"/m["file_flop"]
  assert fp.is_file() and sha(fp)==m["file_flop_sha256"]
  fr=read(fp)
  assert (fr["flop"],fr["pot"],fr["stack"])==(flop,250,9900)
  item.update(genuine_original_solved_cases=len(m["cases"]),flop_root_sha256=sha(fp),
    original_manifest_sha256=sha(mp),original_job_sha256=sha(fp.with_suffix(".job.json")))
  for c in m["cases"]:
   assert (c["line"],c["turn"])==("b33 c",m["turns"][0])
   assert c["status"]=="GTO_EXACT_ONLY" and c["hero_gap_pct"] is None
   assert c["gto_gap_pct"] is not None and 0<=c["gto_gap_pct"]<=.5
   p=root/"solver/postflop"/c["source_path"]
   assert p.is_file() and sha(p)==c["source_sha256"]
   d=read(p)
   assert (d["flop"],d["turn"],d["line0"])==(flop,c["turn"],"b33 c")
   mask,stats=game_reach(fr,d)
   rows=[]
   for n in d["nodes"]:
    if n["player"]!=1 or n["line"]!=LINE or len(n["board"])!=10:continue
    q=mask["|".join((n["board"],n["line"],"1"))]
    spr=(d["stack"]-max(n["bets"]))/n["pot"]
    row=dict(flop=flop,turn=c["turn"],public_board=n["board"],
      actor="CO_IP",exact_action_line=LINE,
      strict_40_70_CO_IP_combos=q["count"],actual_spr=round(spr,6),
      original_source_sha256=c["source_sha256"],
      original_GTO_exploitability_pct=c["gto_gap_pct"],source_run_id=args.run_id)
    rows.append(row)
    for rank,model in targets.items():
     if q["count"]>0 and abs(spr-model["assumed_model_node_spr"])/max(1,spr)<=.05:
      positives[str(rank)].append(row)
   item.setdefault("cases",[]).append(dict(turn=c["turn"],original_GTO_sha256=c["source_sha256"],
    GTO_exploitability_pct=c["gto_gap_pct"],strict_full_street_stats=dict(stats),
    exact_target_river_actor_IP_nodes=rows))
  item["verified_exact_positive_IP_river_nodes"]=[x for x in item["cases"][0]["exact_target_river_actor_IP_nodes"]
     if x["strict_40_70_CO_IP_combos"]>0]
  item["source_status"]="REAL_GTO_POSITIVE_TARGET" if item["verified_exact_positive_IP_river_nodes"] else "REAL_GTO_ZERO_TARGET"
  actual.append(item)
 assert len(actual)==3
 positive_flops={rank:sorted(set(x["flop"] for x in positives[str(rank)])) for rank in MODELS}
 r=dict(schema="NL2_B391_RANK115_116_PREREG_THREE_GENUINE_GTO_FIRST_V1",
  predeclared_original_flops=list(FLOPS),original_run_id=args.run_id,
  model_ids={str(rank):mid for rank,mid in MODELS.items()},
  original_poker_solver_pin=PIN,authentic_Rust_pin=RUST,
  source_spot="LMP_CO_BB",actor="CO_IP",exact_line=LINE,
  original_true_Rust_GTO_only_sources=actual,
  positive_named_public_river_actor_IP_by_model=positives,
  positive_distinct_flops_by_model={str(k):v for k,v in positive_flops.items()},
  preflop_LMP_169class_explicit_assumption_not_observed_NL2=True,
  NL2_partial_lock_only_after_GTO_strict_actor_positive=True,
  no_new_CERT_until_original_true_NL2_hero_IP_source_and_independent_three_flop_gate=True,
  no_2026_NL2_private_card_data_used=True,no_generic_texture_GTO_claim=True,
  CERT_MULTIBOARD=159,APPROX=233,EST=0,TOTAL=392,
  PR2_Draft_NEVER_MERGE=True)
 OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B391 ranks 115/116: three predeclared original LMP GTO-only full100bb flops\n\n"
  +"Candidates As9h2d, Js9h4d, QsJh4d were selected before seeing their Rust CFR results, "
  +"with exact b33-call / x-b50-call / x CO-IP node, 40/70 sequential legal combos and source SPR within 5%. "
  +"Only flops with genuine positive actor-IP GTO root may be scheduled for real partial NL2 lock, "
  +"not converted into CERT by texture inference. "
  +"; ".join(f"rank{k}: {len(v)} eligible distinct flops" for k,v in positive_flops.items())
  +". Preflop 169-class limped ranges ASSUMED, not observed NL2. "
  +"159 CERT / 233 APPROX /0 EST unchanged.\n")
 print("B391 original GTO-only LMP source triage",positive_flops,"eligible flops; no premature CERT 159/233")
if __name__=="__main__":main()
