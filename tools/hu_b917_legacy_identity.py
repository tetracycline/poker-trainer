"""B917: preserve B916, normalize legacy job/result schemas in the 75-row ledger.
No native invocation or ref mutation. Scope clearance is not global clearance.
"""
import io,json,os,sys,zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b908_source_review import canonical
import hu_b916_history_dedup as prior

BASE="a3532e96dd2abc348ee1ebcb1d4578be5396e2a9"
HEAD="7697e00b68330a141964c22d58fcdd3b9a9f3f3c"
RUN=46019825905
AUDIT=46019825925
JOB=140576269427
AID=15207398502
DIGEST="1bc773ec90f77f14bf850ce84b8713c74c2be94054c6886a0233292f77e09b13"
PREFIX=Path("data/solver_evidence/b917_legacy_identity")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
def read(p):return json.loads(Path(p).read_bytes())
def dump(p,x):Path(p).write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def scan_receipt():
    runs={str(i):api("/actions/runs/"+str(i)) for i in (RUN,AUDIT)}
    assert all((x["head_sha"],x["head_branch"],x["status"],x["conclusion"])==(HEAD,BRANCH,"completed","success") for x in runs.values())
    a=api("/actions/artifacts/"+str(AID));j=api("/actions/jobs/"+str(JOB))
    assert (a["name"],a["digest"],a["expired"],a["workflow_run"]["id"],a["workflow_run"]["head_sha"])==("B916-six-identity-scan","sha256:"+DIGEST,False,RUN,HEAD)
    assert (j["name"],j["status"],j["conclusion"],j["head_sha"],j["run_id"])==("identity-scan","completed","success",HEAD,RUN)
    b=api("/actions/artifacts/"+str(AID)+"/zip",raw=True);assert sha(b)==DIGEST
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        assert z.testzip() is None
        raw=z.read("scan.json");s=json.loads(raw)
    assert s["parent"]==HEAD and s["coverage"]==coverage() and len(s["targets"])==6
    assert s["tracked_archives"]==554 and len(s["sources"])==633 and not s["blocked"]
    assert not any(x["native_duplicate_candidates"] for x in s["targets"].values())
    assert sum(x["candidate"]["boundary_pass"] for x in s["targets"].values())==4
    assert not s["global_history_clearance"] and not s["can_dispatch_native"] and s["native_solves"]==s["cert_promotions"]==0
    return b,raw,s,dict(runs=runs,artifact=a,job=j)
def prepare(out):
    h=guard();cov=coverage();b,raw,s,receipt=scan_receipt()
    PREFIX.mkdir(parents=True,exist_ok=False);out.mkdir(parents=True,exist_ok=False)
    (PREFIX/"b916-scan.zip").write_bytes(b);(PREFIX/"b916-scan.json").write_bytes(raw)
    dump(PREFIX/"receipts.json",dict(receipt,coverage=cov,scope="B916 bounded scan; no global clearance"))
    dump(out/"prepared.json",dict(parent=h,coverage=cov,files={str(p):sha(p.read_bytes()) for p in sorted(PREFIX.iterdir())},native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))
def classify(out):
    h=guard();cov=coverage();_,_,s,_=scan_receipt()
    inv=read(INV);assert inv["coverage"]==cov and len(inv["remaining_input"])==75
    target={k:v["candidate"] for k,v in s["targets"].items()}
    targetsha={v["job_sha256"] for v in target.values()}
    src={x["source"]:x for x in inv["observations"]}
    allrows=[];remaining=[];closed=[]
    def analyze(raw,label,depth=0):
        report=dict(source=label,sha256=sha(raw),jobs=[],children=[],issues=[],candidate_hits=[])
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=set(z.namelist())
            if len(names)!=len(z.namelist()) or sum(x.file_size for x in z.infolist())>256*1024**2:
                report["issues"].append("archive budget or duplicate member");return report
            for n in sorted(names):
                if n.endswith(".zip"):
                    if depth>=2:report["issues"].append("depth limit");continue
                    report["children"].append(analyze(z.read(n),label+"!"+n,depth+1))
                if not n.endswith(".json"):continue
                b=z.read(n)
                try:q=json.loads(b)
                except (ValueError,UnicodeError):report["issues"].append("invalid JSON "+n);continue
                if not isinstance(q,dict):continue
                # Explicit job members, including older flat prefix.job.json.
                if n.rsplit("/",1)[-1]=="job.json":
                    base=n[:-len("job.json")]
                    options=[base+"result.json",base+"turn.json"]
                elif n.endswith(".job.json"):
                    options=[n[:-len(".job.json")]+".json"]
                else:
                    # Do not infer a native job from summary/result mentions.
                    continue
                matches=[x for x in options if x in names]
                f,t=q.get("flop"),q.get("turn");k=canonical(f,t)
                row=dict(member=n,job_sha256=sha(b),flop=f,turn=t,canonical=k,pot=q.get("pot"),stack=q.get("stack"),line0=q.get("line0"),result_members=matches)
                if len(matches)==1:
                    rb=z.read(matches[0]);res=json.loads(rb)
                    row["result_sha256"]=sha(rb)
                    row["result_matches_geometry"]=isinstance(res,dict) and all(res.get(a)==q.get(a) for a in ("flop","pot","stack"))
                    if isinstance(res,dict) and res.get("turn") is not None:row["result_matches_geometry"] &= res["turn"]==t
                else:row["result_matches_geometry"]=False
                valid_flop=isinstance(f,str) and len(f)==6 and all(f[i] in "23456789TJQKA" and f[i+1] in "cdhs" for i in (0,2,4)) and len({f[i:i+2] for i in (0,2,4)})==3
                row["geometry_inspectable"]=valid_flop and isinstance(q.get("pot"),int) and isinstance(q.get("stack"),int) and (t is None or k is not None)
                row["target_geometry"]=k in target and (q.get("pot"),q.get("stack"),q.get("line0"))==(1100,9475,["x","b50","c","/"])
                row["target_sha"]=row["job_sha256"] in targetsha
                if row["target_geometry"] or row["target_sha"]:report["candidate_hits"].append(row)
                report["jobs"].append(row)
        return report
    def flatten(x):
        yield x
        for c in x["children"]:yield from flatten(c)
    for item in inv["remaining_input"]:
        if "run" in item:remaining.append(item);continue
        label=item.get("path") or "artifact:"+str(item["artifact"])
        if "path" in item:b=Path(item["path"]).read_bytes()
        else:
            a=inv["artifact_metadata"][str(item["artifact"])]
            if a["expired"] or not a.get("digest"):remaining.append(item);continue
            b=api("/actions/artifacts/"+str(item["artifact"])+"/zip",raw=True)
            assert sha(b)==a["digest"].removeprefix("sha256:")
        assert sha(b)==src[label]["sha256"]
        rep=analyze(b,label);flat=list(flatten(rep))
        jobs=[j for x in flat for j in x["jobs"]]
        hits=[j for x in flat for j in x["candidate_hits"]]
        # Only known tracked legacy sources and the exact nested B620 copy may
        # close an individual ledger row; other generic artifacts need scope proof.
        expected_members={m["name"] for m in src[label]["members"]}
        with zipfile.ZipFile(io.BytesIO(b)) as z:assert expected_members==set(z.namelist())
        explicit="path" in item and Path(item["path"]).name.startswith(("NL2_B548_","NL2_B595_","NL2_B619_","NL2_B620_"))
        nested=item.get("artifact")==14819709671 and len(rep["children"])==1 and rep["children"][0]["sha256"]==src["data/solver_evidence/NL2_B620_R127_9H7S4D.zip"]["sha256"]
        eligible=(explicit or nested) and bool(jobs) and not hits and all(not x["issues"] for x in flat) and all(j["geometry_inspectable"] and j["result_matches_geometry"] for j in jobs)
        allrows.append(dict(ledger=item,report=rep,scope_closed=eligible,known_legacy_layout=bool(explicit or nested)))
        (closed if eligible else remaining).append(item)
    assert len(closed)+len(remaining)==75
    # Retain the full original denylist and candidate identities. No change to
    # the six continuations or authorisation, even if these local rows close.
    result=dict(parent=h,coverage=cov,closed=closed,remaining=remaining,source_rows=allrows,original_native_denylist=s["original_native_denylist"],targets=s["targets"],
        global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,
        scope="Legacy job/result geometry only; unresolved workflow scopes remain. No negative scan is proof of global absence.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"legacy.json",result)
    print(json.dumps(dict(closed=len(closed),remaining=len(remaining),explicit_sources=len(allrows),native_solves=0,cert_promotions=0,clearance=False)))
if __name__=="__main__":
    mode=sys.argv[1];out=Path(sys.argv[2]).resolve()
    if mode=="publish":
        prior.guard=guard;prior.PREFIX=PREFIX;prior.publish(out)
    else:{"prepare":prepare,"classify":classify}[mode](out)
