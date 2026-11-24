"""Study three new K/Q-high rank75 flops without changing any source gates."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import hu_b690_rank75_connected as base
from hu_b467_river_source_gate import json_bytes, sha

CASES = {
    "Kc9h3d": ["2s", "4h", "5c"],
    "QhJc4d": ["2h", "3c", "5s"],
    "KdTh5h": ["2c", "3s", "4d"],
}
WITNESSES = {
    "Kc9h3d": ("QcJh", "TsTd"),
    "QhJc4d": ("AsKd", "QcQs"),
    "KdTh5h": ("AcQs", "JcJd"),
}
PINS = {
    "tools/hu_b690_rank75_connected.py": "9d95c0dde4465dab8b35441cf8ceff1bc73e54f8",
    "tools/hu_b674_threebet_call_routes.cjs": "f217abef1567f5e1a6ef3ce7fcef2400cd5f9635",
    "tools/hu_b637_rank57.py": "86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9",
}
APP_STATES = (
    ("a98cb80d7762b464064874de39dcff6f4bf5707d", "15aee97e53a156fe073c96a120638a8a3679958f", "31370c779d22b7d895e76f1030504909019dbe5a"),
    ("b4a308a0f65b707f43f41f0b354cec87c08d5af6", "15aee97e53a156fe073c96a120638a8a3679958f", "3b10524228c357552bb3f1eac88e17f9b2459b32"),
)
APP_FILES = ("nl2_hu_model.js", "nl2.js", "tools/hu_trainer_route_contract.cjs")
ORIGINAL_GATE = base.root_gate


def blob(path):
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def cards(value):
    return {value[i:i + 2] for i in range(0, len(value), 2)}


def range_class(hand):
    ranks = sorted((hand[0], hand[2]), key="23456789TJQKA".index, reverse=True)
    return "".join(ranks) + ("" if ranks[0] == ranks[1] else "s" if hand[1] == hand[3] else "o")


def checked_gate(root, turn, route):
    assert len(root["flop"]) == 6 and len(cards(root["flop"])) == 3
    for line, player in (("", 0), ("b33", 1)):
        node, = (n for n in root["nodes"] if (n["line"], n["player"]) == (line, player))
        assert len(node["board"]) == 6 and cards(node["board"]) == cards(root["flop"])
    node, = (n for n in root["nodes"] if n["line"] == "b33 c/" and n["board"].endswith(turn))
    assert len(node["board"]) == 8 and len(cards(node["board"])) == 4
    assert cards(node["board"][:6]) == cards(root["flop"]) and node["board"][6:] == turn
    return ORIGINAL_GATE(root, turn, route)


def configure():
    assert all(blob(path) == expected for path, expected in PINS.items())
    current = tuple(blob(path) for path in APP_FILES)
    assert current in APP_STATES, "Only the two complete reviewed app revisions are accepted"
    base.CASES = CASES
    base.root_gate = checked_gate
    return dict(zip(APP_FILES, current, strict=True))


def static(args):
    solver = args.solver.resolve()
    assert subprocess.check_output(["git", "-C", solver, "rev-parse", "HEAD"], text=True).strip() == base.SOLVER
    assert sha((solver / "postflop/py/pipeline.py").read_bytes()) == base.PIPELINE
    assert sha((solver / "postflop/py/ranges.py").read_bytes()) == base.RANGES
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline
    import ranges
    ranges.SPOTS.update(base.EXTRA_SPOTS)
    job = base.root_job(args.flop, pipeline)
    assert (job["pot"], job["stack"], job["flop_oop"], job["flop_ip"]) == (1650, 9250, "33%", "33%,75%")
    weights = [dict(zip(ranges.NAMES, w, strict=True)) for w in ranges.ranges("CO3_BTN", "gto")]
    route = json.loads(subprocess.check_output(["node", "tools/hu_b674_threebet_call_routes.cjs"]))["75"]
    assert (route["id"], route["line"], route["seat"], route["turn_pot"], route["turn_stack"]) == (
        base.MODEL, "b33 c/x", 1, 2740, 8705)
    hero, villain = WITNESSES[args.flop]
    assert weights[1][range_class(hero)] >= .005 and weights[0][range_class(villain)] >= .005
    for turn in CASES[args.flop]:
        public = args.flop + turn
        assert len(cards(public + hero + villain)) == 8
        assert base.hcls(hero, args.flop) in route["routes"][base.tx(args.flop)]["parents"]
        assert route["routes"][base.tx(public)]["decisions"][base.hcls(hero, public)] == "過"
    return dict(hero=hero, villain=villain, ip_weight=weights[1][range_class(hero)],
        oop_weight=weights[0][range_class(villain)], exact_ui_each_turn=True,
        not_a_native_strategy_witness=True)


def run(args):
    app = configure()
    witness = static(args)
    if args.preflight:
        print(json.dumps(dict(flop=args.flop, static_witness=witness, actual_turn_pot=2740,
            actual_turn_stack=8705, no_certification=True)))
        return
    if args.driver:
        assert not args.output.exists() or not any(args.output.iterdir()), "Use a fresh native source directory"
    else:
        assert (args.output / "proof.json").is_file(), "Replay requires the original complete proof"
    saved = sys.argv
    sys.argv = [saved[0], "--solver", str(args.solver), "--flop", args.flop, "--output", str(args.output)]
    if args.driver:
        sys.argv += ["--driver", str(args.driver)]
    try:
        base.main()
    finally:
        sys.argv = saved
    proof_path = args.output / "proof.json"
    report = json.loads(proof_path.read_bytes())
    report.update(schema="NL2_B707_R75_HIGH_ORIGINAL_WORKER_V1", source_algorithm_blobs=PINS,
        source_app_blobs=app, source_worker_blob=blob("tools/hu_b707_rank75_highcards.py"),
        static_range_witness=witness, preregistered_flops=list(CASES), preregistered_turns=CASES[args.flop],
        native_file_sha256={str(p.relative_to(args.output)): sha(p.read_bytes())
            for p in sorted(args.output.rglob("*")) if p.is_file() and p != proof_path})
    proof_path.write_bytes(json_bytes(report))
    print(json.dumps(dict(flop=args.flop, positive=report["positive_distinct_flops"],
        actor_locked_boards=sum(t["paired"] for t in report["turns"]),
        half_pot_assessed=sum(t.get("nl2_b50") is not None for t in report["turns"]))))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--solver", type=Path, required=True)
    cli.add_argument("--flop", choices=CASES, required=True)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--driver", type=Path)
    cli.add_argument("--preflight", action="store_true")
    run(cli.parse_args())
