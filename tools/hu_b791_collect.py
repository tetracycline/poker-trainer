"""Authenticate B789's two source jobs and independent root checkpoints and their original native solutions."""
import argparse
import json
from pathlib import Path
import re

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45350129410
HEAD='c07e37633bca2933ac09c473e06ebc1a3af4e499'
JOBS={'9h8h7c':138294208605,'Ts7h6s':138294208300}
WORKFLOW='.github/workflows/nl2-hu-b789-rank230-seven-draws.yml'
WORKER='tools/hu_b789_rank230_seven_draws.py'
PINS={WORKER:'84f0186a2b0d96ab7f10ccf81fb7818b0a0db5ae',WORKFLOW:'4dfab898de16c8e51e9a264366dd73d47ecac3fa'}
STEPS=['Verify J7 suited, its compatible BTN hand and the displayed three-street route','Build the pinned native driver',
    'Solve the original native flop once with five registered checked boundaries','Preserve the completed original before turn solves',
    'Solve reachable turns and replay real two-seat strategy checks','Preserve both strategies and all positive and negative source decisions']
SOURCES={name+flop:code+flop.upper() for flop in JOBS for name,code in (
    ('B789-R230-','B789_R230_'),('B789-root-R230-','B789_ROOT_R230_'))}


def validate(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    assert len(raw['jobs'])==2 and len(raw['artifacts'])==4
    result=dict(run=run,jobs=[],artifacts=[])
    for flop,jid in JOBS.items():
        j,=[j for j in raw['jobs'] if j['id']==jid]
        result['jobs'].append(job_receipt(j,run,jid,'solve ('+flop+')',STEPS))
        for prefix in ('B789-R230-','B789-root-R230-'):
            name=prefix+flop
            art,=[a for a in raw['artifacts'] if a['name']==name]
            assert art['size_in_bytes']>0 and re.fullmatch('sha256:[a-f0-9]{64}',art['digest'])
            result['artifacts'].append(artifact_receipt(art,run,art['id'],name,art['digest'][7:]))
    assert len({a['id'] for a in result['artifacts']})==4
    return result


def collect(out):
    out.mkdir(parents=True,exist_ok=True);endpoint=f'actions/runs/{RUN}'
    jobs=json.loads(api(endpoint+'/jobs?per_page=100'));artifacts=json.loads(api(endpoint+'/artifacts?per_page=100'))
    assert (jobs['total_count'],artifacts['total_count'])==(2,4)
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
