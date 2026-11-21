#!/usr/bin/env python3
"""B40: certify only separately preregistered source-blind equal-score ties.

The immutable original 24/368 V1 ledger stays byte-for-byte untouched.
V2 is an explicit additive 2-node cohort built from authentic pinned GTO +
matching hero-side NL2 locks. Never extend a whole texture class to GTO.
"""
import copy
import hashlib
import json
import pathlib

from hu_multiboard_promote import build_source_index, candidates, choose_3_5

ROOT=pathlib.Path("data")
BASE=ROOT/"nl2_hu_multiboard_status.json"
RANK=ROOT/"nl2_hu_multiboard_prerank.json"
QUEUE=ROOT/"nl2_hu_stage2_queue.json"
B39=ROOT/"nl2_hu_b39_frequency_tie_prereg.json"
OUT=ROOT/"nl2_hu_multiboard_status_v2_tie.json"
DOC=pathlib.Path("docs/NL2_HU_B40_TIE_CERT.md")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    base=json.loads(BASE.read_text())
    rank=json.loads(RANK.read_text())
    queue=json.loads(QUEUE.read_text())
    prior=json.loads(B39.read_text())
    assert base["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V1"
    assert base["CERT_MULTIBOARD"]==24 and base["APPROX"]==368 and base["TOTAL"]==392
    assert prior["schema"]=="NL2_HU_B39_SOURCE_BLIND_EQUAL_SCORE_TIE_PREREG_V1"
    assert prior["tie_ranks"]==[25,26] and prior["no_auto_upgrade_to_cert"]
    assert prior["source_blind_selection"]=="ALL_RANKS_AFTER_24_WITH_SCORE_EQUAL_TO_FROZEN_RANK24"
    assert digest(RANK)==prior["frozen_top24_original_sha256"]
    assert rank["cutoff"]["N"]==base["top_N_rank_cutoff"]==24
    assert rank["cutoff"]["min_priority_score"]==prior["original_cutoff_score"]
    # No CFR evidence enters the selection: B39 was frozen independently.
    candidates_rank={x["rank_by_empirically_grounded_frequency_proxy"]:dict(x)
                     for x in rank["nodes"]}
    ties=[candidates_rank[i] for i in prior["tie_ranks"]]
    assert [x["model_id"] for x in ties]==prior["tie_node_ids"]
    assert all(not x["high_frequency_priority"] and
       x["estimated_NL2_hand_opportunity_fraction"]==prior["original_cutoff_score"]
       for x in ties)
    by_id={x["model_id"]:x for x in queue["records"]}
    paths=[pathlib.Path(x) for x in base["source_evidence"]["source_files"]]
    assert paths and all(x.is_file() for x in paths)
    by_exact,by_locked,summary=build_source_index(ROOT,paths)
    v2=copy.deepcopy(base)
    verified=[]
    for r in ties:
        model=by_id[r["model_id"]]
        assert base["records"][r["model_id"]]["label"]=="APPROX"
        assert r["family"]==model["family"] and r["spot"]==model["solver_profile"]
        r["preflop_text"]=model["preflop_text"]
        r["abstract_action_history"]=model["abstract_action_history"]
        sources,reason=candidates(r,by_exact,by_locked,None)
        if reason:raise ValueError("No real GTO action-line proof for tied cohort "+r["model_id"]+":"+reason)
        examples,gap=choose_3_5(sources)
        if gap or not 3<=len(examples)<=5:
            raise ValueError("Tied cohort not certifiable: "+r["model_id"]+" "+str(gap))
        assert len({x["flop"] for x in examples})==len(examples)
        assert len({x["flop_texture"] for x in examples})>=2
        for b in examples:
            assert b["nl2_locked_variants"],"Hero-side NL2 lock missing"
            assert b["strict_full_street_combo_reachable"]>0
            assert b["genuine_gto_exploitability_pct"]<=0.5
            assert b["relative_spr_error_pct"]<=5
            assert len(b["source_sha256"])==64
            assert b["public_board"] and b["actual_exact_action_line"]
        record=v2["records"][r["model_id"]]
        record.update(
            label="CERT-MULTIBOARD",
            high_frequency_preregistered=True,
            original_top24_high_frequency_preregistered=False,
            b39_equal_score_tie_preregistered=True,
            b39_original_cutoff=24,
            certified_3_to_5_exact_flop_boards=examples,
            proven_exact_board_count=len(examples),
            blocked_reason=None,
            source_credibility="GITHUB_ACTIONS_AUTHENTIC_CFR_SHA256_AND_FULL_STREET_COMBO_REACH")
        verified.append(dict(rank=r["rank_by_empirically_grounded_frequency_proxy"],
           model_id=r["model_id"],named_flops=[x["flop"] for x in examples],
           exact_source_runs=[x["source_run_id"] for x in examples],
           hero_lock_run_ids=sorted(set(v["run_id"] for x in examples
               for v in x["nl2_locked_variants"])),
           observed_NL2_per_private_combo=False))
    assert len(verified)==2
    ids=set(prior["tie_node_ids"])
    assert all(v2["records"][mid]==row for mid,row in base["records"].items() if mid not in ids)
    assert sum(x["label"]=="CERT-MULTIBOARD" for x in v2["records"].values())==26
    assert sum(x["label"]=="APPROX" for x in v2["records"].values())==366
    v2["schema"]="NL2_HU_392_MULTIBOARD_CERT_STATUS_V2_EQUAL_SCORE_TIE"
    v2["CERT_MULTIBOARD"]=26
    v2["APPROX"]=366
    v2["original_top24_cert"]=24
    v2["original_top24_approx"]=368
    v2["source_blind_tie_ranks"]=[25,26]
    v2["supplementary_cert_count"]=2
    v2["original_top24_cutoff_unchanged"]=True
    v2["original_top24_status_sha256"]=digest(BASE)
    v2["original_rank_file_sha256"]=digest(RANK)
    v2["b39_source_blind_prereg_sha256"]=digest(B39)
    v2["b40_named_board_certificates"]=verified
    v2["no_generic_texture_certification"]=True
    v2["no_claim_of_per_combo_NL2_empirical_rates"]=True
    v2["source_evidence"]=summary
    OUT.write_text(json.dumps(v2,indent=2,ensure_ascii=False)+"\n")
    lines=[
       "# B40 | Source-blind equal-score tie cohort CERT-MULTIBOARD (supplement)",
       "",
       "**Draft PR #2 only; never merge.** Original V1 remains 24 CERT / 368 APPROX.",
       "The separate V2 overlay certifies ranks25-26 only after B39 source-blind",
       "selection of both ties (identical rank24 NL2 opportunity score), with full",
       "named GTO/SPR/full-street reach/actor-specific partial NL2 lock evidence.",
       "V2 totals are **26 CERT / 366 APPROX**; the original V1 ledger is not mutated.",
       "",
       "| rank | model | certified true flops | source runs (GTO) | hero-side NL2 locked runs |",
       "|---:|---|---|---|---|"
    ]
    for z in verified:
        lines.append("| "+str(z["rank"])+" | "+z["model_id"]+" | "+", ".join(z["named_flops"])+
         " | "+str(sorted(set(z["exact_source_runs"])))+
         " | "+str(z["hero_lock_run_ids"])+" |")
    lines+=["",
      "All unlisted cards and generic textures are APPROX. At least 3 and at most 5 independent flop boards",
      "per added model were selected by the same preexisting, deterministic original choose_3_5()",
      "algorithm used for core CERT. Different textures, true actor and SPR, authentic solver SHA",
      "and nonzero sequential combo reach were checked. Partial pool observed marginals are not",
      "per-private-card observed frequencies. Missing histories retain explicit assumption flags.",
      "",
      "The static site prefers the fully derived V2 ledger only after exact schema/count/cohort checks;",
      "if unavailable, it uses the unchanged V1 24/368 ledger. This never changes the original",
      "2010-2018 or external solver inputs nor the immutable top24 ranking. Never merge.",
      ""]
    DOC.write_text("\n".join(lines))
    print(json.dumps({"schema":v2["schema"],"CERT":26,"APPROX":366,
                      "verified":verified},ensure_ascii=False))

if __name__=="__main__":
    main()
