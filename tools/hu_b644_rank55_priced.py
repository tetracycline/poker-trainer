"""Verify rank55 on a small lead followed by a larger barrel, or the reverse."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL, proof
from hu_b546_rank70_conditional import current_texture
from hu_b550_rank69_originals import execute, published_actions
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import game_reach
from hu_trainer_route_gate import compatible

MODEL = "ln-ipfr-r_model-1mcb4lz"
CASES = json.loads(Path("data/nl2_hu_b644_rank55_parents.json").read_bytes())
DECK = [rank+suit for rank in "23456789TJQKA" for suit in "cdhs"]


def original(folder, case):
    artifact = case["artifact"]
    receipt = json.loads((folder / f"{artifact}.json").read_bytes())
    path = folder / f"{artifact}.zip"
    info = receipt["workflow_run"]
    assert (receipt["id"], info["id"], info["head_sha"], info["repository_id"]) == (
        artifact, case["run"], case["head"], 1438346845)
    assert receipt["name"] == case["name"] and case["digest"] == receipt["digest"] == "sha256:" + sha(path.read_bytes())
    with ZipFile(path) as z:
        old = json.loads(z.read("flop/result.json"))
        job = json.loads(z.read("flop/job.json"))
        source = json.loads(z.read("proof.json"))
    assert sha(compact(job)) == case["job_sha256"]
    assert (old["flop"], old["pot"], old["stack"]) == (source["flop"], 550, 9750)
    assert job["flop_oop"] == job["flop_ip"] == "33%,50%,75%,100%" and not job.get("locks")
    return old, job


def native(folder, job, driver):
    if driver:
        return json.loads(execute(driver, folder, job))
    assert json.loads((folder / "job.json").read_bytes()) == json.loads(compact(job))
    return json.loads((folder / "result.json").read_bytes())


def verify(args):
    solver = args.solver.resolve()
    assert subprocess.check_output(["git", "-C", solver, "rev-parse", "HEAD"], text=True).strip() == SOLVER
    if args.driver:
        assert args.driver.resolve() == solver / "postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git", "-C", solver / "postflop/postflop-solver", "rev-parse", "HEAD"], text=True).strip() == RUST
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    pool_bytes = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(pool_bytes) == POOL
    pool = json.loads(pool_bytes)["NL2"]
    routes = json.loads(subprocess.check_output(["node", "tools/hu_b613_rank55_routes.cjs"]))
    contracts = json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"]
    registry = json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"]
    case = CASES[args.flop]
    first, second = case["bets"]
    flop_bet, turn_bet = f"b{first}", f"b{second}"
    flop_line = flop_bet + " c"
    line = f"{flop_line}/{turn_bet} c/x"
    old, job = original(args.originals, case)
    assert (old["flop"], first + second) == (args.flop, 108)
    turns = [t for t in ("Ac", "Ad", "Ah", "As") if current_texture(args.flop+t) == "A_high"]
    extra = [dict(prefix=[flop_bet, "c", t], raw=True, street=False) for t in turns]
    root = native(args.output / "flop", dict(job, extract=job["extract"] + extra), args.driver)
    key = lambda n: (n["board"], n["line"], n["player"])
    nodes = {key(n): n for n in root["nodes"]}
    assert root["hands"] == old["hands"] and all(nodes[key(n)] == n for n in old["nodes"])
    assert 0 <= root["info"]["gto_expl_pct"] <= .5 and not root["info"].get("lock_stats")
    saved = []
    for turn in turns:
        parent, = (n for n in root["nodes"] if n["line"] == flop_line + "/" and n["board"].endswith(turn))
        flop_paid = (550 * first + 50) // 100
        pot, stack = 550 + 2 * flop_paid, 9750 - flop_paid
        assert (parent["pot"], parent["bets"]) == (pot, [flop_paid, flop_paid])
        paid = (pot * second + 50) // 100
        river_pot = pot + 2 * paid
        spr = (stack - paid) / river_pot
        assert abs(spr / registry[MODEL]["assumed_model_node_spr"] - 1) <= .05
        board = parent["board"]
        blocked = {board[i:i+2] for i in range(0, 8, 2)}
        rivers = [r for r in DECK if r not in blocked and current_texture(board+r) == "A_high"]
        gto = pipeline.make_job("BTN_BB", "gto", args.flop, "result.json", compress=False, target=.4, rank=.4, iters=2200)
        gto.update(pipeline.SUB)
        gto.update(oop="", ip="", turn=turn, pot=pot, stack=stack, line0=[flop_bet, "c", "/"],
                   turn_oop=f"{second}%,100%", root_no_bet=False, extract=[dict(prefix=[], street=True)] +
                   [dict(prefix=[turn_bet, "c", r], street=True) for r in rivers])
        for seat, field in enumerate(("oop_w", "ip_w")):
            gto[field] = [[hand, w] for hand,w in zip(root["hands"][seat], parent["wr"][seat], strict=True) if w > 1e-4]
        manifest = dict(spot="BTN_BB", pot_family="SRP")
        locked, rules = prepare_job(dict(source=dict(version="gto", root=root, manifest=manifest), job=gto), "exp_ip", pool, pipeline)
        locked["out"] = "result.json"
        policies = {}
        half_pot = {}
        for version, spec in (("gto", gto), ("exp_ip", locked)):
            sub = native(args.output / (turn+"-"+version), spec, args.driver)
            assert (sub["flop"], sub["pot"], sub["stack"]) == (args.flop, pot, stack)
            assert 0 <= sub["info"]["gto_expl_pct"] <= .5
            if version == "gto":
                assert not sub["info"].get("lock_stats")
            else:
                assert 0 <= sub["info"]["hero_gap_pct"] <= .5
                audit_patterns(sub, spec, dict(manifest, locks=rules), pool, 1)
            sub.update(turn=turn, rivers=rivers, line0=flop_line)
            masks = game_reach(root, sub)[0]
            decisions = {}
            targets = [n for n in sub["nodes"] if (n["line"], n["player"]) == (line, 1)]
            assert {n["board"] for n in targets} == {board+r for r in rivers}
            for node in targets:
                assert (node["pot"], node["bets"]) == (river_pot, [paid,paid])
                assert compatible(contracts[MODEL], dict(public_board=node["board"], actual_exact_action_line=line, acting_seat=1))
                row = proof(root, sub, node, masks)
                decisions[node["board"]] = set(published_actions(dict(root=root, subgame=sub), row, routes))
                if version == "exp_ip":
                    half_pot[node["board"]] = row["b50"]
            policies[version] = decisions
        checks = []
        for public in sorted(policies["gto"]):
            shared = policies["gto"][public] & policies["exp_ip"][public]
            if shared:
                checks.append(dict(board=public, hands=sorted(shared), locked_half_pot=half_pot[public]))
        saved.append(dict(turn=turn, checks=checks))
        if checks:
            break
    return dict(rank=55, batch=644, model_id=MODEL, flop=args.flop, run=args.run,
                line=line, parent_artifact=case["artifact"], actual_river_pot_bb=river_pot/100,
                actual_river_effective_stack_bb=(stack-paid)/100, turns=saved)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ("solver", "originals", "output"):
        cli.add_argument("--"+name, type=Path, required=True)
    cli.add_argument("--run", required=True, type=int)
    cli.add_argument("--flop", required=True, choices=CASES)
    cli.add_argument("--driver", type=Path)
    args = cli.parse_args()
    assert args.run > 0
    result = verify(args)
    (args.output / "proof.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
