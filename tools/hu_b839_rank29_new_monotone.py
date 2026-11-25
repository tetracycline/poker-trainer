"""B839: two new rank29 monotone GTO/NL2 pairings in frozen frequency order.

Rank29 is 1st among the 234 still-APPROX models. Prior negative original
flops remain negative, never re-solved or selected for a posthoc menu.
A certificate requires independent replay of three different full flop solves.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path
import hu_b659_rank29_monotone as original
import hu_b703_rank29_highcards as earlier_high
import hu_b717_rank29_low_connected as earlier_low
import hu_b730_rank29_turn_gate as archived
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

MODEL = "ln-iso-lmp_r_model-gifggm"
WORKER = "tools/hu_b839_rank29_new_monotone.py"
PARENT_SHA = "167c1a6de9c98882d8487e493368585b92adc833"
CASES = {
    "AdJd7d": ["2c", "3h", "4s", "5c", "9h"],
    "KdTd6d": ["2c", "3h", "4s", "8c", "9h"],
}


def check_preflight():
    assert subprocess.check_output(["git", "hash-object", original.__file__], text=True).strip() == PARENT_SHA
    assert original.MODEL == MODEL
    archived_flops = []
    for file in archived.PINS:
        m = re.search(r"_R[0-9]+_([0-9A-Z]+)\.zip$", file, flags=re.I)
        if m:
            archived_flops.append(m.group(1).lower())
    old = set(original.CASES) | set(earlier_high.CASES) | set(earlier_low.CASES)
    old |= set(archived_flops)
    assert len({suit_isomorphism_class(x) for x in CASES}) == 2
    assert not {suit_isomorphism_class(x) for x in CASES} & {suit_isomorphism_class(x) for x in old}
    for f, turns in CASES.items():
        assert len(f) == 6 and f[1] == f[3] == f[5] == "d"
        assert len({f[0], f[2], f[4]}) == 3
        assert all(len(t) == 2 and t not in {f[:2], f[2:4], f[4:]} for t in turns)
        assert len(set(turns)) == len(turns)
    return len(old)


def run(args):
    prior = check_preflight()
    if args.preflight:
        print(json.dumps({"rank": 29, "new_distinct_original_flops": sorted(CASES),
                          "archived_flops_not_rerun": prior,
                          "certified_models_changed": 0}))
        return
    old = original.CASES
    try:
        original.CASES = CASES
        original.run(args)
    finally:
        original.CASES = old
    path = args.output / "proof.json"
    proof = json.loads(path.read_bytes())
    assert proof["rank"] == 29 and proof["model_id"] == MODEL and proof["flop"] == args.flop
    count = sum(len(row["checks"]) for row in proof["turns"])
    proof["schema"] = "NL2_B839_R29_TWO_UNTESTED_MONOTONE_ORIGINALS_V1"
    proof["parent_worker_blob"] = PARENT_SHA
    proof["new_original_flop"] = True
    proof["no_certificate_until_independent_artifact_replay"] = True
    proof["candidate_reachable_public_boards"] = count
    path.write_bytes(json_bytes(proof))
    print(json.dumps({"rank": 29, "flop": args.flop,
                      "candidate_reachable_public_boards": count,
                      "not_yet_CERT": True}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--driver", type=Path)
    p.add_argument("--flop", choices=CASES, required=True)
    p.add_argument("--preflight", action="store_true")
    run(p.parse_args())
