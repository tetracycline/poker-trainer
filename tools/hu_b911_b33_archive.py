"""B911: archive completed B910 roots, repair only failed source pin, triage historical audit-only runs.
No native solver dispatch or ref update. Positive preflight never certifies.
"""
import base64,hashlib,io,json,os,sys,zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
BASE="f9d3f7a6e5db1646c6a2da065dcfdb57dc706d95"
RUN=45968453270
AUDIT=45968453045
PREFIX="data/solver_evidence/b911_b910_b33/"
PINS={
"8h7h5c":(15183647783,140402722780,"480368a76d24d9056bd55119af1965291370b98d6f9fdb4d0c15406ee93fd773"),
"7d5c4c":(15183588499,140402723180,"59b2735b49a7217adcf7197bc922deda13dda201bff146a10ed741bc5c148f97"),
}
def dump(p,x):p.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def prepare(out):
    h=guard();cov=coverage();out.mkdir(parents=True,exist_ok=False)
    r=api("/actions/runs/"+str(RUN));audit=api("/actions/runs/"+str(AUDIT))
    assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(BASE,BRANCH,"completed","failure")
    assert (audit["head_sha"],audit["head_branch"],audit["status"],audit["conclusion"])==(BASE,BRANCH,"completed","success")
    fail=api("/actions/jobs/140402723240")
    assert (fail["run_id"],fail["head_sha"],fail["name"],fail["status"],fail["conclusion"])==(RUN,BASE,"root-screen (5h4h3s)","completed","failure")
    root=Path(PREFIX);root.mkdir(parents=True,exist_ok=False);receipt={}
    for flop,(aid,jid,d) in PINS.items():
        a=api("/actions/artifacts/"+str(aid));j=api("/actions/jobs/"+str(jid))
        assert (a["name"],a["digest"],a["expired"])==("B910-b33-root-"+flop,"sha256:"+d,False)
        assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"],a["workflow_run"]["head_branch"])==(RUN,BASE,BRANCH)
        assert (j["run_id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(RUN,BASE,"root-screen ("+flop+")","completed","success")
        raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True);assert sha(raw)==d
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            rb=z.read("report.json");p=json.loads(rb)
            assert sha(z.read("routes.json"))==p["routes_sha256"]
        assert p["flop"]==flop and p["coverage"]==cov and set(p["identities"])=={"gto","exp_ip"}
        assert all(p[k]==0 for k in ("native_solves","cert_promotions","formal_lock_additions","formal_nonpolarized_additions"))
        assert {x["rank"] for x in p["rows"]}=={"106","107"}
        assert all(x["status"]=="NO_COMMON_FLOP_OR_CLASS_ROUTE_PAIR_ON_THIS_ROOT" and x["common_flop_pairs"]==0 and not x["possible_turns"] and not x["cert_eligible"] and not x["can_dispatch_native"] for x in p["rows"])
        (root/(flop+".zip")).write_bytes(raw);(root/(flop+".json")).write_bytes(rb)
        receipt[flop]=dict(artifact=a,job=j)
    dump(root/"receipts.json",dict(run=r,audit=audit,failed_job=fail,coverage=cov,sources=receipt,scope="Two completed read-only zero-pair screens; third source failed identity check. Not a global rank exclusion."))
    dump(out/"prepared.json",dict(parent=h,coverage=cov,files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())},native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))
def publish(out):
    h=guard();p=json.loads((out/"prepared.json").read_bytes())
    assert p["parent"]==h and p["coverage"]==coverage() and not git("diff","--name-only")
    entries=[]
    for path,d in p["files"].items():
        assert path.startswith(PREFIX)
        raw=Path(path).read_bytes();assert sha(raw)==d
        expected=hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()
        actual=api("/git/blobs",dict(content=base64.b64encode(raw).decode(),encoding="base64"))["sha"]
        assert actual==expected
        entries.append(dict(path=path,mode="100644",type="blob",sha=actual))
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=entries))["sha"]
    c=api("/git/commits",dict(message="B911 archive two successful B910 b33 root screens; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=h,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))

def repair(out,solver):
    guard()
    import hu_b910_b33_root_screen as worker
    import hu_b906_btn_original_gate as original
    aid,jid,old=original.PINS["5h4h3s"]["gto"]
    new="63bbcdaa03624c3c37e3e3de35bdcb6ae1c50b12116d1423c5de5d2c34f36d58"
    assert aid==14792264343 and jid==137505625094 and old=="63bbcdaa03624c3c37e3e3de35bdcb6ae1c50b12116d1423c5de5d34f36d58"
    a=api("/actions/artifacts/"+str(aid));j=api("/actions/jobs/"+str(jid))
    assert (a["id"],a["name"],a["digest"],a["expired"])==(aid,"B524-R8-5h4h3s-gto","sha256:"+new,False)
    assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"],a["workflow_run"]["head_branch"])==(original.RUN,original.SOURCE,BRANCH)
    assert (j["run_id"],j["head_sha"],j["conclusion"])==(original.RUN,original.SOURCE,"success")
    original.PINS["5h4h3s"]["gto"]=(aid,jid,new)
    worker.BASE=BASE
    worker.main(out,solver,"5h4h3s")
    dump(out/"pin-correction.json",dict(artifact=aid,job=jid,old=old,verified=new,reason="Missing hex character in historical transcription; source and job unchanged.",native_solves=0))
def history(out):
    guard();cov=coverage();out.mkdir(parents=True,exist_ok=False)
    # Eliminate only demonstrably identical static audit workflows. Do not infer absence from artifact names.
    path=".github/workflows/nl2-hu-full-batch-audit.yml"
    auditsha="5bdfa177cd4f0edac118fa3a9f87affe81c62973"
    shellsha="a0c75c3acbe71ac8b504921f1aa44ef467bdcb92"
    assert git("rev-parse",BASE+":"+path)==auditsha
    assert git("rev-parse",BASE+":tools/hu_exact_batch_audit.sh")==shellsha
    rows={}
    for flop in ("8h7h3c","7h6h2c","9d7h4c"):
        p=Path("data/solver_evidence/b909_review_archive")/(flop+".json")
        history=json.loads(p.read_bytes())["history"]
        assert not history["clearance"]
        runs={r["id"]:(c["commit"],r) for c in history["commits"] for r in c["runs"]}
        reviewed=[];remaining=[]
        for u in history["unresolved"]:
            rid=u.get("run")
            if rid not in runs:
                remaining.append(u);continue
            commit,r=runs[rid]
            if r["path"]!=path or r["status"]!="completed":
                remaining.append(u);continue
            try:
                w=git("rev-parse",commit+":"+path)
                s=git("rev-parse",commit+":tools/hu_exact_batch_audit.sh")
            except Exception:
                remaining.append(u);continue
            if (w,s)!=(auditsha,shellsha):
                remaining.append(u);continue
            # A completed identical static workflow is not a native-job dispatch. Keep the source hashes.
            reviewed.append(dict(run=rid,commit=commit,workflow_blob=w,audit_script_blob=s,classification="STATIC_AUDIT_WORKFLOW_NO_NATIVE_DISPATCH"))
        assert len(reviewed)+len(remaining)==len(history["unresolved"])
        rows[flop]=dict(input_unresolved=len(history["unresolved"]),static_audit_records=reviewed,remaining=remaining,clearance=False,can_dispatch_native=False,original_review_sha256=sha(p.read_bytes()))
    dump(out/"triage.json",dict(coverage=cov,rows=rows,scope="Exact static workflow and shell hashes only; no claim that unnamed/expired native sources are cleared. Remaining entries need actual job geometry review.",native_solves=0,cert_promotions=0))
    print(json.dumps({f:dict(before=v["input_unresolved"],classified=len(v["static_audit_records"]),remaining=len(v["remaining"])) for f,v in rows.items()}))
if __name__=="__main__":
    action=sys.argv[1];out=Path(sys.argv[2]).resolve()
    if action=="repair":repair(out,Path(sys.argv[3]).resolve())
    else:{"prepare":prepare,"publish":publish,"history":history}[action](out)
