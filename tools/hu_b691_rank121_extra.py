"""Preregister three new two-tone rank121 flops using the unchanged B686 gates."""
import argparse
import json
from pathlib import Path

import hu_b686_rank121 as native
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

CASES={
    "QhTh7s":["2c","3d","4s","6h"],
    "Jd9d6h":["2s","3c","4h","8c"],
    "Tc8c5d":["2h","3s","4d","7h"],
}


def run(args):
    old_cases=native.CASES
    all_flops=[*old_cases,*CASES]
    assert len({suit_isomorphism_class(f) for f in all_flops})==len(all_flops)
    assert all(sorted([f[1::2].count(s) for s in set(f[1::2])])==[1,2] for f in CASES)
    try:
        native.CASES=CASES
        native.run(args)
    finally:
        native.CASES=old_cases
    path=args.output/"proof.json"
    proof=json.loads(path.read_bytes())
    assert proof["schema"]=="NL2_B686_R121_ORIGINAL_WORKER_V1"
    proof.update(schema="NL2_B691_R121_ORIGINAL_WORKER_V1",source_algorithm_batch=686,
        new_source_batch=691,preregistered_new_flops=list(CASES))
    path.write_bytes(json_bytes(proof))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","output","routes"):
        cli.add_argument("--"+key,type=Path,required=True)
    cli.add_argument("--flop",choices=CASES,required=True)
    cli.add_argument("--driver",type=Path)
    run(cli.parse_args())

