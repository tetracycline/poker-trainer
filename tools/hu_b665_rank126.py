"""Solve BB river stabs after a one-third SB flop lead and a half-pot turn call."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL, proof
from hu_b568_caller_rivers import hand_cell, rendered
from hu_b637_rank57 import solve
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, game_reach
from hu_trainer_route_gate import compatible

MODEL="ln-ipc-r_model-1h0u85n"
LINE="b33 c/x b50 c/x"
CASES={
    "9h6s2c":["3d","4h","5c","7d","8h","9c"],
    "8d5h3c":["2s","4d","6s","7c","9s","8h"],
    "7c4h2d":["3s","5c","6d","8c","9h","7s"],
    "Kh8c3d":["Ks","8h","3s","2c","4h","6d"],
}
DECK=[r+s for r in "23456789TJQKA" for s in "cdhs"]
ACTIONS={"過":"x","下注 ½":"b50","下注 ¾":"b75"}


def cards(public):
    return {public[i:i+2] for i in range(0,len(public),2)}


def decisions(root,sub,turn,rivers,route):
    sub.update(line0="b33 c",turn=turn,rivers=rivers)
    masks=game_reach(root,sub)[0]
    nodes=[n for n in sub["nodes"] if (n["line"],n["player"])==(LINE,1)]
    assert {n["board"][-2:] for n in nodes}==set(rivers)
    result={}
    for node in nodes:
        assert (node["pot"],node["bets"])==(1992,[498,498])
        row=proof(root,sub,node,masks)
        hands=rendered(dict(root=root,subgame=sub),row,node,route)
        same={hand:info for hand,info in hands.items() if ACTIONS[info["displayed_suggestion"]] in info["native"]["accepted_actions"]}
        if same:
            result[node["board"]]=(same,row["b50"])
    return result


def run(args):
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    if args.driver:
        assert args.driver.resolve()==solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    pool_raw=(solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"]
    route=json.loads(subprocess.check_output(["node","tools/hu_b665_rank126_routes.cjs"]))
    contract=json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"][MODEL]
    model=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"][MODEL]
    assert model["frequency_rank"]==126 and model["solver_profile"]=="SB_BB"
    assert abs(9004/1992/model["assumed_model_node_spr"]-1)<=.05
    flop=args.flop
    job=pipeline.make_job("SB_BB","gto",flop,"result.json",iters=1700,target=.5,compress=True)
    job.update(flop_oop="33%",flop_ip="50%",extract=[dict(prefix=[],street=True)]+[
        dict(prefix=["b33","c",t],street=False,raw=True) for t in CASES[flop]])
    root=solve(args.output/"flop",job,args.driver)
    assert (root["flop"],root["pot"],root["stack"])==(flop,600,9700)
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    first,= [n for n in root["nodes"] if n["line"]==""]
    second,= [n for n in root["nodes"] if n["line"]=="b33"]
    assert (first["player"],first["pot"],second["player"],second["pot"])==(0,600,1,798)
    bettors=accepted(first,root["hands"],"b33")
    callers=accepted(second,root["hands"],"c")
    tested=[]
    for turn in CASES[flop]:
        parent,=[n for n in root["nodes"] if n["line"]=="b33 c/" and n["board"].endswith(turn)]
        assert (parent["pot"],parent["bets"])==(996,[198,198])
        pub=parent["board"]
        eligible=[h for h in callers if turn not in h and hand_cell("".join(h),pub[:6])[0] in route["flop"] and
                  hand_cell("".join(h),pub)[0] in route["turn"] and
                  any(turn not in villain and set(h).isdisjoint(villain) for villain in bettors)]
        rivers=[r for r in DECK if r not in cards(pub) and any(r not in h and
                hand_cell("".join(h),pub+r)[0] in route["river"] for h in eligible)]
        record=dict(turn=turn,eligible_turn_hands=len(eligible),legal_rivers=len(rivers),paired_policies=False,checks=[])
        tested.append(record)
        if not rivers:
            continue
        original=pipeline.make_job("SB_BB","gto",flop,"result.json",iters=2100,target=.4,rank=.4,compress=False)
        original.update(pipeline.SUB)
        original.update(oop="",ip="",pot=996,stack=9502,turn=turn,line0=["b33","c","/"],root_no_bet=False,
            turn_oop="33%,50%,75%",turn_ip="50%",river_oop="33%,50%,75%,100%,a",river_ip="50%,75%,100%,a",
            extract=[dict(prefix=[],street=True)]+[dict(prefix=["x","b50","c",r],street=True) for r in rivers])
        for seat,key in enumerate(("oop_w","ip_w")):
            original[key]=[[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
        gto=solve(args.output/(turn+"-gto"),original,args.driver)
        assert (gto["flop"],gto["pot"],gto["stack"])==(flop,996,9502)
        assert 0<=gto["info"]["gto_expl_pct"]<=.5 and not gto["info"].get("lock_stats")
        before=decisions(root,gto,turn,rivers,route)
        if not before:
            continue
        locked_job,rules=prepare_job(dict(source=dict(version="gto",root=root,manifest=dict(spot="SB_BB")),job=original),"exp_ip",pool,pipeline)
        locked_job["out"]="result.json"
        locked=solve(args.output/(turn+"-exp_ip"),locked_job,args.driver)
        assert (locked["flop"],locked["pot"],locked["stack"])==(flop,996,9502)
        assert 0<=locked["info"]["gto_expl_pct"]<=.5 and 0<=locked["info"]["hero_gap_pct"]<=.5
        audit_patterns(locked,locked_job,dict(locks=rules),pool,1)
        after=decisions(root,locked,turn,rivers,route)
        record["paired_policies"]=True
        for public in sorted(before.keys() & after.keys()):
            common=sorted(before[public][0].keys() & after[public][0].keys())
            if common:
                assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=1))
                record["checks"].append(dict(board=public,hands=common,gto_b50=before[public][1],locked_b50=after[public][1]))
        if record["checks"]:
            break
    report=dict(rank=126,model_id=MODEL,flop=flop,line=LINE,root_sha256=sha(compact(root)),
                actual_river_pot_bb=19.92,actual_river_effective_stack_bb=90.04,turns=tested)
    (args.output/"proof.json").write_bytes(json_bytes(report))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--solver",type=Path,required=True)
    cli.add_argument("--flop",choices=CASES,required=True)
    cli.add_argument("--output",type=Path,required=True)
    cli.add_argument("--driver",type=Path)
    run(cli.parse_args())
