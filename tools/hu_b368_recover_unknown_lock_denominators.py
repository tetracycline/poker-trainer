#!/usr/bin/env python3
"""B368 recover historical NL2 source-node denominators from exact original jobs.
Fail closed: only update a source variant if (run, raw subgame SHA, original
root SHA, exact driver lock list, pinned solver commit) all match. Otherwise
leave UNKNOWN. No inferred per-hole-card opponent frequencies.
"""
import collections,copy,hashlib,importlib,json,pathlib,re,sys
D=pathlib.Path("data")
SOLVER=pathlib.Path("solver")
DOWNLOADS=pathlib.Path("downloads")
STATUS=D/"nl2_hu_multiboard_status_v47_b364_rank96.json"
MATRIX=D/"nl2_hu_cert_lock_medium_matrix_v47_b364.json"
GATE=D/"nl2_hu_b364_v47_rank96_three_new_full_100bb_GTO_NL2_OOP_source_gate.json"
OUT=D/"nl2_hu_b368_lock_denominator_recovery.json"
DOC=pathlib.Path("docs/NL2_HU_B368_LOCK_DENOMINATOR_RECOVERY.md")
CSV=D/"nl2_hu_b368_lock_denominator_recovery.csv"
PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def canon(x):
    if isinstance(x,dict):return {k:canon(v) for k,v in sorted(x.items())}
    if isinstance(x,list):return [canon(v) for v in x]
    if isinstance(x,float):return round(x,10)
    return x
def pf_path(root,rel):
    p=pathlib.Path(rel)
    if p.parts[:2]==("solver","postflop"):return root/p
    if p.parts[:1]==("postflop",):return root/"solver"/p
    return root/"solver"/"postflop"/p
def locate_source(run_dir,spot,flop,version,target_sha):
    for mf in run_dir.rglob("evidence/*.json"):
        try:m=read(mf)
        except Exception:continue
        if m.get("spot")!=spot or m.get("version")!=version:continue
        artifact_root=mf.parent.parent
        for c in m.get("cases",[]):
            cf=c.get("flop",m.get("flop"))
            if cf not in (None,flop):continue
            shas=[c.get(k) for k in ("sub_sha256","source_sha256","turn_river_sha256")]
            if target_sha not in shas:continue
            subrel=c.get("sub_json") or c.get("source_path")
            if not subrel:continue
            sub=pf_path(artifact_root,subrel)
            if not sub.is_file() or sha(sub)!=target_sha:continue
            rootrel=c.get("flop_json") or m.get("file_flop")
            if not rootrel:
                rootrel=f"out/{spot}/{version}/{flop}_multiboard.json"
            root=pf_path(artifact_root,rootrel)
            job=root.with_suffix(".job.json")
            if not root.is_file() or not job.is_file():continue
            if c.get("flop_sha256") and sha(root)!=c["flop_sha256"]:continue
            if m.get("file_flop_sha256") and sha(root)!=m["file_flop_sha256"]:continue
            try:
                pinfiles=[artifact_root/"evidence"/"poker-solver-commit.txt",
                          artifact_root/"evidence"/"poker-solver-pin.txt"]
                pins=[x.read_text().strip() for x in pinfiles if x.is_file()]
                if not pins or any(x!=PIN for x in pins):continue
                if board_turn:=None:pass
                return dict(manifest=m,case=c,manifest_path=mf,artifact_root=artifact_root,
                    sub=sub,root=root,job=job,root_sha256=sha(root),sub_sha256=sha(sub))
            except Exception:continue
    return None
def setup_solver():
    sys.path.insert(0,str(SOLVER/"postflop"/"py"))
    sys.path.insert(0,str(pathlib.Path("tools").resolve()))
    import pipeline,ranges,locks as LK
    from solve_hu_missing_branches import EXTRA_SPOTS
    for name,profile in EXTRA_SPOTS.items():
        ranges.SPOTS[name]=profile
        pipeline.SPOTS[name]=profile
    from solve_hu_multiboard_100bb import make_fallbacks,RULES
    pool=read(SOLVER/"inputs/pool_stats.json")["NL2"]
    return pipeline,ranges,LK,make_fallbacks,RULES,pool
def expected_locks(spot,version,flop,ctx):
    pipeline,ranges,LK,make_fallbacks,RULES,pool=ctx
    if spot in RULES:
        driver,meta=make_fallbacks(spot,version,pool,pipeline.lock_list,flop)
        return driver,meta
    if spot not in pipeline.SPOTS:
        raise KeyError("spot absent from pinned pipeline: "+spot)
    driver,meta=pipeline.lock_list(spot,version,flop)
    return driver,meta
def recover_one(board,lock,ctx,run_dir):
    spot,flop=board["spot"],board["flop"]
    version=lock["version"];run=int(lock["source_run_id"]);target=lock["source_sha256"]
    found=locate_source(run_dir,spot,flop,version,target)
    if not found:return None,"EXACT_SOURCE_SHA_OR_MANIFEST_NOT_FOUND"
    m,c,root,job=found["manifest"],found["case"],read(found["root"]),read(found["job"])
    if root.get("flop") not in (None,flop):return None,"ROOT_FLOP_MISMATCH"
    if not isinstance(root.get("nodes"),list):return None,"ROOT_NODES_MISSING"
    if not isinstance(job.get("locks"),list):return None,"ORIGINAL_JOB_LOCKS_MISSING"
    driver,meta=expected_locks(spot,version,flop,ctx)
    if canon(driver)!=canon(job["locks"]):
        return None,"PINNED_LOCK_LIST_NOT_BYTE_EQUIVALENT_TO_ORIGINAL_JOB"
    patterns=[]
    for x in meta:
        if not x.get("pat"):continue
        patterns.append(dict(pat=x["pat"],n=int(x.get("n") or 0),
            scope=x.get("scope","PINNED_MEASURED_NL2_SOURCE"),
            source=x.get("src") or x.get("source") or "",
            size=x.get("size"),street=x.get("street")))
    if len(patterns)!=len(job["locks"]):
        return None,"PATTERN_METADATA_COUNT_MISMATCH"
    villain=1 if version=="exp_oop" else 0
    observed=assumed=unmatched=0
    candidate_nodes=0
    matched_patterns=collections.Counter()
    for n in root["nodes"]:
        if n.get("player")!=villain or len(n.get("acts",[]))<2:continue
        w=n.get("w")
        if not isinstance(w,list) or len(w)<=villain:continue
        if not any(float(x)>1e-4 for x in w[villain]):continue
        candidate_nodes+=1
        hits=[x for x in patterns if re.search(x["pat"],n.get("line",""))]
        if not hits:
            unmatched+=1;continue
        p=hits[0];matched_patterns[p["pat"]]+=1
        if str(p.get("scope","")).startswith("ASSUMED") or p["n"]<500:
            assumed+=1
        else:
            observed+=1
    if observed+assumed+unmatched!=candidate_nodes:
        return None,"NODE_PARTITION_MISMATCH"
    if candidate_nodes==0:
        return None,"NO_VILLAIN_DECISION_NODES"
    # All lock patterns and empirical denominators are recovered from the exact
    # pinned original pool_stats + original job's byte-equivalent lock list.
    denom=[dict(pat=x["pat"],n=x["n"],source=x["source"],scope=x["scope"],
        matched_source_nodes=matched_patterns.get(x["pat"],0)) for x in patterns]
    return dict(run_id=run,source_sha256=target,spot=spot,flop=flop,version=version,
        original_manifest_schema=m.get("schema"),original_turn=c.get("turn"),
        original_action_line=c.get("line") or c.get("flop_line"),
        original_subgame_sha256=found["sub_sha256"],original_root_sha256=found["root_sha256"],
        original_root_job_sha256=sha(found["job"]),poker_solver_pin=PIN,
        lock_pattern_count=len(patterns),candidate_villain_decision_nodes=candidate_nodes,
        observed_marginal=observed,assumed_default=assumed,unmatched_unlocked=unmatched,
        observed_fraction_pct=round(100*observed/candidate_nodes,3),
        pattern_sample_denominators=denom,
        recovery_method="REPLAY_PINNED_LOCKS_BUILD_AND_EXACT_ORIGINAL_ROOT_JOB",
        no_private_hand_conditional_NL2_rates_observed=True),None
def main():
    status=read(STATUS);matrix=read(MATRIX)
    assert status["schema"]=="NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96"
    assert (status["CERT_MULTIBOARD"],status["APPROX"],status["EST"],status["TOTAL"])==(159,233,0,392)
    assert matrix["parent_v47_status_sha256"]==sha(STATUS)
    assert matrix["strict_aggregate"]["hero_lock_variants"]==698
    unknown=[]
    for b in matrix["boards"]:
        for l in b["hero_lock_proofs"]:
            c=l["source_node_counts"]
            if all(c[k] is None for k in ("observed_marginal","assumed_default","unmatched_unlocked")):
                unknown.append((b,l))
    assert len(unknown)==334,("unexpected historical UNKNOWN count",len(unknown))
    run_ids=sorted({int(l["source_run_id"]) for b,l in unknown})
    missing=[r for r in run_ids if not (DOWNLOADS/str(r)).exists()]
    ctx=setup_solver()
    # Calibrate the exact reconstruction against a previously recorded,
    # non-UNKNOWN LMP source in the same downloaded source-run cohort.
    known_checks=[];known_mismatches=[]
    for b in matrix["boards"]:
        for l in b["hero_lock_proofs"]:
            if l["node_rate_data_status"]=="HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN":continue
            if int(l["source_run_id"]) not in run_ids:continue
            x,reason=recover_one(b,l,ctx,DOWNLOADS/str(l["source_run_id"]))
            if not x:continue
            c=l["source_node_counts"]
            actual=(x["observed_marginal"],x["assumed_default"],x["unmatched_unlocked"])
            expected=(c["observed_marginal"],c["assumed_default"],c["unmatched_unlocked"])
            if actual==expected:
                known_checks.append(dict(run_id=x["run_id"],sha=x["source_sha256"],counts=actual))
            else:
                known_mismatches.append(dict(run_id=x["run_id"],sha=x["source_sha256"],actual=actual,expected=expected))
            if len(known_checks)>=3:break
        if len(known_checks)>=3:break
    # Any source family that fails its known-count calibration is excluded from
    # recovery; do not "correct" a known source with a different counting rule.
    bad_types=set()
    for item in known_mismatches:
        bad_types.add((item.get("spot"),item.get("version")))
    recovered={};skipped=collections.Counter();details=[]
    for b,l in unknown:
        if (b["spot"],l["version"]) in bad_types:
            skipped["KNOWN_SOURCE_CALIBRATION_MISMATCH"]+=1
            continue
        key=f'{l["source_run_id"]}:{l["source_sha256"]}'
        if key in recovered:continue
        run_dir=DOWNLOADS/str(l["source_run_id"])
        if not run_dir.exists():
            skipped["SOURCE_RUN_ARTIFACTS_UNAVAILABLE"]+=1
            continue
        result,reason=recover_one(b,l,ctx,run_dir)
        if result:
            recovered[key]=result
        else:
            skipped[reason]+=1
            details.append(dict(key=key,spot=b["spot"],flop=b["flop"],reason=reason))
    # Apply only exact raw-source matches and exact original-job lock-list matches.
    updated=0
    for b,l in unknown:
        key=f'{l["source_run_id"]}:{l["source_sha256"]}'
        x=recovered.get(key)
        if not x:continue
        model=status["records"][b["model_id"]]
        boards=[z for z in model["certified_3_to_5_exact_flop_boards"]
            if z["flop"]==b["flop"] and z["public_board"]==b["exact_public_board"]]
        assert len(boards)==1
        variants=[v for v in boards[0]["nl2_locked_variants"]
            if v["run_id"]==x["run_id"] and v["sha256"]==x["source_sha256"]]
        assert len(variants)==1
        v=variants[0]
        v["observed_marginal_source_nodes"]=x["observed_marginal"]
        v["assumed_default_source_nodes"]=x["assumed_default"]
        v["unlocked_source_nodes"]=x["unmatched_unlocked"]
        v["villain_observed_pattern_node_share_pct"]=x["observed_fraction_pct"]
        v["unknown_history_frequency_filled_with_default"]=bool(x["assumed_default"])
        v["source_scope"]=v.get("source_scope","PARTIAL_NL2_OBSERVED_AGGREGATE_LOCK")+"; EXACT_PINNED_POOL_DENOMINATOR_RECOVERED"
        v["recovered_pattern_denominators"]=x["pattern_sample_denominators"]
        v["source_node_counts_recovery_method"]=x["recovery_method"]
        updated+=1
    assert updated==sum(1 for b,l in unknown if f'{l["source_run_id"]}:{l["source_sha256"]}' in recovered)
    if updated==0:
        raise RuntimeError("No exact original lock denominators recovered; leave all 334 UNKNOWN unchanged.")
    before_unknown=len(unknown)
    status["B368_lock_denominator_recovery"]=dict(
        schema="NL2_HU_B368_PINNED_POOL_LOCK_DENOMINATOR_RECOVERY_V1",
        source_matrix_sha256=sha(MATRIX),source_unknown_variants=before_unknown,
        unique_original_source_runs=run_ids,missing_run_artifact_dirs=missing,
        known_source_calibration_checks=known_checks,known_source_calibration_mismatches=known_mismatches,
        unique_raw_lock_sources=len(recovered),recovered_lock_variants=updated,
        remaining_unknown_variants=before_unknown-updated,
        recovery_method="Pinned poker-solver locks.build/pool_stats and exact original job/root raw source SHA; exact lock-list equivalence required.",
        empirical_sample_denominators_recovered=True,
        exact_source_node_partitions_recovered=True,
        no_private_hand_conditional_NL2_frequencies=True,
        skipped_reasons=dict(skipped),unresolved_sources=details,
        no_inferred_or_fabricated_counts=True)
    status_path=STATUS
    status_path.write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n")
    import hu_cert_lock_medium_audit,hu_cert_lock_medium_coverage_matrix
    audit=hu_cert_lock_medium_audit.audit(status)
    assert (audit["cert_multiboard"],audit["approx"],audit["EST"])==(159,233,0)
    assert (audit["aggregate"]["named_board_proofs"],audit["aggregate"]["paired_hero_locked_source_variants"])==(606,698)
    new_matrix=hu_cert_lock_medium_coverage_matrix.create(status)
    assert (len(new_matrix["boards"]),len(new_matrix["models"]))==(606,159)
    new_unknown=sum(1 for b in new_matrix["boards"] for l in b["hero_lock_proofs"]
        if l["node_rate_data_status"]=="HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN")
    assert new_unknown==before_unknown-updated
    new_matrix.update(schema="NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V47_B368",
        parent_v47_status_sha256=sha(STATUS),
        B368_lock_denominator_recovery_sha256=None,
        source_unknown_variants_before=before_unknown,
        source_unknown_variants_after=new_unknown,
        source_denominator_recovery_method="PINNED_POOL_STATS_AND_EXACT_ORIGINAL_JOB_LOCKS",
        no_inferred_or_fabricated_counts=True,
        PR2_Draft_NEVER_MERGE=True)
    MATRIX.write_text(json.dumps(new_matrix,ensure_ascii=False,indent=2)+"\n")
    overlay=dict(schema="NL2_HU_B368_RECOVERED_LOCK_SOURCE_NODE_COUNTS_V1",
        source_matrix_pre_overlay_sha256=sha(MATRIX),source_status_sha256=sha(STATUS),
        unknown_before=before_unknown,recovered_variants=updated,
        unknown_after=new_unknown,recovered_sources=list(recovered.values()),
        skipped_reason_counts=dict(skipped),unresolved_sources=details,
        no_private_hand_conditional_NL2_frequencies=True)
    OUT.write_text(json.dumps(overlay,ensure_ascii=False,indent=2)+"\n")
    new_matrix["B368_lock_denominator_recovery_sha256"]=sha(OUT)
    MATRIX.write_text(json.dumps(new_matrix,ensure_ascii=False,indent=2)+"\n")
    gate=read(GATE)
    gate["V47_status_sha256"]=sha(STATUS)
    gate["V47_matrix_sha256"]=sha(MATRIX)
    gate["B368_lock_denominator_recovery_sha256"]=sha(OUT)
    GATE.write_text(json.dumps(gate,ensure_ascii=False,indent=2)+"\n")
    # CSV is a compact audit trail, one row per recovered unique run+source SHA.
    import csv
    with CSV.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["run_id","source_sha256","spot","flop","version",
          "candidate_villain_nodes","observed_marginal_nodes","assumed_default_nodes",
          "unmatched_unlocked_nodes","observed_fraction_pct","lock_pattern_count","pattern_sample_denominators_json"])
        for x in recovered.values():
            w.writerow([x["run_id"],x["source_sha256"],x["spot"],x["flop"],x["version"],
              x["candidate_villain_decision_nodes"],x["observed_marginal"],x["assumed_default"],
              x["unmatched_unlocked"],x["observed_fraction_pct"],x["lock_pattern_count"],
              json.dumps(x["pattern_sample_denominators"],ensure_ascii=False,separators=(",",":"))])
    DOC.write_text("# B368: historical node-lock denominators recovered only from exact original sources\n\n"
      f"Original historical UNKNOWN lock variants: **{before_unknown}**. Recovered exact source variants: **{updated}**. Remaining UNKNOWN: **{new_unknown}**.\n\n"
      "Recovery required all of: original run artifact available, exact raw subgame SHA match, exact original root SHA, pinned poker-solver commit, exact original job lock-list equivalence to regenerated pinned pool_stats patterns, and full root villain decision-node partition into observed / assumed / unmatched. Unmatched nodes remain explicitly unlocked. No counts were imputed from board rank or neighboring models. No opponent private-card-conditional NL2 frequencies are claimed.\n\n"
      f"V47 remains **159 CERT /233 APPROX /0 EST**; named boards 606, partial actor locks 698, exact-board b50 nonpolarized research candidates 135. "
      "Only the 135 exact named boards keep the 50% research tag; no general 50% sizing policy. "
      "Full 392-model and HU2475/2475 audits required. PR #2 remains draft; never merge.\n")
    print(json.dumps(dict(before_unknown=before_unknown,recovered=updated,remaining_unknown=new_unknown,
      unique_runs=len(run_ids),unique_sources=len(recovered),known_calibration_checks=len(known_checks),
      known_calibration_mismatches=len(known_mismatches),skipped=dict(skipped),
      CERT=159,APPROX=233,boards=606,locks=698,b50_candidates=new_matrix["strict_aggregate"]["b50_research_candidate_boards"]),ensure_ascii=False))
if __name__=="__main__":main()
