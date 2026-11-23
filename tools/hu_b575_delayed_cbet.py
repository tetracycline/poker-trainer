"""Verify two conditional half-pot UTG delayed bets, including an explicitly frozen GTO boundary."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, sha
from hu_b483_locked_medium import POOL
from hu_b573_restricted_turn import replay
from hu_checked_gto_boundary import load_original
from solve_hu_missing_branches import EXTRA_SPOTS

MODEL = "ln-opfr-t_model-1ocorr7"
ARCHIVE = EVIDENCE / "NL2_B575_R33_DELAYED_HALF_POT.zip"


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver", required=True, type=Path)
    p.add_argument("--originals", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args=p.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    raw=(solver/"inputs/pool_stats.json").read_bytes()
    assert sha(raw)==POOL
    pool=json.loads(raw)["NL2"]
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    import ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    pins=json.loads(Path("data/nl2_hu_b575_turn_inputs.json").read_bytes())
    assert sha(ARCHIVE.read_bytes())==pins["archive_sha256"]
    registry=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    model=registry["records"][MODEL]
    assert model["frequency_rank"]==33 and model["label"]=="CERT-MULTIBOARD"
    results=[]
    with ZipFile(ARCHIVE) as z:
        for public, spec in pins["boards"].items():
            b,=(b for b in model["certified_3_to_5_exact_flop_boards"] if b["public_board"]==public)
            assert b["actual_exact_action_line"]=="x x/" and b["acting_seat"]==0 and b["medium_50pct_eligible_combos"]==0
            lock,=(l for l in b["nl2_locked_variants"] if l["sha256"]==spec["original_locked_sha256"])
            assert lock["run_id"]==b["source_run_id"] and lock["medium_50pct_eligible_combos"]==0
            rec=dict(model_id=MODEL,public_board=public,line="x x/",seat=0,source_run=lock["run_id"],
                     original_locked_sha256=lock["sha256"], archive=ARCHIVE.name,archive_sha256=pins["archive_sha256"],policies={})
            for v, job in spec["policies"].items():
                parentv=job["parent_version"]
                pin=pins["originals"][str(job["parent_artifact"])]
                parent=load_original(args.originals,job["parent_artifact"],pin,"UTG_CO",b["flop"],b["turn"],parentv,
                                     pot=650,stack=9750,pipeline=pipeline,ranges=ranges,flop_line="x x")
                assert parent["identity"]["source_sha256"]==(b["source_sha256"] if parentv=="gto" else lock["sha256"])
                policy=replay(parent,v,pool,pipeline,z,stem=job["stem"],public=public,line="x x/")
                rec["policies"][v]=dict(policy,parent_version=parentv)
            results.append(rec)
    args.out.write_text(json.dumps(dict(solver=SOLVER,rust=RUST,pool_sha256=POOL,records=results),sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    main()
