"""B847: test the unexamined B524 6s5h4d/Kd boundary without native reruns.

B720 checked 6s5h4d/6h, 7d5c4c/9c and 6d4c3h/Kd. Kd on
6s5h4d has separately positive original turn reach in both B524 policies.
Test the same physical BTN and BB hands through the exact turn bet/call,
then distinguish possible future river extracts from genuine river evidence.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from hu_b467_river_source_gate import json_bytes, sha
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b463_rank45_gate import SOLVER
from hu_checked_gto_boundary import load_original
from hu_b568_caller_rivers import hand_cell
from hu_sequential_cfr_reach import accepted, cardkey
from hu_b470_rank73_new_rivers import audit_patterns

FLOP, TURN = "6s5h4d", "Kd"
RUN = 45118153398
HEAD = "d1b22cd54e8c5391f2ee6d9411488923979ac797"
BRANCH = "fix/nl2-hu-lines-audit-20261118"
PINS = {
    "gto": (14792976867, 137505625101, "df887d5566b9f99505a5310b3e236205c6bfbd55b19013266fbf3e91071a442b"),
    "exp_ip": (14793655339, 137505625113, "5725c811a63ba90be177b3c40ef3a7f240248f6cfa1ccf2096d05c18da8292e7"),
}
DECK = [r+s for r in "23456789TJQKA" for s in "cdhs"]

def cards(s):
    return {s[i:i+2] for i in range(0,len(s),2)}

def policy_gate(orig, route):
    source=orig["source"]; root=source["root"]; game=source["subgame"]
    b=orig["public"]; assert cards(b[:6])==cards(FLOP) and b[6:]==TURN
    assert (game["pot"],game["stack"])==(1100,9475)
    def unique(g,line,board,actor,pot,bets):
        found=[n for n in g["nodes"] if (n["line"],n["board"],n["player"])==(line,board,actor)]
        if not found:return None
        n,=found;assert (n["pot"],n["bets"])==(pot,bets)
        return n
    f=next(n["board"] for n in root["nodes"] if len(n["board"])==6)
    assert cards(f)==cards(FLOP)
    steps=[
        (root,unique(root,"",f,0,550,[0,0]),"b50",0),
        (root,unique(root,"b50",f,1,825,[275,0]),"c",1),
        (game,unique(game,"b50 c/",b,0,1100,[0,0]),"x",0),
        (game,unique(game,"b50 c/x",b,1,1100,[0,0]),"b50",1),
        (game,unique(game,"b50 c/x b50",b,0,1650,[0,550]),"c",0),
    ]
    if any(n is None or a not in n["acts"] for g,n,a,seat in steps):
        return None,dict(status="ORIGINAL_NODE_OR_SIZE_NOT_EXPORTED",
                         missing=[i for i,(g,n,a,seat) in enumerate(steps) if n is None or a not in n["acts"]])
    alive=[None,None]; counts=[]
    for g,n,a,seat in steps:
        x=accepted(n,g["hands"],a)
        alive[seat]=x if alive[seat] is None else alive[seat]&x
        counts.append(len(alive[seat]))
    for seat in (0,1):
        alive[seat]={h for h in alive[seat] if cards(b).isdisjoint(h)}
    alive[1]={h for h in alive[1] if hand_cell("".join(h),b[:6])[0] in route["routes"]["flop"]
              and hand_cell("".join(h),b)[0] in route["routes"]["turn"]}
    exported=[n["board"] for n in game["nodes"] if n["line"]=="b50 c/x b50 c/x" and n["player"]==1]
    return alive,dict(status="EXACT_PRIOR_ACTIONS_REPLAYED",intersection_counts=counts,
                      two_seat_route_hands=[len(s) for s in alive],exported_target_rivers=sorted(exported),
                      prior_turn_barrel_call_pairs=sum(set(h).isdisjoint(v) for h in alive[1] for v in alive[0]))

def main(a):
    solver=a.solver.resolve(); py=solver/"postflop/py"
    assert sys.version_info[:2]==(3,11)
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    assert (sha((py/"pipeline.py").read_bytes()),sha((py/"ranges.py").read_bytes()),
            sha((solver/"inputs/pool_stats.json").read_bytes()))==(PIPELINE,RANGES,POOL)
    sys.path.insert(0,str(py)); import pipeline,ranges
    pool=json.loads((solver/"inputs/pool_stats.json").read_bytes())["NL2"]
    status=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    priority=json.loads(Path("data/nl2_hu_b838_234_approx_frequency_priority.json").read_bytes())
    assert priority["current_certified_opportunity_share_pct"]<90
    assert all(status["records"][x["model_id"]]["label"]=="APPROX" and x["passes_min_0_2_pct_frequency"]
               for x in priority["rows"] if x["rank"] in (104,105))
    old=json.loads(Path("data/nl2_hu_b720_summary.json").read_bytes())
    assert (FLOP,TURN) not in {(x["flop"],x["turn"]) for x in old["workers"]}
    assert old["distinct_positive_flops_by_rank"]=={"104":0,"105":0}
    route_raw=subprocess.check_output(["node","tools/hu_b713_btn_lead_routes.cjs"])
    route=json.loads(route_raw)["105"]; assert (route["actor"],route["spot"],route["pct"],
        route["river_pot"],route["river_stack"],route["line"])==(1,"BTN_BB",50,2200,8925,"b50 c/x b50 c/x")
    assert abs(8925/2200/route["spr"]-1)<=.05
    origins={}; gates={}; rangesets=[]; public=None
    for version,(aid,jid,digest) in PINS.items():
        name=f"B524-R8-{FLOP}-{version}"
        meta=json.loads((a.receipts/f"{aid}.json").read_bytes())
        job=json.loads((a.receipts/f"{jid}.json").read_bytes())
        assert (job["id"],job["run_id"],job["head_sha"],job["name"],job["status"],job["conclusion"])==(
            jid,RUN,HEAD,f"fresh ({FLOP}, {version})","completed","success")
        assert {"Compile pinned Rust solver","Solve full BTN and BB ranges and both selected turns","Run actions/upload-artifact@v4"} <= {
            x["name"] for x in job["steps"] if x["conclusion"]=="success"}
        assert meta["workflow_run"]["head_branch"]==BRANCH
        orig=load_original(a.receipts,aid,dict(name=name,run=RUN,head=HEAD,sha256=digest),
            "BTN_BB",FLOP,TURN,version,pot=550,stack=9750,pipeline=pipeline,ranges=ranges,flop_line="b50 c")
        assert orig["job"]["turn_ip"]=="50%,100%"
        assert public is None or public==orig["public"]
        public=orig["public"]; origins[version]=orig["identity"]
        if version=="exp_ip":
            src=orig["source"]
            lock=audit_patterns(src["subgame"],orig["job"],src["manifest"],pool,1)
            assert any(v>0 for k,v in lock["driver_tree_nodes"].items() if k in lock["marginal_targets"])
            origins[version]["measured_lock_application"]=lock
        live,gate=policy_gate(orig,route);rangesets.append(live);gates[version]=gate
    feasible={}
    if all(x is not None for x in rangesets):
        both=[rangesets[0][s]&rangesets[1][s] for s in (0,1)]
        for river in DECK:
            if river in cards(public):continue
            pairs=[]
            for h in sorted(both[1]):
                if river in h or hand_cell("".join(h),public+river)[0] not in route["routes"]["river"]:continue
                for v in sorted(both[0]):
                    if river not in v and set(h).isdisjoint(v):pairs.append(["".join(h),"".join(v)])
            if pairs:feasible[river]=dict(pair_count=len(pairs),first_pair=pairs[0])
    report=dict(schema="NL2_B847_B524_HELDOUT_EXACT_TURN_PRIOR_GATE_V1",flop=FLOP,turn=TURN,
                source_run=RUN,source_head=HEAD,source_identities=origins,prior_gates=gates,
                rank104_status="B75_NOT_PRESENT_IN_ORIGINAL_TURN_MENU",
                rank105_status=("SOURCE_NODE_MISSING" if any(x is None for x in rangesets)
                    else "POSSIBLE_UNSOLVED_RIVER_CANDIDATES" if feasible else "NO_COMMON_PHYSICAL_ROUTE_PAIR_BEFORE_RIVER"),
                rank105_possible_rivers=feasible,route_sha256=sha(route_raw),native_solve_invocations=0,
                cert_promotions=0,new_locks=0,new_joint_halfpot=0,new_nonpolarized=0,
                requires_actual_river_action_and_full_source_replay=True,not_a_certification=True)
    a.output.write_bytes(json_bytes(report))
    print(json.dumps({k:report[k] for k in ("rank104_status","rank105_status","rank105_possible_rivers","native_solve_invocations")}))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for x in ("solver","receipts","output"):p.add_argument("--"+x,type=Path,required=True)
    main(p.parse_args())
