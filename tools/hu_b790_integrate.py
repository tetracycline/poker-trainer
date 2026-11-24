"""Publish only rank 229 after independent original-flop witnesses and protect all other records."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile
import subprocess
import sys

from hu_b467_river_source_gate import json_bytes, sha
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b676_checked_rivers import LINE, MODELS, public_cards
from hu_b719_integrate import CENTRAL
from hu_b788_rank229_two_suited import CASES

MODEL = MODELS[229]
RUN = 45350106474
HEAD = 'd95c5bc9650de53edf4b169df23a490989f703bd'
EVIDENCE = Path('solver_evidence')
GROUP = EVIDENCE / 'reverified/rank229.json'
MEDIUM = Path('nl2_hu_b790_locked_medium.json')
MANIFEST = Path('nl2_hu_b790_source_manifest.json')
SUMMARY = Path('nl2_hu_b790_results.json')
REPORT = Path('nl2_hu_b790_integration.json')


def read(path):
    return json.loads(path.read_bytes())


def archives(stage, receipt):
    assert (receipt['run']['id'], receipt['run']['head_sha'], receipt['run']['conclusion']) == (RUN, HEAD, 'success')
    jobs = {row['name']: row for row in receipt['jobs']}
    assert len(jobs) == len(receipt['jobs']) == 3
    rows = {row['name']: row for row in receipt['artifacts']}
    assert len(rows) == len(receipt['artifacts']) == 6
    paths = set()
    for flop in CASES:
        job = jobs['solve (' + flop + ')']
        assert (job['run_id'], job['head_sha'], job['status'], job['conclusion']) == (RUN, HEAD, 'completed', 'success')
        for role, prefix in (('root-', 'ROOT_'), ('', '')):
            artifact = rows['B788-' + role + 'R229-' + flop]
            path = EVIDENCE / ('NL2_B788_' + prefix + 'R229_' + flop.upper() + '.zip')
            assert artifact['workflow_run']['id'] == RUN and artifact['workflow_run']['head_sha'] == HEAD
            assert artifact['digest'] == 'sha256:' + sha((stage / path).read_bytes())
            paths.add(path)
        worker_path = stage / EVIDENCE / ('NL2_B788_R229_' + flop.upper() + '.zip')
        checkpoint_path = stage / EVIDENCE / ('NL2_B788_ROOT_R229_' + flop.upper() + '.zip')
        with ZipFile(worker_path) as worker, ZipFile(checkpoint_path) as checkpoint:
            assert set(checkpoint.namelist()) == {'selection.json', 'checkpoint.json', 'flop/job.json', 'flop/result.json'}
            for key in ('flop/job.json', 'flop/result.json'):
                assert checkpoint.read(key) == worker.read(key)
            proof = json.loads(worker.read('proof.json'))
            assert json.loads(checkpoint.read('selection.json')) == proof['selection']
            assert json.loads(checkpoint.read('checkpoint.json')) == proof['original_flop_source']
            assert proof['checkpoint_source_identity'] == sha(checkpoint.read('selection.json'))
    return paths, rows, jobs


def verify_group(stage, dest, summary, artifacts, jobs):
    previous = read(dest / EVIDENCE / 'partial/b781_rank229.json')
    previous_medium = read(dest / EVIDENCE / 'partial/b781_rank229_locked_medium.json')
    group = read(stage / GROUP)
    medium = read(stage / MEDIUM)
    assert (group['rank'], group['model_id']) == (229, MODEL)
    assert [b['flop'] for b in previous['boards']] == ['Kc9d4h', 'Kd9c5h']
    assert group['boards'][:2] == previous['boards'] and group['pins'][:2] == previous['pins']
    selected = summary['selected_by_flop']
    n = summary['positive_distinct_flops']
    assert set(selected) <= set(CASES) and n == len(selected) + 2
    assert n == len(group['boards']) == len(group['pins']) and 3 <= n <= 5
    assert n == len({suit_isomorphism_class(b['flop']) for b in group['boards']})
    assert {b['flop'] for b in group['boards'][2:]} == set(selected)
    public_boards = {b['public_board'] for b in group['boards']}
    for mode in ('references', 'gto_references'):
        assert all(medium[mode].get(k) == v for k, v in previous_medium[mode].items())
        assert len(medium[mode]) == n and {r['public_board'] for r in medium[mode].values()} == public_boards
    viewers = set()
    for board, pin in zip(group['boards'], group['pins'], strict=True):
        flop = board['flop']
        public = board['public_board']
        assert all(board[k] == pin[k] for k in ('flop', 'turn', 'river', 'public_board', 'actual_spr'))
        assert len(public_cards(public)) == 5 and public_cards(public[:6]) == public_cards(flop)
        assert public[6:] == board['turn'] + board['river']
        assert (board['actual_exact_action_line'], board['acting_seat'], board['actual_pot_bb'], board['actual_effective_stack_bb']) == (LINE, 0, 21, 90)
        assert 0 <= board['relative_spr_error_pct'] <= 5 and board['nl2_locked_variants'][0]['version'] == 'exp_oop'
        assert pin['pool_observed_marginal_lock_nodes'] > 0 and pin['rendered_decision_hands']
        for policy in ('GTO', 'NL2'):
            assert pin[policy + '_compatible_hole_card_pairs'] >= pin[policy + '_strict_combos'] > 0
        for witness in pin['rendered_decision_hands']:
            assert witness['displayed_suggestion'] == '過'
            assert all('x' in witness[policy]['accepted_actions'] for policy in ('gto', 'nl2'))
        if flop not in selected:
            continue
        outcome = selected[flop]
        assert (outcome['public_board'], outcome['turn']) == (public, board['turn'])
        hero = outcome['sb']
        foes = outcome['btn_hands']
        blocked = public_cards(public + hero)
        assert len(blocked) == 7 and foes and len(foes) == len(set(foes))
        assert all(len(public_cards(foe)) == 2 and blocked.isdisjoint(public_cards(foe)) for foe in foes)
        assert {w['hand'] for w in pin['rendered_decision_hands']} == {hero}
        assert all(w['compatible_btn_hand'] in foes and w['same_policy_opponents'] == len(foes) for w in pin['rendered_decision_hands'])
        worker = artifacts['B788-R229-' + flop]
        checkpoint = artifacts['B788-root-R229-' + flop]
        assert (pin['worker_head'], pin['worker_artifact'], pin['original_job_id']) == (HEAD, worker['id'], jobs['solve (' + flop + ')']['id'])
        assert (pin['checkpoint_artifact_id'], pin['checkpoint_sha256']) == (checkpoint['id'], checkpoint['digest'][7:])
        assert pin['archive_sha256'] == worker['digest'][7:]
        assert pin['archive_code'] == 'B788_R229_' + flop.upper() and pin['viewer_archive_code'] == 'B790_R229_' + flop.upper()
        view = EVIDENCE / ('NL2_MULTIBOARD_' + pin['viewer_archive_code'] + '.json.gz')
        assert sha((stage / view).read_bytes()) == pin['viewer_sha256']
        viewers.add(view)
    return public_boards, viewers


def integrate(args):
    stage = args.stage.resolve()
    dest = Path('data').resolve()
    assert stage.is_dir() and not stage.is_relative_to(dest)
    registry = Path(CENTRAL[0])
    before = read(registry)
    records = before['records']
    assert before['TOTAL'] == len(records) == 392
    assert (records[MODEL]['frequency_rank'], records[MODEL]['label'], records[MODEL]['solver_profile']) == (229, 'APPROX', 'SB3_BTN')
    summary = read(stage / SUMMARY)
    assert (summary['source_run'], summary['source_head'], summary['model_id'], summary['rank']) == (RUN, HEAD, MODEL, 229)
    assert summary['cert_eligible_ranks'] == [229]
    assert (summary['positive_distinct_flops'], summary['new_positive_flops'], summary['new_original_flops']) == (4, 2, 3)
    assert (summary['locked_public_boards'], summary['joint_halfpot_assessed'], summary['halfpot_candidates']) == (45, 45, 0)
    assert {flop: (w['turn'], w['public_board'][-2:], w['sb'], len(w['btn_hands']))
            for flop, w in summary['selected_by_flop'].items()} == {
                'Kd9h4h': ('8d', '2c', '6d9d', 75), 'Kd9d5h': ('7h', '2d', '6h9h', 66)
            }
    manifest = read(stage / MANIFEST)
    assert manifest == read(dest / MANIFEST)
    raw_paths, artifacts, jobs = archives(stage, manifest)
    public_boards, viewers = verify_group(stage, dest, summary, artifacts, jobs)
    expected = {GROUP, MEDIUM, MANIFEST, SUMMARY} | raw_paths | viewers
    actual = {p.relative_to(stage) for p in stage.rglob('*') if p.is_file()}
    assert actual == expected, actual ^ expected
    for path in sorted(expected):
        src, target = stage / path, dest / path
        assert not src.is_symlink() and src.resolve().is_relative_to(stage)
        assert not target.is_symlink() and target.resolve().is_relative_to(dest)
        data = src.read_bytes()
        assert not target.exists() or target.read_bytes() == data
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    subprocess.run([sys.executable, 'tools/hu_apply_cert_extensions.py', '--out', str(registry)], check=True)
    after = read(registry)
    assert records.keys() == after['records'].keys()
    assert all(value == after['records'][key] for key, value in records.items() if key != MODEL)
    assert (after['CERT_MULTIBOARD'], after['APPROX'], after['TOTAL']) == (before['CERT_MULTIBOARD'] + 1, before['APPROX'] - 1, 392)
    new = after['records'][MODEL]
    assert new['label'] == 'CERT-MULTIBOARD' and new['proven_exact_board_count'] == len(public_boards)
    assert {b['public_board'] for b in new['certified_3_to_5_exact_flop_boards']} == public_boards
    report = dict(rank=229, model_id=MODEL, source_run=RUN, source_head=HEAD, positive_distinct_flops=len(public_boards),
                  protected_other_records=391, protected_prior_certificates=before['CERT_MULTIBOARD'],
                  CERT_MULTIBOARD=after['CERT_MULTIBOARD'], APPROX=after['APPROX'])
    for key in ('locked_public_boards', 'joint_halfpot_assessed', 'halfpot_candidates'):
        report[key] = summary[key]
    assert report['locked_public_boards'] >= report['joint_halfpot_assessed'] >= report['halfpot_candidates'] >= 0
    (dest / REPORT).write_bytes(json_bytes(report))
    paths = {str(Path('data') / path) for path in expected | {REPORT}} | set(CENTRAL)
    args.paths.write_text('\n'.join(sorted(paths)) + '\n')
    args.group.write_text(str(Path('data') / GROUP) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('stage', 'paths', 'group'):
        parser.add_argument('--' + key, type=Path, required=True)
    integrate(parser.parse_args())
