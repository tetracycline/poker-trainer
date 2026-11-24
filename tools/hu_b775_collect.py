"""Authenticate B770's original conditional worker, re-export checkpoint and native output."""
import argparse
import json
from pathlib import Path
import re

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45344058693
HEAD='9fd70b00708fc81a98bafaaaaf01a8889f748b30'
JOB=138274246237
FLOP='7s7h4d'
WORKFLOW='.github/workflows/nl2-hu-b770-rank150-straight-draw.yml'
WORKER='tools/hu_b770_rank150_straight_draw.py'
PINS={WORKER:'737ddbb49bb8873f7dbf88581e1fdc246d11a3e5',WORKFLOW:'1eb450b0d79e50087b74f50478c61d57e0e858d8'}
STEPS=['Verify the B733 source, suited 65 hands and the current rank150 route','Build the pinned native solver',
       'Export the missing third-pot turn ranges and match all 37 B733 root nodes','Preserve the verified original root and newly extracted ranges',
       'Solve the missing turn branches and replay each supported CO and BB deal','Preserve the conditional jobs and original decisions']
SOURCES={'B770-root-R150-'+FLOP:'B770_ROOT_R150_7S7H4D','B770-R150-'+FLOP:'B770_R150_7S7H4D'}


def validate(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    j,=raw['jobs'];job=job_receipt(j,run,JOB,'solve',STEPS)
    assert len(raw['artifacts'])==2 and {a['name'] for a in raw['artifacts']}==set(SOURCES)
    artifacts=[]
    for name in SOURCES:
        a,=[a for a in raw['artifacts'] if a['name']==name]
        assert a['size_in_bytes']>0 and re.fullmatch('sha256:[a-f0-9]{64}',a['digest'])
        artifacts.append(artifact_receipt(a,run,a['id'],name,a['digest'][7:]))
    assert len({a['id'] for a in artifacts})==2
    return dict(run=run,jobs=[job],artifacts=artifacts)


def collect(out):
    out.mkdir(parents=True,exist_ok=True);endpoint=f'actions/runs/{RUN}'
    jobs=json.loads(api(endpoint+'/jobs?per_page=100'));artifacts=json.loads(api(endpoint+'/artifacts?per_page=100'))
    assert (jobs['total_count'],artifacts['total_count'])==(1,2)
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
