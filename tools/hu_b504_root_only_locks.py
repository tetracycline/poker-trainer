"""Add measured turn/river opponent locks to the six certified decisions with root-only locks."""
import argparse
import base64
import gzip
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b480_rank1_street_locks import packed
from hu_b483_locked_medium import POOL, proof
from hu_b485_locked_medium import ORIGINS, check_job, legacy_rules, read_game
from hu_board_reach_corrections import read_replays, source_key
from hu_checked_gto_boundary import lock_metadata
from hu_reverified_board_pair import source_case
from hu_sequential_cfr_reach import game_reach
from solve_hu_multiboard_100bb import make_fallbacks
from verify_hu_multiboard_100bb import lock_scope, locked_model_gain

REGISTRY = Path('data/nl2_hu_multiboard_status_current.json')
# The group is the original EXP artifact, flop action and named turn, shared by these targets.
GROUPS = (
    (44654973894, 14594206088, 'x b50 c', '9d', (9, 91, 119)),
    (44654973894, 14591994917, 'x b75 c', '9d', (190,)),
    (44525865923, 14530962451, 'x b33 r c', 'Ts', (349, 351)),
)


def write(path, data):
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_bytes(compact(data) + b'\n')


def original(folder, run, aid, flop_line, turn, pipeline, ranges):
    pin, = (p for p in ORIGINS[str(run)]['artifacts'] if p['id'] == aid)
    path = folder/f'{aid}.zip'
    assert sha(path.read_bytes()) == pin['sha256']
    with ZipFile(path) as z:
        assert {SOLVER, RUST} <= {z.read(n).decode().strip() for n in z.namelist()
                                  if n.startswith('evidence/') and n.endswith('.txt')}
        name, = (n for n in z.namelist() if n.startswith('evidence/') and n.endswith('.json'))
        m = json.loads(z.read(name))
        assert m['schema'] == 'HU_MISSING_ACTION_HISTORY_CFR_V1' and not m['failures']
        spot, version = m['spot'], m['version']
        case, = (c for c in m['cases'] if (c['line'], c['turn']) == (flop_line, turn))
        flop = case['flop']
        assert pin['name'].endswith(f'-{spot}-{version}-{flop}')
        rootraw = z.read('solver/postflop/'+case['flop_json'])
        root, rootjob = read_game(z, case['flop_json'], case['flop_sha256'])
        sub, oldjob = read_game(z, case['sub_json'], case['sub_sha256'])
    rules, _ = legacy_rules(pipeline, spot, version, flop, m['flop_bet_sizes'])
    for job, game in ((rootjob, root), (oldjob, sub)):
        check_job(job, game, version, json.loads(compact(rules)))
    assert [rootjob['oop'], rootjob['ip']] == [ranges.to_str(w) for w in ranges.ranges(spot, version)]
    assert (sub['turn'], sub['line0'], oldjob['line0']) == (turn, flop_line, [*flop_line.split(), '/'])
    assert root['info']['lock_stats'] and not sub['info']['lock_stats']
    parent, = (n for n in root['nodes'] if n['line'] == flop_line+'/' and n['board'][-2:] == turn)
    assert (parent['pot'], root['stack']-max(parent['bets'])) == (sub['pot'], sub['stack'])
    for seat, weights in enumerate(('oop_w', 'ip_w')):
        assert oldjob[weights] == [[h,w] for h,w in zip(root['hands'][seat], parent['wr'][seat], strict=True) if w > 1e-4]
    return dict(run=run, id=aid, archive_sha256=pin['sha256'], source_sha256=case['sub_sha256'],
                root_sha256=case['flop_sha256'], root=root, rootraw=rootraw,
                sub=sub, job=oldjob, version=version, spot=spot, flop=flop, turn=turn, line=flop_line)


def exact_observation(root, sub, board, masks):
    key = board['public_board'], board['actual_exact_action_line'], board['acting_seat']
    node, = (n for n in sub['nodes'] if (n['board'], n['line'], n['player']) == key)
    assert node['acts'] == board['exact_node_actions']
    assert (node['pot']/100, (sub['stack']-max(node['bets']))/100) == (board['actual_pot_bb'], board['actual_effective_stack_bb'])
    return proof(root, sub, node, masks)


def targets(old, ranks, models, locked, gtos):
    masks = game_reach(old['root'], old['sub'])[0]
    result = []
    for rank in ranks:
        model = models[rank]
        assert model['label'] == 'CERT-MULTIBOARD' and model['solver_profile'] == old['spot']
        board, = (b for b in model['certified_3_to_5_exact_flop_boards']
                  if (b['flop'], b['turn'], b['exact_flop_action']) == (old['flop'], old['turn'], old['line']))
        prior, = (v for v in board['nl2_locked_variants'] if v['sha256'] == old['source_sha256'] and v['run_id'] == old['run'])
        assert prior['subgame_applied_rust_lock_nodes'] == 0 < prior['root_applied_rust_lock_nodes']
        identity = dict(public_board=board['public_board'], line=board['actual_exact_action_line'], acting_seat=board['acting_seat'])
        def lookup(db, run, digest):
            return db[source_key(model['model_id'], dict(identity, source_run_id=run, source_sha256=digest))]
        gr = lookup(gtos, board['source_run_id'], board['source_sha256'])
        er = lookup(locked, prior['run_id'], prior['sha256'])
        assert gr['status'] == er['status'] == 'POSITIVE_JOINT_REACH' and gr['source_actions'] == er['source_actions'] == board['exact_node_actions']
        assert er['root_sha256'] == old['root_sha256']
        assert all(er[k] == v for k,v in exact_observation(old['root'], old['sub'], board, masks).items())
        result.append((model, board))
    return result


def solve_or_replay(args, old, pipeline, pool, out):
    rules, raw_meta = make_fallbacks(old['spot'], old['version'], pool, pipeline.lock_list, old['flop'], by_street=True)
    meta = lock_metadata(raw_meta)
    job = dict(old['job'], locks=json.loads(compact(rules)), rank_pct=.45, target_pct=.45,
               iters=max(2000, old['job']['iters']), out='continuation.json')
    origin = {k:old[k] for k in ('run','id','archive_sha256','source_sha256','root_sha256')}
    path = out/f"NL2_B504_{old['id']}.json.gz"
    if args.replay:
        data = json.loads(gzip.decompress((args.replay/'data/solver_evidence'/path.name).read_bytes()))
        raw = base64.b64decode(data['source_file_b64'], validate=True)
    else:
        work = args.out/f"work-{old['id']}"
        write(work/'job.json', job)
        subprocess.run([str(args.driver.resolve()), 'job.json'], cwd=work, check=True, timeout=360)
        raw = (work/job['out']).read_bytes()
    envelope = dict(schema='NL2_HU_NATIVE_PARENT_STREET_LOCK_V1', solver=SOLVER, rust=RUST, pool_sha256=POOL,
                    run=args.run, original=origin, job=job, locks=meta, source_sha256=sha(raw),
                    conditional_root_sha256=old['root_sha256'],
                    conditional_root_file_b64=base64.b64encode(old['rootraw']).decode(),
                    source_file_b64=base64.b64encode(raw).decode())
    if args.replay:
        assert data == envelope
    packed(path, envelope)
    sub = json.loads(raw)
    assert all(sub[k] == old['sub'][k] for k in ('hands','pot','stack','flop'))
    sub.update(line0=old['line'], turn=old['turn'], rivers=old['sub']['rivers'])
    manifest = dict(spot=old['spot'], pot_family='SRP', locks=meta)
    verified = audit_patterns(sub, job, manifest, pool, hero_seat=job['hero'])
    rates = []
    for pattern, target in verified['marginal_targets'].items():
        actual = sub['info']['lock_stats'].get(pattern)
        if actual and actual['nodes']:
            assert target['street'] in (2,3)
            token = 'r' if target['source'].endswith('bettor_vs_raise') else pattern.split(')?')[-1][:-1]
            rates.append(dict(pattern=pattern, source=target['source'], street=target['street'], token=token, n=target['n'],
                              nodes=actual['nodes'], fold_pct=100*actual['fold'], raise_pct=100*actual['agg'],
                              target_fold_pct=100*target['fold_target'], target_raise_pct=100*target['raise_target']))
    source = dict(version=old['version'], run=args.run, root=old['root'], subgame=sub, manifest=manifest,
                  source_sha256=envelope['source_sha256'], archive_sha256=sha(path.read_bytes()))
    return source, path, rates


def register(out, model, board, old, source, raw_path, rates, observations, masks):
    rank = model['frequency_rank']
    sub = source['subgame']
    target = (board['public_board'], board['actual_exact_action_line'], board['acting_seat'])
    if not any((n['board'], n['line'], n['player']) == target for n in sub['nodes']):
        return dict(rank=rank, public_board=target[0], line=target[1], acting_seat=target[2],
                    run=source['run'], source_sha256=source['source_sha256'], status='EXACT_NODE_UNAVAILABLE')
    reach = exact_observation(source['root'], sub, board, masks)
    scope = lock_scope(sub, source['manifest']['locks'], source['version'])
    stats = sub['info']
    identity = dict(public_board=board['public_board'], line=board['actual_exact_action_line'], acting_seat=board['acting_seat'])
    summary = dict(rank=rank, **identity, run=source['run'], source_sha256=source['source_sha256'],
                   compatible_hole_card_pairs=reach['compatible_hole_card_pairs'], applied_street_rates=rates,
                   gto_gap_pct=stats['gto_expl_pct'], locked_hero_gap_pct=stats['hero_gap_pct'], b50=reach['b50'])
    if not (0 <= stats['gto_expl_pct'] <= .5 and 0 <= stats['hero_gap_pct'] <= .5):
        return dict(summary, status='CONVERGENCE_OUTSIDE_GATE')
    if not reach['compatible_hole_card_pairs']:
        return dict(summary, status='ZERO_JOINT_REACH')
    if {r['street'] for r in rates} != {2,3} or not scope['observed_marginal_source_nodes']:
        return dict(summary, status='MISSING_VERIFIED_TURN_OR_RIVER_LOCK')
    case, _, pairs = source_case(model, source, identity['public_board'], identity['line'], identity['acting_seat'])
    node, = case['nodes']
    assert pairs == reach['compatible_hole_card_pairs'] and node['strictly_reachable_masks_b64'] == reach['compatible_action_mask_b64']
    name = f'B504_R{rank}_NATIVE_STREET_LOCK'
    viewer_sha = packed(out/f'NL2_MULTIBOARD_{name}.json.gz',dict(schema='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1',
                        source_run_id=source['run'], errors=[], no_generic_texture_certification=True, artifacts=[dict(cases=[case])]))
    lock = dict(version=source['version'], run_id=source['run'], sha256=source['source_sha256'], viewer_archive_code=name,
                viewer_sha256=viewer_sha, requires_native_joint_replay=True,
                source_scope='PARTIALLY_LOCKED_NL2_MARGINAL_PROXY', variant_label='原始鎖頻翻牌範圍・轉河分街實測鎖頻',
                measurement_policy='STREET_SPECIFIC_POOL_MARGINALS', pool_sha256=POOL, applied_street_rates=rates,
                hero_model_gain_bb=locked_model_gain(sub,source['version']), true_hero_gap_pct=stats['hero_gap_pct'],
                observed_marginal_source_nodes=scope['observed_marginal_source_nodes'], assumed_default_source_nodes=scope['imputed_assumption_nodes'],
                unknown_history_frequency_filled_with_default=bool(scope['imputed_assumption_nodes']), unlocked_source_nodes=scope['unmatched_nodes'],
                villain_observed_pattern_node_share_pct=scope['coverage_pct'], source_not_real_per_combo_observation=True,
                strictly_reachable_combos=reach['strict_legal_combos'], medium_50pct_eligible_combos=reach['b50']['eligible'],
                b50_nonpolarized_relative_equity_research_candidate=reach['b50']['candidate'])
    overlay = dict(model_id=model['model_id'], flop=old['flop'], turn=old['turn'], **identity, gto_run=board['source_run_id'],
                   gto_sha256=board['source_sha256'], parent_lock_run=old['run'], parent_lock_sha256=old['source_sha256'],
                   original_package=raw_path.name, original_package_sha256=source['archive_sha256'], lock=lock)
    write(out/f'lock_variants/rank{rank}_b504.json', overlay)
    obs = dict(reach, spot=old['spot'], family=model['family'], flop=old['flop'], turn=old['turn'], version=source['version'],
               source_run_id=source['run'], source_sha256=source['source_sha256'], archive_sha256=source['archive_sha256'],
               root_sha256=old['root_sha256'], gto_gap_pct=stats['gto_expl_pct'], locked_hero_gap_pct=stats['hero_gap_pct'], lock_scope=scope,
               root_applied_rust_lock_nodes=sum(r['nodes'] for r in old['root']['info']['lock_stats'].values()),
               subgame_applied_rust_lock_nodes=sum(r['nodes'] for r in stats['lock_stats'].values()))
    observations[source_key(model['model_id'],obs)] = obs
    return dict(summary, status='REGISTERED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals', required=True, type=Path)
    parser.add_argument('--solver', required=True, type=Path)
    parser.add_argument('--run', type=int)
    parser.add_argument('--out', type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--driver', type=Path)
    modes.add_argument('--replay', type=Path)
    args = parser.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',str(solver),'rev-parse','HEAD'],text=True).strip() == SOLVER
    raw_pool = (solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw_pool) == POOL
    pool = json.loads(raw_pool)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges
    if args.driver:
        assert args.driver.resolve() == solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',str(solver/'postflop/postflop-solver'),'rev-parse','HEAD'],text=True).strip() == RUST
    _, locked, gtos, _ = read_replays()
    models = {m['frequency_rank']:m for m in json.loads(REGISTRY.read_bytes())['records'].values()}
    reports, observations = [], {}
    for run, aid, line, turn, ranks in GROUPS:
        old = original(args.originals,run,aid,line,turn,pipeline,ranges)
        selected = targets(old,ranks,models,locked,gtos)
        if args.driver or args.replay:
            assert args.out and args.run > 0
            out = args.out/'data/solver_evidence'
            out.mkdir(parents=True,exist_ok=True)
            source, path, rates = solve_or_replay(args,old,pipeline,pool,out)
            masks = game_reach(old['root'],source['subgame'])[0]
            for model, board in selected:
                reports.append(register(out,model,board,old,source,path,rates,observations,masks))
    if args.driver or args.replay:
        write(args.out/'data/nl2_hu_b504_native_street_locks.json', dict(run=args.run, pool_sha256=POOL, records=reports))
        write(args.out/'data/nl2_hu_b504_locked_medium.json',dict(schema='NL2_HU_B504_ORIGINAL_LOCKED_MEDIUM_V1',references=observations))
        print([(r['rank'],r['status']) for r in reports])


if __name__ == '__main__':
    main()
