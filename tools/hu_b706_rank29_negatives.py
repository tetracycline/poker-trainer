"""Preserve completed B703 root negatives after exact source-head replay; never change labels."""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from zipfile import ZipFile

from hu_b467_river_source_gate import json_bytes, sha
from hu_b706_rank29_collect import FLOPS, SOURCE_RUN, SOURCE_HEAD, SOURCE_BLOBS, check_source, check_worker
from hu_sequential_cfr_reach import accepted, cardkey
from hu_b582_rank29_reach import rendered
from hu_b703_rank29_highcards import CASES, MODEL, LINE

VALIDATION_PINS = {
    "tools/hu_b703_rank29_highcards.py": "1adbb4fe4bd2ad36643dd3e79bf5f41cd9580ac8",
    "tools/hu_b703_rank29_routes.cjs": "8ac70c349c5f60d35578e9f85fda0d2ec08d5384",
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
    "tools/lines_pipeline/run10_common.py": "9422f8fdff8dfeca245bae48ded7fc38353332f0",
    "tools/hu_b659_rank29_monotone.py": "167c1a6de9c98882d8487e493368585b92adc833",
    "tools/hu_b582_rank29_reach.py": "191862b9aa1f869b78e40e621f6325f15be61c9e",
    "tools/hu_b582_rank29_route.cjs": "96eaa79cef526cbc68db6d4b1c9b2698c2cf972e",
    "tools/hu_b637_rank57.py": "86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9",
    "tools/hu_b481_rank27_limp_rivers.py": "1df87de10baee731af50c89c6297bf67e3543098"
}
CODE_PAIRS = (
    {
        'nl2_hu_model.js': 'a98cb80d7762b464064874de39dcff6f4bf5707d',
        'nl2.js': '15aee97e53a156fe073c96a120638a8a3679958f',
        'tools/hu_trainer_route_contract.cjs': '31370c779d22b7d895e76f1030504909019dbe5a',
    },
    {
        'nl2_hu_model.js': 'b4a308a0f65b707f43f41f0b354cec87c08d5af6',
        'nl2.js': '15aee97e53a156fe073c96a120638a8a3679958f',
        'tools/hu_trainer_route_contract.cjs': '3b10524228c357552bb3f1eac88e17f9b2459b32',
    },
)
ORIGINAL_FILES = {'proof.json', 'rendered-routes.json', 'original-manifest.json', 'flop/job.json', 'flop/result.json'}


def git_blob(path):
    return subprocess.check_output(['git', 'hash-object', str(path)], text=True).strip()


def record_hash(record):
    return sha(json.dumps(record, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


def frozen_workspace(destination):
    subprocess.run(['git', 'cat-file', '-e', SOURCE_HEAD + '^{commit}'], check=True, capture_output=True)
    paths = ['tools'] + sorted(path for path in SOURCE_BLOBS if not path.startswith('tools/'))
    raw = subprocess.check_output(['git', 'archive', '--format=tar', SOURCE_HEAD, '--', *paths])
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        names = set()
        for member in archive.getmembers():
            path = Path(member.name)
            assert not path.is_absolute() and '..' not in path.parts and member.name not in names
            names.add(member.name)
            target = destination / path
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            assert member.isfile(), ('Unexpected source tree link', member.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
    for path, digest in SOURCE_BLOBS.items():
        assert git_blob(destination / path) == digest, ('Frozen source content differs', path)


def independent_root(root, route):
    lead, = [node for node in root['nodes'] if node['line'] == '']
    call, = [node for node in root['nodes'] if node['line'] == 'b50']
    assert (root['pot'], root['stack'], lead['player'], call['player'], lead['pot'], call['pot']) == (
        250, 9900, 0, 1, 250, 375)
    assert 0 <= root['info']['gto_expl_pct'] <= .5 and not root['info'].get('lock_stats')
    assert lead['acts'] == ['x', 'b50']
    hands = root['hands'][0]
    count, choice = len(hands), lead['acts'].index('b50')
    selected, values, ui = set(), [], set()
    for index, hand in enumerate(hands):
        weight = lead['w'][0][index]
        if weight <= 1e-4:
            continue
        raw = [max(0., float(lead['strat'][offset * count + index])) for offset in range(len(lead['acts']))]
        total = sum(raw)
        if total <= 0:
            continue
        probabilities = [value / total for value in raw]
        best = max(range(len(probabilities)), key=probabilities.__getitem__)
        if choice == best or (probabilities[choice] >= .4 - 1e-7 and probabilities[choice] >= .7 * probabilities[best] - 1e-7):
            selected.add(cardkey(hand))
        values.append((probabilities[choice], weight))
        if rendered(hand, lead['board'], 'flop', route):
            ui.add(cardkey(hand))
    assert selected == accepted(lead, root['hands'], 'b50')
    assert not selected and values and ui, 'This closeout is restricted to the actual zero-accepted-b50 workers'
    return dict(native_root_action_order=lead['acts'], native_weighted_hero_hands=len(values),
        ui_flop_hands_before_native_gate=len(ui), independently_accepted_b50_hands=0,
        independent_gate_matches=True, b50_max_frequency=max(value for value, _ in values),
        b50_weighted_frequency=sum(value * weight for value, weight in values) / sum(weight for _, weight in values),
        ip_call_accepted=len(accepted(call, root['hands'], 'c')), negative_cause='GTO_ROOT_B50_ACCEPTED_HANDS_ZERO',
        reach_threshold='MAX_FREQUENCY_OR_GE40PCT_AND_GE70PCT_OF_MAX_UNCHANGED')


def publish(args):
    for path, digest in VALIDATION_PINS.items():
        assert git_blob(path) == digest, ('Changed replay implementation', path)
    code = {path: git_blob(path) for path in CODE_PAIRS[0]}
    assert code in CODE_PAIRS, 'Require exactly one known complete four-price or six-price code pair'
    registry_path = Path('data/nl2_hu_multiboard_status_current.json')
    registry_raw = registry_path.read_bytes()
    registry = json.loads(registry_raw)
    model = registry['records'][MODEL]
    assert (model['frequency_rank'], model['solver_profile'], model['family'], model['street'], model['label']) == (
        29, 'LMP_CO_BB', 'LMP', 2, 'APPROX')
    assert model['assumed_model_node_spr'] == 7.52 and not model['certified_3_to_5_exact_flop_boards']
    protected = {mid: record_hash(record) for mid, record in registry['records'].items() if record['label'] == 'CERT-MULTIBOARD'}
    assert len(protected) >= 150
    all_records = {mid: record_hash(record) for mid, record in registry['records'].items()}
    current_route = json.loads(subprocess.check_output(['node', 'tools/hu_b703_rank29_routes.cjs']))
    current_contract = json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    receipts = args.receipts.resolve()
    run = json.loads((receipts / 'source-run.json').read_bytes())
    files = json.loads((receipts / 'source-files.json').read_bytes())
    check_source(run, files)
    inputs = json.loads((receipts / 'workers.json').read_bytes())
    assert len(inputs) == 3 and {pin['flop'] for pin in inputs} == set(FLOPS)
    assert len({pin['id'] for pin in inputs}) == len({pin['job_id'] for pin in inputs}) == 3
    data = (args.output / 'data').resolve()
    central = Path('data').resolve()
    assert data != central and central not in data.parents and not data.exists(), 'Use a fresh isolated output'
    evidence = data / 'solver_evidence'
    target_receipts, target_proofs = evidence / 'b706_receipts', evidence / 'b706_proofs'
    target_receipts.mkdir(parents=True)
    target_proofs.mkdir()
    for name in ('source-run.json', 'source-files.json', 'workers.json'):
        (target_receipts / name).write_bytes((receipts / name).read_bytes())
    reports = []
    with tempfile.TemporaryDirectory(prefix='b706-source-replay-') as tmp:
        frozen = Path(tmp) / 'source'
        frozen.mkdir()
        frozen_workspace(frozen)
        source_contract = json.loads((frozen / 'data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
        assert current_contract == source_contract, 'Current rank29 contract changed'
        for pin in sorted(inputs, key=lambda value: FLOPS.index(value['flop'])):
            assert (pin['run'], pin['head'], pin['run_attempt']) == (SOURCE_RUN, SOURCE_HEAD, run['run_attempt'])
            receipt_path, job_path = receipts / f'{pin["id"]}.json', receipts / f'job-{pin["job_id"]}.json'
            receipt, job = json.loads(receipt_path.read_bytes()), json.loads(job_path.read_bytes())
            assert (receipt['id'], job['id'], receipt['name'], job['name']) == (
                pin['id'], pin['job_id'], pin['name'], pin['job_name'])
            check_worker(job, receipt, pin['flop'], run['run_attempt'])
            raw = (receipts / f'{pin["id"]}.zip').read_bytes()
            assert sha(raw) == pin['sha256'] and receipt['digest'] == 'sha256:' + pin['sha256']
            output = Path(tmp) / pin['flop']
            output.mkdir()
            with ZipFile(io.BytesIO(raw)) as archive:
                assert len(archive.namelist()) == len(set(archive.namelist()))
                assert set(archive.namelist()) == ORIGINAL_FILES, 'Negative workers must have no downstream native files'
                assert sum(info.file_size for info in archive.infolist()) < 64 * 1024 * 1024
                for name in ORIGINAL_FILES:
                    target = output / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(name))
            original_proof = (output / 'proof.json').read_bytes()
            claim = json.loads(original_proof)
            assert (claim['schema'], claim['rank'], claim['model_id'], claim['flop'], claim['line'], claim['actor']) == (
                'NL2_B703_R29_ORIGINAL_WORKER_V1', 29, MODEL, pin['flop'], LINE, 0)
            assert claim['source_app_blobs'] == {path: CODE_PAIRS[0][path] for path in ('nl2_hu_model.js', 'nl2.js')}
            assert claim['source_worker_blob'] == SOURCE_BLOBS['tools/hu_b703_rank29_highcards.py']
            assert claim['source_route_blob'] == SOURCE_BLOBS['tools/hu_b703_rank29_routes.cjs']
            assert set(claim['native_file_sha256']) == ORIGINAL_FILES - {'proof.json'}
            assert all(sha((output / name).read_bytes()) == digest for name, digest in claim['native_file_sha256'].items())
            assert current_route == json.loads((output / 'rendered-routes.json').read_bytes())
            result = subprocess.run([sys.executable, str(frozen / 'tools/hu_b703_rank29_highcards.py'),
                '--solver', str(args.solver.resolve()), '--flop', pin['flop'], '--output', str(output)],
                cwd=frozen, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), capture_output=True, text=True)
            assert result.returncode == 0, (pin['flop'], result.stdout[-1500:], result.stderr[-2000:])
            assert (output / 'proof.json').read_bytes() == original_proof, 'Original source replay must be byte identical'
            for field in ('positive_distinct_flops', 'gto_turn_subgames', 'actor_locked_turn_subgames',
                    'gto_half_pot_river_nodes', 'nl2_half_pot_river_nodes'):
                assert claim[field] == 0
            assert [turn['turn'] for turn in claim['turns']] == CASES[pin['flop']]
            for turn in claim['turns']:
                assert not turn['gto_solved'] and not turn['actor_locked'] and not turn['checks']
                assert turn['negative_stage'] == 'ROOT_TWO_SEAT_UI_INTERSECTION_ZERO'
                gate = turn['root_gate']
                assert all(gate[key] == 0 for key in ('oop_b50_accepted', 'strict_two_seat_hero_combos',
                    'compatible_hole_card_pairs', 'flop_ui_after_ancestry', 'turn_ui_after_ancestry', 'legal_river_count'))
                assert not gate['legal_river_hands'] and gate['ip_call_accepted'] > 0
            root = json.loads((output / 'flop/result.json').read_bytes())
            diagnostic = independent_root(root, current_route)
            archive_name = 'NL2_B706_R29_' + pin['flop'].upper() + '.zip'
            (evidence / archive_name).write_bytes(raw)
            (target_proofs / (pin['flop'] + '.json')).write_bytes(original_proof)
            for path in (receipt_path, job_path):
                (target_receipts / path.name).write_bytes(path.read_bytes())
            reports.append(dict(flop=pin['flop'], source_run=SOURCE_RUN, source_head=SOURCE_HEAD,
                artifact_id=pin['id'], archive_sha256=pin['sha256'], original_job_id=pin['job_id'],
                archive_path='data/solver_evidence/' + archive_name,
                proof_path='data/solver_evidence/b706_proofs/' + pin['flop'] + '.json',
                original_proof_sha256=sha(original_proof), root_sha256=claim['root_sha256'],
                root_job_sha256=claim['root_job_sha256'], root_gap_pct=claim['root_gap_pct'],
                source_commit_workspace_replayed=True, byte_identical_original_proof=True,
                current_rank29_route_rechecked=True, native_solve_repeated=False,
                original_source_app_blobs=claim['source_app_blobs'], static_range_witness=claim['static_range_witness'],
                independent_root_diagnostic=diagnostic, turns=claim['turns']))
    guard = dict(schema='NL2_HU_B706_UNCHANGED_REGISTRY_GUARD_V1', registry_sha256=sha(registry_raw),
        target_model_id=MODEL, target_label_before='APPROX', all_record_sha256=all_records,
        protected_cert_record_sha256=protected, current_exact_code_pair=code)
    report = dict(schema='NL2_HU_B706_AUTHENTICATED_RANK29_NEGATIVES_V1', rank=29, model_id=MODEL,
        source_run=SOURCE_RUN, source_head=SOURCE_HEAD, source_exact_blob_pins=SOURCE_BLOBS,
        current_exact_code_pair=code, negative_flops=3, valid_distinct_flops=0, checked_root_turns=12,
        gto_turn_subgames=0, actor_locked_boards=0, half_pot_assessed_boards=0, nonpolarized_candidates=0,
        root_negative_cause='GTO_ROOT_B50_ACCEPTED_HANDS_ZERO', registry_changed=False, label_changed=False,
        native_solves_repeated=0, protected_cert_records=len(protected), records=reports)
    (data / 'nl2_hu_b706_rank29_negatives.json').write_bytes(json_bytes(report))
    (data / 'nl2_hu_b706_registry_guard.json').write_bytes(json_bytes(guard))
    assert registry_path.read_bytes() == registry_raw
    assert {path: git_blob(path) for path in CODE_PAIRS[0]} == code
    print(json.dumps({key: value for key, value in report.items() if key not in (
        'records', 'source_exact_blob_pins', 'current_exact_code_pair')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('solver', 'receipts', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    publish(parser.parse_args())
