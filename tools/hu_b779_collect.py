"""Authenticate B778's three registered conditional turns and original native solutions."""
import argparse
import json
from pathlib import Path
import re

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45345948499
HEAD='117f4fe5dfd263d685dd29db6bd2977c9c82d2e4'
JOB=138280404272
FLOP='Ts9s5h'
WORKFLOW='.github/workflows/nl2-hu-b778-rank150-chance-turns.yml'
WORKER='tools/hu_b778_rank150_chance_turns.py'
PINS={WORKER:'7b2f3fbddb0ff644bd706bba97d0f4d558143dd1',WORKFLOW:'d483daed69928961d565738f1df5700689d68e17'}
STEPS=['Reconstruct four held-out original jobs and every two-seat reach weight','Build the pinned native driver',
       'Solve the missing conditional games and replay evidence from native output','Preserve original jobs, decisions and range reconstruction']
SOURCES={'B778-R150-Ts9s5h':'B778_R150_TS9S5H'}


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
