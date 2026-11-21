#!/usr/bin/env python3
"""B35: source-only forensic of older BTN_BB KsQh4d / Js9h4d (run 44653774402).

Six original GitHub artifacts (GTO, exp_oop, exp_ip on both flops).
Records SHA and actual GTO weighted parent nodes and NL2 locked-job status.
Never relabels old UNKNOWN historical lock frequencies as observed.
No GTO or model certifications created by this read-only audit.
"""
import collections, hashlib, json, pathlib
from hu_multiboard_promote import FAM_ROOT

ROOT=pathlib.Path("originals")
DATA=pathlib.Path("data")
OUT=DATA/"nl2_hu_b35_BTN_BB_original_GTO_parent_probe.json"
SPOT="BTN_BB"; RUN=44653774402
FLOPS=("KsQh4d","Js9h4d"); VERS=("gto","exp_oop","exp_ip")
ROOTPOT,ROOTSTACK=FAM_ROOT[SPOT]
MAX_READ=18_000_000

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for z in iter(lambda:f.read(1<<20),b""): h.update(z)
    return h.hexdigest()

def sample(path):
    if path.stat().st_size>MAX_READ:return {"oversized_not_parsed":True}
    try:
        d=json.loads(path.read_text())
    except (ValueError,UnicodeError) as e:
        return {"invalid_json":str(e)[:120]}
    if not isinstance(d,dict):return {"non_object":True}
    result=dict(keys=list(d)[:23],schema=d.get("schema"),flop=d.get("flop"),
        pot=d.get("pot"),stack=d.get("stack"),hero=d.get("hero"),
        rake_rate=d.get("rake_rate"),rake_cap=d.get("rake_cap"),
        node_count=len(d.get("nodes",[])) if isinstance(d.get("nodes"),list) else None,
        turn_count=len(d.get("turns",[])) if isinstance(d.get("turns"),list) else None,
        cases=len(d.get("cases",[])) if isinstance(d.get("cases"),list) else None,
        gto_gap_pct=(d.get("info") or {}).get("gto_expl_pct"))
    if isinstance(d.get("nodes"),list):
        subset=[n for n in d["nodes"] if isinstance(n,dict) and
            n.get("board","") and n.get("wr") and
            n.get("line","") in ("x x/","x b50 c/","b50 c/","b33 c/","b75 c/")]
        result["weighted_hero_parent_nodes"]=[
          dict(line=n.get("line"),board=n.get("board"),turn=n.get("board","")[-2:],
               pot=n.get("pot"),actor=n.get("actor"),
               weighted_seat_lengths=[len(x) for x in n.get("wr",[])])
          for n in subset[:24]]
        result["root_action_names"]=sorted({n.get("line","") for n in d["nodes"]
            if isinstance(n,dict) and n.get("line","").endswith("/")})[:16]
    if isinstance(d.get("locks"),list):
        result["actual_lock_pattern_count"]=len(d["locks"])
    if d.get("schema")=="HU_MISSING_ACTION_HISTORY_CFR_V1":
        result["source_dependency_SHA"]={
          k:d.get(k) for k in ("source_preflop_tree_sha256",
            "source_pipeline_sha256","source_ranges_sha256")}
        result["flops_in_manifest"]=d.get("selected_flops")
    return result

def main():
    status=json.loads((DATA/"nl2_hu_multiboard_status.json").read_text())
    matrix=json.loads((DATA/"nl2_hu_cert_lock_medium_matrix.json").read_text())
    assert status["TOTAL"]==392 and status["CERT_MULTIBOARD"]==24
    assert matrix["CERT_MULTIBOARD"]==24 and matrix["APPROX"]==368
    listed={}
    for b in matrix["boards"]:
        if b["spot"]!=SPOT or b["flop"] not in FLOPS:continue
        old=[z for z in b["hero_lock_proofs"]
             if z["source_run_id"]==RUN and z["node_rate_data_status"]==
             "HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN"]
        if old:
            listed.setdefault(b["flop"],[]).append(dict(
                model_id=b["model_id"],rank=b["rank"],
                actor=b["actor_seat"],board=b["exact_public_board"],
                exact_line=b["exact_action_line"],source_run_id=b["GTO_run_id"],
                gto_sha256=b["GTO_sha256"],
                strict_combos=b["strictly_reachable_combo_count"],
                unknown_legacy_lock_sha256=[z["source_sha256"] for z in old]))
    if not listed:raise ValueError("No registered historical unknown NL2 lock source to improve")
    expected_gto={f:{x["gto_sha256"] for x in records}
         for f,records in listed.items()}
    raw={}
    for flop in FLOPS:
        for version in VERS:
            name=f"nl2-stage2-{SPOT}-{version}-{flop}"
            root=ROOT/name
            if not root.is_dir():raise FileNotFoundError("Missing immutable GitHub artifact "+name)
            files=[p for p in root.rglob("*") if p.is_file()]
            if not files:raise ValueError("Empty original GitHub archive "+name)
            results=[];found=[]
            for path in files:
                rel=path.relative_to(root).as_posix()
                digest=sha(path)
                row=dict(path=rel,bytes=path.stat().st_size,sha256=digest)
                if rel.endswith(".json"):
                    fingerprint=sample(path)
                    row["fingerprint"]=fingerprint
                    if (fingerprint.get("weighted_hero_parent_nodes") and
                        path.name.endswith("_extra_branch.json")):
                        found.append(dict(path=rel,sha256=digest,
                            pot=fingerprint.get("pot"),stack=fingerprint.get("stack"),
                            GTO_gap_pct=fingerprint.get("gto_gap_pct"),
                            weighted_nodes=fingerprint["weighted_hero_parent_nodes"]))
                results.append(row)
            matched=[z for z in results if z["sha256"] in expected_gto.get(flop,set())]
            if version=="gto" and flop in expected_gto and not matched:
                raise ValueError("No original independently registered GTO subgame SHA "+flop)
            raw[name]=dict(flop=flop,version=version,
                original_run=RUN,artifact_name=name,file_count=len(files),
                total_bytes=sum(x["bytes"] for x in results),
                source_ledger_GTO_SHA_matches=[dict(path=x["path"],sha256=x["sha256"])
                   for x in matched],
                original_weighted_parent_candidates=found,
                files=results)
    noGTO=[f for f in listed if not raw[f"nl2-stage2-{SPOT}-gto-{f}"]["source_ledger_GTO_SHA_matches"]]
    if noGTO:raise ValueError("Original GTO SHA not matched: "+str(noGTO))
    report=dict(schema="TASK_HYBRID_B35_IMMUTABLE_BTN_BB_GTO_PARENT_SOURCE_PROBE_V1",
        original_run=RUN,spot=SPOT,flops=list(FLOPS),versions=list(VERS),
        frozen_cert=24,other_approx=368,
        existing_old_UNKNOWN_model_board_rows=listed,
        per_artifact=raw,
        originals_with_GTO_SHA_match=len(listed),
        source_gate="Immutable true original weighted GTO range; old opponent lock rate denominators remain unknown",
        no_claim_of_per_combo_NL2_behavior=True,
        no_new_CFR_solutions=True,no_certification_change=True,never_merge=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(
       audited_archives=len(raw),official_GTO_SHA_matched=[f for f in listed
         if raw[f"nl2-stage2-{SPOT}-gto-{f}"]["source_ledger_GTO_SHA_matches"]],
       possible_parent_lines={name:[x["weighted_nodes"] for x in v["original_weighted_parent_candidates"]]
        for name,v in raw.items() if v["version"]=="gto"},
       unknown_board_entries=sum(len(x) for x in listed.values()),
       CERT=24,APPROX=368),ensure_ascii=False),flush=True)
if __name__=="__main__":main()
