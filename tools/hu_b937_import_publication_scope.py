"""B937: audit historical native-witness import and B331 publication scopes, without executing any historical solver."""
import io,json,os,subprocess,sys,traceback,zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump
import hu_b936_registry_only_scope as previous

BASE="9ccf01a8d2eec91587a473c7e26cc38f017543eb"
PRIOR=Path("data/solver_evidence/b936_registry_only_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b937_import_publication_scope")
SELECT={45195896854,44961393736}
IMPORT_HEAD="5d4cc240b6a8ccddd95a78915c45539f80db6d90"
B331_HEAD="12729fa2afbb8c20387f97b3fbdaf7f5468e7281"
B331_OUTPUT="b15ab39aa5b6bd43b6c3ecffee1915ae727a3172"
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
IMPORT_PINS={
 "tools/hu_native_river_witness_import.py":"536b0504e631f6bbe31008814261eb6a42d1ea28",
 "data/nl2_hu_native_river_worker_receipts.json":"63edb220a42b9795a9539073af3849568d8caf60",
 "tools/hu_b613_rank55_barrels.py":"1978b8e40fc6f0d0a24eaef592df66c56ea5635b",
 "tools/hu_b617_rank58.py":"f0f9f4a3cc3856029254d4ebe3768f5480aed21f",
 "tools/hu_b624_rank55_flops.py":"6f4a57bcd77a857f0b51d15c3955b7914a6799a4",
 "tools/hu_b613_rank55_routes.cjs":"8e0553943c1b13b9c0961f501332e54fbd4d80a7",
 "tools/hu_b617_sb_routes.cjs":"bef524e2f09b1b7c519256ae080a372f3ea1c70e",
 "data/nl2_hu_b613_rank55_partial.json":"3132327fcb3a3ba2a88f86d13a0c9f7e4427f33a",
 "data/nl2_hu_b617_rank58_partial.json":"fa251d06ef8399a243fea7cb853d4c865d551a69",
 "data/nl2_hu_b624_rank55_partial.json":"159e9545d5ece54c2766c1a2b940f3ba35636d62",
 "tools/hu_checked_gto_boundary.py":"b3916a3dbc7e2750be3f09feaea349caa3119168",
 "tools/hu_b550_rank69_originals.py":"26d034594710a1d3809aa4b59127ac5657aeeb9d",
 "tools/hu_b470_rank73_new_rivers.py":"39336981ae910b385744a2b0aaea237397babb38",
 "tools/hu_reverified_board_pair.py":"ac58961ba8890d989165b03e3432d4f27b9cd5c6",
}
B331_PINS={
 "tools/hu_b331_v44_rank60_four_true_gto_nl2_boards.py":"f3678ed50cea3390e953dd6b68edb4153b026dab",
 "tools/hu_b331_v44_ui_primary_failclosed.py":"d5e6a1e037c142c572a2fae1e6ee811358e835d0",
 "tools/hu_b319_v43_rank60_three_real_gto_nl2_cert.py":"0b053b6aa895e71d65a637803f2bb7ac44f9f588",
 "tools/hu_cert_lock_medium_audit.py":"20c05e5dad1a1652ac8aa92754fc99add918907d",
 "tools/hu_line_contract.js":"4128055d73d5ee9ae4398fdcc7579fcad01ef523",
 "tools/link_audit.js":"f48e66acf5c3f466836ab4aeb36eb8df129cd82a",
 "tools/reach_verify.js":"432bdb1b1582718bc93733106524383f5c10bf93",
 "tools/hu_model_path_audit.js":"ebcabaa9c1f65a878cca09c554c699b1919d4e28",
 "tools/hu_cert_lock_medium_coverage_matrix.py":"353c34fa5bedcc26b1b371b9c4a2499bb6dbf492",
 "tools/hu_multiboard_promote.py":"07e6b6fc915960de87fd5bf8aacbcea88b290b15",
 "data/nl2_hu_b323_rank60_cobb_9s7h4d_gto_parent_pin.json":"cab023b96c260699fb4a2ef8aa9cd934989afc6e",
 "data/solver_evidence/NL2_MULTIBOARD_B323_R60_9S7H4D_GTO.index.json":"4c510273a911c7b24466311ffc08b45493901510",
 "data/solver_evidence/NL2_MULTIBOARD_B255_R60_9S7H4D_EXP_IP.index.json":"2fd41a9b630d024c7bd874742f9d44c67a86b08f",
}
def blob(h,p):return git("rev-parse",h+":"+str(p))
def rawgit(h,p):return subprocess.check_output(["git","show",h+":"+str(p)])
def json_git(h,p):return json.loads(rawgit(h,p))
def verify_pins(h,pins):
    assert {p:blob(h,p) for p in pins}==pins
    return pins
def guard():
    previous.BASE=BASE
    return previous.guard()
def successful_run(rid):
    r=api("/actions/runs/"+str(rid))
    assert (r["head_branch"],r["status"],r["conclusion"])==(BRANCH,"completed","success")
    return r
def run_scope(row,head,wf):
    rid=row["run"];r=successful_run(rid)
    assert (r["head_sha"],r["path"])==(head,wf)
    assert row["head"]==head and row["workflow"]==wf and row["complete_listing"]
    assert blob(head,wf)==row["workflow_blob"]
    jobs=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
    assert jobs["total_count"]==len(jobs["jobs"])==len(row["jobs"])
    known={j["id"]:j for j in row["jobs"]};out={}
    for j in jobs["jobs"]:
        old=known[j["id"]]
        assert (j["name"],j["head_sha"],j["status"],j["conclusion"])==(old["name"],head,"completed","success")
        assert [(s["name"],s["conclusion"]) for s in j["steps"]]==[(s["name"],s["conclusion"]) for s in old["steps"]]
        log=api("/actions/jobs/"+str(j["id"])+"/logs",raw=True)
        text=log.decode("utf-8",errors="strict")
        assert head in text
        out[j["name"]]=(j["id"],sha(log),text)
    artifacts=api("/actions/runs/"+str(rid)+"/artifacts?per_page=100")
    assert artifacts["total_count"]==len(artifacts["artifacts"])==len(row["artifacts"])
    assert sorted(x["id"] for x in artifacts["artifacts"])==sorted(row["artifacts"])
    return out
def artifact(aid,rid=None,name=None,digest=None):
    a=api("/actions/artifacts/"+str(aid));w=a["workflow_run"]
    assert a["id"]==aid and not a["expired"] and w["repository_id"]==1438346845 and w["head_branch"]==BRANCH
    assert rid is None or w["id"]==rid
    assert name is None or a["name"]==name
    assert digest is None or a["digest"]=="sha256:"+digest
    r=successful_run(w["id"]);assert r["head_sha"]==w["head_sha"]
    raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True)
    assert a["digest"]=="sha256:"+sha(raw)
    return a,raw
def import_scope(item,row):
    assert row["workflow_blob"]=="eb49643af5d8d68645600b804e0bd189010aaa63"
    logs=run_scope(row,IMPORT_HEAD,".github/workflows/nl2-hu-native-river-import.yml")
    assert set(logs)=={"replay (613)","replay (617)","replay (624)"}
    pins=verify_pins(IMPORT_HEAD,IMPORT_PINS)
    index=json_git(IMPORT_HEAD,"data/nl2_hu_native_river_worker_receipts.json")
    assert set(index)=={"613","617","624"}
    proofs=[]
    for batch,count in [(613,1),(617,2),(624,1)]:
        r=index[str(batch)];j,d,log=logs[f"replay ({batch})"]
        assert SOLVER in log and f"{count} distinct positive named flops from {count} worker artifacts" in log
        part=json_git(IMPORT_HEAD,r["partial"]);g=part["group"];rank=58 if batch==617 else 55
        assert g["rank"]==rank and len(g["boards"])==len(g["pins"])==count
        assert {p["worker_artifact"] for p in g["pins"]}==set(r["worker"])
        assert {p["original_flop_artifact"] for p in g["pins"]}==set(r["original"])
        # Original roots are read as source receipts only; native run scopes are not removed.
        originals={}
        for aid in r["original"]:
            a,raw=artifact(aid)
            originals[aid]={"run":a["workflow_run"]["id"],"head":a["workflow_run"]["head_sha"],"zip_sha256":sha(raw)}
        for p in g["pins"]:
            flop,turn=p["flop"],p["turn"];aid=p["worker_artifact"]
            a,raw=artifact(aid,r["run"],f"B{batch}-R{rank}-{flop}",p["worker_sha256"])
            assert p["source_run_id"]==r["run"]
            ar=rawgit(IMPORT_HEAD,"data/solver_evidence/NL2_"+p["archive_code"]+".zip")
            assert sha(ar)==p["archive_sha256"]
            v="exp_oop" if rank==58 else "exp_ip"
            with zipfile.ZipFile(io.BytesIO(raw)) as source,zipfile.ZipFile(io.BytesIO(ar)) as published:
                rep=json.loads(source.read("proof.json"));receipt=json.loads(published.read("worker.json"))
                assert (rep["rank"],rep["run"],rep["flop"],rep["original_artifact"])==(rank,r["run"],flop,p["original_flop_artifact"])
                assert (receipt["id"],receipt["sha256"],receipt["head"],receipt["run"],receipt["original_artifact"])==(aid,a["digest"],a["workflow_run"]["head_sha"],r["run"],p["original_flop_artifact"])
                matches={}
                for version in ["gto",v]:
                    for name in ["job.json","result.json"]:
                        member=turn+"-"+version+"/"+name
                        s=source.read(member);assert published.read(member)==s
                        matches[member]=sha(s)
            proofs.append(dict(batch=batch,rank=rank,model_id=g["model_id"],flop=flop,turn=turn,worker_artifact=aid,
                 worker_run=r["run"],worker_head=a["workflow_run"]["head_sha"],worker_sha256=sha(raw),original=originals[p["original_flop_artifact"]],
                 published_archive_sha256=sha(ar),matching_native_members=matches,replay_job=j,replay_log_sha256=d))
    assert len(proofs)==4
    return dict(ledger=item,run=row["run"],head=IMPORT_HEAD,workflow_blob=row["workflow_blob"],pins=pins,
                category="READ_ONLY_WITNESS_IMPORT_NO_NATIVE_DISPATCH",original_native_sources=proofs)
def b331_scope(item,row):
    assert row["workflow_blob"]=="a4c592bf49b8959b1c705d6677777c096fad086f"
    logs=run_scope(row,B331_HEAD,".github/workflows/nl2-hu-hybrid-b331-v44-rank60-four-real-gto-nl2.yml")
    assert len(logs)==1
    j,d,log=next(iter(logs.values()))
    assert "PASS original immutable 6 actor GTO and genuine separate 6 NL2 Rust low texture 9s7h4d/Ad, V43 untouched" in log
    assert "PASS B331 V44 2475/2475" in log and "12729fa..b15ab39  HEAD -> "+BRANCH in log
    pins=verify_pins(B331_HEAD,B331_PINS)
    for rid in [44960840011,44960100932,44960924477]:successful_run(rid)
    assert git("rev-parse",B331_OUTPUT+"^")==B331_HEAD
    git("merge-base","--is-ancestor",B331_OUTPUT,BASE)
    files=[
     "data/nl2_hu_b331_rank60_four_true_GTO_NL2_actor_lock_source_gate.json",
     "data/nl2_hu_cert_lock_medium_matrix_v44_b331.json",
     "data/nl2_hu_multiboard_status_v44_b331_rank60_four_flops.json",
     "docs/NL2_HU_B331_V44_ALL_597_NAMED_ACTOR_LOCK_MEDIUM.md",
     "docs/NL2_HU_B331_V44_RANK60_FOUR_REAL_GTO_NL2_BOARD_CERT.md"]
    changed=set(git("diff","--name-only",B331_HEAD,B331_OUTPUT).splitlines())
    assert changed==set(files+["nl2-multiboard.js","nl2_hu_multiboard_ui.js"])
    aid=14730130721
    a,raw=artifact(aid,row["run"],"NL2-HU-B331-V44-rank60-four-true-GTO-plus-NL2-3textures-597-HU2475","16af1fc2344844e806c996993a17e6de2ea88fca41e96bd9c182480430dd45d0")
    outputs={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for path in files:
            candidates=[n for n in z.namelist() if n==path or n.endswith("/"+path) or n==Path(path).name]
            assert len(candidates)==1,(path,candidates)
            b=z.read(candidates[0]);assert b==rawgit(B331_OUTPUT,path)
            outputs[path]=sha(b)
    state=json_git(B331_OUTPUT,files[2]);prior=json_git(B331_HEAD,"data/nl2_hu_multiboard_status_v43_b319_rank60.json")
    assert (state["CERT_MULTIBOARD"],state["APPROX"],state["EST"],state["TOTAL"])==(156,236,0,392)
    assert {k for k in prior["records"] if prior["records"][k]!=state["records"][k]}=={"ln-ipfr-t_model-hxdit"}
    assert state["records"]["ln-ipfr-t_model-hxdit"]["proven_exact_board_count"]==4
    gi=json_git(B331_HEAD,"data/solver_evidence/NL2_MULTIBOARD_B323_R60_9S7H4D_GTO.index.json")
    ci=json_git(B331_HEAD,"data/solver_evidence/NL2_MULTIBOARD_B255_R60_9S7H4D_EXP_IP.index.json")
    assert (ci["spot"],ci["flop"],ci["turn"],ci["acting_seat"],ci["exact_line"])==("CO_BB","9s7h4d","Ad",1,"x b50 c/x")
    assert (gi["run_id"],ci["source_run_id"])==(44960100932,44960924477)
    assert sha(rawgit(B331_HEAD,"data/solver_evidence/NL2_MULTIBOARD_B323_R60_9S7H4D_GTO.json.gz"))==gi["gzip_sha256"]
    assert sha(rawgit(B331_HEAD,"data/solver_evidence/NL2_MULTIBOARD_B255_R60_9S7H4D_EXP_IP.json.gz"))==ci["authentic_NL2_Rust_gzip_sha256"]
    return dict(ledger=item,run=row["run"],head=B331_HEAD,workflow_blob=row["workflow_blob"],job=j,log_sha256=d,pins=pins,
                output_commit=B331_OUTPUT,output_files=outputs,artifact=aid,artifact_sha256=sha(raw),
                original_runs=[44960840011,44960100932,44960924477],category="EXISTING_CO_IP_RANK60_PUBLICATION_NO_NATIVE_DISPATCH")
def prepare(out):
    h=guard();cov=coverage();p=read(PRIOR);inv=read(INV)
    assert blob(h,PRIOR)=="46a74ecf5adf6f69e2204ecaefa47131cceebbb5"
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==5
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    rows={x["run"]:x for x in inv["runs"]};assert SELECT<={x["run"] for x in p["remaining"]}
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item["run"]
        if rid not in SELECT:remaining.append(item);continue
        try:closed.append((import_scope if rid==45195896854 else b331_scope)(item,rows[rid]))
        except Exception as e:
            remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:900],traceback=traceback.format_exc(limit=4)[-1800:]))
    assert len(closed)+len(blocked)==len(SELECT) and len(closed)+len(remaining)==5
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=closed,closed_artifact_scopes=[],remaining=remaining,
        blocked_selected=blocked,grouped_original_run_scopes=p["grouped_original_run_scopes"],original_native_denylist=p["original_native_denylist"],targets=p["targets"],
        global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,
        scope="Historical importer and B331 publication only; all native source identities retained, no continuation clearance.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=len(SELECT),closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,clearance=False)))
def publish(out):
    # Reuse the previously audited detached publisher and label the new receipt accurately.
    previous.BASE=BASE;previous.PREFIX=PREFIX
    def labelled_api(path,body=None,raw=False):
        if path=="/git/commits" and body is not None:
            body=dict(body,message="B937 archive verified import and publication scopes; no promotions")
        return api(path,body,raw)
    previous.api=labelled_api
    previous.publish(out)
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
