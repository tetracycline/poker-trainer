"""Find the third rank 108 original flop from two independently archived GTO roots."""
import argparse
import json
import subprocess
from pathlib import Path

import hu_b739_rank108 as source
from hu_b467_river_source_gate import json_bytes

CASES = {
    "3c3d4h": ("B500_LMP_CO_BB_3C3D4H_7H_GTO", "3195be0cb0903fb4f99098dc04611c924746ef52e4ae3fc4fd8caa5bd8f20bb5", "7h"),
    "5c5d2h": ("B500_LMP_CO_BB_5C5D2H_KC_GTO", "5262789c631959bde7be45dc0001866133b06aed464c8645633d1d1eefea4a30", "Kc"),
}
TURNS = {"3c3d4h": ("7s", "8s", "6c", "Td"), "5c5d2h": ("7s", "8s", "6d", "Tc")}
SOURCE_PINS = {
    "tools/hu_b739_rank108.py": "80d942e394270c0a1fece4a01ec89b9121e92d79",
    "tools/hu_b739_rank108_routes.cjs": "f3e413e029542819ad0c011196c6fe8984840b30",
}


def main(args):
    for path, expected in SOURCE_PINS.items():
        assert subprocess.check_output(["git", "hash-object", path], text=True).strip() == expected
    old_flops = set(source.TURNS)
    assert set(CASES) == set(TURNS) and old_flops.isdisjoint(CASES)
    # Card ranks distinguish all five originals even after any permutation of suits.
    fingerprints = {tuple(sorted(flop[::2])) for flop in (*old_flops, *CASES)}
    assert len(fingerprints) == len(old_flops) + len(CASES)
    source.CASES = CASES
    source.TURNS = TURNS
    source.main(args)
    if not args.preflight:
        path = args.output / "proof.json"
        report = json.loads(path.read_bytes())
        report.update(schema="NL2_B744_LIMP_BB_B50_R3_CALL_ADDITIONAL_ORIGINAL", previous_source_run=45331727303,
                      source_reader_git_blobs=SOURCE_PINS)
        path.write_bytes(json_bytes(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flop", required=True, choices=CASES)
    for field in ("solver", "routes", "output"):
        parser.add_argument("--"+field, type=Path, required=True)
    parser.add_argument("--driver", type=Path)
    parser.add_argument("--preflight", action="store_true")
    main(parser.parse_args())
