"""Solve CO river decisions after a one-third BB flop lead and checked turn."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import POOL, proof
from hu_b568_caller_rivers import hand_cell, rendered
from hu_b637_rank57 import solve
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, game_reach
from hu_trainer_route_gate import compatible

MODEL="ln-iso-lmp_r_model-17pklmg"
LINE="b33 c/x x/x"
CASES={
    "As9s4d":["2h","3c","6h","7d","Td","Jc"],
    "Jh8h3d":["2s","4c","5d","6s","9c","Th"],
    "Qs7s2d":["3c","4h","5c","8d","Td","Jc"],
    "AcTc5h":["2d","3s","6d","7h","8s","Jd"],
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
        assert (node["pot"],node["bets"])==(416,[0,0])
        row=proof(root,sub,node,masks)
        hands=rendered(dict(root=root,subgame=sub),row,node,route)
        common={h:r for h,r in hands.items() if ACTIONS[r["displayed_suggestion"]] in r["native"]["accepted_actions"]}
        if common:
            result[node["board"]]=(common,row["b50"])
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
    route=json.loads(subprocess.check_output(["node","tools/hu_b671_rank80_routes.cjs"]))
    contract=json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"][MODEL]
    model=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"][MODEL]
    assert model["frequency_rank"]==80 and model["solver_profile"]=="LMP_CO_BB"
    assert abs(9817/416/model["assumed_model_node_spr"]-1)<=.05
    template=EVIDENCE/"NL2_B580_R27_LMP.zip"
    assert sha(template.read_bytes())=="d4b98b4351012d78aa62f3cd31b75228d4f7a35725584d86f633552fbf28369a"
    with ZipFile(template) as z:
        root_template,turn_template,manifest=[json.loads(z.read(n)) for n in (
            "original-flop.job.json","original-turn.job.json","original-manifest.json")]
    flop=args.flop
    job=dict(root_template,flop=flop,out="result.json",flop_oop="33%",
             extract=[dict(prefix=[],street=True)]+[
                 dict(prefix=["b33","c",t],street=False,raw=True) for t in CASES[flop]])
    check_limp_source(dict(manifest=manifest,root_job=job,subgame_job=None))
    root=solve(args.output/"flop",job,args.driver)
    assert (root["flop"],root["pot"],root["stack"])==(flop,250,9900)
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    lead,=[n for n in root["nodes"] if n["line"]==""]
    call,=[n for n in root["nodes"] if n["line"]=="b33"]
    assert (lead["player"],lead["pot"],call["player"],call["pot"])==(0,250,1,333)
    bettors=accepted(lead,root["hands"],"b33")
    callers=accepted(call,root["hands"],"c")
    tested=[]
    for turn in CASES[flop]:
        parent,=[n for n in root["nodes"] if n["line"]=="b33 c/" and n["board"].endswith(turn)]
        assert (parent["pot"],parent["bets"])==(416,[83,83])
        pub=parent["board"]
        eligible=[h for h in callers if turn not in h and hand_cell("".join(h),pub[:6])[0] in route["flop"] and
                  hand_cell("".join(h),pub)[0] in route["turn"] and
                  any(turn not in villain and set(h).isdisjoint(villain) for villain in bettors)]
        rivers=[r for r in DECK if r not in cards(pub) and any(r not in h and hand_cell("".join(h),pub+r)[0] in route["river"] for h in eligible)]
        record=dict(turn=turn,eligible_turn_hands=len(eligible),legal_rivers=len(rivers),paired_policies=False,checks=[])
        tested.append(record)
        if not rivers:
            continue
        original=dict(turn_template,flop=flop,turn=turn,out="result.json",pot=416,stack=9817,
            line0=["b33","c","/"],root_no_bet=False,turn_oop="33%,50%,75%",turn_ip="33%,50%,75%",
            river_oop="33%,50%,75%,100%,a",river_ip="50%,75%,100%,a",target_pct=.4,iters=2200,
            extract=[dict(prefix=[],street=True)]+[dict(prefix=["x","x",r],street=True) for r in rivers])
        for seat,key in enumerate(("oop_w","ip_w")):
            original[key]=[[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
        gto=solve(args.output/(turn+"-gto"),original,args.driver)
        assert (gto["flop"],gto["pot"],gto["stack"])==(flop,416,9817)
        assert 0<=gto["info"]["gto_expl_pct"]<=.5 and not gto["info"].get("lock_stats")
        before=decisions(root,gto,turn,rivers,route)
        if not before:
            continue
        locked_job,rules=prepare_job(dict(source=dict(version="gto",root=root,manifest=manifest),job=original),"exp_ip",pool,pipeline)
        locked_job["out"]="result.json"
        locked=solve(args.output/(turn+"-exp_ip"),locked_job,args.driver)
        assert (locked["flop"],locked["pot"],locked["stack"])==(flop,416,9817)
        assert 0<=locked["info"]["gto_expl_pct"]<=.5 and 0<=locked["info"]["hero_gap_pct"]<=.5
        audit_patterns(locked,locked_job,dict(manifest,locks=rules),pool,1)
        after=decisions(root,locked,turn,rivers,route)
        record["paired_policies"]=True
        for public in sorted(before.keys() & after.keys()):
            hands=sorted(before[public][0].keys() & after[public][0].keys())
            if hands:
                assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=1))
                record["checks"].append(dict(board=public,hands=hands,gto_b50=before[public][1],locked_b50=after[public][1]))
        if record["checks"]:
            break
    result=dict(rank=80,model_id=MODEL,flop=flop,line=LINE,root_sha256=sha(compact(root)),
                actual_river_pot_bb=4.16,actual_river_effective_stack_bb=98.17,turns=tested)
    (args.output/"proof.json").write_bytes(json_bytes(result))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--solver",type=Path,required=True)
    cli.add_argument("--flop",choices=CASES,required=True)
    cli.add_argument("--output",type=Path,required=True)
    cli.add_argument("--driver",type=Path)
    run(cli.parse_args())
