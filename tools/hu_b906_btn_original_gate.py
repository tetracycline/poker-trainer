"""B906: one-shot B905 receipt recovery and untouched B524 fixed-turn gates.
No native solver, registry change, or ref mutation. Detached archive only.
"""
import io,json,os,subprocess,sys,zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
from hu_b467_river_source_gate import json_bytes
from hu_b483_locked_medium import PIPELINE,POOL,RANGES
from hu_b463_rank45_gate import SOLVER
from hu_checked_gto_boundary import load_original
from hu_b470_rank73_new_rivers import audit_patterns
import hu_b847_btn_heldout_turn as prior
import hu_b905_bb_archive_plan as inventory

BASE="af5e067d61a1b2a1344aaa87fdd89545c30c3fff"
RUN=45118153398
SOURCE="d1b22cd54e8c5391f2ee6d9411488923979ac797"
PINS={
"7d5c4c":{"gto":(14792312789,137505625125,"8aeec8c25159cde3db0b15046bddee1bd1fa3f71b4b92851b25918879c392852"),"exp_ip":(14793231393,137505624829,"5b311583db3309721378332b6c57f8e9e9a98e223d04bf44f4d23681ed9d9d96")},
"5h4h3s":{"gto":(14792264343,137505625094,"63bbcdaa03624c3c37e3e3de35bdcb6ae1c50b12116d1423c5de5d34f36d58"),"exp_ip":(14793380647,137505625092,"257e7a84b611c236ba68170c341442ea9aaf9257ce3364afe188f706db38a728")},
"8h7h5c":{"gto":(14792029853,137505625136,"d823ed2e55e7d968ab4a682d004b1bc691700ad8cdf2f9b9003147e4bc3ca3e4"),"exp_ip":(14793400856,137505625095,"c0d6f34a5a1493fc3980f16e7d693b1118052d8beb5d119a9854a7a52f5d70bc")},
}
CHANGED={"tools/hu_b906_btn_original_gate.py",".github/workflows/nl2-hu-b906-btn-original-gate.yml","docs/NL2_HU_B906_BTN_ORIGINAL_GATE.md"}
def dump(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
def read(p):return json.loads(Path(p).read_bytes())
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert p["state"]=="open" and p["draft"] and not p["merged"]
    assert (p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==(REPO,BRANCH,h)
    assert set(git("diff","--name-only",BASE,h).splitlines())==CHANGED
    return h
def sources(out,flop):
    turns={}; receipts={}
    for mode,(aid,jid,digest) in PINS[flop].items():
        a=api("/actions/artifacts/"+str(aid));j=api("/actions/jobs/"+str(jid))
        assert (a["id"],a["name"],a["digest"],a["expired"])==(aid,"B524-R8-"+flop+"-"+mode,"sha256:"+digest,False)
        assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"],a["workflow_run"]["head_branch"])==(RUN,SOURCE,BRANCH)
        assert (j["id"],j["run_id"],j["name"],j["status"],j["conclusion"])==(jid,RUN,"fresh ("+flop+", "+mode+")","completed","success")
        raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True);assert sha(raw)==digest
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            mf,=[n for n in z.namelist() if n.startswith(("evidence/","trainer/evidence/")) and n.endswith(".json") and not n.endswith("pool_stats.json")]
            m=json.loads(z.read(mf))
            assert (m["spot"],m["version"],m["failures"])==("BTN_BB",mode,[])
            turns[mode]={c["turn"] for c in m["cases"] if c["line"]=="b50 c" and (m.get("flop") or c["flop"])==flop}
        dump(out/(str(aid)+".json"),a);(out/(str(aid)+".zip")).write_bytes(raw)
        receipts[mode]={"artifact":a,"job":j}
    return turns,receipts
def screen(out,solver,flop):
    guard();cov=coverage();out.mkdir(parents=True,exist_ok=False)
    assert git("-C",str(solver),"rev-parse","HEAD")==SOLVER
    py=solver/"postflop/py"
    assert (sha((py/"pipeline.py").read_bytes()),sha((py/"ranges.py").read_bytes()),sha((solver/"inputs/pool_stats.json").read_bytes()))==(PIPELINE,RANGES,POOL)
    sys.path.insert(0,str(py));import pipeline,ranges
    pool=read(solver/"inputs/pool_stats.json")["NL2"]
    turns,receipts=sources(out,flop)
    old=read("data/nl2_hu_b720_summary.json")
    assert old["distinct_positive_flops_by_rank"]=={"104":0,"105":0}
    excluded={x["turn"] for x in old["workers"] if x["flop"]==flop}
    # B847/B850 studied 6s5h4d/Kd, deliberately not in this batch.
    # Inspect complete dispatch ancestry before interpreting any additional source.
    inventory.PARENT=BASE
    history=inventory.inventory(flop)
    routes_raw=subprocess.check_output(["node","tools/hu_b713_btn_lead_routes.cjs"])
    route=json.loads(routes_raw)["105"]
    assert (route["actor"],route["spot"],route["pct"],route["line"],route["river_pot"],route["river_stack"])==(1,"BTN_BB",50,"b50 c/x b50 c/x",2200,8925)
    assert abs(8925/2200/route["spr"]-1)<=.05
    rows=[]
    prior.FLOP=flop
    for t in sorted(turns["gto"]&turns["exp_ip"]-excluded):
        prior.TURN=t;live={};gates={};identities={}
        for mode,(aid,jid,digest) in PINS[flop].items():
            orig=load_original(out,aid,dict(name="B524-R8-"+flop+"-"+mode,run=RUN,head=SOURCE,sha256=digest),"BTN_BB",flop,t,mode,pot=550,stack=9750,pipeline=pipeline,ranges=ranges,flop_line="b50 c")
            assert orig["job"]["turn_ip"]=="50%,100%"
            identities[mode]=orig["identity"]
            if mode=="exp_ip":
                src=orig["source"];lock=audit_patterns(src["subgame"],orig["job"],src["manifest"],pool,1)
                assert any(v>0 for k,v in lock["driver_tree_nodes"].items() if k in lock["marginal_targets"])
                identities[mode]["measured_lock_application"]=lock
            live[mode],gates[mode]=prior.policy_gate(orig,route)
        possible={}
        if all(s is not None for s in live.values()):
            both=[live["gto"][s]&live["exp_ip"][s] for s in (0,1)]
            for river in prior.DECK:
                b=flop+t
                if river in prior.cards(b):continue
                pairs=[]
                for h in sorted(both[1]):
                    if river in h or prior.hand_cell("".join(h),b+river)[0] not in route["routes"]["river"]:continue
                    for v in sorted(both[0]):
                        if river not in v and set(h).isdisjoint(v):pairs.append(["".join(h),"".join(v)])
                if pairs:possible[river]={"pairs":len(pairs),"first_pair":pairs[0]}
        rows.append(dict(turn=t,identities=identities,gates=gates,rank104="B75_NOT_IN_ORIGINAL_MENU",rank105="SOURCE_NODE_MISSING" if any(s is None for s in live.values()) else "PREFLIGHT_POSITIVE" if possible else "NO_COMMON_PHYSICAL_ROUTE_PAIR_BEFORE_RIVER",possible_rivers=possible,cert_eligible=False))
    # The report is a prior-action screen; not a river or new native certificate.
    report=dict(flop=flop,coverage=cov,prior_excluded=sorted(excluded),source_turns={k:sorted(v) for k,v in turns.items()},rows=rows,history=history,receipts=receipts,route_sha256=sha(routes_raw),native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0)
    dump(out/"report.json",report)
    print(json.dumps({k:report[k] for k in ("flop","coverage","source_turns","prior_excluded","native_solves","cert_promotions")}))
    print(json.dumps([{"turn":r["turn"],"rank104":r["rank104"],"rank105":r["rank105"],"possible_rivers":len(r["possible_rivers"])} for r in rows]))
    # Source ZIPs remain in original authenticated artifact locations; retain report only here.
    for p in out.glob("*.zip"):p.unlink()
def recover(out):
    h=guard();cov=coverage();out.mkdir(parents=True,exist_ok=False)
    # One snapshot of already dispatched B905, never poll or wait.
    r=api("/actions/runs?head_sha="+BASE+"&per_page=100")
    assert r["total_count"]<=100
    runs=[x for x in r["workflow_runs"] if x["head_sha"]==BASE and x["head_branch"]==BRANCH]
    snap=dict(coverage=cov,runs=[{k:x.get(k) for k in ("id","name","status","conclusion","html_url","head_sha","path")} for x in runs],plans=[],archive=None)
    for run in runs:
        if run["status"]!="completed" or "nl2-hu-b905-bb-archive-plan.yml" not in run.get("path",""):continue
        jobs=api("/actions/runs/"+str(run["id"])+"/jobs?per_page=100")
        arts=api("/actions/runs/"+str(run["id"])+"/artifacts?per_page=100")
        assert jobs["total_count"]<=100 and arts["total_count"]<=100
        snap["jobs"]=[{k:j.get(k) for k in ("id","name","status","conclusion","html_url")} for j in jobs["jobs"]]
        for a in arts["artifacts"]:
            if a["expired"]:continue
            name=a["name"]
            if not (name.startswith("B905-rank92-plan-") or name=="B905-detached-B904-archive"):continue
            assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"])==(run["id"],BASE)
            raw=api("/actions/artifacts/"+str(a["id"])+"/zip",raw=True);assert "sha256:"+sha(raw)==a["digest"]
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                assert z.testzip() is None
                if name.startswith("B905-rank92-plan-"):
                    p=json.loads(z.read("plan.json"));assert p["coverage"]==cov and not p["native_solves"] and not p["cert_promotions"]
                    assert not p["historical_inventory"]["clearance"] and all(not x["can_dispatch_native"] for x in p["plans"])
                    for x in p["plans"]:assert sha(z.read(x["turn"]+"-gto-job.json"))==x["job_sha256"]
                    snap["plans"].append(dict(artifact_id=a["id"],sha256=sha(raw),plan=p))
                else:
                    j,=[j for j in jobs["jobs"] if j["name"]=="archive"]
                    assert (j["status"],j["conclusion"])==("completed","success")
                    p=json.loads(z.read("detached-candidate.json"))
                    assert (p["parent"],p["expected_sha"],p["coverage"],p["candidate_only"],p["ref_updated"],p["full_audit_completed"])==(BASE,BASE,cov,True,False,True)
                    assert p["native_solves"]==p["cert_promotions"]==0
                    c=api("/git/commits/"+p["candidate_commit"])
                    assert [x["sha"] for x in c["parents"]]==[BASE] and c["tree"]["sha"]==p["candidate_tree"]
                    entries=p["blobs"]; paths={x["path"] for x in entries}
                    assert len(entries)==13 and paths==set(p["files"]) and all(x.startswith(inventory.PREFIX) for x in paths)
                    diff=api("/compare/"+BASE+"..."+p["candidate_commit"])
                    assert diff["ahead_by"]==1 and diff["behind_by"]==0 and {x["filename"] for x in diff["files"]}==paths
                    assert all(x["status"]=="added" for x in diff["files"])
                    for e in entries:
                        b=api("/git/blobs/"+e["sha"])
                        import base64
                        assert sha(base64.b64decode(b["content"]))==p["files"][e["path"]]
                    snap["archive"]=dict(artifact_id=a["id"],sha256=sha(raw),candidate=p)
    dump(out/"snapshot.json",snap)
    print(json.dumps(dict(runs=snap["runs"],plan_count=len(snap["plans"]),archive_candidate=bool(snap["archive"]))))
def reanchor(out):
    h=guard();s=read(out/"snapshot.json")
    if not s["archive"]:return
    p=s["archive"]["candidate"]
    assert coverage()==s["coverage"] and not git("diff","--name-only")
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=p["blobs"]))["sha"]
    c=api("/git/commits",dict(message="B906 preserve verified B905 archived B904 evidence; no promotions",tree=tree,parents=[h]))
    assert [x["sha"] for x in c["parents"]]==[h] and c["tree"]["sha"]==tree
    dump(out/"detached-candidate.json",dict(expected_sha=h,candidate_commit=c["sha"],candidate_tree=tree,source_candidate=p["candidate_commit"],files=p["files"],coverage=s["coverage"],full_audit_completed=True,candidate_only=True,ref_updated=False,native_solves=0,cert_promotions=0))
    print(json.dumps(read(out/"detached-candidate.json")))
if __name__=="__main__":
    m=sys.argv[1];out=Path(sys.argv[2]).resolve()
    if m=="screen":screen(out,Path(sys.argv[3]).resolve(),sys.argv[4])
    else:{"recover":recover,"reanchor":reanchor}[m](out)
