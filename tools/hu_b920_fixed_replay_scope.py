"""B920: prove historical fixed native replay scopes without executing a solver.
Conservative full flop-rank multiset + turn-rank exclusion, plus exact job SHA.
No ref mutation. A scope proof is not a certification or global clearance.
"""
import ast,base64,hashlib,json,os,re,subprocess,sys
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump,index_runs,rank_signature

BASE="dedb0696b34f18f1a712b13eac0cdcde873d4096"
PRIOR=Path("data/solver_evidence/b918_run_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b920_fixed_replay_scope")
CORE="tools/hu_b590_rank3_barrels.py"
CORE_BLOB="8d8dd6e9fcfe1f81421d098b2de877bc8d004aac"
# Immutable worker and workflow versions reviewed, including the exact
# cases -> public board -> one fixed turn subgame loop in the shared worker.
GROUPS={
 "9c336d6ce27d451703cd94ad03d210137c8bc556":("590",CORE,CORE_BLOB,[3],"b75 c"),
 "c17453df6ce624402b5ac41f102d2a9845a69301":("632","tools/hu_b632_threebet_delayed.py","fdf064c14d31e7a9fa3937b544d0ceb476ff34df",[82,120,131],"x x"),
 "e3abc4aa8a2d222aa5a3fff7c8fd88a282e0f8fa":("640","tools/hu_b640_ip_turn_barrels.py","31965775b825d2b0a3846225e039361a90839ff6",[36,37,38,39,59,60,61],None),
 "7ad9121c523359d503e3cb8c4ee63b3e5cd27134":("638","tools/hu_b638_limped_turns.py","41d037f934c67ab13647c9f740caa0cd602f26ce",[1,7],None),
}
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def blob(head,path):
    return git("rev-parse",head+":"+str(path))
def raw(head,path):
    return subprocess.check_output(["git","show",head+":"+str(path)])
def literals(source,name):
    node,=[n for n in ast.parse(source).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name]
    return ast.literal_eval(node.value)
def board_key(public):
    assert isinstance(public,str) and len(public)==8
    assert public[6] in "23456789TJQKA" and public[7] in "cdhs"
    assert len({public[i:i+2] for i in (0,2,4,6)})==4
    return rank_signature(public[:6])+"/"+public[6]
def hex64(s):
    return isinstance(s,str) and re.fullmatch(r"[0-9a-f]{64}",s) is not None
def prove(item,row,targets):
    rid=item["run"];head=row["head"];wf=row["workflow"];wb=row["workflow_blob"]
    batch,worker,worker_blob,ranks,fixed=GROUPS[wb]
    assert blob(head,wf)==wb and blob(head,worker)==worker_blob and blob(head,CORE)==CORE_BLOB
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(head,BRANCH,wf,"completed","success")
    jobs=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
    assert jobs["total_count"]==len(jobs["jobs"])==len(row["jobs"])==1
    j,=jobs["jobs"]
    assert (j["id"],j["name"],j["conclusion"])==(row["jobs"][0]["id"],"verify","success")
    assert j["head_sha"]==head and j["status"]=="completed"
    steps=[x for x in j["steps"] if x["name"].startswith("Authenticate")]
    assert len(steps)==1 and steps[0]["conclusion"]=="success"
    target_keys={board_key(t["flop"]+t["turn"]) for t in targets}
    target_shas={t["job_sha256"] for t in targets}
    source=raw(head,worker).decode()
    if batch=="590":
        cases={3:(literals(source,"MODEL"),fixed,literals(source,"CASES"))}
    else:
        table=literals(source,"SOURCES")
        assert set(table)==set(ranks)
        cases={rank:(value[0],fixed,value[1]) if fixed else value for rank,value in table.items()}
    records=[]
    for rank in ranks:
        model,line,boards=cases[rank]
        report=f"data/nl2_hu_b{batch}_rank{rank}_barrels.json"
        archive=f"data/solver_evidence/NL2_B{batch}_R{rank}.zip"
        report_bytes=raw(head,report);d=json.loads(report_bytes)
        archive_bytes=raw(head,archive)
        assert sha(archive_bytes)==d["archive_sha256"]
        rs=d["records"]
        assert len(rs)==len(boards)==len({x["public_board"] for x in rs})
        assert set(x["public_board"] for x in rs)==set(boards)
        entries=[]
        for x in rs:
            public=x["public_board"];aid,digest=boards[public]
            p=x["original"]
            assert x["rank"]==rank and x["model_id"]==model and x["line"].startswith(line+"/")
            assert p.get("archive_id",p.get("archive_code"))==aid and p["archive_sha256"]==digest
            assert all(hex64(x[k]) for k in ("job_sha256","root_sha256","output_sha256"))
            key=board_key(public)
            assert key not in target_keys and x["job_sha256"] not in target_shas,(rank,public,key)
            entries.append(dict(public_board=public,rank_key=key,job_sha256=x["job_sha256"],
                root_sha256=x["root_sha256"],output_sha256=x["output_sha256"],line=x["line"],
                original=p,pot_bb=x["pot_bb"],stack_bb=x["stack_bb"],seat=x["seat"]))
        records.append(dict(rank=rank,report=report,report_blob=blob(head,report),report_sha256=sha(report_bytes),
            archive=archive,archive_blob=blob(head,archive),archive_sha256=d["archive_sha256"],entries=entries))
    return dict(ledger=item,run=rid,head=head,workflow=wf,workflow_blob=wb,worker=worker,
        worker_blob=worker_blob,core_blob=CORE_BLOB,job_id=j["id"],verified_step=steps[0],
        category="FIXED_REPLAY_ALL_TURN_RANK_KEYS_DISJOINT_AND_JOB_SHAS_DISJOINT",records=records,
        original_artifacts=row["artifacts"])
def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="b4320f2659b00694ac5c4c524bf77c9364c30f9c"
    p=read(PRIOR);inv=read(INV);byid=index_runs(inv)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==61
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    targets=[x["candidate"] for x in p["targets"].values()]
    assert len(targets)==6 and sum(t["boundary_pass"] for t in targets)==4
    selected={r for b,g in p["grouped_original_run_scopes"].items() if b in GROUPS for r in g["runs"]}
    assert len(selected)==8
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item.get("run")
        if rid not in selected:
            remaining.append(item);continue
        try:
            closed.append(prove(item,byid[rid],targets))
        except Exception as e:
            # Fail closed per run. Never promote an incomplete or mismatched record.
            blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800]))
            remaining.append(item)
    assert len(closed)+len(remaining)==len(p["remaining"])
    assert len(closed)+len(blocked)==len(selected)
    groups={}
    for item in remaining:
        if "run" in item:
            row=byid[item["run"]]
            groups.setdefault(row["workflow_blob"],dict(path=row["workflow"],runs=[]))["runs"].append(item["run"])
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=closed,
        remaining=remaining,blocked_selected=blocked,grouped_original_run_scopes=groups,
        original_native_denylist=p["original_native_denylist"],targets=p["targets"],
        global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,
        formal_lock_additions=0,formal_nonpolarized_additions=0,
        scope="Only these exact historical replay runs; same flop with a different turn rank is not the target fixed turn. No global clearance.")
    out.mkdir(parents=True,exist_ok=False)
    dump(out/"run-scope.json",report)
    if closed:
        PREFIX.mkdir(parents=True,exist_ok=False)
        dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=len(selected),closed=len(closed),remaining=len(remaining),
        blocked=blocked,coverage=cov,clearance=False)))
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
    c=api("/git/commits",dict(message="B920 archive audited fixed native replay scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_run_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
