"""B928: exclude historical turn scopes only after authenticating the existing native artifacts; never execute a solver."""
import base64,hashlib,json,os,sys,traceback,subprocess
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump,index_runs,rank_signature
BASE="1fb06b38b9acc5ad6058a18190c7ec4048924999"
PRIOR=Path("data/solver_evidence/b927_rank58_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b928_turn_scope")
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
A="5d4cc240b6a8ccddd95a78915c45539f80db6d90"
B="493988019bd1a93f2e970d8c8a2baf588695a002"
HELPER={A:"824b787fc87d39d8c3f725a1ba53b5b9bcee8fee",B:"6da8742ef6220174ec4f6e5de03ebd5191ec1aea"}
B607=(607,198,"b607_checked_3bet_turns","b607_checked_3bet","7bac386ef5940024405d5af1bfce7b4a487ab3b7","7490b349210007be4c01c8789191c691ae6eb554","acfc44a70f5e4258d84a902832b3e8ade02b76b0")
B633=(633,56,"b633_rank56_iso","b633_iso","fd5c26ac77f9ecbbc2f095d50930196003931f8d","185e00d762752d12f6fbb75949b9656fc61c929a","0e63285c9199985d94ffeaa7c912871eba7e8cda")
B611=(611,67,"b611_iso_turns","b611_iso","c9759ca950a4a9253ed85397fcd167f6561d9889","c812246cf5badaa68f6d762416c6fbcdef487820","c0ffc998846aeb9987675b21fee6c867465e28e0")
SELECT={
45195896786:(A,B607,137767117956,14828906390,None,{"Th9s4h":137766119531,"JcTs6c":137766119920,"JhTd7h":137766119958,"Td9c6d":137766119987,"JdTc5d":137766120091}),
45176302852:(B,B607,137699071352,14819951374,None,{"JcTs6c":137698320812,"Td9c6d":137698321163,"JhTd7h":137698321166,"Th9s4h":137698321191,"JdTc5d":137698321488}),
45195896687:(A,B633,137769087898,14828956811,137766118569,{"7h5h2h":137766311175,"7c4c2c":137766311200,"8s4c2c":137766311259,"6d5h3h":137766311282,"8h6h3h":137766311540}),
45176302891:(B,B611,137700445009,14819578261,None,{"8s5h3d":137698321071,"9c6h4s":137698321706,"7h5h2h":137698321960}),
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
    head,spec,verify_id,aid,select_id,cases=SELECT[rid]
    batch,rank,entry,stem,wf,workerpin,inputpin=spec
    assert (row["run"],row["head"],row["workflow_blob"])==(rid,head,wf)
    assert blob(head,row["workflow"])==wf
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(head,BRANCH,row["workflow"],"completed","success")
    worker="tools/hu_"+entry+".py"
    inputpath="data/nl2_hu_"+stem+"_inputs.json"
    pins={worker:workerpin,inputpath:inputpin,"tools/hu_checked_stab_turns.py":HELPER[head]}
    for path,digest in pins.items():assert blob(head,path)==digest
    inputs=json.loads(historical(head,inputpath))
    byflop={x["flop"]:x for x in inputs}
    assert len(byflop)==len(inputs) and set(byflop)==set(cases)
    target_ranks={rank_signature(t["candidate"]["flop"]) for t in targets.values()}
    assert all(rank_signature(f) not in target_ranks for f in cases)
    response=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
    jobs={j["id"]:j for j in response["jobs"]}
    expected=set(cases.values())|{verify_id}|({select_id} if select_id else set())
    assert set(jobs)==expected and response["total_count"]==len(jobs)==len(row["jobs"])
    assert {j["id"] for j in row["jobs"]}==expected
    assert all((j["head_sha"],j["status"],j["conclusion"])==(head,"completed","success") for j in jobs.values())
    if select_id:
        j=jobs[select_id]
        assert j["name"]=="select"
        raw=api("/actions/jobs/"+str(select_id)+"/logs",raw=True)
        lines=raw.decode("utf-8").splitlines()
        checkouts=[lines[i+1] for i,l in enumerate(lines[:-1]) if "git log -1 --format=%H" in l]
        assert [x.split()[-1] for x in checkouts]==[head]
        assert any(inputpath in l and "jq" in l for l in lines)
        selection=dict(job_id=select_id,log_sha256=sha(raw),checkout_log_lines=checkouts)
    else:selection=None
    receipts=[]
    for flop,jid in cases.items():
        j=jobs[jid];assert j["name"]=="reproduce ("+flop+")"
        steps={s["name"]:s["conclusion"] for s in j["steps"]}
        assert steps["Build the pinned native engine"]=="success"
        assert steps["Re-solve the complete native flop and both turn policies"]=="success"
        raw,lines,checkouts=logs_for(j,head)
        assert any("python "+worker+" --solver ../solver --reproduce-flop "+flop in l for l in lines)
        path="data/solver_evidence/NL2_B"+str(batch)+"_R"+str(rank)+"_"+flop.upper()+".zip"
        b=historical(head,path)
        assert sha(b)==byflop[flop]["sha256"]
        pairs=[]
        with ZipFile(BytesIO(b)) as z:
            names=z.namelist();assert z.testzip() is None and len(set(names))==len(names)
            assert {n for n in names if n.endswith(".job.json")}=={"root.job.json","gto.job.json","lock.job.json"}
            for jname,rname in [("root.job.json","root.json"),("gto.job.json","gto.json"),("lock.job.json","native.json")]:
                jb=z.read(jname);rb=z.read(rname);job=json.loads(jb);result=json.loads(rb)
                assert job["flop"]==result["flop"]==flop and job["out"]==rname
                assert (job["pot"],job["stack"])==(result["pot"],result["stack"])
                if jname!="root.job.json":assert job["turn"]==byflop[flop]["turn"]
                pairs.append(dict(job=jname,result=rname,job_sha256=sha(jb),result_sha256=sha(rb),turn=job.get("turn")))
        receipts.append(dict(flop=flop,job_id=jid,archive_path=path,archive_blob=blob(head,path),archive_sha256=sha(b),job_result_pairs=pairs,log_sha256=sha(raw),checkout_log_lines=checkouts,steps=steps))
    j=jobs[verify_id];assert j["name"]=="verify"
    steps={s["name"]:s["conclusion"] for s in j["steps"]}
    assert steps["Check shared private hands, branch prices and existing certifications"]=="success"
    raw,lines,checkouts=logs_for(j,head)
    assert any("python "+worker+" --solver ../solver --run" in l for l in lines)
    assert not any("--reproduce-flop" in l for l in lines)
    assert any('cmp "$RUNNER_TEMP/report.json"' in l for l in lines)
    artifacts=api("/actions/runs/"+str(rid)+"/artifacts?per_page=100")
    assert artifacts["total_count"]==1 and {a["id"] for a in artifacts["artifacts"]}=={aid}==set(row["artifacts"])
    a,b=archive(aid,inv,rid,head)
    assert a["name"]=="B"+str(batch)+"-authenticated-rank"+str(rank)
    assert any("Artifact ID "+str(aid) in l for l in lines)
    assert any(a["digest"].split(":")[1] in l and "SHA256 digest of uploaded artifact" in l for l in lines)
    with ZipFile(BytesIO(b)) as z:
        assert z.testzip() is None
        groupname,=[n for n in z.namelist() if Path(n).name=="rank"+str(rank)+".json"]
        group=json.loads(z.read(groupname))
        assert group["rank"]==rank
        flops={x["flop"] for x in group["boards"]}
        assert flops and flops<=set(cases) and all(rank_signature(f) not in target_ranks for f in flops)
        publication=dict(job_id=verify_id,artifact_id=aid,artifact_sha256=sha(b),group_sha256=sha(z.read(groupname)),flops=sorted(flops),log_sha256=sha(raw),checkout_log_lines=checkouts,steps=steps)
    return dict(ledger=item,run=rid,head=head,workflow=row["workflow"],workflow_blob=wf,pins=pins,native_cases=receipts,selection=selection,publication=publication,category="PINNED_HISTORICAL_TURN_NATIVE_ARCHIVES_DISJOINT_FROM_SIX_TARGETS")
def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="747707b01038601f2abb2a1708654b223c2646db"
    p=read(PRIOR);inv=read(INV);byid=index_runs(inv)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==28
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    assert set(SELECT)<=set(x.get("run") for x in p["remaining"])
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item.get("run")
        if rid not in SELECT:remaining.append(item);continue
        try:closed.append(prove(item,byid[rid],inv,p["targets"]))
        except Exception as e:remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800],traceback=traceback.format_exc(limit=4)[-2200:]))
    assert len(closed)+len(blocked)==4 and len(closed)+len(remaining)==28
    groups={}
    for item in remaining:
        if "run" in item:
            row=byid[item["run"]]
            groups.setdefault(row["workflow_blob"],dict(path=row["workflow"],runs=[]))["runs"].append(item["run"])
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=closed,remaining=remaining,blocked_selected=blocked,grouped_original_run_scopes=groups,original_native_denylist=p["original_native_denylist"],targets=p["targets"],global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="Four historical turn reproduction runs; authenticate immutable committed native job/result pairs and existing successful publication receipts; exclude only disjoint flop rank multisets.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:
        PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=4,closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,clearance=False)))
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
    c=api("/git/commits",dict(message="B928 archive audited disjoint historical turn native scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_run_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
