"""B931: bound two original failed aggregates by successful native matrix receipts; never re-solve."""
import ast,base64,hashlib,json,os,sys,traceback,subprocess
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from itertools import combinations
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump,index_runs,rank_signature
BASE="326101418cc0270803acac3249ab8fd94f11f1f3"
PRIOR=Path("data/solver_evidence/b930_barrel_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b931_original_matrix_scope")
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
REPLAY=Path("data/solver_evidence/b925_publication_scope/run-scope.json")
SELECT={
45151346575:("7b31aa925fdb8747370595ae970bf7c5f82d10f8","365e02ddd86b56d67c6b3720a02f2ac194bbe819","b592_iso","b592_iso_turns","b8789b854118887e8d2b206c19842c98389e36a9","5f6c7a26bfc8da6102787361cf34fb5fc914940e",124),
45174797088:("6e305c61b113b36b54cba8fbaee404f57b3b1d69","eb14fcbe644cc53730371c728316342ebc69ff84","b598_stab","b598_stab_turns","89dd490b8050f2020f4d3d094f75418cf53b7bb2","3a6953559748d1f3c707fb95b8af9c08bff66956",133),
}
def historical(head,path):
    return subprocess.check_output(["git","show",head+":"+str(path)])
def logs_for(j,head):
    raw=api("/actions/jobs/"+str(j["id"])+"/logs",raw=True)
    lines=raw.decode("utf-8").splitlines()
    checkouts=[lines[i+1] for i,l in enumerate(lines[:-1]) if "git log -1 --format=%H" in l]
    assert [x.split()[-1] for x in checkouts]==[head,SOLVER]
    return raw,lines,checkouts
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def blob(head,path):return git("rev-parse",head+":"+str(path))

def prove(item,row,inv,targets):
    rid=item["run"]
    head,wf,stem,worker,workerpin,inputpin,rank=SELECT[rid]
    assert (row["run"],row["head"],row["workflow_blob"])==(rid,head,wf)
    assert blob(head,row["workflow"])==wf
    assert blob(BASE,REPLAY)=="6b957be8c12c0365017aabf93a9fc4e31a621a37"
    prior=[x for x in read(REPLAY)["closed_run_scopes"] if x["prior_native_run"]==rid]
    assert prior and all(x["prior_native_jobs"]==prior[0]["prior_native_jobs"] and x["original_run_failure"]==prior[0]["original_run_failure"] for x in prior)
    proof=prior[0]; orig=proof["original_run_failure"]
    assert proof["prior_native_head"]==head and orig["run"]==rid and orig["conclusion"]=="failure"
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(head,BRANCH,row["workflow"],"completed","failure")
    response=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
    js=response["jobs"]
    assert response["total_count"]==len(js)==len(row["jobs"])==len(proof["prior_native_jobs"])+1
    assert {(j["id"],j["name"],j["conclusion"]) for j in js}=={(j["id"],j["name"],j["conclusion"]) for j in row["jobs"]}
    assert all(j["head_sha"]==head and j["status"]=="completed" for j in js)
    vf,=[j for j in js if j["id"]==orig["verify_job"]]
    assert vf["name"]=="verify" and vf["conclusion"]=="failure"
    assert any(s["name"]=="Run actions/upload-artifact@v4" and s["conclusion"]=="skipped" for s in vf["steps"])
    failure=api("/actions/jobs/"+str(vf["id"])+"/logs",raw=True)
    assert sha(failure)==orig["verify_log_sha256"] and orig["failure_marker"] in failure.decode("utf-8")
    ipath=f"data/nl2_hu_{stem}_inputs.json"
    wpath=f"tools/hu_{worker}.py"
    pins={ipath:inputpin,wpath:workerpin}
    if rank==133:pins["tools/hu_checked_stab_turns.py"]="c29258118514ec9a291f1de4538089755cd0fa7e"
    for path,pin in pins.items():assert blob(head,path)==pin
    specs=json.loads(historical(head,ipath))
    assert len(specs)==len(proof["prior_native_jobs"]) and {x["flop"] for x in specs}=={x["flop"] for x in proof["prior_native_jobs"]}
    tr={rank_signature(x["candidate"]["flop"]) for x in targets.values()}
    assert not {rank_signature(x["flop"]) for x in specs}&tr
    receipts=[]
    for spec in specs:
        flop=spec["flop"]; turn=spec["turn"]
        q,=[x for x in proof["prior_native_jobs"] if x["flop"]==flop]
        j,=[j for j in js if j["id"]==q["job_id"]]
        assert j["name"]==f"reproduce ({flop})" and j["conclusion"]=="success" and j["id"] in orig["successful_reproduction_job_ids"]
        steps={s["name"]:s["conclusion"] for s in j["steps"]}
        assert steps["Build the pinned native engine"]==steps["Re-solve the complete native flop and both turn policies"]=="success"
        raw,lines,checkouts=logs_for(j,head)
        assert any(f"python {wpath} --solver ../solver --reproduce-flop {flop}" in l for l in lines)
        assert blob(head,q["path"])==q["blob"]
        archive=historical(head,q["path"])
        assert sha(archive)==spec["sha256"]
        pairs=[]
        with ZipFile(BytesIO(archive)) as z:
            assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
            for jobname,resultname in [("root.job.json","root.json"),("gto.job.json","gto.json"),("lock.job.json","native.json")]:
                jb=z.read(jobname);rb=z.read(resultname)
                job=json.loads(jb);result=json.loads(rb)
                assert job["out"]==resultname and job["flop"]==result["flop"]==flop
                assert (job["pot"],job["stack"])==(result["pot"],result["stack"])
                if jobname!="root.job.json":
                    assert job["turn"]==turn and turn in spec["root_turns"]
                pairs.append(dict(job=jobname,result=resultname,job_sha256=sha(jb),result_sha256=sha(rb),flop=flop,turn=job.get("turn"),pot=result["pot"],stack=result["stack"]))
        receipts.append(dict(flop=flop,turn=turn,job_id=j["id"],archive=q,archive_sha256=sha(archive),log_sha256=sha(raw),checkout_log_lines=checkouts,native_pairs=pairs))
    artifacts=api("/actions/runs/"+str(rid)+"/artifacts?per_page=100")
    assert artifacts["total_count"]==0 and not row["artifacts"]
    return dict(ledger=item,run=rid,head=head,workflow=row["workflow"],workflow_blob=wf,pins=pins,native_cases=receipts,original_run_failure=orig,prior_publication_runs=[x["run"] for x in prior],category="FAILED_AGGREGATE_SUCCESSFUL_NATIVE_MATRIX_DISJOINT_FLOP_RANKS")
def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="a4813fda7858b1ff270e45dd90ab162e2e50138b"
    p=read(PRIOR);inv=read(INV);byid=index_runs(inv)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==18
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    assert set(SELECT)<=set(x.get("run") for x in p["remaining"])
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item.get("run")
        if rid not in SELECT:remaining.append(item);continue
        try:closed.append(prove(item,byid[rid],inv,p["targets"]))
        except Exception as e:remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800],traceback=traceback.format_exc(limit=4)[-2200:]))
    assert len(closed)+len(blocked)==2 and len(closed)+len(remaining)==18
    groups={}
    for item in remaining:
        if "run" in item:
            row=byid[item["run"]]
            groups.setdefault(row["workflow_blob"],dict(path=row["workflow"],runs=[]))["runs"].append(item["run"])
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=closed,remaining=remaining,blocked_selected=blocked,grouped_original_run_scopes=groups,original_native_denylist=p["original_native_denylist"],targets=p["targets"],global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="Two failed historical aggregate scopes; all eight native matrix reproductions succeeded, authenticate their actual fixed flop and original bytes; retain failed downstream receipt, no certification.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:
        PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=2,closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,clearance=False)))
def publish(out):
    h=guard();p=read(out/"run-scope.json")
    assert p["parent"]==h and p["coverage"]==coverage() and not git("diff","--name-only")
    if not p["closed_run_scopes"]:
        print("No newly proven scope; no candidate created.");return
    path=PREFIX/"run-scope.json";b=path.read_bytes()
    assert b==(out/"run-scope.json").read_bytes()
    expected=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
    actual=api("/git/blobs",dict(content=base64.b64encode(b).decode(),encoding="base64"))["sha"]
    assert actual==expected
    entry=dict(path=str(path),mode="100644",type="blob",sha=actual)
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=[entry]))["sha"]
    c=api("/git/commits",dict(message="B931 archive audited disjoint historical original native matrix scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_run_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
