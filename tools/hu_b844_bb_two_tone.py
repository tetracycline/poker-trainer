"""B844: three distinct two-tone CO/BB originals, ranks 92-94 in frozen priority order.

B715 had no accepted CO half-pot on two rainbow roots and no joint river
reach on its three GTO turn games. New connected two-tone roots test a
different texture, not a duplicate root/turn or an automatic certification.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

import hu_b711_bb_lead_rivers as parent
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

CASES = {
    "9h8h2c": ["3d", "5s", "8s"],
    "8h7h3c": ["2d", "5s", "7s"],
    "7h6h2c": ["3d", "5s", "6s"],
}
WITNESSES = {
    "9h8h2c": {92: ("Td9d", "3d", "4c"), 93: ("Jd9d", "3d", "4c"), 94: ("Jd9d", "8s", "3c")},
    "8h7h3c": {92: ("Td8d", "2d", "4c"), 93: ("Jd8d", "2d", "4c"), 94: ("Jd8d", "7s", "2c")},
    "7h6h2c": {92: ("Td7d", "3d", "4c"), 93: ("Jd7d", "3d", "4c"), 94: ("Jd7d", "6s", "3c")},
}
PARENT_BLOB = "7ba3ce3a3120378cf8de8c252eda0298365714e3"


def preflight():
    assert subprocess.check_output(["git", "hash-object", parent.__file__], text=True).strip() == PARENT_BLOB
    prior = json.loads(Path("data/nl2_hu_b715_results.json").read_bytes())
    assert {p["flop"] for p in prior} == set(parent.CASES)
    assert all(p["bytes_replayed"] for p in prior)
    assert all(p["source_run"] == 45324358830 for p in prior)
    summary = json.loads(Path("data/nl2_hu_b715_summary.json").read_bytes())
    assert summary["positive_distinct_flops_by_rank"] == {"92": 0, "93": 0, "94": 0}
    registry = json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    priority = json.loads(Path("data/nl2_hu_b838_234_approx_frequency_priority.json").read_bytes())
    for rank, (mid, *_rest) in parent.MODELS.items():
        assert registry["records"][mid]["label"] == "APPROX"
        row, = [x for x in priority["rows"] if x["rank"] == rank]
        assert row["model_id"] == mid and row["passes_min_0_2_pct_frequency"]
    assert priority["current_certified_opportunity_share_pct"] < 90
    wanted = {suit_isomorphism_class(f) for f in CASES}
    assert len(wanted) == len(CASES) == 3
    assert not wanted & {suit_isomorphism_class(f) for f in parent.CASES}
    names = subprocess.check_output(["git", "ls-files", "data/solver_evidence"], text=True)
    pattern = re.compile(r"(?<![A-Za-z0-9])((?:[2-9TJQKA][CDHS]){3})(?![A-Za-z0-9])", re.I)
    for name in names.splitlines():
        for m in pattern.finditer(name):
            raw = m.group(1)
            flop = "".join(raw[i].upper() + raw[i + 1].lower() for i in range(0, 6, 2))
            assert suit_isomorphism_class(flop) not in wanted, "Historical named source orbit: " + name
    for flop, turns in CASES.items():
        cards = [flop[i:i+2] for i in (0, 2, 4)]
        assert len(set(cards)) == 3 and len({c[1] for c in cards}) == 2
        assert len(set(turns)) == len(turns) == 3 and not set(cards) & set(turns)
    return len(names.splitlines())


def run(args):
    n = preflight()
    old_cases, old_witnesses = parent.CASES, parent.WITNESSES
    try:
        parent.CASES, parent.WITNESSES = CASES, WITNESSES
        parent.run(args)
    finally:
        parent.CASES, parent.WITNESSES = old_cases, old_witnesses
    if args.preflight:
        print(json.dumps({"rank_order": [92, 93, 94], "flop": args.flop, "checked_named_source_paths": n, "native_solve": False}))
        return
    dest = args.output / "proof.json"
    result = json.loads(dest.read_bytes())
    assert result["flop"] == args.flop and result["source_worker_blob"] == PARENT_BLOB
    result.update(schema="NL2_B844_CO_BB_TWO_TONE_NATIVE_SOURCE_V1",
                  parent_worker_blob=PARENT_BLOB,
                  new_worker_blob=subprocess.check_output(["git", "hash-object", __file__], text=True).strip(),
                  not_a_certification=True,
                  independent_same_two_seat_replay_required=True)
    dest.write_bytes(json_bytes(result))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for field in ("solver", "output", "routes"):
        p.add_argument("--" + field, type=Path, required=True)
    p.add_argument("--flop", choices=CASES, required=True)
    p.add_argument("--driver", type=Path)
    p.add_argument("--preflight", action="store_true")
    run(p.parse_args())
