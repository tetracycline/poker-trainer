#!/usr/bin/env python3
"""B382 exact 100bb BTN-IP GTO+NL2 partial Rust source SHA and full-street 40/70 reach."""
import argparse,hashlib,json,pathlib
from hu_sequential_cfr_reach import game_reach
D=pathlib.Path("data")
TARGET="b33 c/x b50 c/x"
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--downloads",type=pathlib.Path,required=True)
 ap.add_argument("--run-id",type=int,required=True); args=ap.parse_args()
 source=[];solved={}
 for ver in ("gto","exp_ip"):
  root=args.downloads/f"nl2-multiboard-B382_R107-BTN_BB-4s4h2d-{ver}"
  mp=root/"evidence"/f"BTN_BB-4s4h2d-{ver}.json"
  item=dict(version=ver,artifact=root.name,exists=mp.exists(),cases=[])
  if not mp.exists():
   item["excluded_reason"]="MISSING_OR_UNFINISHED_RUST_MANIFEST";source.append(item);continue
  assert (root/"evidence/poker-solver-pin.txt").read_text().strip()==PIN
  assert (root/"evidence/rust-pin.txt").read_text().strip()==RUST
  m=read(mp)
  assert (m["schema"],m["spot"],m["pot_family"],m["flop"],m["version"])==(
   "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","BTN_BB","SRP","4s4h2d",ver)
  assert (m["root_pot_bb"],m["root_remaining_bb"])==(5.5,97.5)
  assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
  assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
  assert m["flop_action_sizes"]==["33%","50%","75%","100%"]
  assert m["flop_line_policy"]=="oop-b33only" and m["selected_lines"]==["b33 c"]
  assert len(m["turns"])==1 and m["solved_cases"]==len(m["cases"])
  if m["failures"]:item["excluded_reason"]="REAL_RUST_SOLVE_FAILED"
  if not m["cases"]:item["excluded_reason"]="NO_ACTUAL_RUST_SUBGAME"
  fp=root/"solver/postflop"/m["file_flop"]
  assert fp.is_file() and sha(fp)==m["file_flop_sha256"]
  fr=read(fp);assert (fr["flop"],fr["pot"],fr["stack"])==("4s4h2d",550,9750)
  item.update(original_manifest_SHA256=sha(mp),authentic_flop_SHA256=sha(fp),
   original_flop_job_SHA256=sha(fp.with_suffix(".job.json")),
   actual_Rust_solved_cases=len(m["cases"]),real_failures=m["failures"])
  for c in m["cases"]:
   assert c["line"]=="b33 c" and c["turn"] in m["turns"]
   assert c["gto_gap_pct"] is not None and c["gto_gap_pct"]<=.5
   if ver=="exp_ip":
    assert c["hero_gap_pct"] is not None and c["hero_gap_pct"]<=.5
    assert any(int(p.get("n") or 0)>=500 and p["scope"].startswith("IMPUTED_HISTORY_FROM_TRUE") for p in m["locks"])
    assert any(v["nodes"]>0 for v in c["lock_stats"].values())
   p=root/"solver/postflop"/c["source_path"]
   assert p.is_file() and sha(p)==c["source_sha256"]
   d=read(p)
   assert (d["flop"],d["turn"],d["line0"])==("4s4h2d",c["turn"],"b33 c")
   masks,stats=game_reach(fr,d)
   matched=[]
   for n in d["nodes"]:
    if n["line"]!=TARGET or n["player"]!=1 or len(n["board"])!=10:continue
    q=masks["|".join((n["board"],n["line"],"1"))]
    matched.append(dict(public_board=n["board"],actor="BTN_IP",
     strict_40_70_combo_count=q["count"],actual_spr=round((d["stack"]-max(n["bets"]))/n["pot"],6),
     parent_actor_decisions=q["parent_actor_decisions"]))
   item["cases"].append(dict(turn=c["turn"],sha256=sha(p),
    GTO_gap_pct=c["gto_gap_pct"],hero_gap_pct=c["hero_gap_pct"],
    full_street_stats=dict(stats),matched_target_river_actor_IP_nodes=matched))
   solved[ver]=item["cases"][-1]
  source.append(item)
 paired=[]
 if "gto" in solved and "exp_ip" in solved and solved["gto"]["turn"]==solved["exp_ip"]["turn"]:
  g=solved["gto"];e=solved["exp_ip"]
  a={x["public_board"]:x for x in g["matched_target_river_actor_IP_nodes"] if x["strict_40_70_combo_count"]>0}
  b={x["public_board"]:x for x in e["matched_target_river_actor_IP_nodes"] if x["strict_40_70_combo_count"]>0}
  for board in sorted(set(a)&set(b)):
   x,y=a[board],b[board]
   if abs(x["actual_spr"]-y["actual_spr"])>1e-6:continue
   if abs(x["actual_spr"]-4.968)/max(x["actual_spr"],1)>.05:continue
   paired.append(dict(exact_public_board=board,GTO_strict=x["strict_40_70_combo_count"],
    NL2_hero_IP_strict=y["strict_40_70_combo_count"],SPR=x["actual_spr"],
    GTO_source_sha256=g["sha256"],NL2_source_sha256=e["sha256"]))
 s=read(D/"nl2_hu_multiboard_status_v47_b364_rank96.json")
 assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"])==(159,233,0)
 assert s["records"]["ln-ipfr-r_model-ujl14x"]["label"]=="APPROX"
 p=read(D/"nl2_hu_b379_rank107_7s5h3d_6c_true_gto_nl2_ip_strict_pair.json")
 assert p["one_distinct_flop_not_three"] and p["rank"]==107
 report=dict(schema="NL2_B382_RANK107_THIRD_DISTINCT_GENUINE_SOLVE_SOURCE_STRICT_V1",
  rank=107,model_id="ln-ipfr-r_model-ujl14x",source_run_id=args.run_id,
  source_solver_pin=PIN,source_rust_pin=RUST,
  spot="BTN_BB",flop="4s4h2d",exact_actor="BTN_IP",exact_line=TARGET,
  true_original_GTO_and_NL2_partial_sources=source,
  strict_40_70_source_paired_actor_IP_river_nodes=paired,
  claimed_new_distinct_cert_flops=(1 if paired else 0),
  B379_prior_distinct_7s5h3d_proven=True,
  strict_one_original_flop_not_two_river_nodes=True,
  NL2_pool_marginal_proxy_not_measured_opponent_private_hand=True,
  needs_independent_three_flop_full_model_source_gate=True,
  no_early_certification=True,CERT_MULTIBOARD=159,APPROX=233,EST=0,
  PR2_remains_draft_never_merge=True)
 path=D/"nl2_hu_b382_rank107_4s4h2d_true_solve_strict_source.json"
 path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 pathlib.Path("docs/NL2_HU_B382_RANK107_THIRD_TRUE_FLOP_SOURCE.md").write_text(
  "# B382 rank107 additional-flop original true Rust source only\n\n"
  +f"Actual strict same-board GTO/NL2 IP source pairs: {len(paired)}. "
  +"Only source SHA, genuine Rust solve, actor/SPR/history and exact 40%-70% cross-street reach count. "
  +"Previously 7s5h3d and source-indexed Jh9d6s are separate flops; all three still need an independent promotion audit. "
  +"Never extrapolate generic textures or treat NL2 pooled marginals as exact opponent hole-card frequency. "
  +"159 CERT / 233 APPROX unchanged.\n")
 print("B382 original paired exact river nodes:",len(paired),"; 159 CERT/233 APPROX, no premature promotion")
if __name__=="__main__":main()
