"""Solve the ISO BTN turn against a street-specific opponent lock from the exact GTO flop boundary."""
import argparse
import base64
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import compact, EVIDENCE, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b514_turn_stab import rates
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, replay_native, solve_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey
from solve_hu_assumed_pots import RULES, w_iso_ip, w_iso_oop

sys.path.insert(0,str(Path(__file__).resolve().parent/'lines_pipeline'))
from run10_common import hcls

DATA=Path('data')
MODELS={124:('ln-iso-t_model-1gjwm8f',50),125:('ln-iso-t_model-szsdgn',33)}
TEXTURE={'LOW':'low','KQ_HIGH':'KQ_high','MONOTONE':'mono'}


def load_boundary(downloads, flop, turn, turns, pct, run):
    line=f'x b{pct} c'
    game=original(downloads,flop,turn,'gto',batch='B539',spot='ISO_BTN_CO',flop_line=line,
        flop_lines=['x b33 c','x b50 c'],flop_policy='iso-checked-b33b50',turn_policy='checkcheck',turn_extract='x x',
        root_pot=950,root_stack=9600,frozen_turns=list(turns),preflop_source='ASSUMED_EXPLICIT_169CLASS')
    root,manifest=game['root'],game['manifest']
    assert (manifest['solver_pin'],manifest['solver_ranges_sha256'],manifest['pool_source_sha256'])==(PIPELINE,RANGES,POOL)
    profile=manifest['preflop_ranges']
    assert profile['profile']==RULES['ISO_BTN_CO'] and manifest['pot_family']=='ISO'
    ranks='AKQJT98765432'
    names={a+b+s for i,a in enumerate(ranks) for b in ranks[i:] for s in (('',) if a==b else ('s','o'))}
    for seat,policy in [('oop',w_iso_oop),('ip',w_iso_ip)]:
        weights={n:float(policy(n)) for n in names}
        assert len(names)==169 and weights==profile[seat+'_169']
        rendered={name:float(value) for name,value in (v.split(':') for v in game['root_job'][seat].split(','))}
        assert rendered=={name:value for name,value in weights.items() if value>=.005}
    if game['subgame'] is None:
        return None
    sub,job=game['subgame'],game['subgame_job']
    bet=(950*pct+50)//100
    facing,=(n for n in root['nodes'] if n['line']==f'x b{pct}' and len(n['board'])==6)
    parent,=(n for n in root['nodes'] if n['line']==line+'/' and n['board'].endswith(turn))
    assert facing['bets']==[0,bet] and facing['player']==0 and 'c' in facing['acts']
    assert parent['bets']==[bet,bet] and (parent['pot'],job['pot'],job['stack'])==(950+2*bet,950+2*bet,9600-bet)
    assert (sub['pot'],sub['stack'],sub['rivers'])==(job['pot'],job['stack'],turns[turn])
    assert job['line0']==line.split()+['/'] and job['root_no_bet'] and not job.get('locks')
    for seat,side in enumerate(('oop_w','ip_w')):
        assert job[side]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    check,=(n for n in sub['nodes'] if n['board']==parent['board'] and n['line']==line+'/')
    assert check['player']==0 and check['acts']==['x']
    identity=dict(original_run=run,root_sha256=game['root_sha256'],source_sha256=game['source_sha256'],
                  root_job_sha256=sha(compact(game['root_job'])),turn_job_sha256=sha(compact(job)))
    packed=gzip.compress(compact(dict(solver=SOLVER,rust=RUST,run_id=run,source_arrays=[game])),mtime=0)
    game.update(run=run,archive_code=f'B539_{flop.upper()}_{turn.upper()}_B{pct}_GTO',archive_sha256=sha(packed))
    return dict(source=game,identity=identity,job=job,public=parent['board']),packed


def actor_hands(source,row):
    mask=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    return {''.join(cardkey(h)) for h,m in zip(source['subgame']['hands'][1],mask,strict=True) if m}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver',required=True,type=Path)
    parser.add_argument('--downloads',required=True,type=Path)
    parser.add_argument('--run',required=True,type=int)
    parser.add_argument('--flop')
    parser.add_argument('--out',type=Path)
    parser.add_argument('--driver',type=Path)
    args=parser.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    if args.driver:
        assert args.flop and args.out and args.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw)==POOL and args.run>0
    pool=json.loads(poolraw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    routes=json.loads(subprocess.check_output(['node','tools/hu_b539_iso_routes.cjs']))
    pins=json.loads((DATA/'nl2_hu_b539_flops.json').read_bytes())
    models=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records']
    groups={r:dict(rank=r,model_id=mid,boards=[],pins=[]) for r,(mid,_) in MODELS.items()}
    data={r:[] for r in MODELS}
    attempts=[]
    if args.flop:
        pins={args.flop:pins[args.flop]}
    for flop,turns in pins.items():
        selected=set()
        for rank,(mid,pct) in MODELS.items():
            model=models[mid]
            assert (model['frequency_rank'],model['solver_profile'],model['street'])==(rank,'ISO_BTN_CO',1)
            cols=routes[str(rank)][TEXTURE[texture(flop)]]
            decision=f'x b{pct} c/x'
            for turn in turns:
                record=dict(rank=rank,flop=flop,turn=turn)
                attempts.append(record)
                manifest=args.downloads/f'NL2-B539-{flop}-gto/trainer/evidence/{flop}-gto.json'
                if not manifest.is_file() or json.loads(manifest.read_bytes())['failures']:
                    record['status']='ORIGINAL_UNAVAILABLE'
                    continue
                result=load_boundary(args.downloads,flop,turn,turns,pct,args.run)
                if not result:
                    record['status']='NO_NATIVE_TURN'
                    continue
                boundary,raw=result
                g=boundary['source'];public=boundary['public'];rootsha=boundary['identity']['root_sha256']
                if not all(0<=g[k]['info']['gto_expl_pct']<=.5 for k in ('root','subgame')):
                    record['status']='GTO_OUTSIDE_CONVERGENCE_GATE'
                    continue
                gr=audit_decision(g,public,decision,1,rootsha)
                assert gr and 'b50' in gr['source_actions']
                eligible={h for h in actor_hands(g,gr) if hcls(h,public[:6]) in cols[0] and hcls(h,public) in cols[1]}
                record.update(public=public,gto_sha=g['source_sha256'],gto_joint_pairs=gr['compatible_hole_card_pairs'],gto_rendered_hands=len(eligible))
                if not eligible:
                    record['status']='NO_VISIBLE_GTO_HAND'
                    continue
                code=f'B539_R{rank}_{flop.upper()}_{turn.upper()}_EXP_IP'
                name=f'NL2_{code}.json.gz'
                if args.driver:
                    out=solve_native(boundary,'exp_ip',pool,pipeline,args.out,args.driver,args.run,code)
                else:
                    out=args.downloads/f'NL2-B539-{flop}-gto/trainer/native/{name}'
                if not out.is_file():
                    record['status']='LOCK_SOURCE_UNAVAILABLE'
                    continue
                e=replay_native(boundary,'exp_ip',pool,pipeline,out,args.run,code)
                if args.driver:
                    continue
                info=e['subgame']['info']
                if not all(0<=info[k]<=.5 for k in ('gto_expl_pct','hero_gap_pct')):
                    record['status']='LOCK_OUTSIDE_CONVERGENCE_GATE'
                    continue
                er=audit_decision(e,public,decision,1,rootsha)
                assert er and er['source_actions']==gr['source_actions'] and er['subgame_applied_rust_lock_nodes']>0
                shared=eligible & actor_hands(e,er)
                record.update(lock_sha=e['source_sha256'],lock_joint_pairs=er['compatible_hole_card_pairs'],shared_rendered_hands=len(shared))
                if not shared:
                    record['status']='NO_SHARED_VISIBLE_HAND'
                    continue
                record['status']='REACHED'
                if rank in selected:
                    continue
                selected.add(rank)
                b,p=emit_board(model,g,e,public,decision,texture(flop))
                p['rendered_source_hands']=[dict(hand=h,flop=hcls(h,public[:6]),turn=hcls(h,public)) for h in sorted(shared)]
                p['native_gto_parent']=boundary['identity']
                b['nl2_locked_variants'][0].update(variant_label='原始翻牌 GTO 範圍・轉河牌 NL2 分街鎖頻',
                    gto_parent_source_run_id=args.run,gto_parent_source_sha256=rootsha,pool_sha256=POOL,
                    measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(e),
                    viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
                (EVIDENCE/f"NL2_{g['archive_code']}.json.gz").write_bytes(raw)
                shutil.copyfile(out,EVIDENCE/name)
                groups[rank]['boards'].append(b);groups[rank]['pins'].append(p);data[rank].append((gr,er))
    if args.driver:
        return
    report=dict(schema='NL2_HU_B539_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    for rank,group in groups.items():
        count=len(group['boards'])
        assert count==len({b['flop'] for b in group['boards']})<=5
        if count>=3:
            (EVIDENCE/'reverified'/f'rank{rank}.json').write_bytes(json_bytes(group))
            for gr,er in data[rank]:
                report['gto_references'][source_key(group['model_id'],gr)]=gr
                report['references'][source_key(group['model_id'],er)]=er
    (DATA/'nl2_hu_b539_locked_medium.json').write_bytes(json_bytes(report))
    (DATA/'nl2_hu_b539_iso_results.json').write_bytes(json_bytes(dict(run=args.run,groups=groups,attempts=attempts)))


if __name__=='__main__':
    main()
