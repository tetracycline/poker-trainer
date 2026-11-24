"""Authenticate B785's jack-high conditional turns and original native solutions."""
import argparse
import json
from pathlib import Path
import re

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45349077751
HEAD='2e4609d2ff934037b9bdc2f9fd0e998499eff931'
JOB=138290712257
FLOP='JhTh8c'
WORKFLOW='.github/workflows/nl2-hu-b785-rank230-jack-high.yml'
WORKER='tools/hu_b785_rank230_jack_high.py'
PINS={WORKER:'7f588b749c4c5ddc8392cb895e0772fee49d3dca',WORKFLOW:'f694f1b84b6885aa8b04a5d3bd486810ce368fe7'}
from hu_b784_collect import STEPS

SOURCES={'B785-R230-JhTh8c':'B785_R230_JHTH8C'}


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
