"""Preregister three new K-high flop checks for rank229 after B676's one positive.

All three flops have distinct rank structures and are distinct from every B676
source. A matching texture is only a proposal: native strict two-seat reach,
actual displayed hands and both policy checks still determine the result.
"""
import argparse
import json
from pathlib import Path

import hu_b676_checked_rivers as native
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

CASES={
    "Ks9h3d":["2c","6s","8h","Td"],
    "Kd9c5h":["2s","6c","8h","Tc"],
    "Ks8d4h":["2c","6d","7h","Td"],
}


def run(args):
    old=list(native.CASES)
    assert not (set(CASES)&set(old))
    assert len({suit_isomorphism_class(f) for f in [*old,*CASES]})==len(old)+len(CASES)
    old_cases,old_targets=native.CASES,native.TARGETS
    try:
        native.CASES=CASES
        native.TARGETS={flop:229 for flop in CASES}
        native.run(args)
    finally:
        native.CASES,native.TARGETS=old_cases,old_targets
    path=args.output/"proof.json"
    proof=json.loads(path.read_bytes())
    proof.update(batch=681,source_algorithm_batch=676)
    path.write_bytes(json_bytes(proof))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","output","routes"):
        cli.add_argument("--"+key,type=Path,required=True)
    cli.add_argument("--flop",choices=CASES,required=True)
    cli.add_argument("--driver",type=Path)
    run(cli.parse_args())

