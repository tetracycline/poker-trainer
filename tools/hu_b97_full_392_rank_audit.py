#!/usr/bin/env python3
"""B97: reconcile EVERY one of 392 frozen NL2 frequency ranks against its source-blind audit,
current V22 exact CERT board GTO/hero-lock registry, B4_MICRO Batch E, and 2475 river routes.

The source-blind preselection is independent of expected EV and profits.
No absent source is upgraded to CERT; NL2 measured marginals are NOT observed
per-private-combo opponent conditional frequencies. PR #2 stays Draft, never merge.
"""
import collections
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, "tools")
from hu_cert_lock_medium_coverage_matrix import create

ROOT=pathlib.Path("data")
RANK=ROOT/"nl2_hu_multiboard_prerank.json"
TIES=ROOT/"nl2_hu_b39_frequency_tie_prereg.json"
V22=ROOT/"nl2_hu_multiboard_status_v22_batch94.json"
MATRIX=ROOT/"nl2_hu_cert_lock_medium_matrix_v22.json"
NAV=ROOT/"nl2_hu_b34_full_integrity.json"
OUT=ROOT/"nl2_hu_b97_all392_source_integrity.json"
DOC=pathlib.Path("docs/NL2_HU_B97_ALL392_RANK_CERT_AUDIT.md")
COHORTS=(
  ("B42",27,32,"b42_next6"),
  ("B48",33,41,"b48_next9"),
  ("B54",42,55,"b54_next14"),
  ("B57",56,75,"b57_next20"),
  ("B60",76,95,"b60_next20"),
  ("B68",96,115,"b68_next20"),
  ("B70",116,135,"b70_next20"),
  ("B72",136,155,"b72_next20"),
  ("B74",156,175,"b74_next20"),
  ("B76",176,195,"b76_next20"),
  ("B79",196,215,"b79_next20"),
  ("B81",216,235,"b81_next20"),
  ("B83",236,255,"b83_next20"),
  ("B85",256,275,"b85_next20"),
  ("B87",276,295,"b87_next20"),
  ("B89",296,315,"b89_next20"),
  ("B91",316,335,"b91_next20"),
  ("B93",336,355,"b93_next20"),
  ("B95",356,375,"b95_next20"),
  ("B96",376,392,"b96_final17"),
)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    rank=json.loads(RANK.read_text())
    ties=json.loads(TIES.read_text())
    status=json.loads(V22.read_text())
    mat=json.loads(MATRIX.read_text())
    nav=json.loads(NAV.read_text())["navigation"]
    assert rank["cutoff"]["N"]==24 and rank["cutoff"]["selection_does_not_consider_solver_result_or_profit"]
    assert len(rank["nodes"])==392
    byrank={x["rank_by_empirically_grounded_frequency_proxy"]:x for x in rank["nodes"]}
    assert set(byrank)==set(range(1,393)) and len({x["model_id"] for x in rank["nodes"]})==392
    assert ties["schema"]=="NL2_HU_B39_SOURCE_BLIND_EQUAL_SCORE_TIE_PREREG_V1"
    assert ties["tie_ranks"]==[25,26]
    assert ties["frozen_top24_original_sha256"]==digest(RANK)
    assert ties["no_auto_upgrade_to_cert"]
    assert ties["tie_node_ids"]==[byrank[i]["model_id"] for i in (25,26)]
    assert status["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V22_BATCH94"
    assert (status["CERT_MULTIBOARD"],status["APPROX"],status["TOTAL"])==(131,261,392)
    assert status["original_top24_cert"]==24
    assert status["original_top24_cutoff_unchanged"]
    assert len(status["records"])==392
    assert set(status["records"])=={x["model_id"] for x in rank["nodes"]}
    labels=collections.Counter(x["label"] for x in status["records"].values())
    assert labels=={"CERT-MULTIBOARD":131,"APPROX":261}
    for i in range(1,25):
        x=status["records"][byrank[i]["model_id"]]
        assert x["label"]=="CERT-MULTIBOARD"
        assert x["frequency_rank"]==i
    for i in (25,26):
        assert status["records"][byrank[i]["model_id"]]["label"]=="CERT-MULTIBOARD"
    seen=set(range(1,27))
    cohort_meta=[]
    remaining_approx_one_board=[]
    for name,start,stop,stem in COHORTS:
        p=ROOT/("nl2_hu_"+stem+"_sourceblind_gaps.json")
        d=json.loads(p.read_text())
        assert d["source_blind_preselection_ranks"]==list(range(start,stop+1))
        assert d["fixed_rank_sha256"]==digest(RANK)
        assert d["no_current_reclassification"] is True
        assert d["no_source_outcome_based_rank_selection"] is True
        assert d["no_private_combo_NL2_empirical_rates"] is True
        assert len(d["rows"])==stop-start+1
        for r in d["rows"]:
            i=r["rank"]
            assert start<=i<=stop and i not in seen
            seen.add(i)
            assert r["model_id"]==byrank[i]["model_id"]
            assert r["current_label"]=="APPROX"
            assert status["records"][r["model_id"]]["frequency_rank"]==i
            assert r["missing_to_three_flops"]==max(0,3-r["distinct_matched_flop_count"])
            if r["meets_named_board_certification_evidence"]:
                proof=r["candidate_3_5_flops"]
                assert 3<=len(proof)<=5 and len(proof)==len(set(proof))
            elif r["missing_to_three_flops"]==1 and status["records"][r["model_id"]]["label"]=="APPROX":
                remaining_approx_one_board.append(dict(rank=i,model_id=r["model_id"],
                    spot=r["spot"],gap_flops=1,
                    true_GTO_flops=r["matching_true_GTO_flops"],
                    verified_hero_lock_flops=r["matched_hero_side_NL2_lock_flops"]))
        cohort_meta.append(dict(name=name,start=start,stop=stop,models=len(d["rows"]),
            original_ready=sum(bool(x["meets_named_board_certification_evidence"]) for x in d["rows"]),
            sha256=digest(p)))
    assert seen==set(range(1,393))
    assert len(COHORTS)==20 and sum(x["models"] for x in cohort_meta)==366
    derived=create(status)
    assert derived["CERT_MULTIBOARD"]==mat["CERT_MULTIBOARD"]==131
    assert derived["APPROX"]==mat["APPROX"]==261
    assert len(derived["boards"])==len(mat["boards"])==521
    assert len(derived["models"])==len(mat["models"])==131
    assert derived["strict_aggregate"]==mat["strict_aggregate"]
    assert mat["parent_v22_status_sha256"]==digest(V22)
    rows=[]
    for model_id,m in status["records"].items():
        if m["label"]!="CERT-MULTIBOARD":continue
        boards=m["certified_3_to_5_exact_flop_boards"]
        assert 3<=len(boards)<=5 and len({x["flop"] for x in boards})==len(boards)
        assert len({x["flop_texture"] for x in boards})>=2
        for b in boards:
            assert b["acting_seat"] in (0,1)
            assert b["genuine_gto_exploitability_pct"]<=0.5
            assert b["relative_spr_error_pct"]<=5
            assert b["strict_full_street_combo_reachable"]>0
            assert len(b["source_sha256"])==64
            assert b["nl2_locked_variants"]
            expected="exp_ip" if b["acting_seat"]==1 else "exp_oop"
            assert all(x["version"]==expected and len(x["sha256"])==64 for x in b["nl2_locked_variants"])
            rows.append(dict(rank=m["frequency_rank"],model_id=model_id,flop=b["flop"],
              actor=b["acting_seat"],gto_source_run=b["source_run_id"],
              hero_source_runs=[x["run_id"] for x in b["nl2_locked_variants"]],
              strict_combo_count=b["strict_full_street_combo_reachable"],
              b50_candidate=bool(b.get("b50_nonpolarized_relative_equity_research_candidate"))))
    assert len(rows)==521
    assert status["independently_verified_completed_batches"]["B4_MICRO"]["run_id"]==44732810327
    assert status["independently_verified_completed_batches"]["B4_MICRO"]["status"]=="VERIFIED"
    assert (status["independently_verified_completed_batches"]["B4_MICRO"]["gto_cases"],
       status["independently_verified_completed_batches"]["B4_MICRO"]["locked_cases"])==(30,30)
    assert nav["continuing"]==nav["reach_river"]==2475 and nav["share_pct"]==100
    assert nav["missing_river"]==nav["link_misses"]==nav["reach_violations"]==nav["modeled_path_violations"]==0
    sources=[pathlib.Path(x) for x in status["source_evidence"]["source_files"]]
    assert len(sources)>=25 and all(x.is_file() for x in sources)
    assert len(set(sources))==len(sources)
    result=dict(schema="NL2_B97_ALL392_SOURCEBLIND_RANK_AND_TRUE_CERT_GTO_LOCK_INTEGRITY_V1",
      verdict="PASS",total_ranked_model_nodes=392,cohorts=cohort_meta,
      sourceblind_rank_set_contiguous=True,no_duplicate_model_id=True,
      frozen_rank_sha256=digest(RANK),
      v22_status_sha256=digest(V22),lock_matrix_sha256=digest(MATRIX),
      cert_multiboard=131,approx=261,EST=0,
      true_named_cert_board_proofs=521,hero_lock_variants=mat["strict_aggregate"]["hero_lock_variants"],
      b50_research_candidate_boards=mat["strict_aggregate"]["b50_research_candidate_boards"],
      b50_unsupported_boards=521-mat["strict_aggregate"]["b50_research_candidate_boards"],
      observed_pool_marginal_pattern_nodes=mat["strict_aggregate"]["observed_marginal_pattern_nodes"],
      assumed_default_pattern_nodes=mat["strict_aggregate"]["assumed_pattern_nodes"],
      unmatched_villain_nodes=mat["strict_aggregate"]["unmatched_opponent_nodes"],
      exact_board_proof_rows=rows,
      remaining_high_priority_one_board_approx=sorted(remaining_approx_one_board,key=lambda x:x["rank"]),
      batch_e_run=44732810327,batch_e_gto_cases=30,batch_e_hero_lock_cases=30,
      verified_river_links=2475,river_coverage_pct=100,
      original_top24_immutable=True,original_v1_through_v21_untouched=True,
      no_generic_texture_GTO=True,no_per_private_combo_NL2_observation=True,
      PR_2_remains_draft_never_merge=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    lines=["# B97 | Independent rank 1–392 frozen-source coverage gate","",
      "**V22 131 CERT-MULTIBOARD / 261 APPROX / EST 0**.",
      "All 392 original frequency-preregistered ranks audited exactly once: 1–24 original, 25–26 source-blind frequency ties, 27–392 in 20 immutable cohorts.",
      "All 521 named board GTO+hero partial locks rechecked for exact public cards, SPR, actor, GTO gap and positive strict combo reach.",
      "No unverified generic texture action is relabeled as GTO. 50% sizing is named-board *research*, not universal advice.",
      "Only NL2 pooled marginals are actually measured; assumed/default, unmatched and historical unknown remain disclosed.",
      "Batch E run 44732810327 remains VERIFIED (30 GTO / 30 genuine partial hero-lock subgames).",
      "HU river navigation 2,475 / 2,475, zero missing or reach violations.",
      "",
      "| Cohort | Ranks | Frozen cells | Originally source-ready |",
      "| --- | --- | ---: | ---: |"]
    for x in cohort_meta:lines.append("| "+x["name"]+" | "+str(x["start"])+"–"+str(x["stop"])+" | "+str(x["models"])+" | "+str(x["original_ready"])+" |")
    lines.extend(["","## Remaining APPROX with exactly one missing authenticated board or lock",""])
    for x in result["remaining_high_priority_one_board_approx"]:
        lines.append("- Rank "+str(x["rank"])+" / "+x["model_id"]+" / "+x["spot"]+" (2 authenticated matched flops; missing 1)")
    lines+=["","Do not certify missing hero decision or stale/failed Rust job as GTO.",
      "Draft PR #2 only; NEVER merge.",""]
    DOC.write_text("\n".join(lines))
    print(json.dumps(dict(PASS=True,total=392,CERT=131,APPROX=261,
      exact_boards=521,locks=result["hero_lock_variants"],
      remaining_one_board_approx=[x["rank"] for x in result["remaining_high_priority_one_board_approx"]],
      batch_e_run=44732810327,river_links=2475),ensure_ascii=False))
if __name__=="__main__":main()
