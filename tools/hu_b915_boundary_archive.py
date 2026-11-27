"""B915: archive completed B914 exact boundary tests and inspect previously
unresolved historical sources in one bounded inventory. No native invocation,
no registry mutation, no ref mutation. Unknown or expired sources stay blocked.
"""
import base64, hashlib, io, json, os, sys, zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
from hu_b895_archive_r158 import coverage
from hu_b908_source_review import canonical
BASE="3298e1220c06782c84b7ca7b3b406a0e8775315a"
RUN=46002856288
AUDIT=46002855987
PREFIX="data/solver_evidence/b915_boundary_archive/"
LEDGER="data/solver_evidence/b913_wrapper_history/narrowed-history.json"
PINS={
 "7h6h2c":(15198996859,140518634478,"83ae6d0cdd7f2c3702f1468b6709c6dcc590dff44fe092c38357584e391f3512",704,["3c","4c"]),
 "8h7h3c":(15199396009,140518634471,"8d8c517cc49d23f8939c65c0f742f2b15c0af91fd068fbeba9d5feb6e9594a71",694,["2c","4c"]),
}
def dump(p,obj): Path(p).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
def read(p): return json.loads(Path(p).read_bytes())
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def prepare(out):
    h=guard(); cov=coverage()
    root=Path(PREFIX); root.mkdir(parents=True,exist_ok=False); out.mkdir(parents=True,exist_ok=False)
    assert git("hash-object",LEDGER)=="ce302151b06db0038c05906775aeef9ee3af589f"
    ledger=read(LEDGER); assert ledger["coverage"]==cov
    runs={}
    for rid in (RUN,AUDIT):
        r=api("/actions/runs/"+str(rid))
        assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(BASE,BRANCH,"completed","success")
        runs[str(rid)]=r
    receipts={}
    for f,(aid,jid,digest,n,turns) in PINS.items():
        a=api("/actions/artifacts/"+str(aid)); j=api("/actions/jobs/"+str(jid))
        assert (a["name"],a["digest"],a["expired"])==("B914-boundary-"+f,"sha256:"+digest,False)
        assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"],a["workflow_run"]["head_branch"])==(RUN,BASE,BRANCH)
        assert (j["run_id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(RUN,BASE,"verify ("+f+")","completed","success")
        raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True); assert sha(raw)==digest
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            rb=z.read("report.json"); p=json.loads(rb)
        assert p["parent"]==BASE and p["flop"]==f and p["coverage"]==cov
        assert p["original_native_denylist"]==ledger["rows"][f]["original_native_denylist"]
        assert p["symmetry_observed"]==dict(both_observable=n,equal=n,mismatch=0,absent_counterpart=0)
        assert len(p["original_heldout_checks"])==3 and all(x["exact_raw_weights"] and x["exact_job_bytes"] and not x["missing"] for x in p["original_heldout_checks"])
        assert [x["turn"] for x in p["candidates"]]==turns
        for c in p["candidates"]:
            assert c["independent_boundary_replay_pass"] and c["all_three_exact"] and not c["can_dispatch_native"]
            assert len(c["heldout_checks"])==3 and all(x["exact_raw_weights"] and x["exact_job_bytes"] and not x["missing"] for x in c["heldout_checks"])
            assert c["canonical_flop_turn"]==canonical(f,c["turn"])
            assert c["not_same_orbit_as_original_or_other_candidate"] and c["not_same_native_job_sha"]
        assert not p["global_history_clearance"] and p["local_history_remaining"]==0
        assert all(p[k]==0 for k in ("native_solves","cert_promotions","formal_lock_additions","formal_nonpolarized_additions"))
        (root/(f+".zip")).write_bytes(raw); (root/(f+".json")).write_bytes(rb)
        receipts[f]=dict(artifact=a,job=j)
    dump(root/"receipts.json",dict(runs=runs,sources=receipts,coverage=cov,scope="Four exact boundary replays accepted, no global history clearance or native dispatch."))
    dump(out/"prepared.json",dict(parent=h,coverage=cov,files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())},native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))
def publish(out):
    h=guard(); p=read(out/"prepared.json"); assert p["parent"]==h and p["coverage"]==coverage()
    assert not git("diff","--name-only")
    entries=[]
    for path,d in p["files"].items():
        assert path.startswith(PREFIX)
        raw=Path(path).read_bytes(); assert sha(raw)==d
        expect=hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()
        actual=api("/git/blobs",dict(content=base64.b64encode(raw).decode(),encoding="base64"))["sha"]
        assert actual==expect
        entries.append(dict(path=path,mode="100644",type="blob",sha=actual))
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=entries))["sha"]
    c=api("/git/commits",dict(message="B915 archive four audited held-out boundary replays; no CERT promotion",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=h,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",rec); print(json.dumps(rec))
def inventory(out):
    h=guard(); cov=coverage(); out.mkdir(parents=True,exist_ok=False)
    ledger=read(LEDGER); assert ledger["coverage"]==cov
    f="9d7h4c"; remaining=ledger["rows"][f]["remaining"]
    assert len(remaining)==75
    prior=read("data/solver_evidence/b909_review_archive/"+f+".json")
    assert prior["coverage"]==cov
    known={r["id"]:(c["commit"],r) for c in prior["history"]["commits"] for r in c["runs"]}
    targets={canonical(f,t):t for t in prior["history"]["candidate_turns"]}
    assert set(targets.values())=={"2c","2h"}
    # Fetch complete artifact listings even when no flop is present in the name.
    # Pin workflow blobs and collect executed steps; never execute historical code.
    run_rows=[]; artifacts={}; local=[]; issues=[]
    for row in remaining:
        if "run" in row:
            rid=row["run"]; commit,old=known[rid]
            r=api("/actions/runs/"+str(rid))
            assert (r["head_sha"],r["head_branch"],r["path"],r["status"],r["conclusion"])==(commit,BRANCH,old["path"],old["status"],old["conclusion"])
            wf=r["path"]
            src=git("show",commit+":"+wf); blob=git("rev-parse",commit+":"+wf)
            js=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
            aa=api("/actions/runs/"+str(rid)+"/artifacts?per_page=100")
            if js["total_count"]!=len(js["jobs"]) or aa["total_count"]!=len(aa["artifacts"]):
                issues.append(dict(run=rid,reason="pagination incomplete"))
            for a in aa["artifacts"]: artifacts[a["id"]]=a
            run_rows.append(dict(run=rid,head=commit,workflow=wf,workflow_blob=blob,workflow_text=src,
              jobs=[dict(id=j["id"],name=j["name"],conclusion=j["conclusion"],steps=[dict(name=s["name"],conclusion=s["conclusion"]) for s in j.get("steps",[])]) for j in js["jobs"]],
              artifacts=[a["id"] for a in aa["artifacts"]],complete_listing=js["total_count"]==len(js["jobs"]) and aa["total_count"]==len(aa["artifacts"]),
              clearance=False))
        elif "artifact" in row:
            a=api("/actions/artifacts/"+str(row["artifact"])); artifacts[a["id"]]=a
        elif "path" in row: local.append(row["path"])
        else: issues.append(dict(source=row,reason="unrecognized ledger row"))
    # Explicit geometry inventory; accept no absence proof from filenames, no
    # result pairing from a generic summary or mere source-array mention.
    total=0; observations=[]
    def inspect(raw,label):
        rows=[]; members=[]
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=set(z.namelist())
            assert len(names)==len(z.namelist())
            if sum(x.file_size for x in z.infolist())>128*1024*1024:
                return dict(source=label,sha256=sha(raw),blocked="uncompressed budget",clearance=False)
            for n in sorted(names):
                info=z.getinfo(n)
                members.append(dict(name=n,size=info.file_size))
                if not n.lower().endswith(".json") or info.file_size>32*1024*1024:continue
                b=z.read(n)
                try: j=json.loads(b)
                except (ValueError,UnicodeError):continue
                if not isinstance(j,dict):continue
                flop=j.get("flop"); turn=j.get("turn")
                orbit=canonical(flop,turn)
                if orbit is None:continue
                geom=(j.get("pot"),j.get("stack"),j.get("line0"))==(1100,9475,["x","b50","c","/"])
                sibling=n.rsplit("/",1)[0]+"/result.json" if "/" in n else "result.json"
                pair=n.rsplit("/",1)[-1]=="job.json" and sibling in names
                row=dict(member=n,sha256=sha(b),flop=flop,turn=turn,canonical=orbit,pot=j.get("pot"),stack=j.get("stack"),line0=j.get("line0"),same_target_geometry=geom,candidate_turn=targets.get(orbit),paired_result_member=sibling if pair else None)
                if pair:
                    row["paired_result_sha256"]=sha(z.read(sibling))
                rows.append(row)
        return dict(source=label,sha256=sha(raw),members=members,job_like_rows=rows,clearance=False)
    def take(label,size,reader,digest=None):
        nonlocal total
        if size>32*1024*1024 or total+size>256*1024*1024:
            return dict(source=label,blocked="compressed byte budget",clearance=False)
        raw=reader(); total+=len(raw)
        if digest is not None: assert sha(raw)==digest
        try:return inspect(raw,label)
        except (zipfile.BadZipFile,ValueError,KeyError) as e:
            return dict(source=label,sha256=sha(raw),blocked=type(e).__name__,clearance=False)
    # Prioritize unresolved permanent and explicitly named sources before other
    # artifacts, so ancillary audit archives cannot consume the evidence budget.
    for path in local:
        p=Path(path); observations.append(take(path,p.stat().st_size,p.read_bytes))
    explicit={x["artifact"] for x in remaining if "artifact" in x}
    for aid,a in sorted(artifacts.items(),key=lambda x:(x[0] not in explicit,x[0])):
        label="artifact:"+str(aid)
        if a["expired"] or not a.get("digest"):
            observations.append(dict(source=label,blocked="expired or missing digest",clearance=False));continue
        observations.append(take(label,a["size_in_bytes"],lambda aid=aid:api("/actions/artifacts/"+str(aid)+"/zip",raw=True),a["digest"].removeprefix("sha256:")))
    matches=[dict(source=o["source"],**r) for o in observations for r in o.get("job_like_rows",[]) if r["candidate_turn"] is not None]
    report=dict(parent=h,coverage=cov,flop=f,original_native_denylist=ledger["rows"][f]["original_native_denylist"],
      remaining_input=remaining,runs=run_rows,artifact_metadata=artifacts,observations=observations,matching_orbits=matches,issues=issues,
      global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,
      scope="Evidence inventory only. A successful run or nonmatching archive name is not a deduplication clearance; failed and unknown formats retain blockers.")
    dump(out/"inventory.json",report)
    print(json.dumps(dict(runs=len(run_rows),artifact_count=len(artifacts),local_count=len(local),inspected=sum("members" in o for o in observations),blocked=sum("blocked" in o for o in observations),matching_orbits=len(matches),same_geometry=sum(r["same_target_geometry"] for r in matches),bytes=total,clearance=False)))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish,"inventory":inventory}[sys.argv[1]](Path(sys.argv[2]).resolve())
