"""Authenticate the single B765 source run's two completed matrix jobs and four artifacts."""
import argparse
import json
import re
from pathlib import Path

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45340661438
HEAD='d733d57af24b34f1171b312b2e3568ccb584c463'
WORKER='tools/hu_b765_rank150_low_flanks.py'
WORKFLOW='.github/workflows/nl2-hu-b765-rank150-low-flanks.yml'
WORKER_BLOB='3b528ee6849904817131e67063c7beb9aae8792f'
WORKFLOW_BLOB='4adbacda3b55708142f551f045607df4354a6e79'
FLOPS=('9s9h3s','TdTc3d')
JOBS={'9s9h3s':138263273004,'TdTc3d':138263272630}
STEPS=['Verify original A-low private deals and current paired-three routes','Build the pinned native solver',
       'Solve just the new full-size flop root','Preserve the completed original before conditional work',
       'Resume the original root and verify both policies on reachable river checks','Preserve the conditional jobs and original decisions']


def validate(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    assert len(raw['jobs'])==2 and len(raw['artifacts'])==4
    out=dict(run=run,jobs=[],artifacts=[])
    for f in FLOPS:
        job,=[j for j in raw['jobs'] if j['name']==f'solve ({f})']
        out['jobs'].append(job_receipt(job,run,JOBS[f],job['name'],STEPS))
        for prefix in ('B765-root-R150-','B765-R150-'):
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
