"""Restore the exact published B702 receipts for B710's full original-job replay."""
import argparse
import json
from pathlib import Path
import subprocess

import hu_b702_collect as original
import hu_b702_resume_collect as resumed
from hu_b467_river_source_gate import json_bytes, sha

PUBLISHED = '61681538aa2d03411ecbf21bc69c2ebb2b823c71'
RECEIPT_PATH = 'data/solver_evidence/partial/b702_auth_receipt.json'
RECEIPT_SHA256 = '2b99a7b6423272c71c7072ffde6e80172953901a60b47d7995150c291538828b'


def published_bytes(path):
    raw = subprocess.check_output(['git', 'show', PUBLISHED + ':' + path])
    assert Path(path).read_bytes() == raw, ('Published B702 file changed', path)
    return raw


def save_worker(output, run, pin, job, artifact, archive):
    resumed.authenticate(run, job, artifact, pin)
    assert sha(archive) == pin['sha256']
    (output / (str(pin['id']) + '.zip')).write_bytes(archive)
    (output / (str(pin['id']) + '.json')).write_bytes(json_bytes(artifact))
    (output / ('job.' + str(pin['job']) + '.json')).write_bytes(json_bytes(job))


def restore(output):
    resumed.source_bytes()
    subprocess.run(['git', 'merge-base', '--is-ancestor', PUBLISHED, 'HEAD'], check=True)
    raw = published_bytes(RECEIPT_PATH)
    assert sha(raw) == RECEIPT_SHA256
    receipt = json.loads(raw)
    run = receipt['run']
    assert (run['id'], run['head_sha'], run['status'], run['conclusion']) == (
        resumed.RUN, resumed.HEAD, 'completed', 'success')
    assert receipt['source'] == dict(head=resumed.HEAD, blobs=resumed.SOURCE_BLOBS)
    actual_workers = json.loads(published_bytes('data/nl2_hu_b702_workers.json'))
    assert actual_workers == resumed.WORKERS and len(actual_workers) == 6
    assert json.loads(published_bytes('data/nl2_hu_b702_original_root_workers.json')) == original.WORKERS
    workers = {entry['artifact']['id']: entry for entry in receipt['workers']}
    assert len(receipt['workers']) == 6 and workers.keys() == {pin['id'] for pin in actual_workers}
    output.mkdir(parents=True, exist_ok=True)
    assert not any(output.iterdir()), 'Use an empty B702 receipt directory'
    (output / 'run.json').write_bytes(json_bytes(run))
    (output / 'source-blobs.json').write_bytes(json_bytes(receipt['source']))
    (output / 'workers.json').write_bytes(json_bytes(actual_workers))
    roots = receipt['original_roots']
    assert roots['pin'] == resumed.ROOTS
    aggregate_path = 'data/solver_evidence/partial/b702_authenticated_original_roots.zip'
    assert roots['published_archive'] == aggregate_path
    aggregate = published_bytes(aggregate_path)
    save_worker(output, run, resumed.ROOTS, roots['job'], roots['artifact'], aggregate)
    old = output / 'original-roots'
    resumed.unpack_roots(aggregate, old)
    assert json.loads((old / 'run.json').read_bytes()) == roots['original_run']
    price = receipt['price_audit']
    assert price['pin'] == original.PRICE
    assert json.loads((old / (str(original.PRICE['id']) + '.json')).read_bytes()) == price['artifact']
    assert json.loads((old / ('job.' + str(original.PRICE['job']) + '.json')).read_bytes()) == price['job']
    assert (old / (str(original.PRICE['id']) + '.zip')).read_bytes() == published_bytes(
        'data/solver_evidence/partial/b702_source_price_gate.zip')
    for pin in original.WORKERS:
        path = f'data/solver_evidence/NL2_B696_R{pin["rank"]}_{pin["flop"].upper()}.zip'
        archive = published_bytes(path)
        assert sha(archive) == pin['sha256'] and archive == (old / (str(pin['id']) + '.zip')).read_bytes()
    for pin in actual_workers:
        entry = workers[pin['id']]
        path = f'data/solver_evidence/NL2_B705_R{pin["rank"]}_{pin["flop"].upper()}.zip'
        save_worker(output, run, pin, entry['job'], entry['artifact'], published_bytes(path))
    print(json.dumps(dict(published_commit=PUBLISHED, receipt_sha256=RECEIPT_SHA256,
        authenticated_original_root_archives=6, authenticated_continuation_archives=6,
        original_root_run=original.RUN, continuation_run=resumed.RUN)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    restore(parser.parse_args().output)
