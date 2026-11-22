#!/usr/bin/env python3
"""B364 V47: exact rank96 OOP CERT only from THREE NEW distinct real Rust
100bb FULL FOUR-SIZE GTO and NL2 OOP actor-linked sources B359+B361+B363.
Historical Stage2 Ks7h2d strict actor zero is EXCLUDED (B362 negative).
This is a named-board source certification, NOT generic GTO/pool private card frequencies.
"""
import copy,hashlib,importlib,json,pathlib
import hu_b362_v47_rank96_three_real_oop_cert as checked
import hu_cert_lock_medium_audit
import hu_cert_lock_medium_coverage_matrix
D=pathlib.Path("data")
DOC=pathlib.Path("docs/NL2_HU_B364_V47_RANK96_THREE_NEW_ORIGINAL_GTO_NL2_OOP_CERT.md")
PARENT=D/"nl2_hu_multiboard_status_v46_b354_rank79.json"
STATUS=D/"nl2_hu_multiboard_status_v47_b364_rank96.json"
MATRIX=D/"nl2_hu_cert_lock_medium_matrix_v47_b364.json"
PROOF=D/"nl2_hu_b364_v47_rank96_three_new_full_100bb_GTO_NL2_OOP_source_gate.json"
NEGATIVE=D/"nl2_hu_b362_rank96_historic_stage2_strict_40_70_negative.json"
MID="ln-opfr-r_model-18g2rvt"
RUNS={359:44976462678,361:44977743690,363:44978936529}
THREE=((359,"As9h2d"),(361,"Qs8h2d"),(363,"Qs7h3d"))
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=read(PARENT)
    assert old["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79"
    assert (old["CERT_MULTIBOARD"],old["APPROX"],old["EST"],old["TOTAL"])==(158,234,0,392)
    target=old["records"][MID]
    assert (target["label"],target["frequency_rank"],target["solver_profile"],
        target["assumed_model_node_spr"])==("APPROX",96,"UTG_CO",4.15)
    neg=read(NEGATIVE)
    assert neg["schema"]=="NL2_HU_B362_HISTORIC_R96_LEGACY_SOURCE_40_70_TRUE_NEGATIVE_V1"
    assert neg["historic_Ks7h2d_CANNOT_COUNT_AS_CERT_FLOP"] is True
    assert neg["historical_NL2_OOP_has_zero_strict_positive"] is True
    assert neg["rerun_actual_NL2_OOP"]["strict_positive_actor_combo_rows"]==0
    assert [r["flop"] for r in neg["authenticated_new_exact_paired_distinct_flops"]]==["As9h2d","Qs8h2d"]
    assert neg["frozen_baseline_source_sha256"]==sha(PARENT)
    assert checked.MID==MID and checked.SPOT=="UTG_CO" and checked.LINE=="b33 c/b50 c/"
    assert checked.SPR==4.15 and checked.PARENT==PARENT
    checked.RUNS.update(RUNS)
    boards=[];pins=[]
    for batch,flop in THREE:
        board,pin=checked.build_fresh(batch,flop)
        assert board["source_run_id"]==RUNS[batch]
        assert board["flop"]==flop and board["acting_seat"]==0
        assert board["actual_exact_action_line"]=="b33 c/b50 c/"
        assert board["source_kind"]=="PINNED_PREFLOP_CFR_AUTHENTIC_FULL_FOUR_SIZE_100BB_RUST"
        assert board["strict_full_street_combo_reachable"]>0
        assert not board["assumed_preflop_ranges"]
        assert len(board["nl2_locked_variants"])==1
        assert board["nl2_locked_variants"][0]["version"]=="exp_oop"
        assert len(board["nl2_locked_variants"][0]["sha256"])==64
        assert board["relative_spr_error_pct"]<=5
        assert board["genuine_gto_exploitability_pct"]<=.5
        assert board["actual_spr"]>0
        boards.append(board);pins.append(pin)
    assert [x["flop"] for x in boards]==["As9h2d","Qs8h2d","Qs7h3d"]
    assert "Ks7h2d" not in {x["flop"] for x in boards}
    assert len({x["flop"] for x in boards})==3
    textures={x["flop_texture"] for x in boards}
    assert len(textures)>=2,("Only a single texture",textures)
    new=copy.deepcopy(old)
    new["records"][MID].update(
        label="CERT-MULTIBOARD",high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=96,
        prereg_cohort="B359_AS9H2D_B361_QS8H2D_B363_QS7H3D_THREE_NEW_FULL_100BB_ORIGINAL_GTO_NL2_ACTOR_40_70_RUST_SHA",
        certified_3_to_5_exact_flop_boards=boards,
        proven_exact_board_count=3,
        blocked_reason=None,
        source_credibility="THREE_DIFFERENT_NEW_FULL_100BB_RUST_GTO_AND_REAL_NL2_OOP_ACTOR_SOURCE_SHA_EXACT_BOARD_NOT_GENERIC")
    assert {k for k in old["records"] if old["records"][k]!=new["records"][k]}=={MID}
    new.update(schema="NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96",
        CERT_MULTIBOARD=159,APPROX=233,EST=0,TOTAL=392,
        parent_v46_sha256=sha(PARENT),
        source_blind_expansion_ranks=sorted(set(old["source_blind_expansion_ranks"])|{96}),
        supplementary_cert_count=old["supplementary_cert_count"]+1,
        B364_rank96_three_true_original_GTO_NL2_OOP_flops=dict(
            rank=96,model_id=MID,spot="UTG_CO",actor="UTG_OOP",exact_line="b33 c/b50 c/",
            model_SPR=4.15,flops=[x["flop"] for x in boards],textures=sorted(textures),
            genuine_sources=pins,
            original_flop_size_menu_all_33_50_75_100=True,
            excluded_failed_historic_stage2_Ks7h2d_sha256=sha(NEGATIVE),
            no_observed_private_combo_NL2_frequencies=True,
            exact_named_boards_only_no_texture_generalization=True))
    assert sum(x["label"]=="CERT-MULTIBOARD" for x in new["records"].values())==159
    assert sum(x["label"]=="APPROX" for x in new["records"].values())==233
    auditor=pathlib.Path("tools/hu_cert_lock_medium_audit.py")
    source=auditor.read_text()
    needle="'NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79')"
    replacement="'NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79',\n                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96')"
    assert source.count(needle)==1 and "V47_B364_RANK96" not in source
    auditor.write_text(source.replace(needle,replacement))
    importlib.reload(hu_cert_lock_medium_audit)
    hu_cert_lock_medium_coverage_matrix.audit=hu_cert_lock_medium_audit.audit
    audit=hu_cert_lock_medium_audit.audit(new)
    assert (audit["cert_multiboard"],audit["approx"],audit["EST"])==(159,233,0)
    assert audit["aggregate"]["named_board_proofs"]==606
    assert audit["aggregate"]["paired_hero_locked_source_variants"]==698
    assert audit["not_generalized_handclass_GTO"] and audit["not_actual_NL2_earnings"]
    matrix=hu_cert_lock_medium_coverage_matrix.create(new)
    assert (len(matrix["boards"]),len(matrix["models"]))==(606,159)
    assert (matrix["strict_aggregate"]["named_board_proofs"],
        matrix["strict_aggregate"]["hero_lock_variants"])==(606,698)
    STATUS.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n")
    matrix.update(
        schema="NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V47_B364",
        parent_v47_status_sha256=sha(STATUS),
        partial_NL2_locks_are_not_whole_flop_GTO=True,
        NL2_private_combo_conditional_rates_not_observed=True,
        only_exact_board_b50_nonpolarized_research=True,
        unknown_source_denominators_are_not_zero_or_empirical=True,
        excluded_historic_negative_source_sha256=sha(NEGATIVE),
        PR2_Draft_NEVER_MERGE=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+"\n")
    PROOF.write_text(json.dumps(dict(
        schema="NL2_HU_B364_V47_RANK96_THREE_NEW_TRUE_UTGCO_GTO_NL2_OOP_SHA_CERT_V1",
        parent_V46_status_sha256=sha(PARENT),V47_status_sha256=sha(STATUS),
        V47_matrix_sha256=sha(MATRIX),independent_auditor_sha256=sha(auditor),
        historical_B362_negative_sha256=sha(NEGATIVE),
        three_new_distinct_flops=[x["flop"] for x in boards],
        two_plus_textures=sorted(textures),three_SHA_authentic_source_pairs=pins,
        all_flop_trees_full_33_50_75_100_original_100bb=True,
        no_unobserved_private_hand_NL2_frequency_claims=True,
        all_40_70_actor_ancestry_and_SPR_gate=True,
        CERT=159,APPROX=233,EST=0,TOTAL=392,
        named_boards=606,genuine_actor_NL2_partial_lock_variants=698,
        HU2475_full_audit_REQUIRED_before_commit=True,
        PR2_Draft_NEVER_MERGE=True
      ),ensure_ascii=False,indent=2)+"\n")
    DOC.write_text(
      "# B364 V47 rank96 authentic three distinct full-size 100bb source promotion\n\n"
      "Only ORIGINAL Rust GTO and actual NL2 OOP response on EXACT same public board, actor0 and b33 c/b50 c/ ancestry with max or 40%/70% per-hand previous action and SPR4.15 ±5%.\n\n"
      "Valid independent flops: "
      +", ".join(x["flop"]+"/"+x["turn"]+" exact "+x["public_board"] for x in boards)
      +". Two or more textures, all three full original 33/50/75/100 flop menus. SHA-pinned B359/B361/B363 and source-to-actor verified.\n\n"
      "Historical Stage2 Ks7h2d source explicitly EXCLUDED: B362 independent re-audit proved NL2 OOP strict sequential combinations ZERO. "
      "Do not infer observed opponent private-combo NL2 frequencies from pooled street/size marginals. Unknown old denominators retained as UNKNOWN. "
      "Only the named original public boards are supported; no universal handclass GTO or bankroll win-rate assertion. "
      "V47 159 CERT/233 APPROX/0 EST, 606 genuine named source boards / 698 partial NL2 actor locks. "
      "Existing frontend stays V46 until separately upgraded with fallback, all 2475 HU paths must pass Actions, draft PR #2 NEVER merge.\n")
    print("PASS B364 V47 rank96 strictly 3 NEW original GTO+NL2 actor flops",
      [(x["flop"],x["strict_full_street_combo_reachable"]) for x in boards],
      "159 CERT 233 APPROX 606 genuine boards 698 NL2 partial locks")
if __name__=="__main__":
    main()
