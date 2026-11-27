"""B908: archive B907 repairs; resolve named dispatch histories and replay frozen jobs.
Read-only evidence; never dispatch a solver, promote a cell, or update refs.
"""
import base64, hashlib, io, itertools, json, os, re, subprocess, sys, zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
from hu_b895_archive_r158 import coverage
from hu_b467_river_source_gate import compact
import hu_b905_bb_archive_plan as bb
import hu_b711_bb_lead_rivers as native
import hu_b766_rank75_chance_turns as chance
import hu_b904_bb_saved_root_screen as screen

BASE="9ee18d4bc447cd62959153c1775325280abd6d02"
HEAD="778afa98de3bab6eba25d763c112b453f18c0fc8"
RUN=45948668066
PREFIX="data/solver_evidence/b908_source_review/"
PINS={
 "bb-7h6h2c":(15175752660,140339154995,"d1cf5121ecd07f9d2dfee20e4c4cce10ec1c594bafdd290ff7b1fbfe54134215",["3c","4c"]),
 "bb-9d7h4c":(15175219263,140339155046,"a7494e83296b23462f442ac954448850d98c48514729c5be77263ca19f38bc06",["2c","2h"]),
 "btn-5h4h3s":(15175313908,140339154942,"158792579df72e3e752da38ee1893c8d8ed7fe208d5c74ca11c685f2cad8f689",["3c","4s"]),
 "btn-8h7h5c":(15175244044,140339154894,"76d3330e9958c0c3f68b317df33f2078db1893d19116f1d259f29907a50437f6",["8c","8s"]),
}
def dump(p,x): p.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h

def read_pin(key):
    aid,jid,digest,turns=PINS[key]
    kind,flop=key.split("-")
    a=api("/actions/artifacts/"+str(aid));j=api("/actions/jobs/"+str(jid))
    assert (a["name"],a["digest"],a["expired"])==("B907-"+key,"sha256:"+digest,False)
    assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"],a["workflow_run"]["head_branch"])==(RUN,HEAD,BRANCH)
    assert (j["run_id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(RUN,HEAD,"repair ("+kind+", "+flop+")","completed","success")
    raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True);assert sha(raw)==digest
    member="plan.json" if kind=="bb" else "report.json"
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        rb=z.read(member);p=json.loads(rb)
        assert p["flop"]==flop and p["coverage"]==coverage()
        assert all(p[k]==0 for k in ("native_solves","cert_promotions","formal_lock_additions","formal_nonpolarized_additions"))
        if kind=="bb":
            assert [x["turn"] for x in p["plans"]]==turns and not p["historical_inventory"]["clearance"]
            for x in p["plans"]:
                assert not x["can_dispatch_native"] and sha(z.read(x["turn"]+"-gto-job.json"))==x["job_sha256"]
        else:
            assert [x["turn"] for x in p["rows"]]==turns
            assert all(x["rank104"]=="B75_NOT_IN_ORIGINAL_MENU" and x["rank105"]=="NO_COMMON_PHYSICAL_ROUTE_PAIR_BEFORE_RIVER" and not x["possible_rivers"] and not x["cert_eligible"] for x in p["rows"])
    return raw,rb,p,dict(artifact=a,job=j)

def prepare(out):
    h=guard();cov=coverage();out.mkdir(parents=True,exist_ok=False)
    r=api("/actions/runs/"+str(RUN))
    assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(HEAD,BRANCH,"completed","success")
    root=Path(PREFIX);root.mkdir(parents=True,exist_ok=False)
    receipts={}
    for key in PINS:
        raw,rb,p,meta=read_pin(key)
        (root/(key+".zip")).write_bytes(raw);(root/(key+".json")).write_bytes(rb);receipts[key]=meta
    dump(root/"receipts.json",dict(run=r,coverage=cov,sources=receipts,scope="Read-only plans and negative screens, not native certification."))
    dump(out/"prepared.json",dict(parent=h,coverage=cov,files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())},native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))

def publish(out):
    h=guard();p=json.loads((out/"prepared.json").read_bytes())
    assert p["parent"]==h and p["coverage"]==coverage() and not git("diff","--name-only")
    entries=[]
    for path,d in p["files"].items():
        assert path.startswith(PREFIX)
        raw=Path(path).read_bytes();assert sha(raw)==d
        expected=hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()
        actual=api("/git/blobs",dict(content=base64.b64encode(raw).decode(),encoding="base64"))["sha"]
        assert actual==expected
        entries.append(dict(path=path,mode="100644",type="blob",sha=actual))
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=entries))["sha"]
    c=api("/git/commits",dict(message="B908 archive four successful B907 repairs; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=h,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))

def canonical(flop,turn):
    if not isinstance(flop,str) or not isinstance(turn,str) or len(flop)!=6 or len(turn)!=2:return None
    cs=[flop[i:i+2] for i in (0,2,4)]
    if any(c[0] not in "23456789TJQKA" or c[1] not in "cdhs" for c in cs+[turn]) or len(set(cs+[turn]))!=4:return None
    vals=[]
    for suit in itertools.permutations("cdhs"):
        m=dict(zip("cdhs",suit))
        vals.append("".join(sorted(c[0]+m[c[1]] for c in cs))+"/"+turn[0]+m[turn[1]])
    return min(vals)

def plan_source(flop):
    if flop=="8h7h3c":
        f=Path("data/solver_evidence/b907_readonly_gate/b905-plan-8h7h3c.zip")
        raw=f.read_bytes();assert sha(raw)=="147124f0c7a7072f07fcce685ed0f87de7ff07ad21ce7bd211da2eb4956860fb"
    else:raw,_,_,_=read_pin("bb-"+flop)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        p=json.loads(z.read("plan.json"));assert p["flop"]==flop and p["coverage"]==coverage()
        jobs={x["turn"]:z.read(x["turn"]+"-gto-job.json") for x in p["plans"]}
        assert all(sha(jobs[x["turn"]])==x["job_sha256"] for x in p["plans"])
    return p,jobs

def root_replay(flop,p,jobs,solver):
    assert git("-C",str(solver),"rev-parse","HEAD")==native.SOLVER
    py=solver/"postflop/py"
    assert (sha((py/"pipeline.py").read_bytes()),sha((py/"ranges.py").read_bytes()),sha((solver/"inputs/pool_stats.json").read_bytes()))==(native.PIPELINE,native.RANGES,native.POOL)
    sys.path.insert(0,str(py));import pipeline
    batch,digest=screen.PINS[flop]
    path=Path("data/solver_evidence")/("NL2_"+batch+"_CO_BB_"+flop.upper()+".zip")
    raw=path.read_bytes();assert sha(raw)==digest==p["source_archive_sha256"]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        proof=json.loads(z.read("proof.json"))
        assert all(sha(z.read(n))==d for n,d in proof["native_file_sha256"].items())
        root=json.loads(z.read("flop/result.json"));assert sha(z.read("flop/result.json"))==proof["root_source_sha256"]
        routes_raw=z.read("rendered-routes.json")
        assert routes_raw==subprocess.check_output(["node","tools/hu_b711_bb_lead_routes.cjs"])
    routes=json.loads(routes_raw)
    old=[r["turn"] for r in proof["turns"]]
    observed={n["board"][-2:]:n for n in root["nodes"] if n["line"]=="x b50 c/"}
    assert set(old)==set(observed) and len(old)==3
    masks={t:chance.blocked(root["hands"],t) for t in old+list(jobs)}
    rows=[]
    for t,job in jobs.items():
        frozen=json.loads(job)
        assert (frozen["flop"],frozen["turn"],frozen["pot"],frozen["stack"],frozen["line0"])==(flop,t,1100,9475,["x","b50","c","/"])
        template=observed[old[0]]
        def rebuild(w):
            n=dict(template,board=flop+t,wr=w)
            rr=dict(root,nodes=[x for x in root["nodes"] if x["line"]!="x b50 c/"]+[n])
            stats,picks=native.gate(rr,t,routes)
            return compact(native.turn_job(rr,t,picks,pipeline))
        assert rebuild(chance.reconstruct(root,observed,masks,old,t))==job
        pairs=[]
        for held in old:
            chosen=[a for a in old if a!=held];weights=[];missing=[]
            for seat,hands in enumerate(root["hands"]):
                w=[]
                for i,h in enumerate(hands):
                    vals=[observed[a]["wr"][seat][i] for a in chosen if i not in masks[a][seat]]
                    if vals:assert all(chance.weight_bytes([v])==chance.weight_bytes([vals[0]]) for v in vals)
                    if i in masks[t][seat]:w.append(0.0)
                    elif vals:w.append(vals[0])
                    else:missing.append([seat,i]);w.append(0.0)
                weights.append(w)
            exact=not missing
            if exact:assert rebuild(weights)==job
            pairs.append(dict(heldout=held,remaining=chosen,unobserved_unblocked=missing,exact_job_bytes=exact))
        rows.append(dict(turn=t,sha256=sha(job),all_three_observations_exact=True,independent_two_observation_replays=pairs,exact_two_observation_count=sum(x["exact_job_bytes"] for x in pairs)))
    return rows

def history_review(flop,p,jobs):
    hist=p["historical_inventory"]
    variants=bb.variants(flop); rx="|".join(variants)
    def matches(s):return any(v in re.sub(r"[^a-z0-9]","",s.lower()) for v in variants)
    # Inspect immutable dispatch diffs through the current parent, not another live offset scan.
    commits=git("log","--format=%H%x09%s","--regexp-ignore-case","-G",rx,BASE,"--",".github/workflows","tools").splitlines()
    old_commits={x.split("\t",1)[0] for x in hist["ancestor_dispatch_matches"]}
    assert old_commits<={x.split("\t",1)[0] for x in commits}
    candidates={canonical(flop,t):t for t in jobs}
    assert None not in candidates and len(candidates)==len(jobs)
    reviewed=[];seen={};unresolved=[];observations=[]
    def inspect_zip(raw,label):
        rows=[];native_count=0
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=set(z.namelist())
            assert len(names)==len(z.namelist()) and sum(x.file_size for x in z.infolist())<=512*1024*1024
            for n in sorted(names):
                if not n.endswith("job.json"):continue
                b=z.read(n);j=json.loads(b)
                if not isinstance(j,dict):continue
                f=j.get("flop");t=j.get("turn")
                k=canonical(f,t)
                result=n.rsplit("/",1)[0]+"/result.json" if "/" in n else "result.json"
                solved=result in names and n.split("/")[-1]=="job.json"
                native_count+=int(solved)
                if k in candidates:
                    rows.append(dict(candidate_turn=candidates[k],source=label,member=n,job_sha256=sha(b),same_job_sha=sha(b)==sha(jobs[candidates[k]]),native_result_present=solved,flop=f,turn=t,pot=j.get("pot"),stack=j.get("stack"),line0=j.get("line0"),same_target_geometry=(j.get("pot"),j.get("stack"),j.get("line0"))==(1100,9475,["x","b50","c","/"])))
            # Source formats without individual jobs remain unresolved, not silently negative.
        return rows,native_count
    def add_art(a):
        aid=a["id"]
        if aid in seen:return
        seen[aid]=a
    for a in hist["artifact_name_matches"]:add_art(api("/actions/artifacts/"+str(a["id"])))
    for row in commits:
        c,_,subject=row.partition("\t")
        patch=git("show","--format=","--unified=2",c,"--",".github/workflows","tools")
        hits=[l for l in patch.splitlines() if matches(l)]
        data=api("/actions/runs?head_sha="+c+"&per_page=100")
        if data["total_count"]>100:unresolved.append({"commit":c,"reason":"run listing truncated"})
        runs=[]
        for r in data["workflow_runs"]:
            if r["head_sha"]!=c or r["head_branch"]!=BRANCH:continue
            runs.append({k:r.get(k) for k in ("id","name","status","conclusion","path")})
            if r["status"]!="completed":unresolved.append({"run":r["id"],"reason":"not completed; do not poll"});continue
            aa=api("/actions/runs/"+str(r["id"])+"/artifacts?per_page=100")
            if aa["total_count"]>100:unresolved.append({"run":r["id"],"reason":"artifact listing truncated"})
            named=[a for a in aa["artifacts"] if matches(a["name"])]
            for a in named:add_art(a)
            # Artifact names without flop identity are not clearance.
            if not named:unresolved.append({"run":r["id"],"reason":"no matching named artifact; inspect immutable dispatch diff"})
        reviewed.append(dict(commit=c,subject=subject,matching_patch_lines=hits,runs=runs))
    total=0;source_rows=[]
    for aid,a in sorted(seen.items()):
        if a["expired"] or not a.get("digest"):
            unresolved.append({"artifact":aid,"reason":"expired or no digest"});continue
        if a.get("size_in_bytes",0)>64*1024*1024 or total+a.get("size_in_bytes",0)>256*1024*1024:
            unresolved.append({"artifact":aid,"reason":"bounded byte budget"});continue
        raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True)
        assert a["digest"]=="sha256:"+sha(raw);total+=len(raw)
        rows,count=inspect_zip(raw,"artifact:"+str(aid))
        observations.extend(rows);source_rows.append(dict(id=aid,name=a["name"],sha256=sha(raw),native_job_result_pairs=count,candidate_matches=len(rows)))
        if not count and not any(x["same_job_sha"] for x in rows):
            unresolved.append({"artifact":aid,"reason":"no inspectable native job/result pair (may be read-only or different archive schema)"})
    # Also check permanent named source bytes, even if GitHub artifact has expired.
    files=[f for f in git("ls-files","data/solver_evidence").splitlines() if f.endswith(".zip") and matches(f)]
    for f in files:
        path=Path(f)
        if path.stat().st_size>64*1024*1024:unresolved.append({"path":f,"reason":"bounded byte budget"});continue
        raw=path.read_bytes();rows,count=inspect_zip(raw,f)
        observations.extend(rows);source_rows.append(dict(path=f,sha256=sha(raw),native_job_result_pairs=count,candidate_matches=len(rows)))
        if not count and not any(x["same_job_sha"] for x in rows):unresolved.append({"path":f,"reason":"no inspectable native job/result pair"})
    return dict(commits=reviewed,sources=source_rows,candidate_observations=observations,unresolved=unresolved,
        candidate_turns={t:{"native_same_geometry_seen":any(x["candidate_turn"]==t and x["native_result_present"] and x["same_target_geometry"] for x in observations),
                            "same_job_native_seen":any(x["candidate_turn"]==t and x["native_result_present"] and x["same_job_sha"] for x in observations)} for t in jobs},
        clearance=False,limitations="Source-level review of named ancestor dispatches and named archives, not global proof of absence from unnamed/expired sources; no new solve permitted.")

def review(out,solver,flop):
    guard();p,jobs=plan_source(flop)
    replay=root_replay(flop,p,jobs,solver)
    history=history_review(flop,p,jobs)
    out.mkdir(parents=True,exist_ok=False)
    report=dict(flop=flop,coverage=coverage(),replay=replay,history=history,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"review.json",report)
    print(json.dumps(dict(flop=flop,replay=replay,history_commits=len(history["commits"]),sources=len(history["sources"]),unresolved=len(history["unresolved"]),candidate_turns=history["candidate_turns"],clearance=False,coverage=report["coverage"])))

if __name__=="__main__":
    m=sys.argv[1];out=Path(sys.argv[2]).resolve()
    if m=="review":review(out,Path(sys.argv[3]).resolve(),sys.argv[4])
    else:{"prepare":prepare,"publish":publish}[m](out)
