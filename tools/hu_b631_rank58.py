"""Extend rank58 to distinct SB roots using the B617 turn game and legal route."""
import argparse
import json
from pathlib import Path

import hu_b617_rank58 as sb

PINS = Path("data/nl2_hu_b631_rank58_sources.json")


def register_sources():
    sources = json.loads(PINS.read_bytes())
    for flop, source in sources.items():
        if flop in sb.CASES:
            assert source == sb.CASES[flop]
        sb.CASES[flop] = source
    return sources


if __name__ == "__main__":
    sources = register_sources()
    p = argparse.ArgumentParser(description=__doc__)
    for name in ["solver", "originals", "output"]:
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--flop", choices=sources, required=True)
    p.add_argument("--run", type=int, required=True)
    p.add_argument("--driver", type=Path)
    args = p.parse_args()
    assert args.run > 0
    report = sb.process(args)
    report["batch"] = 631
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "proof.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
