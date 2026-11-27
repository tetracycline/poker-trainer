"""B913: distinguish historical read-only wrapper runs from native originals.
Keep original source jobs/turns in the denylist. No native dispatch or promotion.
"""
import json, os, sys, zipfile, io
from pathlib import Path
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
from hu_b895_archive_r158 import coverage
import hu_b911_b33_archive as publisher

BASE="46ccb70844ef89a241d0d4669bfa1126d05e5374"
PREFIX="data/solver_evidence/b913_wrapper_history/"
LEDGER="data/solver_evidence/b912_repair_history/narrowed-history.json"
PINS={
  45936923715:("af5e067d61a1b2a1344aaa87fdd89545c30c3fff","failure","nl2-hu-b905-bb-archive-plan.yml","5ffccbec0339e3fa487e9b5b7073d403914213bf",{"hu_b905_bb_archive_plan.py":"aaa73fea099b4c512b54fc44f26b55dea39d64fc"},"PLAN_AND_REPLAY_NO_NATIVE",{"plan (7h6h2c)":"failure","plan (9d7h4c)":"failure","plan (8h7h3c)":"success","archive":"success"}),
  45948668066:("778afa98de3bab6eba25d763c112b453f18c0fc8","success","nl2-hu-b907-readonly-gate.yml","c2bbed85e439541c3f9c08bd7d334c9202f0469f",{"hu_b907_readonly_gate.py":"df802da9560cf899fb6ac468338412810e7bba7a","hu_b905_bb_archive_plan.py":"aaa73fea099b4c512b54fc44f26b55dea39d64fc"},"READ_ONLY_REPAIR_NO_NATIVE",{"repair (bb, 7h6h2c)":"success","repair (bb, 9d7h4c)":"success","repair (btn, 5h4h3s)":"success","repair (btn, 8h7h5c)":"success","archive":"success","receipt":"success"}),
  45542907477:("da7915dbc0c176ffe7c7267e980b123bae3c6121","success","nl2-hu-b845-originals.yml","7eaf3c8dfb131dd366ef6446245b5ca24fec25b0",{"hu_b845_originals.py":"324e5e2b9137fc87fcb9d35f04e3aca5c988b42c","hu_b844_bb_two_tone.py":None,"hu_b711_bb_lead_rivers.py":"7ba3ce3a3120378cf8de8c252eda0298365714e3"},"REPLAY_EXISTING_B844_ORIGINALS_ONLY",{"replay-audit-candidate":"success"}),
  45325878184:("910082029d81d3223bbe8fd5e62df38fd45c5e4f","success","nl2-hu-b715-bb-lead-negatives.yml","c70a1c385dc5bbee1a7595ecec069e69221037f5",{"hu_b715_publish.py":"804d7a1c13720d5529ff32acff6ea7bb0df40135"},"REPLAY_EXISTING_B711_ORIGINALS_ONLY",{"verify":"success"}),
}
TARGETS={"7h6h2c":{45936923715,45542907477},"8h7h3c":{45948668066,45542907477},"9d7h4c":{45936923715,45325878184}}
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def dump(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
def read(p):return json.loads(Path(p).read_bytes())
def check_original(row,flop):
    raw=(Path("data/solver_evidence")/row["archive"]).read_bytes()
    assert sha(raw)==row["archive_sha256"]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        proof=json.loads(z.read("proof.json"))
        assert proof["flop"]==flop
        files={n:sha(z.read(n)) for n in z.namelist() if n.endswith("/job.json")}
        assert "flop/job.json" in files
        assert all(n in z.namelist() for n in proof["native_file_sha256"])
        assert all(sha(z.read(n))==d for n,d in proof["native_file_sha256"].items())
    return dict(flop=flop,archive=row["archive"],archive_sha256=row["archive_sha256"],native_job_sha256=files,original_source_run=row.get("source_run"),classification="RETAIN_ORIGINAL_NATIVE_JOBS_IN_DENYLIST")
def prepare(out):
    h=guard();cov=coverage()
    assert git("hash-object",LEDGER)=="3ba4f20d1a05ba98959df5376a71eab1d38a05a9"
    old=read(LEDGER);assert old["coverage"]==cov
    root=Path(PREFIX);root.mkdir(parents=True,exist_ok=False);out.mkdir(parents=True,exist_ok=False)
    evidence={}
    for rid,(head,conclusion,wf,wh,scripts,category,jobs) in PINS.items():
        run=api("/actions/runs/"+str(rid))
        assert (run["head_sha"],run["head_branch"],run["status"],run["conclusion"],run["path"])==(head,BRANCH,"completed",conclusion,".github/workflows/"+wf)
        js=api("/actions/runs/"+str(rid)+"/jobs?per_page=100")
        assert js["total_count"]==len(js["jobs"])==len(jobs)
        assert {j["name"]:j["conclusion"] for j in js["jobs"]}==jobs
        assert all(j["head_sha"]==head and j["status"]=="completed" for j in js["jobs"])
        pins={".github/workflows/"+wf:wh,**{"tools/"+k:v for k,v in scripts.items()}}
        source={}
        for path,pin in pins.items():
            blob=git("rev-parse",head+":"+path)
            if pin is not None:assert blob==pin,(path,blob,pin)
            raw=git("show",head+":"+path)
            source[path]=dict(blob=blob,reviewed_text=raw)
        evidence[str(rid)]=dict(category=category,run=run,jobs=js["jobs"],immutable_sources=source)
    # B845/B715 replay wrappers do not introduce a new job identity. Their
    # original native inputs are NOT cleared; retain every original job SHA.
    b845=read("data/solver_evidence/partial/b845_b844_original_observations.json")
    assert b845["result"]["native_repeated"]==0 and b845["result"]["source_run"]==45535807925
    b715=read("data/nl2_hu_b715_summary.json")
    assert b715["native_solves_repeated"]==0 and b715["source_run"]==45324358830
    orig={}
    for row in b845["observations"]:
        f=row["flop"]
        if f in ("7h6h2c","8h7h3c"):
            orig[f]=check_original(dict(row,source_run=45535807925),f)
    for row in read("data/nl2_hu_b715_results.json"):
        if row["flop"]=="9d7h4c":orig["9d7h4c"]=check_original(row,"9d7h4c")
    assert set(orig)==set(TARGETS)
    result={}
    for f,wanted in TARGETS.items():
        remaining=old["rows"][f]["remaining"]
        removed=[x for x in remaining if x.get("run") in wanted]
        left=[x for x in remaining if x.get("run") not in wanted]
        assert {x["run"] for x in removed}==wanted and len(removed)==len(wanted)
        result[f]=dict(before=len(remaining),classified=removed,remaining=left,original_native_denylist=orig[f],clearance=False,can_dispatch_native=False,scope="Wrapper run records only; original native identities and other inventories remain blocked.")
    dump(root/"wrapper-receipts.json",dict(coverage=cov,runs=evidence,native_solves=0,cert_promotions=0))
    dump(root/"narrowed-history.json",dict(coverage=cov,rows=result,scope="No global clearance, no held-out reconstruction waiver, no native dispatch; original native job SHAs remain excluded.",native_solves=0,cert_promotions=0))
    dump(out/"prepared.json",dict(parent=h,coverage=cov,files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())},native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))
    print(json.dumps({f:dict(before=x["before"],remaining=len(x["remaining"]),original_native_jobs=len(x["original_native_denylist"]["native_job_sha256"])) for f,x in result.items()}))
if __name__=="__main__":
    action=sys.argv[1];out=Path(sys.argv[2]).resolve()
    if action=="prepare":prepare(out)
    elif action=="publish":
        publisher.guard=guard;publisher.PREFIX=PREFIX
        publisher.publish(out)
    else:raise ValueError(action)
