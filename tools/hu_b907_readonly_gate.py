"""B907: repair failed evidence readers, never rerun native solves or authorize dispatch."""
import io,json,os,re,sys,zipfile
from pathlib import Path
import hu_b905_bb_archive_plan as bb
import hu_b906_btn_original_gate as btn
import hu_b895_archive_r158 as archive
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage

BASE="08082a78b781c80a7df83108dd5ba0f67296aaa9"
PREFIX="data/solver_evidence/b907_readonly_gate/"
FILES={"tools/hu_b907_readonly_gate.py",".github/workflows/nl2-hu-b907-readonly-gate.yml","docs/NL2_HU_B907_READONLY_GATE.md"}
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    assert set(git("diff","--name-only",BASE,h).splitlines())==FILES
    p=api("/pulls/2")
    assert p["state"]=="open" and p["draft"] and not p["merged"]
    assert (p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==(REPO,BRANCH,h)
    return h

def inventory(flop):
    # One pass, never poll. Live offset pagination can shift; keep observable
    # hits but record all anomalies and never certify historical clearance.
    vs=bb.variants(flop); pattern="|".join(vs)
    history=git("log","--format=%H%x09%s","--regexp-ignore-case","-G",pattern,BASE,"--",".github/workflows","tools").splitlines()
    paths=[p for p in git("ls-files","data/solver_evidence").splitlines() if any(v in re.sub(r"[^a-z0-9]","",p.lower()) for v in vs)]
    ids={}; counts=[]; duplicates=[]; conflicts=[]; exhausted=False
    for page in range(1,101):
        data=api("/actions/artifacts?per_page=100&page="+str(page))
        counts.append(data["total_count"])
        for a in data["artifacts"]:
            row={k:a.get(k) for k in ("id","name","expired","digest","workflow_run")}
            if a["id"] in ids:
                duplicates.append(a["id"])
                if ids[a["id"]]!=row:conflicts.append(a["id"])
            else:ids[a["id"]]=row
        if len(data["artifacts"])<100:
            exhausted=True
            break
    hits=[a for a in ids.values() if any(v in re.sub(r"[^a-z0-9]","",a["name"].lower()) for v in vs)]
    stable=exhausted and not duplicates and not conflicts and len(set(counts))==1 and len(ids)==counts[0]
    return dict(ancestor_dispatch_matches=history,tracked_named_source_paths=paths,artifact_name_matches=hits,artifact_metadata_rows=len(ids),historical_ref=BASE,clearance=False,offset_listing_stable=stable,listing_exhausted=exhausted,listing_counts=counts,duplicate_ids=sorted(set(duplicates)),conflicting_ids=sorted(set(conflicts)),limitations="Even a stable listing does not clear expired or unnamed sources; unstable pages are partial inventory only. No native dispatch.")

def prepare(out):
    h=guard();cov=coverage();out.mkdir(parents=True,exist_ok=False)
    root=Path(PREFIX);root.mkdir(parents=True,exist_ok=False)
    pins=[
      ("b905-plan-8h7h3c",15170588946,"147124f0c7a7072f07fcce685ed0f87de7ff07ad21ce7bd211da2eb4956860fb",45936923715,140302147614,"af5e067d61a1b2a1344aaa87fdd89545c30c3fff","B905-rank92-plan-8h7h3c","plan (8h7h3c)","plan.json"),
      ("b906-screen-7d5c4c",15172719100,"8b69a9eebab47c8c769f62be42d3dbf13e8bd5ec34cd40ced1a87f4e01337193",45943163497,140321815023,"2a60e8bf20506a4483e86185df8181c1515e15a4","B906-BTN-screen-7d5c4c","screen (7d5c4c)","report.json")]
    receipts={}
    for key,aid,digest,run,jid,head,name,jobname,member in pins:
        a=api("/actions/artifacts/"+str(aid));j=api("/actions/jobs/"+str(jid))
        assert (a["id"],a["name"],a["digest"],a["expired"])==(aid,name,"sha256:"+digest,False)
        assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"],a["workflow_run"]["head_branch"])==(run,head,BRANCH)
        assert (j["id"],j["run_id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(jid,run,head,jobname,"completed","success")
        raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True);assert sha(raw)==digest
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            rb=z.read(member);p=json.loads(rb)
            assert p["coverage"]==cov and all(p[k]==0 for k in ("native_solves","cert_promotions","formal_lock_additions","formal_nonpolarized_additions"))
            if member=="plan.json":
                assert p["flop"]=="8h7h3c" and not p["historical_inventory"]["clearance"]
                assert [x["turn"] for x in p["plans"]]==["2c","4c"]
                for x in p["plans"]:
                    assert not x["can_dispatch_native"] and sha(z.read(x["turn"]+"-gto-job.json"))==x["job_sha256"]
            else:
                assert p["flop"]=="7d5c4c" and len(p["rows"])==1
                row=p["rows"][0]
                assert row["turn"]=="8c" and row["rank104"]=="B75_NOT_IN_ORIGINAL_MENU" and row["rank105"]=="NO_COMMON_PHYSICAL_ROUTE_PAIR_BEFORE_RIVER"
                assert not row["possible_rivers"] and not row["cert_eligible"]
        (root/(key+".zip")).write_bytes(raw);(root/(key+".json")).write_bytes(rb)
        receipts[key]=dict(artifact=a,job=j)
    archive.dump(root/"receipts.json",dict(coverage=cov,sources=receipts,scope="Successful individual read-only jobs from mixed-result runs; no native or CERT clearance."))
    archive.dump(out/"prepared.json",dict(parent=h,files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())},coverage=cov,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))

def publish(out):
    # Same validated blob/tree/parent procedure as B895, but explicit B907 receipt.
    h=guard();p=archive.read(out/"prepared.json")
    assert p["parent"]==h and p["coverage"]==coverage() and p["native_solves"]==p["cert_promotions"]==0
    assert not git("diff","--name-only")
    import base64,hashlib
    entries=[]
    for path,d in p["files"].items():
        assert path.startswith(PREFIX)
        b=Path(path).read_bytes();assert sha(b)==d
        expected=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
        got=api("/git/blobs",{"content":base64.b64encode(b).decode(),"encoding":"base64"})["sha"]
        assert got==expected
        entries.append(dict(path=path,mode="100644",type="blob",sha=got))
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=entries))["sha"]
    c=api("/git/commits",dict(message="B907 archive successful read-only B905 and B906 evidence; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    receipt=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=h,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    archive.dump(out/"detached-candidate.json",receipt);print(json.dumps(receipt))

if __name__=="__main__":
    mode=sys.argv[1];out=Path(sys.argv[2]).resolve()
    bb.guard=guard;bb.inventory=inventory;btn.guard=guard
    # B906 copied a malformed GTO digest; pin exact API digest, not observed result.
    btn.PINS["5h4h3s"]["gto"]=(14792264343,137505625094,"63bbcdaa03624c3c37e3e3de35bdcb6ae1c50b12116d1423c5de5d2c34f36d58")
    if mode=="bb":
        assert sys.argv[4] in ("7h6h2c","9d7h4c")
        bb.plan(out,Path(sys.argv[3]).resolve(),sys.argv[4])
    elif mode=="btn":
        assert sys.argv[4] in ("5h4h3s","8h7h5c")
        btn.screen(out,Path(sys.argv[3]).resolve(),sys.argv[4])
    else:{"prepare":prepare,"publish":publish}[mode](out)
