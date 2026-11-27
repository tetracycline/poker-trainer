"""B916: freeze completed B915 inventory, and independently search immutable
repository evidence and generic B915 archives for all six frozen continuations.
No solve, registry change, or ref mutation. An absence in this bounded scan
is not global deduplication clearance.
"""
import base64, hashlib, io, json, os, sys, zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
from hu_b895_archive_r158 import coverage
from hu_b908_source_review import canonical

BASE="27da6e61fbe6838d159bd1a227fff9bb4fc7d690"
SOURCE="2b397246b7f99af0407113286396dfa0bf57bb74"
RUN=46010167190
AUDIT=46010167273
JOB=140543347792
AID=15203067206
DIGEST="8376b3a660286043e6a1a3cdffaae94c75c34581ac1d872236e98e202b02dd48"
E=Path("data/solver_evidence")
PREFIX=E/"b916_history_inventory"
LEDGER=E/"b913_wrapper_history/narrowed-history.json"
def read(p): return json.loads(Path(p).read_bytes())
def dump(p,x): Path(p).write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def load_inventory():
    runs={str(r):api("/actions/runs/"+str(r)) for r in (RUN,AUDIT)}
    assert all((r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(SOURCE,BRANCH,"completed","success") for r in runs.values())
    a=api("/actions/artifacts/"+str(AID)); j=api("/actions/jobs/"+str(JOB))
    assert (a["name"],a["digest"],a["expired"])==("B915-history-inventory","sha256:"+DIGEST,False)
    assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"])==(RUN,SOURCE)
    assert (j["run_id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(RUN,SOURCE,"history-inventory","completed","success")
    raw=api("/actions/artifacts/"+str(AID)+"/zip",raw=True); assert sha(raw)==DIGEST
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        rb=z.read("inventory.json"); p=json.loads(rb)
    lr=read(LEDGER)["rows"]["9d7h4c"]
    assert p["parent"]==SOURCE and p["flop"]=="9d7h4c" and p["coverage"]==coverage()
    assert p["remaining_input"]==lr["remaining"] and len(p["remaining_input"])==75
    assert p["original_native_denylist"]==lr["original_native_denylist"]
    assert len(p["runs"])==61 and len(p["artifact_metadata"])==43 and len(p["observations"])==49
    assert not p["matching_orbits"] and not any("blocked" in x for x in p["observations"])
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    assert p["native_solves"]==p["cert_promotions"]==0
    return raw,rb,p,dict(runs=runs,artifact=a,job=j)
def targets():
    out={}; deny=set()
    ledger=read(LEDGER)
    for flop,turns in {"7h6h2c":["3c","4c"],"8h7h3c":["2c","4c"],"9d7h4c":["2c","2h"]}.items():
        deny.update(ledger["rows"][flop]["original_native_denylist"]["native_job_sha256"].values())
        if flop=="9d7h4c":
            path=E/"b908_source_review/bb-9d7h4c.zip"
            with zipfile.ZipFile(path) as z:
                p=json.loads(z.read("plan.json"))
                rows=[dict(turn=x["turn"],job_sha256=x["job_sha256"],boundary_pass=False) for x in p["plans"]]
        else:
            p=read(E/"b915_boundary_archive"/(flop+".json"))
            rows=[dict(turn=x["turn"],job_sha256=x["job_sha256"],boundary_pass=x["independent_boundary_replay_pass"]) for x in p["candidates"]]
        assert [r["turn"] for r in rows]==turns
        for r in rows:
            k=canonical(flop,r["turn"]); assert k and k not in out
            out[k]=dict(r,flop=flop,canonical=k)
    assert len(out)==6 and len({v["job_sha256"] for v in out.values()})==6
    assert not (deny & {v["job_sha256"] for v in out.values()})
    return out,sorted(deny)
def prepare(out):
    h=guard(); cov=coverage(); raw,rb,p,receipt=load_inventory()
    assert not PREFIX.exists(); PREFIX.mkdir(parents=True)
    out.mkdir(parents=True,exist_ok=False)
    (PREFIX/"inventory.zip").write_bytes(raw); (PREFIX/"inventory.json").write_bytes(rb)
    dump(PREFIX/"receipts.json",dict(receipt,coverage=cov,scope="Immutable B915 inventory only; no source clearance."))
    dump(out/"prepared.json",dict(parent=h,coverage=cov,files={str(p):sha(p.read_bytes()) for p in sorted(PREFIX.iterdir())},
        native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))
def publish(out):
    h=guard(); p=read(out/"prepared.json"); assert p["parent"]==h and p["coverage"]==coverage()
    assert not git("diff","--name-only")
    entries=[]
    for path,digest in p["files"].items():
        assert Path(path).parent==PREFIX
        b=Path(path).read_bytes(); assert sha(b)==digest
        expected=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
        actual=api("/git/blobs",dict(content=base64.b64encode(b).decode(),encoding="base64"))["sha"]
        assert expected==actual
        entries.append(dict(path=path,mode="100644",type="blob",sha=actual))
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=entries))["sha"]
    c=api("/git/commits",dict(message="B916 archive audited B915 historical inventory; no CERT promotion",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=h,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",rec); print(json.dumps(rec))
def scan(out):
    h=guard(); cov=coverage(); _,_,inv,_=load_inventory()
    out.mkdir(parents=True,exist_ok=False)
    target,deny=targets(); bysha={v["job_sha256"]:v for v in target.values()}
    obs=[]; blocked=[]; sources=[]; seen=set(); read_bytes=0; expanded=0
    max_raw=768*1024**2; max_expand=3*1024**3
    def issue(source,reason):
        blocked.append(dict(source=source,reason=reason))
    def walk(b,label,depth=0):
        nonlocal expanded
        digest=sha(b)
        if digest in seen:
            sources.append(dict(source=label,sha256=digest,duplicate_bytes=True)); return
        seen.add(digest)
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            names=set(z.namelist()); sizes=sum(x.file_size for x in z.infolist())
            if len(names)!=len(z.namelist()): issue(label,"duplicate ZIP member names"); return
            if sizes>256*1024**2 or expanded+sizes>max_expand: issue(label,"expanded byte budget"); return
            expanded+=sizes
            stats=dict(source=label,sha256=digest,member_count=len(names),job_result_pairs=0,inspectable_geometry_jobs=0)
            for n in sorted(names):
                info=z.getinfo(n); low=n.lower()
                if info.is_dir(): continue
                if info.file_size>64*1024**2:
                    issue(label+"!"+n,"member byte budget"); continue
                if low.endswith(".zip"):
                    if depth>=2: issue(label+"!"+n,"nested depth budget"); continue
                    try: walk(z.read(n),label+"!"+n,depth+1)
                    except (zipfile.BadZipFile,ValueError,KeyError,RuntimeError) as e: issue(label+"!"+n,type(e).__name__)
                    continue
                if not low.endswith(".json"): continue
                raw=z.read(n); d=sha(raw)
                try: j=json.loads(raw)
                except (UnicodeError,ValueError): issue(label+"!"+n,"invalid JSON"); continue
                if not isinstance(j,dict): continue
                # Only top-level job objects count as exact native job geometry.
                # Result summaries and nested references are evidence pointers only.
                basename=n.rsplit("/",1)[-1]; sibling=n.rsplit("/",1)[0]+"/result.json" if "/" in n else "result.json"
                paired=basename=="job.json" and sibling in names
                stats["job_result_pairs"]+=int(paired)
                f,t=j.get("flop"),j.get("turn")
                k=canonical(f,t)
                if paired and k: stats["inspectable_geometry_jobs"]+=1
                hit=target.get(k) or bysha.get(d)
                if hit is None: continue
                geom=(j.get("pot"),j.get("stack"),j.get("line0"))==(1100,9475,["x","b50","c","/"])
                row=dict(source=label,member=n,job_sha256=d,flop=f,turn=t,canonical=k,
                    candidate=hit,exact_job_sha=d==hit["job_sha256"],same_geometry=geom,
                    job_result_member_pair=paired,pot=j.get("pot"),stack=j.get("stack"),line0=j.get("line0"))
                if paired:
                    result=z.read(sibling); row["result_sha256"]=sha(result)
                    try:
                        q=json.loads(result)
                        row["result_geometry_matches"]=isinstance(q,dict) and (q.get("flop"),q.get("turn"),q.get("pot"),q.get("stack"))==(f,t,j.get("pot"),j.get("stack"))
                    except (ValueError,UnicodeError): row["result_geometry_matches"]=False
                obs.append(row)
            sources.append(stats)
    def take(label,n,reader,expected=None):
        nonlocal read_bytes
        if n>64*1024**2 or read_bytes+n>max_raw: issue(label,"compressed byte budget"); return
        raw=reader(); read_bytes+=len(raw)
        if expected is not None: assert sha(raw)==expected
        try: walk(raw,label)
        except (zipfile.BadZipFile,ValueError,KeyError,RuntimeError) as e: issue(label,type(e).__name__)
    # Use the complete immutable B915 listing, including generic archive names.
    for aid,a in sorted(inv["artifact_metadata"].items(),key=lambda x:int(x[0])):
        if a["expired"] or not a.get("digest"): issue("artifact:"+aid,"expired or missing digest"); continue
        take("artifact:"+aid,a["size_in_bytes"],lambda aid=aid:api("/actions/artifacts/"+aid+"/zip",raw=True),a["digest"].removeprefix("sha256:"))
    # Search every tracked permanent ZIP in solver_evidence, not just filename hits.
    paths=[Path(p) for p in git("ls-files","data/solver_evidence").splitlines() if p.lower().endswith(".zip")]
    keys=("7h6h2c","8h7h3c","9d7h4c")
    for p in sorted(paths,key=lambda p:(not any(k in str(p).lower() for k in keys),p.stat().st_size,str(p))):
        take(str(p),p.stat().st_size,p.read_bytes)
    hits=[x for x in obs if x["job_result_member_pair"] and (x["exact_job_sha"] or x["same_geometry"])]
    summary={k:dict(candidate=v,native_duplicate_candidates=[x for x in hits if x["candidate"]["canonical"]==k],
        can_dispatch_native=False) for k,v in target.items()}
    report=dict(parent=h,coverage=cov,targets=summary,original_native_denylist=deny,observations=obs,
        sources=sources,blocked=blocked,tracked_archives=len(paths),source_inventory_sha256=DIGEST,
        global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,
        scope="Byte/hash/orbit scan; result-member pairing is not a validated native result. Generic or unsupported formats and nonenumerated historical artifacts remain blockers.")
    dump(out/"scan.json",report)
    print(json.dumps(dict(targets=len(target),boundary_pass=sum(x["boundary_pass"] for x in target.values()),tracked_archives=len(paths),
        source_rows=len(sources),unique_zip_bytes=len(seen),blocked=len(blocked),candidate_observations=len(obs),
        native_duplicate_candidates=len(hits),read_bytes=read_bytes,expanded_bytes=expanded,clearance=False)))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish,"scan":scan}[sys.argv[1]](Path(sys.argv[2]).resolve())
