"""Solve five previously untested low two-tone flop rank sets on the rank55 line."""
import argparse
import json
from pathlib import Path

from hu_b546_rank70_conditional import current_texture
from hu_b613_rank55_barrels import CASES, process
from hu_b624_rank55_flops import ARTIFACT, FLOPS as PRIOR_FLOPS, TEMPLATE, source_job

FLOPS = ("7d6c5c", "7d5c3c", "8d6c4c", "7d4c3c", "8d7c5c")


def job_for(originals, flop):
    tested = (*CASES, *PRIOR_FLOPS, *FLOPS)
    assert len({tuple(sorted(board[::2])) for board in tested}) == len(tested)
    assert flop in FLOPS
    base, _ = source_job(originals, PRIOR_FLOPS[0])
    turns = ["A" + suit for suit in "cdhs" if current_texture(flop + "A" + suit) == "A_high"]
    requests = [dict(prefix=[], street=True)]
    requests.extend(dict(prefix=["b50", "c", turn], street=False, raw=True) for turn in turns)
    return dict(base, flop=flop, extract=requests), turns


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["solver", "originals", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--run", type=int, required=True)
    parser.add_argument("--flop", choices=FLOPS, required=True)
    parser.add_argument("--driver", type=Path)
    args = parser.parse_args()
    assert args.run > 0
    report = process(args, job_for(args.originals, args.flop), ARTIFACT)
    report.update(batch=627, preflop_template=TEMPLATE)
    (args.output / "proof.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
