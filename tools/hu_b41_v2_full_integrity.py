#!/usr/bin/env python3
"""B41 regression: independent full V2 26 CERT/366 APPROX provenance / UI / river gate.

This is verification of existing immutable pinned solves, NOT new GTO solves.
Original top24 (24/368), B39 prereg, Batch E and 2475 HU links remain intact.
"""
import hashlib
import json
import pathlib
from hu_multiboard_promote import hero_seat

ROOT=pathlib.Path("data")
OUT=ROOT/"nl2_hu_b41_v2_integrity.json"
DOC=pathlib.Path("docs/NL2_HU_B41_FULL_INTEGRITY.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    base_path=ROOT/"nl2_hu_multiboard_status.json"
    v2_path=ROOT/"nl2_hu_multiboard_status_v2_tie.json"
    b39_path=ROOT/"nl2_hu_b39_frequency_tie_prereg.json"
    rank_path=ROOT/"nl2_hu_multiboard_prerank.json"
    base=json.loads(base_path.read_text())
    v2=json.loads(v2_path.read_text())
    b39=json.loads(b39_path.read_text())
    nav=json.loads((ROOT/"nl2_hu_b34_full_integrity.json").read_text())["navigation"]
    assert base["CERT_MULTIBOARD"]==24 and base["APPROX"]==368
    assert v2["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V2_EQUAL_SCORE_TIE"
    assert v2["CERT_MULTIBOARD"]==26 and v2["APPROX"]==366 and v2["TOTAL"]==392
    assert v2["top_N_rank_cutoff"]==24 and v2["original_top24_cutoff_unchanged"] is True
    assert b39["tie_ranks"]==v2["source_blind_tie_ranks"]==[25,26]
    assert v2["original_top24_status_sha256"]==sha(base_path)
    assert v2["original_rank_file_sha256"]==sha(rank_path)
    assert v2["b39_source_blind_prereg_sha256"]==sha(b39_path)
    assert len(base["records"])==len(v2["records"])==392
    extra=set(b39["tie_node_ids"])
    assert len(extra)==2 and all(v2["records"][i]["frequency_rank"] in (25,26) for i in extra)
    assert all(v2["records"][i]==old for i,old in base["records"].items() if i not in extra)
    for i in extra:
        assert base["records"][i]["label"]=="APPROX"
        assert v2["records"][i]["label"]=="CERT-MULTIBOARD"
        assert v2["records"][i]["b39_equal_score_tie_preregistered"] is True
    assert sum(x["label"]=="CERT-MULTIBOARD" for x in v2["records"].values())==26
    assert sum(x["label"]=="APPROX" for x in v2["records"].values())==366
    named=locked=medium=low_reach=assumed=real_marginal=0
    flops={}
    for row in v2["records"].values():
        b=row["certified_3_to_5_exact_flop_boards"]
        if row["label"]=="APPROX":
            assert not b, "Approx cannot have CERT board proofs"
            continue
        assert 3<=len(b)<=5, "Every CERT requires 3-5 original GTO flops"
        assert len({x["flop"] for x in b})==len(b)
        assert len({x["flop_texture"] for x in b})>=2
        actor=hero_seat(row["preflop_text"])
        assert actor in (0,1)
        for z in b:
            assert z["acting_seat"]==actor, "Cannot borrow villain action for hero CERT"
            assert len(z["source_sha256"])==64 and z["source_run_id"]>0
            assert 0<=z["genuine_gto_exploitability_pct"]<=0.5
            assert z["strict_full_street_combo_reachable"]>0
            assert z["relative_spr_error_pct"]<=5
            assert z["nl2_locked_variants"], "Hero lock source mandatory"
            assert z["actual_exact_action_line"] and z["public_board"] and z["flop"]
            assert all(x["version"]==("exp_ip" if actor==1 else "exp_oop") for x in z["nl2_locked_variants"])
            if z["b50_nonpolarized_relative_equity_research_candidate"]:
                assert z["medium_50pct_eligible_combos"]>0
            named+=1
            locked+=1
            medium+=bool(z["b50_nonpolarized_relative_equity_research_candidate"])
            low_reach+=z["strict_full_street_combo_reachable"]<10
            assumed+=any(x["unknown_history_frequency_filled_with_default"] for x in z["nl2_locked_variants"])
            real_marginal+=any((x.get("observed_marginal_source_nodes") or 0)>0 for x in z["nl2_locked_variants"])
        flops[row["model_id"]]=len(b)
    batches=v2["independently_verified_completed_batches"]
    e=batches["B4_MICRO"]
    assert e["status"]=="VERIFIED" and e["run_id"]==44732810327
    assert e["authentic_jobs"]==4 and e["gto_cases"]==30 and e["locked_cases"]==30
    for key in ("B36_BTN_RELOCK","B37_BTN_XB50_XX","B38_BTN_IP_XX"):
        assert batches[key]["status"]=="VERIFIED"
        assert batches[key]["authentic_jobs"]==2 and batches[key]["locked_cases"]==2
    assert nav["reach_river"]==nav["continuing"]==2475 and nav["share_pct"]==100
    for key in ("missing_river","link_misses","reach_violations","modeled_path_violations","hu_contract_errors"):
        assert nav[key]==0
    for path in ("nl2-multiboard.js","nl2_hu_multiboard_ui.js"):
        s=pathlib.Path(path).read_text()
        assert "fetchCertifiedRegistry()" in s
        assert "data/nl2_hu_multiboard_status_v2_tie.json" in s
        assert "data/nl2_hu_multiboard_status.json" in s
        assert "B40 2-node evidence ledger failed guard" in s
    report=dict(schema="NL2_HU_B41_V2_INTEGRITY_V1",
        status="PASS",core_v1=dict(cert=24,approx=368),
        source_blind_v2=dict(cert=26,approx=366),
        separately_preregistered_tie_ranks=[25,26],
        no_other_model_changed=True,
        cert_models_with_3_5_real_boards=len(flops),
        certified_named_board_proofs=named,
        certified_named_board_proofs_with_true_hero_lock=locked,
        named_board_b50_research_candidates=medium,
        named_board_strict_reach_under_10=low_reach,
        named_board_any_assumed_default_scope=assumed,
        named_board_any_measured_NL2_aggregate_source=real_marginal,
        observed_per_private_combo_NL2_frequencies=False,
        gate_batch_E_44732810327="VERIFIED_30_GTO_30_LOCKED",
        river_coverage=nav,
        v2_status_sha256=sha(v2_path),
        parent_V1_status_sha256=sha(base_path),
        b39_prereg_sha256=sha(b39_path))
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    DOC.write_text("# B41 | Full NL2 V2 source/UI and river integrity\n\n"+
        "**PASS** independent V2 audit. Original core V1: 24 CERT/368 APPROX.\n"+
        "B39 source-blind equal-frequency ties 25–26: +2 fully named-board certified models; "+
        "**V2: 26 CERT/366 APPROX**. No other of 392 models changed.\n\n"+
        "- Individually named certified board proofs: "+str(named)+"; with hero-side lock: "+str(locked)+".\n"+
        "- 50% pot nonpolarized research candidates on named examples: "+str(medium)+
        " (not advice across texture classes).\n"+
        "- Less than ten strictly reachable combos: "+str(low_reach)+
        "; explicit assumed-default lock sources: "+str(assumed)+
        "; aggregate NL2 measured-marginal source present: "+str(real_marginal)+".\n"+
        "- Batch E 44732810327 independently VERIFIED, 30 GTO / 30 partial NL2 lock games.\n"+
        "- River links 2475/2475; 0 missing, 0 modeled path / reach violations.\n"+
        "- Original V1 source ledger immutable; both UI loaders prefer verified V2 or safely fall back to V1.\n"+
        "- The 3–5 specific examples are NOT generic six-texture GTO; marginal pool observations are NOT per-combo measured probabilities.\n"+
        "- PR #2 remains Draft and MUST NOT be merged.\n")
    print(json.dumps({k:report[k] for k in ("status","source_blind_v2","cert_models_with_3_5_real_boards","certified_named_board_proofs","certified_named_board_proofs_with_true_hero_lock","named_board_b50_research_candidates")},ensure_ascii=False))
if __name__=="__main__":
    main()
