#!/usr/bin/env python3
"""B373: independently validate completed genuine Rust source, never certify a one-flop model."""
import hashlib,json,pathlib,sys
D=pathlib.Path("data")
S="nl2_hu_multiboard_status_v47_b364_rank96.json"
GTO="b2aeb59fe69c73c42c4c848eed27df9c055f65a7503bd9d4ee07ab07b3c89822"
GMAN="a8b98dbf6c03c6282d33081d9937d58235b3c5f4bec348b7da6cd6fb200e0cfe"
GTOTURN="ecb792caaf13c22d09317c28349152c549c6b4596e6301c63f6e650bbb504aa0"
LOCK="8ea00b1942b607bd862cac0ccb144a0823f696f337695ed840f0a48a9d674e21"
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=pathlib.Path(sys.argv[1])
 a=r/"evidence/LMP_CO_BB-9s6h3d-exp_oop-turn-only.json"
 b=r/"original/evidence/LMP_CO_BB-9s6h3d-gto.json"
 f=r/"solver/postflop/out/LMP_CO_BB/exp_oop/9s6h3d_multiboard.json"
 t=r/"solver/postflop/out/LMP_CO_BB/exp_oop/9s6h3d_b33c_Ts.json"
 j=r/"solver/postflop/out/LMP_CO_BB/exp_oop/9s6h3d_b33c_Ts.job.json"
 for path in (a,b,f,t,j,r/"original/evidence/poker-solver-pin.txt",r/"original/evidence/rust-pin.txt"):
  assert path.is_file(),path
 assert (r/"original/evidence/poker-solver-pin.txt").read_text().strip()==SOLVER
 assert (r/"original/evidence/rust-pin.txt").read_text().strip()==RUST
 m,g,root,turn,job=map(read,(a,b,f,t,j))
 assert (m["schema"],m["spot"],m["version"],m["flop"],m["pot_family"])==("NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","LMP_CO_BB","exp_oop","9s6h3d","LMP")
 assert (g["schema"],g["spot"],g["version"],g["flop"])==("NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1","LMP_CO_BB","gto","9s6h3d")
 assert (m["root_pot_bb"],m["root_remaining_bb"])==(2.5,99.0)==(g["root_pot_bb"],g["root_remaining_bb"])
 assert m["preflop_ranges"]["source"]==g["preflop_ranges"]["source"]=="ASSUMED_EXPLICIT_169CLASS"
 assert m["flop_size_profile"]==g["flop_size_profile"]=="full"
 assert not m["restricted_tree_assumption"] and not g["restricted_tree_assumption"]
 assert m["flop_action_sizes"]==g["flop_action_sizes"]==["33%","50%","75%","100%"]
 assert m["selected_lines"]==g["selected_lines"]==["b33 c"] and m["turns"]==g["turns"]==["Ts"]
 assert m["turn_sizing_mode"]=="exact-b50-only"
 assert m["turn_subgame_sizing"]==g["turn_subgame_sizing"]=={"oop":"50%","ip":"50%"}
 assert m["solver_pin"]==g["solver_pin"] and m["solver_ranges_sha256"]==g["solver_ranges_sha256"]
 assert m["n_NL2_hands"]==2334487 and len(m["pool_source_sha256"])==64
 assert m["solved_cases"]==g["solved_cases"]==1 and not m["failures"] and not g["failures"]
 assert not m["skipped"] and not g["skipped"] and len(m["cases"])==len(g["cases"])==1
 assert digest(b)==GMAN and digest(f)==m["file_flop_sha256"]==g["file_flop_sha256"]==GTO
 p=m["authenticated_original_gto_parent"]
 assert (p["original_run_id"],p["original_artifact_id"])==(45013144124,14751218545)
 assert p["original_GTO_root_sha256"]==GTO and p["original_GTO_manifest_sha256"]==GMAN
 assert p["flop_is_original_unlocked_GTO_not_fully_hero_NL2_locked"] and p["genuine_NL2_partial_lock_only_on_downstream_turn_and_river"]
 assert g["cases"][0]["source_sha256"]==GTOTURN
 c=m["cases"][0]
 assert (c["line"],c["turn"],c["status"])==("b33 c","Ts","NL2_IMPUTED_MARGINAL_LOCKED_EXPERIMENT")
 assert digest(t)==c["source_sha256"]==LOCK
 assert (turn["flop"],turn["turn"])==("9s6h3d","Ts")
 assert (job["flop"],job["turn"],str(job["hero"]))==("9s6h3d","Ts","0")
 assert c["source_node_count"]==len(turn["nodes"]) and c["true_river_nodes"]==sum(len(n["board"])==10 for n in turn["nodes"])
 assert 0<=c["gto_gap_pct"]<=.5 and 0<=c["hero_gap_pct"]<=.5
 assert abs(c["gto_gap_pct"]-turn["info"]["gto_expl_pct"])<1e-9
 assert abs(c["hero_gap_pct"]-turn["info"]["hero_gap_pct"])<1e-9
 assert any(v["nodes"]>0 for v in c["lock_stats"].values())
 marginal=[x for x in m["locks"] if x["scope"] in ("IMPUTED_HISTORY_FROM_TRUE_STREET_BY_SIZE_MARGINAL","IMPUTED_HISTORY_FROM_TRUE_STREET_RAISE_MARGINAL") and x.get("n",0)>0]
 fallback=[x for x in m["locks"] if x["scope"]=="ASSUMED_HISTORY_RATE_OR_SIZE" and x.get("n",0)==0]
 assert (len(marginal),len(fallback),len(m["locks"]))==(15,4,19)
 assert all(x["scope"]!="PINNED_MEASURED_NL2_SOURCE" for x in m["locks"])
 named=[x for x in turn["nodes"] if x["line"]=="b33 c/b50 c/" and x["player"]==0 and len(x["board"])==10]
 assert len(named)==2 and len({x["board"] for x in named})==2
 assert all(x["pot"]==832 and x["bets"]==[208,208] for x in named)
 s=read(D/S)
 mid="ln-iso-lmp_r_model-1aov4pd"
 assert (s["schema"],s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==("NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96",159,233,0,392)
 assert s["records"][mid]["label"]=="APPROX"
 out=dict(schema="NL2_HU_B373_COMPLETED_ORIGINAL_GTO_PLUS_ACTUAL_RUST_NL2_PARTIAL_TURN_V1",
  run_id=45016548530,artifact_id=14752470971,original_gto_run_id=45013144124,
  original_gto_artifact_id=14751218545,model_id=mid,rank=27,
  source_solver_commit=SOLVER,source_rust_commit=RUST,
  original_gto_root_sha256=GTO,original_gto_manifest_sha256=GMAN,
  original_gto_turn_sha256=GTOTURN,real_nl2_turn_rust_sha256=LOCK,
  real_nl2_source_manifest_sha256=digest(a),original_nl2_turn_job_sha256=digest(j),
  actor="BB_OOP",pot="LMP_100bb",flop="9s6h3d",turn="Ts",exact_line="b33 c/b50 c/",
  exact_river_public_boards=sorted(x["board"] for x in named),
  real_rust_gto_gap_pct=c["gto_gap_pct"],real_rust_hero_gap_pct=c["hero_gap_pct"],
  actually_activated_Rust_lock_node_patterns={k:v["nodes"] for k,v in c["lock_stats"].items()},
  actual_NL2_measured_pooled_marginal_patterns_history_imputed=len(marginal),
  assumed_history_fallback_patterns=len(fallback),
  no_observed_opponent_private_hand_conditionals=True,
  not_original_flop_fully_NL2_locked=True,
  strict_sequential_full_street_combo_gate_pending=True,
  only_one_distinct_genuine_flop=True,not_CERT_multiboard=True,
  CERT_MULTIBOARD=159,APPROX=233,EST=0,HU2475_audit_independent=True,
  B368_not_rerun=True,PR2_remains_draft_never_merge=True)
 (D/"nl2_hu_b373_rank27_b372_true_partial_nl2_oop_original_source_proof.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 pathlib.Path("docs/NL2_HU_B373_RANK27_TRUE_NL2_PARTIAL_SOURCE_AUDIT.md").write_text(
  "# B373 verified B372 true Rust turn lock\n\n"
  "Original SHA-pinned GTO flop 9s6h3d; true NL2 OOP partially locked Rust turn/river on 9s6h3d/Ts. "
  "15 genuine NL2 pooled marginal source patterns **history-imputed** on these nodes, plus four assumed fallbacks; "
  "no observed villain private-card-conditional frequencies. Original flop was GTO, NOT fully NL2-locked. "
  "One authenticated flop only; sequential full-street per-combo reach still needs independent proof. "
  "**159 CERT / 233 APPROX / 0 EST** unchanged.\n")
 print("PASS B373 authentic Rust partial turn/river only, no false CERT 159/233")
if __name__=="__main__":main()
