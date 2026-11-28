"""B930: bound three completed barrel replay scopes by immutable native result bytes; never re-solve."""
import ast,base64,hashlib,json,os,sys,traceback,subprocess
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from itertools import combinations
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump,index_runs,rank_signature
BASE="3693046bae86c322e2a0b4c0f3c106f1ef84dbff"
PRIOR=Path("data/solver_evidence/b929_bb_river_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b930_barrel_scope")
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
SELECT={
45176303161:("493988019bd1a93f2e970d8c8a2baf588695a002",609,137698322452,"6486e790fa7744042d9b8c396186d5111407d46b","61856557953cb43d3a24f4674c354080c37673d5",[(6,"probe","70902129e6925be0b052ead1a57898432cc43331","b69e0f8523a161ed52ff73b9a867dfc481cc5b80")]),
45174796831:("6e305c61b113b36b54cba8fbaee404f57b3b1d69",596,137693157178,"8e31a7fbc4d46e6e099f7e8bcba3324ba6ee5226","2f271fb02785f8726ed3d841b2ffa1220b407d05",[(5,"delayed","1f57171ce04f48c42ddfade90072773dd5667350","5cb702a5a25f5e7a907c8865691660d5f131aa90")]),
45151346545:("7b31aa925fdb8747370595ae970bf7c5f82d10f8",594,137613223240,"7d603a4cdc6dde1afb9faa9ffb042274713c3277","a38e5e8bde4407c97a6130d366a22d7623bac993",[(2,"barrels","09be4af82a681d7deb13e103fbc5ed0499b137e5","a1c4a262b8e5954dcadb5b10ebedb591e6e5d432"),(4,"barrels","71b4e8f7edad4929183c7f866ff9d7752b1ca000","a542fc031fd34d64421dc22e9e2fc981771d7f66")]),
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
    head,batch,jid,wf,helper,groups=SELECT[rid]
    assert (row["run"],row["head"],row["workflow_blob"])==(rid,head,wf)
    assert blob(head,row["workflow"])==wf
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(head,BRANCH,row["workflow"],"completed","success")
    response=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
    assert response["total_count"]==len(response["jobs"])==len(row["jobs"])==1
    j=response["jobs"][0]
    assert (j["id"],j["name"],j["head_sha"],j["status"],j["conclusion"])==(jid,"verify",head,"completed","success")
    assert row["jobs"][0]["id"]==jid
    steps={s["name"]:s["conclusion"] for s in j["steps"]}
    n="six" if batch==594 else "five"
    assert steps["Build the original native solver"]==steps["Authenticate all "+n+" original boards and reproduce the native policies"]=="success"
    raw,lines,checkouts=logs_for(j,head)
    assert any('cmp "$RUNNER_TEMP/replay.json" "$report"' in l for l in lines)
    if batch==594:
        assert any('for rank in 2 4; do' in l for l in lines)
        assert any('python "tools/hu_b594_rank${rank}_barrels.py"' in l and '--verification-driver' in l for l in lines)
    else:
        assert any("python tools/hu_b"+str(batch)+"_rank" in l and "--verification-driver" in l for l in lines)
    assert blob(head,"tools/hu_b590_rank3_barrels.py")==helper
    registry=json.loads(historical(head,"data/nl2_hu_multiboard_status_current.json"))["records"]
    target_ranks={rank_signature(t["candidate"]["flop"]) for t in targets.values()}
    receipts=[]; pins={"tools/hu_b590_rank3_barrels.py":helper}
    for rank,suffix,workerpin,reportpin in groups:
        worker=f"tools/hu_b{batch}_rank{rank}_{suffix}.py"
        report=f"data/nl2_hu_b{batch}_rank{rank}_barrels.json"
        path=f"data/solver_evidence/NL2_B{batch}_R{rank}.zip"
        for p,pin in [(worker,workerpin),(report,reportpin)]:
            assert blob(head,p)==pin
            pins[p]=pin
        tree=ast.parse(historical(head,worker))
        assignment,=[x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CASES" for t in x.targets)]
        cases=ast.literal_eval(assignment.value)
        p=json.loads(historical(head,report));rows=p["records"]
        assert p["solver"]==SOLVER and len(rows)==len(cases)
        assert {r["public_board"] for r in rows}==set(cases)
        archive=historical(head,path)
        assert sha(archive)==p["archive_sha256"]
        with ZipFile(BytesIO(archive)) as z:
            assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
            assert set(z.namelist())=={b+"/result.json" for b in cases}
            for r in rows:
                public=r["public_board"];aid,digest=cases[public]
                assert r["rank"]==rank and r["original"]["archive_id"]==aid and r["original"]["archive_sha256"]==digest
                result_raw=z.read(public+"/result.json");result=json.loads(result_raw)
                assert sha(result_raw)==r["output_sha256"]
                flop=result["flop"];assert rank_signature(flop) not in target_ranks
                model=registry[r["model_id"]]
                assert model["frequency_rank"]==rank and model["label"]=="CERT-MULTIBOARD"
                board,=[b for b in model["certified_3_to_5_exact_flop_boards"] if b["public_board"]==public]
                assert board["flop"]==flop and board["source_sha256"]==r["original"]["source_sha256"]
                cards=[public[i:i+2] for i in range(0,len(public),2)]
                assert len(cards)==4 and len(set(cards))==4 and set(cards)=={flop[i:i+2] for i in (0,2,4)}|{board["turn"]}
                # Conservative: even any possible three-card subset must be disjoint.
                assert all(rank_signature("".join(c)) not in target_ranks for c in combinations(cards,3))
                assert (result["pot"]/100,result["stack"]/100)==(r["pot_bb"],r["stack_bb"])
                original=api("/actions/artifacts/"+str(aid))
                assert original["digest"]=="sha256:"+digest and original["workflow_run"]["id"]==r["original"]["run"]
                receipts.append(dict(rank=rank,flop=flop,turn=board["turn"],public_board=public,archive_path=path,archive_blob=blob(head,path),archive_sha256=sha(archive),result_sha256=sha(result_raw),reported_job_sha256=r["job_sha256"],root_sha256=r["root_sha256"],original=r["original"]))
    assert len(receipts)==(6 if batch==594 else 5)
    artifacts=api("/actions/runs/"+str(rid)+"/artifacts?per_page=100")
    assert artifacts["total_count"]==0 and not row["artifacts"]
    return dict(ledger=item,run=rid,head=head,workflow=row["workflow"],workflow_blob=wf,pins=pins,native_cases=receipts,job_id=jid,log_sha256=sha(raw),checkout_log_lines=checkouts,steps=steps,category="PINNED_COMPLETED_BARREL_REPLAY_DISJOINT_FROM_SIX_TARGETS")
def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="cb9fd588177c4a3bf74e903d9cdb64d2893e49e5"
    p=read(PRIOR);inv=read(INV);byid=index_runs(inv)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==21
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    assert set(SELECT)<=set(x.get("run") for x in p["remaining"])
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item.get("run")
        if rid not in SELECT:remaining.append(item);continue
        try:closed.append(prove(item,byid[rid],inv,p["targets"]))
        except Exception as e:remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800],traceback=traceback.format_exc(limit=4)[-2200:]))
    assert len(closed)+len(blocked)==3 and len(closed)+len(remaining)==21
    groups={}
    for item in remaining:
        if "run" in item:
            row=byid[item["run"]]
            groups.setdefault(row["workflow_blob"],dict(path=row["workflow"],runs=[]))["runs"].append(item["run"])
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=closed,remaining=remaining,blocked_selected=blocked,grouped_original_run_scopes=groups,original_native_denylist=p["original_native_denylist"],targets=p["targets"],global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="Three completed historical barrel replay scopes; verify pinned native result bytes, original receipt identities, registry and replay logs; exclude only disjoint flop rank multisets.")
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
    c=api("/git/commits",dict(message="B930 archive audited disjoint historical barrel replay scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_run_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
