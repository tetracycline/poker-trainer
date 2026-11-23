"""Authenticate and register the three completed B568 native jobs without invoking a solver."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from zipfile import ZipFile

from hu_b568_caller_rivers import (
    DATA,
    EVIDENCE,
    MID,
    POOL,
    SOLVER,
    TURNS,
    fresh,
    historical_screen,
    json_bytes,
    sha,
)

RUN = 45129965580
HEAD = "669819f4c5afec3bb1456733799ba9a691d85dde"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--solver", type=Path, required=True)
    ap.add_argument("--archives", type=Path, required=True)
    args = ap.parse_args()
    solver = args.solver.resolve()
    assert (
        subprocess.check_output(["git", "-C", solver, "rev-parse", "HEAD"], text=True).strip() == SOLVER
    )
    raw = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline, ranges

    route = json.loads(subprocess.check_output(["node", "tools/hu_b568_caller_routes.cjs"]))
    model = json.loads((DATA / "nl2_hu_multiboard_status_current.json").read_bytes())["records"][MID]
    assert (model["frequency_rank"], model["solver_profile"], model["assumed_model_node_spr"]) == (64, "SB_BB", 3.667)
    pins = json.loads((DATA / "nl2_hu_b579_completed_artifacts.json").read_bytes())
    assert set(pins) == set(TURNS)
    group = dict(rank=64, model_id=MID, boards=[], pins=[])
    medium = dict(schema="NL2_HU_B568_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={})
    records = []
    with TemporaryDirectory() as temporary:
        folder = Path(temporary)
        verify = SimpleNamespace(driver=None, saved_root=False, results=folder, run=RUN)
        for flop in TURNS:
            pin = pins[flop]
            aid = pin["id"]
            meta = json.loads((args.archives / f"{aid}.json").read_bytes())
            assert (meta["id"], meta["name"], meta["digest"]) == (
                aid,
                "B568-R64-" + flop,
                "sha256:" + pin["sha256"],
            )
            assert (
                meta["workflow_run"]["id"],
                meta["workflow_run"]["head_sha"],
                meta["workflow_run"]["repository_id"],
            ) == (RUN, HEAD, 1438346845)
            archive = args.archives / f"{aid}.zip"
            assert sha(archive.read_bytes()) == pin["sha256"]
            with ZipFile(archive) as z:
                assert all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in z.namelist())
                z.extractall(folder / flop)
            signed = json.loads((folder / flop / "verification.json").read_bytes())
            rebuilt = fresh(verify, flop, model, group, medium, route, pool, pipeline, ranges)
            assert signed == rebuilt and rebuilt["selected"]
            records.append(rebuilt)
    assert len(group["boards"]) == len({b["flop"] for b in group["boards"]}) == 3
    destination = EVIDENCE / "reverified/rank64.json"
    if destination.exists():
        present = json.loads(destination.read_bytes())
        for b in present["boards"]:
            b.pop("optional_named_rivers", None)
        assert present == group, "Independent rank64 publication is present"
    else:
        destination.write_bytes(json_bytes(group))
    (DATA / "nl2_hu_b568_locked_medium.json").write_bytes(json_bytes(medium))
    (DATA / "nl2_hu_b568_caller_results.json").write_bytes(
        json_bytes(
            dict(run=RUN, count=3, records=records, paired=group, historical=historical_screen(route))
        )
    )
    print(
        "Authenticated B568 native jobs:",
        [(p["public_board"], len(p["rendered_decision_hands"])) for p in group["pins"]],
    )


if __name__ == "__main__":
    main()
