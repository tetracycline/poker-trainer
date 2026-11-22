#!/usr/bin/env python3
"""B388 independent genuine GTO+NL2 IP paired source at frozen QsJh4d/7s.
Original B387 GTO root is NOT re-solved. New Rust EXP_IP has its own original
full flop and partially locked turn; never certify a generic texture.
"""
import argparse,hashlib,json,pathlib
from hu_sequential_cfr_reach import game_reach

D=pathlib.Path("data")
GTO_ROOT="f60ffafdea6058eb23ac0f314be28eac14d4ff97e5ac8c92faf2e84a031c2bcf"
GTO_TURN="ebfd419f66fcbeca371b4542e57838474d404f1ab566c01c607192ddb80337b7"
GTO_MANIFEST="c9a2fcc854ab6e586aabe176a311f2d4988597dd50913855b5033daf71b814c3"
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
MID="ln-ipfr-r_model-ujl14x"
LINE="b33 c/x b50 c/x"
EXPECTED={"4dJhQs7sJc":4,"4dJhQs7s6c":8}
OUT=D/"nl2_hu_b388_rank107_qsjh4d_real_gto_nl2_ip_pair.json"
DOC=pathlib.Path("docs/NL2_HU_B388_RANK107_QSJH4D_TRUE_NL2_PAIR.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def analyze(mp,base,version):
 m=load(mp)
 assert (m["schema"],m["pot_family"],m["spot"],m["version"],m["flop"])==(
    "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","SRP","BTN_BB",version,"QsJh4d")
 assert (m["root_pot_bb"],m["root_remaining_bb"])==(5.5,97.5)
 assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
 assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
 assert m["flop_action_sizes"]==["33%","50%","75%","100%"]
 assert m["selected_lines"]==["b33 c"] and m["turns"]==["7s"]
 assert m["flop_line_policy"]=="oop-b33only"
 assert len(m["solver_pin"])==len(m["solver_ranges_sha256"])==len(m["pool_source_sha256"])==64
 assert m["solved_cases"]==len(m["cases"])
 root=base/m["file_flop"]
 assert root.is_file() and sha(root)==m["file_flop_sha256"]
 fr=load(root)
 assert (fr["flop"],fr["pot"],fr["stack"])==("QsJh4d",550,9750)
 sources=[]
 for c in m["cases"]:
  assert (c["line"],c["turn"])==("b33 c","7s")
  assert c["gto_gap_pct"] is not None and 0<=c["gto_gap_pct"]<=.5
  if version=="gto":
   assert c["status"]=="GTO_EXACT_ONLY" and c["hero_gap_pct"] is None
  else:
   assert c["hero_gap_pct"] is not None and 0<=c["hero_gap_pct"]<=.5
   assert c["status"]=="NL2_IMPUTED_MARGINAL_LOCKED_EXPERIMENT"
   assert any(int(x.get("n") or 0)>=500 and str(x.get("scope","")).startswith("IMPUTED_HISTORY_FROM_TRUE")
              for x in m["locks"])
   assert any(int(x.get("nodes",0))>0 for x in c["lock_stats"].values())
  sub=base/c["source_path"]
  assert sub.is_file() and sha(sub)==c["source_sha256"]
  data=load(sub)
  assert (data["flop"],data["turn"],data["line0"])==("QsJh4d","7s","b33 c")
  masks,stats=game_reach(fr,data)
  exact={}
  for n in data["nodes"]:
   if n["player"]!=1 or n["line"]!=LINE or len(n["board"])!=10:continue
   q=masks["|".join((n["board"],n["line"],"1"))]
   exact[n["board"]]=dict(public_board=n["board"],strict_combos=q["count"],
    node_spr=round((data["stack"]-max(n["bets"]))/n["pot"],6),
    parent_actor_decisions=q["parent_actor_decisions"])
  assert set(exact)==set(EXPECTED)
  sources.append(dict(original_subgame_SHA256=sha(sub),original_turn="7s",
    gto_gap_pct=c["gto_gap_pct"],hero_gap_pct=c["hero_gap_pct"],
    full_street_sequential_reach_stats=dict(stats),exact_hero_IP_river_nodes=exact))
 return m,dict(original_manifest_SHA256=sha(mp),original_flop_SHA256=sha(root),
   original_flop_job_SHA256=sha(root.with_suffix(".job.json")),
   genuine_Rust_solved_cases=m["solved_cases"],failures=m["failures"],skipped=m["skipped"],
   preflop_CFR_data_SHA256=m["preflop_ranges"]["full_sha256"],
   pool_source_SHA256=m["pool_source_sha256"],partial_lock_provenance=m["locks"] if version!="gto" else [],
   subgames=sources)
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--original-gto",type=pathlib.Path,required=True)
 p.add_argument("--new-exp",type=pathlib.Path,required=True)
 p.add_argument("--run-id",type=int,required=True)
 args=p.parse_args()
 g=args.original_gto
 gm=g/"evidence/BTN_BB-QsJh4d-gto.json"
 assert gm.is_file()
 assert sha(gm)==GTO_MANIFEST
 assert (g/"evidence/poker-solver-pin.txt").read_text().strip()==PIN
 assert (g/"evidence/rust-pin.txt").read_text().strip()==RUST
 _,gto=analyze(gm,g/"solver/postflop","gto")
 assert (gto["original_flop_SHA256"],gto["subgames"][0]["original_subgame_SHA256"])==(GTO_ROOT,GTO_TURN)
 previous=load(D/"nl2_hu_b387_rank107_gto_first_three_frozen_flops.json")
 assert previous["candidate_flops_eligible_for_future_matching_real_NL2_IP_partial_lock"]==["QsJh4d"]
 assert previous["strict_positive_exact_board_GTO_sources"]
 assert all(gto["subgames"][0]["exact_hero_IP_river_nodes"][b]["strict_combos"]==n for b,n in EXPECTED.items())
 s=load(D/"nl2_hu_multiboard_status_v47_b364_rank96.json")
 assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(159,233,0,392)
 assert (s["records"][MID]["label"],s["records"][MID]["frequency_rank"])==("APPROX",107)
 exp_path=args.new_exp/"evidence/BTN_BB-QsJh4d-exp_ip.json"
 result=None
 if exp_path.is_file():
  assert (args.new_exp/"evidence/poker-solver-pin.txt").read_text().strip()==PIN
  assert (args.new_exp/"evidence/rust-pin.txt").read_text().strip()==RUST
  _,result=analyze(exp_path,args.new_exp/"solver/postflop","exp_ip")
  assert (result["preflop_CFR_data_SHA256"],result["pool_source_SHA256"])==(
     gto["preflop_CFR_data_SHA256"],gto["pool_source_SHA256"])
 evidence=[]
 if result and result["genuine_Rust_solved_cases"]==1 and not result["failures"]:
  for board,expected in EXPECTED.items():
   gnode=gto["subgames"][0]["exact_hero_IP_river_nodes"][board]
   enode=result["subgames"][0]["exact_hero_IP_river_nodes"][board]
   assert gnode["strict_combos"]==expected
   if enode["strict_combos"]<=0:continue
   assert abs(gnode["node_spr"]-enode["node_spr"])<1e-5
   assert abs(gnode["node_spr"]-4.968)/max(1,gnode["node_spr"])<=.05
   evidence.append(dict(flop="QsJh4d",turn="7s",exact_public_board=board,actor="BTN_IP",
     exact_line=LINE,original_GTO_sha256=GTO_TURN,
     new_actual_partial_NL2_sha256=result["subgames"][0]["original_subgame_SHA256"],
     GTO_strict_40_70_combos=gnode["strict_combos"],NL2_IP_strict_40_70_combos=enode["strict_combos"],
     original_GTO_SPR=gnode["node_spr"],partial_NL2_SPR=enode["node_spr"]))
 out=dict(schema="NL2_HU_B388_RANK107_GENUINE_GTO_AND_ACTUAL_NL2_IP_QSJH4D_PARTIAL_V1",
  source_run_B387_GTO=45023132316,source_run_B388_EXP=args.run_id,
  model_id=MID,rank=107,flop="QsJh4d",turn="7s",spot="BTN_BB",
  exact_history=LINE,actor="BTN_IP",preflop_solver_pin=PIN,rust_pin=RUST,
  original_GTO_source=gto,real_NL2_partial_source=result,
  exact_paired_legal_river_nodes=evidence,
  distinct_new_qualified_flop_count=1 if evidence else 0,
  partial_lock_is_NL2_pool_marginal_proxy_not_private_hand_observation=True,
  no_generic_texture_CERT=True,no_promote_before_independent_three_flop_source_gate=True,
  original_V47_CERT=159,original_V47_APPROX=233,EST=0,
  B368_not_rerun=True,PR2_remains_draft_never_merge=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 DOC.write_text("# B388 rank107 exact QsJh4d/7s matched real Rust EXP_IP\n\n"
   +f"Original B387 SHA-pinned GTO actor-IP strict 40/70 combo counts 4 and 8. "
   +f"Actual new partially locked NL2 IP Rust output: {'available' if result else 'MISSING'}. "
   +f"Strict GTO/NL2 paired river nodes: {len(evidence)}. "
   +"Pool marginal frequencies are NOT villain private-card conditional observations. "
   +"Certification for rank107 requires an independent three-distinct-flop gate; "
   +"B388 itself leaves 159 CERT / 233 APPROX unchanged.\n")
 print("B388 SHA-gated genuine original GTO+NL2 partial IP:",len(evidence),"exact river pairs; 159 CERT /233 APPROX")
if __name__=="__main__":main()
