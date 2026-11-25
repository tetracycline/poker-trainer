"""B846: rank75 two fresh monotone public-flop source experiments.

Research only. Two distinct named flops are preselected before outcome inspection.
All authenticated actor, turn, root SHA, strict physical reach and measured
NL2 lock gates remain inherited unchanged from B833/B830.
"""
import argparse
import json
from pathlib import Path
import hu_b833_rank75_new_monotone as parent
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

WORKER = "tools/hu_b846_rank75_unseen_monotone.py"
CASES = {
    "Td9d4d": ["2d", "3d", "5d"],
    "Td8d5d": ["2d", "3d", "4d"],
}

def run(a):
    assert set(CASES) == {"Td9d4d", "Td8d5d"}
    assert len({suit_isomorphism_class(f) for f in CASES}) == 2
    old = set(parent.OLD) | set(parent.CASES)
    assert not {suit_isomorphism_class(f) for f in CASES} & {suit_isomorphism_class(f) for f in old}
    previous = parent.WORKER, parent.CASES, parent.OLD
    try:
        parent.WORKER, parent.CASES, parent.OLD = WORKER, CASES, old
        parent.run(a)
    finally:
        parent.WORKER, parent.CASES, parent.OLD = previous
    if a.preflight or a.checkpoint_only:
        return
    proof_file = a.output / "proof.json"
    proof = json.loads(proof_file.read_bytes())
    assert proof["flop"] == a.flop
    assert proof["origin"]["worker_blob"] == parent.parent.checked.blob(WORKER)
    assert proof["new_flop_solve_invocations"] == 1
    assert proof["preregistered_turns"] == CASES[a.flop]
    proof.update(
        schema="NL2_B846_R75_TWO_UNSEEN_MONOTONE_ORIGINALS_V1",
        approved_as_cert=False,
        eligibility_requires_independent_artifact_replay=True,
        not_a_generic_texture_policy=True,
        unobserved_private_hand_NL2_actions_not_inferred=True,
    )
    proof_file.write_bytes(json_bytes(proof))
    print(json.dumps({
        "flop": a.flop,
        "positive_distinct_flops": proof["positive_distinct_flops"],
        "locked_public_boards": proof["locked_public_boards"],
        "joint_halfpot_assessed": proof["joint_halfpot_assessed"],
        "halfpot_candidates": proof["halfpot_candidates"],
        "CERT_promotions": 0,
    }))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for key in ("solver", "output"):
        ap.add_argument("--" + key, type=Path, required=True)
    ap.add_argument("--flop", choices=CASES, required=True)
    ap.add_argument("--driver", type=Path)
    ap.add_argument("--checkpoint", type=Path)
    ap.add_argument("--checkpoint-only", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    run(ap.parse_args())
