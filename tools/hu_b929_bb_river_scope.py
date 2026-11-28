"""B929: authenticate three historical BB river audit scopes without executing native jobs."""
import base64,hashlib,json,os,sys,traceback,subprocess
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump,index_runs,rank_signature
BASE="8e71f0111905cd277543a819f2a5b81c1631c5cd"
PRIOR=Path("data/solver_evidence/b928_turn_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b929_bb_river_scope")
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
A="6e305c61b113b36b54cba8fbaee404f57b3b1d69"
B="7b31aa925fdb8747370595ae970bf7c5f82d10f8"
W588="7338e0bcae175a8e514cf78e88104028f4f86356"
W597="9c5610aa74e6d12521f4f913f66530a4de46302d"
I588="439037777c57dd2ae3d64e4ad3384737c9667a56"
I597="df2c4a6d8520d839cfc28367ca13bf2ba31fa6f4"
HELPER={A:"8d2289753875dec951e2c00e8c55cc20d7e93c2c",B:"4fe090576a118120557e137500cdfd009e6006c1"}
SELECT={
  45174796787:(A,588,74,W588,I588,137693157077,14818482116,{"7s4d2c","8s5d3c","9h6c2h"}),
  45174796764:(A,597,72,W597,I597,137693157087,14818626970,{"7h6c3d","7s4d2c","8s5d3c"}),
  45151346608:(B,588,74,W588,I588,137613223231,14806437569,{"7s4d2c","8s5d3c","9h6c2h"}),
}
def historical(head,path):
    return subprocess.check_output(["git","show",head+":"+str(path)])
def logs_for(j,head):
    raw=api("/actions/jobs/"+str(j["id"])+"/logs",raw=True)
    lines=raw.decode("utf-8").splitlines()
    checkouts=[lines[i+1] for i,l in enumerate(lines[:-1]) if "git log -1 --format=%H" in l]
    assert [x.split()[-1] for x in checkouts]==[head,SOLVER]
    return raw,lines,checkouts
def archive(aid,inv,rid,head):
    pin=inv["artifact_metadata"][str(aid)]
    a=api("/actions/artifacts/"+str(aid))
    assert (a["id"],a["name"],a["digest"],a["expired"])==(aid,pin["name"],pin["digest"],False)
    assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"],a["workflow_run"]["repository_id"],a["workflow_run"]["head_branch"])==(rid,head,1438346845,BRANCH)
    raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True)
    assert "sha256:"+sha(raw)==a["digest"]
    return a,raw
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
    head,batch,rank,wf,inputpin,jid,aid,flops=SELECT[rid]
    assert (row["run"],row["head"],row["workflow_blob"])==(rid,head,wf)
    assert blob(head,row["workflow"])==wf
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(head,BRANCH,row["workflow"],"completed","success")
    worker="tools/hu_b588_bb_rivers.py"
    inputpath="data/nl2_hu_b"+str(batch)+"_bb_river_inputs.json"
    pins={worker:HELPER[head],inputpath:inputpin}
    for path,digest in pins.items():assert blob(head,path)==digest
    inputs=json.loads(historical(head,inputpath))
    assert set(inputs)=={str(rank)}
    entries=inputs[str(rank)]
    assert len(entries)==len(flops) and {s["flop"] for s in entries}==flops
    target_ranks={rank_signature(t["candidate"]["flop"]) for t in targets.values()}
    assert all(rank_signature(f) not in target_ranks for f in flops)
    response=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
    assert response["total_count"]==len(response["jobs"])==len(row["jobs"])==1
    j=response["jobs"][0]
    assert (j["id"],j["name"],j["head_sha"],j["status"],j["conclusion"])==(jid,"verify-audit",head,"completed","success")
    assert row["jobs"][0]["id"]==jid
    steps={s["name"]:s["conclusion"] for s in j["steps"]}
    assert steps["Rebuild both native job specifications and replay both private-hand policies"]=="success"
    assert steps["Verify the published viewer policies, node locks, medium sizes and all registry routes"]=="success"
    raw,lines,checkouts=logs_for(j,head)
    command="python "+worker+(" --batch 597" if batch==597 else "")+" --solver ../solver"
    assert any(command+' --out "$RUNNER_TEMP/preview.json"' in l for l in lines)
    assert any(command+' --run "$GITHUB_RUN_ID"' in l for l in lines)
    assert any("cmp " in l and "nl2_hu_b"+str(batch)+"_bb_river_preview.json" in l for l in lines)
    receipts=[]
    for spec in entries:
        flop=spec["flop"]
        path="data/solver_evidence/NL2_B"+str(batch)+"_R"+str(rank)+"_"+flop.upper()+".zip"
        b=historical(head,path)
        assert sha(b)==spec["archive_sha256"]
        pairs=[]
        with ZipFile(BytesIO(b)) as z:
            names=z.namelist()
            assert len(names)==len(set(names)) and z.testzip() is None
            assert set(names)=={"root.json","root.job.json","gto.json","gto.job.json","native.json","native.job.json","locks.json"}
            for jname,rname in [("root.job.json","root.json"),("gto.job.json","gto.json"),("native.job.json","native.json")]:
                jb=z.read(jname);rb=z.read(rname);job=json.loads(jb);result=json.loads(rb)
                assert job["flop"]==result["flop"]==flop and job["out"]==rname
                assert (job["pot"],job["stack"])==(result["pot"],result["stack"])
                assert (job["pot"],job["stack"])==((550,9750) if jname=="root.job.json" else (1100,9475))
                if jname!="root.job.json":assert job["turn"]==spec["turn"]
                pairs.append(dict(job=jname,result=rname,job_sha256=sha(jb),result_sha256=sha(rb),turn=job.get("turn")))
        receipts.append(dict(flop=flop,turn=spec["turn"],river=spec["river"],archive_path=path,archive_blob=blob(head,path),archive_sha256=sha(b),job_result_pairs=pairs))
    artifacts=api("/actions/runs/"+str(rid)+"/artifacts?per_page=100")
    assert artifacts["total_count"]==1 and {a["id"] for a in artifacts["artifacts"]}=={aid}==set(row["artifacts"])
    a,b=archive(aid,inv,rid,head)
    assert a["name"]=="B"+str(batch)+"-authenticated-BB-river-policies"
    assert any("Artifact ID "+str(aid) in l for l in lines)
    assert any(a["digest"].split(":")[1] in l and "SHA256 digest of uploaded artifact" in l for l in lines)
    with ZipFile(BytesIO(b)) as z:
        assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
        groupname,=[n for n in z.namelist() if Path(n).name=="rank"+str(rank)+".json"]
        group=json.loads(z.read(groupname))
        assert group["rank"]==rank
        published={x["flop"] for x in group["boards"]}
        assert published and published<=flops and all(rank_signature(f) not in target_ranks for f in published)
        publication=dict(job_id=jid,artifact_id=aid,artifact_sha256=sha(b),group_sha256=sha(z.read(groupname)),flops=sorted(published),log_sha256=sha(raw),checkout_log_lines=checkouts,steps=steps)
    return dict(ledger=item,run=rid,head=head,workflow=row["workflow"],workflow_blob=wf,pins=pins,native_cases=receipts,publication=publication,category="PINNED_BB_RIVER_ARCHIVES_AND_HISTORICAL_AUDIT_DISJOINT_FROM_SIX_TARGETS")

def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="b642819cc09d64707cb087c3a813fa86e0ca01c4"
    p=read(PRIOR);inv=read(INV);byid=index_runs(inv)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==24
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    assert set(SELECT)<=set(x.get("run") for x in p["remaining"])
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item.get("run")
        if rid not in SELECT:remaining.append(item);continue
        try:closed.append(prove(item,byid[rid],inv,p["targets"]))
        except Exception as e:remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800],traceback=traceback.format_exc(limit=4)[-2200:]))
    assert len(closed)+len(blocked)==3 and len(closed)+len(remaining)==24
    groups={}
    for item in remaining:
        if "run" in item:
            row=byid[item["run"]]
            groups.setdefault(row["workflow_blob"],dict(path=row["workflow"],runs=[]))["runs"].append(item["run"])
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=closed,remaining=remaining,blocked_selected=blocked,grouped_original_run_scopes=groups,original_native_denylist=p["original_native_denylist"],targets=p["targets"],global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="Three historical BB river audit runs; authenticate immutable committed native job/result pairs and existing successful publication receipts; exclude only disjoint flop rank multisets.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:
        PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=3,closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,clearance=False)))
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
    c=api("/git/commits",dict(message="B929 archive audited disjoint historical BB river scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_run_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
