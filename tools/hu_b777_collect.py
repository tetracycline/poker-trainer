"""Authenticate the completed B776 source and its one original NL2 conditional CFR job."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_collect import api
from hu_b738_collect import artifact_receipt, job_receipt, run_receipt

RUN = 45344964385
HEAD = '4d62d03453a4316ec3377c67d7b07f78e5c0311f'
JOB = 138277195818
WORKER = 'tools/hu_b776_rank150_checked_broadway.py'
WORKFLOW = '.github/workflows/nl2-hu-b776-rank150-checked-broadway.yml'
BLOBS = {WORKER:'d98b615c2e72b6531036b8e2419ccc522cbf94cf',WORKFLOW:'b60ec56fc42320c3fad8a23f005e2bd43b3037cd'}
STEPS = ['Verify the pinned GTO and all ten actual KdJd river-check deals',
         'Build the pinned native solver','Solve just the missing measured IP-hero policy and replay the exact jobs',
         'Preserve the original GTO and new exp_ip source']
ARTIFACT = 14897114584
DIGEST = 'e67bf9ca0b717bb175cfa32dd32cec75ef2398a718bc5287a3f83cac66e6b118'


def validate(raw):
    r = run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    assert r['run_attempt'] == 1
    job, = raw['jobs']
    artifact, = raw['artifacts']
    j = job_receipt(job,r,JOB,'solve',STEPS)
    a = artifact_receipt(artifact,r,ARTIFACT,'B776-R150-TdTc3d-2c',DIGEST)
    return dict(run=r,jobs=[j],artifacts=[a])


def collect(output):
    output.mkdir(exist_ok=True,parents=True)
    endpoint = 'actions/runs/'+str(RUN)
    jobs = json.loads(api(endpoint+'/jobs?per_page=100'))
    artifacts = json.loads(api(endpoint+'/artifacts?per_page=100'))
    assert jobs['total_count'] == artifacts['total_count'] == 1
    receipted = validate(dict(run=json.loads(api(endpoint)),jobs=jobs['jobs'],artifacts=artifacts['artifacts']))
    original = api('actions/artifacts/'+str(ARTIFACT)+'/zip')
    assert sha(original) == DIGEST and len(original) == receipted['artifacts'][0]['size_in_bytes']
    (output/'receipt.json').write_bytes(json_bytes(receipted))
    (output/(str(ARTIFACT)+'.zip')).write_bytes(original)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',type=Path,required=True)
    collect(cli.parse_args().output)
