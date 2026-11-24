"""Authenticate the completed B766 source and its original conditional CFR output."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_collect import api
from hu_b738_collect import artifact_receipt, job_receipt, run_receipt

RUN = 45341571635
HEAD = '7ea8bb0f6c5f689cfebe8525995642f9365148c6'
JOB = 138266206790
WORKER = 'tools/hu_b766_rank75_chance_turns.py'
WORKFLOW = '.github/workflows/nl2-hu-b766-rank75-chance-turns.yml'
BLOBS = {WORKER:'2624730b49abd405db6aa82b2f87c5e8bf728c64',WORKFLOW:'60b8e0d97cd673f1779c128c91f30b9d197bb348'}
STEPS = ['Reconstruct four held-out original jobs and every two-seat reach weight',
         'Build the pinned native driver','Solve the missing conditional games and replay evidence from native output',
         'Preserve original jobs, decisions and range reconstruction']
ARTIFACT = 14895764870
DIGEST = 'e0f64d46e8513b817b1ca69644caa3702c257ead9f96c07327de392877a0d76d'


def validate(raw):
    r = run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    assert r['run_attempt'] == 1
    job, = raw['jobs']
    artifact, = raw['artifacts']
    j = job_receipt(job,r,JOB,'solve',STEPS)
    a = artifact_receipt(artifact,r,ARTIFACT,'B766-R75-9d8d6d',DIGEST)
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
