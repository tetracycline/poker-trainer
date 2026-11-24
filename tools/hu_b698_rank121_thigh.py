"""Preregister three new T-high two-tone BB3/BTN flops with unchanged B686 gates."""
import argparse
import json
from pathlib import Path

import hu_b686_rank121 as native
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

CASES={
    "Ts9s6h":["2c","3d","4h","7c"],
    "Th9h5c":["2s","3d","4c","7s"],
    "Td8d4s":["2h","3c","5s","6h"],
}
PRIOR_EXTRA_FLOPS=("QhTh7s","Jd9d6h","Tc8c5d")


def run(args):
    old_cases=native.CASES
    all_flops=[*old_cases,*PRIOR_EXTRA_FLOPS,*CASES]
    assert len({suit_isomorphism_class(f) for f in all_flops})==len(all_flops)==9
    assert all(sorted([f[1::2].count(s) for s in set(f[1::2])])==[1,2] for f in CASES)
    try:
        native.CASES=CASES
        native.run(args)
    finally:
        native.CASES=old_cases
    path=args.output/"proof.json"
    proof=json.loads(path.read_bytes())
    assert proof["schema"]=="NL2_B686_R121_ORIGINAL_WORKER_V1"
    assert (proof["root_pot"],proof["root_stack"],proof["pot"],proof["stack"])==(2050,9000,3404,8323)
    proof.update(schema="NL2_B698_R121_ORIGINAL_WORKER_V1",source_algorithm_batch=686,
        new_source_batch=698,preregistered_new_flops=list(CASES))
    path.write_bytes(json_bytes(proof))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","output","routes"):
        cli.add_argument("--"+key,type=Path,required=True)
    cli.add_argument("--flop",choices=CASES,required=True)
    cli.add_argument("--driver",type=Path)
    run(cli.parse_args())

