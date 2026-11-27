"""B924: authenticate five prior publication-only replays, never run native jobs."""
import base64,hashlib,json,os,sys
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump,index_runs

BASE="727ac15b141252b0ec58133e98314a5e997d2842"
PRIOR=Path("data/solver_evidence/b923_static_checkout_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b924_publication_scope")
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
A="5d4cc240b6a8ccddd95a78915c45539f80db6d90"
B="493988019bd1a93f2e970d8c8a2baf588695a002"
C="6e305c61b113b36b54cba8fbaee404f57b3b1d69"
PINS={
 A:("824b787fc87d39d8c3f725a1ba53b5b9bcee8fee","3ee7436401e795a90723181be6fed150c43543d5"),
 B:("6da8742ef6220174ec4f6e5de03ebd5191ec1aea","4b841604d9e41a20424d2f968ca39ed116c340bb"),
 C:("c29258118514ec9a291f1de4538089755cd0fa7e","c973c38e3cc8d6f531ef56164a004adc1287f531"),
}
ISO=("9ebf88c469c0ba335e687eb379e61b07bf9fae23","b592_iso_turns","b592_iso", "8700567be95340fa149a7087852f00bc1c32004a",45151346575,"7b31aa925fdb8747370595ae970bf7c5f82d10f8",124,("9c6h4s","8s5h3d","7h5h2h"),(137613223556,137613224143,137613224383))
STAB=("4caada5f53e1106b6f44b0c762081296a76b262a","b598_stab_turns","b598_stab","89dd490b8050f2020f4d3d094f75418cf53b7bb2",45174797088,C,133,("JsJc4d","Jc7c4c","Qd8d3d","8h6h2h","9s6h3d"),(137693158155,137693158506,137693158553,137693158781,137693159083))
SELECT={
45195896498:(137766117601,A,ISO),45176302897:(137698320892,B,ISO),45174796877:(137693157863,C,ISO),
45195896537:(137766121827,A,STAB),45176302776:(137698320631,B,STAB),
}
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def blob(head,path):return git("rev-parse",head+":"+str(path))
def prove(item,row):
    rid=item["run"];jid,head,spec=SELECT[rid]
    wf,entry,stem,entry_sha,origin,origin_head,rank,flops,jobids=spec
    assert row["run"]==rid and row["head"]==head and row["workflow_blob"]==wf==blob(head,row["workflow"])
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(head,BRANCH,row["workflow"],"completed","success")
    jobs=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
    assert jobs["total_count"]==len(jobs["jobs"])==len(row["jobs"])==1
    j,=jobs["jobs"]
    assert (j["id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(jid,head,"publication","completed","success")
    assert row["jobs"][0]["id"]==jid and row["jobs"][0]["conclusion"]=="success"
    steps={x["name"]:x["conclusion"] for x in j["steps"]}
    assert steps["Match the archived jobs and solutions to each successful native run"]=="success"
    logs=api("/actions/jobs/"+str(jid)+"/logs",raw=True)
    lines=logs.decode("utf-8").splitlines()
    checkouts=[lines[i+1] for i,l in enumerate(lines[:-1]) if "git log -1 --format=%H" in l]
    assert len(checkouts)==2 and [x.split()[-1] for x in checkouts]==[head,SOLVER]
    command=f"python tools/hu_{entry}.py --solver ../solver --run {origin} --out"
    assert any(command in l for l in lines) and not any("--reproduce-flop" in l for l in lines)
    assert any('cmp "$RUNNER_TEMP/preview.json"' in l for l in lines)
    assert any("git diff --exit-code -- data" in l for l in lines)
    pins={"tools/hu_checked_stab_turns.py":PINS[head][0],"tools/hu_b592_iso_turn_routes.cjs":PINS[head][1],f"tools/hu_{entry}.py":entry_sha}
    for path,digest in pins.items():assert blob(head,path)==digest
    # No new native invocation: these workflows replay archived jobs only.
    # Their exact source native runs are deliberately left in the remaining ledger.
    orig=api("/actions/runs/"+str(origin))
    assert (orig["head_sha"],orig["head_branch"],orig["status"],orig["conclusion"])==(origin_head,BRANCH,"completed","success")
    inputpath=f"data/nl2_hu_{stem}_inputs.json"
    pins[inputpath]=blob(head,inputpath)
    assert pins[inputpath]==blob(origin_head,inputpath)
    native=[]
    for flop,jobid in zip(flops,jobids,strict=True):
        job=api("/actions/jobs/"+str(jobid))
        assert (job["run_id"],job["name"],job["conclusion"])==(origin,f"reproduce ({flop})","success")
        path=f"data/solver_evidence/NL2_{stem.split('_')[0].upper()}_R{rank}_{flop.upper()}.zip"
        digest=blob(head,path)
        assert digest==blob(origin_head,path)
        native.append(dict(flop=flop,job_id=jobid,path=path,blob=digest))
    assert not row["artifacts"]
    return dict(ledger=item,run=rid,head=head,job_id=jid,workflow=row["workflow"],workflow_blob=wf,checkout_log_lines=checkouts,original_log_sha256=sha(logs),pins=pins,steps=steps,prior_native_run=origin,prior_native_head=origin_head,prior_native_jobs=native,category="PINNED_PUBLICATION_REPLAY_NO_NEW_NATIVE_SOLVER")
def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="dc528f972a251531de55277c0094120eca7f2dcc"
    p=read(PRIOR);inv=read(INV);byid=index_runs(inv)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==38
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    assert set(SELECT)<=set(x.get("run") for x in p["remaining"])
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item.get("run")
        if rid not in SELECT:remaining.append(item);continue
        try:closed.append(prove(item,byid[rid]))
        except Exception as e:remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800]))
    assert len(closed)+len(blocked)==5 and len(closed)+len(remaining)==38
    groups={}
    for item in remaining:
        if "run" in item:
            row=byid[item["run"]]
            groups.setdefault(row["workflow_blob"],dict(path=row["workflow"],runs=[]))["runs"].append(item["run"])
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=closed,remaining=remaining,blocked_selected=blocked,grouped_original_run_scopes=groups,original_native_denylist=p["original_native_denylist"],targets=p["targets"],global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="Five publication-only replays; original native source runs remain unresolved. No global clearance.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:
        PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=5,closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,clearance=False)))
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
    c=api("/git/commits",dict(message="B924 archive audited historical turn publication replay scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_run_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
