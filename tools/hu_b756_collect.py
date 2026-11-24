"""Authenticate the single B754 source run's two completed matrix jobs and four artifacts."""
import argparse
import json
import re
from pathlib import Path

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45336981856
HEAD='fa1044afeb3c1aa8943d94fbdbd224d058093f8c'
WORKER='tools/hu_b754_rank150_paired_six.py'
WORKFLOW='.github/workflows/nl2-hu-b754-rank150-paired-six.yml'
WORKER_BLOB='fc49ca7aff86b3432f389921bb74190fffff94d3'
WORKFLOW_BLOB='aba90088de2d9ec112bc3ba96e0d72512ccec4e4'
FLOPS=('8d8c6d','JcJh6c')
STEPS=['Verify two previous original flops, the A4/A5 suited policies and the new rendered routes','Build the pinned native solver',
       'Solve just the new full-size flop root','Preserve the completed original before conditional work',
       'Resume the original root and verify both policies on reachable river checks','Preserve the conditional jobs and original decisions']


def validate(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    assert len(raw['jobs'])==2 and len(raw['artifacts'])==4
    out=dict(run=run,jobs=[],artifacts=[])
    for f in FLOPS:
        job,=[j for j in raw['jobs'] if j['name']==f'solve ({f})']
        out['jobs'].append(job_receipt(job,run,job['id'],job['name'],STEPS))
        for prefix in ('B754-root-R150-','B754-R150-'):
            a,=[a for a in raw['artifacts'] if a['name']==prefix+f]
            assert re.fullmatch(r'sha256:[0-9a-f]{64}',a['digest']) and a['size_in_bytes']>0
            out['artifacts'].append(artifact_receipt(a,run,a['id'],a['name'],a['digest'][7:]))
    assert len({a['id'] for a in out['artifacts']})==4 and len({j['id'] for j in out['jobs']})==2
    return out


def collect(out):
    out.mkdir(parents=True,exist_ok=True);source=f'actions/runs/{RUN}'
    jobs=json.loads(api(source+'/jobs?per_page=100'))
    artifacts=json.loads(api(source+'/artifacts?per_page=100'))
    assert jobs['total_count']==2 and artifacts['total_count']==4
    auth=validate(dict(run=json.loads(api(source)),jobs=jobs['jobs'],artifacts=artifacts['artifacts']))
    (out/'receipt.json').write_bytes(json_bytes(auth))
    for a in auth['artifacts']:
        target=out/f"{a['id']}.zip"
        data=target.read_bytes() if target.is_file() else api(f"actions/artifacts/{a['id']}/zip")
        assert sha(data)==a['digest'][7:] and len(data)==a['size_in_bytes']
        target.write_bytes(data)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    collect(p.parse_args().output)
