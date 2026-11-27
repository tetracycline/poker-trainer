"""B918: archive B917's audited legacy result; narrow immutable run scopes.
No driver execution, no ref mutation, no certification. Keep all source identities.
"""
import base64, hashlib, io, json, os, sys, zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
from hu_b895_archive_r158 import coverage
BASE="79673c29773bb3bb8a300ec0d78315f8b29e7971"
SOURCE="499b8c38545d911e2fa437c515fcffa4d8009cae"
RUN=46028303360
AUDIT=46028303252
JOB=140605299501
AID=15213356027
DIGEST="1fefced9d28101877eff8e07b72152b5e52fc11545f6962bffc761dcb8ce0047"
E=Path("data/solver_evidence")
PREFIX=E/"b918_run_scope"
INV=E/"b916_history_inventory/inventory.json"
SCAN=E/"b917_legacy_identity/b916-scan.json"
STATIC={45230117610,45195896794,45176303085,45174796664,45151346610}
MATRICES={
45230117506:("8a2dafd8dcb3aa93a340896f4a26e07d41e286da","hu_b637_rank57.py","86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9","solve",["TdTs4h","QcQd4s","JdJh3c","TcTh3s"],"SB_BB"),
45178881468:("38e6ff545e9e5e49d3cf783e3df29241c3d9918d","hu_b618_limp_monotone.py","edee99129f6ef481d0677f0cf13fea6a25616c07","reproduce",["Ks7s3s","Qh8h4h","Jc7c3c","Kd9d4d","Qs6s2s"],"LMP_CO_BB"),
}
def read(p):return json.loads(Path(p).read_bytes())
def dump(p,x):Path(p).write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def key(x):return json.dumps(x,sort_keys=True,separators=(",",":"))
def rank_signature(f):
    assert isinstance(f,str) and len(f)==6 and all(f[i] in "23456789TJQKA" and f[i+1] in "cdhs" for i in (0,2,4))
    assert len({f[i:i+2] for i in (0,2,4)})==3
    return "".join(sorted(f[::2]))
def source_receipt():
    runs={str(r):api("/actions/runs/"+str(r)) for r in (RUN,AUDIT)}
    assert all((r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(SOURCE,BRANCH,"completed","success") for r in runs.values())
    a=api("/actions/artifacts/"+str(AID));j=api("/actions/jobs/"+str(JOB))
    assert (a["name"],a["digest"],a["expired"],a["workflow_run"]["id"],a["workflow_run"]["head_sha"])==("B917-legacy-identity","sha256:"+DIGEST,False,RUN,SOURCE)
    assert (j["name"],j["status"],j["conclusion"],j["head_sha"],j["run_id"])==("legacy","completed","success",SOURCE,RUN)
    b=api("/actions/artifacts/"+str(AID)+"/zip",raw=True);assert sha(b)==DIGEST
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        assert z.testzip() is None
        raw=z.read("legacy.json");p=json.loads(raw)
    inv=read(INV);scan=read(SCAN)
    assert p["parent"]==SOURCE and p["coverage"]==coverage()==inv["coverage"]==scan["coverage"]
    assert len(p["closed"])==7 and len(p["remaining"])==68 and len(p["source_rows"])==14
    assert sorted(map(key,p["closed"]+p["remaining"]))==sorted(map(key,inv["remaining_input"]))
    assert p["original_native_denylist"]==scan["original_native_denylist"] and p["targets"]==scan["targets"]
    assert all(x["scope_closed"]==(x["ledger"] in p["closed"]) for x in p["source_rows"])
    assert not p["global_history_clearance"] and not p["can_dispatch_native"]
    assert all(p[k]==0 for k in ("native_solves","cert_promotions","formal_lock_additions","formal_nonpolarized_additions"))
    return b,raw,p,inv,dict(runs=runs,artifact=a,job=j)
def pin(head,path,expected):
    got=git("rev-parse",head+":"+path)
    assert got==expected,(head,path,got,expected)
    return dict(path=path,blob=got)
def index_runs(inv):
    # The persisted inventory schema stores an array, not a dict.
    rows=inv["runs"]
    assert isinstance(rows,list) and all(isinstance(x,dict) and isinstance(x.get("run"),int) for x in rows)
    byid={x["run"]:x for x in rows}
    assert len(byid)==len(rows)
    assert {x["run"] for x in inv["remaining_input"] if x.get("run") is not None}==set(byid)
    return byid

def prepare(out):
    h=guard();cov=coverage();b,raw,p,inv,receipt=source_receipt()
    assert rank_signature("9d7h4c")==rank_signature("4s9c7d")
    assert rank_signature("9d7h4c")!=rank_signature("9d7h5c")
    target_signatures={rank_signature(x["candidate"]["flop"]) for x in p["targets"].values()}
    assert len(target_signatures)==3
    byid=index_runs(inv)
    closed=[];remaining=[];groups={}
    for item in p["remaining"]:
        rid=item.get("run")
        if rid is None:
            remaining.append(item);continue
        row=byid[rid]
        if rid not in STATIC and rid not in MATRICES:
            groups.setdefault(row["workflow_blob"],dict(path=row["workflow"],runs=[]))["runs"].append(rid)
            remaining.append(item);continue
        head=row["head"]
        run=api("/actions/runs/"+str(rid))
        assert (run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"])==(head,BRANCH,row["workflow"],"completed","success")
        jobs=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
        assert jobs["total_count"]==len(jobs["jobs"])==len(row["jobs"])
        assert {(j["id"],j["name"],j["conclusion"]) for j in jobs["jobs"]}=={(j["id"],j["name"],j["conclusion"]) for j in row["jobs"]}
        assert all(j["head_sha"]==head and j["status"]=="completed" for j in jobs["jobs"])
        pins=[];boards=[]
        if rid in STATIC:
            assert row["workflow_blob"]=="829c4e66186c9e8fe6444e83d888c89833dfb31c"
            assert not row["artifacts"] and {j["name"] for j in row["jobs"]}=={"verify"}
            pins.extend([pin(head,row["workflow"],row["workflow_blob"]),pin(head,"tools/hu_b492_medium_tree_ui.cjs","1661b7fcae1b5c030df96940df47607ed2c682bc"),pin(head,"tools/hu_exact_batch_audit.sh","a0c75c3acbe71ac8b504921f1aa44ef467bdcb92")])
            category="PINNED_UI_AND_STATIC_AUDIT_NO_NATIVE_DISPATCH"
        else:
            wf,worker,worker_blob,jobprefix,boards,profile=MATRICES[rid]
            assert row["workflow_blob"]==wf and len(row["artifacts"])==len(boards)
            assert {j["name"] for j in row["jobs"]}=={jobprefix+" ("+f+")" for f in boards}
            assert all(j["conclusion"]=="success" for j in row["jobs"])
            assert not ({rank_signature(f) for f in boards}&target_signatures)
            pins.extend([pin(head,row["workflow"],wf),pin(head,"tools/"+worker,worker_blob)])
            # Retain the original artifact receipts. This closes only a run scope:
            # these immutable workers use their selected flop for root and children.
            for aid in row["artifacts"]:
                a=inv["artifact_metadata"][str(aid)]
                assert a["workflow_run"]["id"]==rid and a["workflow_run"]["head_sha"]==head and a.get("digest")
            category="PINNED_NATIVE_MATRIX_DISJOINT_FLOP_RANKS"
        closed.append(dict(ledger=item,run=rid,head=head,category=category,pins=pins,selected_flops=boards,
            original_artifacts=[inv["artifact_metadata"][str(a)] for a in row["artifacts"]],job_ids=[j["id"] for j in row["jobs"]]))
    assert len(closed)==7 and {x["run"] for x in closed}==STATIC|set(MATRICES)
    assert len(closed)+len(remaining)==68 and len(remaining)==61
    assert sorted(r for g in groups.values() for r in g["runs"])==sorted(x["run"] for x in remaining if x.get("run") is not None)
    assert not PREFIX.exists();PREFIX.mkdir(parents=True)
    out.mkdir(parents=True,exist_ok=False)
    (PREFIX/"b917-legacy.zip").write_bytes(b);(PREFIX/"b917-legacy.json").write_bytes(raw)
    dump(PREFIX/"b917-receipts.json",receipt)
    report=dict(parent=h,coverage=cov,prior_legacy_closed=p["closed"],closed_run_scopes=closed,remaining=remaining,
        grouped_original_run_scopes=groups,target_flop_rank_signatures=sorted(target_signatures),
        original_native_denylist=p["original_native_denylist"],targets=p["targets"],
        global_history_clearance=False,can_dispatch_native=False,native_solves=0,cert_promotions=0,
        formal_lock_additions=0,formal_nonpolarized_additions=0,
        scope="Only pinned run scopes closed; original native jobs retained, no global dedup or rainbow boundary clearance.")
    dump(PREFIX/"run-scope.json",report);dump(out/"run-scope.json",report)
    dump(out/"prepared.json",dict(parent=h,coverage=cov,files={str(f):sha(f.read_bytes()) for f in sorted(PREFIX.iterdir())},
        native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))
    print(json.dumps(dict(legacy_closed=7,run_scopes_closed=len(closed),remaining=len(remaining),clearance=False)))
def publish(out):
    h=guard();p=read(out/"prepared.json")
    assert p["parent"]==h and p["coverage"]==coverage() and not git("diff","--name-only")
    entries=[]
    for path,d in p["files"].items():
        assert Path(path).parent==PREFIX
        b=Path(path).read_bytes();assert sha(b)==d
        expected=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
        actual=api("/git/blobs",dict(content=base64.b64encode(b).decode(),encoding="base64"))["sha"]
        assert actual==expected
        entries.append(dict(path=path,mode="100644",type="blob",sha=actual))
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=entries))["sha"]
    c=api("/git/commits",dict(message="B919 archive B917 legacy identities and pinned disjoint run scopes after B918 schema fix; zero promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=h,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))
if __name__=="__main__":
    {"prepare":prepare,"publish":publish}[sys.argv[1]](Path(sys.argv[2]).resolve())
