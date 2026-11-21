#!/usr/bin/env python3
"""B58: independently upgrade preregistered rank33 only after B51 real GTO+hero lock.

V1-V5 are immutable, selected rank33 was frozen in source-blind B48. New
exact-board certification does not generalize to all textures/private cards.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md
ROOT=pathlib.Path("data")
P=ROOT/"nl2_hu_multiboard_status_v5_batch55.json"
B48=ROOT/"nl2_hu_b48_next9_sourceblind_gaps.json"
SRC=ROOT/"solver_evidence/NL2_MULTIBOARD_B51_UTG_XX.json.gz"
IDX=ROOT/"solver_evidence/NL2_MULTIBOARD_B51_UTG_XX.index.json"
OUT=ROOT/"nl2_hu_multiboard_status_v6_rank33.json"
MATRIX=ROOT/"nl2_hu_cert_lock_medium_matrix_v6.json"
DOC=pathlib.Path("docs/NL2_HU_B58_V6_RANK33_CERT.md")
MATDOC=pathlib.Path("docs/NL2_HU_B58_V6_ALL_LOCKS_MEDIUM.md")
ID="ln-opfr-t_model-1ocorr7"
def sha(b):return hashlib.sha256(b).hexdigest()
def fsha(p):return sha(p.read_bytes())
def main():
    before=json.loads(P.read_text());pre=json.loads(B48.read_text())
    assert before["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V5_BATCH55"
    assert (before["CERT_MULTIBOARD"],before["APPROX"],before["TOTAL"])==(41,351,392)
    assert pre["schema"]=="NL2_HU_B48_SOURCE_BLIND_NEXT9_GAP_AUDIT_V1"
    assert pre["source_blind_preselection_ranks"]==list(range(33,42))
    frozen=next(x for x in pre["rows"] if x["rank"]==33)
    assert frozen["model_id"]==ID and frozen["missing_to_three_flops"]==1
    assert before["records"][ID]["label"]=="APPROX"
    ix=json.loads(IDX.read_text());raw=gzip.decompress(SRC.read_bytes());proof=json.loads(raw)
    assert ix["schema"]=="NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1"
    assert ix["batch"]=="B51_UTG_XX" and ix["run_id"]==44808905109
    assert ix["gto_cases"]>=1 and ix["locked_cases"]>=1 and ix["actual_spot_flop_version_jobs"]==2
    assert ix["source_sha256"]==sha(raw) and ix["gzip_sha256"]==fsha(SRC)
    assert proof["schema"]=="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1" and not proof["errors"]
    assert proof["source_run_id"]==ix["run_id"] and len(proof["artifacts"])==2
    assert {(z["spot"],z["flop"],z["version"]) for z in proof["artifacts"]}=={
         ("UTG_CO","9s6h3d","gto"),("UTG_CO","9s6h3d","exp_oop")}
    rank=json.loads((ROOT/"nl2_hu_multiboard_prerank.json").read_text())
    queue=json.loads((ROOT/"nl2_hu_stage2_queue.json").read_text())
    n=next(dict(x) for x in rank["nodes"] if x["model_id"]==ID)
    model=next(x for x in queue["records"] if x["model_id"]==ID)
    assert n["rank_by_empirically_grounded_frequency_proxy"]==33
    assert model["solver_profile"]=="UTG_CO" and model["family"]=="SRP"
    n["preflop_text"]=model["preflop_text"]
    n["abstract_action_history"]=model["abstract_action_history"]
    old_sources=[pathlib.Path(x) for x in before["source_evidence"]["source_files"]]
    assert SRC not in old_sources and len(old_sources)>=25 and all(x.is_file() for x in old_sources)
    exact,locks,metadata=build_source_index(ROOT,old_sources+[SRC])
    possibilities,reason=candidates(n,exact,locks,None)
    if reason:raise ValueError(str(reason))
    boards,gap=choose_3_5(possibilities)
    if gap or len(boards)!=3:raise ValueError("Rank33 lacks three true GTO+hero lock flops: "+str(gap))
    assert {x["flop"] for x in boards}=={"AsKh3d","Ks7h2d","9s6h3d"}
    assert len({x["flop_texture"] for x in boards})>=2
    seat=hero_seat(model["preflop_text"]);assert seat==0
    for b in boards:
        assert b["acting_seat"]==seat and b["nl2_locked_variants"]
        assert b["actual_exact_action_line"]=="x x/" and b["strict_full_street_combo_reachable"]>0
        assert b["genuine_gto_exploitability_pct"]<=.5 and b["relative_spr_error_pct"]<=5
        assert len(b["source_sha256"])==64
        assert all(z["version"]=="exp_oop" for z in b["nl2_locked_variants"])
    fresh=next(b for b in boards if b["flop"]=="9s6h3d")
    assert fresh["source_run_id"]==ix["run_id"]
    assert any(z["run_id"]==ix["run_id"] for z in fresh["nl2_locked_variants"])
    after=copy.deepcopy(before)
    after["records"][ID].update(label="CERT-MULTIBOARD",high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,source_blind_expansion_rank=33,
        prereg_cohort="B48_NEXT9",
        certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=len(boards),
        blocked_reason=None,source_credibility="GITHUB_ACTIONS_AUTHENTIC_CFR_SHA256_AND_FULL_STREET_COMBO_REACH")
    changed={k for k in before["records"] if before["records"][k]!=after["records"][k]}
    assert changed=={ID}
    assert sum(v["label"]=="CERT-MULTIBOARD" for v in after["records"].values())==42
    assert sum(v["label"]=="APPROX" for v in after["records"].values())==350
    after.update(schema="NL2_HU_392_MULTIBOARD_CERT_STATUS_V6_RANK33",CERT_MULTIBOARD=42,
        APPROX=350,original_v5_cert=41,original_v5_approx=351,
        original_top24_cutoff_unchanged=True,added_cert_rank=33,added_cert_model_id=ID,
        source_blind_expansion_ranks=[33],supplementary_cert_count=18,
        parent_v5_sha256=fsha(P),source_blind_b48_sha256=fsha(B48),
        source_evidence=metadata,no_generic_texture_GTO=True,
        no_exact_private_combo_pool_rates=True,PR2_remains_draft_never_merge=True)
    after["independently_verified_completed_batches"]["B51_UTG_XX"]=dict(status="VERIFIED",
        run_id=ix["run_id"],authentic_jobs=ix["actual_spot_flop_version_jobs"],
        gto_cases=ix["gto_cases"],locked_cases=ix["locked_cases"],
        new_subgames=ix["verified_cases"],gzip_sha256=ix["gzip_sha256"])
    assert after["independently_verified_completed_batches"]["B4_MICRO"]["run_id"]==44732810327
    matrix=create(after)
    assert matrix["CERT_MULTIBOARD"]==42 and matrix["APPROX"]==350
    assert len(matrix["models"])==42 and len(matrix["boards"])==164
    assert matrix["strict_aggregate"]["named_board_proofs"]==164
    OUT.write_text(json.dumps(after,ensure_ascii=False,indent=2)+"\n")
    matrix.update(schema="NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V6",
        parent_v6_sha256=fsha(OUT),no_general_bet_size_advice=True,
        no_exact_private_hand_NL2_frequencies=True,never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+"\n")
    DOC.write_text("# B58 | Rank33 authentic 3-board certification, V6 42/350\n\n"+
      "Original V1–V5 remain unchanged. Preregistered B48 rank33, UTG_CO x-x.\n"+
      "B51 source 44808905109 adds real 9s6h3d GTO and OOP NL2 partial lock.\n"+
      "Three exact boards: "+", ".join(x["flop"] for x in boards)+".\n"+
      "All actor/pot/SPR/source SHA, full-street combos and hero-lock sources pass.\n"+
      "Any small strict combo count is thin evidence. Never generalize other texture cards.\n"+
      "Pool-marginal NL2 frequencies are not private-hand observations. PR #2 Draft, never merge.\n")
    MATDOC.write_text("# B58 | All V6 42 CERT named-board NL2 lock/nonpolarized proofs\n\n"+write_md(matrix))
    c=matrix["strict_aggregate"]
    print(json.dumps({"PASS":True,"CERT":42,"APPROX":350,"boards":len(matrix["boards"]),
       "rank33":[x["flop"] for x in boards],
       "strict_reach":{x["flop"]:x["strict_full_street_combo_reachable"] for x in boards},
       "lock_variants":c["hero_lock_variants"],"b50_candidate_boards":c["b50_research_candidate_boards"]},ensure_ascii=False))
if __name__=="__main__":main()
