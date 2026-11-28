"""B926: authenticate eight already reproduced native turn policies, without running a solver."""
import base64,hashlib,json,os,sys,traceback,ast
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump,index_runs

BASE="9ecda903f8b5b5f8168204e23e42cd42cb1b9cec"
PRIOR=Path("data/solver_evidence/b925_publication_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b926_barrel_scope")
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
HEAD="5d4cc240b6a8ccddd95a78915c45539f80db6d90"
HELPER="5a1a229e379b305f56a7199e6ccd06e5c3ea4824"
SELECT={
45195896696: (137766119281,628,19,"ln-3bp-3b_t_model-1gg0bw","e0d5f9fe94a883c8ec650e362c8ebc1745afcbcd","a10289f318090c0645eda1f7774fc079684692e9","80685d29889d376d03cbe2e97f349ec0f8ab00c9","37def147b4ec57362b299412c47eea252a7aaee5",("3d8h8s5s","3d7hAsJh","2d7hKs9d"),"three"),
45195896929: (137766119937,630,42,"ln-3bp-3b_t_model-1fvksvd","67e6b273a9ed845666431cbdbfea49a29054ac43","b6d6778f5ae090319cb10dc73b648476133ac77c","7099145c86a33a94819714408e0a3dfc0bcc2f6f","0369dd2965b110b9da480a53721ca9ec2b63ae50",("3d8h8s5s","3d6h9sTs","3dThKsTc","4d9hJsTs","4d8hAs8d"),"five"),
}
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def blob(head,path):return git("rev-parse",head+":"+str(path))

def historical_bytes(path):
    # The local Git object is pinned at the actual checkout, not today's file.
    import subprocess
    return subprocess.check_output(["git","show",HEAD+":"+str(path)])
def rank_signature(flop):
    assert len(flop)==6
    return tuple(sorted(flop[::2]))
def prove(item,row,targets):
    rid=item["run"]
    jid,batch,rank,model,wf,entry_sha,report_sha,archive_blob,boards,count=SELECT[rid]
    assert row["run"]==rid and row["head"]==HEAD and row["workflow_blob"]==wf==blob(HEAD,row["workflow"])
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(HEAD,BRANCH,row["workflow"],"completed","success")
    jobs=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
    assert jobs["total_count"]==len(jobs["jobs"])==len(row["jobs"])==1
    j,=jobs["jobs"]
    assert (j["id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(jid,HEAD,"verify","completed","success")
    assert row["jobs"][0]["id"]==jid and row["jobs"][0]["conclusion"]=="success"
    steps={s["name"]:s["conclusion"] for s in j["steps"]}
    assert steps["Build the original native solver"]=="success"
    assert steps[f"Authenticate all {count} original boards and reproduce the native policies"]=="success"
    logs=api("/actions/jobs/"+str(jid)+"/logs",raw=True)
    lines=logs.decode("utf-8").splitlines()
    checkouts=[lines[i+1] for i,l in enumerate(lines[:-1]) if "git log -1 --format=%H" in l]
    assert len(checkouts)==2 and [x.split()[-1] for x in checkouts]==[HEAD,SOLVER]
    entry=f"tools/hu_b{batch}_rank{rank}_barrels.py"
    report=f"data/nl2_hu_b{batch}_rank{rank}_barrels.json"
    archive=f"data/solver_evidence/NL2_B{batch}_R{rank}.zip"
    pins={entry:entry_sha,report:report_sha,archive:archive_blob,"tools/hu_b590_rank3_barrels.py":HELPER}
    for path,digest in pins.items():assert blob(HEAD,path)==digest
    assert any(f"python {entry} --solver ../solver --verification-driver " in l and f"--archive {archive}" in l for l in lines)
    assert any('cmp "$RUNNER_TEMP/replay.json" "$report"' in l for l in lines)
    assert not row["artifacts"]
    tree=ast.parse(historical_bytes(entry).decode())
    cases,=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CASES" for t in n.targets)]
    assert tuple(cases)==boards
    doc=json.loads(historical_bytes(report))
    assert doc["solver"]==SOLVER and tuple(x["public_board"] for x in doc["records"])==boards
    raw=historical_bytes(archive)
    assert sha(raw)==doc["archive_sha256"]
    target_ranks={rank_signature(t["candidate"]["flop"]) for t in targets.values()}
    native=[]
    with ZipFile(BytesIO(raw)) as z:
        assert len(z.namelist())==len(boards) and set(z.namelist())=={b+"/result.json" for b in boards}
        for record in doc["records"]:
            board=record["public_board"]
            aid,digest=cases[board]
            assert (record["rank"],record["model_id"],record["line"],record["seat"])==(rank,model,"b75 c/",0)
            assert (record["original"]["archive_id"],record["original"]["archive_sha256"])==(aid,digest)
            assert len(board)==8 and rank_signature(board[:6]) not in target_ranks
            assert sha(z.read(board+"/result.json"))==record["output_sha256"]
            assert len(record["job_sha256"])==len(record["root_sha256"])==64
            native.append({k:record[k] for k in ("public_board","rank","model_id","line","seat","root_sha256","job_sha256","output_sha256","original")})
    return dict(ledger=item,run=rid,head=HEAD,job_id=jid,workflow=row["workflow"],workflow_blob=wf,checkout_log_lines=checkouts,original_log_sha256=sha(logs),pins=pins,steps=steps,native_cases=native,archive_sha256=doc["archive_sha256"],category="PINNED_NATIVE_REPRODUCTION_BOARD_RANK_DISJOINT_FROM_SIX_TARGETS")
def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="6b957be8c12c0365017aabf93a9fc4e31a621a37"
    p=read(PRIOR);inv=read(INV);byid=index_runs(inv)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==33
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    assert set(SELECT)<=set(x.get("run") for x in p["remaining"])
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item.get("run")
        if rid not in SELECT:remaining.append(item);continue
        try:closed.append(prove(item,byid[rid],p["targets"]))
        except Exception as e:remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800],traceback=traceback.format_exc(limit=4)[-2200:]))
    assert len(closed)+len(blocked)==2 and len(closed)+len(remaining)==33
    groups={}
    for item in remaining:
        if "run" in item:
            row=byid[item["run"]]
            groups.setdefault(row["workflow_blob"],dict(path=row["workflow"],runs=[]))["runs"].append(item["run"])
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=closed,remaining=remaining,blocked_selected=blocked,grouped_original_run_scopes=groups,original_native_denylist=p["original_native_denylist"],targets=p["targets"],global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="Two pinned native reproduction runs, eight already solved turn policies, all flop rank signatures disjoint from six targets. No global clearance.")
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
    c=api("/git/commits",dict(message="B926 archive two audited disjoint historical native barrel scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_run_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
