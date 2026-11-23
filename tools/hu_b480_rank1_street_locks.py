"""Re-solve three exact BB turn decisions with street-specific NL2 opponent marginals."""
import argparse
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

from hu_b472_street_lock import MODEL, PIN, POOL, RUST, measured, read, save, sha
from hu_sequential_cfr_reach import cardkey, compatible_node_reach, game_reach
from solve_hu_multiboard_100bb import marginal_pattern
from verify_hu_multiboard_100bb import locked_model_gain, lock_scope, source_nodes

CASES = {
    '2s4h6d': (44769773770, (14646892297,'54f16c00656c2235f13bf219e76d2c8635fb9591eaaf11e6ac9c977bee656023'),
              (14648420706,'ae91b233a12aa4cb45a02b563d8a024f111bf85fd1d8dc24b36ed9c61fb71495')),
    '7s5h3d': (44769773770, (14648360341,'aa1a858743cc1904a7f92a7cb2c4d4102e9faf760bdd4fbd89d482268ad27897'),
              (14645529508,'dd0c4c8a8d4748b7c7917f31df6655bf0e8b35d7bad12e5f526bf9be16da06e2')),
    '8s8h3d': (44767785255, (14643774933,'a8ab800f0289e0ffeacf7aaf823ff12abbab372cfa732af29f113a7123b04d65'),
              (14644844459,'8b0ec777464c3715aafa1c85395930ece9171f17c2c60e850fc6c0600cf950f8')),
}
EVIDENCE = Path('data/solver_evidence')
LINE = 'b50 c/'


def packed(path, data):
    raw = json.dumps(data, ensure_ascii=False, separators=(',',':')).encode()
    compressed = gzip.compress(raw, mtime=0)
    path.write_bytes(compressed[:9]+bytes([255])+compressed[10:])
    return sha(path)


def original(downloads, artifact, board, version):
    artifact_id, zip_digest = artifact
    folder = downloads/str(artifact_id)
    assert sha(folder.with_suffix('.zip')) == zip_digest
    evidence = folder/'evidence'
    assert (evidence/'poker-solver-pin.txt').read_text().strip()==PIN
    assert (evidence/'rust-pin.txt').read_text().strip()==RUST
    flop,turn = board['flop'],board['turn']
    manifest_file=evidence/f'LMP_CO_BB-{flop}-{version}.json'
    m=read(manifest_file)
    assert (m['spot'],m['version'],m['flop'],m['pot_family'])==('LMP_CO_BB',version,flop,'LMP')
    assert m['pool_source_sha256']==POOL and m['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
    assert not m['failures'] and m['flop_action_sizes']==['50%']
    case,=(c for c in m['cases'] if (c['line'],c['turn'])==('b50 c',turn))
    pf = folder/'solver/postflop'
    root=read(pf/m['file_flop'],m['file_flop_sha256'])
    source=pf/case['source_path']
    sub=read(source,case['source_sha256'])
    job_path=source.with_suffix('.job.json')
    job=read(job_path)
    expected=board['source_sha256'] if version=='gto' else next(v['sha256'] for v in board['nl2_locked_variants']
        if (v['run_id'],v['version'])==(board['source_run_id'],'exp_oop'))
    assert expected==case['source_sha256']
    assert (root['pot'],root['stack'],root['flop'])==(250,9900,flop)
    assert (sub['pot'],sub['stack'],sub['flop'],sub['turn'],sub['line0'])==(500,9775,flop,turn,'b50 c')
    assert (job['pot'],job['stack'],job['turn'],job['line0'],job['rake_rate'],job['rake_cap'])==(500,9775,turn,['b50','c','/'],.05,1000)
    assert job.get('hero')==(0 if version=='exp_oop' else None) and bool(job.get('locks'))==(version=='exp_oop')
    for game in (root,sub):
        assert 0<=game['info']['gto_expl_pct']<=.5
        if version=='exp_oop':
            assert 0<=game['info']['hero_gap_pct']<=.5
    origin=dict(artifact_id=artifact_id,archive_sha256=zip_digest,manifest_sha256=sha(manifest_file),
                root_sha256=m['file_flop_sha256'],source_sha256=expected,job_sha256=sha(job_path))
    return root,sub,job,m,origin


def decision(root, sub, board):
    n,=(n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(board['public_board'],LINE,0))
    key=f"{n['board']}|{LINE}|0"
    strict=compatible_node_reach(root,sub,n,game_reach(root,sub)[0][key])
    assert (n['pot']/100,(sub['stack']-max(n['bets']))/100)==(board['actual_pot_bb'],board['actual_effective_stack_bb'])
    mask=base64.b64decode(strict['mask'],validate=True)
    assert len(mask)==len(sub['hands'][0])
    hands={cardkey(h) for h,b in zip(sub['hands'][0],mask) if b}
    assert len(hands)==strict['count']
    nodes=source_nodes(dict(sub,nodes=[n]),{'nodes':{key:strict}})
    assert len(nodes)==bool(hands)==bool(strict['compatible_hole_card_pairs'])
    return nodes[0] if nodes else None,hands,strict['compatible_hole_card_pairs']


def correction(job, metadata, pool):
    job,metadata=copy.deepcopy(job),copy.deepcopy(metadata)
    expected=[]
    for lock,rule in zip(job['locks'],metadata,strict=True):
        assert lock['pat']==rule['pat']
        found=measured(rule['source'],pool)
        if found is None:
            continue
        street,token,rate=found
        assert lock['pat']==marginal_pattern(street,token,False)
        assert rule['n']==rate['n']>=500
        assert abs(100*lock['fold']-rate['fold'])<1e-6 and abs(100*lock['raise']-rate['raise'])<1e-6
        pattern=marginal_pattern(street,token,True)
        lock['pat']=rule['pat']=pattern
        expected.append(dict(street=street,token=token,pattern=pattern,n=rate['n'],fold=rate['fold'],call=rate['call'],raise_pct=rate['raise']))
    assert len(expected)==len({r['pattern'] for r in expected})
    return job,metadata,expected


def achieved_rates(raw, expected):
    stats=raw['info']['lock_stats']
    rows=[]
    for rate in expected:
        actual=stats.get(rate['pattern'])
        if actual is None:
            continue
        assert rate['street'] in (2,3) and actual['nodes']>0
        fold,raise_pct=100*actual['fold'],100*actual['agg']
        assert abs(fold-rate['fold'])<.2 and abs(raise_pct-rate['raise_pct'])<.2
        rows.append(dict(street=rate['street'],token=rate['token'],n=rate['n'],fold_pct=round(fold,3),
                         raise_pct=round(raise_pct,3),nodes=actual['nodes']))
    assert {(r['street'],r['token']) for r in rows}=={(s,t) for s in (2,3) for t in ('b50','b100')}
    return rows


def export(out_dir, board, run, sources, job, metadata, targets, original_output):
    groot,gsub,_,_,g_origin=sources[0]
    eroot,old,_,_,e_origin=sources[1]
    raw=json.loads(original_output)
    assert raw['hands']==old['hands'] and (raw['flop'],raw['pot'],raw['stack'])==(old['flop'],old['pot'],old['stack'])
    assert 0<=raw['info']['hero_gap_pct']<=job['target_pct']==.5 and 0<=raw['info']['gto_expl_pct']<=.5
    new=dict(raw,line0=old['line0'],turn=old['turn'],rivers=old['rivers'])
    g,gh,gpairs=decision(groot,gsub,board)
    _,eh,epairs=decision(eroot,old,board)
    node,nh,npairs=decision(eroot,new,board)
    achieved=achieved_rates(raw,targets)
    scope=lock_scope(new,metadata,'exp_oop')
    assert scope['observed_marginal_source_nodes']>0
    source_sha=hashlib.sha256(original_output).hexdigest()
    flop,turn,public=board['flop'],board['turn'],board['public_board']
    path=out_dir/'data/solver_evidence'
    path.mkdir(parents=True,exist_ok=True)
    code='B480_R1_'+flop.upper()+'_STREET_LOCK'
    pack_file=path/f'NL2_{code}.json.gz'
    pack_hash=packed(pack_file,dict(schema='NL2_B480_RANK1_ORIGINAL_STREET_LOCK_V1',run=run,flop=flop,turn=turn,
                     job=job,source_sha256=source_sha,source_file_b64=base64.b64encode(original_output).decode(),
                     original_gto=g_origin,original_exp=e_origin,pool_sha256=POOL,measured_targets=targets))
    comparison=dict(GTO_strict_combos=len(gh),prior_NL2_strict_combos=len(eh),NL2_strict_combos=len(nh),
                    common_legal_hero_combos=len(gh&nh),prior_and_new_common_combos=len(eh&nh))
    report=dict(model_id=MODEL,flop=flop,turn=turn,public_board=public,line=LINE,acting_seat=0,run=run,
                prior_run=board['source_run_id'],source_sha256=source_sha,archive_sha256=pack_hash,original_package=pack_file.name,
                GTO_compatible_hole_card_pairs=gpairs,prior_NL2_compatible_hole_card_pairs=epairs,
                NL2_compatible_hole_card_pairs=npairs,reach_comparison=comparison,achieved=achieved,
                pool_sha256=POOL,lock_scope=scope,gto_expl_pct=raw['info']['gto_expl_pct'],hero_gap_pct=raw['info']['hero_gap_pct'],
                measured_lock_registered=bool(g and node),fresh_medium50_evidence=node['medium_50pct_strict_evidence'] if node else None)
    save(out_dir/'data'/f'nl2_hu_b480_rank1_{flop}.json',report)
    if not report['measured_lock_registered']:
        return report
    case=dict(run_id=run,version='exp_oop',source_sha256=source_sha,spot='LMP_CO_BB',pot_family='LMP',flop=flop,turn=turn,
              flop_line=new['line0'],hands_by_seat=new['hands'],nodes=[node],gto_exploitability_pct=report['gto_expl_pct'],
              locked_hero_gap_pct=report['hero_gap_pct'],villain_lock_scope=scope)
    view=dict(schema='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1',source_run_id=run,
              no_generic_texture_certification=True,errors=[],artifacts=[dict(cases=[case])])
    view_hash=packed(path/f'NL2_MULTIBOARD_{code}.json.gz',view)
    lock=dict(version='exp_oop',run_id=run,sha256=source_sha,source_scope='PARTIALLY_LOCKED_NL2_MARGINAL_PROXY',
              viewer_archive_code=code,viewer_sha256=view_hash,pool_sha256=POOL,variant_label='分街實測池鎖頻',
              measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',observed_marginal_source_nodes=scope['observed_marginal_source_nodes'],
              assumed_default_source_nodes=scope['imputed_assumption_nodes'],unlocked_source_nodes=scope['unmatched_nodes'],
              villain_observed_pattern_node_share_pct=scope['coverage_pct'],unknown_history_frequency_filled_with_default=scope['imputed_assumption_nodes']>0,
              source_not_real_per_combo_observation=True,hero_model_gain_bb=locked_model_gain(new,'exp_oop'),true_hero_gap_pct=report['hero_gap_pct'],
              strictly_reachable_combos=len(nh),medium_50pct_eligible_combos=node['medium_50pct_eligible_combos'],
              b50_nonpolarized_relative_equity_research_candidate=node['b50_nonpolarized_relative_equity_research_candidate'],
              reach_comparison=comparison,applied_street_rates=achieved)
    overlay=dict(model_id=MODEL,flop=flop,turn=turn,public_board=public,line=LINE,acting_seat=0,gto_run=board['source_run_id'],
                gto_sha256=g_origin['source_sha256'],parent_lock_run=board['source_run_id'],parent_lock_sha256=e_origin['source_sha256'],
                original_package=pack_file.name,original_package_sha256=pack_hash,lock=lock)
    (path/'lock_variants').mkdir(exist_ok=True)
    save(path/'lock_variants'/f'rank1_b480_{flop}.json',overlay)
    return report


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--flop',choices=CASES,required=True)
    cli.add_argument('--list-artifacts',action='store_true')
    cli.add_argument('--downloads',type=Path)
    cli.add_argument('--pool',type=Path)
    cli.add_argument('--driver',type=Path)
    cli.add_argument('--replay',type=Path,help='Verified original output package from the fresh solve')
    cli.add_argument('--out-dir',type=Path)
    cli.add_argument('--run',type=int)
    args=cli.parse_args()
    old_run,ga,ea=CASES[args.flop]
    if args.list_artifacts:
        print(ga[0],ea[0]); return
    record=read(Path('data/nl2_hu_multiboard_status_current.json'))['records'][MODEL]
    assert record['frequency_rank']==1 and record['label']=='CERT-MULTIBOARD'
    board,=(b for b in record['certified_3_to_5_exact_flop_boards'] if b['flop']==args.flop)
    assert board['assumed_preflop_ranges'] and (board['source_run_id'],board['acting_seat'],board['actual_exact_action_line'])==(old_run,0,LINE)
    assert board['actual_spr']==19.55
    sources=[original(args.downloads,a,board,v) for a,v in [(ga,'gto'),(ea,'exp_oop')]]
    root,old,job,m,e_origin=sources[1]
    job,metadata,targets=correction(job,m['locks'],read(args.pool,POOL))
    if args.driver is None and args.replay is None:
        print(args.flop,'GTO / original NL2 compatible deals:',decision(sources[0][0],sources[0][1],board)[2],decision(root,old,board)[2])
        return
    assert args.run>0 and args.out_dir and not (args.replay and args.driver)
    # Keep the original job and all range/size controls except the measured lock patterns.
    job['out']='street-lock-output.json'
    if args.replay:
        pack=json.loads(gzip.decompress(args.replay.read_bytes()))
        assert (pack['run'],pack['flop'],pack['job'],pack['pool_sha256'])==(args.run,args.flop,job,POOL)
        output=base64.b64decode(pack['source_file_b64'],validate=True)
        assert pack['source_sha256']==hashlib.sha256(output).hexdigest()
    else:
        work=args.out_dir/'job'
        work.mkdir(parents=True,exist_ok=True)
        save(work/'street-lock.job.json',job)
        subprocess.run([str(args.driver.resolve()),'street-lock.job.json'],cwd=work,check=True)
        output=(work/job['out']).read_bytes()
    result=export(args.out_dir,board,args.run,sources,job,metadata,targets,output)
    print(args.flop,result['reach_comparison'],result['measured_lock_registered'])


if __name__=='__main__':
    main()
