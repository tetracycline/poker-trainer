"""Verify the BB 3-bettor's native checked-through turn and solve the missing OOP locks."""
import argparse
from pathlib import Path
import json
import shutil
import subprocess
import sys

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, load_original, replay_native, solve_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from solve_hu_missing_branches import EXTRA_SPOTS

MID='ln-3bp-3b_t_model-n5cvfv'
LINE='x x/'
PINS=Path('data/nl2_hu_b502_rank120_artifacts.json')
# Freeze all named public runouts before observing the new OOP solves.
CASES={
    'Ks7h2d':('9d',14593390837,14592524168),
    'As8h4d':('8d',14528551179,None),
    'Ks7s2s':('9d',14530206356,None),
    'KsQh4d':('Tc',14592263783,None),
}
ATTEMPTS=Path('data/nl2_hu_b502_rank120_attempts.json')
JOINT=Path('data/nl2_hu_b502_locked_medium.json')
GROUP=EVIDENCE/'reverified/rank120.json'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals',type=Path,required=True)
    parser.add_argument('--solver',type=Path,required=True)
    parser.add_argument('--flop',choices=CASES)
    parser.add_argument('--driver',type=Path)
    parser.add_argument('--results',type=Path)
    parser.add_argument('--run',type=int)
    args=parser.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',str(solver),'rev-parse','HEAD'],text=True).strip()==SOLVER
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw)==POOL
    pool=json.loads(poolraw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    pins=json.loads(PINS.read_bytes())
    registry=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())
    model=registry['records'][MID]
    assert (model['frequency_rank'],model['solver_profile'],model['family'],model['street'])==(120,'BB3_BTN','3BP',1)
    group=dict(rank=120,model_id=MID,boards=[],pins=[])
    report=dict(schema='NL2_HU_B502_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    attempts=[]
    for flop,(turn,gid,eid) in CASES.items():
        if args.flop and flop!=args.flop:continue
        def load(artifact,version):
            return load_original(args.originals,artifact,pins[str(artifact)],'BB3_BTN',flop,turn,version,
                                 pot=2050,stack=9000,pipeline=pipeline,ranges=ranges)
        original=load(gid,'gto')
        g=original['source'];public=original['public'];root=original['identity']['root_sha256']
        gr=audit_decision(g,public,LINE,0,root)
        assert gr and gr['status']=='POSITIVE_JOINT_REACH' and 'b50' in gr['source_actions']
        code='B502_R120_'+flop.upper()+'_'+turn.upper()+'_EXP_OOP'
        filename=f'NL2_{code}.json.gz'
        if args.driver:
            assert args.flop and args.results and args.run and not eid
            dest=solve_native(original,'exp_oop',pool,pipeline,args.results,args.driver,args.run,code)
            replay_native(original,'exp_oop',pool,pipeline,dest,args.run,code)
            return
        if eid:
            previous=load(eid,'exp_oop');e=previous['source'];lockroot=previous['identity']['root_sha256']
        elif not args.results:
            continue
        else:
            matches=list(args.results.rglob(filename));assert len(matches)<=1
            if not matches:
                attempts.append(dict(flop=flop,public_board=public,gto=gr,status='MISSING_COMPLETED_NATIVE_OUTPUT'))
                continue
            dest=EVIDENCE/filename;shutil.copyfile(matches[0],dest)
            e=replay_native(original,'exp_oop',pool,pipeline,dest,args.run,code)
            lockroot=root
        er=audit_decision(e,public,LINE,0,lockroot)
        assert er and er['source_actions']==gr['source_actions']
        assert er['subgame_applied_rust_lock_nodes']>0 and er['lock_scope']['observed_marginal_source_nodes']>0
        row=dict(flop=flop,public_board=public,gto=gr,exp_oop=er,original_gto=original['identity'])
        if eid:row['original_exp_oop']=previous['identity']
        else:
            row.update(frozen_gto_flop=True,verified_street_locks=e['measured_lock_application'],
                       applied_rust_rates=e['applied_rust_rates'])
        if not 0<=er['gto_gap_pct']<=.5 or not 0<=er['locked_hero_gap_pct']<=.5:
            row['status']='CONVERGENCE_OUTSIDE_GATE'
        elif er['status']!='POSITIVE_JOINT_REACH':
            row['status']=er['status']
        else:
            row['status']='BOTH_POSITIVE'
            if args.results:
                b,p=emit_board(model,g,e,public,LINE,texture(flop))
                assert p['GTO_compatible_hole_card_pairs']==gr['compatible_hole_card_pairs'] and p['NL2_compatible_hole_card_pairs']==er['compatible_hole_card_pairs']
                p['original_gto_archive']=original['identity']
                if eid:p['original_locked_archive']=previous['identity']
                else:
                    p['conditional_gto_flop_root_sha256']=root
                    rates=[]
                    for pattern,target in e['measured_lock_application']['marginal_targets'].items():
                        actual=e['applied_rust_rates'].get(pattern)
                        if not actual or not actual['nodes']:continue
                        token=pattern.split(')?')[-1][:-1]
                        rates.append(dict(street=target['street'],token=token,n=target['n'],nodes=actual['nodes'],
                                          fold_pct=100*actual['fold'],raise_pct=100*actual['agg']))
                    assert rates
                    b['nl2_locked_variants'][0].update(variant_label='原始 GTO 翻牌範圍，轉河牌分街 NL2 鎖頻',
                        measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',pool_sha256=POOL,applied_street_rates=rates,
                        viewer_archive_code=p['locked_viewer_archive_code'],viewer_sha256=p['locked_viewer_sha256'],
                        gto_parent_source_run_id=g['run'],gto_parent_source_sha256=root)
                group['boards'].append(b);group['pins'].append(p)
                report['references'][source_key(MID,er)]=er
                report['gto_references'][source_key(MID,gr)]=gr
        attempts.append(row)
    if args.results:
        assert args.run and not args.flop
        ATTEMPTS.write_bytes(json_bytes(dict(rank=120,model_id=MID,run_id=args.run,attempts=attempts)))
        if len(group['boards'])>=3:
            assert len(group['boards'])==len({b['flop'] for b in group['boards']})<=5
            GROUP.parent.mkdir(exist_ok=True);GROUP.write_bytes(json_bytes(group));JOINT.write_bytes(json_bytes(report))
        print('Positive paired flops',len(group['boards']))


if __name__=='__main__':
    main()
