"""B923: identify completed historical UI/inventory audits, not native solves.
Only exact pinned workflow and actual checked-out source; no ref update.
"""
import base64,hashlib,json,os,re,sys
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump,index_runs

BASE="7d8041499b3e36d93c7e7ecdf0920f2f13c8ef2c"
PRIOR=Path("data/solver_evidence/b922_static_checkout_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b923_static_checkout_scope")
H1="493988019bd1a93f2e970d8c8a2baf588695a002"
H2="e926ffadd56e49878f79088014274ad9a9334f00"
H3="872f4a39509d8a94821fbc479cd614135671c651"
H4="972be701de6e00e72e55b01e99d95d6234106aee"
FULL1="49e51eae6352cafb82c30e5dbafd34cdc25e0d81"
FULL2="4ed920912f00b1ce21edfd1e70208456f1d79150"
VIEW="05c6815c684b962fe639d7d023ecfcdc57a20c0c"
LEAD="829c4e66186c9e8fe6444e83d888c89833dfb31c"
SKIP="d1d4d08b9340057cd368aab7eafeabbcc9b35ea7"
COMMON={
"tools/hu_exact_batch_audit.sh":"01ce5bc29eef6b979110b72852d9a46632bb4233",
"tools/hu_b483_lock_medium_ui.cjs":"85b4c082272f0f1cef657c7f76e3b158746d3dc0",
"tools/hu_b485_medium_viewers.cjs":"58c2aa8b6666f42e500733ed247122fa24978efe",
}
FULL={**COMMON,
"tools/hu_b491_incremental_medium.py":"5be9ead01394aef8d911b0a09dae10c3acea177a",
"tools/hu_b491_incremental_medium.cjs":"65481854b32f3847c1266b87ee5dcc5b9fa58ed9",
"tools/hu_b492_medium_tree_ui.cjs":"1661b7fcae1b5c030df96940df47607ed2c682bc",
}
PINS={
FULL1:{**FULL,"tools/hu_apply_cert_extensions.py":"13fa49a8014891b8083590da2359a2eaa709b41d","tools/hu_extension_runtime_test.cjs":"713232bbb65eedadc1d497b2c899623e56d9eea5"},
FULL2:{**FULL,"tools/hu_apply_cert_extensions.py":"a5baeaa8ce3d7350bca0ececd158d9e90ec08877","tools/hu_extension_runtime_test.cjs":"a7b534e8a23cecbbe638fd8814a8bafa3061618a","tools/hu_current_medium_coverage.py":"3bf0a20db57f662645fcfa52dd5fd3a87f83b4a7"},
VIEW:{**COMMON,"tools/hu_apply_cert_extensions.py":"13fa49a8014891b8083590da2359a2eaa709b41d"},
LEAD:{"tools/hu_exact_batch_audit.sh":COMMON["tools/hu_exact_batch_audit.sh"],"tools/hu_b492_medium_tree_ui.cjs":FULL["tools/hu_b492_medium_tree_ui.cjs"]},
SKIP:{},
}
SELECT={
137488291892:(45112658123,H3,FULL1,"registry-and-routes"),
137512002024:(45120208652,H4,FULL2,"registry-and-routes"),
137488292237:(45112658110,H3,VIEW,"verify"),
137488291331:(45112658159,H3,LEAD,"verify"),
137887066662:(45230117586,H2,SKIP,"promote-audit-commit"),
137698321042:(45176302922,H1,SKIP,"promote-audit-commit"),
137488292496:(45112658136,H3,SKIP,"promote-audit-commit"),
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
    steps={x["name"]:x["conclusion"] for x in j["steps"]}
    if wf==SKIP:
        assert steps["Wait for both B365 and B367 original source proofs; never promote a partial pair"]=="success"
        skipped=["Build rank27 V48 only from three distinct exact GTO plus real NL2 OOP paired flops","Independent V48 source, node-lock, medium-size and schema audit","Full HU2475 river navigation, reach and model path audit","Commit and push V48 source promotion, node-lock matrix, medium evidence and full audit; never merge PR2"]
        assert all(steps.get(x)=="skipped" for x in skipped)
        assert any(re.search(r"Z Waiting for both source-proof commits; no status change\.",l) for l in lines), "no actual skip message"
    pins={}
    for path,digest in PINS[wf].items():
        assert blob(head,path)==digest,(path,head)
        pins[path]=digest
    # Pin also the exact UI sources used inside the read-only VM or extracted
    # validator; no source from current head is substituted.
    ui=["lines_data.js","nl2_rules.js","hwrange.js","nl2_reach.js","nl2_titles.js","nl2_hu_model.js","nl2.js"]
    ui+=["nl2_hu_multiboard_ui.js","nl2-multiboard.js","nl2.html","nl2-multiboard.html"]
    if wf==SKIP:ui=[]
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
        original_artifacts=artifacts,steps=steps,category=("PINNED_SOURCE_GATE_SKIPPED_NO_SOLVE" if wf==SKIP else "PINNED_HISTORICAL_STATIC_REPLAY_NO_NATIVE_SOLVER"))
def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="cbaee02dbb7b4c91e2fa016d5effcec5916fd7c9"
    p=read(PRIOR);inv=read(INV);byid=index_runs(inv)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==45
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    byrun={v[0]:(j,v) for j,v in SELECT.items()}
    assert len(byrun)==7 and set(byrun)<=set(x.get("run") for x in p["remaining"])
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item.get("run")
        if rid not in byrun:remaining.append(item);continue
        try:
            jid,expected=byrun[rid]
            closed.append(prove(item,byid[rid],inv,jid,expected))
        except Exception as e:
            remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800]))
    assert len(closed)+len(blocked)==7 and len(closed)+len(remaining)==45
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
        scope="Only four static and three skipped promotion run scopes, not all legacy artifact rows or native history. No global clearance.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:
        PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=7,closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,clearance=False)))
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
    c=api("/git/commits",dict(message="B923 archive audited static replay and skipped promotion run scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_run_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
