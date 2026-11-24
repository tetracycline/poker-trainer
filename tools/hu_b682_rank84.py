"""Solve three exact SB/BTN 3BP check-call turns after the explicit 33% price repair.

The worker records original native output and both-seat, displayed-action witnesses.
No worker result promotes CERT; an independent receipt/SHA importer is still required.
"""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b536_sb_barrels import tx
from hu_b637_rank57 import solve
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import cardkey, game_reach

sys.path.insert(0,str(Path(__file__).resolve().parent/"lines_pipeline"))
from run10_common import hcls

MODEL = "ln-3bp-3b_t_model-ciziut"
FLOP_LINE = "x b33 c"
LINE = "x b33 c/"
CASES = {
    "Qs8h3d": ["2c","4s","5h","6d"],
    "Qh9c4s": ["2d","3h","5c","6s"],
    "Kd7s2h": ["3c","4h","5d","6c"],
}
ACTIONS = {"過":"x","下注 ⅓":"b33","下注 ½":"b50","下注 ¾":"b75"}


def root_job(flop, pipeline):
    job = pipeline.make_job("SB3_BTN","gto",flop,"result.json",iters=2100,target=.45,compress=True)
    job.update(flop_oop="33%",flop_ip="33%",
        extract=[dict(prefix=[],street=True)]+[
            dict(prefix=["x","b33","c",turn],street=False,raw=True) for turn in CASES[flop]])
    return job


def turn_job(root, turn, pipeline):
    parent, = (n for n in root["nodes"] if n["line"] == FLOP_LINE+"/" and n["board"].endswith(turn))
    assert (parent["player"],parent["pot"],parent["bets"]) == (0,3486,[693,693])
    job = pipeline.make_job("SB3_BTN","gto",root["flop"],"result.json",iters=2200,target=.4,rank=.4,compress=False)
    job.update(pipeline.SUB)
    job.update(oop="",ip="",pot=3486,stack=8307,turn=turn,line0=["x","b33","c","/"],root_no_bet=False,
        turn_oop="33%,50%,75%,100%",turn_ip="33%,50%,75%,100%",
        river_oop="50%,75%,100%,a",river_ip="50%,75%,100%,a",
        extract=[dict(prefix=[],street=True)])
    for seat,key in enumerate(("oop_w","ip_w")):
        job[key] = [[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    return job


def decision(root, game, turn, route):
    game.update(line0=FLOP_LINE,turn=turn,rivers=[])
    node, = (n for n in game["nodes"] if (n["line"],n["player"]) == (LINE,0))
    assert (node["pot"],node["bets"]) == (3486,[0,0])
    row = proof(root,game,node,game_reach(root,game)[0])
    masks = base64.b64decode(row["compatible_action_mask_b64"],validate=True)
    public = node["board"]
    flop_cells = route["routes"].get(tx(public[:6]),{}).get("parents",[])
    turn_cells = route["routes"].get(tx(public),{}).get("decisions",{})
    eligible = {}
    for hand,bits in zip(game["hands"][0],masks,strict=True):
        if not bits:
            continue
        fc,tc = hcls(hand,public[:6]),hcls(hand,public)
        label = turn_cells.get(tc)
        action = ACTIONS.get(label)
        if fc not in flop_cells or action not in node["acts"]:
            continue
        if bits & (1 << node["acts"].index(action)):
            eligible["".join(cardkey(hand))] = dict(flop_class=fc,turn_class=tc,
                displayed_suggestion=label,accepted_actions=[a for i,a in enumerate(node["acts"]) if bits & (1<<i)])
    return row,eligible


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--solver",type=Path,required=True)
    cli.add_argument("--flop",choices=CASES,required=True)
    cli.add_argument("--output",type=Path,required=True)
    cli.add_argument("--driver",type=Path)
    args = cli.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip() == SOLVER
    assert sha((solver/"postflop/py/pipeline.py").read_bytes()) == PIPELINE
    assert sha((solver/"postflop/py/ranges.py").read_bytes()) == RANGES
    if args.driver:
        assert args.driver.resolve() == solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip() == RUST
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    import ranges
    pool_raw = (solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)["NL2"]
    route = json.loads(subprocess.check_output(["node","tools/hu_b682_rank84_routes.cjs"]))["84"]
    assert (route["id"],route["line"],route["seat"],route["turn_pot"],route["turn_stack"]) == (MODEL,LINE,0,3486,8307)
    assert abs(8307/3486/route["spr"]-1)<.001
    job = root_job(args.flop,pipeline)
    assert (job["pot"],job["stack"]) == (2100,9000)
    assert (job["oop"],job["ip"]) == tuple(ranges.to_str(w) for w in ranges.ranges("SB3_BTN","gto"))
    root = solve(args.output/"flop",job,args.driver)
    assert (root["flop"],root["pot"],root["stack"]) == (args.flop,2100,9000)
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    first, = (n for n in root["nodes"] if n["line"] == "")
    facing, = (n for n in root["nodes"] if n["line"] == "x b33")
    assert (first["player"],first["pot"],first["bets"]) == (0,2100,[0,0])
    assert (facing["player"],facing["pot"],facing["bets"]) == (0,2793,[0,693])
    attempts = []
    for turn in CASES[args.flop]:
        gto_job = turn_job(root,turn,pipeline)
        gto = solve(args.output/(turn+"-gto"),gto_job,args.driver)
        assert (gto["flop"],gto["pot"],gto["stack"]) == (args.flop,3486,8307)
        assert 0<=gto["info"]["gto_expl_pct"]<=.5 and not gto["info"].get("lock_stats")
        before,gh = decision(root,gto,turn,route)
        record = dict(turn=turn,public_board=before["public_board"],gto_sha256=sha((args.output/(turn+"-gto")/"result.json").read_bytes()),
            gto_rendered_hands=len(gh),gto_reach=before["strict_legal_combos"],paired=False,shared_hands=[],
            gto_b50=before["b50"])
        attempts.append(record)
        if not gh:
            continue
        locked_job,rules = prepare_job(dict(source=dict(version="gto",root=root,manifest=dict(spot="SB3_BTN")),job=gto_job),
            "exp_oop",pool,pipeline)
        locked_job["out"]="result.json"
        locked = solve(args.output/(turn+"-exp_oop"),locked_job,args.driver)
        assert (locked["flop"],locked["pot"],locked["stack"]) == (args.flop,3486,8307)
        assert 0<=locked["info"]["gto_expl_pct"]<=.5 and 0<=locked["info"]["hero_gap_pct"]<=.5
        counts = audit_patterns(locked,locked_job,dict(locks=rules),pool,0)
        after,eh = decision(root,locked,turn,route)
        common = sorted(gh.keys() & eh.keys())
        record.update(paired=True,nl2_sha256=sha((args.output/(turn+"-exp_oop")/"result.json").read_bytes()),
            nl2_rendered_hands=len(eh),nl2_reach=after["strict_legal_combos"],nl2_b50=after["b50"],
            measured_lock_application=counts,shared_hands=common,
            gto_witnesses={h:gh[h] for h in common},nl2_witnesses={h:eh[h] for h in common})
        if common:
            break
    report = dict(schema="NL2_B682_R84_ORIGINAL_WORKER_V1",rank=84,model_id=MODEL,flop=args.flop,line=LINE,
        root_sha256=sha((args.output/"flop/result.json").read_bytes()),root_job_sha256=sha(compact(job)),
        solver=SOLVER,rust=RUST,pool_sha256=POOL,pot=3486,stack=8307,actor=0,
        restricted_flop_oop_sizes_pct=[33],restricted_flop_ip_sizes_pct=[33],
        positive_distinct_flops=int(any(r["shared_hands"] for r in attempts)),turns=attempts,
        not_a_certification=True,no_observed_per_hole_card_NL2_frequencies=True)
    (args.output/"proof.json").write_bytes(json_bytes(report))

if __name__ == "__main__":
    main()
