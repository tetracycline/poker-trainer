#!/usr/bin/env python3
"""B371: independent SHA validation of a completed B367 original GTO artifact.
No HERO NL2 lock and no certified three-distinct-flop source in this artifact.
Never classify a single genuine source as a CERT-MULTIBOARD model.
"""
import hashlib,json,pathlib,sys
ROOT=pathlib.Path(sys.argv[1])
D=pathlib.Path("data")
OUT=D/"nl2_hu_b371_r27_b367_original_gto_only_salvage.json"
DOC=pathlib.Path("docs/NL2_HU_B371_R27_B367_GTO_ONLY_SALVAGE.md")
PIN_SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
PIN_RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
EXPECTED_ROOT="b2aeb59fe69c73c42c4c848eed27df9c055f65a7503bd9d4ee07ab07b3c89822"
EXPECTED_TURN="ecb792caaf13c22d09317c28349152c549c6b4596e6301c63f6e650bbb504aa0"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def main():
    man=ROOT/"evidence/LMP_CO_BB-9s6h3d-gto.json"
    root=ROOT/"solver/postflop/out/LMP_CO_BB/gto/9s6h3d_multiboard.json"
    turn=ROOT/"solver/postflop/out/LMP_CO_BB/gto/9s6h3d_b33c_Ts.json"
    root_job=ROOT/"solver/postflop/out/LMP_CO_BB/gto/9s6h3d_multiboard.job.json"
    turn_job=ROOT/"solver/postflop/out/LMP_CO_BB/gto/9s6h3d_b33c_Ts.job.json"
    for p in (man,root,turn,root_job,turn_job):
        assert p.is_file(),p
    assert (ROOT/"evidence/poker-solver-pin.txt").read_text().strip()==PIN_SOLVER
    assert (ROOT/"evidence/rust-pin.txt").read_text().strip()==PIN_RUST
    m=load(man)
    assert m["schema"]=="NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1"
    assert (m["spot"],m["pot_family"],m["version"],m["flop"])==("LMP_CO_BB","LMP","gto","9s6h3d")
    assert (m["root_pot_bb"],m["root_remaining_bb"])==(2.5,99.0)
    assert m["preflop_ranges"]["source"]=="ASSUMED_EXPLICIT_169CLASS"
    assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
    assert m["flop_action_sizes"]==["33%","50%","75%","100%"]
    assert m["selected_lines"]==["b33 c"] and m["turns"]==["Ts"]
    assert m["turn_subgame_sizing"]=={"oop":"50%","ip":"50%"}
    assert m["solved_cases"]==1 and len(m["cases"])==1 and not m["failures"] and not m["skipped"]
    assert m["file_flop_sha256"]==sha(root)==EXPECTED_ROOT
    c=m["cases"][0]
    assert c["line"]=="b33 c" and c["turn"]=="Ts" and c["status"]=="GTO_EXACT_ONLY"
    assert c["source_sha256"]==sha(turn)==EXPECTED_TURN and c["hero_gap_pct"] is None
    assert 0<=c["gto_gap_pct"]<=.5 and c["true_river_nodes"]==24
    j=load(turn)
    assert (j["flop"],j["turn"])==("9s6h3d","Ts")
    nodes=[n for n in j["nodes"] if n["line"]=="b33 c/b50 c/" and n["player"]==0]
    assert len(nodes)==2 and len({n["board"] for n in nodes})==2
    assert all(len(n["board"])==10 and n["pot"]==832 for n in nodes)
    s=load(D/"nl2_hu_multiboard_status_v47_b364_rank96.json")
    assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"])==(159,233,0)
    mid="ln-iso-lmp_r_model-1aov4pd"
    assert s["records"][mid]["label"]=="APPROX"
    proof=dict(schema="NL2_HU_B371_B367_COMPLETED_ORIGINAL_GTO_ONLY_ARTIFACT_SHA_V1",
       original_run_id=45013144124,original_artifact_id=14751218545,
       source_artifact_name="nl2-multiboard-B367_R27_LMPCOBB_THIRD-LMP_CO_BB-9s6h3d-gto",
       original_solver_commit=PIN_SOLVER,original_rust_commit=PIN_RUST,
       original_manifest_sha256=sha(man),original_flop_gto_sha256=sha(root),
       original_turn_river_gto_sha256=sha(turn),
       original_flop_job_sha256=sha(root_job),original_turn_job_sha256=sha(turn_job),
       model_id=mid,frequency_rank=27,spot="LMP_CO_BB",
       exact_flop="9s6h3d",exact_turn="Ts",exact_line="b33 c/b50 c/",
       actor="BB_OOP",named_exact_river_public_boards=sorted(n["board"] for n in nodes),
       original_flop_action_menu=m["flop_action_sizes"],
       gto_exploitability_pct=c["gto_gap_pct"],
       real_solved_original_turn_cases=1,
       actual_gto_original_source=True,actual_matching_NL2_OOP_hero_lock=False,
       strict_sequential_combo_reach_independently_authenticated=False,
       assumption="ASSUMED_EXPLICIT_169CLASS_PRE_FLOP_NOT_OBSERVED_PRIVATE_CARD_NL2",
       certificate_level="ORIGINAL_GTO_ONLY_NOT_CERT_MULTIBOARD",
       cert_count_unchanged=159,approx_count_unchanged=233,
       no_generic_texture_or_handclass_GTO_claim=True,
       no_source_reuse_as_third_distinct_flop=True,
       B368_not_reexecuted=True,PR2_stays_draft_never_merge=True)
    OUT.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    DOC.write_text("# B371 GTO-only exact source from B367 cancellation\n\n"
        +"Verified original 100bb, SHA-pinned GTO solve on `9s6h3d/Ts`, "
        +f"GTO gap {c['gto_gap_pct']:.6f}%, two true river runouts. "
        +"The genuine NL2 OOP hero partial-lock counterpart is absent. "
        +"This is **one flop**, not three; strict per-combo sequential reach also remains unverified. "
        +"**159 CERT / 233 APPROX / 0 EST unchanged**. Never promote from this source alone.\n",
         encoding="utf-8")
    print("PASS B371 authentic source GTO-only 9s6h3d/Ts; CERT 159 / APPROX 233; no lock, no promotion.")
if __name__=="__main__":main()
