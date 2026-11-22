#!/usr/bin/env python3
"""B380 true Rust source rank107, 0 strict actor-IP combos on target line."""
import hashlib,json,pathlib,sys
from hu_sequential_cfr_reach import game_reach
ROOT="f77c13a51de71506642bd620c685beb76ff13d0dfc8f081f16222b53d99d9a60"
TURN="7b8d93bc70a9c8c13f83bf741ebaa066bf646937a0e57b056d87b08d0da28e93"
MAN="8def1695bbaeae3ff8d1bf1bca07ea2bbef80fd2e79fd79d1132527809cef14a"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 r=pathlib.Path(sys.argv[1]); mpath=r/"evidence/BTN_BB-KsQh4d-gto.json"
 fpath=r/"solver/postflop/out/BTN_BB/gto/KsQh4d_multiboard.json"
 spath=r/"solver/postflop/out/BTN_BB/gto/KsQh4d_b33c_Tc.json"
 assert all(p.is_file() for p in (mpath,fpath,spath))
 assert (sha(mpath),sha(fpath),sha(spath))==(MAN,ROOT,TURN)
 assert (r/"evidence/poker-solver-pin.txt").read_text().strip()=="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
 assert (r/"evidence/rust-pin.txt").read_text().strip()=="9d1509fe5077d019825f833eed04b16d342dfda1"
 m,fr,sub=read(mpath),read(fpath),read(spath)
 assert (m["spot"],m["flop"],m["version"],m["pot_family"])==("BTN_BB","KsQh4d","gto","SRP")
 assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
 assert (m["root_pot_bb"],m["root_remaining_bb"])==(5.5,97.5)
 assert m["flop_size_profile"]=="full" and m["flop_action_sizes"]==["33%","50%","75%","100%"]
 assert (m["selected_lines"],m["turns"])==(["b33 c"],["Tc"])
 assert m["solved_cases"]==len(m["cases"])==1 and not m["failures"] and not m["skipped"]
 c=m["cases"][0]
 assert (c["line"],c["turn"],c["source_sha256"])==("b33 c","Tc",TURN)
 assert 0<=c["gto_gap_pct"]<=.5 and c["status"]=="GTO_EXACT_ONLY"
 assert (fr["flop"],fr["pot"],fr["stack"])==("KsQh4d",550,9750)
 assert (sub["flop"],sub["turn"],sub["line0"])==("KsQh4d","Tc","b33 c")
 masks,stats=game_reach(fr,sub)
 rows=[]
 for node in sub["nodes"]:
  if node["line"]=="b33 c/x b50 c/x" and node["player"]==1 and len(node["board"])==10:
   x=masks["|".join((node["board"],node["line"],"1"))]
   rows.append(dict(board=node["board"],actor="BTN_IP",strict_40_70_combos=x["count"],
    raw_reachable_combos=sum(float(w)>1e-4 for w in node["w"][1])))
 assert sorted(x["board"] for x in rows)==["4dQhKsTc3h","4dQhKsTc4c"]
 assert all(x["strict_40_70_combos"]==0 for x in rows)
 assert stats["sequential_actor_combo_nodes"]==20
 s=read(pathlib.Path("data/nl2_hu_multiboard_status_v47_b364_rank96.json"))
 assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"])==(159,233,0)
 assert s["records"]["ln-ipfr-r_model-ujl14x"]["label"]=="APPROX"
 out=dict(schema="NL2_B380_RANK107_KSQH4D_ORIGINAL_RUST_GTO_ZERO_STRICT_TARGET_IP",
  original_run_id=45017142943,original_artifact_id=14753000740,model_id="ln-ipfr-r_model-ujl14x",
  rank=107,flop="KsQh4d",turn="Tc",line="b33 c/x b50 c/x",
  verified_original_Rust_source_SHAs=dict(manifest=MAN,flop=ROOT,turn=TURN),
  gto_gap_pct=c["gto_gap_pct"],strict_reach_stats=dict(stats),excluded_named_river_boards=rows,
  no_CERT_because_zero_legal_actor_IP_combos=True,
  B368_not_rerun=True,CERT_MULTIBOARD=159,APPROX=233,EST=0,PR2_draft_never_merge=True)
 pathlib.Path("data/nl2_hu_b380_rank107_ksqh4d_strict_zero_gto_source_negative.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 pathlib.Path("docs/NL2_HU_B380_RANK107_KSQH4D_STRICT_ZERO_NEGATIVE.md").write_text(
  "# B380 source-verified negative: rank107\n\n"
  "Original full 100bb GTO Rust flop KsQh4d/Tc SHA-verified, gap <=0.5%. "
  "Both BTN-IP target river roots on b33 c/x b50 c/x have ZERO full-street max/40%-70% actor combos. "
  "Authentic solve does not qualify as a certifying third flop. 159 CERT / 233 APPROX unchanged.\n")
 print("PASS B380 original GTO, zero strict target combos; CERT159 APPROX233")
if __name__=="__main__":main()
