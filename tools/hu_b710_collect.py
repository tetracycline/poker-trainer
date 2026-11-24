"""Authenticate the completed B709 original native workers for rank89."""
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
WORKFLOW = '.github/workflows/nl2-hu-b709-rank89-extra.yml'
SOURCE_RUN = 45322275998
SOURCE_HEAD = 'b2b5dd89fc9dcc17bff547099c2b0581721366f9'
FLOPS = ('Td8c3h', 'Jh7d4c', 'Qc9s5d')
SOURCE_BLOBS = {
  "tools/hu_b696_turn_call_rivers.py": "ca9d29bbe212262dd5f834714779a339e8204c3c",
  "tools/hu_b705_resume_turn_call.py": "65da6780b509e42873a6fce2aaeda37f3dcba4dc",
  "tools/hu_b696_turn_call_routes.cjs": "c3e61df26eba23f6b15be5f5e9d181c1a4fa7e5b",
  "tools/hu_b637_rank57.py": "86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9",
  "tools/hu_b568_caller_rivers.py": "e69bda7fe46c3dd18a48dee1bb97f965ab2813f7",
  "tools/staged/hu_b696_nl2_hu_model.js": "b4a308a0f65b707f43f41f0b354cec87c08d5af6",
  "tools/staged/hu_b696_trainer_route_contract.cjs": "3b10524228c357552bb3f1eac88e17f9b2459b32",
  "nl2.js": "15aee97e53a156fe073c96a120638a8a3679958f",
  "tools/hu_b709_rank89_extra.py": "cad817ed08efd7d6eeb4dfc2774c92bbe1d81df0",
  ".github/workflows/nl2-hu-b709-rank89-extra.yml": "26de438f523c38f52e3e7441a05c6bc0530f9c1c",
  "lines_data.js": "a0c64c5cb7f611d23edfa21518fce51347a9e877",
  "nl2_rules.js": "bf96f090d114b932f96a2a56dadc00dc94cb0939",
  "hwrange.js": "1871d8706adf85e5e6e0f4a7ba94f72454bdb06f",
  "nl2_reach.js": "45a600fdfe80781a550f4f3dc4b2914d4771c972",
  "nl2_titles.js": "7fea5003d96b48fd06ff80c192c38198979551d4",
  "nl2_hu_model.js": "a98cb80d7762b464064874de39dcff6f4bf5707d",
  "data/nl2_hu_b485_original_artifacts.json": "51940e0a9a39503e95419c0e66d8a7a872288d1e",
  "tools/hu_b483_locked_medium.py": "018ac485d3fc115f125c777399d96ce38b0f5f04",
  "tools/hu_sequential_cfr_reach.py": "f26df926c088e5b4117bb911956cbc5031e2458d",
  "tools/hu_checked_gto_boundary.py": "219f46b0a259fa3e71f1225046ab5b12c44c28c6",
  "tools/hu_b470_rank73_new_rivers.py": "39336981ae910b385744a2b0aaea237397babb38",
  "tools/hu_reverified_board_pair.py": "ac58961ba8890d989165b03e3432d4f27b9cd5c6",
  "tools/hu_trainer_route_gate.py": "c58b3391a35b95563bb90a6bc898e0b4114f9486",
  "tools/hu_board_reach_corrections.py": "002b20cedf32ef43bf0bbd1cf1ae2c7d0bec666a",
  "tools/verify_hu_multiboard_100bb.py": "df06b9480c0beef93165c46b13e71dd641f82177",
  "tools/hu_b467_river_source_gate.py": "57d9eac04b074eb58e54ede0de384682fad35062",
  "tools/lines_pipeline/vclass.py": "512f315c14baa2eb1af908a9f3cbc1f68d57e533",
  "tools/lines_pipeline/common.py": "7338a5593f19dd878aba5cb21690bc9cf90365b3",
  "tools/lines_pipeline/run10_common.py": "9422f8fdff8dfeca245bae48ded7fc38353332f0"
}
EXPECTED_JOBS = {'Td8c3h': 138203399181, 'Jh7d4c': 138203399462, 'Qc9s5d': 138203399496}
ARTIFACT_PINS = {
    "Td8c3h": [
        14888542529,
        "139033aee47ce8525da1a56036af1a45238b79db8286aaefd8304fa73013c077"
    ],
    "Qc9s5d": [
        14888232855,
        "1aac3eb315201bc898b95b0ea74e787d6e04e393ad8ede6b33199557bc16507f"
    ],
    "Jh7d4c": [
        14887499681,
        "c87233d0e22251cf08478d38acb9b6831e71d12e5cb5a5560cf696ef7643ee95"
    ]
}

REQUIRED_STEPS = {
    'Verify pinned staged prices, original ranges and all three-street UI witnesses',
    'Build the pinned native solver',
    'Solve new original roots and only strict reachable river GTO and actor locks',
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
        'B709-R89-' + flop, SOURCE_RUN, SOURCE_HEAD, REPO_ID)
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
