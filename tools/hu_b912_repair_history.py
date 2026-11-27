"""B912: archive B911 repair/history receipts, clear only exact B904 read-only duplicate entries.
No native dispatch, certification, or branch mutation.
"""
import io,json,os,sys,zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
import hu_b911_b33_archive as publisher
import hu_b905_bb_archive_plan as prior

BASE="9b3a39c0d8e151a9fa104d7ce61fcc1091b5dc8a"
SOURCE="3b6ffd15dc1b14f996402a7f2bb307811534266c"
RUN=45977072367
PREFIX="data/solver_evidence/b912_repair_history/"
PINS={
    "repair":(15187237845,140431356724,"B911-repair-5h4h3s","40da96f12ccf53a50746db6d51e025fab733d31722cbdfe4ee75bffcd049ed6f","report.json"),
    "history":(15187547904,140431357141,"B911-history-triage","ac6ba56504931a1c52e4c0336491fda45a89bf927bd749882721048e34a71080","triage.json"),
}
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def dump(p,obj):p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
def prepare(out):
    h=guard();cov=coverage();out.mkdir(parents=True,exist_ok=False)
    rr=api("/actions/runs/"+str(RUN))
    assert (rr["head_sha"],rr["head_branch"],rr["status"],rr["conclusion"])==(SOURCE,BRANCH,"completed","success")
    root=Path(PREFIX);root.mkdir(parents=True,exist_ok=False)
    receipts={};objects={}
    for k,(aid,jid,name,d,member) in PINS.items():
        a=api("/actions/artifacts/"+str(aid));j=api("/actions/jobs/"+str(jid))
        assert (a["id"],a["name"],a["digest"],a["expired"])==(aid,name,"sha256:"+d,False)
        assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"],a["workflow_run"]["head_branch"])==(RUN,SOURCE,BRANCH)
        assert (j["id"],j["run_id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(jid,RUN,SOURCE,k,"completed","success")
        raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True);assert sha(raw)==d
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            rb=z.read(member);p=json.loads(rb)
            if k=="repair":
                assert sha(z.read("routes.json"))==p["routes_sha256"]
                pin=json.loads(z.read("pin-correction.json"))
                assert pin["artifact"]==14792264343 and pin["verified"]=="63bbcdaa03624c3c37e3e3de35bdcb6ae1c50b12116d1423c5de5d2c34f36d58"
                assert p["flop"]=="5h4h3s" and set(p["identities"])=={"gto","exp_ip"}
                assert {x["rank"] for x in p["rows"]}=={"106","107"}
                assert all(x["status"]=="NO_COMMON_FLOP_OR_CLASS_ROUTE_PAIR_ON_THIS_ROOT" and x["common_flop_pairs"]==0 and not x["possible_turns"] and not x["cert_eligible"] and not x["can_dispatch_native"] for x in p["rows"])
        assert p["coverage"]==cov and p["native_solves"]==p["cert_promotions"]==0
        (root/(k+".zip")).write_bytes(raw);(root/(k+".json")).write_bytes(rb);objects[k]=p
        receipts[k]=dict(artifact=a,job=j)
    tri=objects["history"]["rows"]
    counts={"8h7h3c":(9,5,4),"7h6h2c":(9,5,4),"9d7h4c":(90,11,79)}
    narrowed={}
    screenroot=Path(prior.PREFIX)
    recorded=json.loads((screenroot/"receipts.json").read_bytes())
    for flop,(before,classified,left) in counts.items():
        row=tri[flop]
        assert (row["input_unresolved"],len(row["static_audit_records"]),len(row["remaining"]))==(before,classified,left)
        assert not row["clearance"] and not row["can_dispatch_native"]
        original=Path("data/solver_evidence/b909_review_archive")/(flop+".json")
        assert sha(original.read_bytes())==row["original_review_sha256"]
        # Exactly the same B904 artifact and committed ZIP are duplicated in the
        # unresolved ledger. This ZIP contains only a non-native screen report.
        aid,d,jid,*_=prior.PINS[flop]
        rec=recorded["sources"][flop]
        assert rec["independent_byte_equal"] and rec["artifact"]["id"]==aid and rec["artifact"]["digest"]=="sha256:"+d
        assert rec["job"]["id"]==jid and rec["job"]["conclusion"]=="success"
        zp=screenroot/(flop+".zip");rp=screenroot/(flop+".json")
        raw=zp.read_bytes();assert sha(raw)==d
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None and z.namelist()==["screen.json"]
            assert z.read("screen.json")==rp.read_bytes()
        report=json.loads(rp.read_bytes())
        assert report["flop"]==flop and report["stage"]=="ROOT_UI_PREFLIGHT_ONLY" and report["native_solves"]==0 and report["cert_promotions"]==0
        cleared=[];remaining=[]
        for item in row["remaining"]:
            if item.get("artifact")==aid or item.get("path")==str(zp):
                cleared.append(item)
            else:remaining.append(item)
        assert len(cleared)==2 and any(x.get("artifact")==aid for x in cleared) and any(x.get("path")==str(zp) for x in cleared)
        narrowed[flop]=dict(before=left,classified=cleared,remaining=remaining,source_zip_sha256=d,source_report_sha256=sha(rp.read_bytes()),classification="EXACT_B904_READ_ONLY_SCREEN_DUPLICATE",clearance=False,can_dispatch_native=False)
    dump(root/"narrowed-history.json",dict(coverage=cov,rows=narrowed,scope="Only exact B904 screen duplicates removed; all remaining historical runs and sources stay blocked.",native_solves=0,cert_promotions=0))
    dump(root/"receipts.json",dict(run=rr,sources=receipts,coverage=cov))
    dump(out/"prepared.json",dict(parent=h,coverage=cov,files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())},native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))
    print(json.dumps({f:dict(before=x["before"],remaining=len(x["remaining"])) for f,x in narrowed.items()}))
if __name__=="__main__":
    action=sys.argv[1];out=Path(sys.argv[2]).resolve()
    if action=="prepare":prepare(out)
    else:
        # Existing detached-only publisher. Override only the current lease and prefix.
        publisher.guard=guard
        publisher.PREFIX=PREFIX
        publisher.publish(out)
