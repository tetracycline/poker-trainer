"""B932 authenticate historical flat worker archives; no native execution."""
import base64,hashlib,json,os,sys,traceback,subprocess
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump
from hu_b908_source_review import canonical
BASE="1b304b3507961463167add7425a588eb9b474ad8"
PRIOR=Path("data/solver_evidence/b931_original_matrix_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b932_flat_artifact_scope")
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
SELECT={
14729427685:(44960100932,"c62d41fb06c5200dcceca59df16a0e341066f5a6","623dc83a81cd57ca64962db97388590f2060dfda",137016788667,"CO_BB","gto","9s7h4d",["Ad"]),
14728889946:(44960924477,"88a62a4ce13c8ab5c10d89a32e2868060fd3f6cb","763cdd2d9fae7786d20e5cbfb1a7f3ad23e97399",137019381426,"CO_BB","exp_ip","9s7h4d",["Ad"]),
14789853217:(45112658221,"872f4a39509d8a94821fbc479cd614135671c651","d057872b1ea32f2b29d759ee78ceae1b0e2d4c47",137488292108,"UTG_CO","gto","9s7d4c",["7s","8d","As"]),
14790238349:(45112658221,"872f4a39509d8a94821fbc479cd614135671c651","d057872b1ea32f2b29d759ee78ceae1b0e2d4c47",137488292181,"UTG_CO","exp_ip","9s7d4c",["7s","8d","As"]),
}
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def blob(head,path):return git("rev-parse",head+":"+str(path))


def prove(item,inv,targets):
    aid=item["artifact"];rid,head,wf,jid,spot,variant,flop,turns=SELECT[aid]
    obs,=[o for o in inv["observations"] if o["source"]=="artifact:"+str(aid)]
    meta=api("/actions/artifacts/"+str(aid));pin=inv["artifact_metadata"][str(aid)]
    assert all(meta[k]==pin[k] for k in ("id","name","digest","workflow_run","size_in_bytes"))
    assert not meta["expired"] and meta["workflow_run"]["id"]==rid and meta["workflow_run"]["head_sha"]==head
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["status"],run["conclusion"])==(head,BRANCH,"completed","success")
    assert blob(head,run["path"])==wf
    job=api("/actions/jobs/"+str(jid))
    assert (job["run_id"],job["head_sha"],job["status"],job["conclusion"])==(rid,head,"completed","success")
    assert any("upload-artifact" in s["name"] and s["conclusion"]=="success" for s in job["steps"])
    raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True)
    assert sha(raw)==obs["sha256"]==meta["digest"].removeprefix("sha256:")
    prefix=f"solver/postflop/out/{spot}/{variant}/";pairs=[]
    targetsha={t["candidate"]["job_sha256"] for t in targets.values()}
    with ZipFile(BytesIO(raw)) as z:
        assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
        assert {m.filename:m.file_size for m in z.infolist()}=={m["name"]:m["size"] for m in obs["members"]}
        names=set(z.namelist());assert not any(n.endswith((".gz",".zip")) for n in names)
        jnames={n for n in names if n.endswith(".job.json")}
        assert len(jnames)==1+len(turns) and all(n.startswith(prefix) for n in jnames)
        assert {n for n in names if n.startswith(prefix)}==jnames|{n.removesuffix(".job.json")+".json" for n in jnames}
        for n in sorted(jnames):
            rn=n.removesuffix(".job.json")+".json";jb=z.read(n);rb=z.read(rn);j=json.loads(jb);res=json.loads(rb)
            assert j["flop"]==res["flop"]==flop and (j["pot"],j["stack"])==(res["pot"],res["stack"])
            t=j.get("turn") or None
            assert (res.get("turn") or None)==t
            if t:
                assert t in turns and canonical(flop,t) not in targets
            else:assert n.endswith("_multiboard.job.json")
            assert sha(jb) not in targetsha
            pairs.append(dict(job=n,result=rn,flop=flop,turn=t,canonical=canonical(flop,t),pot=j["pot"],stack=j["stack"],line0=j.get("line0"),job_sha256=sha(jb),result_sha256=sha(rb)))
        assert {x["turn"] for x in pairs}==set(turns)|{None}
        for suffix,expected in [("poker-solver-pin.txt",SOLVER),("rust-engine-pin.txt" if spot=="CO_BB" else "rust-pin.txt",RUST)]:
            n,=[n for n in names if n.endswith("/"+suffix)]
            assert z.read(n).decode().strip()==expected
    return dict(ledger=item,artifact=meta,run=rid,head=head,workflow=run["path"],workflow_blob=wf,job=jid,job_name=job["name"],archive_sha256=sha(raw),profile=spot,variant=variant,flop=flop,turns=turns,native_pairs=pairs,category="FLAT_NATIVE_ARCHIVE_FIXED_CHILD_IDENTITIES_NOT_TARGETS")
def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="b95732585aca5871925ec53151d2f9a6a921a0e2"
    p=read(PRIOR);inv=read(INV)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==16
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    assert set(SELECT)<={x.get("artifact") for x in p["remaining"]}
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        if item.get("artifact") not in SELECT:remaining.append(item);continue
        try:closed.append(prove(item,inv,p["targets"]))
        except Exception as e:
            remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800],traceback=traceback.format_exc(limit=4)[-2200:]))
    assert len(closed)+len(blocked)==len(SELECT) and len(closed)+len(remaining)==16
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=[],closed_artifact_scopes=closed,remaining=remaining,blocked_selected=blocked,grouped_original_run_scopes=p["grouped_original_run_scopes"],original_native_denylist=p["original_native_denylist"],targets=p["targets"],global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="Four flat native worker archives; fixed child identity closure only. Root jobs retained, no dispatch or promotion.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:
        PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=len(SELECT),closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,clearance=False)))
def publish(out):
    h=guard();p=read(out/"run-scope.json")
    assert p["parent"]==h and p["coverage"]==coverage() and not git("diff","--name-only")
    if not p["closed_artifact_scopes"]:
        print("No newly proven scope; no candidate created.");return
    path=PREFIX/"run-scope.json";b=path.read_bytes()
    assert b==(out/"run-scope.json").read_bytes()
    expected=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
    actual=api("/git/blobs",dict(content=base64.b64encode(b).decode(),encoding="base64"))["sha"]
    assert actual==expected
    entry=dict(path=str(path),mode="100644",type="blob",sha=actual)
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=[entry]))["sha"]
    c=api("/git/commits",dict(message="B932 archive verified flat native artifact scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_artifact_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
