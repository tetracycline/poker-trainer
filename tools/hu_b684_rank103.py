"""Solve three fresh BB/BTN 3BP flop-call turns at the displayed 33% call price.

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
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

sys.path.insert(0,str(Path(__file__).resolve().parent/"lines_pipeline"))
from run10_common import hcls

MODEL = "ln-3bp-3c_t_model-owdwy"
FLOP_LINE = "b33 c"
LINE = "b33 c/x"
CASES = {
    "Qs8h4d": ["2c","5s","Tc","Ah"],
    "Jh8d3c": ["2h","5s","9c","Qs"],
    "9c6c3h": ["2d","4s","8d","Td"],
}
ACTIONS = {"過":"x","下注 ⅓":"b33","下注 ½":"b50","下注 ¾":"b75"}


def root_job(flop, pipeline):
    job = pipeline.make_job("BB3_BTN","gto",flop,"result.json",iters=2100,target=.45,compress=True)
    job.update(flop_oop="33%,50%,75%",flop_ip="33%,50%,75%",
        extract=[dict(prefix=[],street=True)]+[
            dict(prefix=["b33","c",turn],street=False,raw=True) for turn in CASES[flop]])
    return job


def turn_job(root, turn, pipeline):
    parent, = (n for n in root["nodes"] if n["line"] == FLOP_LINE+"/" and n["board"].endswith(turn))
    assert (parent["player"],parent["pot"],parent["bets"]) == (0,3404,[677,677])
    job = pipeline.make_job("BB3_BTN","gto",root["flop"],"result.json",iters=2200,target=.4,rank=.4,compress=False)
    job.update(pipeline.SUB)
    job.update(oop="",ip="",pot=3404,stack=8323,turn=turn,line0=["b33","c","/"],root_no_bet=False,
        turn_oop="33%,50%,75%,100%",turn_ip="33%,50%,75%,100%",
        river_oop="50%,75%,100%,a",river_ip="50%,75%,100%,a",
        extract=[dict(prefix=[],street=True)])
    for seat,key in enumerate(("oop_w","ip_w")):
        job[key] = [[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    return job



def flop_candidates(root, turn, route):
    """Reject only zero-reach/non-rendered paths before spending a turn solve."""
    first, = (n for n in root["nodes"] if n["line"] == "")
    facing, = (n for n in root["nodes"] if n["line"] == "b33")
    parent, = (n for n in root["nodes"] if n["line"] == FLOP_LINE+"/" and n["board"].endswith(turn))
    assert (parent["player"],parent["pot"],parent["bets"]) == (0,3404,[677,677])
    public = parent["board"]
    alive = [{cardkey(h) for h,w in zip(root["hands"][s],parent["wr"][s],strict=True) if w>1e-4}
             for s in (0,1)]
    villain = accepted(first,root["hands"],"b33") & alive[0]
    hero = accepted(facing,root["hands"],"c") & alive[1]
    parents = route["routes"].get(tx(public[:6]),{}).get("parents",[])
    decisions = route["routes"].get(tx(public),{}).get("decisions",{})
    return sorted("".join(h) for h in hero if turn not in h
        and hcls("".join(h),public[:6]) in parents and hcls("".join(h),public) in decisions
        and any(turn not in v and set(h).isdisjoint(v) for v in villain))


def decision(root, game, turn, route):
    game.update(line0=FLOP_LINE,turn=turn,rivers=[])
    node, = (n for n in game["nodes"] if (n["line"],n["player"]) == (LINE,1))
    assert (node["pot"],node["bets"]) == (3404,[0,0])
    row = proof(root,game,node,game_reach(root,game)[0])
    masks = base64.b64decode(row["compatible_action_mask_b64"],validate=True)
    public = node["board"]
    flop_cells = route["routes"].get(tx(public[:6]),{}).get("parents",[])
    turn_cells = route["routes"].get(tx(public),{}).get("decisions",{})
    eligible = {}
    for hand,bits in zip(game["hands"][1],masks,strict=True):
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
    assert ranges.SPOTS["BB3_BTN"] == dict(oop="BB",ip="BTN",oopc=[("BTNopen>BB","3bet")],
        ipc=[("BTNrfi","open"),("BTNopen>BB3b","call")],pot=20.5,stack=90.0,pfr="oop",kind="3BP")
    pool_raw = (solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)["NL2"]
    route = json.loads(subprocess.check_output(["node","tools/hu_b684_rank103_routes.cjs"]))
    assert (route["id"],route["line"],route["seat"],route["turn_pot"],route["turn_stack"]) == (MODEL,LINE,1,3404,8323)
    assert abs(8323/3404/route["spr"]-1)<.001
    job = root_job(args.flop,pipeline)
    assert (job["pot"],job["stack"]) == (2050,9000)
    assert (job["oop"],job["ip"]) == tuple(ranges.to_str(w) for w in ranges.ranges("BB3_BTN","gto"))
    assert not job.get("locks") and job.get("hero") is None
    assert (job["rake_rate"],job["rake_cap"]) == (.05,1000)
    root = solve(args.output/"flop",job,args.driver)
    assert (root["flop"],root["pot"],root["stack"]) == (args.flop,2050,9000)
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    first, = (n for n in root["nodes"] if n["line"] == "")
    facing, = (n for n in root["nodes"] if n["line"] == "b33")
    assert (first["player"],first["pot"],first["bets"]) == (0,2050,[0,0])
    assert (facing["player"],facing["pot"],facing["bets"]) == (1,2727,[677,0])
    attempts = []
    for turn in CASES[args.flop]:
        eligible = flop_candidates(root,turn,route)
        if not eligible:
            attempts.append(dict(turn=turn,flop_route_hands=0,stage="FLOP_ROUTE_REJECTED",
                gto_rendered_hands=0,paired=False,shared_hands=[]))
            continue
        gto_job = turn_job(root,turn,pipeline)
        gto = solve(args.output/(turn+"-gto"),gto_job,args.driver)
        assert (gto["flop"],gto["pot"],gto["stack"]) == (args.flop,3404,8323)
        assert 0<=gto["info"]["gto_expl_pct"]<=.5 and not gto["info"].get("lock_stats")
        before,gh = decision(root,gto,turn,route)
        record = dict(turn=turn,flop_route_hands=len(eligible),public_board=before["public_board"],gto_sha256=sha((args.output/(turn+"-gto")/"result.json").read_bytes()),
            gto_rendered_hands=len(gh),gto_reach=before["strict_legal_combos"],paired=False,shared_hands=[],
            gto_b50=before["b50"])
        attempts.append(record)
        if not gh:
            continue
        locked_job,rules = prepare_job(dict(source=dict(version="gto",root=root,manifest=dict(spot="BB3_BTN")),job=gto_job),
            "exp_ip",pool,pipeline)
        locked_job["out"]="result.json"
        locked = solve(args.output/(turn+"-exp_ip"),locked_job,args.driver)
        assert (locked["flop"],locked["pot"],locked["stack"]) == (args.flop,3404,8323)
        assert 0<=locked["info"]["gto_expl_pct"]<=.5 and 0<=locked["info"]["hero_gap_pct"]<=.5
        counts = audit_patterns(locked,locked_job,dict(locks=rules),pool,1)
        assert any(n>0 for pat,n in counts["driver_tree_nodes"].items() if pat in counts["marginal_targets"])
        after,eh = decision(root,locked,turn,route)
        common = sorted(gh.keys() & eh.keys())
        record.update(paired=True,nl2_sha256=sha((args.output/(turn+"-exp_ip")/"result.json").read_bytes()),
            nl2_rendered_hands=len(eh),nl2_reach=after["strict_legal_combos"],nl2_b50=after["b50"],
            measured_lock_application=counts,shared_hands=common,
            gto_witnesses={h:gh[h] for h in common},nl2_witnesses={h:eh[h] for h in common})
        if common:
            break
    report = dict(schema="NL2_B684_R103_ORIGINAL_WORKER_V1",rank=103,model_id=MODEL,flop=args.flop,line=LINE,
        root_sha256=sha((args.output/"flop/result.json").read_bytes()),root_job_sha256=sha(compact(job)),
        solver=SOLVER,rust=RUST,pipeline_sha256=PIPELINE,ranges_sha256=RANGES,pool_sha256=POOL,
        preflop_source="PINNED_POKER_SOLVER_PREFLOP_CFR",pot=3404,stack=8323,actor=1,
        lock_scope="FROZEN_GTO_FLOP_TURN_RIVER_LOCK_ONLY",route_sha256=sha(compact(route)),
        restricted_flop_oop_sizes_pct=[33,50,75],restricted_flop_ip_sizes_pct=[33,50,75],
        positive_distinct_flops=int(any(r["shared_hands"] for r in attempts)),turns=attempts,
        not_a_certification=True,no_observed_per_hole_card_NL2_frequencies=True)
    (args.output/"proof.json").write_bytes(json_bytes(report))

if __name__ == "__main__":
    main()
