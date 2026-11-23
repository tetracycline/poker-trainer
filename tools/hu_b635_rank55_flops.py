"""Solve new rank55 flop ranks using the authenticated four-size BTN versus BB game."""
import argparse
import json
from pathlib import Path

from hu_b546_rank70_conditional import current_texture
from hu_b613_rank55_barrels import CASES, process
from hu_b624_rank55_flops import ARTIFACT, FLOPS as B624_FLOPS, TEMPLATE, source_job
from hu_b627_rank55_flops import FLOPS as B627_FLOPS


FLOPS = ("6d5c3c", "8d7c4c", "7d6c3c", "7d5c2c", "8d5c4c")


def flop_job(originals, flop):
    ranks = [tuple(sorted(board[::2])) for board in (*CASES, *B624_FLOPS, *B627_FLOPS, *FLOPS)]
    assert flop in FLOPS and len(ranks) == len(set(ranks))
    base, _ = source_job(originals, B624_FLOPS[0])
    ace_turns = ("Ac", "Ad", "Ah", "As")
    turns = [card for card in ace_turns if current_texture(flop + card) == "A_high"]
    extract = [dict(prefix=[], street=True)]
    extract.extend(dict(prefix=["b50", "c", turn], street=False, raw=True) for turn in turns)
    return dict(base, flop=flop, extract=extract), turns


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("solver", "originals", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--driver", type=Path)
    parser.add_argument("--run", type=int, required=True)
    parser.add_argument("--flop", choices=FLOPS, required=True)
    args = parser.parse_args()
    assert args.run > 0
    report = process(args, flop_job(args.originals, args.flop), ARTIFACT)
    report.update(batch=635, preflop_template=TEMPLATE)
    (args.output / "proof.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
