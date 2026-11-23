"""Replay one native SB turn with the archived two-seat boundary and measured BB response locks."""
import argparse
import base64
import gzip
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b472_street_lock import POOL
from hu_b480_rank1_street_locks import packed
from hu_b483_locked_medium import proof
from hu_sequential_cfr_reach import cardkey, game_reach
from solve_hu_multiboard_100bb import make_fallbacks
from verify_hu_multiboard_100bb import lock_scope, locked_model_gain, source_nodes

MID = 'ln-opfr-t_model-id38uf'
FLOP, TURN, PUBLIC, LINE = 'As7h3d', 'Kd', '3d7hAsKd', 'x x/'
CODE = 'B494_R5_AS7H3D_STREET_LOCK'
SCOPE = 'PINNED_GTO_FLOP_PARENT_TURN_RIVER_ONLY_MEASURED_BB_RESPONSE_LOCK'
ARCHIVES = {
    'gto': (14628913050, 44736420272, 'b22c76c1e20f29d34096a197d1e50e3a5e03843bfe43554f6bcb02a9890a1aff',
            'af894c256528d482110eea24682467970fdb2d90cafec6de677cfd46a664b0d3', 'cbf9b8d8b508f5272e6a0e39fd7b0526fb3b0285bf0bd77cebbf0932d874566e'),
    'exp_oop': (14643721866, 44765475084, '8c83b39a0669189bd1b9b9f0c3bb7514a95d91ed3623509a4985cf1bccde56c2',
                'fc1a8837152e8afa2901495ae649147d7e0ccd720a7be7b8d2265bd55234b966', '39833178b55b3f268c4a3f9795d2b7cce7acae336b6aea701e940a2393d7326f'),
}


def save(path, value):
    path.write_bytes(compact(value) + b'\n')


def original(directory, version):
    artifact, run, archive_sha, root_sha, sub_sha = ARCHIVES[version]
    meta = json.loads((directory/f'{artifact}.json').read_bytes())
    assert (meta['id'], meta['digest'], meta['workflow_run']['id'], meta['workflow_run']['repository_id']) == (
        artifact, 'sha256:'+archive_sha, run, 1438346845)
    path = directory/f'{artifact}.zip'
    assert sha(path.read_bytes()) == archive_sha
    with zipfile.ZipFile(path) as archive:
        assert {SOLVER, RUST} <= {archive.read(n).decode().strip() for n in archive.namelist() if n.endswith('.txt')}
        mf, = (n for n in archive.namelist() if n.startswith('evidence/') and n.endswith('.json'))
        m = json.loads(archive.read(mf))
        assert (m['schema'], m['spot'], m['version'], m['flop'], m['pot_family']) == (
            'NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1', 'SB_BB', version, FLOP, 'SRP')
        assert not m['failures'] and m['pool_source_sha256'] == POOL
        assert m['preflop_ranges']['source'] == 'PINNED_POKER_SOLVER_PREFLOP_CFR'
        case, = (c for c in m['cases'] if (c['line'], c['turn']) == ('x x', TURN))
        assert (m['file_flop_sha256'], case['source_sha256']) == (root_sha, sub_sha)
        if version == 'exp_oop':
            assert (m['flop_parent_mode'], m['gto_parent_source_sha256'], m['gto_parent_source_run_id']) == (
                'PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK', root_sha, 44763159052)
        root_raw = archive.read('solver/postflop/'+m['file_flop'])
        sub_path = 'solver/postflop/'+case['source_path']
        sub_raw = archive.read(sub_path)
        assert (sha(root_raw), sha(sub_raw)) == (root_sha, sub_sha)
        job = json.loads(archive.read(sub_path.replace('.json', '.job.json')))
    root, sub = json.loads(root_raw), json.loads(sub_raw)
    assert not root['info'].get('lock_stats') and 0 <= root['info']['gto_expl_pct'] <= .5
    assert 0 <= sub['info']['gto_expl_pct'] <= .5
    assert (sub['flop'], sub['turn'], sub['line0'], sub['pot'], sub['stack']) == (FLOP, TURN, 'x x', 600, 9700)
    assert (job['flop'], job['turn'], job['line0'], job['pot'], job['stack'], job['rake_rate'], job['rake_cap']) == (
        FLOP, TURN, ['x', 'x', '/'], 600, 9700, .05, 1000)
    assert job.get('hero') == (None if version == 'gto' else 0) and bool(job.get('locks')) == (version == 'exp_oop')
    parent, = (n for n in root['nodes'] if (n['line'], n['board']) == (LINE, PUBLIC))
    assert parent['pot'] == job['pot'] and root['stack']-max(parent['bets']) == job['stack']
    for seat, key in enumerate(('oop_w', 'ip_w')):
        assert job[key] == [[h,w] for h,w in zip(root['hands'][seat], parent['wr'][seat], strict=True) if w > 1e-4]
    return dict(root=root, sub=sub, job=job, root_raw=root_raw, locks=m['locks'])


def decision(root, sub):
    node, = (n for n in sub['nodes'] if (n['board'], n['line'], n['player']) == (PUBLIC, LINE, 0))
    assert node['pot'] == 600 and node['bets'] == [0, 0]
    obs = proof(root, sub, node, game_reach(root, sub)[0])
    mask = base64.b64decode(obs['compatible_action_mask_b64'], validate=True)
    hands = {cardkey(h) for h,b in zip(sub['hands'][0], mask, strict=True) if b}
    assert len(hands) == obs['strict_legal_combos']
    return node, obs, hands


def native_job(gto, prior, pool, pipeline):
    native, old = gto['job'], prior['job']
    # The two authenticated original jobs reach identical weighted cards. Only print/extract paths,
    # turn sizing and exploit settings differed before this solve.
    different = {k for k in set(native)|set(old) if native.get(k) != old.get(k)}
    assert different == {'out','extract','turn_oop','turn_ip','hero','locks','rank_pct'}
    assert native['turn_oop'] == native['turn_ip'] == '50%,100%' and old['turn_oop'] == old['turn_ip'] == '66%'
    rules, meta = make_fallbacks('SB_BB', 'exp_oop', pool, pipeline.lock_list, FLOP, by_street=True)
    job = dict(native, hero=0, locks=rules, rank_pct=.45, target_pct=.45, iters=max(2000,native['iters']), out='fresh.json')
    locks = [dict(pat=r['pat'], source=r['src'], scope=r.get('scope','PINNED_MEASURED_NL2_SOURCE'),
                  n=r.get('n'), **({'street':r['street']} if 'street' in r else {})) for r in meta]
    return job, locks


def export(directory, run, gto, prior, job, locks, pool, raw):
    sub = json.loads(raw)
    assert (sub['hands'], sub['flop'], sub['pot'], sub['stack']) == (
        prior['sub']['hands'], FLOP, job['pot'], job['stack'])
    sub.update(turn=TURN, line0='x x', rivers=gto['sub']['rivers'])
    g, gproof, gh = decision(gto['root'], gto['sub'])
    old, oldproof, oh = decision(prior['root'], prior['sub'])
    n, reach, hands = decision(prior['root'], sub)
    assert old['acts'] == ['x','b66'] and n['acts'] == g['acts'] == ['x','b50','b100'] and gh and oh
    for s in (gto['sub'], sub):
        child, = (a for a in s['nodes'] if (a['line'],a['board'],a['player']) == (LINE+'b50',PUBLIC,1))
        assert child['pot'] == 900 and child['bets'] == [300,0]
    source_sha = sha(raw)
    summary = dict(model_id=MID, public_board=PUBLIC, acting_seat=0, line=LINE, run_id=run,
                   gto_run=ARCHIVES['gto'][1], gto_sha256=ARCHIVES['gto'][4], parent_lock_run=ARCHIVES['exp_oop'][1],
                   parent_lock_sha256=ARCHIVES['exp_oop'][4], condition=SCOPE, source_sha256=source_sha,
                   root_applied_rust_lock_nodes=sum(r['nodes'] for r in prior['root']['info'].get('lock_stats', {}).values()),
                   subgame_applied_rust_lock_nodes=sum(r['nodes'] for r in sub['info']['lock_stats'].values()),
                   GTO_compatible_hole_card_pairs=gproof['compatible_hole_card_pairs'],
                   prior_NL2_compatible_hole_card_pairs=oldproof['compatible_hole_card_pairs'],
                   NL2_compatible_hole_card_pairs=reach['compatible_hole_card_pairs'],
                   reach_comparison=dict(GTO_strict_combos=len(gh), prior_NL2_strict_combos=len(oh), NL2_strict_combos=len(hands),
                                         common_legal_hero_combos=len(gh & hands),prior_and_new_common_combos=len(oh & hands)),
                   gto_gap_pct=sub['info']['gto_expl_pct'], locked_hero_gap_pct=sub['info']['hero_gap_pct'])
    path = directory/'data/solver_evidence'
    path.mkdir(parents=True,exist_ok=True)
    original_file = path/f'NL2_{CODE}.json.gz'
    archive_sha = packed(original_file,dict(schema='NL2_B494_RANK5_CONDITIONAL_SOURCE_V1',run=run,job=job,locks=locks,
                                            pool_sha256=POOL, original_sources=ARCHIVES, scope=SCOPE, source_sha256=source_sha,
                                            gto_parent_run_id=44763159052, conditional_root_sha256=ARCHIVES['exp_oop'][3],
                                            conditional_root_file_b64=base64.b64encode(prior['root_raw']).decode(),
                                            source_file_b64=base64.b64encode(raw).decode()))
    stats = sub['info']['lock_stats']
    applied = audit_patterns(sub, job, {'locks':locks}, pool, hero_seat=0)
    scope = lock_scope(sub, locks, 'exp_oop')
    rates = []
    for pat, target in applied['marginal_targets'].items():
        if pat not in stats: continue
        actual = stats[pat]
        assert actual['nodes'] > 0 and target['street'] in (2,3)
        rates.append(dict(pattern=pat, street=target['street'], token=pat.split(')?')[-1][:-1], n=target['n'],
                          fold_pct=100*actual['fold'],raise_pct=100*actual['agg'], nodes=actual['nodes'],
                          target_fold_pct=100*target['fold_target'], target_raise_pct=100*target['raise_target']))
    qualified = bool(hands and rates and scope['observed_marginal_source_nodes'] and
                     0 <= summary['gto_gap_pct'] <= .5 and 0 <= summary['locked_hero_gap_pct'] <= .5)
    summary.update(status='REGISTERED' if qualified else 'WITHHELD', archive_sha256=archive_sha,
                   archive=original_file.name, applied_street_rates=rates,lock_scope=scope, b50=reach['b50'])
    save(path.parent/'nl2_hu_b494_rank5_attempt.json', summary)
    if not qualified:
        return
    strict = dict(mask=reach['compatible_action_mask_b64'], count=len(hands),
                  compatible_hole_card_pairs=reach['compatible_hole_card_pairs'])
    node, = source_nodes(dict(sub,nodes=[n]), {'nodes':{f'{PUBLIC}|{LINE}|0':strict}})
    assert node['medium_50pct_strict_evidence'] == reach['b50']
    case = dict(run_id=run, version='exp_oop', spot='SB_BB',pot_family='SRP',flop=FLOP,turn=TURN,flop_line='x x',
                source_sha256=source_sha,hands_by_seat=sub['hands'], nodes=[node],gto_exploitability_pct=summary['gto_gap_pct'],
                locked_hero_gap_pct=summary['locked_hero_gap_pct'],villain_lock_scope=scope)
    viewer_sha = packed(path/f'NL2_MULTIBOARD_{CODE}.json.gz',dict(schema='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1',
        source_run_id=run,no_generic_texture_certification=True,errors=[],artifacts=[dict(cases=[case])]))
    lock = dict(version='exp_oop',run_id=run,sha256=source_sha,viewer_archive_code=CODE,viewer_sha256=viewer_sha,
                requires_native_joint_replay=True,
                source_scope='PARTIALLY_LOCKED_NL2_MARGINAL_PROXY', conditioning=SCOPE,variant_label='GTO 翻牌範圍・轉河分街實測鎖頻',
                pool_sha256=POOL,measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates,
                hero_model_gain_bb=locked_model_gain(sub,'exp_oop'),true_hero_gap_pct=summary['locked_hero_gap_pct'],
                observed_marginal_source_nodes=scope['observed_marginal_source_nodes'],assumed_default_source_nodes=scope['imputed_assumption_nodes'],
                unlocked_source_nodes=scope['unmatched_nodes'],villain_observed_pattern_node_share_pct=scope['coverage_pct'],
                unknown_history_frequency_filled_with_default=bool(scope['imputed_assumption_nodes']),source_not_real_per_combo_observation=True,
                strictly_reachable_combos=len(hands), medium_50pct_eligible_combos=reach['b50']['eligible'],
                b50_nonpolarized_relative_equity_research_candidate=reach['b50']['candidate'],reach_comparison=summary['reach_comparison'])
    overlay = {k:summary[k] for k in ('model_id','public_board','acting_seat','line','gto_run','gto_sha256','parent_lock_run','parent_lock_sha256')}
    overlay.update(flop=FLOP,turn=TURN,original_package=original_file.name,original_package_sha256=archive_sha,lock=lock)
    (path/'lock_variants').mkdir(exist_ok=True)
    save(path/'lock_variants/rank5_b494_As7h3d.json', overlay)
    obs = dict(reach, spot='SB_BB',family='SRP',flop=FLOP,turn=TURN,version='exp_oop',source_run_id=run,source_sha256=source_sha,
               archive_sha256=archive_sha,lock_scope=scope,gto_gap_pct=summary['gto_gap_pct'],locked_hero_gap_pct=summary['locked_hero_gap_pct'],
               root_applied_rust_lock_nodes=summary['root_applied_rust_lock_nodes'],
               subgame_applied_rust_lock_nodes=summary['subgame_applied_rust_lock_nodes'])
    save(path.parent/'nl2_hu_b494_locked_medium.json', dict(schema='NL2_HU_B494_ORIGINAL_LOCKED_MEDIUM_V1',
         references={compact([MID,PUBLIC,LINE,0,run,source_sha]).decode():obs}))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--originals',type=Path,required=True)
    cli.add_argument('--solver',type=Path,required=True)
    cli.add_argument('--driver',type=Path)
    cli.add_argument('--replay',type=Path)
    cli.add_argument('--out',type=Path)
    cli.add_argument('--run',type=int)
    args = cli.parse_args()
    solver = args.solver.resolve()
    raw_pool = (solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw_pool) == POOL
    pool = json.loads(raw_pool)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    model = json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MID]
    assert model['label'] == 'CERT-MULTIBOARD' and model['frequency_rank'] == 5
    board, = (b for b in model['certified_3_to_5_exact_flop_boards'] if b['public_board'] == PUBLIC)
    assert (board['source_run_id'],board['source_sha256'],board['actual_exact_action_line'],board['acting_seat']) == (
        ARCHIVES['gto'][1],ARCHIVES['gto'][4],LINE,0)
    assert any((l['run_id'],l['sha256'],l['version'])==(ARCHIVES['exp_oop'][1],ARCHIVES['exp_oop'][4],'exp_oop') for l in board['nl2_locked_variants'])
    gto, prior = [original(args.originals, version) for version in ('gto','exp_oop')]
    job, locks = native_job(gto, prior, pool, pipeline)
    if not (args.driver or args.replay):
        for source, menu in ((gto,['x','b50','b100']), (prior,['x','b66'])):
            n,r,h = decision(source['root'],source['sub'])
            assert n['acts'] == menu and h and r['compatible_hole_card_pairs']
        return
    assert args.out and args.run > 0 and not (args.driver and args.replay)
    args.out.mkdir(parents=True,exist_ok=True)
    if args.replay:
        src=json.loads(gzip.decompress(args.replay.read_bytes()))
        assert src['run']==args.run and src['job']==job and src['locks']==locks and src['pool_sha256']==POOL
        raw=base64.b64decode(src['source_file_b64'],validate=True)
        assert sha(raw)==src['source_sha256']
    else:
        save(args.out/'conditional.job.json',job)
        subprocess.run([str(args.driver.resolve()),'conditional.job.json'],cwd=args.out,check=True,timeout=360)
        raw=(args.out/job['out']).read_bytes()
    export(args.out,args.run,gto,prior,job,locks,pool,raw)


if __name__ == '__main__':
    main()
