#!/usr/bin/env python3
"""B113: authentic pinned B43 UTG_CO 9s6h3d IP turn-river NL2 lock.

Original GTO flop/root/job comes byte-for-byte from B112 SHA audited
individual B43 GTO job. Original whole run 44806967313 had a verifier
bookkeeping failure; it was later independently verified and salvaged.
NO full flop re-solve or falsely observed per-private-card NL2 strategies.
"""
import argparse,json,pathlib,shutil,sys,time,traceback
from solve_hu_multiboard_100bb import make_fallbacks,sha,SIZES
R=pathlib.Path(__file__).resolve().parents[1]/'data'
PIN=R/'nl2_hu_b112_utg_9s6h3d_gto_parent_pin.json'
INDEX=R/'solver_evidence/NL2_MULTIBOARD_B43_UTG_B75.index.json'
SPOT='UTG_CO';FLOP='9s6h3d';TURN='Ts'
LINE='b75 c';TURNLINE='x b50 c';RUN=44806967313

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--solver-root',required=True,type=pathlib.Path)
    ap.add_argument('--gto-artifact-root',required=True,type=pathlib.Path)
    ap.add_argument('--manifest',required=True,type=pathlib.Path)
    args=ap.parse_args()
    pin=json.loads(PIN.read_text());index=json.loads(INDEX.read_text())
    assert pin['schema']=='NL2_HU_B112_UTG_CO_B43_9S6H3D_GTO_PARENT_PIN_V1'
    assert pin['result']=='PASS_INDIVIDUALLY_VERIFIED_GTO_PARENT'
    assert pin['original_GTO_source_run']==index['run_id']==RUN
    assert pin['source_archive_sha256']==index['gzip_sha256']
    assert pin['original_B43_whole_run_failed_verifier_count_not_CFR']
    assert pin['B43_two_individual_solver_jobs_reverified']
    assert pin['frozen_rank']==236 and pin['model_id']=='ln-ipc-r_model-1nz4lt1'
    assert pin['existing_locked_boards']==['AsKh3d','Ks7h2d']
    assert (pin['public_flop'],pin['turn'],pin['flop_line'],pin['turn_line'])==(FLOP,TURN,LINE,TURNLINE)
    assert pin['positive_reach_IP_GTO_actor_nodes']>0
    artifact=args.gto_artifact_root.resolve()
    mfile=artifact/'evidence/UTG_CO-gto-9s6h3d.json'
    root=artifact/'solver/postflop'/pin['GTO_root_relative_path']
    jobfile=root.with_suffix('.job.json')
    assert all(x.is_file() for x in (mfile,root,jobfile))
    assert sha(mfile)==pin['GTO_manifest_sha256']
    assert sha(root)==pin['GTO_root_sha256']
    assert sha(jobfile)==pin['GTO_job_sha256']
    m=json.loads(mfile.read_text());fr=json.loads(root.read_text());jobroot=json.loads(jobfile.read_text())
    assert m['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
    assert (m['spot'],m['version'],m['flop'])==(SPOT,'gto',FLOP)
    assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    assert m['no_generic_certification'] and not m['failures']
    assert (m['root_pot_bb'],m['root_remaining_bb'])==(6.5,97.5)
    assert (fr['flop'],fr['pot'],fr['stack'])==(FLOP,650,9750)
    assert (jobroot['pot'],jobroot['stack'])==(650,9750)
    assert jobroot.get('hero') is None and not jobroot.get('locks')
    assert jobroot['rake_rate']==.05 and jobroot['rake_cap']==1000
    assert all(z in jobroot.get('flop_oop','') for z in SIZES)
    assert all(z in jobroot.get('flop_ip','') for z in SIZES)
    assert TURN in fr.get('turns',[])
    parents=[x for x in fr['nodes'] if x['line']==LINE+'/' and x['board'][-2:]==TURN]
    assert len(parents)==1
    parent=parents[0]
    assert all(any(float(w)>1e-4 for w in seat) for seat in parent['wr'])
    src=args.solver_root.resolve();pf=src/'postflop'
    assert (pf/'pfdriver/target/release/pfdriver').is_file()
    sys.path.insert(0,str(pf/'py'))
    import pipeline
    spot=pipeline.SPOTS[SPOT]
    assert abs(spot['pot']-6.5)<1e-8 and abs(spot['stack']-97.5)<1e-8
    pool=json.loads((src/'inputs/pool_stats.json').read_text())['NL2']
    assert sha(src/'inputs/pool_stats.json')==m['pool_source_sha256']
    assert sha(src/'v8_build/build/pf_data.json')==m['preflop_ranges']['full_sha256']
    orig_locks=pipeline.lock_list
    pipeline.lock_list=lambda s,v,f:make_fallbacks(s,v,pool,orig_locks,f)
    old_make=pipeline.make_job
    def make(*pos,**kwargs):
        kwargs['target']=.5;kwargs['rank']=.5;kwargs['iters']=1700
        job=old_make(*pos,**kwargs)
        job['flop_oop']=','.join(SIZES)
        job['flop_ip']=','.join(SIZES)
        job['flop_raise']='3x,a'
        return job
    pipeline.make_job=make
    pipeline.TURN_LINES=[TURNLINE]
    assert pipeline.turns_for(FLOP)[0]==TURN
    out=pf/'out'/SPOT/'exp_ip'
    out.mkdir(parents=True,exist_ok=True)
    cloned=out/(FLOP+'_multiboard.json')
    clonedjob=cloned.with_suffix('.job.json')
    shutil.copy2(root,cloned);shutil.copy2(jobfile,clonedjob)
    assert sha(cloned)==pin['GTO_root_sha256']
    assert sha(clonedjob)==pin['GTO_job_sha256']
    lock_source,locks_meta=pipeline.lock_list(SPOT,'exp_ip',FLOP)
    assert lock_source and locks_meta
    report=dict(schema='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',
       spot=SPOT,version='exp_ip',flop=FLOP,
       pot_family='SRP',root_pot_bb=6.5,root_remaining_bb=97.5,
       root_spr=round(97.5/6.5,6),
       preflop_ranges=m['preflop_ranges'],n_NL2_hands=pool['hands'],
       pool_source_sha256=sha(src/'inputs/pool_stats.json'),
       solver_pin=sha(pf/'py/pipeline.py'),solver_ranges_sha256=sha(pf/'py/ranges.py'),
       flop_action_sizes=list(SIZES),flop_size_profile='full',
       restricted_tree_assumption=False,allow_OOP_flop_leads=True,
       turn_sizing_mode='default',
       turn_subgame_sizing={'oop':pipeline.SUB['turn_oop'],'ip':pipeline.SUB['turn_ip']},
       selected_lines=[LINE],flop_line_policy='oop-b75only',
       selected_turn_lines=[TURNLINE],turn_line_policy='xb50only',turns=[TURN],
       flop_parent_mode='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK',
       file_flop=str(cloned.relative_to(pf)),file_flop_sha256=sha(cloned),
       flop_root_jobfile_sha256=sha(clonedjob),
       gto_parent_source_sha256=pin['GTO_root_sha256'],
       gto_parent_source_run_id=RUN,
       gto_parent_source_manifest_sha256=pin['GTO_manifest_sha256'],
       original_B112_verified_GTO_pin_sha256=sha(PIN),
       original_B43_whole_workflow_verification_failed_but_GTO_individually_verified=True,
       B43_already_verified_EXP_OOP_is_not_EXP_IP_source=True,
       original_full_GTO_flop_byte_identical_not_recomputed=True,
       NL2_hero_lock_scope='TURN_RIVER_ONLY_FROM_SHA_PINNED_ORIGINAL_B43_GTO',
       locks=[dict(pat=x['pat'],scope=x.get('scope','PINNED_MEASURED_NL2_SOURCE'),
           source=x.get('src'),n=x.get('n')) for x in locks_meta],
       unknown_action_frequency_policy='NL2 measured pooled action-size/street marginals where observed; separate assumed defaults otherwise. No measured private-hand conditional policy.',
       no_generic_certification=True,not_observed_exact_NL2_hero_EV=True,
       cases=[],failures=[],skipped=[],elapsed_seconds=0)
    t0=time.monotonic()
    try:
        pipeline.solve_sub(SPOT,'exp_ip',FLOP,fr,LINE,TURN)
        sub=out/(FLOP+'_'+LINE.replace(' ','')+'_'+TURN+'.json')
        if not sub.is_file():raise FileNotFoundError('Authentic pinned Rust IP river subgame absent')
        data=json.loads(sub.read_text())
        assert data['line0']==LINE and data['turn']==TURN
        assert any(len(z['board'])==10 for z in data['nodes'])
        report['cases'].append(dict(line=LINE,turn=TURN,
            source_path=str(sub.relative_to(pf)),source_sha256=sha(sub),
            real_flop_parent_spr=round((fr['stack']-max(parent['bets']))/parent['pot'],6),
            flop_parent_pot_bb=parent['pot']/100,
            flop_parent_effective_remaining_bb=(fr['stack']-max(parent['bets']))/100,
            true_river_nodes=sum(len(z['board'])==10 for z in data['nodes']),
            source_node_count=len(data['nodes']),
            gto_gap_pct=data['info'].get('gto_expl_pct'),
            hero_gap_pct=data['info'].get('hero_gap_pct'),
            lock_stats=data['info'].get('lock_stats',{}),
            status='REAL_B43_GTO_FLOP_TURN_RIVER_PARTIAL_NL2_IP_LOCK'))
    except Exception as e:
        report['failures'].append(dict(error=str(e),traceback=traceback.format_exc()[-1900:]))
    report['elapsed_seconds']=round(time.monotonic()-t0,2)
    report['solved_cases']=len(report['cases'])
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(spot=SPOT,flop=FLOP,turn=TURN,flop_line=LINE,
        turn_line=TURNLINE,locked_cases=report['solved_cases'],
        failures=report['failures'],elapsed_seconds=report['elapsed_seconds'],
        original_GTO_root_SHA=pin['GTO_root_sha256']),ensure_ascii=False),flush=True)
    if report['failures'] or report['solved_cases']!=1:raise SystemExit(1)

if __name__=='__main__':main()
