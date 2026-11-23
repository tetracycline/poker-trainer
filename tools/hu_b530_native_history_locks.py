"""Verify previously solved B521 turns against the pinned action-history NL2 sample."""

import argparse
import gzip
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import sha
from hu_b483_locked_medium import POOL
from hu_b504_root_only_locks import REGISTRY, register, solve_or_replay, write
from hu_b521_native_street_locks import PINS, original, targets
from hu_board_reach_corrections import read_replays, source_key
from hu_sequential_cfr_reach import compatible_node_reach, game_reach

RUN = 45112623332
RESULTS = Path('data/nl2_hu_b521_native_street_locks.json')
EVIDENCE = Path('data/solver_evidence')


def history_rates(native, source, pool, rules, masks):
    """Resolve the first active Rust rule on each jointly reachable opponent turn decision."""
    root, sub = source['root'], source['subgame']
    hero = native['job']['hero']
    by_pattern = {r['pat']: r for r in rules}
    active = {}
    assumed = None
    for node in sub['nodes']:
        if len(node['board']) != 8 or node['player'] == hero or len(node['acts']) < 2:
            continue
        key = '|'.join((node['board'], node['line'], str(node['player'])))
        if not compatible_node_reach(root, sub, node, masks[key])['compatible_hole_card_pairs']:
            continue
        match = next((r for r in native['locks'] if re.search(r['pat'], node['line'])), None)
        if not match:
            continue
        pattern = match['pat']
        config = next(r for r in native['job']['locks'] if r['pat'] == pattern)
        stats = sub['info']['lock_stats'][pattern]
        assert stats['nodes'] > 0
        if match['scope'] == 'ASSUMED_HISTORY_RATE_OR_SIZE' and pattern == '.*/x$':
            assert config['bet'] == .45 and match['n'] == 0 and abs(stats['agg'] - .45) < .001
            assumed = dict(pattern=pattern, bet=.45, pool_decisions=0,
                           applied_subgame_nodes=stats['nodes'], scope=match['scope'])
            continue
        if match['scope'] != 'PINNED_MEASURED_NL2_SOURCE':
            continue
        rule = by_pattern[pattern]
        label = match['source']
        assert rule['src'] == label and rule['n'] == match['n'] >= 500
        table = pool['postflop_HU']
        if label == 'SRP_turn_stab_ip_after_pfr_checks':
            values = table[label]
        else:
            family, metric = label.split('.')
            assert family in ('SRP_PFR_IP', 'SRP_PFR_OOP')
            if metric.startswith('vs_turn_barrel_by_size['):
                bucket = re.fullmatch(r'vs_turn_barrel_by_size\[(34-55%|81-110%)\]', metric)[1]
                values = table[family]['vs_turn_barrel_by_size'][bucket]
            else:
                assert metric in ('delayed_cbet', 'vs_probe', 'vs_delayed_cbet')
                values = table[family][metric]
        assert match['n'] == values['n']
        summary = dict(street=2, pattern=pattern, source=label, token='history',
                       n=values['n'], nodes=stats['nodes'])
        if 'bet' in config:
            assert config['bet'] == values['pct'] / 100 and abs(stats['agg'] - config['bet']) < .001
            assert rule['szsrc'].endswith(' (proxy)') and rule['sizes'] == config['sizes']
            summary.update(opportunity='BET', target_bet_pct=values['pct'], bet_pct=100*stats['agg'],
                           size_proxy=rule['szsrc'])
        else:
            assert (config['fold'], config['raise']) == (values['fold']/100, values['raise']/100)
            # The driver reports its achieved, reach-weighted aggregate independently of the target.
            summary.update(opportunity='FACING_BET', target_fold_pct=values['fold'], target_raise_pct=values['raise'],
                           fold_pct=100*stats['fold'], raise_pct=100*stats['agg'])
        if pattern in active:
            assert active[pattern] == summary
        active[pattern] = summary
    return list(active.values()), assumed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals', required=True, type=Path)
    parser.add_argument('--solver', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip() == SOLVER
    raw_pool = (solver / 'inputs/pool_stats.json').read_bytes()
    assert sha(raw_pool) == POOL
    pool = json.loads(raw_pool)['NL2']
    sys.path.insert(0, str(solver / 'postflop/py'))
    import pipeline
    import ranges

    pins = json.loads(PINS.read_bytes())
    previous = json.loads(RESULTS.read_bytes())
    assert previous['run'] == RUN and previous['pool_sha256'] == POOL
    pending = {(r['parent_source'],r['model_id']) for r in previous['records']
               if r['status'] == 'MISSING_VERIFIED_TURN_OR_RIVER_LOCK'}
    registry = json.loads(REGISTRY.read_bytes())['records']
    _, refs, gtos, _ = read_replays()
    observations, outcomes = {}, []
    out = args.out/'data/solver_evidence'
    out.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as temp:
        for key, pin in pins.items():
            selected = [t for t in pin['targets'] if (key,t['model_id']) in pending]
            if not selected:
                continue
            old = original(args.originals,pin,ranges)
            prior_boards = targets(dict(pin,targets=selected),old,registry,refs,gtos)
            replay = SimpleNamespace(replay=Path.cwd(), run=RUN)
            source, raw, rates = solve_or_replay(replay,old,pipeline,pool,Path(temp),archive_code='B521_'+key)
            assert raw.read_bytes() == (EVIDENCE/raw.name).read_bytes() and {r['street'] for r in rates} == {3}
            native = json.loads(gzip.decompress(raw.read_bytes()))
            masks = game_reach(old['root'],source['subgame'])[0]
            _, rules = pipeline.lock_list(old['spot'],old['version'],old['flop'])
            measured, assumed = history_rates(native,source,pool,rules,masks)
            for model, board, prior in prior_boards:
                row = register(out,model,board,old,source,raw,measured+rates,observations,masks,
                               batch='B530',source_suffix='_'+key)
                row.update(parent_source=key,model_id=model['model_id'])
                outcomes.append(row)
                if row['status'] != 'REGISTERED':
                    continue
                observations[source_key(model['model_id'],prior)] = prior
                overlay = out/f"lock_variants/rank{row['rank']}_b530_{key}.json"
                item = json.loads(overlay.read_bytes())
                item['lock']['variant_label'] = '轉牌實測行動線與河牌尺寸鎖頻'
                if assumed:
                    item['lock']['turn_checked_to_bet_assumption'] = assumed
                write(overlay,item)
    assert len(outcomes) == len(pending)
    write(out.parent/'nl2_hu_b530_native_street_locks.json',dict(run=RUN,pool_sha256=POOL,records=outcomes))
    write(out.parent/'nl2_hu_b530_locked_medium.json',dict(schema='NL2_HU_B530_ORIGINAL_LOCKED_MEDIUM_V1',references=observations))


if __name__ == '__main__':
    main()
