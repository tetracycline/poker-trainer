"""Solve exact UTG river value bets after a checked monotone flop and 75% turn bet."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b527_checked_barrels import board_row
from hu_b613_rank55_barrels import native
from hu_b619_utg_rivers import TEMPLATE, TEMPLATE_SHA, decision
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import game_reach
from hu_trainer_route_gate import compatible

MODEL = "ln-opfr-r_model-1txz51y"
LINE = "x x/b75 c/"
CASES = {
    "Ks8s3s": ["2d", "4c", "5h", "6d", "9c", "Th"],
    "Qh7h2h": ["3c", "4d", "5s", "6c", "8d", "9s"],
    "Ad8d4d": ["2c", "3h", "5s", "6c", "7h", "9s"],
    "Jc6c2c": ["3h", "4d", "5s", "7h", "8d", "9s"],
}


def template_jobs():
    raw = (EVIDENCE / TEMPLATE).read_bytes()
    assert sha(raw) == TEMPLATE_SHA
    template, = [s for s in json.loads(gzip.decompress(raw))["source_arrays"] if s["version"] == "gto"]
    meta = template["manifest"]
    assert (meta["spot"], meta["pot_family"], meta["solver_pin"], meta["solver_ranges_sha256"]) == ("UTG_CO", "SRP", PIPELINE, RANGES)
    assert meta["preflop_ranges"]["source"] == "PINNED_POKER_SOLVER_PREFLOP_CFR"
    return template


def root_job(template, flop):
    extracts = [dict(prefix=[], street=True)]
    extracts.extend(dict(prefix=["x", "x", turn], street=False, raw=True) for turn in CASES[flop])
    return dict(template["root_job"], flop=flop, out="result.json", extract=extracts)


def turn_job(template, root, parent, rivers):
    assert parent["pot"] == 650 and parent["bets"] == [0, 0]
    job = dict(template["subgame_job"], flop=root["flop"], turn=parent["board"][-2:],
               line0=["x", "x", "/"], pot=650, stack=9750, out="result.json",
               turn_oop="75%", turn_ip="50%,100%", river_oop="50%,75%,100%,a", river_ip="50%,75%,100%,a",
               root_no_bet=False, iters=2200, rank_pct=.45, target_pct=.45,
               extract=[dict(prefix=[], street=True)] + [dict(prefix=["b75", "c", r], street=True) for r in rivers])
    for seat, key in enumerate(("oop_w", "ip_w")):
        job[key] = [[hand, weight] for hand, weight in zip(root["hands"][seat], parent["wr"][seat], strict=True) if weight > 1e-4]
    return job


def read_source(folder, job, driver, root, manifest, run, turn, rivers, version):
    raw = native(folder, job, driver)
    sub = json.loads(raw)
    info = sub["info"]
    assert 0 <= info["gto_expl_pct"] <= .5
    assert (sub["flop"], sub["pot"], sub["stack"]) == (root["flop"], 650, 9750)
    if version == "gto":
        assert not info.get("lock_stats")
    else:
        assert 0 <= info["hero_gap_pct"] <= .5 and info["lock_stats"]
    sub.update(line0="x x", turn=turn, rivers=rivers)
    source = dict(version=version, root=root, subgame=sub, run=run, manifest=manifest,
                  root_sha256=sha(compact(root)), source_sha256=sha(raw), archive_sha256=None)
    return source


def choices(source, route):
    root, sub = source["root"], source["subgame"]
    masks = game_reach(root, sub)[0]
    results = {}
    for node in sub["nodes"]:
        if (node["line"], node["player"]) != (LINE, 0):
            continue
        row = proof(root, sub, node, masks)
        if row["compatible_hole_card_pairs"] == 0:
            continue
        row, hands = decision(source, node["board"], 75, route, 5.7, require_displayed_action=True)
        if hands:
            results[node["board"]] = (row, hands)
    return results


def run(args):
    solver = args.solver.resolve()
    assert subprocess.check_output(["git", "-C", solver, "rev-parse", "HEAD"], text=True).strip() == SOLVER
    if args.driver:
        assert args.driver.resolve() == solver / "postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git", "-C", solver / "postflop/postflop-solver", "rev-parse", "HEAD"], text=True).strip() == RUST
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    import ranges
    from solve_hu_missing_branches import EXTRA_SPOTS
    pipeline.SPOTS.update(EXTRA_SPOTS)
    ranges.SPOTS.update(EXTRA_SPOTS)
    pool_raw = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)["NL2"]
    template = template_jobs()
    setup = root_job(template, args.flop)
    assert (setup["oop"], setup["ip"]) == tuple(ranges.to_str(r) for r in ranges.ranges("UTG_CO", "gto"))
    route = json.loads(subprocess.check_output(["node", "tools/hu_b619_utg_routes.cjs", "619"]))["109"]
    assert route["id"] == MODEL and route["turn"] == ["mono:0"] and route["river"] == {"mono:0": "下注 ¾"}
    contract = json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"][MODEL]
    root_raw = native(args.output / "flop", setup, args.driver)
    root = json.loads(root_raw)
    assert (root["flop"], root["pot"], root["stack"]) == (args.flop, 650, 9750)
    assert 0 <= root["info"]["gto_expl_pct"] <= .5 and not root["info"].get("lock_stats")
    manifest = dict(spot="UTG_CO", pot_family="SRP", preflop_ranges=template["manifest"]["preflop_ranges"], locks=[])
    report = dict(rank=109, model_id=MODEL, flop=args.flop, run=args.run, root_sha256=sha(root_raw), turns=[], selected=None)
    for turn in CASES[args.flop]:
        parent, = [n for n in root["nodes"] if n["line"] == "x x/" and n["board"].endswith(turn)]
        public = parent["board"]
        known = {public[i:i+2] for i in range(0, 8, 2)}
        rivers = [rank+suit for rank in "23456789TJQKA" for suit in "cdhs"
                  if rank+suit not in known and board_row(public+rank+suit) == "mono"]
        job = turn_job(template, root, parent, rivers)
        gto = read_source(args.output / (turn+"-gto"), job, args.driver, root, manifest, args.run, turn, rivers, "gto")
        original = choices(gto, route)
        record = dict(turn=turn, original_positive_rivers=len(original), locked_positive_rivers=0)
        report["turns"].append(record)
        if not original:
            continue
        locked_job, rules = prepare_job(dict(source=gto, job=job), "exp_oop", pool, pipeline)
        locked_job["out"] = "result.json"
        lock_manifest = dict(manifest, locks=rules, gto_parent_source_run_id=args.run, gto_parent_source_sha256=gto["root_sha256"])
        locked = read_source(args.output / (turn+"-exp_oop"), locked_job, args.driver, root, lock_manifest, args.run, turn, rivers, "exp_oop")
        locked["measured_lock_application"] = audit_patterns(locked["subgame"], locked_job, lock_manifest, pool, hero_seat=0)
        paired = choices(locked, route)
        record["locked_positive_rivers"] = len(paired)
        for board in sorted(original.keys() & paired.keys()):
            hands = sorted(original[board][1].keys() & paired[board][1].keys())
            if hands:
                assert compatible(contract, dict(public_board=board, actual_exact_action_line=LINE, acting_seat=0))
                report["selected"] = dict(public_board=board, turn=turn, hands=hands,
                    gto_pairs=original[board][0]["compatible_hole_card_pairs"],
                    locked_pairs=paired[board][0]["compatible_hole_card_pairs"],
                    locked_half_pot=paired[board][0]["b50"])
                break
        if report["selected"]:
            break
    (args.output / "proof.json").write_bytes(json_bytes(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--driver", type=Path)
    parser.add_argument("--flop", choices=CASES, required=True)
    parser.add_argument("--run", type=int, required=True)
    args = parser.parse_args()
    assert args.run > 0
    run(args)
