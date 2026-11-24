"""Replay B709 originals and B702's original two positives before staging rank89.

No native CFR is run here. The old B705/B696 evidence is rebuilt by its pinned
B702 publisher. B709 is replayed in its immutable source tree, then its jobs,
two-seat reach, displayed decisions and measured actor locks are independently
checked at the current exact 11bb/94.75bb river price. Registry writes belong to
the separate publication job.
"""
import argparse
import contextlib
from copy import deepcopy
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from zipfile import ZipFile

import hu_b696_turn_call_rivers as native
import hu_b702_publish as prior
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b710_collect import FLOPS, SOURCE_RUN, SOURCE_HEAD, SOURCE_BLOBS, check_source, check_worker
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_trainer_route_gate import compatible

RANK = 89
MODEL = 'ln-ipfr-r_model-bqgbuq'
LINE = 'x x/b50 c/x'
CASES = {'Td8c3h': ['Ts', '8h', '3s'], 'Jh7d4c': ['Js', '7s', '4h'], 'Qc9s5d': ['Qh', '9d', '5h']}
SCHEMA = 'NL2_HU_B710_ORIGINAL_LOCKED_MEDIUM_V1'
PRIOR_TOOLS = {
    'tools/hu_b702_publish.py': '6e0e8d10219bfbe18e6b33fe2757359125f5d39b',
    'tools/hu_b702_resume_collect.py': '279504f51a77088a7a953c9a4770618e96ce5b18',
}
CURRENT_PRICE_CODE = {
    'nl2_hu_model.js': 'b4a308a0f65b707f43f41f0b354cec87c08d5af6',
    'nl2.js': '15aee97e53a156fe073c96a120638a8a3679958f',
    'tools/hu_trainer_route_contract.cjs': '3b10524228c357552bb3f1eac88e17f9b2459b32',
}


def git_blob(path):
    return subprocess.check_output(['git', 'hash-object', str(path)], text=True).strip()


def record_hash(record):
    return sha(json.dumps(record, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


def frozen_workspace(destination):
    """Materialize only the fixed source commit; never change the working branch."""
    paths = ['tools'] + sorted(p for p in SOURCE_BLOBS if not p.startswith('tools/'))
    raw = subprocess.check_output(['git', 'archive', '--format=tar', SOURCE_HEAD, '--', *paths])
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        names = set()
        for member in archive.getmembers():
            name = PurePosixPath(member.name)
            assert not name.is_absolute() and '..' not in name.parts and member.name not in names
            names.add(member.name)
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                assert member.isfile(), ('Unexpected source tree link', member.name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    for path, digest in SOURCE_BLOBS.items():
        assert git_blob(destination / path) == digest, ('Frozen source content differs', path)


def unpack_original(raw, folder):
    with ZipFile(io.BytesIO(raw)) as archive:
        names = [name for name in archive.namelist() if not name.endswith('/')]
        assert len(names) == len(set(names)) and sum(i.file_size for i in archive.infolist()) < 512 * 1024 * 1024
        for name in names:
            path = PurePosixPath(name)
            assert not path.is_absolute() and '..' not in path.parts
            target = folder / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    return set(names)


def required_files(report):
    result = {'proof.json', 'rendered-routes.json', 'flop/job.json', 'flop/result.json'}
    for turn in report['turns']:
        if turn['parent_gate']['river_extracts']:
            result |= {turn['turn'] + '-gto/' + name for name in ('job.json', 'result.json')}
        if turn['paired_policies']:
            result |= {turn['turn'] + '-exp_ip/' + name for name in ('job.json', 'result.json')}
    return result


def add_selected(group, medium, model, contract, c, pin, expected, origin, selected):
    gto, locked, public, comparisons, grow, erow = selected
    assert comparisons and compatible(contract['routes'][MODEL], dict(
        public_board=public, actual_exact_action_line=LINE, acting_seat=1))
    board, pinout = pairs.emit_board(model, gto, locked, public, LINE, texture(pin['flop']),
        viewer_code='B710_R89_' + pin['flop'].upper())
    assert board and pinout['GTO_compatible_hole_card_pairs'] >= pinout['GTO_strict_combos'] > 0
    assert pinout['NL2_compatible_hole_card_pairs'] >= pinout['NL2_strict_combos'] > 0
    assert pinout['common_legal_hero_combos'] >= len(comparisons) > 0
    board.update(source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR', origin_solve_run_id=SOURCE_RUN,
        restricted_flop_bet_sizes_pct=[33, 50, 75], flop_bet_size_menu=native.ROOT_MENU,
        certification_scope=expected['lock_scope'], original_root_run_id=SOURCE_RUN,
        original_root_result_sha256=origin['original_root_result_sha256'], source_root_reused=False,
        flop_native_solves_repeated=0)
    pinout.update(rendered_decision_hands=comparisons, source_run_role=board['source_run_role'],
        worker_artifact=pin['id'], worker_sha256=pin['sha256'], source_blob_head=SOURCE_HEAD,
        root_origin=origin, original_root_archive_code=gto['archive_code'],
        original_root_archive_sha256=pin['sha256'],
        exact_root_sizing=dict(pot_bb=5.5, effective_stack_bb=97.5, turn_bet_chips=275,
            river_pot_chips=1100, river_stack_chips=9475))
    board['nl2_locked_variants'][0].update(source_run_role=board['source_run_role'],
        origin_solve_run_id=SOURCE_RUN, pool_sha256=POOL,
        measurement_policy='STREET_SPECIFIC_POOL_MARGINALS', applied_street_rates=rates(locked),
        gto_parent_source_run_id=SOURCE_RUN, gto_parent_source_sha256=gto['root_sha256'],
        turn_gto_source_run_id=SOURCE_RUN, turn_gto_source_sha256=gto['source_sha256'],
        viewer_archive_code=pinout['viewer_archive_code'], viewer_sha256=pinout['viewer_sha256'])
    group['boards'].append(board)
    group['pins'].append(pinout)
    for key, row in (('gto_references', grow), ('references', erow)):
        ref = source_key(MODEL, row)
        assert ref not in medium[key]
        medium[key][ref] = row
    return dict(public_board=public, shared_rendered_hands=len(comparisons),
        gto_strict_combos=grow['strict_legal_combos'], nl2_strict_combos=erow['strict_legal_combos'],
        nonpolarized_candidate=erow['b50']['candidate'])


def publish(args):
    assert sys.version_info[:2] == (3, 11), 'Exact original job replay requires source Python 3.11'
    for path, digest in {**PRIOR_TOOLS, **CURRENT_PRICE_CODE}.items():
        assert git_blob(path) == digest, ('Changed publication code', path)
    for path, digest in SOURCE_BLOBS.items():
        if path.startswith('tools/') or path not in ('nl2_hu_model.js',):
            assert git_blob(path) == digest, ('Changed source validation implementation', path)
    registry_path = Path('data/nl2_hu_multiboard_status_current.json')
    registry_raw = registry_path.read_bytes()
    registry = json.loads(registry_raw)
    records = registry['records']
    assert len(records) == 392
    model = records[MODEL]
    assert (model['frequency_rank'], model['label'], model['solver_profile'], model['family'], model['street'],
        model['assumed_model_node_spr']) == (89, 'APPROX', 'BTN_BB', 'SRP', 2, 8.614)
    assert not model['certified_3_to_5_exact_flop_boards']
    all_records = {mid: record_hash(record) for mid, record in records.items()}
    protected = {mid: all_records[mid] for mid, record in records.items() if record['label'] == 'CERT-MULTIBOARD'}
    assert len(protected) >= 150
    central = Path('data').resolve()
    data = (args.output / 'data').resolve()
    assert data != central and central not in data.parents and not data.exists(), 'Use a fresh isolated stage'
    receipts = args.receipts.resolve()
    run = json.loads((receipts / 'source-run.json').read_bytes())
    files = json.loads((receipts / 'source-files.json').read_bytes())
    check_source(run, files)
    workers = json.loads((receipts / 'workers.json').read_bytes())
    assert len(workers) == 3 and {p['flop'] for p in workers} == set(FLOPS)
    assert len({p['id'] for p in workers}) == len({p['job_id'] for p in workers}) == 3
    solver = args.solver.resolve()
    assert subprocess.check_output(['git', '-C', solver, 'rev-parse', 'HEAD'], text=True).strip() == native.SOLVER
    py = solver / 'postflop/py'
    assert sha((py / 'pipeline.py').read_bytes()) == PIPELINE and sha((py / 'ranges.py').read_bytes()) == RANGES
    sys.path.insert(0, str(py))
    import pipeline
    pool_raw = (solver / 'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)['NL2']
    prior_args = SimpleNamespace(solver=solver, receipts=args.prior_receipts.resolve(), output=args.output.resolve(),
        routes=None, registry=registry_path)
    # This rebuilds the two earlier positives from authenticated B705 and B696
    # raw native ZIPs, including every exact original job and every old negative.
    prior.replay(prior_args)
    evidence = data / 'solver_evidence'
    partial = evidence / 'partial'
    pairs.EVIDENCE = evidence
    group = json.loads((partial / 'b702_rank89.json').read_bytes())
    assert (group['rank'], group['model_id']) == (RANK, MODEL)
    assert {b['flop'] for b in group['boards']} == {'Qs7h3d', 'Jc6d2s'} and len(group['pins']) == 2
    assert all(p['rendered_decision_hands'] for p in group['pins'])
    medium = json.loads((partial / 'b702_rank89_locked_medium.json').read_bytes())
    medium['schema'] = SCHEMA
    assert all(len(medium[key]) == 2 for key in ('references', 'gto_references'))
    prior_data_pins = {str(path.relative_to(data)): sha(path.read_bytes()) for path in sorted(data.rglob('*')) if path.is_file()}
    routes_raw, routes, contract, models, price_manifest = prior.isolated_prices(prior_args)
    current_routes_raw = subprocess.check_output(['node', 'tools/hu_b696_turn_call_routes.cjs'])
    assert current_routes_raw == routes_raw, 'Current and staged exact UI routes must agree'
    current_contract = json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    assert current_contract == contract['routes'][MODEL]
    c = routes[str(RANK)]
    assert (c['id'], c['actor'], c['spot'], c['pot'], c['stack'], c['river_pot'], c['river_stack'], c['line']) == (
        MODEL, 1, 'BTN_BB', 550, 9750, 1100, 9475, LINE)
    all_rows = dict(gto_references={}, references={})
    results = []
    authenticated = []
    native_gto_turns = native_locked_turns = 0
    with TemporaryDirectory(prefix='b710-source-replay-') as td:
        frozen = Path(td) / 'source'
        frozen.mkdir()
        frozen_workspace(frozen)
        for pin in sorted(workers, key=lambda item: FLOPS.index(item['flop'])):
            assert (pin['run'], pin['head'], pin['run_attempt']) == (SOURCE_RUN, SOURCE_HEAD, run['run_attempt'])
            artifact = json.loads((receipts / f'{pin["id"]}.json').read_bytes())
            job = json.loads((receipts / f'job-{pin["job_id"]}.json').read_bytes())
            check_worker(job, artifact, pin['flop'], run['run_attempt'])
            assert (pin['id'], pin['job_id'], pin['name'], pin['job_name']) == (
                artifact['id'], job['id'], artifact['name'], job['name'])
            archive = (receipts / f'{pin["id"]}.zip').read_bytes()
            assert sha(archive) == pin['sha256'] and artifact['digest'] == 'sha256:' + pin['sha256']
            authenticated.append(dict(artifact=artifact, job=job))
            folder = Path(td) / pin['flop']
            folder.mkdir()
            names = unpack_original(archive, folder)
            original_proof = (folder / 'proof.json').read_bytes()
            expected = json.loads(original_proof)
            assert (expected['schema'], expected['rank'], expected['model_id'], expected['flop'], expected['line'], expected['actor']) == (
                'NL2_B709_R89_NEW_TURN_CALL_WORKER_V1', RANK, MODEL, pin['flop'], LINE, 1)
            assert expected['source_worker_blob'] == SOURCE_BLOBS['tools/hu_b709_rank89_extra.py']
            assert all(SOURCE_BLOBS[path] == digest for path, digest in expected['source_algorithm_blobs'].items())
            assert expected['canonical_card_order_fix'] == 'B705_CARD_SET_CHECK_AND_TEMPORARY_NATIVE_ORDER_VIEW'
            assert expected['prior_native_solves_repeated'] == 0
            assert names == required_files(expected)
            assert set(expected['native_file_sha256']) == names - {'proof.json'}
            assert all(sha((folder / name).read_bytes()) == digest for name, digest in expected['native_file_sha256'].items())
            assert (folder / 'rendered-routes.json').read_bytes() == routes_raw
            assert expected['preregistered_new_flops'] == list(CASES)
            assert expected['preregistered_turns'] == CASES[pin['flop']]
            assert [t['turn'] for t in expected['turns']] == CASES[pin['flop']][:len(expected['turns'])]
            result = subprocess.run([sys.executable, str(frozen / 'tools/hu_b709_rank89_extra.py'),
                '--solver', str(solver), '--flop', pin['flop'], '--routes', str(folder / 'rendered-routes.json'),
                '--output', str(folder)], cwd=frozen, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                capture_output=True, text=True)
            assert result.returncode == 0, (pin['flop'], result.stdout[-2000:], result.stderr[-2500:])
            assert (folder / 'proof.json').read_bytes() == original_proof, 'Frozen original proof must replay byte for byte'
            assert all(sha((folder / name).read_bytes()) == digest for name, digest in expected['native_file_sha256'].items())
            code = 'B709_R89_' + pin['flop'].upper()
            archive_path = evidence / ('NL2_' + code + '.zip')
            archive_path.write_bytes(archive)
            proof_path = partial / ('b710_R89_' + pin['flop'].upper() + '_proof.json')
            proof_path.write_bytes(original_proof)
            origin = dict(original_root_run=SOURCE_RUN, original_root_head=SOURCE_HEAD,
                original_root_artifact=pin['id'], original_root_archive_sha256=pin['sha256'],
                original_root_result_sha256=sha((folder / 'flop/result.json').read_bytes()),
                original_root_job_sha256=sha((folder / 'flop/job.json').read_bytes()),
                source_root_reused=False, original_native_flop_solves_repeated=0)
            record = dict(rank=RANK, flop=pin['flop'], source_run_id=SOURCE_RUN, source_blob_head=SOURCE_HEAD,
                worker_artifact=pin['id'], original_job_id=pin['job_id'], archive_code=code,
                archive_sha256=pin['sha256'], proof_path=str(proof_path.relative_to(args.output.resolve())),
                proof_sha256=sha(original_proof), root_origin=origin,
                byte_identical_original_proof=True, native_cfr_rerun=False,
                positive=expected['selected'] is not None, proof=expected)
            selected_data = None
            for turn in expected['turns']:
                if not turn['parent_gate']['river_extracts']:
                    assert not turn['paired_policies'] and not turn['gto_boards'] and not turn['nl2_boards']
                    continue
                native_gto_turns += 1
                native_locked_turns += int(turn['paired_policies'])
                gto, locked = prior.source_turn(folder, pin, turn, c, pipeline, pool, code, origin)
                by_version = []
                for source, prefix, key in ((gto, 'gto', 'gto_references'), (locked, 'nl2', 'references')):
                    if source is None:
                        continue
                    observed = prior.observations(source, c)
                    by_version.append(observed)
                    original = {row['public_board']: row for row in turn[prefix + '_boards']}
                    assert set(observed) == set(original)
                    for public, item in observed.items():
                        assert native.public_cards(public[:6]) == native.public_cards(pin['flop'])
                        assert public[6:8] == turn['turn'] and public[-2:] in turn['parent_gate']['river_extracts']
                        assert item['raw_proof'] == original[public]['reach']
                        assert len(item['hands']) == original[public]['displayed_hands']
                        item['row']['rendered_decision_hands'] = []
                        key_id = source_key(MODEL, item['row'])
                        assert key_id not in all_rows[key]
                        all_rows[key][key_id] = item['row']
                if locked is None:
                    assert not turn['common']
                    continue
                before, after = by_version
                common = {match['public_board']: match for match in turn['common']}
                assert set(before) == set(after)
                actual = {public for public in before if before[public]['hands'].keys() & after[public]['hands'].keys()}
                assert actual == set(common)
                for public, match in common.items():
                    comparisons = prior.common_policies(before[public], after[public], match)
                    for prefix, row in (('gto', before[public]['row']), ('nl2', after[public]['row'])):
                        assert row['b50'] == match[prefix + '_b50'] and row['strict_legal_combos'] > 0
                        row['rendered_decision_hands'] = comparisons
                    if expected['selected'] and (turn['turn'], public) == (
                            expected['selected']['turn'], expected['selected']['public_board']):
                        assert dict(turn=turn['turn'], **match) == expected['selected']
                        selected_data = (gto, locked, public, comparisons, before[public]['row'], after[public]['row'])
            assert bool(selected_data) == record['positive']
            assert expected['positive_distinct_flops'] == int(record['positive'])
            if selected_data:
                record.update(add_selected(group, medium, models[RANK], contract, c, pin, expected, origin, selected_data))
            results.append(record)
    flops = [board['flop'] for board in group['boards']]
    assert len(flops) == len({suit_isomorphism_class(flop) for flop in flops}) == len(group['pins']) <= 5
    assert len(flops) >= 2 and all(pin['rendered_decision_hands'] for pin in group['pins'])
    eligible = len(flops) >= 3
    (partial / 'b710_rank89.json').write_bytes(json_bytes(group))
    (partial / 'b710_rank89_locked_medium.json').write_bytes(json_bytes(medium))
    if eligible:
        destination = evidence / 'reverified'
        destination.mkdir(exist_ok=True)
        (destination / 'rank89.json').write_bytes(json_bytes(group))
        (data / 'nl2_hu_b710_locked_medium.json').write_bytes(json_bytes(medium))
    (partial / 'b710_all_native_node_observations.json').write_bytes(json_bytes(dict(schema=SCHEMA, **all_rows)))
    (partial / 'b710_auth_receipt.json').write_bytes(json_bytes(dict(run=run, source=files,
        workers=authenticated, prior_stage_original_replay_sha256=prior_data_pins, prior_replay_tools=PRIOR_TOOLS)))
    (data / 'nl2_hu_b710_workers.json').write_bytes(json_bytes(workers))
    (data / 'nl2_hu_b710_results.json').write_bytes(json_bytes(results))
    locked = list(all_rows['references'].values())
    joint = [row for row in locked if row['strict_legal_combos'] > 0 and row['compatible_hole_card_pairs'] > 0]
    assessed = [row for row in joint if row['b50'] is not None]
    summary = dict(schema='NL2_HU_B710_RANK89_PUBLICATION_SUMMARY_V1', rank=RANK, model_id=MODEL,
        source_run_id=SOURCE_RUN, source_head=SOURCE_HEAD, source_workers=3, prior_positive_flops=2,
        new_positive_flops=sum(record['positive'] for record in results), negative_new_flops=sum(not record['positive'] for record in results),
        distinct_positive_flops=len(flops), certified_eligible=eligible, selected_exact_boards=flops,
        native_gto_root_jobs=3, native_gto_turn_jobs=native_gto_turns, native_actor_locked_turn_jobs=native_locked_turns,
        native_locked_river_nodes=len(locked), actor_locked_joint_boards=len(joint), half_pot_assessed_joint_boards=len(assessed),
        half_pot_nonpolarized_candidates=sum(row['b50']['candidate'] for row in assessed),
        both_policies_rendered_positive_rivers=sum(bool(row['rendered_decision_hands']) for row in locked),
        selected_combined_actor_locked_boards=len(medium['references']),
        selected_combined_half_pot_assessed_boards=sum(row['b50'] is not None for row in medium['references'].values()),
        native_solves_repeated=0, protected_cert_records=len(protected), live_registry_written=False,
        current_exact_code_pair=CURRENT_PRICE_CODE, original_source_frozen=True)
    (data / 'nl2_hu_b710_summary.json').write_bytes(json_bytes(summary))
    (data / 'nl2_hu_b710_registry_guard.json').write_bytes(json_bytes(dict(
        schema='NL2_HU_B710_UNCHANGED_REGISTRY_GUARD_V1', registry_sha256=sha(registry_raw),
        target_model_id=MODEL, all_record_sha256=all_records, protected_cert_record_sha256=protected,
        current_exact_code_pair=CURRENT_PRICE_CODE)))
    assert all(sha((data / path).read_bytes()) == digest for path, digest in prior_data_pins.items())
    assert registry_path.read_bytes() == registry_raw
    assert {path: git_blob(path) for path in CURRENT_PRICE_CODE} == CURRENT_PRICE_CODE
    print(json.dumps(summary))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('solver', 'receipts', 'prior-receipts', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    publish(parser.parse_args())
