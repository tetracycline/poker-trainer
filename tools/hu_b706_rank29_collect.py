"""Authenticate the completed B703 original native workers for rank29."""
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
WORKFLOW = '.github/workflows/nl2-hu-b703-rank29-highcards.yml'
SOURCE_RUN = 45317650807
SOURCE_HEAD = 'd59466ad88881943ff56ab8d9a102f05ecf683b1'
FLOPS = ('Kd9d4c', 'Qh8h3s', 'As7s2d')
SOURCE_BLOBS = {
    "data/nl2_hu_b485_original_artifacts.json": "51940e0a9a39503e95419c0e66d8a7a872288d1e",
    "tools/hu_b703_rank29_highcards.py": "1adbb4fe4bd2ad36643dd3e79bf5f41cd9580ac8",
    "tools/hu_b703_rank29_routes.cjs": "8ac70c349c5f60d35578e9f85fda0d2ec08d5384",
    ".github/workflows/nl2-hu-b703-rank29-highcards.yml": "fef72de93b415b0a51fa80be94e7e63687700d26",
    "lines_data.js": "a0c64c5cb7f611d23edfa21518fce51347a9e877",
    "nl2_rules.js": "bf96f090d114b932f96a2a56dadc00dc94cb0939",
    "hwrange.js": "1871d8706adf85e5e6e0f4a7ba94f72454bdb06f",
    "nl2_reach.js": "45a600fdfe80781a550f4f3dc4b2914d4771c972",
    "nl2_titles.js": "7fea5003d96b48fd06ff80c192c38198979551d4",
    "nl2_hu_model.js": "a98cb80d7762b464064874de39dcff6f4bf5707d",
    "nl2.js": "15aee97e53a156fe073c96a120638a8a3679958f",
    "tools/hu_trainer_route_contract.cjs": "31370c779d22b7d895e76f1030504909019dbe5a",
    "data/nl2_hu_verified_extensions.json": "010db6219408cd8eaa657007d8aeed240e650942",
    "data/solver_evidence/NL2_B580_R27_LMP.zip": "332740cf24b11a13454a548029a665fdff9d46d3",
    "tools/hu_b659_rank29_monotone.py": "167c1a6de9c98882d8487e493368585b92adc833",
    "tools/hu_b582_rank29_reach.py": "191862b9aa1f869b78e40e621f6325f15be61c9e",
    "tools/hu_b582_rank29_route.cjs": "96eaa79cef526cbc68db6d4b1c9b2698c2cf972e",
    "tools/hu_b637_rank57.py": "86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9",
    "tools/hu_b481_rank27_limp_rivers.py": "1df87de10baee731af50c89c6297bf67e3543098"
}
EXPECTED_JOBS = {'Kd9d4c': 138188261638, 'Qh8h3s': 138188261471, 'As7s2d': 138188261159}
ARTIFACT_PINS = {
    'Qh8h3s': (14886916567, '50f9c74973dc0a57a7da6f6bc33be625a45398fde3179b79478205b471156a4e'),
    'Kd9d4c': (14886661359, '6b5433a9e86cfb22bf3dd007d02db4b5eeadeaa65edadcae559b4c22c7f1407f'),
    'As7s2d': (14885633773, '67cbdffafea7609d9fdedb4e4d3804edaa96ed93ab6d2cbc54a6564a66adea8b'),
}
REQUIRED_STEPS = {
    'Verify genuine LMP ranges and exact three-street UI prices',
    'Build the pinned native solver',
    'Solve native roots and only reachable displayed GTO and actor-locked rivers',
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


def check_source(run, files):
    assert (run['id'], run['head_sha'], run['head_branch'], run['path']) == (SOURCE_RUN, SOURCE_HEAD, BRANCH, WORKFLOW)
    assert (run['repository']['id'], run['repository']['full_name']) == (REPO_ID, REPO)
    assert (run['status'], run['conclusion']) == ('completed', 'success')
    assert (files['run'], files['head'], files['blobs']) == (SOURCE_RUN, SOURCE_HEAD, SOURCE_BLOBS)


def check_worker(job, receipt, flop, attempt):
    assert flop in FLOPS and set(ARTIFACT_PINS) == set(FLOPS), 'Original completed artifact pins are required'
    artifact_id, digest = ARTIFACT_PINS[flop]
    assert (job['id'], receipt['id'], receipt['digest']) == (EXPECTED_JOBS[flop], artifact_id, 'sha256:' + digest)
    assert (job['run_id'], job['head_sha'], job['name'], job['status'], job['conclusion']) == (
        SOURCE_RUN, SOURCE_HEAD, 'solve (' + flop + ')', 'completed', 'success')
    assert job['run_attempt'] == attempt
    successful = {step['name'] for step in job['steps'] if step['status'] == 'completed' and step['conclusion'] == 'success'}
    assert REQUIRED_STEPS <= successful
    source = receipt['workflow_run']
    assert (receipt['name'], source['id'], source['head_sha'], source['repository_id']) == (
        'B703-R29-' + flop, SOURCE_RUN, SOURCE_HEAD, REPO_ID)
    assert not receipt['expired'] and re.fullmatch('sha256:[0-9a-f]{64}', receipt['digest'])


def main(args):
    assert set(ARTIFACT_PINS) == set(FLOPS), 'Pin completed original artifacts before publishing this collector'
    run = json.loads(api('actions/runs/' + str(SOURCE_RUN)))
    files = dict(run=SOURCE_RUN, head=SOURCE_HEAD, blobs={})
    for path in sorted(SOURCE_BLOBS):
        entry = json.loads(api('contents/' + path + '?ref=' + SOURCE_HEAD))
        assert entry['type'] == 'file' and entry['path'] == path
        files['blobs'][path] = entry['sha']
    check_source(run, files)
    job_page = json.loads(api('actions/runs/' + str(SOURCE_RUN) + '/jobs?filter=latest&per_page=100'))
    artifact_page = json.loads(api('actions/runs/' + str(SOURCE_RUN) + '/artifacts?per_page=100'))
    assert job_page['total_count'] <= 100 and artifact_page['total_count'] <= 100
    args.output.mkdir(parents=True, exist_ok=True)
    assert not any(args.output.iterdir()), 'Use an empty receipt directory'
    (args.output / 'source-run.json').write_bytes(json_bytes(run))
    (args.output / 'source-files.json').write_bytes(json_bytes(files))
    workers = []
    for flop in FLOPS:
        job, = [entry for entry in job_page['jobs'] if entry['id'] == EXPECTED_JOBS[flop]]
        artifact, = [entry for entry in artifact_page['artifacts'] if entry['id'] == ARTIFACT_PINS[flop][0]]
        receipt = json.loads(api('actions/artifacts/' + str(artifact['id'])))
        assert all(receipt[key] == artifact[key] for key in ('id', 'name', 'digest', 'workflow_run'))
        check_worker(job, receipt, flop, run['run_attempt'])
        raw = api('actions/artifacts/' + str(receipt['id']) + '/zip')
        digest = sha(raw)
        assert receipt['digest'] == 'sha256:' + digest
        (args.output / f'{receipt["id"]}.zip').write_bytes(raw)
        (args.output / f'{receipt["id"]}.json').write_bytes(json_bytes(receipt))
        (args.output / f'job-{job["id"]}.json').write_bytes(json_bytes(job))
        workers.append(dict(id=receipt['id'], name=receipt['name'], flop=flop, run=SOURCE_RUN, head=SOURCE_HEAD,
            sha256=digest, job_id=job['id'], job_name=job['name'], run_attempt=run['run_attempt']))
    (args.output / 'workers.json').write_bytes(json_bytes(workers))
    print(json.dumps(dict(successful_source_jobs=len(workers), source_run=SOURCE_RUN, source_head=SOURCE_HEAD)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args())
