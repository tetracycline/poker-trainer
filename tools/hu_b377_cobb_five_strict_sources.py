#!/usr/bin/env python3
"""B377: source SHA, 40/70 combo reach, actor and per-line gates for five CO_IP APPROX cells.
Each Rust run is real, but alone is NOT a 3–5-flop model certification.
"""
import argparse,collections,hashlib,json,pathlib
from hu_sequential_cfr_reach import game_reach
D=pathlib.Path("data")
FLOPS=("7s5h3d","8s8h3d")
VERSIONS=("gto","exp_ip")
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
FLOP_LINES=("x b50 c","x b100 c")
LINES={
 166:"x b100 c/x x/x",
 214:"x b100 c/x b50 c/x",
 216:"x b50 c/x b50 c/x",
 218:"x b50 c/x b50 c/x",
 219:"x b100 c/x b50 c/x",
}
MIDS={
 166:"ln-ipfr-r_model-1spq1ko",
 214:"ln-ipfr-r_model-1t7q0mn",
 216:"ln-ipfr-r_model-7kv23r",
 218:"ln-ipfr-r_model-h0c7q7",
 219:"ln-ipfr-r_model-kp19if"
}
OUT=D/"nl2_hu_b377_co_bb_five_approx_two_fresh_true_gto_nl2_ip_strict_source.json"
DOC=pathlib.Path("docs/NL2_HU_B377_FIVE_CO_BB_APPROX_STRICT_PAIR_SOURCE.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument("--downloads",type=pathlib.Path,required=True)
 args=p.parse_args();root=args.downloads
 results=[];exact={}
 for flop in FLOPS:
  for ver in VERSIONS:
   tag=f"nl2-multiboard-B377_COBB_FIVE-CO_BB-{flop}-{ver}"
   folder=root/tag;mp=folder/"evidence"/f"CO_BB-{flop}-{ver}.json"
   part=dict(flop=flop,version=ver,artifact=tag,manifest_present=mp.is_file(),cases=[],explicit_negatives=[])
   if not mp.is_file():
    part["explicit_negatives"].append("NO_GENUINE_RUST_MANIFEST_NO_CERT")
    results.append(part);continue
   m=read(mp)
   assert (m["schema"],m["spot"],m["pot_family"],m["version"],m["flop"])==(
     "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","CO_BB","SRP",ver,flop)
   assert (m["root_pot_bb"],m["root_remaining_bb"])==(5.5,97.5)
   assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
   assert not m["restricted_tree_assumption"] and m["flop_size_profile"]=="full"
   assert m["flop_action_sizes"]==["33%","50%","75%","100%"]
   assert m["flop_line_policy"]=="checked-b50b100only"
   assert m["selected_lines"]==list(FLOP_LINES) and len(m["turns"])==1
   assert m["turn_sizing_mode"]=="default"
   assert m["solved_cases"]==len(m["cases"])
   assert (folder/"evidence/poker-solver-pin.txt").read_text().strip()==PIN
   assert (folder/"evidence/rust-pin.txt").read_text().strip()==RUST
   original=folder/"solver/postflop"/m["file_flop"]
   assert original.is_file() and sha(original)==m["file_flop_sha256"]
   fr=read(original)
   assert (fr["flop"],fr["pot"],fr["stack"])==(flop,550,9750)
   part.update(original_flop_source_SHA256=sha(original),
     actual_original_Rust_manifest_SHA256=sha(mp),
     pool_source_sha256=m["pool_source_sha256"],
     preflop_CFR_data_pin=m["preflop_ranges"]["full_sha256"],
     solved_cases=m["solved_cases"],genuine_solve_failures=m["failures"],
     exact_unreached_turn_negatives=m["skipped"],
     real_NL2_pooled_marginal_history_locked_not_private_holecard_data=(ver=="exp_ip"))
   if m["failures"]:
    part["explicit_negatives"].append("GENUINE_SOLVER_FAILURE_NO_CERT")
   for c in m["cases"]:
    assert c["line"] in FLOP_LINES and c["turn"] in m["turns"]
    assert c["gto_gap_pct"] is not None and c["gto_gap_pct"]<=.5
    if ver=="exp_ip":
     assert c["hero_gap_pct"] is not None and c["hero_gap_pct"]<=.5
    file=folder/"solver/postflop"/c["source_path"]
    assert file.is_file() and sha(file)==c["source_sha256"]
    sub=read(file)
    assert (sub["flop"],sub["turn"],sub["line0"])==(flop,c["turn"],c["line"])
    masks,stats=game_reach(fr,sub)
    rows=[]
    for n in sub["nodes"]:
     if n["player"]!=1 or len(n["board"])!=10 or n["line"] not in set(LINES.values()):continue
     key="|".join((n["board"],n["line"],str(n["player"])))
     q=masks[key]
     if q["count"]>0:
      rows.append(dict(board=n["board"],action_line=n["line"],strict_actor_IP_combos=q["count"],
                       SPR=round((sub["stack"]-max(n["bets"]))/n["pot"],6)))
    item=dict(flop=flop,version=ver,turn=c["turn"],flop_line=c["line"],
      source_sha256=sha(file),gto_gap_pct=c["gto_gap_pct"],hero_gap_pct=c["hero_gap_pct"],
      actual_strict_40_70_stats=dict(stats),
      target_line_actor_IP_legally_reached_river_nodes=rows)
    part["cases"].append(item)
    exact[(flop,ver,c["line"])]=item
   results.append(part)
 paired=[]
 for flop in FLOPS:
  for line in sorted(set(LINES.values())):
   fst=line.split("/")[0]
   g,e=exact.get((flop,"gto",fst)),exact.get((flop,"exp_ip",fst))
   if not g or not e or g["turn"]!=e["turn"]:continue
   gnodes={n["board"]:n for n in g["target_line_actor_IP_legally_reached_river_nodes"] if n["action_line"]==line}
   enodes={n["board"]:n for n in e["target_line_actor_IP_legally_reached_river_nodes"] if n["action_line"]==line}
   matched=[]
   for board in sorted(set(gnodes)&set(enodes)):
    a,b=gnodes[board],enodes[board]
    if a["strict_actor_IP_combos"]<=0 or b["strict_actor_IP_combos"]<=0:continue
    if abs(a["SPR"]-b["SPR"])/max(1.,a["SPR"])>.05:continue
    matched.append(dict(board=board,GTO_strict_combos=a["strict_actor_IP_combos"],
          genuine_NL2_hero_lock_strict_combos=b["strict_actor_IP_combos"],
          actual_GTO_SPR=a["SPR"],actual_NL2_SPR=b["SPR"]))
   if matched:
    paired.append(dict(flop=flop,turn=g["turn"],exact_line=line,
      source_GTO_sha256=g["source_sha256"],source_NL2_sha256=e["source_sha256"],
      same_exact_named_river_40_70_matched_nodes=matched))
 s=read(D/"nl2_hu_multiboard_status_v47_b364_rank96.json")
 assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(159,233,0,392)
 assert all(s["records"][mid]["label"]=="APPROX" and s["records"][mid]["frequency_rank"]==rank
   for rank,mid in MIDS.items())
 per_rank={str(rank):[x for x in paired if x["exact_line"]==line]
           for rank,line in LINES.items()}
 out=dict(schema="NL2_HU_B377_CO_BB_FIVE_APPROX_TWO_NEW_100BB_ORIGINAL_SHA_GATED_CFR_V1",
  no_2026_live_data_used=True,
  models_and_frozen_lines={str(k):dict(model_id=MIDS[k],exact_line=LINES[k]) for k in sorted(MIDS)},
  source_flops=list(FLOPS),pre_registered_b370_first10_proven_one_flop="Js9h4d",
  source_solver_pin=PIN,source_rust_pin=RUST,
  actual_original_artifacts=results,
  GTO_plus_genuine_NL2_partial_actor_IP_strict_source_pairs=paired,
  matched_new_distinct_flops_by_model=per_rank,
  certify_only_after_three_distinct_authenticated_flops_and_spr_gate=True,
  no_certification_from_missing_or_zero_combo_board=True,
  no_observed_NL2_per_private_card_conditional_rates=True,
  no_general_50pct_pot_recommendation=True,
  CERT_MULTIBOARD=159,APPROX=233,EST=0,
  PR2_remains_draft_never_merge=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B377 two fresh original CO_BB flops for five fixed APPROX models\n\n"
   +"Source blind original GTO and authentic NL2 CO-IP partial solves on 7s5h3d and 8s8h3d. "
   +"Every new named exact board requires 40/70 full-street legal reach, correct actor, exact history and SPR. "
   +"Results are source evidence only; **159 CERT / 233 APPROX** remain until independent 3-flop model gate.\n\n"
   +"Eligible new exact flop counts by rank: "+", ".join(
      f"{k}: {len(set(x['flop'] for x in v))}" for k,v in per_rank.items())+"\n")
 print("B377 source-only PASS",{"models":len(MIDS),"flops":len(FLOPS),
    "actual_paired_exact_line_flops":{k:len(set(x["flop"] for x in v)) for k,v in per_rank.items()},
    "CERT":159,"APPROX":233})
if __name__=="__main__":main()
