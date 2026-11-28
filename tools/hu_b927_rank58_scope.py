"""B927: exclude historical rank58 scopes only after authenticating the existing native artifacts; never execute a solver."""
import base64,hashlib,json,os,sys,traceback,subprocess
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump,index_runs,rank_signature
BASE="68ebc35522703e85afdd0c0f6978b59bb4f3619f"
PRIOR=Path("data/solver_evidence/b926_barrel_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b927_rank58_scope")
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
SELECT={
45178881600:(617,"2ebce6807193eb5a992af4939349c29729b30fda","a2ad844d9cffc0cb0b90019d6d49a3244308a992","f0f9f4a3cc3856029254d4ebe3768f5480aed21f","1ccbdbda7f39247c0a2fd75ff110f3d9fcd31a81","bbf9fc433a561dde0a608411730dc6c1869cf327",{
"Kh8d5h":(137707181216,14821670088),"Jh8s5d":(137707181670,14821251168),"Ks7h2d":(137707181845,14819788838),"Ks9h5d":(137707181987,14822300047)}),
45195896755:(631,"5d4cc240b6a8ccddd95a78915c45539f80db6d90","74b7fcb56a87102f59b887605ead4e8a932fd47a","8d8435f02fab34318a64e6c7a20ed2bc5738805b","ec2ebede581d289834b6ec8485ccaec396bf7cb3","1978b8e40fc6f0d0a24eaef592df66c56ea5635b",{
"KsQh4d":(137766118827,14829520536),"Js9h4d":(137766119331,14829586341),"QsTc5h":(137766119543,14829690308)}),
45230117917:(636,"e926ffadd56e49878f79088014274ad9a9334f00","e2e6cdce7c103a2e2023323834517114a1050742","948bd3b983440196ebcfae66b59b9cc32b93004d","1ccbdbda7f39247c0a2fd75ff110f3d9fcd31a81","1978b8e40fc6f0d0a24eaef592df66c56ea5635b",{"Kh8d5h":(137887067274,14846059010)}),
}
def historical(head,path):
    return subprocess.check_output(["git","show",head+":"+str(path)])
def logs_for(j,head):
    raw=api("/actions/jobs/"+str(j["id"])+"/logs",raw=True)
    lines=raw.decode("utf-8").splitlines()
    checkouts=[lines[i+1] for i,l in enumerate(lines[:-1]) if "git log -1 --format=%H" in l]
    assert [x.split()[-1] for x in checkouts]==[head,SOLVER]
    return raw,lines,checkouts
def archive(aid,inv,rid,head):
    pin=inv["artifact_metadata"][str(aid)]
    a=api("/actions/artifacts/"+str(aid))
    assert (a["id"],a["name"],a["digest"],a["expired"])==(aid,pin["name"],pin["digest"],False)
    assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"],a["workflow_run"]["repository_id"],a["workflow_run"]["head_branch"])==(rid,head,1438346845,BRANCH)
    raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True)
    assert "sha256:"+sha(raw)==a["digest"]
    return a,raw
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def blob(head,path):return git("rev-parse",head+":"+str(path))

def prove(item,row,inv,targets):
    rid=item["run"]
    batch,head,wf,workerpin,sourcepin,helperpin,cases=SELECT[rid]
    assert (row["run"],row["head"],row["workflow_blob"])==(rid,head,wf)
    assert blob(head,row["workflow"])==wf
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(head,BRANCH,row["workflow"],"completed","success")
    sourcepath="data/nl2_hu_b"+str(631 if batch==631 else 617)+"_rank58_sources.json"
    worker="tools/hu_b"+str(batch)+"_rank58.py"
    pins={worker:workerpin,sourcepath:sourcepin,"tools/hu_b617_rank58.py":"f0f9f4a3cc3856029254d4ebe3768f5480aed21f","tools/hu_b613_rank55_barrels.py":helperpin,"tools/hu_b617_sb_routes.cjs":"bef524e2f09b1b7c519256ae080a372f3ea1c70e"}
    if batch==636:
        pins.update({"tools/hu_native_river_witness_import.py":"536b0504e631f6bbe31008814261eb6a42d1ea28","data/nl2_hu_b617_rank58_partial.json":"fa251d06ef8399a243fea7cb853d4c865d551a69"})
    for path,digest in pins.items():assert blob(head,path)==digest
    sources=json.loads(historical(head,sourcepath))
    assert set(cases)==(set(sources) if batch!=636 else {"Kh8d5h"})
    target_ranks={rank_signature(t["candidate"]["flop"]) for t in targets.values()}
    assert all(rank_signature(f) not in target_ranks for f in cases)
    response=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
    jobs={j["id"]:j for j in response["jobs"]}
    expected={j for j,a in cases.values()}|({137892759699} if batch==636 else set())
    assert set(jobs)==expected and response["total_count"]==len(jobs)==len(row["jobs"])
    assert {j["id"] for j in row["jobs"]}==expected
    assert all((j["head_sha"],j["status"],j["conclusion"])==(head,"completed","success") for j in jobs.values())
    artifacts=api("/actions/runs/"+str(rid)+"/artifacts?per_page=100")
    expected_artifacts={a for j,a in cases.values()}|({14848101009} if batch==636 else set())
    assert {a["id"] for a in artifacts["artifacts"]}==expected_artifacts==set(row["artifacts"])
    assert artifacts["total_count"]==len(expected_artifacts)
    receipts=[]
    for flop,(jid,aid) in cases.items():
        j=jobs[jid];assert j["name"]==("solve" if batch==636 else "solve ("+flop+")")
        steps={s["name"]:s["conclusion"] for s in j["steps"]}
        assert steps["Compile the pinned Rust solver and verify the named original GTO boundary"]=="success"
        assert steps["Run actions/upload-artifact@v4"]=="success"
        raw,lines,checkouts=logs_for(j,head)
        assert any("python "+worker+" --solver pinned-solver" in l for l in lines)
        assert any("--driver pinned-solver/postflop/pfdriver/target/release/pfdriver" in l for l in lines)
        assert any('cmp "$RUNNER_TEMP/native-proof.json" "$output/proof.json"' in l for l in lines)
        a,b=archive(aid,inv,rid,head)
        assert a["name"]=="B"+str(batch)+"-R58-"+flop
        assert any("Artifact ID "+str(aid) in l for l in lines)
        assert any(a["digest"].split(":")[1] in l and "SHA256 digest of uploaded artifact" in l for l in lines)
        with ZipFile(BytesIO(b)) as z:
            names=z.namelist();assert z.testzip() is None and len(set(names))==len(names)
            proofname,=[n for n in names if Path(n).name=="proof.json"]
            report=json.loads(z.read(proofname))
            assert (report["rank"],report["model_id"],report["flop"],report["run"],report["original_artifact"])==(58,"ln-opfr-r_model-aumml6",flop,rid,sources[flop]["artifact_id"])
            assert len(report["root_sha256"])==64 and report["original_nodes_reproduced"]>0
            allowed=["7d"] if batch==636 else sources[flop]["turns"]
            turns=[x["turn"] for x in report["turns"]]
            assert turns and turns==allowed[:len(turns)]
            pairs=[]
            jnames=[n for n in names if Path(n).name=="job.json"]
            rnames=[n for n in names if Path(n).name=="result.json"]
            assert {str(Path(n).parent) for n in jnames}=={str(Path(n).parent) for n in rnames}
            for name in jnames:
                res=str(Path(name).with_name("result.json"))
                jb=z.read(name);rb=z.read(res);job=json.loads(jb);result=json.loads(rb)
                assert job["flop"]==result["flop"]==flop
                assert rank_signature(job["flop"]) not in target_ranks
                pairs.append(dict(job=name,result=res,job_sha256=sha(jb),result_sha256=sha(rb),turn=job.get("turn")))
            for t in turns:
                for v in ("gto","exp_oop"):
                    assert any(Path(x["job"]).parent.name==t+"-"+v and x["turn"]==t for x in pairs)
        receipts.append(dict(flop=flop,job_id=jid,artifact_id=aid,artifact_sha256=sha(b),proof=report,job_result_pairs=pairs,log_sha256=sha(raw),checkout_log_lines=checkouts,steps=steps))
    publication=None
    if batch==636:
        j=jobs[137892759699];assert j["name"]=="verify"
        raw,lines,checkouts=logs_for(j,head)
        assert any("python tools/hu_b636_rank58.py --solver ../solver" in l for l in lines)
        assert not any("--driver " in l for l in lines)
        old=json.loads(historical(head,"data/nl2_hu_b617_rank58_partial.json"))
        priorflops={b["flop"] for b in old["group"]["boards"]}
        assert priorflops=={"Ks7h2d","Jh8s5d"} and all(rank_signature(f) not in target_ranks for f in priorflops)
        a,b=archive(14848101009,inv,rid,head)
        assert a["name"]=="B636-authenticated-rank58"
        with ZipFile(BytesIO(b)) as z:
            assert z.testzip() is None
            groupname,=[n for n in z.namelist() if n.endswith("/rank58.json") or n=="rank58.json"]
            group=json.loads(z.read(groupname))
            assert {x["flop"] for x in group["boards"]}==priorflops|set(cases)
        publication=dict(job_id=j["id"],artifact_id=a["id"],artifact_sha256=sha(b),log_sha256=sha(raw),checkout_log_lines=checkouts,flops=sorted(priorflops|set(cases)))
    return dict(ledger=item,run=rid,head=head,workflow=row["workflow"],workflow_blob=wf,pins=pins,native_cases=receipts,publication=publication,category="PINNED_RANK58_NATIVE_WORKER_FLOP_RANK_DISJOINT_FROM_SIX_TARGETS")
def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="71dca91ef10aac27376c30d9689029a4c563baf1"
    p=read(PRIOR);inv=read(INV);byid=index_runs(inv)
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==31
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    assert set(SELECT)<=set(x.get("run") for x in p["remaining"])
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        rid=item.get("run")
        if rid not in SELECT:remaining.append(item);continue
        try:closed.append(prove(item,byid[rid],inv,p["targets"]))
        except Exception as e:remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800],traceback=traceback.format_exc(limit=4)[-2200:]))
    assert len(closed)+len(blocked)==3 and len(closed)+len(remaining)==31
    groups={}
    for item in remaining:
        if "run" in item:
            row=byid[item["run"]]
            groups.setdefault(row["workflow_blob"],dict(path=row["workflow"],runs=[]))["runs"].append(item["run"])
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=closed,remaining=remaining,blocked_selected=blocked,grouped_original_run_scopes=groups,original_native_denylist=p["original_native_denylist"],targets=p["targets"],global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="Three historical rank58 runs with eight existing worker artifacts; authenticate original checkout, proof and each native job/result hash, exclude disjoint flop rank multisets only.")
    out.mkdir(parents=True,exist_ok=False);dump(out/"run-scope.json",report)
    if closed:
        PREFIX.mkdir(parents=True,exist_ok=False);dump(PREFIX/"run-scope.json",report)
    print(json.dumps(dict(selected=3,closed=len(closed),remaining=len(remaining),blocked=blocked,coverage=cov,clearance=False)))
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
    c=api("/git/commits",dict(message="B927 archive audited disjoint historical rank58 native scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_run_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
