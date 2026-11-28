"""B938: frozen historical rank89 publication and priced UTG source scopes; never run CFR."""
import io,json,sys,traceback,zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump
import hu_b936_registry_only_scope as publisher
import hu_b937_import_publication_scope as p937

BASE="9264f987ad08dc24fe0435df6048b9298d2cdbaa"
PRIOR=Path("data/solver_evidence/b937_import_publication_scope/run-scope.json")
PREFIX=Path("data/solver_evidence/b938_final_priced_scopes")
SELECT={45324358817,45178881476,45174796802}
H710="d9886707905cb909e60ded0fe213321286457a4e"
H619="2ebce6807193eb5a992af4939349c29729b30fda"
H595="6e305c61b113b36b54cba8fbaee404f57b3b1d69"
C710="387be667e12ca4707279714d6e388230b7d58a89"
TARGET_GEOM=(1100,9475,["x","b50","c","/"])
blob=p937.blob
rawgit=p937.rawgit
json_git=p937.json_git
verify_pins=p937.verify_pins

def guard():
    publisher.BASE=BASE
    return publisher.guard()

def member(z,path):
    matches=[n for n in z.namelist() if n==path or n.endswith("/"+path)]
    assert len(matches)==1,(path,matches)
    return z.read(matches[0])

def audit_scope(row,head,wf,wf_sha,pins):
    assert row["workflow_blob"]==wf_sha
    return p937.run_scope(row,head,wf),verify_pins(head,pins)

def rank89(item,row):
    logs,pins=audit_scope(row,H710,".github/workflows/nl2-hu-b710-rank89-publication.yml",
        "ab42d975bf774ddbf9db0fdd46a270f7f6a1181d",{
        "tools/hu_b710_collect.py":"928eee2cdefa9df794c0ef65e3f92fddda2b1283",
        "tools/hu_b710_prior_receipts.py":"7fe571624d6f0575d75fc580f4671f0a44017e17",
        "tools/hu_b710_publish.py":"7a877f1c1beab30653d1dc091830519d8220eb7d",
        "tools/hu_b710_integrate.py":"385478b0a2baeea19580f5eb466e4cd96c253565",
        "tools/hu_publish_candidate.py":"bb990fe27873c7680146515c262062db1645fd92"})
    assert set(logs)=={"replay-audit-candidate"}
    jid,d,log=logs["replay-audit-candidate"]
    assert jid==138210244129
    assert "CANDIDATE_COMMIT="+C710 in log and "CANDIDATE_PARENT="+H710 in log
    assert "CANDIDATE_TREE=64e035a1361c4aca92a2a1778232015a25186475" in log
    assert "PASS exact source registry, GTO/locked archives and zero-reach rejection" in log
    assert git("rev-parse",C710+"^")==H710
    git("merge-base","--is-ancestor",C710,BASE)
    assert blob(C710,"data/nl2_hu_b710_workers.json")=="364a654cac6905b64b55925674df7fa12e55be61"
    assert blob(C710,"data/nl2_hu_b710_summary.json")=="d62896ef6bac8df2a2a56375b3bb8b0e917cff01"
    assert blob(C710,"data/nl2_hu_b710_integration.json")=="a857f76b8861c485d56ccca6a81c240f6eb14117"
    a,raw=p937.artifact(14889530813,row["run"],"B710-five-original-rank89-publication",
        "3a0729e96ed70814f00c02830863e4373ba034f1bdc4d80d1af549a2d3bdf198")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for f in ["nl2_hu_b710_summary.json","nl2_hu_b710_integration.json"]:
            assert member(z,f)==rawgit(C710,"data/"+f)
    summary=json_git(C710,"data/nl2_hu_b710_summary.json")
    assert (summary["rank"],summary["distinct_positive_flops"],summary["native_solves_repeated"])==(89,5,0)
    workers=json_git(C710,"data/nl2_hu_b710_workers.json")
    assert len(workers)==3 and {w["flop"] for w in workers}=={"Td8c3h","Jh7d4c","Qc9s5d"}
    rr=p937.successful_run(45322275998)
    jobs={j["id"]:j for j in api("/actions/runs/45322275998/jobs?per_page=100")["jobs"]}
    source=[]
    for w in workers:
        assert (w["run"],w["head"])==(45322275998,rr["head_sha"])
        j=jobs[w["job_id"]]
        assert (j["name"],j["conclusion"],j["head_sha"])==(w["job_name"],"success",w["head"])
        a,b=p937.artifact(w["id"],w["run"],w["name"],w["sha256"])
        assert b==rawgit(C710,"data/solver_evidence/NL2_B709_R89_"+w["flop"].upper()+".zip")
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            proof=json.loads(z.read("proof.json"))
            files={n for n in z.namelist() if not n.endswith("/") and n!="proof.json"}
            assert set(proof["native_file_sha256"])==files
            assert all(sha(z.read(n))==proof["native_file_sha256"][n] for n in files)
        source.append(dict(worker=w,member_sha256=proof["native_file_sha256"]))
    return dict(ledger=item,run=row["run"],head=H710,job=jid,log_sha256=d,pins=pins,publication=C710,
        artifact=14889530813,artifact_sha256=sha(raw),original_native_workers=source,
        category="EXISTING_RANK89_PUBLICATION_NO_NEW_NATIVE_DISPATCH")

def native_archive(head,path,digest,flop,turn,mode,target_hashes):
    b=rawgit(head,path);assert sha(b)==digest
    rows=[]
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        assert set(z.namelist())=={s+ext for s in ("root","gto",mode) for ext in (".job.json",".json")}
        for stage in ("root","gto",mode):
            jb=z.read(stage+".job.json");rb=z.read(stage+".json")
            j=json.loads(jb);r=json.loads(rb)
            assert j["flop"]==r["flop"]==flop
            assert (j["pot"],j["stack"])==(r["pot"],r["stack"])==(650,9750)
            if stage!="root":
                assert j["turn"]==turn and j["line0"]==["x","x","/"]
                assert r.get("turn") in (None,turn)
            assert (j["pot"],j["stack"],j.get("line0"))!=TARGET_GEOM
            assert sha(jb) not in target_hashes
            rows.append(dict(stage=stage,job_sha256=sha(jb),result_sha256=sha(rb),flop=flop,
                turn=j.get("turn"),pot=j["pot"],stack=j["stack"],line0=j.get("line0")))
    return dict(path=path,sha256=digest,jobs=rows)

def utg(item,row,prior):
    rid=row["run"]
    b619=rid==45178881476
    if b619:
        head=H619;wf=".github/workflows/nl2-hu-b619-utg-rivers.yml";wf_sha="d166fb5e650fcddd9bd98321ebd82dc43e765130"
        inputs="data/nl2_hu_b619_utg_inputs.json"
        pins={"tools/hu_b619_utg_rivers.py":"655dca7e8e7cac16bea9de92e14b583d4c1a1fe5",inputs:"ffab79e1f0238baff68d46902b007fd2c47b53dd"}
        aid=14819809971;name="B619-authenticated-utg-rivers";digest="1330b94a1a026cd4024d1c3b1bc8cce0320c1b3fdae97a0f1e73978790c2620b"
        entries=json_git(head,inputs);assert set(entries)=={"110","111"} and all(len(v)==5 for v in entries.values())
    else:
        head=H595;wf=".github/workflows/nl2-hu-b595-rank149.yml";wf_sha="fbf262f4f2f87abb20db20c306d23f6257eb536b"
        inputs="data/nl2_hu_b595_rank149_inputs.json"
        pins={"tools/hu_b595_rank149.py":"2bea2fa755899c60d5ef0cbd6c8de5ef3ed6d535",inputs:"1453906bc759c130acbcd00a23be7ff99123caa7",
              "data/nl2_hu_b575_turn_inputs.json":"36bb6c68357522223004d60671b5ab6c90cc2f86"}
        aid=14818656717;name="B595-authenticated-rank149";digest="d1c5502ad56f15402834608aeebff22c7b125679172a4f3684198c523d856cc1"
        entries={"149":json_git(head,inputs)["boards"]};assert len(entries["149"])==3
    logs,pins=audit_scope(row,head,wf,wf_sha,pins)
    allflops={s["flop"] for v in entries.values() for s in v}
    if b619:
        assert set(logs)=={"select","verify"}|{"reproduce ("+f+")" for f in allflops}
        assert all("Re-solve flop, transferred turn and locked river policies" in logs["reproduce ("+f+")"][2]
                   or " --reproduce-flop "+f in logs["reproduce ("+f+")"][2] for f in allflops)
        final=logs["verify"]
    else:
        assert set(logs)=={"replay-audit"};final=logs["replay-audit"]
    assert "PASS exact source registry, GTO/locked archives and zero-reach rejection" in final[2]
    a,b=p937.artifact(aid,rid,name,digest)
    target_hashes={v["candidate"]["job_sha256"] for v in prior["targets"].values()}
    archives=[];groups=[]
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        for rank,specs in entries.items():
            g=json.loads(member(z,"rank"+rank+".json"))
            assert g["rank"]==int(rank) and len(g["boards"])==len(g["pins"])==(5 if b619 else 4)
            assert all(b["spot"]=="UTG_CO" for b in g["boards"]) if all("spot" in b for b in g["boards"]) else True
            assert {s["flop"] for s in specs}<={b["flop"] for b in g["boards"]}
            groups.append(dict(rank=int(rank),model=g["model_id"],flops=[b["flop"] for b in g["boards"]]))
            for s in specs:
                path="data/solver_evidence/"+(f"NL2_B619_R{rank}_{s['flop'].upper()}.zip" if b619 else s["archive"])
                archives.append(native_archive(head,path,s["archive_sha256"] if b619 else s["sha256"],
                    s["flop"],s["turn"],"native" if b619 else "exp_oop",target_hashes))
    originals=[]
    if not b619:
        # Existing B51 roots also remain original receipts; do not treat the publication
        # replay as new native evidence, or weaken the original success gate.
        receipt=json_git(head,"data/nl2_hu_b575_turn_inputs.json")["originals"]
        for k in ("14664258709","14664239001"):
            x=receipt[k];a,b=p937.artifact(int(k),x["run"],x["name"],x["sha256"])
            assert a["workflow_run"]["head_sha"]==x["head"]
            originals.append(dict(artifact=int(k),receipt=x))
    return dict(ledger=item,run=rid,head=head,pins=pins,job_log_sha256={k:v[1] for k,v in logs.items()},
        artifact=aid,artifact_sha256=digest,groups=groups,native_archive_receipts=archives,original_artifacts=originals,
        category="UTG_CO_650_9750_CHECK_THROUGH_SOURCE_NOT_1100_9475_TARGET",
        native_replay_performed_historically=b619,native_replay_this_batch=False)

def prepare(out):
    h=guard();cov=coverage();p=read(PRIOR);inv=read(p937.INV)
    assert blob(h,PRIOR)=="d1c5ea5d81bbf622e7ec375b84bbb1d2b01e3774"
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==4
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    rows={x["run"]:x for x in inv["runs"]}
    assert SELECT<={x["run"] for x in p["remaining"]}
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item["run"]
        if rid not in SELECT:remaining.append(item);continue
        try:closed.append(rank89(item,rows[rid]) if rid==45324358817 else utg(item,rows[rid],p))
        except Exception as e:
            remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:900],traceback=traceback.format_exc(limit=4)[-1800:]))
    assert len(closed)+len(blocked)==3 and len(closed)+len(remaining)==4
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=closed,closed_artifact_scopes=[],remaining=remaining,
      blocked_selected=blocked,grouped_original_run_scopes=p["grouped_original_run_scopes"],original_native_denylist=p["original_native_denylist"],
      targets=p["targets"],global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,
      formal_lock_additions=0,formal_nonpolarized_additions=0,
      scope="Rank89 prior publication and UTG original job/result identities only; same texture does not imply same pot/stack/line. B937 importer remains blocked. No dispatch.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=3,closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,clearance=False)))

def publish(out):
    publisher.BASE=BASE;publisher.PREFIX=PREFIX
    def labelled(path,body=None,raw=False):
        if path=="/git/commits" and body is not None:
            body=dict(body,message="B938 archive rank89 publication and priced UTG source scope evidence; no promotions")
        return api(path,body,raw)
    publisher.api=labelled
    publisher.publish(out)

if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
