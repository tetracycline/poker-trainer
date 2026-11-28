"""B936: prove four historical B484 reconciliation-only run scopes with version-specific assembler pins. Never invoke solver or move refs."""
import base64,hashlib,json,os,sys,traceback,re
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump

BASE="f388ef712d706d52264ad4ba01ffa894ebffad22"
PRIOR=Path("data/solver_evidence/b935_registry_only_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b936_registry_only_scope")
WF=".github/workflows/nl2-hu-b484-two-seat-registry.yml"
WF_SHA="fbbdfd4fbcf185a6068c349828c7390e6856f391"
SELECT={
 45174796805:("6e305c61b113b36b54cba8fbaee404f57b3b1d69",137693156976,"a72af7d"),
 45151346459:("7b31aa925fdb8747370595ae970bf7c5f82d10f8",137613223162,None),
}
PINS={
 "tools/hu_apply_cert_extensions.py":"c73452c131d268e0d2b64ffb1565f0d06f186c33",
 "tools/hu_board_reach_corrections.py":"002b20cedf32ef43bf0bbd1cf1ae2c7d0bec666a",
 "tools/hu_b491_incremental_medium.py":"e7833967337c33c6202bd550dd0202bdd1ab4b50",
 "tools/hu_b491_incremental_medium.cjs":"b2be7896961249c12ea685db225905ae2514b525",
 "tools/hu_b483_lock_medium_ui.cjs":"85b4c082272f0f1cef657c7f76e3b158746d3dc0",
 "tools/hu_b485_medium_viewers.cjs":"58c2aa8b6666f42e500733ed247122fa24978efe",
 "tools/hu_extension_runtime_test.cjs":"c4b3b3a505a6c71537b6165002f43d4067990dcd",
 "tools/hu_exact_batch_audit.sh":"a0c75c3acbe71ac8b504921f1aa44ef467bdcb92",
 "tools/hu_publish_cert_extensions.sh":"1c8cfb2a52d4095b1f4081bb315e8bacd78ab0c3",
 "tools/hu_cert_lock_medium_audit.py":"0ae4fd85aaf9bece7edba83f059106ffbf95eb98",
 "tools/hu_b483_locked_medium.py":"018ac485d3fc115f125c777399d96ce38b0f5f04",
 "tools/hu_sequential_cfr_reach.py":"f26df926c088e5b4117bb911956cbc5031e2458d",
 "tools/hu_trainer_route_gate.py":"c58b3391a35b95563bb90a6bc898e0b4114f9486",
}
ASSEMBLER="tools/hu_apply_cert_extensions.py"
LEGACY_BLOB="d06f54c24b89e1a5a52dc4b05e15cf07706cae40"
LATER_BLOB=PINS[ASSEMBLER]
LEGACY_HEADS={"6e305c61b113b36b54cba8fbaee404f57b3b1d69","a72af7df23b03fc00494fb0c38fe7582080b1ef4","7b31aa925fdb8747370595ae970bf7c5f82d10f8"}
def verify_assembler_delta():
    # Both versions are immutable; the only reviewed difference moves the route
    # contract earlier and propagates its priced SPR into the registry/reference.
    old=git("cat-file","blob",LEGACY_BLOB)
    new=git("cat-file","blob",LATER_BLOB)
    route="    contract = rendered_contract(registry[\"records\"])\n"
    inserted="    contract = rendered_contract(registry[\"records\"])\n    for mid, route in contract[\"routes\"].items():\n        if \"priced_model_spr\" in route:\n            registry[\"records\"][mid][\"assumed_model_node_spr\"] = route[\"priced_model_spr\"]\n            refs[\"items\"][mid][\"model_node_spr\"] = route[\"priced_model_spr\"]\n"
    anchor='    ordered = sorted(loaded, key=lambda x: x["rank"])\n'
    assert old.count(route)==1 and old.count(anchor)==1
    assert old.replace(route,"").replace(anchor,inserted+anchor)==new

def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def blob(h,p):return git("rev-parse",h+":"+str(p))
def prove(item,row):
    rid=item["run"];head,jid,live=SELECT[rid]
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(head,BRANCH,WF,"completed","success")
    assert row["head"]==head and row["workflow_blob"]==WF_SHA and row["complete_listing"] and not row["artifacts"]
    assert blob(head,WF)==WF_SHA
    jobs=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
    assert jobs["total_count"]==len(jobs["jobs"])==len(row["jobs"])==1
    j,=jobs["jobs"]
    assert (j["id"],j["name"],j["head_sha"],j["conclusion"],j["status"])==(jid,"reconcile",head,"success","completed")
    assert [(s["name"],s["conclusion"]) for s in j["steps"]]==[(s["name"],s["conclusion"]) for s in row["jobs"][0]["steps"]]
    assert api("/actions/runs/"+str(rid)+"/artifacts?per_page=100")["total_count"]==0
    raw=api("/actions/jobs/"+str(jid)+"/logs",raw=True);log=raw.decode("utf-8",errors="strict")
    assert log.count("PASS exact source registry, GTO/locked archives and zero-reach rejection")==2
    assert log.count("2475/2475 HU routes")==2 and log.count("Everything up-to-date")==1
    # The historical publish step dynamically fetched the live branch; authenticate both
    # snapshots, not just the original checkout. Only registry replay/publish scope closes.
    assert "fix/nl2-hu-lines-audit-20261118 -> FETCH_HEAD" in log
    updates=re.findall(r"([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\s+fix/nl2-hu-lines-audit-20261118 -> origin/fix/nl2-hu-lines-audit-20261118",log)
    if live:
        assert len(updates)==1 and updates[0][0]==head[:len(updates[0][0])] and updates[0][1]==live
        live_head=git("rev-parse",live)
        git("merge-base","--is-ancestor",head,live_head)
    else:
        assert not updates
        live_head=head
    verified={}
    for h in {head,live_head}:
        actual={p:blob(h,p) for p in PINS}
        expected=dict(PINS)
        assert h in LEGACY_HEADS
        expected[ASSEMBLER]=LEGACY_BLOB
        assert actual==expected,(h,{p:v for p,v in actual.items() if expected[p]!=v})
        verified[h]=actual
    return dict(ledger=item,run=rid,head=head,live_publish_head=live_head,workflow_blob=WF_SHA,job=jid,
                job_log_sha256=sha(raw),pins=verified,category="REGISTRY_REPLAY_ONLY_NO_NATIVE_DISPATCH",original_artifacts=[])
def prepare(out):
    h=guard();cov=coverage();verify_assembler_delta()
    assert blob(h,PRIOR)=="a3b6708bf2588099ce26ce0735b6be5ca3c2da45"
    p=read(PRIOR);inv=read(INV)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==7
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    rows={x["run"]:x for x in inv["runs"]}
    assert set(SELECT)<={x.get("run") for x in p["remaining"]}
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item.get("run")
        if rid not in SELECT:remaining.append(item);continue
        try:closed.append(prove(item,rows[rid]))
        except Exception as e:
            remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:900],traceback=traceback.format_exc(limit=4)[-1800:]))
    assert len(closed)+len(blocked)==len(SELECT) and len(closed)+len(remaining)==7
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=closed,closed_artifact_scopes=[],remaining=remaining,
        blocked_selected=blocked,grouped_original_run_scopes=p["grouped_original_run_scopes"],original_native_denylist=p["original_native_denylist"],targets=p["targets"],
        global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,
        scope="B484 historical registry reconciliation/publish runs only. Version-specific assembler pin and exact delta verified. No original native job removed from denylist; all other runs still blocked.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:
        PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=len(SELECT),closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,clearance=False)))
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
    c=api("/git/commits",dict(message="B936 archive verified registry-only historical run scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_run_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
