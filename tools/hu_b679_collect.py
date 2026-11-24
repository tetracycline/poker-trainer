"""Authenticate the six immutable, completed B676 worker artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

REPO="tetracycline/poker-trainer"
REPOSITORY_ID=1438346845
RUN=45307442313
HEAD="c7785b29f9fcfc1124e49689bdd80c3e89066f73"
WORKFLOW=".github/workflows/nl2-hu-b676-checked-rivers.yml"
WORKERS=[
    {
        "id": 14880754286,
        "name": "B676-SB3-Kc9d4h",
        "flop": "Kc9d4h",
        "rank": 229,
        "run": 45307442313,
        "head": "c7785b29f9fcfc1124e49689bdd80c3e89066f73",
        "sha256": "7220d620cec1b3f43b101bdcb410aaba6867d1cb4918fd7ae8969b03e45abbdf",
        "job": 138154615628
    },
    {
        "id": 14880984149,
        "name": "B676-SB3-Qd8s3h",
        "flop": "Qd8s3h",
        "rank": 229,
        "run": 45307442313,
        "head": "c7785b29f9fcfc1124e49689bdd80c3e89066f73",
        "sha256": "14830679ca7078285a08220541716f80e5b8c2db248422facb059dfd21ec895f",
        "job": 138154615633
    },
    {
        "id": 14881407371,
        "name": "B676-SB3-Qh9c5d",
        "flop": "Qh9c5d",
        "rank": 229,
        "run": 45307442313,
        "head": "c7785b29f9fcfc1124e49689bdd80c3e89066f73",
        "sha256": "8ff90f7311b17bbcbc741eee84f19491b0013b9cf86e7ab99e185ff22b0173b5",
        "job": 138154615800
    },
    {
        "id": 14882205008,
        "name": "B676-SB3-8h6c3d",
        "flop": "8h6c3d",
        "rank": 230,
        "run": 45307442313,
        "head": "c7785b29f9fcfc1124e49689bdd80c3e89066f73",
        "sha256": "d32ee81980c4645d5cb69918f97b6cb721d7666e0cd7e704fd86ca0f32c60c58",
        "job": 138154615712
    },
    {
        "id": 14880949355,
        "name": "B676-SB3-Jc7d4s",
        "flop": "Jc7d4s",
        "rank": 230,
        "run": 45307442313,
        "head": "c7785b29f9fcfc1124e49689bdd80c3e89066f73",
        "sha256": "488f1d32fa4cfd40566545e16babf0e6590883b18a63a4237b459dcafe93f828",
        "job": 138154615680
    },
    {
        "id": 14881358105,
        "name": "B676-SB3-Td8c5h",
        "flop": "Td8c5h",
        "rank": 230,
        "run": 45307442313,
        "head": "c7785b29f9fcfc1124e49689bdd80c3e89066f73",
        "sha256": "c124b82abb05e0c28a6c0a4c19ad81e11178606f70b2dd415e47026fae1180b9",
        "job": 138154615418
    }
]
REQUIRED_STEPS={
    "Build the pinned engine and freeze the actual displayed routes",
    "Solve original GTO and actual OOP partial locks with independent model gates",
    "Run actions/upload-artifact@v4",
}


def api(path):
    for attempt in range(4):
        result=subprocess.run(["gh","api","repos/"+REPO+"/"+path],capture_output=True)
        if result.returncode==0:return result.stdout
        if attempt==3:raise RuntimeError(result.stderr.decode(errors="replace")[-800:])
        time.sleep(2*(attempt+1))


def authenticate(run,job,receipt,pin):
    assert pin in WORKERS
    assert (run["id"],run["head_sha"],run["status"],run["conclusion"],run["path"],
            run["repository"]["id"],run["head_repository"]["id"])==(
        RUN,HEAD,"completed","success",WORKFLOW,REPOSITORY_ID,REPOSITORY_ID)
    assert (job["id"],job["run_id"],job["head_sha"],job["name"],job["status"],job["conclusion"])==(
        pin["job"],RUN,HEAD,"solve ("+pin["flop"]+")","completed","success")
    assert REQUIRED_STEPS<={s["name"] for s in job["steps"]
        if s["status"]=="completed" and s["conclusion"]=="success"}
    origin=receipt["workflow_run"]
    assert (receipt["id"],receipt["name"],receipt["digest"],receipt["expired"],
            origin["id"],origin["head_sha"],origin["repository_id"],origin["head_repository_id"])==(
        pin["id"],pin["name"],"sha256:"+pin["sha256"],False,RUN,HEAD,REPOSITORY_ID,REPOSITORY_ID)


def collect(args):
    args.output.mkdir(parents=True,exist_ok=True)
    run_raw=api("actions/runs/"+str(RUN));run=json.loads(run_raw)
    jobs=json.loads(api("actions/runs/"+str(RUN)+"/jobs?per_page=100"))["jobs"]
    artifacts=json.loads(api("actions/runs/"+str(RUN)+"/artifacts?per_page=100"))["artifacts"]
    assert len({a["name"] for a in artifacts})==len(artifacts)
    (args.output/"run.json").write_bytes(run_raw)
    for pin in WORKERS:
        job,=[j for j in jobs if j["id"]==pin["job"]]
        listed,=[a for a in artifacts if a["id"]==pin["id"]]
        raw=api("actions/artifacts/"+str(pin["id"]));receipt=json.loads(raw)
        authenticate(run,job,listed,pin)
        authenticate(run,job,receipt,pin)
        archive=api("actions/artifacts/"+str(pin["id"])+"/zip")
        assert hashlib.sha256(archive).hexdigest()==pin["sha256"]
        (args.output/(str(pin["id"])+".json")).write_bytes(raw)
        (args.output/(str(pin["id"])+".zip")).write_bytes(archive)
        (args.output/("job."+str(pin["job"])+".json")).write_text(json.dumps(job))
    print(json.dumps(dict(authenticated_workers=len(WORKERS),source_run=RUN,source_head=HEAD)))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output",type=Path,required=True)
    collect(cli.parse_args())

