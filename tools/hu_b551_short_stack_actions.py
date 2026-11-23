"""Replay native all-in actions where a nominal half-pot bet exceeds the effective stack."""
import argparse
import base64
from collections import Counter
import hashlib
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from hu_b483_locked_medium import proof
from hu_board_reach_corrections import read_replays, source_key
from hu_sequential_cfr_reach import game_reach

DATA = Path('data')
REPORT = DATA / 'nl2_hu_b551_locked_medium.json'
TARGETS = {87, 129}


def equity_profile(node, mask):
    actor = node['player']
    jam = node['acts'].index('a')
    hands = len(mask)
    assert hands == len(node['w'][actor]) == len(node['eq'])
    assert len(node['ev']) == hands * len(node['acts'])
    live = [(float(node['eq'][i]), float(node['w'][actor][i]), i)
            for i, bits in enumerate(mask) if bits and node['w'][actor][i] > 1e-4]
    assert live and all(0 <= e <= 1.001 for e, _, _ in live)
    live.sort()
    total = sum(w for _, w, _ in live)
    bounds = []
    cumulative = 0.0
    for equity, weight, _ in live:
        cumulative += weight
        while len(bounds) < 2 and cumulative >= total * (len(bounds) + 1) / 3:
            bounds.append(equity)
    assert len(bounds) == 2
    bins = Counter()
    weights = Counter()
    preferred = 0
    for equity, weight, i in live:
        if not mask[i] & (1 << jam):
            continue
        bucket = 'low' if equity < bounds[0] else 'high' if equity > bounds[1] else 'middle'
        bins[bucket] += 1
        weights[bucket] += weight
        ev = [node['ev'][j*hands+i] for j in range(len(node['acts']))]
        preferred += (ev.index(max(ev)) == jam)
    eligible = sum(bins.values())
    mid = weights['middle'] / sum(weights.values()) if eligible else 0.0
    return dict(eligible_combos=eligible, highest_ev_combos=preferred,
                low_equity_combos=bins['low'], middle_equity_combos=bins['middle'], high_equity_combos=bins['high'],
                middle_reach_mass_pct=round(mid*100, 3),
                nonpolarized_research_candidate=eligible >= 20 and bins['middle'] >= 10 and mid >= .20 and
                (bins['low'] >= 5 or bins['high'] >= 5))


def game(archive, path, expected):
    data = archive.read('solver/postflop/' + path)
    assert hashlib.sha256(data).hexdigest() == expected
    return json.loads(data)


def replay(folder, board, row):
    raw = (folder / f"{row['archive_id']}.zip").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['archive_sha256']
    with ZipFile(BytesIO(raw)) as archive:
        manifest, = (n for n in archive.namelist() if n.startswith('evidence/') and n.endswith('.json') and not n.endswith('pool_stats.json'))
        m = json.loads(archive.read(manifest))
        assert (m['spot'], m['version'], m['failures']) == (row['spot'], row['version'], [])
        case, = (c for c in m['cases'] if c.get('source_sha256', c.get('sub_sha256')) == row['source_sha256'])
        root = game(archive, m.get('file_flop') or case['flop_json'], row['root_sha256'])
        sub = game(archive, case.get('source_path') or case['sub_json'], row['source_sha256'])
    public, line, seat = row['public_board'], row['line'], row['acting_seat']
    node, = (n for n in sub['nodes'] if (n['board'], n['line'], n['player']) == (public, line, seat))
    call, = (n for n in sub['nodes'] if (n['board'], n['line'], n['player']) == (public, line+'a', 1-seat))
    pot, chips = node['pot'], sub['stack'] - max(node['bets'])
    assert (pot/100, chips/100) == (board['actual_pot_bb'], board['actual_effective_stack_bb'])
    assert node['acts'] == row['source_actions'] == ['x', 'a'] and 0 < 2*chips < pot
    assert call['pot']-pot == call['bets'][seat]-node['bets'][seat] == chips and 'c' in call['acts']
    observed = proof(root, sub, node, game_reach(root, sub)[0])
    for k in ('status', 'source_hand_order_sha256', 'compatible_action_mask_b64','strict_legal_combos','compatible_hole_card_pairs'):
        assert observed[k] == row[k]
    assert observed['compatible_hole_card_pairs'] > 0
    mask = base64.b64decode(observed['compatible_action_mask_b64'], validate=True)
    result = equity_profile(node, mask)
    assert result['eligible_combos'] == sum(bool(b & 2) for b in mask)
    return dict(archive_id=row['archive_id'], archive_sha256=row['archive_sha256'],
                version=row['version'], action='a', pot_chips=pot, all_in_chips=chips, pot_pct=round(100*chips/pot,3),
                compatible_pairs=observed['compatible_hole_card_pairs'], **result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals', type=Path)
    parser.add_argument('--out', type=Path, default=REPORT)
    parser.add_argument('--list-ids', action='store_true')
    args = parser.parse_args()
    _, locked, gtos, _ = read_replays()
    inventory = json.loads((DATA/'nl2_hu_b485_original_artifacts.json').read_bytes())
    registry = json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())
    jobs = {}
    for model in registry['records'].values():
        if model['frequency_rank'] not in TARGETS or model['label'] != 'CERT-MULTIBOARD':
            continue
        for board in model['certified_3_to_5_exact_flop_boards']:
            if board['actual_effective_stack_bb'] >= board['actual_pot_bb']/2:
                continue
            policies = [('gto',board['source_run_id'],board['source_sha256'])]
            policies += [(v['version'],v['run_id'],v['sha256']) for v in board['nl2_locked_variants']]
            for version, run, sha in policies:
                key = source_key(model['model_id'], dict(public_board=board['public_board'], line=board['actual_exact_action_line'],
                    acting_seat=board['acting_seat'], source_run_id=run, source_sha256=sha))
                row = (gtos if version=='gto' else locked)[key]
                entries = inventory.get(str(run), {}).get('artifacts', [])
                if not any(v['id'] == row.get('archive_id') and v['sha256'] == row.get('archive_sha256') for v in entries):
                    continue
                jobs[key] = (board, row)
    if args.list_ids:
        print('\n'.join(map(str, sorted({r['archive_id'] for _,r in jobs.values()}))))
        return
    assert args.originals and jobs
    report = dict(schema='NL2_HU_B551_ORIGINAL_LOCKED_MEDIUM_V1', gto_references={}, references={})
    for key, (board, row) in jobs.items():
        side = 'gto_references' if row['version'] == 'gto' else 'references'
        report[side][key] = dict(row, short_stack_all_in=replay(args.originals, board, row))
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
