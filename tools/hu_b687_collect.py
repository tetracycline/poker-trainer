"""Authenticate the fixed B684 native run, jobs and original artifact bytes."""
import argparse
import hashlib
import json
from pathlib import Path

from hu_b679_collect import api

REPO="tetracycline/poker-trainer"
REPOSITORY_ID=1438346845
RUN=45310713025
HEAD="30c81f5d06a94610cdb2b9aa3100f4c495352c5f"
WORKFLOW=".github/workflows/nl2-hu-b684-rank103-turns.yml"
FLOPS=("Qs8h4d","Jh8d3c","9c6c3h")
STEPS={"Solve original BB-BTN flop and independently lock the exact turn","Run actions/upload-artifact@v4"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_run(run):
    assert (run["id"],run["head_sha"],run["head_branch"],run["status"],run["conclusion"],run["path"],
            run["repository"]["id"],run["head_repository"]["id"])==(
        RUN,HEAD,"fix/nl2-hu-lines-audit-20261118","completed","success",WORKFLOW,REPOSITORY_ID,REPOSITORY_ID)


def validate_preflight(job):
    assert (job["run_id"],job["head_sha"],job["name"],job["status"],job["conclusion"])==(
        RUN,HEAD,"routes-and-audit","completed","success")
    assert "Verify exact displayed prices and preserve every existing certificate" in {
        s["name"] for s in job["steps"] if s["status"]=="completed" and s["conclusion"]=="success"}


def authenticate(run,job,receipt,pin):
    validate_run(run)
    assert pin["flop"] in FLOPS and (pin["run"],pin["head"],pin["name"])==(RUN,HEAD,"B684-R103-"+pin["flop"])
    assert (job["id"],job["run_id"],job["head_sha"],job["name"],job["status"],job["conclusion"])==(
        pin["job"],RUN,HEAD,"solve ("+pin["flop"]+")","completed","success")
    assert STEPS<={s["name"] for s in job["steps"] if s["status"]=="completed" and s["conclusion"]=="success"}
    origin=receipt["workflow_run"]
    assert (receipt["id"],receipt["name"],receipt["digest"],receipt["expired"],origin["id"],origin["head_sha"],
            origin["repository_id"],origin["head_repository_id"])==(
        pin["id"],pin["name"],"sha256:"+pin["sha256"],False,RUN,HEAD,REPOSITORY_ID,REPOSITORY_ID)


def encoded(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode()


def collect(args):
    assert (args.run,args.head)==(RUN,HEAD),"Only the reviewed native source run/head is allowed"
    args.output.mkdir(parents=True,exist_ok=True)
    run_raw=api("actions/runs/"+str(RUN));run=json.loads(run_raw);validate_run(run)
    jobs_raw=api("actions/runs/"+str(RUN)+"/jobs?per_page=100");jobs_response=json.loads(jobs_raw)
    jobs=jobs_response["jobs"];assert jobs_response["total_count"]==len(jobs)==4
    preflight,=(j for j in jobs if j["name"]=="routes-and-audit");validate_preflight(preflight)
    artifacts_raw=api("actions/runs/"+str(RUN)+"/artifacts?per_page=100");listed=json.loads(artifacts_raw)
    artifacts=listed["artifacts"];assert listed["total_count"]==len(artifacts)==4
    assert {a["name"] for a in artifacts}=={"B684-verified-rank103-routes",*("B684-R103-"+f for f in FLOPS)}
    for name,raw in (("run.json",run_raw),("jobs.json",jobs_raw),("artifacts.json",artifacts_raw)):
        (args.output/name).write_bytes(raw)
    pins=[]
    for flop in FLOPS:
        artifact,=(a for a in artifacts if a["name"]=="B684-R103-"+flop)
        job,=(j for j in jobs if j["name"]=="solve ("+flop+")")
        aid=artifact["id"];receipt_raw=api("actions/artifacts/"+str(aid));receipt=json.loads(receipt_raw)
        pin=dict(id=aid,name=artifact["name"],flop=flop,run=RUN,head=HEAD,sha256=artifact["digest"].removeprefix("sha256:"),job=job["id"])
        authenticate(run,job,artifact,pin);authenticate(run,job,receipt,pin)
        raw=api("actions/artifacts/"+str(aid)+"/zip");assert sha(raw)==pin["sha256"]
        job_raw=encoded(job)
        (args.output/(str(aid)+".json")).write_bytes(receipt_raw)
        (args.output/(str(aid)+".zip")).write_bytes(raw)
        (args.output/("job."+str(job["id"])+".json")).write_bytes(job_raw)
        pin.update(receipt_sha256=sha(receipt_raw),job_receipt_sha256=sha(job_raw),workflow_run_receipt_sha256=sha(run_raw))
        pins.append(pin)
    (args.output/"workers.json").write_bytes(encoded(pins))
    print(json.dumps(dict(source_run=RUN,source_head=HEAD,authenticated_workers=len(pins))))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--run",type=int,default=RUN);cli.add_argument("--head",default=HEAD)
    cli.add_argument("--output",type=Path,required=True)
    collect(cli.parse_args())
