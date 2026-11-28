"""B939: close the last *dispatch inventory* scope, not cancelled-run certification.
Only inspect immutable artifacts and read-only import receipts; never run native CFR.
"""
import io,json,sys,zipfile,traceback
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump
import hu_b936_registry_only_scope as publisher
import hu_b937_import_publication_scope as p937

BASE="bbb3147bd36d96644a896af4eefd7b1df7c74ac1"
PRIOR=Path("data/solver_evidence/b938_final_priced_scopes/run-scope.json")
PREFIX=Path("data/solver_evidence/b939_import_dispatch_identity")
IMPORT=45195896854
HEAD=p937.IMPORT_HEAD
WF=".github/workflows/nl2-hu-native-river-import.yml"
# Cancelled original workflow evidence stays quarantined; never reinterpret it as successful.
ORIGINALS={
 14792312789:(45118153398,"d1b22cd54e8c5391f2ee6d9411488923979ac797","B524-R8-7d5c4c-gto","8aeec8c25159cde3db0b15046bddee1bd1fa3f71b4b92851b25918879c392852","cancelled","7d5c4c"),
 14790353462:(45112310600,"d8bf083bae0185722d754a0bffe2b95e58dd62","B519-R16-Jh8s5d-gto","48834f904a76292a95d1b159440624bbeb36085f045da42c9aa3cc99c2c80d3c","cancelled","Jh8s5d"),
 14593610543:(44654973894,"d1c7d1e07f214ca957dd7d707c452de846ecf007","nl2-stage2-SB_BB-gto-Ks7h2d","28f37cefb8d6adb25ed64f2b7d20098d4215fda32054f6a88b672aad0dc627b7","success","Ks7h2d"),
}
WORKERS={
 14819818214:(45177383424,"4ce7b90e0d4b9aa39934100596e7913a1b76e17a","B613-R55-7d5c4c","2209ba685404138b2e2e495ad539a8a1786ac9bb6e79a0f57fa1813a6d25946c","success","7d5c4c"),
 14821251168:(45178881600,"2ebce6807193eb5a992af4939349c29729b30fda","B617-R58-Jh8s5d","e069fd3b8aef8b2c95a71fedb9cbf983ce791d4c0d5da874a060acc89022cc83","success","Jh8s5d"),
 14819788838:(45178881600,"2ebce6807193eb5a992af4939349c29729b30fda","B617-R58-Ks7h2d","56fd68bd2550c9b2bbbad0facfd423f5a514a43c3b7ad16f8c24018e86ec1499","success","Ks7h2d"),
 14821790906:(45179871107,"d01c356959f6f9f9c7c6cb7ffe1c16348562603d","B624-R55-7s6c4c","f5384e2ae53deece390fb454c591bdc32b2b3856f547176ff4e5751c9036e3ea","success","7s6c4c"),
}

def guard():
    publisher.BASE=BASE
    return publisher.guard()

def rankset(f):
    assert isinstance(f,str) and len(f)==6 and all(f[i] in "23456789TJQKA" and f[i+1] in "cdhs" for i in (0,2,4))
    return "".join(sorted(f[::2]))

def scan_jobs(z,expected_flop,targets,target_hashes):
    # Conservative rank-multiset exclusion also rules out any suit-isomorphic duplicate.
    jobs=[]
    for member in z.namelist():
        if not (member.endswith(".job.json") or member.endswith("/job.json") or member=="job.json"):continue
        raw=z.read(member);j=json.loads(raw);f=j["flop"]
        assert rankset(f)==rankset(expected_flop), (member,f,expected_flop)
        assert rankset(f) not in targets and sha(raw) not in target_hashes
        jobs.append(dict(member=member,job_sha256=sha(raw),flop=f,turn=j.get("turn"),
                         pot=j["pot"],stack=j["stack"],line0=j.get("line0"),hero=j.get("hero")))
    assert jobs,expected_flop
    return jobs

def inspect(aid,pin,targets,target_hashes):
    rid,head,name,digest,conclusion,flop=pin
    r=api("/actions/runs/"+str(rid))
    assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(head,BRANCH,"completed",conclusion)
    if conclusion=="success":
        a,raw=p937.artifact(aid,rid,name,digest)
    else:
        # This branch is only a negative/identity receipt, NOT a substitute for
        # p937.successful_run. Cancelled original sources cannot support CERT.
        assert aid in ORIGINALS and conclusion=="cancelled"
        a=api("/actions/artifacts/"+str(aid));w=a["workflow_run"]
        assert a["id"]==aid and a["name"]==name and not a["expired"]
        assert (w["id"],w["head_sha"],w["head_branch"],w["repository_id"])==(rid,head,BRANCH,1438346845)
        assert a["digest"]=="sha256:"+digest
        raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True)
        assert sha(raw)==digest
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        jobs=scan_jobs(z,flop,targets,target_hashes)
    return dict(artifact=aid,run=rid,head=head,name=name,zip_sha256=digest,conclusion=conclusion,
                certification_source_eligible=conclusion=="success",flop=flop,jobs=jobs),raw

def prove(prior,inv):
    row,=[x for x in inv["runs"] if x["run"]==IMPORT]
    logs=p937.run_scope(row,HEAD,WF)
    assert set(logs)=={"replay (613)","replay (617)","replay (624)"}
    pins=p937.verify_pins(HEAD,p937.IMPORT_PINS)
    assert row["workflow_blob"]=="eb49643af5d8d68645600b804e0bd189010aaa63"
    index=p937.json_git(HEAD,"data/nl2_hu_native_river_worker_receipts.json")
    assert set(index)=={"613","617","624"}
    assert {i for v in index.values() for i in v["original"]}==set(ORIGINALS)
    assert {i for v in index.values() for i in v["worker"]}==set(WORKERS)
    # Read-only importer workflow actually executed only the pinned replay command,
    # downloaded previously created archives and checked git diff. Native driver is
    # not invoked by this workflow. Do not run the importer or any historical solver.
    for batch,count in ((613,1),(617,2),(624,1)):
        jid,d,log=logs[f"replay ({batch})"]
        assert p937.SOLVER in log
        assert f"{count} distinct positive named flops from {count} worker artifacts" in log
        assert "hu_native_river_witness_import.py" in log and "git diff --exit-code -- data" in log
    t=prior["targets"]
    target_ranks={rankset(v["candidate"]["flop"]) for v in t.values()}
    target_hashes={v["candidate"]["job_sha256"] for v in t.values()}
    assert len(t)==len(target_hashes)==6 and len(target_ranks)==3
    originals={};workers={};worker_bytes={}
    for aid,pin in ORIGINALS.items(): originals[aid],_=inspect(aid,pin,target_ranks,target_hashes)
    for aid,pin in WORKERS.items(): workers[aid],worker_bytes[aid]=inspect(aid,pin,target_ranks,target_hashes)
    publications=[]
    for batch,count in ((613,1),(617,2),(624,1)):
        idx=index[str(batch)];part=p937.json_git(HEAD,idx["partial"]);g=part["group"]
        rank=58 if batch==617 else 55
        assert g["rank"]==rank and len(g["boards"])==len(g["pins"])==count
        assert {p["worker_artifact"] for p in g["pins"]}==set(idx["worker"])
        assert {p["original_flop_artifact"] for p in g["pins"]}==set(idx["original"])
        for pin in g["pins"]:
            aid=pin["worker_artifact"];oid=pin["original_flop_artifact"];flop=pin["flop"];turn=pin["turn"]
            assert workers[aid]["flop"]==flop and workers[aid]["run"]==pin["source_run_id"]==idx["run"]
            assert workers[aid]["zip_sha256"]==pin["worker_sha256"]
            archive=p937.rawgit(HEAD,"data/solver_evidence/NL2_"+pin["archive_code"]+".zip")
            assert sha(archive)==pin["archive_sha256"]
            mode="exp_oop" if rank==58 else "exp_ip"
            with zipfile.ZipFile(io.BytesIO(worker_bytes[aid])) as source,zipfile.ZipFile(io.BytesIO(archive)) as published:
                rep=json.loads(source.read("proof.json"));receipt=json.loads(published.read("worker.json"))
                assert (rep["rank"],rep["run"],rep["flop"],rep["original_artifact"])==(rank,idx["run"],flop,oid)
                assert (receipt["id"],receipt["sha256"],receipt["head"],receipt["run"],receipt["original_artifact"])==(aid,"sha256:"+pin["worker_sha256"],workers[aid]["head"],idx["run"],oid)
                matches={}
                for version in ("gto",mode):
                    for filename in ("job.json","result.json"):
                        member=turn+"-"+version+"/"+filename
                        raw=source.read(member);assert published.read(member)==raw
                        matches[member]=sha(raw)
                    j=json.loads(source.read(turn+"-"+version+"/job.json"))
                    res=json.loads(source.read(turn+"-"+version+"/result.json"))
                    geom=(1200,9400,["x","b50","c","/"]) if rank==58 else (1100,9475,["b50","c","/"])
                    assert (j["pot"],j["stack"],j["line0"])==geom
                    assert (res["pot"],res["stack"],res["flop"])==(j["pot"],j["stack"],flop)
                pubjobs=scan_jobs(published,flop,target_ranks,target_hashes)
            publications.append(dict(batch=batch,rank=rank,flop=flop,turn=turn,worker=aid,original=oid,
                source_certification_eligible=originals[oid]["certification_source_eligible"],
                archive_sha256=sha(archive),matching_native_members=matches,job_identities=pubjobs))
    assert len(publications)==4
    assert {a for a,v in originals.items() if not v["certification_source_eligible"]}=={14792312789,14790353462}
    return dict(run=IMPORT,head=HEAD,workflow_blob=row["workflow_blob"],pins=pins,
        job_log_sha256={k:v[1] for k,v in logs.items()},originals=list(originals.values()),workers=list(workers.values()),
        publications=publications,target_rank_signatures=sorted(target_ranks),
        category="READ_ONLY_IMPORT_DISPATCH_IDENTITY_ONLY_NO_TARGET_RANK_MULTISET_MATCH",
        blocked_original_certification_artifacts=[14792312789,14790353462],native_dispatch=False)

def prepare(out):
    h=guard();p=read(PRIOR);inv=read(p937.INV);cov=coverage()
    assert p937.blob(h,PRIOR)=="e084b8837857aba35d96908c6457b6edae2a061d"
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==1 and p["remaining"][0]["run"]==IMPORT
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    try:
        proof=prove(p,inv);closed=[proof];remaining=[];blocked=[]
    except Exception as e:
        closed=[];remaining=p["remaining"];blocked=[dict(error=type(e).__name__+": "+str(e)[:900],traceback=traceback.format_exc(limit=5)[-2400:])]
    # Keep the old denylist and the target flags unchanged. Identity-only clearance
    # is a separate receipt; next stage must review the accepted audit and the
    # frozen boundary/positive source gate before dispatch. Cancelled roots remain
    # blocked for certification regardless of this inventory result.
    report=dict(parent=h,coverage=cov,prior_scope_blob=p937.blob(h,PRIOR),
      closed_run_scopes=closed,closed_artifact_scopes=[],remaining=remaining,blocked_selected=blocked,
      grouped_original_run_scopes=p["grouped_original_run_scopes"],original_native_denylist=p["original_native_denylist"],
      targets=p["targets"],dispatch_inventory_complete=bool(closed),global_history_clearance=False,can_dispatch_native=False,
      blocked_original_certification_artifacts=[14792312789,14790353462],native_solves=0,cert_promotions=0,
      formal_lock_additions=0,formal_nonpolarized_additions=0,
      scope="Dispatch inventory only; cancelled source runs remain non-CERT, target flags unchanged until separately reviewed.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,dispatch_inventory_complete=bool(closed))))

def publish(out):
    publisher.BASE=BASE;publisher.PREFIX=PREFIX
    def labelled(path,body=None,raw=False):
        if path=="/git/commits" and body is not None:
            body=dict(body,message="B939 archive last import dispatch identity; cancelled originals remain blocked for CERT")
        return api(path,body,raw)
    publisher.api=labelled
    publisher.publish(out)

if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
