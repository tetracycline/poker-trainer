"""Verify the SB river check on a new seven-of-diamonds turn from the named B536 flop."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys

import hu_b617_rank58 as sb
from hu_native_river_witness_import import create_pair
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_board_reach_corrections import source_key

FLOP = "Kh8d5h"
TURN = "7d"


def publish(args):
    receipt = json.loads(args.receipt.read_bytes())
    assert receipt["workflow_run"]["id"] == args.run and receipt["workflow_run"]["head_sha"] == args.head
    assert subprocess.check_output(["git", "-C", args.solver, "rev-parse", "HEAD"], text=True).strip() == sb.SOLVER
    sys.path.insert(0, str((args.solver / "postflop/py").resolve()))
    import pipeline

    data = Path("data")
    before = json.loads((data / "nl2_hu_b617_rank58_partial.json").read_bytes())
    group, observations = before["group"], before["observations"]
    assert (group["rank"], group["model_id"]) == (58, sb.MODEL)
    assert [b["flop"] for b in group["boards"]] == [p["flop"] for p in group["pins"]]
    assert {b["flop"] for b in group["boards"]} == {"Ks7h2d", "Jh8s5d"}
    registry = json.loads((data / "nl2_hu_multiboard_status_current.json").read_bytes())
    model = registry["records"][sb.MODEL]
    pool_bytes = (args.solver / "inputs/pool_stats.json").read_bytes()
    assert sha(pool_bytes) == sb.POOL
    route = json.loads(subprocess.check_output(["node", "tools/hu_b617_sb_routes.cjs"]))["58"]
    options = SimpleNamespace(batch=636, rank=58, seat=0, version="exp_oop", line=sb.LINE,
                              run=args.run, model=sb.MODEL, originals=args.originals, archives=args.receipt.parent)
    result = create_pair(options, FLOP, model, receipt, route, pipeline, json.loads(pool_bytes)["NL2"])
    if result is None:
        print("No shared legal decision on the native GTO and NL2 policies.")
        return
    board, pin, rows = result
    assert board["turn"] == TURN and board["source_run_id"] == args.run and pin["shared_rendered_checks"]
    assert pin["GTO_strict_combos"] > 0 and pin["NL2_strict_combos"] > 0
    group["boards"].append(board)
    group["pins"].append(pin)
    observations["schema"] = "NL2_HU_B636_ORIGINAL_LOCKED_MEDIUM_V1"
    for version, key in [("gto", "gto_references"), ("exp_oop", "references")]:
        row = rows[version]
        observations[key][source_key(sb.MODEL, row)] = row
    (EVIDENCE / "reverified/rank58.json").write_bytes(json_bytes(group))
    (data / "nl2_hu_b636_locked_medium.json").write_bytes(json_bytes(observations))


if __name__ == "__main__":
    sb.CASES[FLOP] = dict(sb.CASES[FLOP], turns=[TURN])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", type=Path, required=True)
    parser.add_argument("--originals", type=Path, required=True)
    parser.add_argument("--run", type=int, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--driver", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--head")
    args = parser.parse_args()
    assert args.run > 0
    if args.receipt:
        assert args.head and not args.driver and not args.output
        publish(args)
    else:
        assert args.output is not None
        args.flop = FLOP
        report = sb.process(args)
        report["batch"] = 636
        (args.output / "proof.json").write_bytes(json_bytes(report))
