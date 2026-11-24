"""Collect the three authenticated B711 native multi-size worker archives."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_collect import BRANCH, REPO, REPO_ID, api

RUN = 45324358830
HEAD = 'd9886707905cb909e60ded0fe213321286457a4e'
WORKFLOW = '.github/workflows/nl2-hu-b711-co-bb-lead-rivers.yml'
JOBS = {'9d7h4c': 138210244846, '8s6d2c': 138210244790, '7c5d3h': 138210244617}
ARTIFACTS = {
    "8s6d2c": [
        14889615852,
        "670f9d12a6e33b5df46b1475506b18a9c3946b9fdcbb461da0542f5ea6c30644"
    ],
    "9d7h4c": [
        14889246787,
        "d4f480e69e5c4b83c683f86dd0d051d9a2b5fde44be4d874ab505841e953fbe9"
    ],
    "7c5d3h": [
        14888559779,
        "51938d92c6f97346e824df1a9f0b896a8c682620f1e8d72ae36565f70f37be45"
    ]
}
STEPS = {
    'Freeze actual UI routes and verify pinned CO-BB ranges and exact prices',
    'Build the pinned native solver',
    'Solve one original flop and the reachable multi-size GTO and actor-lock continuations',
    'Run actions/upload-artifact@v4',
}
BLOBS = {
    "data/nl2_hu_b485_original_artifacts.json": "51940e0a9a39503e95419c0e66d8a7a872288d1e",
    ".github/workflows/nl2-hu-b711-co-bb-lead-rivers.yml": "db6df71cced200290c6a6504110ffee58935d0df",
    "data/nl2_hu_multiboard_status_current.json": "df113d527a0027722ea5af27b8e493e6b79dd7f5",
    "data/nl2_hu_verified_extensions.json": "c774695a895477688a445dc0737b0c4ba133cca4",
    "hwrange.js": "1871d8706adf85e5e6e0f4a7ba94f72454bdb06f",
    "lines_data.js": "a0c64c5cb7f611d23edfa21518fce51347a9e877",
    "nl2.js": "15aee97e53a156fe073c96a120638a8a3679958f",
    "nl2_hu_model.js": "b4a308a0f65b707f43f41f0b354cec87c08d5af6",
    "nl2_reach.js": "45a600fdfe80781a550f4f3dc4b2914d4771c972",
    "nl2_rules.js": "bf96f090d114b932f96a2a56dadc00dc94cb0939",
    "nl2_titles.js": "7fea5003d96b48fd06ff80c192c38198979551d4",
    "tools/hu_b463_rank45_gate.py": "3f2fb4378667b9bb8397f7929e1469e86dd3c77b",
    "tools/hu_b467_river_source_gate.py": "57d9eac04b074eb58e54ede0de384682fad35062",
    "tools/hu_b470_rank73_new_rivers.py": "39336981ae910b385744a2b0aaea237397babb38",
    "tools/hu_b483_locked_medium.py": "018ac485d3fc115f125c777399d96ce38b0f5f04",
    "tools/hu_b568_caller_rivers.py": "e69bda7fe46c3dd18a48dee1bb97f965ab2813f7",
    "tools/hu_b580_rank27_rivers.py": "bfe7f61342593b625e16670367401b595139004e",
    "tools/hu_b637_rank57.py": "86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9",
    "tools/hu_b711_bb_lead_rivers.py": "7ba3ce3a3120378cf8de8c252eda0298365714e3",
    "tools/hu_b711_bb_lead_routes.cjs": "0a18b2f5f11d725244cdaf5091ede76f26272a39",
    "tools/hu_checked_gto_boundary.py": "219f46b0a259fa3e71f1225046ab5b12c44c28c6",
    "tools/hu_sequential_cfr_reach.py": "f26df926c088e5b4117bb911956cbc5031e2458d",
    "tools/lines_pipeline/common.py": "7338a5593f19dd878aba5cb21690bc9cf90365b3",
    "tools/lines_pipeline/run10_common.py": "9422f8fdff8dfeca245bae48ded7fc38353332f0",
    "tools/lines_pipeline/vclass.py": "512f315c14baa2eb1af908a9f3cbc1f68d57e533",
    "tools/verify_hu_multiboard_100bb.py": "df06b9480c0beef93165c46b13e71dd641f82177"
}


def verify_run(run, files):
    assert (run['id'], run['head_sha'], run['head_branch'], run['path'], run['status'], run['conclusion']) == (
        RUN, HEAD, BRANCH, WORKFLOW, 'completed', 'success')
    assert (run['repository']['id'], run['repository']['full_name']) == (REPO_ID, REPO)
    assert files == dict(run=RUN, head=HEAD, blobs=BLOBS)


def verify_worker(flop, run, job, artifact):
    aid, digest = ARTIFACTS[flop]
    assert (job['id'], job['run_id'], job['head_sha'], job['name'], job['run_attempt'], job['status'], job['conclusion']) == (
        JOBS[flop], RUN, HEAD, f'solve ({flop})', run['run_attempt'], 'completed', 'success')
    assert STEPS <= {s['name'] for s in job['steps'] if s['status'] == 'completed' and s['conclusion'] == 'success'}
    assert (artifact['id'], artifact['name'], artifact['digest'], artifact['expired']) == (
        aid, 'B711-CO-BB-' + flop, 'sha256:' + digest, False)
    origin = artifact['workflow_run']
    assert (origin['id'], origin['head_sha'], origin['head_branch'], origin['repository_id'], origin['head_repository_id']) == (
        RUN, HEAD, BRANCH, REPO_ID, REPO_ID)
    return dict(flop=flop, run=RUN, head=HEAD, job_id=job['id'], id=aid, sha256=digest, name=artifact['name'])


def collect(output):
    assert set(ARTIFACTS) == set(JOBS) and len({aid for aid, _ in ARTIFACTS.values()}) == 3
    output.mkdir(parents=True, exist_ok=True)
    assert not any(output.iterdir()), 'Use an empty receipt directory'
    run = json.loads(api(f'actions/runs/{RUN}'))
    tree = json.loads(api(f'git/trees/{HEAD}?recursive=1'))
    assert not tree.get('truncated')
    files = dict(run=RUN, head=HEAD, blobs={e['path']: e['sha'] for e in tree['tree'] if e['path'] in BLOBS and e['type'] == 'blob'})
    verify_run(run, files)
    (output/'source-run.json').write_bytes(json_bytes(run))
    (output/'source-files.json').write_bytes(json_bytes(files))
    listed = json.loads(api(f'actions/runs/{RUN}/artifacts?per_page=100'))
    jobs = json.loads(api(f'actions/runs/{RUN}/jobs?filter=latest&per_page=100'))
    assert jobs['total_count'] == listed['total_count'] == 3
    workers = []
    for flop, job_id in JOBS.items():
        job, = [j for j in jobs['jobs'] if j['id'] == job_id]
        aid, digest = ARTIFACTS[flop]
        item, = [a for a in listed['artifacts'] if a['id'] == aid]
        raw = api(f'actions/artifacts/{aid}')
        artifact = json.loads(raw)
        assert verify_worker(flop, run, job, item) == verify_worker(flop, run, job, artifact)
        archive = api(f'actions/artifacts/{aid}/zip')
        assert sha(archive) == digest
        (output/f'{aid}.zip').write_bytes(archive)
        (output/f'{aid}.json').write_bytes(raw)
        (output/f'job-{job_id}.json').write_bytes(json_bytes(job))
        workers.append(verify_worker(flop, run, job, artifact))
    (output/'workers.json').write_bytes(json_bytes(workers))
    print(json.dumps(dict(authenticated_workers=len(workers), run=RUN)))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output', type=Path, required=True)
    collect(cli.parse_args().output)
