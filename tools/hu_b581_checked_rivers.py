"""Verify CO three-bet caller river decisions against native flop and turn/river CFR arrays."""
import argparse
import base64
import gzip
import json
import re
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b514_turn_stab import rates
from hu_b527_checked_barrels import COLUMNS, board_row, hcls
from hu_b537_threebet_checked import MODELS, RANGE_SHA
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, compatible_node_reach, game_reach
from solve_hu_missing_branches import EXTRA_SPOTS
from run10_common import classes

DATA = Path('data')
RANK = 261
MODEL, LINE, _ = MODELS[RANK]
B537 = 45119582030
PINS = DATA / 'nl2_hu_b581_checked_river_inputs.json'


def input_jobs(flop, turn, river, root, template, pool, pipeline):
    boundary, = (n for n in root['nodes'] if n['line'] == 'x x/' and n['board'].endswith(turn))
    assert boundary['bets'] == [0, 0] and boundary['pot'] == 1650
    job = dict(template['subgame_job'], flop=flop, turn=turn, iters=2500, rank_pct=.4, target_pct=.4,
               out='result.json', extract=[dict(prefix=[], street=True), dict(prefix=['x','x',river], street=True)])
    assert job['pot'] == 1650 and job['stack'] == 9250 and job['line0'] == ['x','x','/']
    for seat, key in enumerate(['oop_w','ip_w']):
        job[key] = [[h,w] for h,w in zip(root['hands'][seat],boundary['wr'][seat], strict=True) if w > 1e-4]
        assert job[key]
    manifest = dict(spot='CO3_BTN', pot_family='3BP', version='gto', flop=flop, locks=[])
    source = dict(manifest=manifest, version='gto', root=root)
    lock, meta = prepare_job(dict(source=source, job=job), 'exp_oop', pool, pipeline)
    lock.update(iters=2500, rank_pct=.4, target_pct=.4, out='result.json')
    return job, lock, manifest, meta


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
        assert routes['river'][keys[-1]] == '過'
        w = [max(0., target['strat'][j*len(masks)+i]) for j in range(len(actions))]
        total = sum(w)
        assert total > 0
        result[hand] = dict(classes=labels, policy=dict(action_order=actions, accepted_mask=mask,
            accepted_actions=[a for j,a in enumerate(actions) if mask & (1<<j)],
            strategy={a:round(weight/total,7) for a,weight in zip(actions,w,strict=True)}))
    return result


def response(source, public, pool):
    sub = source['subgame']
    masks = game_reach(source['root'],sub)[0]
    result = []
    for board,line in [(public[:8], 'x x/x'), (public, LINE+'b50'), (public, LINE+'x')]:
        node, = (n for n in sub['nodes'] if (n['board'],n['line'],n['player']) == (board,line,1))
        rule = next(r for r in source['native_job']['locks'] if re.search(r['pat'],line))
        meta = next(r for r in source['manifest']['locks'] if re.search(r['pat'],line))
        assert rule['pat'] == meta['pat']
        stat = sub['info']['lock_stats'][rule['pat']]
        assert stat['nodes'] > 0
        legal = compatible_node_reach(source['root'],sub,node,masks[f'{board}|{line}|1'])
        if line == 'x x/x':
            observed = pool['postflop_HU']['3BP_PFR_IP']['delayed_cbet']
            assert meta['n'] == observed['n'] and rule['bet'] == observed['pct']/100
        elif line.endswith('b50'):
            observed = pool['HU_facing_bet']['3']['by_size']['34-55%']
            assert meta['n'] == observed['n'] and rule['fold'] == observed['fold']/100 and rule['raise'] == observed['raise']/100
            assert node['pot'] == 2475 and node['bets'] == [825,0]
        result.append(dict(board=board, line=line, first_rule=rule, source=meta['source'], n=meta['n'], scope=meta['scope'],
                           applied_nodes=stat['nodes'], compatible_hole_card_pairs=legal['compatible_hole_card_pairs']))
    return result


def replay(spec, template, routes, pool, pipeline, run):
    flop, turn, river = [spec[k] for k in ('flop','turn','river')]
    package = EVIDENCE / spec['archive']
    assert sha(package.read_bytes()) == spec['sha256']
    with ZipFile(package) as archive:
        def read(name):
            return json.loads(archive.read(name))

        root, root_job = read('root.json'), read('root.job.json')
        rootsum = sha(archive.read('root.json'))
        assert rootsum == sha(compact(root))
        expected = dict(template['root_job'], flop=flop, out=root_job['out'], extract=root_job['extract'])
        assert root_job == expected and root['flop'] == flop
        assert sha(compact([root_job['oop'],root_job['ip']])) == RANGE_SHA['gto']
        assert root_job['extract'][0] == dict(prefix=[],street=True)
        assert dict(prefix=['x','x',turn],street=False,raw=True) in root_job['extract']
        if spec.get('prior_archive'):
            original = json.loads(gzip.decompress((EVIDENCE/spec['prior_archive']).read_bytes()))
            old = original['source_arrays'][0]
            assert original['run_id'] == B537 and old['root_job'] == root_job and old['root_sha256'] == rootsum
            assert old['manifest']['file_flop_sha256'] == rootsum
            parent_run = B537
        else:
            parent_run = run
        assert (root['pot'],root['stack']) == (1650,9250) and 0 <= root['info']['gto_expl_pct'] <= .5
        gto, lock, manifest, meta = input_jobs(flop,turn,river,root,template,pool,pipeline)
        pair = []
        for version,expected in [('gto',gto),('exp_oop',lock)]:
            job = read(version+'.job.json')
            assert job == expected
            raw = archive.read(version+'.json')
            sub = json.loads(raw)
            assert sub['flop'] == flop and (sub['pot'],sub['stack']) == (1650,9250)
            assert 0 <= sub['info']['gto_expl_pct'] <= .5
            sub.update(turn=turn, line0='x x', rivers=[river])
            source = dict(version=version, root=root, root_sha256=rootsum, subgame=sub,
                manifest=dict(manifest), native_job=job, source_sha256=sha(raw), archive_sha256=spec['sha256'],
                archive_code=package.stem.removeprefix('NL2_'), run=run)
            if version == 'exp_oop':
                assert 0 <= sub['info']['hero_gap_pct'] <= .5 and sub['hands'] == pair[0]['subgame']['hands']
                source['manifest'].update(version=version,locks=meta,gto_parent_source_run_id=parent_run,gto_parent_source_sha256=rootsum)
                source['verified_gto_parent'] = dict(run=parent_run,sha256=rootsum)
                source['measured_lock_application'] = audit_patterns(sub,job,source['manifest'],pool,hero_seat=0)
                source['applied_rust_rates'] = sub['info']['lock_stats']
            pair.append(source)
    pub, = (n['board'] for n in pair[0]['subgame']['nodes'] if n['line'] == LINE and n['player'] == 0)
    assert pub.endswith(turn+river) and set(pub[i:i+2] for i in (0,2,4)) == set(flop[i:i+2] for i in (0,2,4))
    rows = [audit_decision(s,pub,LINE,0,rootsum) for s in pair]
    hs = [policy_hands(s,r,routes) for s,r in zip(pair,rows,strict=True)]
    witnesses = []
    for h in sorted(hs[0].keys() & hs[1].keys()):
        labels = hs[0][h]['classes']
        assert labels == hs[1][h]['classes']
        witnesses.append(dict(hand=h,flop_class=labels[0],turn_class=labels[1],river_class=labels[2],
            flop_texture=board_row(pub[:6]),turn_texture=board_row(pub[:8]),river_texture=board_row(pub),
            displayed_suggestion='x',gto=hs[0][h]['policy'],nl2=hs[1][h]['policy']))
    assert any(all('x' in h[k]['accepted_actions'] for k in ('gto','nl2')) for h in witnesses)
    return pub, pair, rows, witnesses, response(pair[1],pub,pool), parent_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver',required=True,type=Path)
    parser.add_argument('--run',type=int)
    args = parser.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip() == SOLVER
    assert sha((solver/'postflop/py/ranges.py').read_bytes()) == RANGES and sha((solver/'postflop/py/pipeline.py').read_bytes()) == PIPELINE
    raw = (solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    pipeline.SPOTS.update(EXTRA_SPOTS)
    template = json.loads(gzip.decompress((EVIDENCE/'NL2_B537_8S7H4D_QH.json.gz').read_bytes()))['source_arrays'][0]
    routes = json.loads(subprocess.check_output(['node','tools/hu_b581_threebet_routes.cjs']))[str(RANK)]
    model = json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr']) == (RANK,'CO3_BTN',5.606)
    pins = json.loads(PINS.read_bytes())
    assert (pins['solver'],pins['rust']) == (SOLVER,RUST) and len({s['flop'] for s in pins['boards']}) == len(pins['boards']) == 3
    group = dict(rank=RANK,model_id=MODEL,boards=[],pins=[])
    medium = dict(schema='NL2_HU_B581_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    for spec in pins['boards']:
        pub,(g,e),(gr,er),hands,lock_rates,old_run = replay(spec,template,routes,pool,pipeline,args.run)
        print(pub,len(hands),gr['compatible_hole_card_pairs'],er['compatible_hole_card_pairs'])
        if not args.run:
            continue
        assert args.run > 0
        board,pin = emit_board(model,g,e,pub,LINE,texture(spec['flop']),viewer_code='B581_R261_'+spec['flop'].upper())
        board.update(source_run_role='VERIFICATION_OF_LOCAL_NATIVE_RESULTS', origin_solve_run_id=None)
        variant = board['nl2_locked_variants'][0]
        variant.update(source_run_role=board['source_run_role'], origin_solve_run_id=None)
        variant.update(variant_label='翻牌 GTO 範圍，轉河牌依 NL2 下注頻率鎖定對手',pool_sha256=POOL,
            gto_parent_source_run_id=old_run,gto_parent_source_sha256=g['root_sha256'],applied_street_rates=rates(e),
            measurement_policy='STREET_SPECIFIC_POOL_MARGINALS', viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
        pin.update(source_run_role='GITHUB_ACTIONS_AUTHENTICATED_LOCAL_NATIVE_IMPORT',
            flop_boundary_authentication_run=old_run,original_flop_archive=spec.get('prior_archive'),
            original_opponent_rules=lock_rates,rendered_decision_hands=hands,
            hands_accepting_displayed_suggestion={label:sum(all('x' in h[k]['accepted_actions'] for k in modes) for h in hands)
                for label,modes in [('gto',('gto',)),('nl2',('nl2',)),('both',('gto','nl2'))]})
        group['boards'].append(board)
        group['pins'].append(pin)
        medium['gto_references'][source_key(MODEL,gr)] = gr
        medium['references'][source_key(MODEL,er)] = er
    if args.run:
        (EVIDENCE/'reverified/rank261.json').write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b581_locked_medium.json').write_bytes(json_bytes(medium))


if __name__ == '__main__':
    main()
