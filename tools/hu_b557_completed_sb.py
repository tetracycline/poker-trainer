"""Authenticate eight completed SB flop archives and replay their named river decisions."""
import argparse
import base64
import gzip
import json
import math
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b527_checked_barrels import board_row, classes, COLUMNS
from hu_b545_sb_half_pot import CASES
from hu_sequential_cfr_reach import cardkey

PINS = Path('data/nl2_hu_b557_completed_archives.json')
LOCAL = Path('data/nl2_hu_b545_local_originals.json')
SOURCE_REPORT = Path('data/nl2_hu_b545_sb_half_pot.json')
ACTION_REPORT = Path('data/nl2_hu_b557_sb_river_actions.json')


def authenticate(pins, receipts):
    """The first five originals shipped with the run's checkout; the other three were uploaded by its workers."""
    seen = set()
    for row in json.loads(LOCAL.read_bytes())['originals']:
        path = EVIDENCE / ('NL2_' + row['archive_code'] + '.zip')
        assert sha(path.read_bytes()) == row['archive_sha256']
        seen.add(row['flop'])
    for row in pins['artifacts']:
        assert row['flop'] not in seen and row['name'] == 'B545-native-' + row['flop']
        seen.add(row['flop'])
        payload = (EVIDENCE / row['source_file']).read_bytes()
        assert row['source_file'] == 'NL2_B545_R18_' + row['flop'].upper() + '.zip'
        assert sha(payload) == row['source_sha256']
        if receipts:
            metadata = json.loads((receipts / f"{row['id']}.json").read_bytes())
            received = receipts / f"{row['id']}.zip"
            assert metadata['id'] == row['id'] and metadata['name'] == row['name']
            assert metadata['digest'] == 'sha256:' + row['artifact_sha256'] == 'sha256:' + sha(received.read_bytes())
            run = metadata['workflow_run']
            assert (run['id'], run['head_sha'], run['repository_id']) == (pins['workflow_run'], pins['head'], pins['repository_id'])
            with ZipFile(received) as archive:
                assert archive.namelist() == [row['source_file']] and archive.read(row['source_file']) == payload
    assert seen == set(CASES)


def hand_actions(pin, current):
    """Compare the two native action masks for every holding that reached the named node in both policies."""
    raw = (EVIDENCE / ('NL2_MULTIBOARD_' + pin['viewer_archive_code'] + '.json.gz')).read_bytes()
    assert sha(raw) == pin['viewer_sha256']
    bundle = json.loads(gzip.decompress(raw))
    assert bundle['original_archive_sha256'] == pin['locked_original_archive_sha256']
    target = set(pin['shared_rendered_route_hands'])
    by_hand = {h: {} for h in sorted(target)}
    for case in bundle['artifacts'][0]['cases']:
        node, = case['nodes']
        public = node['public_board']
        assert public == pin['public_board'] and node['acting_seat'] == 0
        assert node['exact_node_line'] == f"b50 c/b{CASES[pin['flop']][0]} c/"
        assert case['source_sha256'] == pin[{'gto':'original_GTO_SHA256', 'exp_oop':'actual_NL2_SHA256'}[case['version']]]
        actions = node['source_actions']
        masks = base64.b64decode(node['strictly_reachable_masks_b64'], validate=True)
        for hole, mask in zip(case['hands_by_seat'][0], masks, strict=True):
            hand = ''.join(cardkey(hole))
            if hand in target:
                assert 0 < mask < (1 << len(actions))
                by_hand[hand][case['version']] = [a for i, a in enumerate(actions) if mask & (1 << i)]
    counts = dict(both=0, gto_only=0, nl2_only=0, neither=0)
    for hand, policies in by_hand.items():
        assert set(policies) == {'gto', 'exp_oop'}
        group, = classes(hand, public)
        action = current[f'{board_row(public)}:{COLUMNS.index(group)}']
        indicators = (action in policies['gto'], action in policies['exp_oop'])
        counts[{(True, True):'both', (True, False):'gto_only', (False, True):'nl2_only', (False, False):'neither'}[indicators]] += 1
        policies['generic_action'] = action
    return dict(public_board=public, shared_reached_hands=len(target), generic_action_counts=counts,
                native_actions_by_reached_hand=by_hand)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--solver', type=Path, required=True)
    ap.add_argument('--receipts', type=Path)
    args = ap.parse_args()
    pins = json.loads(PINS.read_bytes())
    authenticate(pins, args.receipts)
    # B545's five checkout archives were serialized using CPython 3.12's compensated float sum.
    # With 3.11 the four measured bins round to 98.30000000000001 and produce different native job bytes.
    pool = json.loads((args.solver/'inputs/pool_stats.json').read_bytes())['NL2']['postflop_HU']['SRP_PFR_OOP']['cbet_size']
    weights = [pool[key] for key in ('≤33%', '34-55%', '56-80%', '81-110%')]
    assert sum(weights) == math.fsum(weights) == 98.3, 'Replay B545 with CPython 3.12'
    subprocess.run([sys.executable, 'tools/hu_b545_sb_half_pot.py', '--solver', str(args.solver), '--inputs', str(EVIDENCE),
                    '--run', str(pins['workflow_run']), '--pins', str(LOCAL), '--out', str(SOURCE_REPORT)], check=True)
    # The standalone B545 report predates the standard registry envelope. Preserve its exact source rows.
    medium_path = Path('data/nl2_hu_b545_locked_medium.json')
    medium = json.loads(medium_path.read_bytes())
    assert medium['schema'] == 'NL2_HU_B545_EXACT_SB_LOCKED_MEDIUM_V1'
    medium['schema'] = 'NL2_HU_B545_ORIGINAL_LOCKED_MEDIUM_V1'
    medium_path.write_bytes(json_bytes(medium))
    decisions = json.loads(subprocess.check_output(['node', 'tools/hu_b557_sb_river_actions.cjs']))
    original = json.loads(SOURCE_REPORT.read_bytes())
    assert original.pop('verified_import_run') == pins['workflow_run']
    original.update(source_worker_run=pins['workflow_run'], original_verifier_conclusion='FAILURE',
                    verification='B557_REPLAY_OF_PINNED_BYTES',
                    source_origins={'checkout':LOCAL.as_posix(), 'worker_artifacts':PINS.as_posix()})
    SOURCE_REPORT.write_bytes(json_bytes(original))
    assert len(original['attempts']) == len(CASES) and all(a['status'] != 'MISSING_ARCHIVE' for a in original['attempts'])
    evaluated = {}
    for rank, result in original['verified_pairs'].items():
        rows = [hand_actions(pin, decisions[rank]) for pin in result['pins']]
        evaluated[rank] = dict(verified_distinct_flops=len({b['flop'] for b in result['boards']}), named_river_nodes=rows)
    ACTION_REPORT.write_bytes(json_bytes(dict(schema='NL2_HU_B557_COMPLETED_SB_NODE_ACTIONS_V1', source_run=pins['workflow_run'],
        source_head=pins['head'], source_attempts=SOURCE_REPORT.as_posix(), original_archive_pins=PINS.as_posix(),
        local_source_pins=LOCAL.as_posix(), scope='NAMED_DECISION_REACH', generic_actions='APPROX', ranks=evaluated)))


if __name__ == '__main__':
    main()
