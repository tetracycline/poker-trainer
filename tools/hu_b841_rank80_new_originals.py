"""B841 source-first new highest-remaining unassigned rank80 LMP river pair.

Avoid the four B672 negative native flops and B501/B732 historical roots.
These two originals retain the exact BB b33 / CO call, checked-turn
line and acting CO. No CERT without three distinct full source replays.
"""
import argparse
import json
import subprocess
from pathlib import Path
import hu_b671_rank80 as parent
import hu_b732_rank80_boundaries as archived
import hu_b501_rank80_originals as historical
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

PARENT_SHA = "56de6ba8eb6a6891c29229cdeaeac7bf410d4fc9"
CASES = {
    "6c6d3h": ["2s", "4d", "7h", "9s"],
    "KdJd5c": ["2s", "3h", "6d", "8c"],
}


def preflight():
    assert subprocess.check_output(["git", "hash-object", parent.__file__], text=True).strip() == PARENT_SHA
    assert parent.MODEL == historical.MID == "ln-iso-lmp_r_model-17pklmg"
    assert parent.LINE == historical.LINE == "b33 c/x x/x"
    old = set(parent.CASES) | set(archived.PINS) | set(historical.ANCHORS)
    classes = {suit_isomorphism_class(f) for f in CASES}
    assert len(classes) == len(CASES) == 2
    assert not classes.intersection(suit_isomorphism_class(f) for f in old)
    for flop, turns in CASES.items():
        cards = (flop[:2], flop[2:4], flop[4:])
        assert len(set(cards)) == 3 and len(set(turns)) == 4
        assert all(t not in cards and len(t) == 2 for t in turns)
    return len(old)


def run(args):
    count = preflight()
    if args.preflight:
        print(json.dumps({"rank": 80, "flops": sorted(CASES),
                          "excluded_historical_flops": count,
                          "native_repeated": 0, "CERT_changed": 0}))
        return
    old = parent.CASES
    try:
        parent.CASES = CASES
        parent.run(args)
    finally:
        parent.CASES = old
    path = args.output / "proof.json"
    proof = json.loads(path.read_bytes())
    assert (proof["rank"], proof["model_id"], proof["flop"]) == (80, parent.MODEL, args.flop)
    candidate = sum(len(t["checks"]) for t in proof["turns"])
    proof.update(schema="NL2_B841_R80_NEW_ORIGINAL_SOURCE_FIRST_V1",
                 source_algorithm_blob=PARENT_SHA,
                 new_original_flop=True,
                 eligible_exact_candidate_boards=candidate,
                 not_a_CERT_without_independent_artifact_replay=True)
    path.write_bytes(json_bytes(proof))
    print(json.dumps({"rank": 80, "flop": args.flop,
                      "candidate_exact_boards": candidate, "not_yet_CERT": True}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--driver", type=Path)
    p.add_argument("--flop", choices=CASES, required=True)
    p.add_argument("--preflight", action="store_true")
    run(p.parse_args())
