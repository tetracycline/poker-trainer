"""B909: retain B908 independent reviews and test next frozen ranks on saved native sources only."""
import base64,hashlib,io,json,os,subprocess,sys,zipfile
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
import hu_b906_btn_original_gate as old
import hu_b847_btn_heldout_turn as prior
from hu_checked_gto_boundary import load_original
from hu_b470_rank73_new_rivers import audit_patterns
from hu_sequential_cfr_reach import accepted

BASE="b7a8edb00d79d970c73e40812f266716ef55a837"
SOURCE="672b8344e62885207913b43f7901bedc3f04ac94"
RUN=45954259355
PREFIX="data/solver_evidence/b909_review_archive/"
PINS={
"8h7h3c":(15177084703,140356968150,"6b615c70ad41437d6cb6825e8017741adf87dc048f602dbd3d43412bb80fbbf2",["2c","4c"]),
"7h6h2c":(15178286332,140356967633,"152e24fa0e70db788fd75239fc9b0ef550202cf994e8ac7bf232dbbf86f75dd3",["3c","4c"]),
"9d7h4c":(15178430904,140356967820,"659bd3c12a64daab21f98cd3b141e7dde3c89be11f11078fef6b713b90a958d2",["2c","2h"]),
}
def dump(p,x):p.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h
def prepare(out):
    h=guard();cov=coverage();out.mkdir(parents=True,exist_ok=False)
    r=api("/actions/runs/"+str(RUN))
    assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(SOURCE,BRANCH,"completed","success")
    root=Path(PREFIX);root.mkdir(parents=True,exist_ok=False);receipt={}
    for flop,(aid,jid,d,turns) in PINS.items():
        a=api("/actions/artifacts/"+str(aid));j=api("/actions/jobs/"+str(jid))
        assert (a["name"],a["digest"],a["expired"])==("B908-review-"+flop,"sha256:"+d,False)
        assert (a["workflow_run"]["id"],a["workflow_run"]["head_sha"],a["workflow_run"]["head_branch"])==(RUN,SOURCE,BRANCH)
        assert (j["run_id"],j["head_sha"],j["name"],j["status"],j["conclusion"])==(RUN,SOURCE,"review ("+flop+")","completed","success")
        raw=api("/actions/artifacts/"+str(aid)+"/zip",raw=True);assert sha(raw)==d
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            rb=z.read("review.json");p=json.loads(rb)
        assert p["flop"]==flop and p["coverage"]==cov
        assert all(p[k]==0 for k in ("native_solves","cert_promotions","formal_lock_additions","formal_nonpolarized_additions"))
        assert [x["turn"] for x in p["replay"]]==turns
        assert all(x["all_three_observations_exact"] and x["exact_two_observation_count"]==2 for x in p["replay"])
        assert not p["history"]["clearance"] and set(p["history"]["candidate_turns"])==set(turns)
        assert all(not v["native_same_geometry_seen"] and not v["same_job_native_seen"] for v in p["history"]["candidate_turns"].values())
        (root/(flop+".zip")).write_bytes(raw);(root/(flop+".json")).write_bytes(rb)
        receipt[flop]=dict(artifact=a,job=j,unresolved=len(p["history"]["unresolved"]))
    dump(root/"receipts.json",dict(run=r,coverage=cov,sources=receipt,scope="Read-only replay; historical clearance not established."))
    dump(out/"prepared.json",dict(parent=h,coverage=cov,files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())},native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))
def publish(out):
    h=guard();p=json.loads((out/"prepared.json").read_bytes())
    assert p["parent"]==h and p["coverage"]==coverage() and not git("diff","--name-only")
    entries=[]
    for path,d in p["files"].items():
        assert path.startswith(PREFIX)
        raw=Path(path).read_bytes();assert sha(raw)==d
        expected=hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()
        actual=api("/git/blobs",dict(content=base64.b64encode(raw).decode(),encoding="base64"))["sha"]
        assert actual==expected
        entries.append(dict(path=path,mode="100644",type="blob",sha=actual))
    tree=api("/git/trees",dict(base_tree=api("/git/commits/"+h)["tree"]["sha"],tree=entries))["sha"]
    c=api("/git/commits",dict(message="B909 archive three B908 source reviews; no promotions",tree=tree,parents=[h]))
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[h]
    rec=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=h,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",rec);print(json.dumps(rec))

def gate(orig,route,flop,turn):
    """Exact common pre-river path; nonmatching geometry or missing menus are explicitly blocked."""
    root=orig["source"]["root"];game=orig["source"]["subgame"];b=orig["public"]
    assert prior.cards(b[:6])==prior.cards(flop) and b[6:]==turn
    assert (game["pot"],game["stack"])==(1100,9475)
    pct=route["pct"]
    if pct not in (33,50,75,100,150):return None,{"status":"UNKNOWN_RENDERED_SIZE"}
    act="b"+str(pct)
    f=next(n["board"] for n in root["nodes"] if len(n["board"])==6)
    def unique(g,line,board,actor):
        found=[n for n in g["nodes"] if (n["line"],n["board"],n["player"])==(line,board,actor)]
        if not found:return None
        n,=found;return n
    steps=[(root,unique(root,"",f,0),"b50",0),(root,unique(root,"b50",f,1),"c",1),
           (game,unique(game,"b50 c/",b,0),"x",0),(game,unique(game,"b50 c/x",b,1),act,1),
           (game,unique(game,"b50 c/x "+act,b,0),"c",0)]
    missing=[i for i,(g,n,a,s) in enumerate(steps) if n is None or a not in n["acts"]]
    if missing:return None,dict(status="ORIGINAL_NODE_OR_SIZE_NOT_EXPORTED",missing=missing)
    for (_,n,_,_),(pot,bets) in zip(steps[:4],[(550,[0,0]),(825,[275,0]),(1100,[0,0]),(1100,[0,0])]):
        assert (n["pot"],n["bets"])==(pot,bets)
    end=steps[-1][1];bet=end["bets"][1]
    assert end["bets"][0]==0 and end["pot"]==1100+bet and bet>0
    actual=(1100+2*bet,9475-bet)
    if abs(actual[1]/actual[0]/route["facts"]["spr"]-1)>.05:
        return None,dict(status="SPR_MISMATCH",actual=actual,model=route["facts"])
    alive=[None,None];counts=[]
    for g,n,a,s in steps:
        x=accepted(n,g["hands"],a)
        alive[s]=x if alive[s] is None else alive[s]&x
        counts.append(len(alive[s]))
    for s in (0,1):alive[s]={h for h in alive[s] if prior.cards(b).isdisjoint(h)}
    alive[1]={h for h in alive[1] if prior.hand_cell("".join(h),b[:6])[0] in route["routes"]["flop"]
        and prior.hand_cell("".join(h),b)[0] in route["routes"]["turn"]}
    return alive,dict(status="EXACT_PRIOR_ACTIONS_REPLAYED",counts=counts,pot=actual[0],stack=actual[1],route_hands=[len(x) for x in alive])

def screen(out,solver,flop):
    guard();cov=coverage();out.mkdir(parents=True,exist_ok=False)
    assert git("-C",str(solver),"rev-parse","HEAD")==old.SOLVER
    py=solver/"postflop/py"
    assert (sha((py/"pipeline.py").read_bytes()),sha((py/"ranges.py").read_bytes()),sha((solver/"inputs/pool_stats.json").read_bytes()))==(old.PIPELINE,old.RANGES,old.POOL)
    sys.path.insert(0,str(py));import pipeline,ranges
    pool=json.loads((solver/"inputs/pool_stats.json").read_bytes())["NL2"]
    raw=subprocess.check_output(["node","tools/hu_b909_btn_routes.cjs"])
    routes=json.loads(raw);assert set(routes)=={"106","107"}
    (out/"routes.json").write_bytes(raw)
    history=git("log","--format=%H%x09%s","--regexp-ignore-case","-G","rank106|rank107|rank[ ]*106|rank[ ]*107|ln-ipfr-r_model-5ce65m|ln-ipfr-r_model-ujl14x",BASE,"--",".github/workflows","tools").splitlines()
    turns,receipts=old.sources(out,flop)
    rows=[]
    for t in sorted(turns["gto"]&turns["exp_ip"]):
        origs={};identities={}
        for mode,(aid,jid,digest) in old.PINS[flop].items():
            orig=load_original(out,aid,dict(name="B524-R8-"+flop+"-"+mode,run=old.RUN,head=old.SOURCE,sha256=digest),"BTN_BB",flop,t,mode,pot=550,stack=9750,pipeline=pipeline,ranges=ranges,flop_line="b50 c")
            origs[mode]=orig;identities[mode]=orig["identity"]
            if mode=="exp_ip":
                src=orig["source"];lock=audit_patterns(src["subgame"],orig["job"],src["manifest"],pool,1)
                assert any(v>0 for k,v in lock["driver_tree_nodes"].items() if k in lock["marginal_targets"])
                identities[mode]["measured_lock_application"]=lock
        for rank,route in routes.items():
            pf=route["parent_facts"]
            if (pf["root"]["spot"],pf["root"]["pot"],pf["root"]["stack"])!=("BTN_BB",5.5,97.5) or abs(pf["spr"]-9475/1100)/pf["spr"]>.05:
                rows.append(dict(rank=rank,turn=t,status="ORIGINAL_PARENT_GEOMETRY_MISMATCH",cert_eligible=False));continue
            live={};gates={}
            for mode,orig in origs.items():live[mode],gates[mode]=gate(orig,route,flop,t)
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
            status="PREFLIGHT_POSITIVE" if possible else "NO_COMMON_PHYSICAL_ROUTE_PAIR_BEFORE_RIVER" if all(s is not None for s in live.values()) else "ORIGINAL_SOURCE_PATH_BLOCKED"
            rows.append(dict(rank=rank,turn=t,identities=identities,gates=gates,status=status,possible_rivers=possible,cert_eligible=False))
    report=dict(flop=flop,coverage=cov,routes_sha256=sha(raw),history_matches=history,source_turns={k:sorted(v) for k,v in turns.items()},receipts=receipts,rows=rows,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="New target-route screen of existing source; not a native run or historical clearance.")
    dump(out/"report.json",report)
    print(json.dumps(dict(flop=flop,coverage=cov,rows=[dict(rank=r["rank"],turn=r["turn"],status=r["status"],gates={k:v["status"] for k,v in r.get("gates",{}).items()},possible_rivers=len(r.get("possible_rivers",{}))) for r in rows])))
    for p in out.glob("*.zip"):p.unlink()
if __name__=="__main__":
    m=sys.argv[1];out=Path(sys.argv[2]).resolve()
    if m=="screen":screen(out,Path(sys.argv[3]).resolve(),sys.argv[4])
    else:{"prepare":prepare,"publish":publish}[m](out)
