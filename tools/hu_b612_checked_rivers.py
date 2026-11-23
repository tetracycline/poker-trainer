"""Authenticate river continuations from the B607 flop and turn ranges for both seats."""
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
from hu_b483_locked_medium import POOL
from hu_b514_turn_stab import rates
from hu_b527_checked_barrels import COLUMNS, board_row
from hu_b607_checked_3bet_turns import STUDY
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, prepare_job
from hu_checked_stab_turns import replay
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey
from hu_trainer_route_gate import compatible
from run10_common import classes, hcls

DATA = Path('data')
LINE = {260: 'x x/x x/', 308: 'x x/x x/x'}
MODE = {260: 'exp_oop', 308: 'exp_ip'}


def policies(source, row, rank, route):
    public = row['public_board']
    sub = source['subgame']
    seat = int(rank == 308)
    node, = [n for n in sub['nodes'] if (n['board'], n['line'], n['player']) == (public, LINE[rank], seat)]
    assert node['pot'] == 1650 and node['bets'] == [0, 0]
    masks = base64.b64decode(row['compatible_action_mask_b64'], validate=True)
    actions = node['acts']
    assert actions == row['source_actions'] and {'x', 'b50'} <= set(actions)
    result = {}
    for index, (hole, mask) in enumerate(zip(sub['hands'][seat], masks, strict=True)):
        if not mask:
            continue
        hand = ''.join(cardkey(hole))
        labels = [hcls(hand, public[:6]), hcls(hand, public[:8]), classes(hand, public)[0]]
        if any(label not in COLUMNS for label in labels):
            continue
        keys = [f'{board_row(public[:end])}:{COLUMNS.index(label)}' for end, label in zip((6, 8, 10), labels, strict=True)]
        if any(key not in route[street] for key, street in zip(keys, ('flop', 'turn', 'river'), strict=True)):
            continue
        weights = [max(0.0, node['strat'][i * len(masks) + index]) for i in range(len(actions))]
        total = sum(weights)
        assert total > 0
        result[hand] = (labels, route['river'][keys[-1]], dict(
            action_order=actions, accepted_mask=mask, accepted_actions=[a for i, a in enumerate(actions) if mask & (1 << i)],
            strategy={a: round(w / total, 7) for a, w in zip(actions, weights, strict=True)}))
    return result


def native_result(z, job, driver, source):
    raw = z.read(job['out'])
    expected = json.loads(raw)
    if driver:
        with tempfile.TemporaryDirectory() as work:
            Path(work, 'job.json').write_bytes(compact(job))
            subprocess.run([str(driver),'job.json'], cwd=work, env=dict(os.environ, RAYON_NUM_THREADS='1'), check=True)
            fresh = json.loads(Path(work, job['out']).read_bytes())
            assert {k:v for k,v in fresh.items() if k != 'info'} == {k:v for k,v in expected.items() if k != 'info'}
            assert {k:v for k,v in fresh['info'].items() if k != 'secs'} == {k:v for k,v in expected['info'].items() if k != 'secs'}
    if source:
        # New river exports must retain every original turn strategy, payoff and range.
        assert source['hands'] == expected['hands']
        turn_nodes = [n for n in expected['nodes'] if len(n['board']) == 8]
        assert source['nodes'] == turn_nodes
    assert (expected['pot'], expected['stack']) == (1650,9250)
    assert 0 <= expected['info']['gto_expl_pct'] <= .5
    return sha(raw), expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver', required=True, type=Path)
    parser.add_argument('--run', type=int)
    parser.add_argument('--reproduce-flop')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    assert args.run is None or args.run > 0
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip() == SOLVER
    driver = None
    if args.reproduce_flop:
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip() == RUST
        driver = solver/'postflop/pfdriver/target/release/pfdriver'
    sys.path.insert(0, str(solver/'postflop/py'))
    import pipeline
    from solve_hu_missing_branches import EXTRA_SPOTS
    pipeline.SPOTS.update(EXTRA_SPOTS)
    parent_specs = {s['flop']:s for s in json.loads((DATA/'nl2_hu_b607_checked_3bet_inputs.json').read_bytes())}
    template_raw = (EVIDENCE/STUDY.template).read_bytes()
    assert sha(template_raw) == STUDY.template_sha
    template, = [s for s in json.loads(gzip.decompress(template_raw))['source_arrays'] if s['version'] == 'gto']
    poolraw = (solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw) == POOL
    pool = json.loads(poolraw)['NL2']
    registry = json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records']
    contracts = json.loads((DATA/'nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes']
    routes = json.loads(subprocess.check_output(['node','tools/hu_b612_river_routes.cjs']))
    parent_route = json.loads(subprocess.check_output(['node','tools/hu_b592_iso_turn_routes.cjs','198']))['198']
    inputs = json.loads((DATA/'nl2_hu_b612_river_inputs.json').read_bytes())
    if args.reproduce_flop:
        inputs = [next(s for s in inputs if s['flop'] == args.reproduce_flop)]
    groups = {r:dict(rank=r, model_id=routes[str(r)]['id'], boards=[], pins=[]) for r in LINE}
    medium = dict(schema='NL2_HU_B612_ORIGINAL_LOCKED_MEDIUM_V1', references={}, gto_references={})
    report = []
    for spec in inputs:
        flop, turn = spec['flop'], spec['turn']
        parent = parent_specs[flop]
        assert turn == parent['turn']
        start, (g, ip), _, _, root_sha = replay(STUDY, parent, template, pool, pipeline, args.run, parent_route, registry[STUDY.model])
        with ZipFile(EVIDENCE/('NL2_'+STUDY.archive_code(flop)+'.zip')) as old:
            job = json.loads(old.read('gto.job.json'))
        job['extract'] = [dict(prefix=[], street=True)] + [dict(prefix=['x','x',r], street=True) for r in spec['rivers']]
        job['out'] = 'gto.json'
        archive = EVIDENCE/f'NL2_B612_{flop.upper()}.zip'
        assert sha(archive.read_bytes()) == spec['sha256']
        with ZipFile(archive) as z:
            modes = ['gto'] + [MODE[int(r)] for r in spec['targets']]
            assert set(z.namelist()) == {m+'.json' for m in modes}
            sources = {}
            for mode in modes:
                config, meta = (job, []) if mode == 'gto' else prepare_job(dict(source=g,job=job), mode, pool, pipeline)
                config = dict(config,out=mode+'.json')
                original = {'gto':g,'exp_ip':ip}.get(mode)
                digest, sub = native_result(z, config, driver, original['subgame'] if original else None)
                sub.update(line0='x x', turn=turn, rivers=spec['rivers'])
                src = dict(g, version=mode, source_sha256=digest, subgame=sub, root_sha256=root_sha,
                           archive_code=archive.stem.removeprefix('NL2_'), archive_sha256=spec['sha256'], manifest=dict(g['manifest'], locks=meta))
                if mode != 'gto':
                    assert 0 <= sub['info']['hero_gap_pct'] <= .5
                    src['manifest'].update(gto_parent_source_run_id=args.run, gto_parent_source_sha256=root_sha)
                    src.update(verified_gto_parent=dict(run=args.run,sha256=root_sha),applied_rust_rates=sub['info']['lock_stats'],
                        measured_lock_application=audit_patterns(sub, config, src['manifest'], pool, hero_seat=int(mode=='exp_ip')))
                sources[mode] = src
        for key, river in spec['targets'].items():
            rank = int(key)
            route = routes[key]
            group = groups[rank]
            model = registry[group['model_id']]
            public = start + river
            seat = int(rank == 308)
            assert compatible(contracts[group['model_id']], dict(public_board=public,actual_exact_action_line=LINE[rank],acting_seat=seat))
            pair = [sources['gto'], sources[MODE[rank]]]
            rows = [audit_decision(s,public,LINE[rank],seat,root_sha) for s in pair]
            assert all(row and row['compatible_hole_card_pairs']>0 for row in rows)
            hands = [policies(s,row,rank,route) for s,row in zip(pair,rows,strict=True)]
            common=[]
            for hole in sorted(hands[0].keys() & hands[1].keys()):
                (fc,tc,rc), label, gpol = hands[0][hole]
                assert hands[0][hole][:2] == hands[1][hole][:2]
                common.append(dict(hand=hole,flop_class=fc,turn_class=tc,river_class=rc,displayed_suggestion=label,gto=gpol,nl2=hands[1][hole][2]))
            assert common
            report.append(dict(rank=rank,flop=flop,public_board=public,shared_hands=len(common),
                               compatible_pairs=[r['compatible_hole_card_pairs'] for r in rows],locked_half_pot_candidate=rows[1]['b50']['candidate']))
            if args.run:
                gto,locked=pair
                board,pin=emit_board(model,gto,locked,public,LINE[rank],texture(flop),viewer_code=f'B612_R{rank}_{flop.upper()}')
                board.update(source_run_role='VERIFICATION_OF_LOCAL_NATIVE_RESULTS',origin_solve_run_id=None,restricted_flop_bet_sizes_pct=[50],
                             flop_bet_size_menu='50%',conditional_turn_oop_bet_sizes_pct=[33,50,75],conditional_turn_ip_bet_sizes_pct=[33,50,75])
                board['nl2_locked_variants'][0].update(source_run_role=board['source_run_role'],origin_solve_run_id=None,pool_sha256=POOL,
                    measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(locked),gto_parent_source_run_id=args.run,
                    gto_parent_source_sha256=root_sha,viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
                pin.update(rendered_decision_hands=common,source_run_role=board['source_run_role'],parent_b607_archive_sha256=parent['sha256'])
                group['boards'].append(board)
                group['pins'].append(pin)
                for member,row in zip(('gto_references','references'),rows,strict=True):
                    medium[member][source_key(group['model_id'],row)] = row
    if args.out:
        args.out.write_bytes(json_bytes(report))
    if args.run:
        for rank,group in groups.items():
            assert 3 <= len(group['boards']) == len({b['flop'] for b in group['boards']}) <= 5
            (EVIDENCE/'reverified'/f'rank{rank}.json').write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b612_locked_medium.json').write_bytes(json_bytes(medium))


if __name__ == '__main__':
    main()
