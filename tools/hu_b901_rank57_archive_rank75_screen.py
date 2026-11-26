"""B901: preserve authenticated B900 rank57 source diagnostic and preflight
untested fourth-suit turns on the existing B846 rank75 root. No native solve."""
import base64, hashlib, io, json, os, sys, zipfile, subprocess
from pathlib import Path
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
from hu_b895_archive_r158 import coverage
import hu_b900_priority_source_diagnostics as prev
import hu_b766_rank75_chance_turns as chance
from hu_b467_river_source_gate import compact
PARENT="475cf16ab21bcaae9132ab424a2eb66ddb3101df"
HEAD900="e0102938f76411c725fe6bbd57a88b3fb485354f"
RUN=45907839357
AUDIT=45907839252
ART=15159240574
DIGEST="e0d3d68569e1c68f124fae79f2f2fb6e53d9130573ebd733b061298a8753da3c"
PREFIX="data/solver_evidence/b901_rank57_diagnostics/"
def dump(p,x):
    p.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==PARENT
    p=api("/pulls/2")
    assert p["state"]=="open" and p["draft"] and not p["merged"]
    assert (p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==(REPO,BRANCH,h)
    return h
def archive(out):
    h=guard();cov=coverage()
    assert not git("status","--porcelain")
    runs={}
    for rid in (RUN,AUDIT):
        r=api("/actions/runs/"+str(rid))
        assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(HEAD900,BRANCH,"completed","success")
        runs[str(rid)]=r
    a=api("/actions/artifacts/"+str(ART))
    assert not a["expired"] and a["digest"]=="sha256:"+DIGEST
    assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"])==(RUN,HEAD900)
    raw=api("/actions/artifacts/"+str(ART)+"/zip",raw=True)
    assert sha(raw)==DIGEST
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        r=prev.read(z,"rank57-diagnostic.json")
    assert r["rank"]==57 and r["coverage"]==cov
    assert r["native_solves"]==r["cert_promotions"]==0
    assert {x["flop"] for x in r["rows"]}==set(prev.R57)
    for row in r["rows"]:
        spec=prev.R57[row["flop"]]
        assert row["source_artifact_sha256"]==spec[2]
        assert [t["turn"] for t in row["turns"]]==spec[3]
        assert all(t["failure_stage"]=="GTO_DISPLAYED_ACTION_ZERO" and t["shared_hero_boards"]==0 for t in row["turns"])
    root=Path(PREFIX);root.mkdir(parents=True,exist_ok=False)
    out.mkdir(parents=True,exist_ok=False)
    (root/"b900-diagnostic.zip").write_bytes(raw)
    dump(root/"diagnostic.json",r)
    meta={}
    for flop,spec in prev.R57.items():
        native,a0=prev.artifact(spec)
        with zipfile.ZipFile(io.BytesIO(native)) as z:
            assert z.testzip() is None
            p=prev.read(z,"proof.json")
            assert (p["rank"],p["flop"])==(57,flop)
            assert p["root_sha256"]==next(q["root_sha256"] for q in r["rows"] if q["flop"]==flop)
        name=flop+".zip";(root/name).write_bytes(native);meta[name]=a0
    dump(root/"receipts.json",dict(runs=runs,diagnostic_artifact=a,source_artifacts=meta))
    files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())}
    dump(out/"prepared.json",dict(parent=h,files=files,coverage=cov,native_solves=0,cert_promotions=0))
    print(json.dumps(dict(rank=57,negative_fixed_turns=sum(len(x["turns"]) for x in r["rows"]),files=files,coverage=cov)))
def upload(out):
    h=guard();p=json.loads((out/"prepared.json").read_bytes())
    assert p["parent"]==h and p["native_solves"]==p["cert_promotions"]==0 and p["coverage"]==coverage()
    assert not git("diff","--name-only")
    entries=[]
    for path,d in p["files"].items():
        assert path.startswith(PREFIX)
        b=Path(path).read_bytes();assert sha(b)==d
        expected=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
        got=api("/git/blobs",{"content":base64.b64encode(b).decode(),"encoding":"base64"})["sha"]
        assert got==expected
        entries.append(dict(path=path,mode="100644",type="blob",sha=got))
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=entries))["sha"]
    c=api("/git/commits",dict(message="B901 archive authenticated B900 rank57 diagnostics and four original native sources; no CERT promotion",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    receipt=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=h,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",receipt);print(json.dumps(receipt))
def screen(out):
    guard();cov=coverage()
    evidence=Path("data/solver_evidence")
    receipt=json.loads(Path("data/nl2_hu_b849_source_receipts.json").read_bytes())
    assert (receipt["run"]["id"],receipt["run"]["head_sha"])==(45550112376,"d1a61d541d2ab12d4ae5cd01b5c31b3791b21cdd")
    assert receipt["successful_job"]["id"]==138988999309 and receipt["successful_job"]["conclusion"]=="success"
    names=("NL2_B846_R75_TD8D5D.zip","NL2_B846_R75_TD8D5D_ROOT.zip")
    ids=(14992699643,14992964370)
    for name,aid in zip(names,ids,strict=True):
        a,=[a for a in receipt["artifacts"] if a["id"]==aid]
        assert sha((evidence/name).read_bytes())==a["digest"].removeprefix("sha256:")
    with zipfile.ZipFile(evidence/names[0]) as z,zipfile.ZipFile(evidence/names[1]) as cp:
        p=json.loads(z.read("proof.json"));pin=json.loads(cp.read("checkpoint.json"))
        rb=z.read("flop/result.json");jb=z.read("flop/job.json")
        assert rb==cp.read("flop/result.json") and jb==cp.read("flop/job.json")
        assert p["origin"]==pin and sha(rb)==pin["root_sha256"] and sha(jb)==pin["root_job_sha256"]
        assert p["positive_distinct_flops"]==0 and p["locked_public_boards"]==0
        assert (p["rank"],p["flop"])==(75,"Td8d5d")
        for row in p["turns"]:
            for mode,pol in row["policies"].items():
                assert sha(z.read(row["turn"]+"-"+mode+"/result.json"))==pol["result_sha256"]
                assert sha(z.read(row["turn"]+"-"+mode+"/job.json"))==pol["job_sha256"]
    root=json.loads(rb);job=json.loads(jb)
    assert (root["flop"],root["pot"],root["stack"],job["pot"],job["stack"])==("Td8d5d",1650,9250,1650,9250)
    assert not root["info"].get("lock_stats") and 0<=root["info"]["gto_expl_pct"]<=.5
    assert job["flop_oop"]==job["flop_ip"]=="33%,50%,75%,100%"
    observed={n["board"][-2:]:n for n in root["nodes"] if n["line"]=="b33 c/"}
    old=list(p["preregistered_turns"])
    assert set(observed)==set(old) and all(sha(compact(n))==pin["raw_boundaries"][t] for t,n in observed.items())
    # Candidate list frozen in rank order, excluding all previous fixed turns
    # and dead cards; no native driver. Historical global dedup is separately
    # required before any future dispatch.
    candidates=[r+"d" for r in "23456789TJQKA" if r+"d" not in set(old)|{"Td","8d","5d"}]
    masks={t:chance.blocked(root["hands"],t) for t in old+candidates}
    held=[]
    for t in old:
        weights=chance.reconstruct(root,observed,masks,[u for u in old if u!=t],t)
        assert all(chance.weight_bytes(x)==chance.weight_bytes(y) for x,y in zip(weights,observed[t]["wr"],strict=True))
        held.append(t)
    route=json.loads(subprocess.check_output(["node","tools/hu_b674_threebet_call_routes.cjs"]))["75"]
    native=chance.native;checked=chance.checked
    assert (route["id"],route["line"],route["seat"],route["turn_pot"],route["turn_stack"])==(native.MODEL,native.LINE,1,2740,8705)
    assert route["routes"]["mono"]==dict(parents=["DRAW","WDRAW"],decisions={"DRAW":"下注 ½","WDRAW":"過"})
    rows=[]
    for t in candidates:
        weights=chance.reconstruct(root,observed,masks,old,t)
        source=chance.range_input(root,t,weights)
        gate=checked.checked_gate(source,t,route)
        weak=[h for h in gate["rendered_hands"] if native.hcls(h,root["flop"]+t)=="WDRAW"]
        rows.append(dict(turn=t,root_gate=gate,weak_draw_hands=weak,raw_seat_sha256=[sha(chance.weight_bytes(x)) for x in weights],can_dispatch_native=False))
    out.mkdir(parents=True,exist_ok=False)
    report=dict(rank=75,flop=root["flop"],root_sha256=pin["root_sha256"],root_job_sha256=pin["root_job_sha256"],heldout_binary64_replay=held,prior_fixed_turns=old,rows=rows,coverage=cov,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,limitation="Raw range and UI gate only. Full historical dispatch dedup, pinned solver full-job byte replay, and native dual-policy same-deal evidence remain mandatory. No root rerun.")
    dump(out/"rank75-screen.json",report)
    print(json.dumps(dict(rank=75,flop=root["flop"],heldout=held,candidate_turns=candidates,root_gate_positive=[r["turn"] for r in rows if r["weak_draw_hands"]],native_solves=0)))
if __name__=="__main__":
    {"archive":archive,"upload":upload,"screen":screen}[sys.argv[1]](Path(sys.argv[2]).resolve())
