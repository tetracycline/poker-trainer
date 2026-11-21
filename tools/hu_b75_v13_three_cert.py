#!/usr/bin/env python3
"""B75 isolated V13: three B74 source-blind high-frequency true multi-board certifications."""
import copy,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md
R=pathlib.Path("data")
OLD=R/"nl2_hu_multiboard_status_v12_batch73.json"
B74=R/"nl2_hu_b74_next20_sourceblind_gaps.json"
OUT=R/"nl2_hu_multiboard_status_v13_batch75.json"
MAT=R/"nl2_hu_cert_lock_medium_matrix_v13.json"
DOC=pathlib.Path("docs/NL2_HU_B75_V13_THREE_CERT.md")
MATDOC=pathlib.Path("docs/NL2_HU_B75_V13_ALL_LOCKS_MEDIUM.md")
FROZEN=(156,170,172)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    before=json.loads(OLD.read_text())
    prereg=json.loads(B74.read_text())
    rank=json.loads((R/"nl2_hu_multiboard_prerank.json").read_text())
    queue=json.loads((R/"nl2_hu_stage2_queue.json").read_text())
    assert before["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V12_BATCH73"
    assert (before["CERT_MULTIBOARD"],before["APPROX"],before["TOTAL"])==(86,306,392)
    assert prereg["schema"]=="NL2_HU_B74_SOURCE_BLIND_NEXT20_GAP_AUDIT_V1"
    assert prereg["source_blind_preselection_ranks"]==list(range(156,176))
    assert prereg["fixed_rank_sha256"]==sha(R/"nl2_hu_multiboard_prerank.json")
    assert prereg["frozen_v12_sha256"]==sha(OLD)
    assert tuple(x["rank"] for x in prereg["rows"] if x["meets_named_board_certification_evidence"])==FROZEN
    ranks={x["rank_by_empirically_grounded_frequency_proxy"]:dict(x) for x in rank["nodes"]}
    queue_by_id={x["model_id"]:x for x in queue["records"]}
    paths=[pathlib.Path(x) for x in before["source_evidence"]["source_files"]]
    assert len(paths)>=25 and all(x.is_file() for x in paths)
    exact,locked,sources=build_source_index(R,paths)
    data=copy.deepcopy(before)
    published=[]
    for i in FROZEN:
        r=ranks[i]; m=queue_by_id[r["model_id"]]
        pre=next(x for x in prereg["rows"] if x["rank"]==i)
        assert not r["high_frequency_priority"] and pre["model_id"]==r["model_id"]
        assert before["records"][r["model_id"]]["label"]=="APPROX"
        assert m["solver_profile"]==r["spot"] and m["family"]==r["family"]
        r["preflop_text"]=m["preflop_text"]
        r["abstract_action_history"]=m["abstract_action_history"]
        matched,why=candidates(r,exact,locked,None)
        if why:raise ValueError("rank "+str(i)+": "+str(why))
        boards,reason=choose_3_5(matched)
        if reason or not 3<=len(boards)<=5:raise ValueError("rank "+str(i)+" insufficient: "+str(reason))
        assert {b["flop"] for b in boards}==set(pre["candidate_3_5_flops"])
        assert len({b["flop_texture"] for b in boards})>=2 and len({b["flop"] for b in boards})==len(boards)
        hero=hero_seat(m["preflop_text"])
        assert hero in (0,1)
        for b in boards:
            assert b["acting_seat"]==hero and b["nl2_locked_variants"]
            assert b["strict_full_street_combo_reachable"]>0
            assert 0<=b["genuine_gto_exploitability_pct"]<=.5 and b["relative_spr_error_pct"]<=5
            assert len(b["source_sha256"])==64 and b["source_run_id"]>0
            assert b["public_board"] and b["actual_exact_action_line"]
            assert all(v["version"]==("exp_ip" if hero==1 else "exp_oop") for v in b["nl2_locked_variants"])
        data["records"][r["model_id"]].update(label="CERT-MULTIBOARD",
            high_frequency_preregistered=True,original_top24_high_frequency_preregistered=False,
            source_blind_expansion_rank=i,prereg_cohort="B74_NEXT20",
            certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=len(boards),
            blocked_reason=None,source_credibility="GITHUB_ACTIONS_AUTHENTIC_CFR_SHA256_AND_FULL_STREET_COMBO_REACH")
        published.append(dict(rank=i,model_id=r["model_id"],flops=[b["flop"] for b in boards],
            thin_combo_warnings=[dict(flop=b["flop"],strict=b["strict_full_street_combo_reachable"]) for b in boards if b["strict_full_street_combo_reachable"]<10],
            source_run_ids=sorted({b["source_run_id"] for b in boards}),
            hero_lock_run_ids=sorted({v["run_id"] for b in boards for v in b["nl2_locked_variants"]})))
    changed={k for k in data["records"] if data["records"][k]!=before["records"][k]}
    assert changed=={r["model_id"] for r in published} and len(changed)==3
    assert sum(r["label"]=="CERT-MULTIBOARD" for r in data["records"].values())==89
    assert sum(r["label"]=="APPROX" for r in data["records"].values())==303
    data.update(schema="NL2_HU_392_MULTIBOARD_CERT_STATUS_V13_BATCH75",CERT_MULTIBOARD=89,APPROX=303,
        original_v12_cert=86,original_v12_approx=306,original_v3_cert=27,original_v3_approx=365,
        original_v2_cert=26,original_v2_approx=366,original_top24_cert=24,original_top24_approx=368,
        original_top24_cutoff_unchanged=True,source_blind_expansion_ranks=list(FROZEN),
        b75_certificates=published,supplementary_cert_count=65,parent_v12_sha256=sha(OLD),
        source_blind_b74_sha256=sha(B74),source_evidence=sources,
        no_generic_texture_GTO=True,no_per_private_combo_observed_pool_rates=True,
        PR2_remains_draft_never_merge=True)
    assert data["independently_verified_completed_batches"]["B4_MICRO"]["run_id"]==44732810327
    matrix=create(data)
    assert matrix["CERT_MULTIBOARD"]==89 and matrix["APPROX"]==303
    assert len(matrix["models"])==89 and len(matrix["boards"])==347
    assert matrix["strict_aggregate"]["named_board_proofs"]==347
    assert matrix["strict_aggregate"]["hero_lock_variants"]>=391
    assert matrix["strict_aggregate"]["b50_research_candidate_boards"]>=102
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    matrix.update(schema="NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V13",
       parent_v13_status_sha256=sha(OUT),no_general_b50_advice=True,
       no_exact_private_combo_pool_counts=True,historical_unknown_counts_remain_null=True,
       PR2_remains_draft_never_merge=True)
    MAT.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+"\n")
    lines=["# B75 | 89 CERT / 303 APPROX source-blind V13","",
      "PR #2 stays Draft; never merge. V1–V12 source ledgers remain byte-for-byte unchanged; V12 86/306 is the verified parent.",
      "Three source-blind preregistered ranks have 3–5 true boards with matching hero locks; no texture-level GTO.",
      "",
      "| Rank | Model | Exact flops | GTO runs | NL2 hero lock runs | Thin-combo warnings |",
      "|---:|---|---|---|---|---|"]
    for x in published:
        lines.append("| "+str(x["rank"])+" | "+x["model_id"]+" | "+", ".join(x["flops"])+
          " | "+str(x["source_run_ids"])+" | "+str(x["hero_lock_run_ids"])+
          " | "+str(x["thin_combo_warnings"])+" |")
    lines+=["","347 exact named board certificates. Some proof has thin legal combos.",
      "LMP restricted 50%-only tree and assumed preflop ranges are not full-game GTO.",
      "Measured NL2 *aggregate* marginals are not observed exact opponent/private-hand frequencies.",
      "50% pot nonpolarized labels refer ONLY to exact supported boards, not to all textures.",
      "Unmatched, assumed and historical unknown node counts remain separate.",
      "Batch E 44732810327 verified, 2475/2475 river navigation previously verified.",""]
    DOC.write_text("\n".join(lines))
    MATDOC.write_text("# B75 | All V13 89-model hero-lock and nonpolarized provenance\n\n"+write_md(matrix))
    a=matrix["strict_aggregate"]
    print(json.dumps(dict(PASS=True,CERT=89,APPROX=303,ranks=FROZEN,boards=347,
         locks=a["hero_lock_variants"],b50_candidates=a["b50_research_candidate_boards"],
         b50_unsupported=347-a["b50_research_candidate_boards"]),ensure_ascii=False))
if __name__=="__main__":main()
