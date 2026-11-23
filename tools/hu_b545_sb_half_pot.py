"""Replay exact SB half-pot flop sources and conditional BB response policies."""
import argparse
import base64
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import original, audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b492_half_pot_leads import zip_payload
from hu_b522_sb_double_barrel import TARGETS
from hu_b527_checked_barrels import witnesses
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, game_reach, compatible_node_reach
from verify_hu_multiboard_100bb import lock_scope

CASES = {
    'Ks8d3c': (33, '9d', ['4h','6s']), 'Kc7h2d': (33, '9d', ['Ac','8c']),
    'Kc6h2s': (33, '9d', ['4d','Jh']), 'Qs7c4h': (33, '2s', ['4s','Th']), '7h7d2s': (75, '6d', ['9c','Jh']),
    '8s8d3h': (75, 'Ts', ['6c','Kh']), '6c6d3s': (75, '7s', ['2h','4d']),
    'TdTs4h': (75, '5d', ['9s','Js']),
}
MENU = '33%,50%,75%,100%'


def parent_entries(solver, flop, manifest_path):
    manifest = json.loads(manifest_path.read_bytes())
    evidence = 'trainer/evidence/'
    entries = {evidence+flop+'-gto.json':manifest_path.read_bytes(),
               evidence+'pool_stats.json':(solver/'inputs/pool_stats.json').read_bytes(),
               evidence+'poker-solver-pin.txt':SOLVER.encode(),evidence+'rust-pin.txt':RUST.encode()}
    paths = [manifest['file_flop']] + [c['source_path'] for c in manifest['cases']]
    for path in paths:
        for name in (Path(path),Path(path).with_suffix('.job.json')):
            entries['solver/postflop/'+name.as_posix()] = (solver/'postflop'/name).read_bytes()
    return entries


def load_parent(directory, flop):
    pct,turn,rivers=CASES[flop]
    g=original(directory,flop,turn,'gto',batch='B545',spot='SB_BB',flop_line='b50 c',
               flop_policy='oop-b50only',root_pot=600,root_stack=9700,flop_profile='sb-50-only',
               turn_policy='default',turn_extracts=['b33 c','b50 c','b75 c','b100 c'],turn_mode='33-50-75-100',turn_menu=MENU)
    root=g['root']
    assert sha(compact(root))==g['root_sha256']
    assert (g['manifest']['solver_pin'],g['manifest']['solver_ranges_sha256'])==(PIPELINE,RANGES)
    if g['subgame'] is None:
        return g
    sub,job=g['subgame'],g['subgame_job']
    assert (sub['pot'],sub['stack'],sub['rivers'])==(1200,9400,rivers)
    assert job['river_oop']==job['river_ip']=='50%,100%,a'
    assert not job['root_no_bet'] and job['line0']==['b50','c','/']
    parent,=(n for n in root['nodes'] if n['line']=='b50 c/' and n['board'].endswith(turn))
    assert (parent['bets'],parent['pot'])==([300,300],1200)
    for seat,key in enumerate(('oop_w','ip_w')):
        assert job[key]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    return g


def river_rows(s, pct, route):
    sub,root=s['subgame'],s['root']
    results={}
    masks=game_reach(root,sub)[0]
    line=f'b50 c/b{pct} c/'
    for n in sub['nodes']:
        if n['line']!=line:
            continue
        assert n['player']==0 and len(n['board'])==10 and 'b50' in n['acts']
        bet=(1200*pct+50)//100
        assert n['bets']==[bet,bet] and n['pot']==1200+2*bet
        parent,=(p for p in sub['nodes'] if p['board']==n['board'][:8] and p['line']==f'b50 c/b{pct}')
        assert (parent['pot'],parent['bets'],parent['player'])==(1200+bet,[bet,0],1)
        response,=(c for c in sub['nodes'] if c['board']==n['board'] and c['line']==line+'b50')
        half=(n['pot']+1)//2
        assert (response['pot'],response['bets'],response['player'])==(n['pot']+half,[bet+half,bet],1)
        row=proof(root,sub,n,masks)
        mask=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
        hands={cardkey(h) for h,allowed in zip(sub['hands'][0],mask,strict=True) if allowed}
        assert len(hands)==row['strict_legal_combos']
        results[n['board']]=(row,set(witnesses(hands,n['board'],route)))
    return results


def native_job(g,pool,pipeline,variant):
    job,locks=prepare_job(dict(source=g,job=g['subgame_job']),'exp_oop',pool,pipeline)
    if variant=='history':
        pct=CASES[g['root']['flop']][0]
        bucket={33:'≤33%',75:'56-80%'}[pct]
        measured=pool['postflop_HU']['SRP_PFR_OOP']['vs_turn_barrel_by_size'][bucket]
        assert measured['n']>=500
        pattern=f'^b50 c/b{pct}$'
        job['locks'].insert(0,dict(pat=pattern,fold=measured['fold']/100,**{'raise':measured['raise']/100}))
        locks.insert(0,dict(pat=pattern,source=f'SRP_PFR_OOP.vs_turn_barrel_by_size[{bucket}]',
                            scope='PINNED_MEASURED_NL2_SOURCE',n=measured['n']))
    return job,locks


def lock_source(g, entries, pool, pipeline, variant):
    job,locks=native_job(g,pool,pipeline,variant)
    assert entries[variant+'/job.json']==compact(job) and entries[variant+'/locks.json']==compact(locks)
    raw=entries[variant+'/output.json']; sub=json.loads(raw)
    assert job['hero']==0 and job['oop_w']==g['subgame_job']['oop_w'] and job['ip_w']==g['subgame_job']['ip_w']
    assert all(sub[k]==g['subgame'][k] for k in ('hands','flop','stack','pot'))
    sub.update({k:g['subgame'][k] for k in ('turn','rivers','line0')})
    roots=[n['board'] for n in g['subgame']['nodes'] if n['line']=='b50 c/']
    assert len(roots)==1 and all(n['board'][:8]==roots[0] for n in sub['nodes'])
    manifest=dict(g['manifest'],version='exp_oop',locks=locks,flop_parent_mode='FROZEN_GTO_FLOP',
                  gto_parent_source_sha256=g['root_sha256'])
    audit_patterns(sub,job,manifest,pool,hero_seat=0)
    return dict(root=g['root'],root_sha256=g['root_sha256'],subgame=sub,source_sha256=sha(raw),manifest=manifest,version='exp_oop')


def first_rates(e, pool, public, pct):
    root,sub=e['root'],e['subgame']
    acts={f'b50 c/b{pct}':2,f'b50 c/b{pct} c/b50':3}
    rates=[]
    masks=game_reach(root,sub)[0]
    for n in sub['nodes']:
        street=acts.get(n['line'])
        if street is None or n['board']!=public[:4+street*2]:
            continue
        assert n['player']==1 and len(n['acts'])>=2
        reach=compatible_node_reach(root,sub,n,masks['|'.join((n['board'],n['line'],'1'))])
        if not reach['compatible_hole_card_pairs']:
            continue
        r=next(x for x in e['manifest']['locks'] if re.search(x['pat'],n['line']))
        stats=sub['info']['lock_stats'][r['pat']]
        assert stats['nodes']>0
        token='b'+str(pct) if street==2 else 'b50'
        bucket={'b33':'≤33%','b50':'34-55%','b75':'56-80%'}[token]
        if r['scope']=='PINNED_MEASURED_NL2_SOURCE':
            metric='vs_'+('turn' if street==2 else 'river')+'_barrel_by_size'
            assert r['source']==f'SRP_PFR_OOP.{metric}[{bucket}]'
            observed=pool['postflop_HU']['SRP_PFR_OOP'][metric][bucket]
        else:
            assert r['scope']=='IMPUTED_HISTORY_FROM_TRUE_STREET_BY_SIZE_MARGINAL' and r['street']==street
            assert r['source']==f'NL2.HU_facing_bet[{street}].by_size[{bucket}]'
            observed=pool['HU_facing_bet'][str(street)]['by_size'][bucket]
        assert r['n']==observed['n']>=500
        rates.append(dict(street=street,token=token,opportunity='FACING_BET',line=n['line'],pattern=r['pat'],
                          scope=r['scope'],source=r['source'],n=r['n'],nodes=stats['nodes'],
                          compatible_hole_card_pairs=reach['compatible_hole_card_pairs'],
                          target_fold_pct=observed['fold'],target_raise_pct=observed['raise'],
                          fold_pct=100*stats['fold'],raise_pct=100*stats['agg']))
    return rates


def assess(flop, g, entries, route, pool, pipeline, solve_dir=None, driver=None):
    """The local replay has no Actions run identity until the raw input is uploaded and audited."""
    pct,turn,rivers=CASES[flop]
    result=dict(flop=flop,turn=turn,root_sha256=g['root_sha256'],gto_sha256=g['source_sha256'],rivers={})
    if g['subgame'] is None:
        return result|dict(status='NO_GTO_SUBGAME'),None
    if any(not 0<=g[stage]['info']['gto_expl_pct']<=.5 for stage in ('root','subgame')):
        return result|dict(status='OUTSIDE_GTO_CONVERGENCE'),None
    grows=river_rows(g,pct,route)
    result['gto_route_witnesses']={b:sorted(hands) for b,(_,hands) in grows.items()}
    result['gto_compatible_deals']={b:row['compatible_hole_card_pairs'] for b,(row,_) in grows.items()}
    if not any(hands for _,hands in grows.values()):
        assert not any(k in entries for k in ('native/output.json','history/output.json'))
        return result|dict(status='NO_GTO_RENDERED_ROUTE_HAND'),None
    if driver:
        assert 'history/output.json' not in entries
        job,locks=native_job(g,pool,pipeline,'history')
        jobdata=compact(job)
        (solve_dir/'native.job.json').write_bytes(jobdata)
        subprocess.run([driver,'native.job.json'],cwd=solve_dir,check=True,timeout=360)
        entries.update({'history/job.json':jobdata,'history/locks.json':compact(locks),'history/output.json':(solve_dir/'native.json').read_bytes()})
    variants={}
    selected=None
    for variant in ('history','native'):
        if variant+'/output.json' not in entries:
            continue
        e=lock_source(g,entries,pool,pipeline,variant)
        entry,pair=assess_locked(flop,g,e,grows,route,pool)
        variants[variant]=entry
        if selected is None and pair:
            selected=(variant,pair)
    assert variants
    variant,pair=selected or (next(iter(variants)),None)
    return result|variants[variant]|dict(selected_lock_variant=variant,verified_lock_variants=variants),pair


def assess_locked(flop,g,e,grows,route,pool):
    pct,turn,rivers=CASES[flop]
    result=dict(locked_sha256=e['source_sha256'],rivers={})
    if any(not 0<=e['subgame']['info'][k]<=.5 for k in ('gto_expl_pct','hero_gap_pct')):
        return result|dict(status='OUTSIDE_LOCK_CONVERGENCE'),None
    erows=river_rows(e,pct,route)
    for river in rivers:
        pub=next((b for b in grows if b.endswith(river)),None)
        if pub not in erows:
            result['rivers'][river]=dict(status='UNEXPORTED_TARGET')
            continue
        gr,gh=grows[pub]; er,eh=erows[pub]
        shared=sorted(gh&eh)
        rates=first_rates(e,pool,pub,pct)
        result['rivers'][river]=dict(public_board=pub,gto_deals=gr['compatible_hole_card_pairs'],
            locked_deals=er['compatible_hole_card_pairs'],shared_rendered_sb_hands=shared,reachable_opponent_rates=rates)
        if shared and {r['street'] for r in rates}=={2,3}:
            return result|dict(status='PAIRED_RENDERED_RIVER',selected=pub),(g,e,gr,er,shared,rates)
    return result|dict(status='NO_PAIRED_RENDERED_RIVER'),None


def unpack(entries, directory, flop):
    base=directory/f'NL2-B545-{flop}-gto'
    for name,raw in entries.items():
        if name.startswith(('trainer/evidence/','solver/postflop/')):
            assert '..' not in Path(name).parts and not Path(name).is_absolute()
            dest=base/name; dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    return load_parent(directory,flop)


def register(model,group,refs,run,code,digest,pair):
    g,e,gr,er,hands,rates=pair
    for s,r in ((g,gr),(e,er)):
        s.update(run=run,archive_code=code,archive_sha256=digest)
        sub=s['subgame']
        r.update(spot='SB_BB',family='SRP',flop=sub['flop'],turn=sub['turn'],version=s['version'],
                 root_sha256=s['root_sha256'],source_run_id=run,source_sha256=s['source_sha256'],archive_sha256=digest,
                 root_gto_stage_gap_pct=g['root']['info']['gto_expl_pct'],root_locked_hero_gap_pct=None,
                 gto_gap_pct=sub['info']['gto_expl_pct'],locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),
                 root_applied_rust_lock_nodes=0,subgame_applied_rust_lock_nodes=sum(n['nodes'] for n in sub['info'].get('lock_stats',{}).values()),
                 lock_scope=lock_scope(sub,s['manifest']['locks'],s['version']))
    e['manifest'].update(gto_parent_source_run_id=run,gto_parent_source_sha256=g['root_sha256'])
    e['verified_gto_parent']=dict(run=run,sha256=g['root_sha256'])
    public=gr['public_board']
    board,pin=emit_board(model,g,e,public,gr['line'],texture(g['subgame']['flop']))
    board.update(restricted_flop_size_profile='SB_BB_50PCT_ONLY',restricted_flop_bet_sizes_pct=[50])
    pin.update(shared_rendered_route_hands=hands,conditional_gto_flop_root_sha256=g['root_sha256'],
               source_run_role='AUTHENTICATED_IMPORT',raw_archive_code=code)
    board['nl2_locked_variants'][0].update(gto_parent_source_run_id=run,gto_parent_source_sha256=g['root_sha256'],
        variant_label='半池翻牌 GTO 範圍，轉河牌實測回應鎖頻',applied_street_rates=rates,pool_sha256=POOL,
        measurement_policy='FROZEN_GTO_FLOP_TURN_AND_RIVER_MEASURED_RESPONSE',
        viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
    group['boards'].append(board);group['pins'].append(pin)
    for key,r in (('references',er),('gto_references',gr)):
        refs[key][source_key(model['model_id'],r)]=r


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--solver',type=Path,required=True)
    ap.add_argument('--inputs',type=Path,required=True)
    ap.add_argument('--flop',choices=CASES)
    ap.add_argument('--manifest',type=Path)
    ap.add_argument('--refine',action='store_true',help='Preserve the earlier marginal solve and add the measured history-specific turn response')
    ap.add_argument('--run',type=int,help='Actions run that uploaded and verified the retained source bytes')
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--pins',type=Path,help='Check the committed byte hashes and local reach results')
    args=ap.parse_args()
    assert not args.refine or (args.flop and not args.run and not args.manifest)
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    raw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw)==POOL
    pool=json.loads(raw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges
    routes=json.loads(subprocess.check_output(['node','tools/hu_b545_sb_routes.cjs']))
    route_models=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records']
    groups={r:dict(rank=int(r),model_id=info['model'],boards=[],pins=[]) for r,info in routes.items()}
    refs={r:dict(references={},gto_references={}) for r in routes}
    attempts=[]
    args.inputs.mkdir(parents=True,exist_ok=True)
    for flop in ([args.flop] if args.flop else CASES):
        pct,turn,rivers=CASES[flop];rank,mid=TARGETS[pct];rank=str(rank)
        assert pipeline.turns_for(flop)[0]==turn and pipeline.rivers_for(flop,turn)==rivers
        code=f'B545_R{rank}_{flop.upper()}'
        archive=args.inputs/f'NL2_{code}.zip'
        if args.manifest or args.refine:
            assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
        if args.manifest:
            assert args.flop and not args.run and not archive.exists()
            entries=parent_entries(solver,flop,args.manifest)
        elif archive.is_file():
            with ZipFile(archive) as z:
                entries={name:z.read(name) for name in z.namelist()}
        else:
            attempts.append(dict(flop=flop,status='MISSING_ARCHIVE'))
            continue
        with TemporaryDirectory() as temp:
            base=Path(temp)
            g=unpack(entries,base,flop)
            expected=tuple(ranges.to_str(v) for v in ranges.ranges('SB_BB','gto'))
            assert (g['root_job']['oop'],g['root_job']['ip'])==expected
            result,pair=assess(flop,g,entries,routes[rank],pool,pipeline,base,solver/'postflop/pfdriver/target/release/pfdriver' if args.manifest or args.refine else None)
        if args.manifest or args.refine:
            temp_archive=archive.with_suffix('.tmp')
            zip_payload(temp_archive,entries)
            temp_archive.replace(archive)
        digest=sha(archive.read_bytes())
        result.update(rank=int(rank),archive_sha256=digest,archive_code=code)
        attempts.append(result)
        if pair and args.run:
            register(route_models[mid],groups[rank],refs[rank],args.run,code,digest,pair)
    if args.pins:
        pins=json.loads(args.pins.read_bytes())
        lookup={r['flop']:r for r in attempts}
        for pin in pins['originals']:
            result=lookup[pin['flop']]
            assert all(result.get(k)==v for k,v in pin.items())
    ready={rank:group for rank,group in groups.items() if len(group['boards'])>=3}
    if args.run:
        measured=dict(schema='NL2_HU_B545_EXACT_SB_LOCKED_MEDIUM_V1',references={},gto_references={})
        for rank,group in ready.items():
            assert 3<=len(group['boards'])==len({b['flop'] for b in group['boards']})<=5
            (EVIDENCE/'reverified'/f'rank{rank}.json').write_bytes(json_bytes(group))
            for field in ('references','gto_references'):
                measured[field].update(refs[rank][field])
        if ready:
            Path('data/nl2_hu_b545_locked_medium.json').write_bytes(json_bytes(measured))
    args.out.write_bytes(json_bytes(dict(verified_import_run=args.run,source_origin='PINNED_RUST_ORIGINAL_ARRAYS',
        frozen_gto_flop=True,exact_bb_private_card_observations=False,attempts=attempts,verified_pairs=groups)))


if __name__=='__main__':
    main()
