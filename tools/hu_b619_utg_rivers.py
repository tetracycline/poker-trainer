"""Replay priced UTG/CO river decisions from pinned CFR ranges and original native policies."""
import argparse
import base64
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b514_turn_stab import rates
from hu_b527_checked_barrels import COLUMNS, board_row
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, game_reach
from hu_trainer_route_gate import compatible
from run10_common import classes, hcls
from verify_hu_multiboard_100bb import lock_scope

DATA = Path('data')
BETS = {619: {109: 75, 110: 50, 111: 33}, 639: {95: 75, 96: 33, 99: 50}}
FLOP_LINE = {619: 'x x', 639: 'b50 c'}
FLOP_PAID = {619: 0, 639: 325}
TEMPLATE = 'NL2_B538_JH9S4C_QC_45119866932.json.gz'
TEMPLATE_SHA = '716e87c13e000aa3d8593bce99ba4a87157d8e57fd05e672589547d8c9ce6a93'


def reproduce(job, original, driver, cache):
    """Exclude elapsed time from the comparison, retaining every native array and statistic."""
    def normalized(result):
        info = {k: v for k, v in result['info'].items() if k != 'secs'}
        return sha(json.dumps(dict(result, info=info), sort_keys=True, separators=(',', ':')).encode())
    key = sha(compact(job))
    if key not in cache:
        with tempfile.TemporaryDirectory() as work:
            Path(work, 'job.json').write_bytes(compact(job))
            subprocess.run([str(driver), 'job.json'], cwd=work, env=dict(os.environ, RAYON_NUM_THREADS='1'), check=True)
            cache[key] = normalized(json.loads(Path(work, job['out']).read_bytes()))
    assert cache[key] == normalized(original), (job['flop'], job['out'])


def sources(batch, rank, spec, template, pool, pipeline, run, driver, cache):
    flop, turn = spec['flop'], spec['turn']
    pct = BETS[batch][rank]
    flop_line, flop_paid = FLOP_LINE[batch], FLOP_PAID[batch]
    turn_pot, turn_stack = 650 + 2*flop_paid, 9750 - flop_paid
    code = f'B{batch}_R{rank}_{flop.upper()}'
    archive = EVIDENCE / f'NL2_{code}.zip'
    assert sha(archive.read_bytes()) == spec['archive_sha256']
    with ZipFile(archive) as bundle:
        raw = {name: bundle.read(name) for name in bundle.namelist()}
    assert set(raw) == {s+ext for s in ('root', 'gto', 'native') for ext in ('.job.json', '.json')}
    assert turn in spec['root_turns'] and spec['river'] in spec['river_extracts']
    root_job = dict(template['root_job'], flop=flop, out='result.json', flop_oop='50%', flop_ip='50%',
                    extract=[dict(prefix=[], street=True)] + [dict(prefix=flop_line.split()+[t], street=False, raw=True) for t in spec['root_turns']])
    assert root_job == json.loads(raw['root.job.json'])
    root = json.loads(raw['root.json'])
    assert (root['flop'], root['pot'], root['stack']) == (flop, 650, 9750)
    assert 0 <= root['info']['gto_expl_pct'] <= .5 and not root['info'].get('lock_stats')
    if driver:
        reproduce(root_job, root, driver, cache)
    first, second = flop_line.split()
    for line, seat, price, bets, action in [('', 0, 650, [0,0], first), (first, 1, 650+flop_paid, [flop_paid,0], second)]:
        node, = [n for n in root['nodes'] if n['line'] == line]
        assert (node['player'], node['pot'], node['bets']) == (seat, price, bets) and action in node['acts']
    parent, = [n for n in root['nodes'] if n['line'] == flop_line+'/' and n['board'].endswith(turn)]
    assert (parent['pot'],parent['bets'],parent['player']) == (turn_pot,[flop_paid,flop_paid],0)
    job = dict(template['subgame_job'], flop=flop, turn=turn, line0=flop_line.split()+['/'], pot=turn_pot, stack=turn_stack, out='gto.json',
               turn_oop=f'{pct}%', turn_ip='50%,100%', river_oop='50%,75%,100%,a', river_ip='50%,75%,100%,a',
               root_no_bet=False, iters=2200, rank_pct=.45, target_pct=.45,
               extract=[dict(prefix=[], street=True)] + [dict(prefix=[f'b{pct}', 'c', r], street=True) for r in spec['river_extracts']])
    for seat, key in enumerate(('oop_w','ip_w')):
        job[key] = [[h,w] for h,w in zip(root['hands'][seat], parent['wr'][seat], strict=True) if w > 1e-4]
    root_sha = sha(compact(root))
    manifest = dict(spot='UTG_CO', pot_family='SRP', locks=[], preflop_ranges=template['manifest']['preflop_ranges'])
    gto = dict(version='gto', root=root, run=run, manifest=manifest, root_sha256=root_sha,
               archive_code=code, archive_sha256=spec['archive_sha256'])
    native_job, rules = prepare_job(dict(source=gto, job=job), 'exp_oop', pool, pipeline)
    locked = dict(gto, version='exp_oop', manifest=dict(manifest, locks=rules, gto_parent_source_run_id=run, gto_parent_source_sha256=root_sha),
                  verified_gto_parent=dict(run=run, sha256=root_sha))
    for source, mode, expected in [(gto, 'gto', job), (locked, 'native', native_job)]:
        assert json.loads(raw[mode+'.job.json']) == expected
        result = raw[mode+'.json']
        sub = json.loads(result)
        if driver:
            reproduce(expected, sub, driver, cache)
        assert (sub['flop'], sub['pot'], sub['stack']) == (flop,turn_pot,turn_stack)
        assert sub['nodes'][0]['board'] == parent['board'] and 0 <= sub['info']['gto_expl_pct'] <= .5
        sub.update(line0=flop_line, turn=turn, rivers=spec['river_extracts'])
        source.update(subgame=sub, source_sha256=sha(result))
    ginfo, linfo = (s['subgame']['info'] for s in (gto, locked))
    assert not ginfo.get('lock_stats') and 0 <= linfo['hero_gap_pct'] <= .5
    assert gto['subgame']['hands'] == locked['subgame']['hands']
    locked.update(applied_rust_rates=linfo['lock_stats'],
                  measured_lock_application=audit_patterns(locked['subgame'],native_job,locked['manifest'],pool,hero_seat=0))
    return (gto, locked), parent['board'] + spec['river']


def decision(source, public, pct, route, spr, require_displayed_action=False):
    sub = source['subgame']
    bet = f'b{pct}'
    turn_pot, turn_stack = sub['pot'], sub['stack']
    paid = (turn_pot*pct+50)//100
    turn_line = sub['line0']+'/'
    line = f'{turn_line}{bet} c/'
    steps = [(public[:8], turn_line, 0, turn_pot, [0,0], bet),
             (public[:8], turn_line+bet, 1, turn_pot+paid, [paid,0], 'c'),
             (public, line, 0, turn_pot+2*paid, [paid,paid], 'b50')]
    for board, path, seat, pot, bets, action in steps:
        node, = [n for n in sub['nodes'] if (n['board'],n['line'],n['player']) == (board,path,seat)]
        assert (node['pot'],node['bets']) == (pot,bets) and action in node['acts']
    assert abs((turn_stack-paid)/(turn_pot+2*paid)/spr-1) <= .05
    root, info = source['root'], sub['info']
    row = proof(root, sub, node, game_reach(root,sub)[0])
    row.update(version=source['version'],spot='UTG_CO',family='SRP',flop=sub['flop'],turn=sub['turn'],
               source_run_id=source['run'],source_sha256=source['source_sha256'],archive_sha256=source['archive_sha256'],
               root_sha256=source['root_sha256'],root_gto_stage_gap_pct=root['info']['gto_expl_pct'],root_locked_hero_gap_pct=None,
               gto_gap_pct=info['gto_expl_pct'],locked_hero_gap_pct=info.get('hero_gap_pct'),
               lock_scope=lock_scope(sub,source['manifest']['locks'],source['version']),root_applied_rust_lock_nodes=0,
               subgame_applied_rust_lock_nodes=sum(s['nodes'] for s in info.get('lock_stats',{}).values()))
    assert row['compatible_hole_card_pairs'] > 0
    masks = base64.b64decode(row['compatible_action_mask_b64'], validate=True)
    actions = node['acts']
    assert actions == row['source_actions'] and {'x', 'b50'} <= set(actions)
    result = {}
    for index, (hole, mask) in enumerate(zip(sub['hands'][0], masks, strict=True)):
        if not mask:
            continue
        hand = ''.join(cardkey(hole))
        labels = [hcls(hand, public[:6]), hcls(hand, public[:8]), classes(hand, public)[0]]
        if any(label not in COLUMNS for label in labels):
            continue
        keys = [f'{board_row(public[:end])}:{COLUMNS.index(label)}' for end, label in zip((6, 8, 10), labels, strict=True)]
        if any(key not in route[street] for key, street in zip(keys, ('flop', 'turn', 'river'), strict=True)):
            continue
        if require_displayed_action:
            wanted = {'過': 'x', '下注 ¾': 'b75'}[route['river'][keys[-1]]]
            if wanted not in actions or not mask & (1 << actions.index(wanted)):
                continue
        weights = [max(0.0, node['strat'][i * len(masks) + index]) for i in range(len(actions))]
        total = sum(weights)
        assert total > 0
        result[hand] = (labels, route['river'][keys[-1]], dict(
            action_order=actions, accepted_mask=mask, accepted_actions=[a for i, a in enumerate(actions) if mask & (1 << i)],
            strategy={a: round(w / total, 7) for a, w in zip(actions, weights, strict=True)}))
    return row, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=int, choices=tuple(BETS), default=619)
    parser.add_argument('--solver', required=True, type=Path)
    parser.add_argument('--run', type=int)
    parser.add_argument('--reproduce-flop')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    assert args.run is None or args.run > 0 and not args.reproduce_flop
    batch = args.batch
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip() == SOLVER
    py = solver/'postflop/py'
    assert sha((py/'pipeline.py').read_bytes()) == PIPELINE and sha((py/'ranges.py').read_bytes()) == RANGES
    driver = None
    if args.reproduce_flop:
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip() == RUST
        driver = solver/'postflop/pfdriver/target/release/pfdriver'
    sys.path.insert(0, str(py))
    import pipeline
    from solve_hu_missing_branches import EXTRA_SPOTS
    pipeline.SPOTS.update(EXTRA_SPOTS)
    raw = (EVIDENCE/TEMPLATE).read_bytes()
    assert sha(raw) == TEMPLATE_SHA
    template, = [s for s in json.loads(gzip.decompress(raw))['source_arrays'] if s['version']=='gto']
    manifest = template['manifest']
    assert (manifest['spot'], manifest['pot_family'], manifest['solver_pin'], manifest['solver_ranges_sha256']) == ('UTG_CO','SRP',PIPELINE,RANGES)
    assert manifest['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR' and manifest['preflop_ranges']['spot']=='UTG_CO'
    poolraw = (solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw) == POOL
    pool = json.loads(poolraw)['NL2']
    registry = json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records']
    contracts = json.loads((DATA/'nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes']
    routes = json.loads(subprocess.check_output(['node','tools/hu_b619_utg_routes.cjs',str(batch)]))
    specs = json.loads((DATA/f'nl2_hu_b{batch}_utg_inputs.json').read_bytes())
    report, cache = [], {}
    medium = dict(schema=f'NL2_HU_B{batch}_ORIGINAL_LOCKED_MEDIUM_V1', references={}, gto_references={})
    for key, entries in specs.items():
        rank, route = int(key), routes[key]
        pct = BETS[batch][rank]
        line = f'{FLOP_LINE[batch]}/b{pct} c/'
        model = registry[route['id']]
        assert model['frequency_rank'] == rank
        assert 1 <= len(entries) <= 5 and len({suit_isomorphism_class(s['flop']) for s in entries}) == len(entries)
        group = dict(rank=rank,model_id=route['id'],boards=[],pins=[])
        prior_path = EVIDENCE / 'reverified' / f'rank{rank}.json'
        published_runs = {}
        if args.run and prior_path.exists():
            prior = json.loads(prior_path.read_bytes())
            assert prior['model_id'] == route['id']
            published_runs = {(p['flop'], p['archive_sha256']): p['source_run_id'] for p in prior['pins']}
        for spec in entries:
            flop = spec['flop']
            if args.reproduce_flop and flop != args.reproduce_flop:
                continue
            # Reproducing identical published inputs retains their original verification run.
            source_run = published_runs.get((flop, spec['archive_sha256']), args.run)
            pair, public = sources(batch,rank,spec,template,pool,pipeline,source_run,driver,cache)
            assert compatible(contracts[route['id']],dict(public_board=public,actual_exact_action_line=line,acting_seat=0))
            records = [decision(s, public, pct, route, model['assumed_model_node_spr'], require_displayed_action=batch == 639) for s in pair]
            rows, hands = zip(*records, strict=True)
            common = []
            for hand in sorted(hands[0].keys() & hands[1].keys()):
                (fc,tc,rc), label, gpol = hands[0][hand]
                assert hands[0][hand][:2] == hands[1][hand][:2]
                common.append(dict(hand=hand,flop_class=fc,turn_class=tc,river_class=rc,displayed_suggestion=label,
                                   gto=gpol,nl2=hands[1][hand][2]))
            assert common, (rank, public)
            report.append(dict(rank=rank,flop=flop,public_board=public,shared_hands=len(common),
                               compatible_pairs=[r['compatible_hole_card_pairs'] for r in rows],locked_half_pot_candidate=rows[1]['b50']['candidate']))
            if args.run and len(entries) >= 3:
                gto, locked = pair
                board,pin = emit_board(model,gto,locked,public,line,texture(flop),viewer_code=f'B{batch}_R{rank}_{flop.upper()}')
                board.update(source_run_role='VERIFICATION_OF_LOCAL_NATIVE_RESULTS',origin_solve_run_id=None,restricted_flop_bet_sizes_pct=[50],
                             flop_bet_size_menu='50%',conditional_turn_oop_bet_sizes_pct=[pct],conditional_turn_ip_bet_sizes_pct=[50,100])
                board['nl2_locked_variants'][0].update(source_run_role=board['source_run_role'],origin_solve_run_id=None,pool_sha256=POOL,
                    measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(locked),gto_parent_source_run_id=source_run,
                    gto_parent_source_sha256=gto['root_sha256'],viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
                pin.update(rendered_decision_hands=common,source_run_role=board['source_run_role'],template_archive_sha256=TEMPLATE_SHA)
                group['boards'].append(board)
                group['pins'].append(pin)
                for name,row in zip(('gto_references','references'),rows,strict=True):
                    medium[name][source_key(route['id'],row)] = row
        if args.run and len(entries)>=3:
            assert len(group['boards']) == len(entries)
            (EVIDENCE/'reverified'/f'rank{rank}.json').write_bytes(json_bytes(group))
    assert report
    if args.out:
        args.out.write_bytes(json_bytes(report))
    if args.run:
        (DATA/f'nl2_hu_b{batch}_locked_medium.json').write_bytes(json_bytes(medium))


if __name__ == '__main__':
    main()
