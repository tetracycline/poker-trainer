"""Solve six distinct two-tone J/T-high flops for BTN's checked-down river."""
import argparse
from pathlib import Path

import hu_b655_rank69_checks as study

CASES = {
    "Jh8h5c": ["2d", "3s", "4c", "6s", "Tc"],
    "Th8h6c": ["2d", "3s", "4c", "7s", "Jc"],
    "Jh7h4c": ["2d", "3s", "5c", "8s", "Tc"],
    "Ts6s4d": ["2c", "3h", "5d", "8h", "Jd"],
    "Js9s5d": ["2c", "3h", "4d", "7h", "Td"],
    "Tc7c4h": ["2d", "3s", "5h", "8s", "Jh"],
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--flop", choices=CASES, required=True)
    parser.add_argument("--driver", type=Path)
    parser.add_argument("--existing-root", action="store_true")
    study.CASES = CASES
    study.screen(parser.parse_args())
