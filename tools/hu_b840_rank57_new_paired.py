"""B840: high-frequency remaining rank57; two unused paired SB_BB flops.

Use the pinned authentic SB flop and partial opponent-locked decision worker.
Do not count a model CERT until independent source-pinned replay has three
distinct exact flops with the displayed original action line and joint reach.
"""
import argparse
import json
import subprocess
from pathlib import Path
import hu_b664_rank57_bottom_pair as parent
import hu_b637_rank57 as archived
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

WORKER = "tools/hu_b840_rank57_new_paired.py"
PARENT_SHA = "aa0eb696f992381e500a6683ed2e90b74f75e5fa"
MODEL = "ln-opfr-r_model-8ze7gv"
CASES = {
    "Ad6h6s": ["2c", "3d", "4h", "9s", "Qc"],
    "Kh8d8s": ["2c", "3h", "5d", "Ts", "Ac"],
}


def preflight():
    assert subprocess.check_output(["git", "hash-object", parent.__file__], text=True).strip() == PARENT_SHA
    assert archived.MODEL == MODEL and archived.LINE == "x b50 c/b75 c/"
    old = set(parent.CASES) | set(archived.CASES)
    assert len({suit_isomorphism_class(f) for f in CASES}) == len(CASES) == 2
    assert not {suit_isomorphism_class(f) for f in CASES} & {suit_isomorphism_class(f) for f in old}
    for flop, turns in CASES.items():
        cards = (flop[:2], flop[2:4], flop[4:])
        assert cards[1][0] == cards[2][0] and cards[1] != cards[2]
        assert len(set(cards)) == 3
        assert 1 <= len(turns) <= 6 and len(set(turns)) == len(turns)
        assert all(len(t) == 2 and t not in cards for t in turns)
    return len(old)


def run(a):
    previous_count = preflight()
    if a.preflight:
        print(json.dumps({"rank": 57, "original_rank_frequency_pct": 0.76786796,
                          "new_distinct_flops": sorted(CASES),
                          "prior_known_flops_not_rerun": previous_count,
                          "not_certified": True}))
        return
    old = parent.CASES
    try:
        parent.CASES = CASES
        parent.run(a)
    finally:
        parent.CASES = old
    result_path = a.output / "proof.json"
    result = json.loads(result_path.read_bytes())
    assert result["rank"] == 57 and result["model_id"] == MODEL and result["flop"] == a.flop
    assert result["actual_river_pot_bb"] == 30 and result["actual_river_effective_stack_bb"] == 85
    positive = sum(len(x["checks"]) for x in result["turns"])
    result.update(schema="NL2_B840_R57_NEW_PAIRED_SB_ORIGINALS_V1",
                  parent_worker_blob=PARENT_SHA,
                  distinct_native_flop=True,
                  candidate_exact_boards=positive,
                  incomplete_until_independent_GTO_NL2_sources_replayed=True)
    result_path.write_bytes(json_bytes(result))
    print(json.dumps({"rank": 57, "flop": a.flop,
                      "candidate_exact_boards": positive, "not_yet_CERT": True}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--driver", type=Path)
    p.add_argument("--flop", choices=CASES, required=True)
    p.add_argument("--preflight", action="store_true")
    run(p.parse_args())
