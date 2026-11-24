"""Authenticate the original B737 workflow run, jobs and artifact bytes."""
import argparse
import json
from pathlib import Path
from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_collect import api
from hu_b736_publish import run_receipt, job_receipt, artifact_receipt

RUN=45331068744
HEAD='24c4d5229b9e498b5c2dc5d936354f30effa2c17'
WORKFLOW='.github/workflows/nl2-hu-b737-rank233-rivers.yml'
JOBS={'Ts8s7h':138232143979,'Ts9s6h':138232144194,'Th9h7c':138232144375}
PINS={"Th9h7c":[14892465533,"830545ce252ef79673beb1676627dc861fbcbf019ac394d56992524d388e5465"],"Ts8s7h":[14891632575,"d434c2bd1d1fe162656122d7045d382b08293f201e9a31016c6991425c96af38"],"Ts9s6h":[14891622522,"204cd92bbd740e9f9b8a7a5317e1313cc9c1809c19b8d185d0ed57849a80c380"]}
FILES={WORKFLOW:'012ba655c59e2f3b483f4316ecae9b0caebd1a69','tools/hu_b737_rank233_rivers.py':'d8ea751f8a2daf7594e1caf15f0c95bcc0224054',
       'tools/hu_b737_rank233_routes.cjs':'8b3510f0fd0c85bdc031acf4703dadf3c6f698d9'}
STEPS=['Verify three-street check links, original range, both original policies and exact source jobs','Build the pinned native solver',
       'Extend the original turn extractions and verify all 18 old nodes per policy','Run actions/upload-artifact@v4']


def validate(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    assert len(raw['jobs'])==len(raw['artifacts'])==len(PINS)==3 and set(PINS)==set(JOBS)
    out=dict(run=run,jobs=[],artifacts=[])
    for flop,jid in JOBS.items():
        aid,digest=PINS[flop]
        j,=[x for x in raw['jobs'] if x['id']==jid];a,=[x for x in raw['artifacts'] if x['id']==aid]
        out['jobs'].append(job_receipt(j,run,jid,'solve ('+flop+')',STEPS))
        out['artifacts'].append(artifact_receipt(a,run,aid,'B737-R233-'+flop,digest))
    return out


def collect(out):
    out.mkdir(exist_ok=True,parents=True)
    raw=dict(run=json.loads(api('actions/runs/'+str(RUN))),
        jobs=[json.loads(api('actions/jobs/'+str(j))) for j in JOBS.values()],
        artifacts=[json.loads(api('actions/artifacts/'+str(a))) for a,d in PINS.values()])
    (out/'receipt.json').write_bytes(json_bytes(validate(raw)))
    for aid,digest in PINS.values():
        b=api('actions/artifacts/'+str(aid)+'/zip');assert sha(b)==digest
        (out/(str(aid)+'.zip')).write_bytes(b)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    collect(p.parse_args().output)

