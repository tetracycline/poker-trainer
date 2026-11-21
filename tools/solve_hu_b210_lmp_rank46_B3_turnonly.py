#!/usr/bin/env python3
"""B210: true actor-IP LMP_CO_BB selected original B3 9s6h3d flop turn/river NL2 marginal lock using
byte-identical successful B3 original full-root GTO parent on either frozen board. The GTO flop is NOT recomputed.
No generic bucket CERT and no unobserved per-hole-card NL2 frequencies.
"""
import argparse,json,pathlib,shutil,sys,time,traceback
from solve_hu_multiboard_100bb import make_fallbacks,sha,SIZES
ROOT=pathlib.Path(__file__).resolve().parents[1]/'data'
PIN=None
SPOT='LMP_CO_BB';FLOP=None;TURN=None;LINE='x b50 c';TURNLINE='x x'
RUN=44666294821

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--solver-root',type=pathlib.Path,required=True)
    ap.add_argument('--gto-artifact-root',type=pathlib.Path,required=True)
    ap.add_argument('--manifest',type=pathlib.Path,required=True)
    ap.add_argument('--flop',choices=['9s6h3d'],required=True)
    # Immutable B3 full-size original GTO, not a new root solve.
    args=ap.parse_args()
    global PIN,FLOP,TURN
    FLOP=args.flop
    PIN=ROOT/'nl2_hu_b209_rank46_lmp_9s6h3d_original_b3_gto_pin.json'
    pin=json.loads(PIN.read_text())
    TURN=pin['turn']
    source=pin
    assert pin['schema']=='NL2_HU_B209_RANK46_ORIGINAL_B3_9S6H3D_GTO_PARENT_PIN_V1'
    assert pin['source_run_id']==RUN and pin['original_B3_archive_sha256']==sha(ROOT/'solver_evidence/NL2_MULTIBOARD_B3.json.gz')
    assert (pin['spot'],pin['flop'],pin['turn'],pin['original_GTO_flop_line'],pin['exact_turn_line'])==(
        SPOT,FLOP,TURN,LINE,LINE+'/x')
    assert pin['target_rank']==46 and pin['model_id']=='ln-iso-lmp_t_model-17z0wyl' and pin['actor']==1
    assert pin['exact_turn_line']=='x b50 c/x'
    assert pin['original_full_GTO_flop_not_recomputed'] is True
    assert pin['assumed_limped_preflop_169class_not_observed'] is True
    artifact=args.gto_artifact_root.resolve()
    mfile=artifact/f'evidence/LMP_CO_BB-gto-{FLOP}.json'
    root=artifact/f'solver/postflop/out/LMP_CO_BB/gto/{FLOP}_multiboard.json'
    jobfile=root.with_suffix('.job.json')
    assert all(p.is_file() for p in (mfile,root,jobfile))
    assert sha(mfile)==source['original_gto_manifest_sha256']
    assert sha(root)==source['original_gto_root_sha256']
    assert sha(jobfile)==source['original_gto_job_sha256']
    m=json.loads(mfile.read_text())
    fr=json.loads(root.read_text())
    jobroot=json.loads(jobfile.read_text())
    assert m['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
    assert (m['spot'],m['version'],m['flop'])==(SPOT,'gto',FLOP)
    assert m['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
    assert m['no_generic_certification'] and not m['failures']
    assert any(z['line']==LINE and z['turn']==TURN and z['gto_gap_pct']<=.5 for z in m['cases']) and TURN in m['turns']
    assert (m['root_pot_bb'],m['root_remaining_bb'])==(2.5,99.0)
    assert (fr['flop'],fr['pot'],fr['stack'])==(FLOP,250,9900)
    assert (jobroot['pot'],jobroot['stack'])==(250,9900)
    parent_cases=[c for c in m['cases'] if c['line']==LINE and c['turn']==TURN]
    assert len(parent_cases)==1 and parent_cases[0]['gto_gap_pct']<=.5
    assert fr['info']['gto_expl_pct']<=.5
    assert jobroot.get('hero') is None and not jobroot.get('locks')
    assert jobroot['rake_rate']==.05 and jobroot['rake_cap']==1000
    assert all(z in jobroot.get('flop_oop','') for z in SIZES)
    assert all(z in jobroot.get('flop_ip','') for z in SIZES)
    parents=[n for n in fr['nodes'] if n['line']==LINE+'/' and n['board'][-2:]==TURN]
    assert len(parents)==1
    parent=parents[0]
    assert all(any(float(w)>1e-4 for w in seat) for seat in parent['wr'])
    src=args.solver_root.resolve();pf=src/'postflop'
    assert (pf/'pfdriver/target/release/pfdriver').is_file()
    sys.path.insert(0,str(pf/'py'))
    import pipeline,ranges,job
    from solve_hu_assumed_pots import RULES,w_lmp_ip
    assert SPOT in RULES
    prof=RULES[SPOT]
    config={k:prof[k] for k in ('pot','stack','oop','ip','pfr')}
    config['kind']='SRP'  # game geometry, not a claim of raised preflop
    ranges.SPOTS[SPOT]=config
    pipeline.SPOTS[SPOT]=config
    weighted=([1.0 for _ in ranges.NAMES], [float(w_lmp_ip(n)) for n in ranges.NAMES])
    assert len(weighted[0])==len(weighted[1])==169
    assert m['preflop_ranges']['oop_169']==dict(zip(ranges.NAMES,weighted[0]))
    assert m['preflop_ranges']['ip_169']==dict(zip(ranges.NAMES,weighted[1]))
    original_range=job.ranges
    job.ranges=lambda sp,v:weighted if sp==SPOT else original_range(sp,v)
    spot=pipeline.SPOTS[SPOT]
    assert abs(spot['pot']-2.5)<1e-8 and abs(spot['stack']-99.0)<1e-8
    assert spot['pfr']=='ip'
    pool=json.loads((src/'inputs/pool_stats.json').read_text())['NL2']
    assert sha(src/'inputs/pool_stats.json')==m['pool_source_sha256']
    assert m['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
    original_locks=pipeline.lock_list
    pipeline.lock_list=lambda s,v,f:make_fallbacks(s,v,pool,original_locks,f)
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
    clone=out/(FLOP+'_multiboard.json')
    clonejob=clone.with_suffix('.job.json')
    shutil.copy2(root,clone);shutil.copy2(jobfile,clonejob)
    assert sha(clone)==source['original_gto_root_sha256']
    assert sha(clonejob)==source['original_gto_job_sha256']
    actual_locks,locks_meta=pipeline.lock_list(SPOT,'exp_ip',FLOP)
    assert actual_locks and locks_meta
    report=dict(schema='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',
        spot=SPOT,version='exp_ip',flop=FLOP,
        pot_family='LMP',root_pot_bb=2.5,root_remaining_bb=99.0,
        root_spr=round(99.0/2.5,6),preflop_ranges=m['preflop_ranges'],
        n_NL2_hands=pool['hands'],pool_source_sha256=sha(src/'inputs/pool_stats.json'),
        solver_pin=sha(pf/'py/pipeline.py'),
        solver_ranges_sha256=sha(pf/'py/ranges.py'),
        flop_action_sizes=list(SIZES),flop_size_profile='full',
        restricted_tree_assumption=False,allow_OOP_flop_leads=True,
        turn_sizing_mode='default',
        turn_subgame_sizing={'oop':pipeline.SUB['turn_oop'],'ip':pipeline.SUB['turn_ip']},
        selected_lines=[LINE],flop_line_policy='checked-b50only',
        selected_turn_lines=[TURNLINE],turn_line_policy='xxonly',turns=[TURN],
        flop_parent_mode='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK',
        file_flop=str(clone.relative_to(pf)),file_flop_sha256=sha(clone),
        flop_root_jobfile_sha256=sha(clonejob),
        gto_parent_source_sha256=source['original_gto_root_sha256'],
        gto_parent_source_run_id=RUN,
        gto_parent_source_manifest_sha256=source['original_gto_manifest_sha256'],
        original_B209_parent_pin_sha256=sha(PIN),
        original_full_GTO_flop_byte_identical_not_recomputed=True,
        original_B3_GTO_turn_size_menu='default_50pct_and_100pct',
        partial_actor_IP_NL2_turn_size_menu='current_default_50pct_and_100pct',
        NL2_hero_lock_scope='TURN_RIVER_ONLY_FROM_SHA_PINNED_B209_RANK46_B3_GTO',
        locks=[dict(pat=z['pat'],scope=z.get('scope','PINNED_MEASURED_NL2_SOURCE'),
            source=z.get('src'),n=z.get('n')) for z in locks_meta],
        unknown_action_frequency_policy='NL2 observed pooled action-size/street marginals where available; separate assumed defaults, no measured per-hole-card actions.',
        no_generic_certification=True,not_observed_exact_NL2_hero_EV=True,
        cases=[],failures=[],skipped=[],elapsed_seconds=0)
    start=time.monotonic()
    try:
        pipeline.solve_sub(SPOT,'exp_ip',FLOP,fr,LINE,TURN)
        sub=out/(FLOP+'_'+LINE.replace(' ','')+'_'+TURN+'.json')
        if not sub.is_file():raise FileNotFoundError('Authentic Rust B210 turn+river subgame absent')
        data=json.loads(sub.read_text())
        assert data['line0']==LINE and data['turn']==TURN
        assert any(len(n['board'])==8 for n in data['nodes'])
        assert any(len(n['board'])==10 for n in data['nodes'])
        report['cases'].append(dict(line=LINE,turn=TURN,
            source_path=str(sub.relative_to(pf)),source_sha256=sha(sub),
            real_flop_parent_spr=round((fr['stack']-max(parent['bets']))/parent['pot'],6),
            flop_parent_pot_bb=parent['pot']/100,
            flop_parent_effective_remaining_bb=(fr['stack']-max(parent['bets']))/100,
            true_river_nodes=sum(len(n['board'])==10 for n in data['nodes']),
            source_node_count=len(data['nodes']),
            gto_gap_pct=data['info'].get('gto_expl_pct'),
            hero_gap_pct=data['info'].get('hero_gap_pct'),
            lock_stats=data['info'].get('lock_stats',{}),
            status='REAL_B3_GTO_FLOP_TURN_RIVER_PARTIAL_NL2_IP_LOCK'))
    except Exception as e:
        report['failures'].append(dict(error=str(e),traceback=traceback.format_exc()[-1900:]))
    report['elapsed_seconds']=round(time.monotonic()-start,2)
    report['solved_cases']=len(report['cases'])
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(spot=SPOT,flop=FLOP,turn=TURN,flop_line=LINE,
        turn_line=TURNLINE,locked_cases=report['solved_cases'],
        failures=report['failures'],elapsed_seconds=report['elapsed_seconds'],
        original_GTO_root_SHA=source['original_gto_root_sha256']),ensure_ascii=False),flush=True)
    if report['failures'] or report['solved_cases']!=1:raise SystemExit(1)

if __name__=='__main__':
    main()
