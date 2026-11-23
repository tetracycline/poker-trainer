"""Replay three exact CO three-bet-pot half-pot turn barrels at the river decision."""
import argparse
import base64
import gzip
import json
import re
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b514_turn_stab import rates
from hu_b527_checked_barrels import COLUMNS, board_row, hcls
from hu_b537_threebet_checked import MODELS, RANGE_SHA, exact_row
from hu_b581_checked_rivers import B537, RUST, SOLVER, input_jobs
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, compatible_node_reach, game_reach
from solve_hu_missing_branches import EXTRA_SPOTS
from run10_common import classes

DATA = Path('data')
MODEL, LINE, INVESTMENT = MODELS[244]
SUGGESTIONS = {'過': 'x', '下注 ½': 'b50'}


def policy_hands(src, row, routes):
    game = src['subgame']
    public = row['public_board']
    target, = (n for n in game['nodes'] if (n['board'], n['line'], n['player']) == (public,LINE,0))
    actions = target['acts']
    assert actions == row['source_actions'] and {'x','b50'} <= set(actions)
    masks = base64.b64decode(row['compatible_action_mask_b64'], validate=True)
    result = {}
    for i, (hole, mask) in enumerate(zip(game['hands'][0], masks, strict=True)):
        if not mask:
            continue
        hand = ''.join(cardkey(hole))
        labels = [hcls(hand,public[:6]), hcls(hand,public[:8]), classes(hand,public)[0]]
        if any(c not in COLUMNS for c in labels):
            continue
        keys = [f'{board_row(public[:end])}:{COLUMNS.index(c)}' for end,c in zip((6,8,10), labels, strict=True)]
        if any(k not in routes[stage] for stage,k in zip(('flop','turn','river'), keys, strict=True)):
            continue
        suggestion = routes['river'][keys[-1]]
        assert suggestion in SUGGESTIONS
        w = [max(0., target['strat'][j*len(masks)+i]) for j in range(len(actions))]
        total = sum(w)
        assert total > 0
        result[hand] = dict(classes=labels, displayed=suggestion, policy=dict(action_order=actions, accepted_mask=mask,
            accepted_actions=[a for j,a in enumerate(actions) if mask & (1<<j)],
            strategy={a:round(weight/total,7) for a,weight in zip(actions,w,strict=True)}))
    return result



def measured_responses(source, public, pool):
    sub = source['subgame']
    masks = game_reach(source['root'], sub)[0]
    report = []
    for street, board, line, pot, bets in (
        (2, public[:8], 'x x/b50', 2475, [825, 0]),
        (3, public, LINE + 'b50', 4950, [2475, 825]),
    ):
        node, = (n for n in sub['nodes'] if (n['board'], n['line'], n['player']) == (board, line, 1))
        assert (node['pot'], node['bets']) == (pot, bets)
        rule = next(r for r in source['native_job']['locks'] if re.search(r['pat'], line))
        meta = next(r for r in source['manifest']['locks'] if re.search(r['pat'], line))
        assert meta['pat'] == rule['pat']
        stat = sub['info']['lock_stats'][rule['pat']]
        assert stat['nodes'] > 0
        if street == 3:
            observed = pool['HU_facing_bet']['3']['by_size']['34-55%']
            assert meta['n'] == observed['n'] and rule['fold'] == observed['fold']/100 and rule['raise'] == observed['raise']/100
        reach = compatible_node_reach(source['root'], sub, node, masks[f'{board}|{line}|1'])
        report.append(dict(board=board, line=line, first_rule=rule, n=meta['n'], source=meta['source'], scope=meta['scope'],
                           applied_nodes=stat['nodes'], compatible_hole_card_pairs=reach['compatible_hole_card_pairs']))
    assert report[0]['compatible_hole_card_pairs'] > 0
    return report


def replay(spec, routes, pool, pipeline, run, receipts):
    flop, turn, river = (spec[k] for k in ('flop','turn','river'))
    parent = json.loads(gzip.decompress((EVIDENCE/spec['prior_archive']).read_bytes()))
    assert (parent['run_id'], parent['solver'], parent['rust']) == (B537, SOLVER, RUST)
    gto_parent, = (s for s in parent['source_arrays'] if s['version'] == 'gto')
    root = gto_parent['root']
    root_sha = sha(compact(root))
    assert root_sha == gto_parent['root_sha256'] == gto_parent['manifest']['file_flop_sha256']
    assert root['flop'] == flop and (root['pot'], root['stack']) == (1650, 9250)
    job = gto_parent['root_job']
    assert sha(compact([job['oop'],job['ip']])) == RANGE_SHA['gto']
    assert dict(prefix=['x','x',turn],street=False,raw=True) in job['extract']
    original = receipts / (str(spec['original_artifact_id']) + '.zip')
    assert sha(original.read_bytes()) == spec['original_artifact_sha256']
    with ZipFile(original) as receipt:
        mf = json.loads(receipt.read('trainer/evidence/'+flop+'-gto.json'))
        member = 'solver/postflop/' + mf['file_flop']
        assert sha(receipt.read(member)) == root_sha == mf['file_flop_sha256']
        assert json.loads(receipt.read(member.replace('.json','.job.json'))) == job
        assert (mf['solver_pin'],mf['solver_ranges_sha256'],mf['pool_source_sha256']) == (PIPELINE,RANGES,POOL)
    assert 0 <= root['info']['gto_expl_pct'] <= .5 and not root['info'].get('lock_stats')
    gto, lock, manifest, meta = input_jobs(flop, turn, river, root, gto_parent, pool, pipeline)
    for expected in (gto,lock):
        expected['extract'] = [dict(prefix=[],street=True), dict(prefix=['b50','c',river],street=True)]
    package = EVIDENCE/spec['archive']
    assert sha(package.read_bytes()) == spec['sha256']
    pair, rows, policies = [], [], []
    with ZipFile(package) as archive:
        for version, expected in [('gto',gto), ('exp_oop',lock)]:
            raw = archive.read(version+'.json')
            assert json.loads(archive.read(version+'.job.json')) == expected
            sub = json.loads(raw)
            assert (sub['flop'],sub['pot'],sub['stack']) == (flop,1650,9250) and 0 <= sub['info']['gto_expl_pct'] <= .5
            sub.update(turn=turn, rivers=[river], line0='x x')
            node, = (n for n in sub['nodes'] if (n['line'],n['player']) == (LINE,0))
            public = node['board']
            assert sorted(public[i:i+2] for i in (0,2,4)) == sorted(flop[i:i+2] for i in (0,2,4))
            assert public[6:] == turn+river and (node['pot'], node['bets']) == (3300,[INVESTMENT,INVESTMENT])
            source = dict(version=version, root=root, root_sha256=root_sha, subgame=sub, manifest=dict(manifest),
                          run=run, native_job=expected, source_sha256=sha(raw), archive_sha256=spec['sha256'],
                          archive_code=package.stem.removeprefix('NL2_'))
            if version == 'exp_oop':
                assert 0 <= sub['info']['hero_gap_pct'] <= .5 and sub['hands'] == pair[0]['subgame']['hands']
                source['manifest'].update(version=version, locks=meta, gto_parent_source_run_id=B537, gto_parent_source_sha256=root_sha)
                source['verified_gto_parent'] = dict(run=B537, sha256=root_sha)
                source['measured_lock_application'] = audit_patterns(sub,expected,source['manifest'],pool,hero_seat=0)
                source['applied_rust_rates'] = sub['info']['lock_stats']
            else:
                assert not sub['info'].get('lock_stats')
            masks = game_reach(root,sub)[0]
            row, _ = exact_row(source,LINE,public,INVESTMENT,masks)
            assert row['compatible_hole_card_pairs'] > 0 and row['b50'] is not None
            rows.append(row)
            policies.append(policy_hands(source,row,routes))
            pair.append(source)
    hands = []
    for hand in sorted(policies[0].keys() & policies[1].keys()):
        g, e = [p[hand] for p in policies]
        assert (g['classes'],g['displayed']) == (e['classes'],e['displayed'])
        f,t,r = g['classes']
        hands.append(dict(hand=hand,flop_class=f,turn_class=t,river_class=r,flop_texture=board_row(public[:6]),
                          turn_texture=board_row(public[:8]),river_texture=board_row(public),
                          displayed_suggestion=g['displayed'],gto=g['policy'],nl2=e['policy']))
    assert hands
    agreement = {key:sum(all(SUGGESTIONS[h['displayed_suggestion']] in h[k]['accepted_actions'] for k in modes) for h in hands)
                 for key,modes in [('gto',('gto',)),('nl2',('nl2',)),('both',('gto','nl2'))]}
    return public,pair,rows,hands,agreement,measured_responses(pair[1],public,pool)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver',type=Path,required=True)
    parser.add_argument('--run',type=int)
    parser.add_argument('--receipts',type=Path,required=True)
    args = parser.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip() == SOLVER
    assert sha((solver/'postflop/py/pipeline.py').read_bytes()) == PIPELINE and sha((solver/'postflop/py/ranges.py').read_bytes()) == RANGES
    raw = (solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    pipeline.SPOTS.update(EXTRA_SPOTS)
    routes = json.loads(subprocess.check_output(['node','tools/hu_b591_rank244_routes.cjs']))['244']
    inputs = json.loads((DATA/'nl2_hu_b591_rank244_inputs.json').read_bytes())
    boards = inputs['boards']
    assert (inputs['solver'],inputs['rust']) == (SOLVER,RUST)
    assert len(boards) == len({entry['flop'][::2] for entry in boards}) == 3
    model = json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr']) == (244,'CO3_BTN',2.553)
    group = dict(rank=244,model_id=MODEL,boards=[],pins=[])
    medium = dict(schema='NL2_HU_B591_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    for spec in boards:
        public,(g,e),(gr,er),hands,agreement,responses = replay(spec,routes,pool,pipeline,args.run,args.receipts)
        print(public, len(hands), agreement, [r['compatible_hole_card_pairs'] for r in responses], [r['b50']['candidate'] for r in (gr,er)])
        if args.run is None:
            continue
        assert args.run > 0
        board,pin = emit_board(model,g,e,public,LINE,texture(spec['flop']),viewer_code='B591_R244_'+spec['flop'].upper())
        board.update(source_run_role='VERIFICATION_OF_LOCAL_NATIVE_RESULTS',origin_solve_run_id=None)
        board['nl2_locked_variants'][0].update(source_run_role=board['source_run_role'],origin_solve_run_id=None,
            variant_label='翻牌 GTO 範圍，轉河牌依 NL2 下注頻率鎖定對手',pool_sha256=POOL,
            gto_parent_source_run_id=B537,gto_parent_source_sha256=g['root_sha256'],applied_street_rates=rates(e),
            measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
        pin.update(source_run_role='GITHUB_ACTIONS_AUTHENTICATED_LOCAL_NATIVE_IMPORT',flop_boundary_authentication_run=B537,
                   original_flop_archive=spec['prior_archive'],original_opponent_rules=responses,rendered_decision_hands=hands,
                   hands_accepting_displayed_suggestion=agreement)
        group['boards'].append(board)
        group['pins'].append(pin)
        medium['gto_references'][source_key(MODEL,gr)] = gr
        medium['references'][source_key(MODEL,er)] = er
    if args.run:
        (EVIDENCE/'reverified/rank244.json').write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b591_locked_medium.json').write_bytes(json_bytes(medium))


if __name__ == '__main__':
    main()
