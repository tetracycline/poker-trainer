"""Freeze a BTN GTO flop boundary and solve the BB's conditional turn and river policy."""
import argparse
import gzip
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_b528_rank134_monotone import LINE, MODEL, decide, route_hands
from hu_b541_rank134_replay import HEAD as OLD_HEAD, RUN as OLD_RUN, PINS
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import load_original, replay_native, solve_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board, source_case
from hu_sequential_cfr_reach import compatible_node_reach, game_reach

CASES = {
    'Qc7c2c': ('3d', ['5s','8c'], 14793081466),
    'Jd9d5d': ('3c', ['Qh','Kh'], 14792986662),
    'Qs6s2s': ('9h', ['7d','Td'], None),
    'Jc7c3c': ('8h', ['Th','8s'], None),
    'Tc8c4c': ('3d', ['7h','8s'], None),
}
REPORT = Path('data/nl2_hu_b544_rank134_conditional.json')


def fetch(folder, run, flops, artifact_id):
    folder.mkdir(parents=True,exist_ok=True)
    api = 'repos/tetracycline/poker-trainer/actions/'
    fresh = json.loads(subprocess.check_output(['gh','api',api+f'runs/{run}/artifacts?per_page=100']))['artifacts']
    for flop in flops:
        historical = CASES[flop][2]
        if historical or artifact_id:
            item = json.loads(subprocess.check_output(['gh','api',api+f'artifacts/{historical or artifact_id}']))
        else:
            selected = [r for r in fresh if r['name']==f'NL2-B544-{flop}-gto']
            if not selected:
                continue
            item, = selected
        aid = item['id']
        (folder/f'{aid}.json').write_bytes(json_bytes(item))
        with (folder/f'{aid}.zip').open('wb') as dest:
            subprocess.run(['gh','api',api+f'artifacts/{aid}/zip'],stdout=dest,check=True)


def gto_source(args, model, flop, pipeline, ranges):
    turn,rivers,historical = CASES[flop]
    name = f'NL2-{"B528" if historical else "B544"}-{flop}-gto'
    catalog = [json.loads(p.read_bytes()) for p in args.originals.glob('*.json')]
    found = [p for p in catalog if p['name']==name]
    if not found:
        return None, dict(status='MISSING_GTO_ORIGINAL')
    item, = found
    run, head = (OLD_RUN,OLD_HEAD) if historical else (args.run,args.head)
    assert (item['workflow_run']['id'],item['workflow_run']['head_sha'],item['workflow_run']['repository_id']) == (run,head,1438346845)
    aid = item['id']
    pin = dict(run=run,head=head,name=name,sha256=item['digest'][7:])
    raw = args.originals/f'{aid}.zip'
    assert item['digest']=='sha256:'+sha(raw.read_bytes())
    if historical:
        fixed, = (p for p in json.loads(PINS.read_bytes()) if p['id']==historical)
        assert (aid,name,pin['sha256'])==(historical,fixed['name'],fixed['sha256'])
    with ZipFile(raw) as archive:
        manifest = json.loads(archive.read(f'trainer/evidence/{flop}-gto.json'))
        assert sha(archive.read('trainer/evidence/pool_stats.json')) == POOL
    assert (manifest['flop_size_profile'],manifest['restricted_tree_assumption']) == (
        ('full',False) if historical else ('btn-50-only',True))
    assert manifest['selected_lines']==['x b50 c'] and manifest['selected_turn_lines']==['x x'] and manifest['turns']==[turn]
    if manifest['failures'] or not manifest['cases']:
        return None,dict(status='NO_GTO_CONTINUATION',failures=manifest['failures'],skips=manifest['skipped'])
    old = load_original(args.originals,aid,pin,'BTN_BB',flop,turn,'gto',pot=550,stack=9750,
                        pipeline=pipeline,ranges=ranges,flop_line='x b50 c')
    g, identity = old['source'],old['identity']
    sizes = '33%,50%,75%,100%' if historical else '50%'
    assert identity['flop_oop_menu']==identity['flop_ip_menu']==sizes
    assert old['job']['turn_oop']==old['job']['turn_ip']=='50%,100%' and old['job']['root_no_bet']
    assert g['subgame']['rivers']==rivers and g['subgame']['pot']==1100 and g['subgame']['stack']==9475
    assert sha(compact(g['root']))==identity['root_sha256']
    g['root_sha256']=identity['root_sha256']
    candidates={}
    for river in rivers:
        public=old['public']+river
        case=source_case(model,g,public,LINE,1)
        candidates[public]=route_hands(case[1],public) if case else []
    if historical:
        assert all(candidates.values())
    report=dict(original=identity,gto_route_witnesses=candidates)
    return (old if any(candidates.values()) else None), dict(report,status='ELIGIBLE_GTO_BOUNDARY' if any(candidates.values()) else 'NO_RENDERED_GTO_HAND')


def measured_at(source, public, native, pool):
    root,sub=source['root'],source['subgame']
    masks=game_reach(root,sub)[0]
    rates=[]
    assumption=None
    for n in sub['nodes']:
        street=len(n['board'])//2-2
        if n['player']!=0 or n['board']!=public[:4+2*street] or len(n['acts'])<2:
            continue
        lines=('x b50 c/x b50','x b50 c/x b100') if street==2 else (LINE[:-1],LINE+' b50',LINE+' b100')
        if n['line'] not in lines:
            continue
        key='|'.join((n['board'],n['line'],'0'))
        reach=compatible_node_reach(root,sub,n,masks[key])['compatible_hole_card_pairs']
        if not reach:
            continue
        i=next(i for i,r in enumerate(native['locks']) if re.search(r['pat'],n['line']))
        r=native['locks'][i]
        config=native['job']['locks'][i]
        stats=sub['info']['lock_stats'][r['pat']]
        assert r['pat']==config['pat'] and stats['nodes']>0 and native['job']['hero']==1
        if n['line']==LINE[:-1]:
            assert (r['scope'],r['n'],config['bet'])==('ASSUMED_HISTORY_RATE_OR_SIZE',0,.45)
            assumption=dict(scope=r['scope'],pattern=r['pat'],bet=.45,pool_decisions=0,
                            compatible_deals=reach,driver_pattern_aggregate=stats)
            continue
        token=n['line'].split()[-1]
        bucket={'b50':'34-55%','b100':'81-110%'}[token]
        if street==2:
            assert r['scope']=='PINNED_MEASURED_NL2_SOURCE'
            assert r['source']==f'SRP_PFR_IP.vs_turn_barrel_by_size[{bucket}]'
            target=pool['postflop_HU']['SRP_PFR_IP']['vs_turn_barrel_by_size'][bucket]
        else:
            assert r['street']==3 and r['scope']=='IMPUTED_HISTORY_FROM_TRUE_STREET_BY_SIZE_MARGINAL'
            assert r['source']==f'NL2.HU_facing_bet[3].by_size[{bucket}]'
            target=pool['HU_facing_bet']['3']['by_size'][bucket]
        assert r['n']==target['n']>=500 and (config['fold'],config['raise'])==(target['fold']/100,target['raise']/100)
        rates.append(dict(street=street,token=token,opportunity='FACING_BET',line=n['line'],pattern=r['pat'],source=r['source'],
                          n=r['n'],nodes=stats['nodes'],scope=r['scope'],compatible_deals=reach,
                          target_fold_pct=target['fold'],target_raise_pct=target['raise'],
                          fold_pct=100*stats['fold'],raise_pct=100*stats['agg']))
    return rates,assumption


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--originals',type=Path,required=True)
    ap.add_argument('--run',type=int,required=True)
    ap.add_argument('--head',required=True)
    ap.add_argument('--solver',type=Path)
    ap.add_argument('--results',type=Path)
    ap.add_argument('--flop',choices=CASES)
    ap.add_argument('--driver',type=Path)
    ap.add_argument('--fetch',action='store_true')
    ap.add_argument('--artifact-id',type=int,help='Fresh GTO artifact just uploaded by this worker')
    args=ap.parse_args()
    flops=[args.flop] if args.flop else list(CASES)
    if args.fetch:
        assert not args.artifact_id or (args.flop and not CASES[args.flop][2])
        fetch(args.originals,args.run,flops,args.artifact_id)
        return
    subprocess.run(['node','tools/hu_b528_rank134_routes.cjs'],check=True)
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    if args.driver:
        assert args.flop and args.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    raw_pool=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw_pool)==POOL
    pool=json.loads(raw_pool)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges
    model=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr'])==(134,'BTN_BB',8.614)
    group=dict(rank=134,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B544_CONDITIONAL_MEDIUM_V1',references={},gto_references={})
    attempts=[]
    for flop in flops:
        old,report=gto_source(args,model,flop,pipeline,ranges)
        report.update(flop=flop,selected=None,rivers={})
        attempts.append(report)
        if old is None:
            continue
        code=f'B544_R134_{flop.upper()}_EXP_IP_{args.run}'
        filename=f'NL2_{code}.json.gz'
        if args.driver:
            path=solve_native(old,'exp_ip',pool,pipeline,args.results,args.driver,args.run,code)
            replay_native(old,'exp_ip',pool,pipeline,path,args.run,code)
            continue
        files=list(args.results.rglob(filename))
        if not files:
            report['status']='MISSING_COMPLETED_CONDITIONAL'
            continue
        path,=files
        e=replay_native(old,'exp_ip',pool,pipeline,path,args.run,code)
        e['root_sha256']=old['identity']['root_sha256']
        g=old['source']
        if any(not 0<=e['subgame']['info'][k]<=.5 for k in ('gto_expl_pct','hero_gap_pct')):
            report['status']='CONDITIONAL_CONVERGENCE_OUTSIDE_GATE'
            continue
        for river in CASES[flop][1]:
            rows,info=decide(model,[g,e],flop,river)
            report['rivers'][river]=info
            if not rows or report['selected']:
                continue
            public=info['public_board']
            native=json.loads(gzip.decompress(path.read_bytes()))
            rates,assumption=measured_at(e,public,native,pool)
            if {r['street'] for r in rates}!={2,3} or not assumption:
                info['status']='INCOMPLETE_REACHABLE_OPPONENT_COVERAGE'
                continue
            parent_zip=args.originals/f"{old['identity']['artifact_id']}.zip"
            g['archive_code']=f"B544_R134_{flop.upper()}_GTO_{g['run']}"
            shutil.copyfile(parent_zip,EVIDENCE/f"NL2_{g['archive_code']}.zip")
            b,pin=emit_board(model,g,e,public,LINE,texture(flop))
            assert b['actual_pot_bb']==11 and b['actual_effective_stack_bb']==94.75
            assert pin['common_legal_hero_combos']==info['common_legal_hands']
            menu=old['identity']['flop_ip_menu']
            pin.update(shared_rendered_route_hands=info['route_witnesses'],original_gto_archive=old['identity'],
                       conditional_gto_flop_root_sha256=e['root_sha256'],historical_restricted_flop_game_tree=menu=='50%')
            b.update(frozen_gto_flop=True,flop_bet_menu=menu)
            if menu=='50%':
                b.update(restricted_flop_size_profile='BTN_BB_50PCT_ONLY',restricted_flop_bet_sizes_pct=[50])
            # The BB's river lead is assumed, even when the subsequent response to the BTN bet has measured rates.
            b['nl2_locked_variants'][0].update(variant_label='固定 GTO 翻牌範圍，轉牌實測回應與河牌尺寸鎖頻（河牌領打 45% 假設）',
                measurement_policy='FROZEN_GTO_FLOP_TURN_HISTORY_RIVER_SIZE_MARGINAL',pool_sha256=POOL,applied_street_rates=rates,
                river_open_bet_assumption=assumption,gto_parent_source_run_id=g['run'],gto_parent_source_sha256=e['root_sha256'],
                viewer_archive_code=pin.get('locked_viewer_archive_code',pin['viewer_archive_code']),
                viewer_sha256=pin.get('locked_viewer_sha256',pin['viewer_sha256']))
            group['boards'].append(b)
            group['pins'].append(pin)
            gr,er=rows
            medium['gto_references'][source_key(MODEL,gr)]=gr
            medium['references'][source_key(MODEL,er)]=er
            shutil.copyfile(path,EVIDENCE/filename)
            report['selected']=public
        report['status']='VERIFIED_COMMON_RENDERED_HAND' if report['selected'] else 'NO_PAIRED_RENDERED_DECISION'
    if args.driver:
        return
    count=len(group['boards'])
    assert len({b['flop'] for b in group['boards']})==count<=5
    REPORT.write_bytes(json_bytes(dict(run=args.run,model_id=MODEL,qualified_distinct_flops=count,
                                       attempts=attempts,verified_pairs=group,locked_medium=medium)))
    if count>=3:
        (EVIDENCE/'reverified/rank134.json').write_bytes(json_bytes(group))
        Path('data/nl2_hu_b544_locked_medium.json').write_bytes(json_bytes(medium))


if __name__=='__main__':
    main()
