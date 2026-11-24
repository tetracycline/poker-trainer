"""Authenticate only B681's three new completed workers; do not recollect B676."""
import argparse
import hashlib
import json
from pathlib import Path
from hu_b679_collect import api

RUN=45308387321
HEAD="47d7bbeb4f40c73113830a72f299f2aabb1ad7aa"
REPOSITORY_ID=1438346845
WORKFLOW=".github/workflows/nl2-hu-b681-rank229-extra.yml"
WORKERS=[
    {
        "id": 14882375723,
        "name": "B681-SB3-Kd9c5h",
        "flop": "Kd9c5h",
        "run": 45308387321,
        "head": "47d7bbeb4f40c73113830a72f299f2aabb1ad7aa",
        "sha256": "0b8ca55055abb9eec56204cb86f38239256cefb95fdefbf6d50dfa825e57779f",
        "job": 138157708558
    },
    {
        "id": 14880859824,
        "name": "B681-SB3-Ks8d4h",
        "flop": "Ks8d4h",
        "run": 45308387321,
        "head": "47d7bbeb4f40c73113830a72f299f2aabb1ad7aa",
        "sha256": "d2c4a90ba9b83070a431cc60d009cfe6d9ac6c4ea9965254ef25b5ff6b8bd775",
        "job": 138157708856
    },
    {
        "id": 14880879704,
        "name": "B681-SB3-Ks9h3d",
        "flop": "Ks9h3d",
        "run": 45308387321,
        "head": "47d7bbeb4f40c73113830a72f299f2aabb1ad7aa",
        "sha256": "592be3afedec4d60c8a4682e43ba91cb03cc967a74006b8939a9619f5d0f5c53",
        "job": 138157708802
    }
]
STEPS={
    "Build the pinned engine and freeze the actual displayed routes",
    "Solve original GTO and actual OOP partial locks with independent model gates",
    "Run actions/upload-artifact@v4",
}


def authenticate(run,job,receipt,pin):
    assert pin in WORKERS
    assert (run["id"],run["head_sha"],run["status"],run["conclusion"],run["path"],
            run["repository"]["id"],run["head_repository"]["id"])==(
        RUN,HEAD,"completed","success",WORKFLOW,REPOSITORY_ID,REPOSITORY_ID)
    assert (job["id"],job["run_id"],job["head_sha"],job["name"],job["status"],job["conclusion"])==(
        pin["job"],RUN,HEAD,"solve ("+pin["flop"]+")","completed","success")
    assert STEPS<={s["name"] for s in job["steps"] if s["status"]=="completed" and s["conclusion"]=="success"}
    origin=receipt["workflow_run"]
    assert (receipt["id"],receipt["name"],receipt["digest"],receipt["expired"],origin["id"],
            origin["head_sha"],origin["repository_id"],origin["head_repository_id"])==(
        pin["id"],pin["name"],"sha256:"+pin["sha256"],False,RUN,HEAD,REPOSITORY_ID,REPOSITORY_ID)


def collect(args):
    args.output.mkdir(parents=True,exist_ok=True)
    raw=api("actions/runs/"+str(RUN));run=json.loads(raw)
    (args.output/"run.json").write_bytes(raw)
    jobs=json.loads(api("actions/runs/"+str(RUN)+"/jobs?per_page=100"))["jobs"]
    artifacts=json.loads(api("actions/runs/"+str(RUN)+"/artifacts?per_page=100"))["artifacts"]
    assert len(artifacts)==len({a["name"] for a in artifacts})==3
    for pin in WORKERS:
        job,=[j for j in jobs if j["id"]==pin["job"]]
        artifact,=[a for a in artifacts if a["id"]==pin["id"]]
        authenticate(run,job,artifact,pin)
        raw=api("actions/artifacts/"+str(pin["id"]));receipt=json.loads(raw)
        authenticate(run,job,receipt,pin)
        archive=api("actions/artifacts/"+str(pin["id"])+"/zip")
        assert hashlib.sha256(archive).hexdigest()==pin["sha256"]
        (args.output/(str(pin["id"])+".json")).write_bytes(raw)
        (args.output/(str(pin["id"])+".zip")).write_bytes(archive)
        (args.output/("job."+str(pin["job"])+".json")).write_text(json.dumps(job))
    print(json.dumps(dict(authenticated_new_workers=3,source_run=RUN,recollected_old_workers=0)))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output",type=Path,required=True)
    collect(cli.parse_args())

