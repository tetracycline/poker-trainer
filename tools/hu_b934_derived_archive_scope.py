"""B934 authenticate historical flat worker archives; no native execution."""
import gzip,base64,hashlib,json,os,sys,traceback,subprocess,itertools,ast
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b918_run_scope import read,dump

BASE="7fa910892780e2265e5d7530f5bd05736c5ce5ff"
PRIOR=Path("data/solver_evidence/b933_flat_artifact_scope/run-scope.json")
INV=Path("data/solver_evidence/b916_history_inventory/inventory.json")
PREFIX=Path("data/solver_evidence/b934_derived_archive_scope")
SOLVER="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST="9d1509fe5077d019825f833eed04b16d342dfda1"
from hu_b933_flat_artifact_scope import canonical,verify_canonical
SELECT={
14729207110:(44960100932,"c62d41fb06c5200dcceca59df16a0e341066f5a6","623dc83a81cd57ca64962db97388590f2060dfda",137018816483),
14730015601:(44960924477,"88a62a4ce13c8ab5c10d89a32e2868060fd3f6cb","763cdd2d9fae7786d20e5cbfb1a7f3ad23e97399",137019668053),
14793549867:(45120208827,"972be701de6e00e72e55b01e99d95d6234106aee","5080944553981de55d01800c67d70f6e936d19ce",137512002839),
}
def compact(x):return json.dumps(x,separators=(",",":"),ensure_ascii=False).encode()
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def blob(head,path):return git("rev-parse",head+":"+str(path))


def derived(z,aid,p,targets):
    is_gto=aid==14729207110
    stem="NL2_MULTIBOARD_B323_R60_9S7H4D_GTO" if is_gto else "NL2_MULTIBOARD_B255_R60_9S7H4D_EXP_IP"
    prefix="data/solver_evidence/"+stem
    extra="data/nl2_hu_b323_rank60_cobb_9s7h4d_gto_parent_pin.json" if is_gto else "data/nl2_hu_b325_rank60_9s7h4d_true_actor_NL2_status.json"
    compressed={n for n in z.namelist() if n.endswith((".gz",".zip"))}
    assert compressed=={prefix+".json.gz"}
    for path in (prefix+".index.json",prefix+".json.gz",extra):
        assert z.read(path)==Path(path).read_bytes()
    ix=json.loads(z.read(prefix+".index.json"));ex=json.loads(z.read(extra))
    packed=z.read(prefix+".json.gz");raw=gzip.decompress(packed);x=json.loads(raw)
    oldid=14729427685 if is_gto else 14728889946
    prior,=[c for c in p["closed_artifact_scopes"] if c["artifact"]["id"]==oldid]
    assert prior["run"]==SELECT[aid][0]
    root,=[v for v in prior["native_pairs"] if v["turn"] is None]
    child,=[v for v in prior["native_pairs"] if v["turn"]=="Ad"]
    assert (child["flop"],child["canonical"],child["pot"],child["stack"])==("9s7h4d","4c7d9h/Ac",1100,9475)
    assert child["canonical"] not in targets and child["job_sha256"] not in {t["candidate"]["job_sha256"] for t in targets.values()}
    if is_gto:
        assert (ix["run_id"],ix["verified_cases"],ix["gto_cases"],ix["locked_cases"])==(prior["run"],1,1,0)
        assert (ix["gzip_sha256"],ix["source_sha256"])==(sha(packed),sha(raw))
        assert (ex["flop"],ex["turn"],ex["spot"],ex["flop_line"])==("9s7h4d","Ad","CO_BB","x b50 c")
        assert (ex["original_gto_root_sha256"],ex["original_gto_job_sha256"])==(root["result_sha256"],root["job_sha256"])
        assert x["source_run_id"]==prior["run"] and not x["errors"]
        a,=x["artifacts"];case,=a["cases"]
        assert (a["spot"],a["flop"],a["version"],case["turn"],case["flop_line"],case["source_sha256"])==("CO_BB","9s7h4d","gto","Ad","x b50 c",child["result_sha256"])
    else:
        assert (ix["source_run_id"],ix["spot"],ix["flop"],ix["turn"],ix["actor"])==(prior["run"],"CO_BB","9s7h4d","Ad","CO_IP")
        assert (ix["authentic_NL2_Rust_gzip_sha256"],ix["authentic_NL2_Rust_source_sha256"],ix["nl2_job_sha256"])==(sha(packed),sha(raw),child["job_sha256"])
        assert sha(raw)==child["result_sha256"] and (x["flop"],x["turn"],x["line0"],x["pot"],x["stack"])==("9s7h4d","Ad","x b50 c",1100,9475)
        assert (ix["original_GTO_root_sha256"],ix["original_GTO_job_sha256"])==(root["result_sha256"],root["job_sha256"])
        assert ex["NL2_paired_source_index_sha256"]==sha(z.read(prefix+".index.json"))
    return dict(category="DERIVED_PUBLICATION_EXACT_MATCH_TO_B933_ORIGINAL_NATIVE_SCOPE",original_artifact=oldid,archive_member=prefix+".json.gz",compressed_sha256=sha(packed),uncompressed_sha256=sha(raw),native_pairs=prior["native_pairs"])

def b539(z,targets):
    f="9s7d4h";prefix="solver/postflop/out/ISO_BTN_CO/gto/";names=set(z.namelist())
    assert z.read("trainer/evidence/poker-solver-pin.txt").decode().strip()==SOLVER
    assert z.read("trainer/evidence/rust-pin.txt").decode().strip()==RUST
    m=json.loads(z.read("trainer/evidence/"+f+"-gto.json"))
    assert (m["spot"],m["flop"],m["version"],m["turns"],m["selected_lines"])==("ISO_BTN_CO",f,"gto",["4s","Jh"],["x b33 c","x b50 c"]) or (m["spot"],m["flop"],m["version"],set(m["turns"]),set(m["selected_lines"]))==("ISO_BTN_CO",f,"gto",{"4s","Jh"},{"x b33 c","x b50 c"})
    assert not m["failures"] and not m["skipped"] and len(m["cases"])==4
    jobs={n for n in names if n.endswith(".job.json")}
    assert len(jobs)==5 and all(n.startswith(prefix) for n in jobs)
    assert {n for n in names if n.startswith(prefix)}==jobs|{n.removesuffix(".job.json")+".json" for n in jobs}
    targetsha={v["candidate"]["job_sha256"] for v in targets.values()}
    pairs=[];originals={}
    for n in sorted(jobs):
        rn=n.removesuffix(".job.json")+".json";jb=z.read(n);rb=z.read(rn);j=json.loads(jb);x=json.loads(rb)
        assert j["flop"]==x["flop"]==f and (j["pot"],j["stack"])==(x["pot"],x["stack"]) and sha(jb) not in targetsha
        t=j.get("turn") or None
        if t:
            assert t==x["turn"] and canonical(f,t) not in targets
            c,=[v for v in m["cases"] if (v["line"],v["turn"])==(x["line0"],t)]
            assert c["source_sha256"]==sha(rb)
            originals[(x["line0"],t)]=(j,x,sha(rb))
        else:
            assert n==prefix+f+"_multiboard.job.json" and m["file_flop_sha256"]==sha(rb)
            root=j;rootsha=sha(rb)
        pairs.append(dict(job=n,result=rn,flop=f,turn=t,canonical=canonical(f,t),pot=j["pot"],stack=j["stack"],job_sha256=sha(jb),result_sha256=sha(rb)))
    assert set(originals)=={(l,t) for l in ("x b33 c","x b50 c") for t in ("4s","Jh")}
    gz,=[n for n in names if n.endswith((".gz",".zip"))]
    assert gz=="trainer/native/NL2_B539_R125_9S7D4H_4S_EXP_IP.json.gz"
    packed=z.read(gz);v=json.loads(gzip.decompress(packed))
    assert (v["schema"],v["solver"],v["rust"],v["run"],v["version"])==("NL2_HU_FROZEN_GTO_FLOP_CONDITIONAL_NATIVE_LOCK_V1",SOLVER,RUST,45120208827,"exp_ip")
    j=v["job"];raw=base64.b64decode(v["source_file_b64"],validate=True);x=json.loads(raw)
    assert v["job_sha256"]==sha(compact(j)) and v["source_sha256"]==sha(raw) and v["job_sha256"] not in targetsha
    g,sub,subsha=originals[("x b33 c","4s")]
    assert (j["flop"],j["turn"],j["line0"],j["hero"])==(f,"4s",["x","b33","c","/"],1) and j["locks"]
    assert all(x[k]==sub[k] for k in ("flop","pot","stack","hands"))
    assert v["original"]==dict(original_run=45120208827,root_sha256=rootsha,source_sha256=subsha,root_job_sha256=sha(compact(root)),turn_job_sha256=sha(compact(g)))
    assert canonical(f,"4s") not in targets
    pairs.append(dict(job=gz+"::job",result=gz+"::source_file_b64",flop=f,turn="4s",canonical=canonical(f,"4s"),pot=j["pot"],stack=j["stack"],job_sha256=v["job_sha256"],result_sha256=v["source_sha256"]))
    return dict(category="ISO_B539_ALL_FLAT_AND_COMPRESSED_NATIVE_IDENTITIES_NOT_TARGETS",native_pairs=pairs,compressed_member=gz,compressed_sha256=sha(packed))

def prove(item,inv,p):
    aid=item["artifact"];rid,head,wf,jid=SELECT[aid]
    obs,=[o for o in inv["observations"] if o["source"]=="artifact:"+str(aid)]
    meta=api("/actions/artifacts/"+str(aid));pin=inv["artifact_metadata"][str(aid)]
    assert all(meta[k]==pin[k] for k in ("id","name","digest","workflow_run","size_in_bytes"))
    assert not meta["expired"] and meta["workflow_run"]["id"]==rid and meta["workflow_run"]["head_sha"]==head
    run=api("/actions/runs/"+str(rid))
    assert (run["head_sha"],run["head_branch"],run["status"],run["conclusion"])==(head,BRANCH,"completed","success") and blob(head,run["path"])==wf
    job=api("/actions/jobs/"+str(jid))
    assert (job["run_id"],job["head_sha"],job["status"],job["conclusion"])==(rid,head,"completed","success")
    assert any("upload-artifact" in x["name"] and x["conclusion"]=="success" for x in job["steps"])
    raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True)
    assert sha(raw)==obs["sha256"]==meta["digest"].removeprefix("sha256:")
    with ZipFile(BytesIO(raw)) as z:
        assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
        assert {m.filename:m.file_size for m in z.infolist()}=={m["name"]:m["size"] for m in obs["members"]}
        proof=b539(z,p["targets"]) if aid==14793549867 else derived(z,aid,p,p["targets"])
    return dict(ledger=item,artifact=meta,run=rid,head=head,workflow=run["path"],workflow_blob=wf,job=jid,job_name=job["name"],archive_sha256=sha(raw),**proof)
def prepare(out):
    h=guard();cov=coverage()
    assert blob(h,PRIOR)=="d6f8362c393b7b70f1253550c2c554244d63fe94"
    p=read(PRIOR);inv=read(INV);verify_canonical(p["targets"])
    assert p["coverage"]==cov==inv["coverage"] and len(p["remaining"])==12
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    assert set(SELECT)<={x.get("artifact") for x in p["remaining"]}
    closed=[];remaining=[];blocked=[]
    for item in p["remaining"]:
        if item.get("artifact") not in SELECT:remaining.append(item);continue
        try:closed.append(prove(item,inv,p))
        except Exception as e:
            remaining.append(item);blocked.append(dict(ledger=item,error=type(e).__name__+": "+str(e)[:800],traceback=traceback.format_exc(limit=4)[-2200:]))
    assert len(closed)+len(blocked)==len(SELECT) and len(closed)+len(remaining)==12
    report=dict(parent=h,coverage=cov,prior_scope_blob=blob(h,PRIOR),closed_run_scopes=[],closed_artifact_scopes=closed,remaining=remaining,blocked_selected=blocked,grouped_original_run_scopes=p["grouped_original_run_scopes"],original_native_denylist=p["original_native_denylist"],targets=p["targets"],global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,prior_success_run=46127639708,scope="Derived B323/B325 publications and B539 mixed native archive; fixed child identity closure only. No dispatch or promotion.")
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
    c=api("/git/commits",dict(message="B934 archive verified derived and compressed native artifact scopes; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(parent=h,expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,
        ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=[entry],
        files={str(path):sha(b)},coverage=p["coverage"],closed=len(p["closed_artifact_scopes"]),
        remaining=len(p["remaining"]),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
