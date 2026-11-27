"""B922: identify completed historical UI/inventory audits, not native solves.
Only exact pinned workflow and actual checked-out source; no ref update.
"""
import base64,hashlib,json,os,re,sys
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump,index_runs

BASE="be64afc2197f986fee364b58bcbfde2bdaa4b118"
PRIOR=Path("data/solver_evidence/b921_historical_worker_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b922_static_checkout_scope")
H1="493988019bd1a93f2e970d8c8a2baf588695a002"
H2="e926ffadd56e49878f79088014274ad9a9334f00"
H3="872f4a39509d8a94821fbc479cd614135671c651"
# Each workflow was inspected at the immutable event head. These workflows
# check existing browser UI/registry/route data, never invoke a native solver.
STAGE2="7c7807861d1504d13adb85a1c9c7e457cd0bfd8e"
INVENTORY="4a08dd02098fb0d7caebb30a6150d120316b145b"
STAGE3="bbd8b9a958b72220861f799b3eed88225902209b"
V47="88ad5854acb43a0dd00df5a25e4b16e5a1277fc6"
ROUTES={
"tools/link_audit.js":"f48e66acf5c3f466836ab4aeb36eb8df129cd82a",
"tools/hu_model_path_audit.js":"ebcabaa9c1f65a878cca09c554c699b1919d4e28",
}
PINS={
STAGE2:ROUTES,
STAGE3:ROUTES,
INVENTORY:{"tools/hu_cert_inventory.js":"430e31c6a329d207c2ddf3c5f8a5ddfa00250334"},
V47:{**ROUTES,"tools/hu_b378_v47_loader_runtime_test.cjs":"7809a3ee14b55f83fd60fedb837f5f166c76c40e",
"tools/hu_cert_lock_medium_audit.py":"0ae4fd85aaf9bece7edba83f059106ffbf95eb98",
"tools/hu_line_contract.js":"4128055d73d5ee9ae4398fdcc7579fcad01ef523",
"tools/reach_verify.js":"432bdb1b1582718bc93733106524383f5c10bf93"},
}
# Run, actual checked-out head (also seen in original checkout log), workflow,
# successful original job and expected job name.
SELECT={
137887071863:(45230117596,H2,STAGE3,"audit"),
137887064650:(45230117190,H2,V47,"strict-full-audit"),
137698321461:(45176302903,H1,STAGE2,"audit"),
137698321730:(45176302953,H1,INVENTORY,"inventory"),
137698320426:(45176302760,H1,STAGE3,"audit"),
137698321376:(45176303019,H1,V47,"strict-full-audit"),
137488291811:(45112658127,H3,STAGE3,"audit"),
137488291385:(45112658128,H3,V47,"strict-full-audit"),
}
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def blob(head,path):return git("rev-parse",head+":"+str(path))
def prove(item,row,inv,jid,expected):
    rid,head,wf,name=expected
    assert item["run"]==rid==row["run"] and row["head"]==head
    assert row["workflow_blob"]==wf==blob(head,row["workflow"])
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(head,BRANCH,row["workflow"],"completed","success")
    jobs=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
    assert jobs["total_count"]==len(jobs["jobs"])==len(row["jobs"])==1
    j,=jobs["jobs"]
    assert (j["id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(jid,head,name,"completed","success")
    assert (row["jobs"][0]["id"],row["jobs"][0]["name"],row["jobs"][0]["conclusion"])==(jid,name,"success")
    logs=api("/actions/jobs/"+str(jid)+"/logs",raw=True)
    lines=logs.decode("utf-8").splitlines()
    # These historical workflows checkout a branch name, not necessarily event
    # SHA; prove the actual checkout from the successful original job log.
    checkout=[lines[i+1] for i,l in enumerate(lines[:-1]) if "git log -1 --format=%H" in l]
    assert len(checkout)==1 and checkout[0].strip().endswith(" "+head),checkout
    pins={}
    for path,digest in PINS[wf].items():
        assert blob(head,path)==digest,(path,head)
        pins[path]=digest
    # Pin also the exact UI sources used inside the read-only VM or extracted
    # validator; no source from current head is substituted.
    ui=["lines_data.js","nl2_rules.js","hwrange.js","nl2_reach.js","nl2_titles.js","nl2_hu_model.js","nl2.js"]
    if wf==V47:ui+=["nl2_hu_multiboard_ui.js","nl2-multiboard.js","nl2.html","nl2-multiboard.html"]
    pins.update({path:blob(head,path) for path in ui})
    artifacts=[]
    for aid in row["artifacts"]:
        a=api("/actions/artifacts/"+str(aid))
        old=inv["artifact_metadata"][str(aid)]
        assert a["workflow_run"]["id"]==rid and a["workflow_run"]["head_sha"]==head
        assert a["digest"]==old["digest"] and a["name"]==old["name"]
        artifacts.append(a)
    return dict(ledger=item,run=rid,head=head,job_id=jid,workflow=row["workflow"],workflow_blob=wf,
        checkout_log_line=checkout[0],original_log_sha256=sha(logs),pins=pins,
        original_artifacts=artifacts,category="PINNED_HISTORICAL_UI_INVENTORY_AUDIT_NO_NATIVE_SOLVER")
def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="5886ac90287ae264bf5558324fb1f48728b7b24f"
    p=read(PRIOR);inv=read(INV);byid=index_runs(inv)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==53
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    byrun={v[0]:(j,v) for j,v in SELECT.items()}
    assert len(byrun)==8 and set(byrun)<=set(x.get("run") for x in p["remaining"])
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item.get("run")
        if rid not in byrun:remaining.append(item);continue
        try:
            jid,expected=byrun[rid]
            closed.append(prove(item,byid[rid],inv,jid,expected))
        except Exception as e:
            remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800]))
    assert len(closed)+len(blocked)==8 and len(closed)+len(remaining)==53
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
        scope="Only eight original static-run scopes, not all legacy artifact rows or native history. No global clearance.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:
        PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=8,closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,clearance=False)))
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
    c=api("/git/commits",dict(message="B922 archive audited original UI and inventory run scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_run_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
