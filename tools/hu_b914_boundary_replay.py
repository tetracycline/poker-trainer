"""B914: independent two-observation boundary replay using only the free-suit
automorphism as a testable missing-weight hypothesis. No solver invocation.
A failed equality test is retained as a blocker, not replaced by an estimate.
"""
import io, json, os, subprocess, sys, zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
from hu_b895_archive_r158 import coverage
from hu_b467_river_source_gate import compact
from hu_sequential_cfr_reach import cardkey
import hu_b711_bb_lead_rivers as native
import hu_b766_rank75_chance_turns as chance
from hu_b908_source_review import canonical

BASE="0a6324667b4c7e9cbbd6995b968a1028bd7bcdd9"
E=Path("data/solver_evidence")
LEDGER=E/"b913_wrapper_history/narrowed-history.json"
PINS={
    "7h6h2c":("b908_source_review/bb-7h6h2c.zip","d1cf5121ecd07f9d2dfee20e4c4cce10ec1c594bafdd290ff7b1fbfe54134215","7c93bee571de0619b6d043b4535b50777103d03b",["3c","4c"]),
    "8h7h3c":("b907_readonly_gate/b905-plan-8h7h3c.zip","147124f0c7a7072f07fcce685ed0f87de7ff07ad21ce7bd211da2eb4956860fb","0d38135600ab3566ce126f6d9600d7ac9e7cb7f5",["2c","4c"]),
}
def read(p):return json.loads(Path(p).read_bytes())
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h

def main(out,solver,flop):
    h=guard();cov=coverage()
    assert git("hash-object",str(LEDGER))=="ce302151b06db0038c05906775aeef9ee3af589f"
    ledger=read(LEDGER)
    lr=ledger["rows"][flop]
    assert not lr["remaining"] and not lr["clearance"] and not lr["can_dispatch_native"]
    assert ledger["coverage"]==cov
    planpath,plandigest,reviewblob,newturns=PINS[flop]
    reviewpath=E/"b909_review_archive"/(flop+".json")
    assert git("hash-object",str(reviewpath))==reviewblob
    review=read(reviewpath)
    assert review["coverage"]==cov and not review["history"]["clearance"]
    assert set(review["history"]["candidate_turns"])==set(newturns)
    assert all(not any(v.values()) for v in review["history"]["candidate_turns"].values())
    raw=(E/planpath).read_bytes();assert sha(raw)==plandigest
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        plan=json.loads(z.read("plan.json"))
        assert plan["flop"]==flop and plan["coverage"]==cov
        assert [x["turn"] for x in plan["plans"]]==newturns
        frozen={t:z.read(t+"-gto-job.json") for t in newturns}
        assert all(sha(frozen[x["turn"]])==x["job_sha256"] and not x["can_dispatch_native"] for x in plan["plans"])
    deny=lr["original_native_denylist"]
    source=(E/deny["archive"]).read_bytes()
    assert sha(source)==deny["archive_sha256"]==plan["source_archive_sha256"]
    with zipfile.ZipFile(io.BytesIO(source)) as z:
        assert z.testzip() is None
        proof=json.loads(z.read("proof.json"))
        assert (proof["flop"],proof["spot"],proof["actor"],proof["flop_line"])==(flop,"CO_BB",0,"x b50 c")
        assert all(sha(z.read(n))==d for n,d in proof["native_file_sha256"].items())
        assert {n:sha(z.read(n)) for n in z.namelist() if n.endswith("/job.json")}==deny["native_job_sha256"]
        root=json.loads(z.read("flop/result.json"))
        assert sha(z.read("flop/result.json"))==proof["root_source_sha256"]
        assert sha(z.read("flop/job.json"))==proof["root_job_sha256"]
        oldturns=[p["turn"] for p in proof["turns"]]
        originaljobs={t:z.read(t+"-gto/job.json") for t in oldturns}
        routebytes=z.read("rendered-routes.json")
    assert len(oldturns)==3 and len(set(oldturns))==3
    assert (root["flop"],root["pot"],root["stack"])==(flop,550,9750)
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    assert routebytes==subprocess.check_output(["node","tools/hu_b711_bb_lead_routes.cjs"])
    routes=json.loads(routebytes)
    assert git("-C",str(solver),"rev-parse","HEAD")==native.SOLVER
    py=solver/"postflop/py"
    assert (sha((py/"pipeline.py").read_bytes()),sha((py/"ranges.py").read_bytes()),sha((solver/"inputs/pool_stats.json").read_bytes()))==(native.PIPELINE,native.RANGES,native.POOL)
    sys.path.insert(0,str(py))
    import pipeline
    observed={n["board"][-2:]:n for n in root["nodes"] if n["line"]=="x b50 c/"}
    assert set(observed)==set(oldturns)
    masks={t:chance.blocked(root["hands"],t) for t in oldturns+newturns}
    free=sorted(set("cdhs")-{flop[i] for i in (1,3,5)})
    assert len(free)==2
    trans=str.maketrans(free[0]+free[1],free[1]+free[0])
    assert flop.translate(trans)==flop
    index=[{cardkey(hand):i for i,hand in enumerate(hands)} for hands in root["hands"]]
    assert all(len(index[s])==len(root["hands"][s]) for s in (0,1))
    def key(v):return chance.weight_bytes([v])
    def known(seat,i,selected):
        vals=[observed[t]["wr"][seat][i] for t in selected if i not in masks[t][seat]]
        assert not vals or all(key(x)==key(vals[0]) for x in vals)
        return vals[0] if vals else None
    def partner(seat,i):
        hand=root["hands"][seat][i]
        transformed="".join(c[0]+c[1].translate(trans) for c in cardkey(hand))
        return index[seat].get(cardkey(transformed))
    # Check the symmetry hypothesis against all directly observable raw weights.
    symmetry={"both_observable":0,"equal":0,"mismatch":0,"absent_counterpart":0}
    for seat in (0,1):
        for i in range(len(root["hands"][seat])):
            k=partner(seat,i)
            if k is None:
                symmetry["absent_counterpart"]+=1
                continue
            a,b=known(seat,i,oldturns),known(seat,k,oldturns)
            if a is not None and b is not None:
                symmetry["both_observable"]+=1
                symmetry["equal" if key(a)==key(b) else "mismatch"]+=1
    def reconstruct(target,selected):
        weights=[];inferred=[];missing=[]
        for seat in (0,1):
            row=[]
            for i,hand in enumerate(root["hands"][seat]):
                if i in masks[target][seat]:
                    row.append(0.0);continue
                v=known(seat,i,selected)
                if v is None:
                    k=partner(seat,i)
                    v=known(seat,k,selected) if k is not None else None
                    detail=dict(seat=seat,index=i,hand=hand,counterpart_index=k,
                                counterpart=root["hands"][seat][k] if k is not None else None,
                                selected=list(selected))
                    if v is None:
                        missing.append(detail);v=0.0
                    else:
                        inferred.append(dict(detail,value=v))
                row.append(v)
            weights.append(row)
        return weights,inferred,missing
    def build(t,w):
        n=dict(observed[oldturns[0]],board=flop+t,wr=w)
        rr=dict(root,nodes=[x for x in root["nodes"] if x["line"]!="x b50 c/"]+[n])
        _,picks=native.gate(rr,t,routes)
        return compact(native.turn_job(rr,t,picks,pipeline))
    def compare(a,b):
        return [[i for i,(x,y) in enumerate(zip(ar,br,strict=True)) if key(x)!=key(y)] for ar,br in zip(a,b,strict=True)]
    def check(target,selected,ref,job):
        w,inferred,missing=reconstruct(target,selected)
        diffs=compare(w,ref)
        exact_raw=not missing and not any(diffs)
        # Validate every inferred value against the withheld raw reference, not merely accepted actions.
        for row in inferred:
            s,i=row["seat"],row["index"]
            row["reference_equal"]=key(row["value"])==key(ref[s][i])
        exact_job=exact_raw and build(target,w)==job
        return dict(target=target,selected=selected,inferred=inferred,missing=missing,
                    differing_raw_indices=diffs,exact_raw_weights=exact_raw,exact_job_bytes=exact_job)
    original_checks=[]
    for t in oldturns:
        ref=observed[t]["wr"]
        assert build(t,ref)==originaljobs[t]
        original_checks.append(check(t,[x for x in oldturns if x!=t],ref,originaljobs[t]))
    oldorbits={canonical(flop,t) for t in oldturns}
    assert None not in oldorbits
    candidates=[]
    for t in newturns:
        ref=chance.reconstruct(root,observed,masks,oldturns,t)
        job=frozen[t]
        assert build(t,ref)==job
        j=json.loads(job)
        assert (j["flop"],j["turn"],j["pot"],j["stack"],j["line0"])==(flop,t,1100,9475,["x","b50","c","/"])
        orbit=canonical(flop,t)
        assert orbit is not None and orbit not in oldorbits
        oldorbits.add(orbit)
        assert sha(job) not in deny["native_job_sha256"].values()
        checks=[check(t,[x for x in oldturns if x!=held],ref,job) for held in oldturns]
        candidates.append(dict(turn=t,job_sha256=sha(job),canonical_flop_turn=orbit,
            not_same_orbit_as_original_or_other_candidate=True,not_same_native_job_sha=True,
            all_three_exact=True,heldout_checks=checks,
            independent_boundary_replay_pass=all(x["exact_job_bytes"] for x in checks)
              and all(x["exact_job_bytes"] for x in original_checks)
              and symmetry["mismatch"]==0,
            can_dispatch_native=False))
    report=dict(schema="NL2_B914_TWO_OBSERVATION_FREE_SUIT_TEST_V1",parent=h,flop=flop,
        coverage=cov,source_archive_sha256=sha(source),plan_archive_sha256=plandigest,
        original_native_denylist=deny,free_suit_swap=free,symmetry_observed=symmetry,
        original_heldout_checks=original_checks,candidates=candidates,
        local_history_remaining=0,global_history_clearance=False,
        scope="Exact raw-weight and job-byte replay test only. A free-suit hypothesis may fail; no native solve or promotion. Unnamed sources outside local ledger not cleared.",
        native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    out.mkdir(parents=True,exist_ok=False)
    (out/"report.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(dict(flop=flop,symmetry=symmetry,original_exact=sum(x["exact_job_bytes"] for x in original_checks),
          candidates=[dict(turn=x["turn"],boundary_pass=x["independent_boundary_replay_pass"],exact_heldout=sum(c["exact_job_bytes"] for c in x["heldout_checks"])) for x in candidates],
          can_dispatch_native=False)))
if __name__=="__main__":
    main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),sys.argv[3])
