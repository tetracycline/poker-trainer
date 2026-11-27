"""B910: correct the B909 wrong-parent/wrong-price route. Use B524 *flop* roots only.
No new native jobs, no turn weights inferred from a different price, no certification.
"""
import json, os, subprocess, sys
from pathlib import Path
from hu_b886_detached_price_candidate import api,git,sha,REPO,BRANCH
from hu_b895_archive_r158 import coverage
import hu_b906_btn_original_gate as old
import hu_b847_btn_heldout_turn as prior
from hu_checked_gto_boundary import load_original
from hu_b470_rank73_new_rivers import audit_patterns
from hu_sequential_cfr_reach import accepted
from hu_b580_rank27_rivers import suit_isomorphism_class

BASE="e2a1633ab278f465222545f4621093ad69ee6555"
FAILED_RUN=45961341505
def dump(p,x):p.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
def guard():
    h=os.environ["GITHUB_SHA"];p=api("/pulls/2")
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==BASE
    assert (p["state"],p["draft"],p["merged"],p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==("open",True,False,REPO,BRANCH,h)
    return h

def gate(root,flop,route):
    f,={n["board"] for n in root["nodes"] if n["line"]==""}
    assert prior.cards(f)==prior.cards(flop) and (root["pot"],root["stack"])==(550,9750)
    def one(line,actor):
        ns=[n for n in root["nodes"] if (n["line"],n["board"],n["player"])==(line,f,actor)]
        if not ns:return None
        n,=ns;return n
    a,b=one("",0),one("b33",1)
    if a is None or b is None or "b33" not in a["acts"] or "c" not in b["acts"]:
        return None,dict(status="B33_FLOP_ACTION_NOT_EXPORTED",root_acts=a["acts"] if a else [],facing_acts=b["acts"] if b else [])
    assert (a["pot"],a["bets"],b["pot"],b["bets"])==(550,[0,0],732,[182,0])
    live=[accepted(a,root["hands"],"b33"),accepted(b,root["hands"],"c")]
    live=[{h for h in s if prior.cards(f).isdisjoint(h)} for s in live]
    live[1]={h for h in live[1] if prior.hand_cell("".join(h),f)[0] in route["routes"]["flop"]}
    # B524 explicitly exported b50 c boundaries, not b33 c. Do not reuse b50 weights.
    return live,dict(status="B33_FLOP_ONLY",board=f,counts=[len(s) for s in live],exported_b33_boundaries=sorted(n["board"] for n in root["nodes"] if n["line"]=="b33 c/"))

def witness(flop,turn,both,route):
    b=flop+turn;dead=prior.cards(b)
    opp=sorted(h for h in both[0] if dead.isdisjoint(h))
    heroes=sorted(h for h in both[1] if dead.isdisjoint(h) and prior.hand_cell("".join(h),b)[0] in route["routes"]["turn"])
    for h in heroes:
        vs=[v for v in opp if set(h).isdisjoint(v)]
        if not vs:continue
        for river in prior.DECK:
            if river in dead or river in h:continue
            cls=prior.hand_cell("".join(h),b+river)[0]
            if cls not in route["routes"]["river"]:continue
            v=next((v for v in vs if river not in v),None)
            if v is not None:return dict(hero="".join(h),villain="".join(v),river=river,river_cell=cls)
    return None

def main(out,solver,flop):
    h=guard();cov=coverage();out.mkdir(parents=True,exist_ok=False)
    assert git("-C",str(solver),"rev-parse","HEAD")==old.SOLVER
    py=solver/"postflop/py"
    assert (sha((py/"pipeline.py").read_bytes()),sha((py/"ranges.py").read_bytes()),sha((solver/"inputs/pool_stats.json").read_bytes()))==(old.PIPELINE,old.RANGES,old.POOL)
    sys.path.insert(0,str(py));import pipeline,ranges
    pool=json.loads((solver/"inputs/pool_stats.json").read_bytes())["NL2"]
    raw=subprocess.check_output(["node","tools/hu_b910_btn_exact_routes.cjs"])
    routes=json.loads(raw);assert set(routes)=={"106","107"}
    (out/"routes.json").write_bytes(raw)
    turns,receipts=old.sources(out,flop)
    roots={};identities={}
    for mode,(aid,jid,digest) in old.PINS[flop].items():
        # Authenticate the already saved b50 subgame only as provenance of its full-menu flop root.
        if not turns[mode]:continue
        t=sorted(turns[mode])[0]
        orig=load_original(out,aid,dict(name="B524-R8-"+flop+"-"+mode,run=old.RUN,head=old.SOURCE,sha256=digest),"BTN_BB",flop,t,mode,pot=550,stack=9750,pipeline=pipeline,ranges=ranges,flop_line="b50 c")
        identities[mode]=orig["identity"];assert identities[mode]["flop_oop_menu"]=="33%,50%,75%,100%"
        roots[mode]=orig["source"]["root"]
        if mode=="exp_ip":
            src=orig["source"];lock=audit_patterns(src["subgame"],orig["job"],src["manifest"],pool,1)
            assert any(v>0 for k,v in lock["driver_tree_nodes"].items() if k in lock["marginal_targets"])
            assert roots[mode]["info"]["lock_stats"]
            identities[mode]["authenticated_b50_source_lock"]=lock
    hist=git("log","--format=%H%x09%s","--regexp-ignore-case","-G",flop+"|rank106|rank107|ln-ipfr-r_model-5ce65m|ln-ipfr-r_model-ujl14x",BASE,"--",".github/workflows","tools").splitlines()
    rows=[]
    for rank,route in routes.items():
        live={};gates={}
        for mode,root in roots.items():live[mode],gates[mode]=gate(root,flop,route)
        row=dict(rank=rank,flop=flop,gates=gates,possible_turns={},cert_eligible=False,can_dispatch_native=False)
        if set(live)!={"gto","exp_ip"} or any(s is None for s in live.values()):
            row["status"]="ORIGINAL_B33_FLOP_SOURCE_INCOMPLETE"
        else:
            both=[live["gto"][s]&live["exp_ip"][s] for s in (0,1)]
            row["common_flop_counts"]=[len(s) for s in both]
            row["common_flop_pairs"]=sum(set(h).isdisjoint(v) for h in both[1] for v in both[0])
            for t in prior.DECK:
                if t in prior.cards(flop):continue
                w=witness(flop,t,both,route)
                if w:row["possible_turns"][t]=w
            row["status"]="FLOP_ONLY_UPPER_BOUND_POSITIVE_NO_B33_BOUNDARY" if row["possible_turns"] else "NO_COMMON_FLOP_OR_CLASS_ROUTE_PAIR_ON_THIS_ROOT"
        rows.append(row)
    dump(out/"report.json",dict(flop=flop,coverage=cov,identities=identities,receipts=receipts,source_turns={k:sorted(v) for k,v in turns.items()},routes_sha256=sha(raw),history_matches=hist,rows=rows,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="B33 full-menu flop actor masks only. No b50 boundary substitution. Upper bound is not turn/river CFR, independent historical clearance or certificate. Negative only for this original pair."))
    print(json.dumps(dict(flop=flop,coverage=cov,rows=[dict(rank=r["rank"],status=r["status"],common_flop_pairs=r.get("common_flop_pairs"),possible_turns=len(r["possible_turns"])) for r in rows])))
    for p in out.glob("*.zip"):p.unlink()
if __name__=="__main__":main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),sys.argv[3])
