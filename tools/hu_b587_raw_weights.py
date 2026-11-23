"""Recover frozen river inputs by re-exporting raw ranges from the original turn policies."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
from zipfile import ZipFile

from hu_b467_river_source_gate import compact, sha
from hu_b583_frozen_rivers import boundary, load_policy, replay, DATA, PINS, RUST, SOLVER

ARCHIVE=DATA/"solver_evidence/NL2_B587_RAW_RIVER_WEIGHTS.zip"
BASE=DATA/"nl2_hu_b583_frozen_rivers.json"
PATCH=Path("tools/hu_b587_raw_weights.patch")


def recover(archive, spec, pin, previous, originals, driver):
    rank=spec["rank"]
    root, original, original_job, root_sha=load_policy(pin,originals)
    flop,turn,river_prefix=spec["line"].split("/")
    prefix=[*turn.split(),spec["public_board"][-2:],*river_prefix.split()]
    expected=dict(original_job, out="raw.json", extract=[
        *original_job["extract"], dict(prefix=prefix,street=False,raw=True)])
    raw_job=archive.read(f"{rank}/job.json")
    assert json.loads(raw_job)==expected
    observed=archive.read(f"{rank}/raw.json")
    game=json.loads(observed)
    if driver:
        with TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/"job.json").write_bytes(raw_job)
            subprocess.run([driver.resolve(),"job.json"],cwd=folder,check=True)
            rebuilt=json.loads((folder/"raw.json").read_bytes())
        assert all(rebuilt[key]==game[key] for key in ("nodes","hands","pot","stack","flop"))
    assert all(game[k]==original[k] for k in ("flop","pot","stack","hands"))
    # Metadata appended by the original Python pipeline is outside the native output.
    assert {k:v for k,v in original["info"].items() if k not in ("secs","log")}=={
        k:v for k,v in game["info"].items() if k not in ("secs","log")}
    assert game["nodes"][:-1]==original["nodes"]
    node=game["nodes"][-1]
    target,=(n for n in original["nodes"] if (n["board"],n["line"],n["player"])==(
        spec["public_board"],spec["line"],spec["seat"]))
    assert target["wr"] is None and dict(node,wr=None)==target
    for side,weights in enumerate(node["wr"]):
        assert len(weights)==len(game["hands"][side]) and all(0<=w<=1 for w in weights)
    job,src=boundary(spec,pin,originals)
    for seat,key in enumerate(("oop_w","ip_w")):
        job[key]=[[h,w] for h,w in zip(game["hands"][seat],node["wr"][seat],strict=True) if w>0]
    river_job=archive.read(f"{rank}/river/river.job.json")
    river=archive.read(f"{rank}/river/river.json")
    result=replay(spec,pin,job,src,river_job,river)
    assert result["status"]=="VERIFIED" and all(error==dict(max_abs=0.,relative_sum=0.) for error in result["range_errors"])
    result.update(raw_turn_job_sha256=sha(raw_job),raw_turn_output_sha256=sha(observed),
        original_node_count=len(original["nodes"]),raw_weights_sha256=sha(compact(node["wr"])),
        prior_unresolved_output_sha256=previous["output_sha256"],prior_range_errors=previous["range_errors"])
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--originals",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--driver",type=Path,help="Also re-extract the original policies with the full-weight native exporter")
    args=p.parse_args()
    base=BASE.read_bytes()
    original=json.loads(base)
    assert original["solver"]==SOLVER and original["rust"]==RUST
    inputs=json.loads(PINS.read_bytes())
    records=[]
    with ZipFile(ARCHIVE) as archive:
        for spec in inputs:
            group,=(r for r in original["records"] if (r["model_id"],r["public_board"],r["line"],r["seat"])==
                   (spec["model_id"],spec["public_board"],spec["line"],spec["seat"]))
            for old in group["policies"]:
                pin=old["original"]
                if old["status"]!="UNRESOLVED_ROUNDED_BOUNDARY":
                    continue
                assert pin in spec["sources"] and any(e["max_abs"]>=.005 or e["relative_sum"]>=.0001 for e in old["range_errors"])
                policy=recover(archive,spec,pin,old,args.originals,args.driver)
                records.append(dict(rank=spec["rank"],model_id=spec["model_id"],public_board=spec["public_board"],
                                    line=spec["line"],seat=spec["seat"],policy=policy))
    assert {r["rank"] for r in records}=={71,159}
    args.out.write_text(json.dumps(dict(schema="NL2_HU_B587_RAW_RIVER_RANGE_RECOVERY_V1",
        solver=SOLVER,rust=RUST,driver_patch_sha256=sha(PATCH.read_bytes()),base_sha256=sha(base),
        archive_sha256=sha(ARCHIVE.read_bytes()),records=records),sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    main()
