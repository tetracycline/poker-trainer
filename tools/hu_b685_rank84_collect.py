"""Authenticate and download the three original B682 native rank84 workers."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time

from hu_b467_river_source_gate import json_bytes, sha

REPO = 'tetracycline/poker-trainer'
REPO_ID = 1438346845
BRANCH = 'fix/nl2-hu-lines-audit-20261118'
WORKFLOW = '.github/workflows/nl2-hu-b682-rank84-checkcalls.yml'
FLOPS = ('Qs8h3d', 'Qh9c4s', 'Kd7s2h')
SOURCE_BLOBS = {
    'tools/hu_b682_rank84.py': '6bd180d507c5e65cf543ed430ce9d7039af0e635',
    'tools/hu_b682_rank84_routes.cjs': '4a701e07bdcc8cc291914517719edc7c681c6c53',
    'tools/hu_b682_stage_prices.py': '7de31f3302c7656c3bf989f4ccc32ebcddd59e15',
    WORKFLOW: '88335f5b7f3c005eb16cc1676609243549c43050',
    'tools/hu_b674_threebet_call_routes.cjs': 'f217abef1567f5e1a6ef3ce7fcef2400cd5f9635',
    'tools/staged/hu_b674_nl2_hu_model.js': 'a98cb80d7762b464064874de39dcff6f4bf5707d',
    'tools/staged/hu_b674_nl2.js': '15aee97e53a156fe073c96a120638a8a3679958f',
}
PRICE_PINS = {
    'nl2_hu_model.js': ('905530800036ae6e57af5a64528223ba5553d634', 'a98cb80d7762b464064874de39dcff6f4bf5707d'),
    'nl2.js': ('09907bc4190c0c05bf7df87cc6ca2d2bbdf5d231', '15aee97e53a156fe073c96a120638a8a3679958f'),
}
REQUIRED_STEPS = {
    'Prepare exact call prices and build the pinned native solver',
    'Solve native flop ancestry and replay genuine turn actor locks',
    'Run actions/upload-artifact@v4',
}


def api(path):
    for attempt in range(4):
        result = subprocess.run(['gh', 'api', 'repos/' + REPO + '/' + path], capture_output=True)
        if result.returncode == 0:
            return result.stdout
        if attempt == 3:
            raise RuntimeError(result.stderr.decode(errors='replace')[-800:])
        time.sleep(2 * (attempt + 1))


def check_source(run, files, run_id, head):
    assert run_id > 0 and re.fullmatch('[0-9a-f]{40}', head)
    assert (run['id'], run['head_sha'], run['head_branch'], run['path']) == (run_id, head, BRANCH, WORKFLOW)
    assert (run['repository']['id'], run['repository']['full_name']) == (REPO_ID, REPO)
    assert files['run'] == run_id and files['head'] == head
    assert set(files['blobs']) == set(SOURCE_BLOBS) | set(PRICE_PINS)
    assert all(files['blobs'][path] == digest for path, digest in SOURCE_BLOBS.items())
    states = []
    for path, (before, after) in PRICE_PINS.items():
        actual = files['blobs'][path]
        assert actual in (before, after), (path, 'unknown source price revision', actual)
        states.append(actual == after)
    assert len(set(states)) == 1, 'The original source must contain one complete known price pair'


def check_worker(job, receipt, flop, run_id, head, attempt):
    assert flop in FLOPS
    assert (job['run_id'], job['head_sha'], job['name'], job['status'], job['conclusion']) == (
        run_id, head, 'solve (' + flop + ')', 'completed', 'success')
    assert job['run_attempt'] == attempt
    successful = {step['name'] for step in job['steps'] if step['status'] == 'completed' and step['conclusion'] == 'success'}
    assert REQUIRED_STEPS <= successful
    source = receipt['workflow_run']
    assert (receipt['name'], source['id'], source['head_sha'], source['repository_id']) == (
        'B682-R84-' + flop, run_id, head, REPO_ID)
    assert not receipt['expired']
    assert re.fullmatch('sha256:[0-9a-f]{64}', receipt['digest'])


def main(args):
    run = json.loads(api('actions/runs/' + str(args.run)))
    files = dict(run=args.run, head=args.head, blobs={})
    for path in sorted(SOURCE_BLOBS.keys() | PRICE_PINS.keys()):
        entry = json.loads(api('contents/' + path + '?ref=' + args.head))
        assert entry['type'] == 'file' and entry['path'] == path
        files['blobs'][path] = entry['sha']
    check_source(run, files, args.run, args.head)
    job_page = json.loads(api('actions/runs/' + str(args.run) + '/jobs?filter=latest&per_page=100'))
    artifact_page = json.loads(api('actions/runs/' + str(args.run) + '/artifacts?per_page=100'))
    assert job_page['total_count'] <= 100 and artifact_page['total_count'] <= 100
    args.output.mkdir(parents=True, exist_ok=True)
    assert not any(args.output.iterdir()), 'Use an empty receipt directory; stale workers must not be mixed'
    (args.output / 'source-run.json').write_bytes(json_bytes(run))
    (args.output / 'source-files.json').write_bytes(json_bytes(files))
    workers = []
    for flop in FLOPS:
        job, = [entry for entry in job_page['jobs'] if entry['name'] == 'solve (' + flop + ')']
        artifact, = [entry for entry in artifact_page['artifacts'] if entry['name'] == 'B682-R84-' + flop]
        receipt = json.loads(api('actions/artifacts/' + str(artifact['id'])))
        assert all(receipt[key] == artifact[key] for key in ('id', 'name', 'digest', 'workflow_run'))
        check_worker(job, receipt, flop, args.run, args.head, run['run_attempt'])
        raw = api('actions/artifacts/' + str(receipt['id']) + '/zip')
        digest = sha(raw)
        assert receipt['digest'] == 'sha256:' + digest
        (args.output / f'{receipt["id"]}.zip').write_bytes(raw)
        (args.output / f'{receipt["id"]}.json').write_bytes(json_bytes(receipt))
        (args.output / f'job-{job["id"]}.json').write_bytes(json_bytes(job))
        workers.append(dict(id=receipt['id'], name=receipt['name'], flop=flop, run=args.run, head=args.head,
            sha256=digest, job_id=job['id'], job_name=job['name'], run_attempt=run['run_attempt']))
    (args.output / 'workers.json').write_bytes(json_bytes(workers))
    print(json.dumps(dict(successful_source_jobs=len(workers), source_run=args.run, source_head=args.head)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=int, required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert args.run > 0 and re.fullmatch('[0-9a-f]{40}', args.head)
    main(args)
