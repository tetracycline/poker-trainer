#!/usr/bin/env python3
"""B431: pair the one B429 texture-diverse GTO-positive 7c6h5d flop with a genuine NL2-IP partial lock.
Source-only; no CERT from one flop. Same exact CO-IP line, runout, SPR and strict sequential 40/70 hero combos.
"""
import argparse,hashlib,json,pathlib
from hu_sequential_cfr_reach import game_reach
D=pathlib.Path("data")
B429=D/"nl2_hu_b429_r216218_three_new_texture_gto_sources.json"
OUT=D/"nl2_hu_b431_r216218_one_new_texture_nl2_ip_pair.json"
DOC=pathlib.Path("docs/NL2_HU_B431_R216218_TRUE_NEW_TEXTURE_NL2_IP_PAIR.md")
FLOP="7c6h5d"
RANKS=(216,218)
LINE="x b50 c/x b50 c/x"
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(root,version,run_id):
 mp=root/"evidence"/f"CO_BB-{FLOP}-{version}.json"
 assert mp.is_file()
 assert (root/"evidence/poker-solver-pin.txt").read_text().strip()==PIN
 assert (root/"evidence/rust-pin.txt").read_text().strip()==RUST
 m=read(mp)
 assert (m["schema"],m["spot"],m["pot_family"],m["version"],m["flop"])==(
  "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","CO_BB","SRP",version,FLOP)
 assert (m["root_pot_bb"],m["root_remaining_bb"])==(5.5,97.5)
 assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
 assert (m["flop_size_profile"],m["restricted_tree_assumption"])==("full",False)
 assert m["flop_action_sizes"]==["33%","50%","75%","100%"]
 if m["flop_line_policy"]=="checked-b50only":
  assert m["selected_lines"]==["x b50 c"]
 else:
  assert (m["flop_line_policy"],m["selected_lines"])==("checked-b50b100only",["x b50 c","x b100 c"])
 assert len(m["turns"])==1 and m["solved_cases"]==len(m["cases"]) and not m["failures"]
 fp=root/"solver/postflop"/m["file_flop"]
 assert fp.is_file() and sha(fp)==m["file_flop_sha256"]
 fr=read(fp);assert (fr["flop"],fr["pot"],fr["stack"])==(FLOP,550,9750)
 real=[]
 for c in m["cases"]:
  assert c["line"]=="x b50 c" and c["turn"] in m["turns"]
  assert c["gto_gap_pct"] is not None and 0<=c["gto_gap_pct"]<=.5
  if version=="gto":
   assert c["status"]=="GTO_EXACT_ONLY" and c["hero_gap_pct"] is None
  else:
   assert c["status"]=="NL2_IMPUTED_MARGINAL_LOCKED_EXPERIMENT"
   assert c["hero_gap_pct"] is not None and 0<=c["hero_gap_pct"]<=.5
  sub=root/"solver/postflop"/c["source_path"]
  assert sub.is_file() and sha(sub)==c["source_sha256"]
  d=read(sub);assert (d["flop"],d["turn"],d["line0"])==(FLOP,c["turn"],"x b50 c")
  seq,stats=game_reach(fr,d);nodes={}
  for n in d["nodes"]:
   if n["player"]!=1 or n["line"]!=LINE or len(n["board"])!=10:continue
   q=seq["|".join((n["board"],n["line"],"1"))]
   nodes[n["board"]]=dict(public_board=n["board"],strict_40_70_IP_hero_combos=q["count"],
    exact_SPR=round((d["stack"]-max(n["bets"]))/n["pot"],6),
    parent_actor_decisions=q["parent_actor_decisions"])
  real.append(dict(line=c["line"],turn=c["turn"],source_sha256=c["source_sha256"],
   original_GTO_gap_pct=c["gto_gap_pct"],original_hero_gap_pct=c["hero_gap_pct"],
   actor_IP_target_nodes=nodes,strict_fullstreet_reach_stats=dict(stats)))
 return dict(status="GENUINE_RUST_EXACT_SOURCE",manifest_sha256=sha(mp),
  root_original_Rust_SHA256=sha(fp),original_root_job_sha256=sha(fp.with_suffix(".job.json")),
  preflop_source_SHA256=m["preflop_ranges"]["full_sha256"],pool_stats_SHA256=m["pool_source_sha256"],
  manifest=m,real_cases=real,source_run_id=run_id)
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--gto-root",type=pathlib.Path,required=True)
 ap.add_argument("--exp-root",type=pathlib.Path,required=True)
 ap.add_argument("--run-id",type=int,required=True)
 a=ap.parse_args()
 base=read(D/"nl2_hu_multiboard_status_v50_b417_rank166.json")
 b=read(B429)
 assert (base["CERT_MULTIBOARD"],base["APPROX"],base["EST"],base["TOTAL"])==(163,229,0,392)
 assert b["schema"]=="NL2_B429_R216218_THREE_NEW_TEXTURE_GENUINE_GTO_FIRST_V1"
 assert b["original_run_id"]==45055601616
 assert b["distinct_new_GTO_positive_flops_by_rank"]=={"216":[FLOP],"218":[FLOP]}
 assert b["real_original_GTO_only_solve_sources"][2]["source_status"]=="ORIGINAL_GTO_ANY_TARGET_POSITIVE"
 G=check(a.gto_root,"gto",45055601616);E=check(a.exp_root,"exp_ip",a.run_id)
 assert G["status"]==E["status"]=="GENUINE_RUST_EXACT_SOURCE"
 assert G["preflop_source_SHA256"]==E["preflop_source_SHA256"]
 assert G["pool_stats_SHA256"]==E["pool_stats_SHA256"]
 source=b["real_original_GTO_only_solve_sources"][2]
 assert G["manifest_sha256"]==source["original_manifest_SHA256"]
 assert G["root_original_Rust_SHA256"]==source["original_root_SHA256"]
 pins={str(k):[] for k in RANKS};positives={str(k):[] for k in RANKS}
 for rank in RANKS:
  row=next(x for x in b["exact_actor_IP_positive_river_nodes_by_model"][str(rank)] if x["flop"]==FLOP)
  gc=next(x for x in G["real_cases"] if x["source_sha256"]==row["original_GTO_sha256"] and x["turn"]==row["turn"])
  ec=next(x for x in E["real_cases"] if x["turn"]==row["turn"] and x["line"]=="x b50 c")
  board=row["public_board"]
  g=gc["actor_IP_target_nodes"][board];n=ec["actor_IP_target_nodes"].get(board)
  assert g["strict_40_70_IP_hero_combos"]==row["legal_full_street_40_70_combos"]>0
  assert n and n["strict_40_70_IP_hero_combos"]>0
  assert abs(g["exact_SPR"]-n["exact_SPR"])<1e-5
  expected=base["records"][b["models"][str(rank)]["model_id"]]["assumed_model_node_spr"]
  assert abs(g["exact_SPR"]-expected)/max(1,g["exact_SPR"])<=.05
  item=dict(rank=rank,flop=FLOP,turn=row["turn"],exact_public_board=board,actor="CO_IP",
   exact_history=LINE,actual_SPR=g["exact_SPR"],
   GTO_strict_40_70_combos=g["strict_40_70_IP_hero_combos"],
   actual_NL2_IP_strict_40_70_combos=n["strict_40_70_IP_hero_combos"],
   original_GTO_source_run=45055601616,original_GTO_sha256=row["original_GTO_sha256"],
   new_NL2_IP_source_run=a.run_id,new_NL2_IP_sha256=ec["source_sha256"])
  positives[str(rank)].append(item);pins[str(rank)].append(item)
 out=dict(schema="NL2_B431_RANK216_218_ONE_NEW_TEXTURE_ACTUAL_RUST_GTO_NL2_IP_PAIR_V1",
  B429_original_GTO_source_sha256=sha(B429),original_GTO_run=45055601616,
  new_NL2_IP_run=a.run_id,spot="CO_BB",actor="CO_IP",exact_line=LINE,
  source_poker_solver_pin=PIN,original_Rust_pin=RUST,
  source_evidence=[dict(flop=FLOP,original_GTO=G,actual_partial_NL2_IP=E,
   original_GTO_artifact="nl2-multiboard-B429_R216218_GTO_FIRST-CO_BB-7c6h5d-gto",
   new_NL2_IP_artifact="nl2-multiboard-B431_R216218_NL2_IP-CO_BB-7c6h5d-exp_ip")],
  positive_40_70_named_river_pairs_by_rank=positives,
  new_distinct_qualifying_flops_by_rank={"216":[FLOP],"218":[FLOP]},
  original_preflop_CFR_not_NL2_observed_private_actions=True,
  opponent_NL2_is_pool_marginal_proxy_not_exact_private_hand=True,
  no_automatic_CERT_while_no_three_independent_original_sources=True,
  no_2026_private_hand_NL2_observations_used=True,
  CERT_MULTIBOARD=163,APPROX=229,EST=0,PR2_remains_draft_unmerged=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B431 ranks216/218: genuine NL2-IP partial-lock on new LOW-texture 7c6h5d\n\n"
  "B429 original full100bb Rust GTO positive exact CO-IP runout is paired with this actual "
  "B431 NL2-IP partially locked Rust source. Only the named board, x b50 c/x b50 c/x, "
  "same turn and SPR within 5%, and sequential 40/70 hero-combo reach qualify. "
  "One new flop is not enough for CERT; no generic texture or villain private-card claim. "
  "163 CERT /229 APPROX unchanged.\n")
 print("PASS B431 true GTO+NL2 IP paired source for LOW-texture rank216/218; no premature CERT")
if __name__=="__main__":main()
