#!/usr/bin/env python3
"""Independent strict old Stage2 GTO/NL2 OOP source audit: negative result must be kept.
Only sequential source-actor max/40/70 paths count, not old file-existence or
unfiltered current-node action candidates. Does NOT promote any model.
"""
import argparse,hashlib,json,pathlib
from hu_sequential_cfr_reach import game_reach
D=pathlib.Path("data");RUN=44654973894;LINE="b33 c/b50 c/"
OUT=D/"nl2_hu_b362_rank96_historic_stage2_strict_40_70_negative.json"
DOC=pathlib.Path("docs/NL2_HU_B362_RANK96_HISTORIC_STAGE2_OOP_STRICT_NEGATIVE.md")
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evaluate(folder,version):
    mf=folder/f"evidence/UTG_CO-{version}-Ks7h2d.json"
    assert mf.is_file()
    m=read(mf)
    assert (m["spot"],m["version"])==("UTG_CO",version)
    cases=[x for x in m["cases"] if
      (x["flop"],x["turn"],x["line"])==("Ks7h2d","9d","b33 c")]
    assert len(cases)==1
    c=cases[0]
    fp=folder/"solver/postflop"/c["flop_json"]
    sp=folder/"solver/postflop"/c["sub_json"]
    assert fp.is_file() and sp.is_file()
    assert sha(fp)==c["flop_sha256"] and sha(sp)==c["sub_sha256"]
    fr=read(fp);d=read(sp)
    assert (fr["flop"],fr["pot"],fr["stack"])==("Ks7h2d",650,9750)
    assert (d["flop"],d["turn"],d["line0"])==("Ks7h2d","9d","b33 c")
    assert d["info"]["gto_expl_pct"]<=.5
    if version=="exp_oop":assert d["info"]["hero_gap_pct"]<=.5
    overlay,stats=game_reach(fr,d)
    rows=[]
    for n in d["nodes"]:
        if (n["player"],n["line"],len(n["board"]))!=(0,LINE,10):continue
        key="|".join((n["board"],n["line"],"0"))
        q=overlay.get(key)
        assert q is not None
        spr=(d["stack"]-max(n["bets"]))/n["pot"]
        if abs(spr-4.15)/4.15>.05:continue
        rows.append(dict(public_board=n["board"],
            source_reachable_actor_hands=sum(float(v)>1e-4 for v in n["w"][0]),
            sequential_strict_40_70_actor_combos=q["count"],
            node_spr=round(spr,6),
            actor=0,line=LINE))
    assert len(rows)>=2
    return dict(version=version,manifest_sha256=sha(mf),
        full_root_sha256=sha(fp),original_turn_river_source_sha256=sha(sp),
        flop_size_menu="LEGACY_33_50_75_NOT_FOUR_SIZE",
        authentic_rust_converged=True,
        exact_target_river_nodes=rows,
        strict_positive_river_board_count=sum(z["sequential_strict_40_70_actor_combos"]>0 for z in rows),
        strict_positive_actor_combo_rows=sum(z["sequential_strict_40_70_actor_combos"] for z in rows))
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--historic-gto",required=True,type=pathlib.Path)
    a.add_argument("--historic-exp-oop",required=True,type=pathlib.Path)
    args=a.parse_args()
    hfile=D/"nl2_hu_b175_v32_248_exact_GTO_source_provenance.json"
    h=read(hfile);row=next(x for x in h["rows"] if x["rank"]==96)
    assert row["model_id"]=="ln-opfr-r_model-18g2rvt"
    prior=[p for p in row["exact_authentic_gto_source_proofs"] if
      (p["flop"],p["turn"],p["source_run"],p["exact_line"],p["actor"])==
      ("Ks7h2d","9d",RUN,LINE,0)]
    assert len(prior)>=2 and all(x["true_NL2_actor_locked"] for x in prior)
    g=evaluate(args.historic_gto,"gto")
    e=evaluate(args.historic_exp_oop,"exp_oop")
    assert all(x["source_sha"]==g["original_turn_river_source_sha256"] for x in prior)
    assert g["strict_positive_river_board_count"]>=2
    assert e["strict_positive_river_board_count"]==0
    assert e["strict_positive_actor_combo_rows"]==0
    assert any(z["source_reachable_actor_hands"]>0 for z in e["exact_target_river_nodes"])
    status=D/"nl2_hu_multiboard_status_v46_b354_rank79.json"
    base=read(status)
    assert (base["CERT_MULTIBOARD"],base["APPROX"],base["EST"],base["TOTAL"])==(158,234,0,392)
    assert base["records"][row["model_id"]]["label"]=="APPROX"
    paired=[]
    for batch,flop in ((359,"As9h2d"),(361,"Qs8h2d")):
        p=D/f"nl2_hu_b{batch}_rank96_two_new_true_source_proofs.json"
        d=read(p)
        r=next(y for y in d["candidate_pairs"] if y["flop"]==flop)
        assert r["strict_authenticated_pair"] and r["new_exact_matched_GTO_NL2_OOP_river_boards"]
        paired.append(dict(flop=flop,run_id=d["source_run_id"],source_sha256=sha(p),
            exact_matched_boards=r["new_exact_matched_GTO_NL2_OOP_river_boards"]))
    evidence=dict(schema="NL2_HU_B362_HISTORIC_R96_LEGACY_SOURCE_40_70_TRUE_NEGATIVE_V1",
      historical_run_id=RUN,original_B175_proof_sha256=sha(hfile),
      historical_B175_claimed_true_actor_lock=True,
      historical_B175_40_70_positive_GTO_rows=[x["strict_legal_combos"] for x in prior],
      rerun_actual_GTO=g,rerun_actual_NL2_OOP=e,
      historical_GTO_has_strict_positive=True,
      historical_NL2_OOP_has_zero_strict_positive=True,
      legacy_original_B175_positive_LOCK_CLASSIFICATION_INSUFFICIENT=True,
      historic_Ks7h2d_CANNOT_COUNT_AS_CERT_FLOP=True,
      authenticated_new_exact_paired_distinct_flops=paired,
      frozen_baseline_source_sha256=sha(status),
      CERT=158,APPROX=234,EST=0,TOTAL=392,
      no_future_CERT_promotion_without_three_NEW_OR_OTHER_INDEPENDENT_STRICT_PAIRS=True,
      private_combo_conditioned_NL2_pool_rates_not_observed=True,
      PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    DOC.write_text("# B362: old Ks7h2d source **fails** the exact-actor sequential 40/70 gate\n\n"
      "Archived pinned Rust GTO and authentic partial NL2 OOP solver both converge and pass original SHA verification, "
      "but their common rank96 UTG_OOP b33 c/b50 c/ river line does not retain any NL2 OOP combos after the full flop-to-turn-to-river max/40/70 actor policy. "
      "The older B175 true-NL2-actor-locked flag counted an existing source, not genuine actor-specific full-street reachable NL2 combos. "
      "Therefore **Ks7h2d must NOT count** toward the three-distinct-flop CERT criterion.\n\n"
      "B359 As9h2d and B361 Qs8h2d are independent genuine newer paired flops, so rank96 still needs one third. "
      "V46 stays 158 CERT /234 APPROX/0 EST. No fabricated private-hand NL2 conditionals or unknown denominators; full HU2475 audit required. PR #2 remains draft and must never merge.\n")
    print("PASS B362 NEGATIVE: historic rank96 GTO has",g["strict_positive_actor_combo_rows"],
      "strict actors but NL2 OOP has ZERO; V46 158/234 preserved")
if __name__=="__main__":
    main()
