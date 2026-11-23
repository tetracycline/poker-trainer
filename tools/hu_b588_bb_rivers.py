"""Verify BTN/BB native root and child policies and publish only jointly reached BB river decisions."""
import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b514_turn_stab import rates
from hu_b527_checked_barrels import board_row
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, game_reach
from verify_hu_multiboard_100bb import lock_scope
from run10_common import classes, hcls

DATA = Path('data')
SPOT = 'BTN_BB'
FLOP_LINE = 'x b50 c'
BET = {72: 50, 74: 33}


def source_pair(spec, rank, pipeline, pool, run):
    flop, turn = spec['flop'], spec['turn']
    code = f'B588_R{rank}_{flop.upper()}'
    archive = EVIDENCE / f'NL2_{code}.zip'
    assert sha(archive.read_bytes()) == spec['archive_sha256']
    with ZipFile(archive) as z:
        raw = {n: z.read(n) for n in z.namelist()}
    assert set(raw) == {'root.json', 'root.job.json', 'gto.json', 'gto.job.json', 'native.json', 'native.job.json', 'locks.json'}
    root = json.loads(raw['root.json'])
    extracts = [dict(prefix=[], street=True)] + [dict(prefix=['x', 'b50', 'c', t], street=False, raw=True) for t in spec['root_turns']]
    root_job = pipeline.make_job(SPOT, 'gto', flop, 'root.json', iters=1700, target=.5, compress=True, extract=extracts)
    root_job.update(flop_oop='50%', flop_ip='50%')
    assert root_job == json.loads(raw['root.job.json'])
    assert (root['flop'], root['pot'], root['stack']) == (flop, 550, 9750)
    assert not root['info'].get('lock_stats') and 0 <= root['info']['gto_expl_pct'] <= .5
    for line, seat, pot, bets, a in [('', 0, 550, [0, 0], 'x'), ('x', 1, 550, [0, 0], 'b50'), ('x b50', 0, 825, [0, 275], 'c')]:
        node, = [n for n in root['nodes'] if n['line'] == line]
        assert (node['player'], node['pot'], node['bets']) == (seat, pot, bets) and a in node['acts']
    parent, = [n for n in root['nodes'] if n['line'] == FLOP_LINE + '/' and n['board'].endswith(turn)]
    assert (parent['pot'], parent['bets']) == (1100, [275, 275])
    bet = f'b{BET[rank]}'
    targets = [dict(prefix=[], street=True)] + [dict(prefix=[bet, 'c', r], street=False) for r in spec['river_extracts']]
    job = pipeline.make_job(SPOT, 'gto', flop, 'gto.json', compress=False, target=.45, iters=2200, extract=targets)
    job.update(pipeline.SUB)
    job.update(oop='', ip='', turn=turn, pot=1100, stack=9475, line0=['x','b50','c','/'], root_no_bet=False,
               turn_oop=f'{BET[rank]}%', river_oop='50%,75%,100%,a', river_ip='50%,75%,100%,a')
    for seat, key in enumerate(('oop_w', 'ip_w')):
        job[key] = [[h, w] for h, w in zip(root['hands'][seat], parent['wr'][seat], strict=True) if w > 1e-4]
    assert job == json.loads(raw['gto.job.json'])
    root_sha = sha(compact(root))
    manifest = dict(spot=SPOT, pot_family='SRP', locks=[])
    g = dict(version='gto', root=root, run=run, manifest=manifest, root_sha256=root_sha,
             archive_code=code, archive_sha256=spec['archive_sha256'])
    locked, metadata = prepare_job(dict(source=g, job=job), 'exp_oop', pool, pipeline)
    assert locked == json.loads(raw['native.job.json']) and metadata == json.loads(raw['locks.json'])
    e = dict(g, version='exp_oop', manifest=dict(manifest, locks=metadata, gto_parent_source_run_id=run,
                                                 gto_parent_source_sha256=root_sha), verified_gto_parent=dict(run=run, sha256=root_sha))
    for source, name in [(g, 'gto'), (e, 'native')]:
        result = raw[name + '.json']
        sub = json.loads(result)
        assert (sub['flop'], sub['pot'], sub['stack']) == (flop, 1100, 9475)
        assert sub['nodes'][0]['board'] == parent['board'] and 0 <= sub['info']['gto_expl_pct'] <= .5
        sub.update(line0=FLOP_LINE, turn=turn, rivers=spec['river_extracts'])
        source.update(source_sha256=sha(result), subgame=sub)
    assert not g['subgame']['info'].get('lock_stats') and g['subgame']['hands'] == e['subgame']['hands']
    assert 0 <= e['subgame']['info']['hero_gap_pct'] <= .5
    e.update(applied_rust_rates=e['subgame']['info']['lock_stats'],
             measured_lock_application=audit_patterns(e['subgame'], locked, e['manifest'], pool, hero_seat=0))
    return g, e, parent['board'] + spec['river']


def decision(source, public, route, rank):
    root, sub = source['root'], source['subgame']
    bet = f'b{BET[rank]}'
    paid = {72: 550, 74: 363}[rank]
    line = FLOP_LINE + '/' + bet + ' c/'
    for b, path, seat, price, bets, action in [(public[:8], FLOP_LINE+'/', 0, 1100, [0,0], bet),
            (public[:8], FLOP_LINE+'/'+bet, 1, 1100+paid, [paid,0], 'c'),
            (public, line, 0, 1100+2*paid, [paid,paid], 'b50')]:
        node, = [n for n in sub['nodes'] if (n['board'], n['line'], n['player']) == (b, path, seat)]
        assert (node['pot'], node['bets']) == (price, bets) and action in node['acts']
    row = proof(root, sub, node, game_reach(root, sub)[0])
    info = sub['info']
    row.update(version=source['version'], spot=SPOT, family='SRP', flop=sub['flop'], turn=sub['turn'],
               source_run_id=source['run'], source_sha256=source['source_sha256'], archive_sha256=source['archive_sha256'],
               root_sha256=source['root_sha256'], gto_gap_pct=info['gto_expl_pct'], locked_hero_gap_pct=info.get('hero_gap_pct'),
               lock_scope=lock_scope(sub, source['manifest']['locks'], source['version']), root_applied_rust_lock_nodes=0,
               subgame_applied_rust_lock_nodes=sum(p['nodes'] for p in info.get('lock_stats', {}).values()))
    mask = base64.b64decode(row['compatible_action_mask_b64'], validate=True)
    names = node['acts']
    hands = sub['hands'][0]
    policies = {}
    for index, (hand, bits) in enumerate(zip(hands, mask, strict=True)):
        if not bits:
            continue
        hand = ''.join(cardkey(hand))
        labels = []
        for stage, length in enumerate((6,8,10)):
            board = public[:length]
            kind = classes(hand, board)[0] if stage == 2 else hcls(hand, board)
            labels.append(route['stages'][stage][board_row(board)].get(kind))
        if not all(labels):
            continue
        probabilities = [max(0., node['strat'][a * len(hands) + index]) for a in range(len(names))]
        total = sum(probabilities)
        assert total > 0
        policy = dict(action_order=names, accepted_mask=bits, accepted_actions=[a for j, a in enumerate(names) if bits & (1<<j)],
                      strategy={a: round(p/total, 7) for a,p in zip(names, probabilities, strict=True)})
        policies[hand] = (labels[-1], policy)
    return row, policies


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--solver', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--run', type=int)
    args = ap.parse_args()
    assert args.run is None or args.run > 0
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'], text=True).strip() == SOLVER
    py = solver/'postflop/py'
    assert sha((py/'pipeline.py').read_bytes()) == PIPELINE and sha((py/'ranges.py').read_bytes()) == RANGES
    poolraw = (solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw) == POOL
    sys.path.insert(0, str(py))
    import pipeline
    pool = json.loads(poolraw)['NL2']
    routes = json.loads(subprocess.check_output(['node', 'tools/hu_b588_bb_river_routes.cjs']))
    records = json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records']
    specs = json.loads((DATA/'nl2_hu_b588_bb_river_inputs.json').read_bytes())
    attempts = []
    medium = dict(schema='NL2_HU_B588_ORIGINAL_LOCKED_MEDIUM_V1', references={}, gto_references={})
    groups = []
    for key, entries in specs.items():
        rank = int(key)
        assert rank in BET and 3 <= len(entries) <= 5 and len({suit_isomorphism_class(s['flop']) for s in entries}) == len(entries)
        route = routes[key]
        mid = route['id']
        model = records[mid]
        assert (model['frequency_rank'], model['solver_profile'], model['family'], model['assumed_model_node_spr']) == (rank, SPOT, 'SRP', route['spr'])
        group = dict(model_id=mid, rank=rank, pins=[], boards=[])
        for spec in entries:
            g, e, public = source_pair(spec, rank, pipeline, pool, args.run)
            gr, gh = decision(g, public, route, rank)
            er, eh = decision(e, public, route, rank)
            named = []
            for hand in sorted(gh.keys() & eh.keys()):
                assert gh[hand][0] == eh[hand][0]
                named.append(dict(hand=hand, displayed_suggestion=gh[hand][0], flop_texture=board_row(public[:6]),
                                  turn_texture=board_row(public[:8]), river_texture=board_row(public),
                                  flop_class=hcls(hand,public[:6]), turn_class=hcls(hand,public[:8]), river_class=classes(hand,public)[0],
                                  gto=gh[hand][1], nl2=eh[hand][1]))
            assert named and gr['compatible_hole_card_pairs'] and er['compatible_hole_card_pairs']
            attempts.append(dict(rank=rank, public_board=public, source_flop=spec['flop'], root_sha256=g['root_sha256'],
                                 gto_sha256=g['source_sha256'], locked_sha256=e['source_sha256'], rendered_decision_hands=named,
                                 gto_medium=gr['b50'], nl2_medium=er['b50'], observed_street_rates=rates(e)))
            if not args.run:
                continue
            board, pin = emit_board(model, g, e, public, gr['line'], texture(spec['flop']), viewer_code=g['archive_code'])
            bet = BET[rank]
            provenance = dict(source_run_role='VERIFICATION_OF_LOCAL_NATIVE_RESULTS', origin_solve_run_id=None)
            board.update(**provenance, restricted_flop_bet_sizes_pct=[50], flop_bet_size_menu='50%', conditional_turn_oop_bet_sizes_pct=[bet])
            board['nl2_locked_variants'][0].update(**provenance, variant_label=f'BB 翻牌限半池；轉牌領打限 {bet}% 底池，轉河牌分街 NL2 回應鎖頻',
                pool_sha256=POOL, measurement_policy='STREET_SPECIFIC_POOL_MARGINALS', applied_street_rates=rates(e),
                gto_parent_source_run_id=args.run, gto_parent_source_sha256=g['root_sha256'], viewer_archive_code=pin['viewer_archive_code'],
                viewer_sha256=pin['viewer_sha256'])
            pin.update(rendered_decision_hands=named, authenticated_flop_boundary=dict(**provenance, verification_run_id=args.run,
                       root_canonical_sha256=g['root_sha256'], root_preflop_ranges='PINNED_POKER_SOLVER_PREFLOP_CFR', solver=SOLVER, rust=RUST,
                       restricted_flop_bet_sizes_pct=[50], conditional_turn_oop_bet_sizes_pct=[bet]))
            group['boards'].append(board)
            group['pins'].append(pin)
            medium['references'][source_key(mid, er)] = er
            medium['gto_references'][source_key(mid, gr)] = gr
        groups.append(group)
    if args.run:
        for group in groups:
            (EVIDENCE/'reverified'/f"rank{group['rank']}.json").write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b588_locked_medium.json').write_bytes(json_bytes(medium))
    args.out.write_bytes(json_bytes(dict(verification_run=args.run, solver=SOLVER, original_execution='LOCAL_PINNED_RUST', observations=attempts)))

if __name__ == '__main__':
    main()
