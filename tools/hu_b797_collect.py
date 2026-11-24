"""Authenticate the B796 checked Qc original GTO and measured IP-hero CFR jobs."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_collect import api
from hu_b738_collect import artifact_receipt, job_receipt, run_receipt

RUN=45352305090
HEAD='cc225dbdd69d9769a84a3316f7ddb9136834d99f'
JOB=138301524002
WORKER='tools/hu_b796_rank309_checked_qc.py'
ROUTE='tools/hu_b796_rank309_routes.cjs'
WORKFLOW='.github/workflows/nl2-hu-b796-rank309-checked-qc.yml'
BLOBS={WORKER:'05e955e340e5878b2ebaaee98a3d1a7665228a62',ROUTE:'9c13636a32df84d9776f0b1b6fee51a9357c553c',
       WORKFLOW:'8c4f00397350f19574e03cddf935ad0cddafdd18'}
STEPS=['Verify the saved flop, preflop action ranges and exact Qc weights','Build the pinned native solver',
       'Solve both Qc policies and replay the original files','Run actions/upload-artifact@v4']
ARTIFACT=14900249054
DIGEST='dce072890f25f06313f19fe7a46e751bbb116497e81514c717297b4f6c3c0670'


def validate(raw):
    r = run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    assert r['run_attempt'] == 1
    job, = raw['jobs']
    artifact, = raw['artifacts']
    j = job_receipt(job,r,JOB,'solve',STEPS)
    a = artifact_receipt(artifact,r,ARTIFACT,'B796-R309-9h7h5h-Qc',DIGEST)
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
