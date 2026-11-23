"""Solve SB check-call, turn lead and river three-quarter barrel on bottom-paired flops."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL
from hu_b637_rank57 import LINE, MODEL, hands_for, root_job, solve, turn_jobs
from hu_trainer_route_gate import compatible

CASES = {
    "Kh4s4d": ["2h","5s","6d","8c","9h","Td","Js","Ac"],
    "Qd3h3s": ["2d","4s","6h","8c","9d","Ts","Kc","Ah"],
    "Js5h5c": ["2s","3c","6h","7d","9s","Tc","Qh","Ad"],
    "9s4d4h": ["2c","3s","5d","6h","8c","Ts","Kd","Ac"],
}


def run(args):
    solver = args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    if args.driver:
        assert args.driver.resolve() == solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    pool_bytes = (solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_bytes)==POOL
    pool=json.loads(pool_bytes)["NL2"]
    route=json.loads(subprocess.check_output(["node","tools/hu_b617_sb_routes.cjs"]))["57"]
    contract=json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"][MODEL]
    status=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"][MODEL]
    assert status["frequency_rank"]==57 and status["solver_profile"]=="SB_BB" and abs(85/30/status["assumed_model_node_spr"]-1)<=.05
    assert route["paired"]["turn"]==["TPG"] and route["paired"]["river"]=={"TPG":"下注 ¾"}
    flop=args.flop
    _,template=root_job("TdTs4h")
    job=dict(template,flop=flop,out="result.json",extract=[dict(prefix=[],street=True)] +
             [dict(prefix=["x","b50","c",turn],street=False,raw=True) for turn in CASES[flop]])
    basis=pipeline.make_job("SB_BB","gto",flop,"result.json")
    for key in ("oop","ip","pot","stack","rake_rate","rake_cap"):
        assert job[key]==basis[key],key
    root=solve(args.output/"flop",job,args.driver)
    assert (root["flop"],root["pot"],root["stack"])==(flop,600,9700)
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    assert {n["board"][-2:] for n in root["nodes"] if n["line"]=="x b50 c/"}==set(CASES[flop])
    tested=[]
    for turn in CASES[flop]:
        original,locked,rules,rivers=turn_jobs(root,turn,pipeline,pool)
        shared_by_policy=[]
        turn_row=dict(turn=turn,paired_policies=False,checks=[])
        tested.append(turn_row)
        for version,subjob in (("gto",original),("exp_oop",locked)):
            sub=solve(args.output/(turn+"-"+version),subjob,args.driver)
            assert (sub["flop"],sub["pot"],sub["stack"])==(flop,1200,9400)
            assert 0<=sub["info"]["gto_expl_pct"]<=.5
            if version=="exp_oop":
                assert 0<=sub["info"]["hero_gap_pct"]<=.5
                audit_patterns(sub,subjob,dict(locks=rules),pool,0)
                turn_row["paired_policies"]=True
            else:
                assert not sub["info"].get("lock_stats")
            choices=hands_for(root,sub,turn,rivers,route)
            shared_by_policy.append(choices)
            if not choices:
                break
        if len(shared_by_policy)==2:
            gto,nl2=shared_by_policy
            for public in sorted(gto.keys() & nl2.keys()):
                holdings=sorted(gto[public][0] & nl2[public][0])
                if holdings:
                    assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=0))
                    turn_row["checks"].append(dict(board=public,hands=holdings,
                        gto_b50=gto[public][1]["b50"],locked_b50=nl2[public][1]["b50"]))
        if turn_row["checks"]:
            break
    report=dict(rank=57,model_id=MODEL,flop=flop,line=LINE,root_sha256=sha(compact(root)),
                actual_river_pot_bb=30,actual_river_effective_stack_bb=85,turns=tested)
    (args.output/"proof.json").write_bytes(json_bytes(report))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--solver",type=Path,required=True)
    cli.add_argument("--flop",choices=CASES,required=True)
    cli.add_argument("--output",type=Path,required=True)
    cli.add_argument("--driver",type=Path)
    run(cli.parse_args())
