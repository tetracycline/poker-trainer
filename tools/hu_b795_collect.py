"""Authenticate B793's held-out heart turns and original native solutions."""
import argparse
import json
from pathlib import Path
import re

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45351520919
HEAD='2b8d1e80e6d05a7c001dbdff97155d56e658be1c'
JOB=138298867861
FLOP='Ts7h6s'
WORKFLOW='.github/workflows/nl2-hu-b793-rank230-heart-turns.yml'
WORKER='tools/hu_b793_rank230_heart_turns.py'
PINS={WORKER:'b2e437bc3d3afe827088b73dd3aea0393bd21869',WORKFLOW:'81e4a99cd4e09951ddffb1d20aaaaa1c768451b6'}
STEPS=['Verify five held-out original jobs and the checked two-seat root','Build the pinned native driver',
       'Solve only the four missing chance branches and verify original native outputs','Preserve the immutable flop source and newly solved conditional jobs']

SOURCES={'B793-R230-Ts7h6s':'B793_R230_TS7H6S'}


def validate(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    j,=raw['jobs'];job=job_receipt(j,run,JOB,'solve',STEPS)
    assert len(raw['artifacts'])==1 and {a['name'] for a in raw['artifacts']}==set(SOURCES)
    artifacts=[]
    for name in SOURCES:
        a,=[a for a in raw['artifacts'] if a['name']==name]
        assert a['size_in_bytes']>0 and re.fullmatch('sha256:[a-f0-9]{64}',a['digest'])
        artifacts.append(artifact_receipt(a,run,a['id'],name,a['digest'][7:]))
    assert len({a['id'] for a in artifacts})==1
    return dict(run=run,jobs=[job],artifacts=artifacts)


def collect(out):
    out.mkdir(parents=True,exist_ok=True);endpoint=f'actions/runs/{RUN}'
    jobs=json.loads(api(endpoint+'/jobs?per_page=100'));artifacts=json.loads(api(endpoint+'/artifacts?per_page=100'))
    assert (jobs['total_count'],artifacts['total_count'])==(1,1)
    receipt=validate(dict(run=json.loads(api(endpoint)),jobs=jobs['jobs'],artifacts=artifacts['artifacts']))
    (out/'receipt.json').write_bytes(json_bytes(receipt))
    for a in receipt['artifacts']:
        target=out/f"{a['id']}.zip"
        data=target.read_bytes() if target.exists() else api(f"actions/artifacts/{a['id']}/zip")
        assert len(data)==a['size_in_bytes'] and sha(data)==a['digest'][7:]
        target.write_bytes(data)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    collect(p.parse_args().output)
