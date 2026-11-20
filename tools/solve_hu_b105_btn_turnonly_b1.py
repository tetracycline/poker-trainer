#!/usr/bin/env python3
"""B105: exact 100bb BTN_BB NL2 IP partial turn+river lock from B104
byte-for-byte original GTO As9h2d flop, flop x-b100-call, turn Kd checkcheck.

NO flop resimulation. Existing B1 EXP_IP sources are NOT assumed matching the exact river; only new Rust and pinned GTO can verify.
NL2 observed action-size marginals are NOT conditional private cards.
"""
import argparse,json,pathlib,shutil,sys,time,traceback
from solve_hu_multiboard_100bb import make_fallbacks,sha,SIZES

R=pathlib.Path(__file__).resolve().parents[1]/'data'
PIN=R/'nl2_hu_b104_btn_as9h2d_gto_parent_pin.json'
B1=R/'solver_evidence/NL2_MULTIBOARD_B1.index.json'
SPOT='BTN_BB';FLOP='As9h2d';TURN='Kd';LINE='x b100 c';TURNLINE='x x'
RUN=44666285424

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--solver-root',type=pathlib.Path,required=True)
    parser.add_argument('--gto-artifact-root',type=pathlib.Path,required=True)
    parser.add_argument('--manifest',type=pathlib.Path,required=True)
    args=parser.parse_args()
    pin=json.loads(PIN.read_text());idx=json.loads(B1.read_text())
    assert pin['schema']=='NL2_HU_B104_B1_BTN_AS9H2D_GTO_SHA_PARENT_V1'
    assert pin['result']=='PASS_FULL_ORIGINAL_GTO_PIN'
    assert pin['original_source_run_id']==idx['run_id']==RUN
    assert pin['source_archive_sha256']==idx['gzip_sha256']
    assert pin['preselected_rank']==135 and pin['preselected_model_id']=='ln-ipfr-r_model-3lq5u6'
    assert pin['missing_one_flop']=='As9h2d' and pin['existing_hero_locked_flops']==['Jh9d6s','KsQh4d']
    assert (pin['target_public_flop',pin['target_turn',pin['flop_line'],pin['turn_line'])==(
       FLOP,TURN,LINE,TURNLINE)
    assert pin['original_source_GTO_IP_hero_river_nodes']>0
    artifact=args.gto_artifact_root.resolve()
    rootfile=artifact/'solver/postflop'/pin['original_GTO_file_relative_path']
    jobfile=rootfile.with_suffix('.job.json')
    mfile=artifact/'evidence/BTN_BB-gto-As9h2d.json'
    assert all(z.is_file() for z in (rootfile,jobfile,mfile))
    assert sha(rootfile)==pin['original_GTO_flop_root_sha256']
    assert sha(jobfile)==pin['original_GTO_Rust_job_sha256']
    assert sha(mfile)==pin['original_GTO_manifest_sha256']
    source=json.loads(mfile.read_text())
    fr=json.loads(rootfile.read_text())
    original_job=json.loads(jobfile.read_text())
    assert source['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
    assert (source['spot'],source['version'],source['flop'])==(SPOT,'gto',FLOP)
    assert source['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    assert source['no_generic_certification'] and not source['failures']
    assert (source['root_pot_bb'],source['root_remaining_bb'])==(5.5,97.5)
    assert (fr['flop'],fr['pot'],fr['stack'])==(FLOP,550,9750)
    assert (original_job['pot'],original_job['stack'])==(550,9750)
    assert original_job.get('hero') is None and not original_job.get('locks')
    assert original_job['rake_rate']==0.05 and original_job['rake_cap']==1000
    assert all(x in original_job.get('flop_oop','') for x in SIZES)
    assert all(x in original_job.get('flop_ip','') for x in SIZES)
    assert TURN in fr.get('turns',[])
    roots=[z for z in fr['nodes'] if z['line']==LINE+'/' and z['board'][-2:]==TURN]
    assert len(roots)==1
    parent=roots[0]
    assert all(any(float(w)>1e-4 for w in ws) for ws in parent['wr'])
    src=args.solver_root.resolve()
    pf=src/'postflop'
    assert (pf/'pfdriver/target/release/pfdriver').is_file()
    sys.path.insert(0,str(pf/'py'))
    import pipeline,job
    conf=pipeline.SPOTS[SPOT]
    assert abs(conf['pot']-5.5)<1e-8 and abs(conf['stack']-97.5)<1e-8
    original_locks=pipeline.lock_list
    pool=json.loads((src/'inputs/pool_stats.json').read_text())['NL2']
    assert sha(src/'inputs/pool_stats.json')==source['pool_source_sha256']
    assert sha(src/'v8_build/build/pf_data.json')==source['preflop_ranges']['full_sha256']
    pipeline.lock_list=lambda spot,ver,flop:make_fallbacks(spot,ver,pool,original_locks,flop)
    old_make=pipeline.make_job
    def sized(*pos,**kwargs):
        kwargs['target']=.5;kwargs['rank']=.5;kwargs['iters']=1700
        j=old_make(*pos,**kwargs)
        j['flop_oop']=','.join(SIZES)
        j['flop_ip']=','.join(SIZES)
        j['flop_raise']='3x,a'
        return j
    pipeline.make_job=sized
    pipeline.TURN_LINES=[TURNLINE]
    assert pipeline.turns_for(FLOP)[0]==TURN
    out=pf/'out'/SPOT/'exp_ip'
    out.mkdir(parents=True,exist_ok=True)
    copied=out/(FLOP+'_multiboard.json')
    copied_job=copied.with_suffix('.job.json')
    shutil.copy2(rootfile,copied)
    shutil.copy2(jobfile,copied_job)
    assert sha(copied)==pin['original_GTO_flop_root_sha256']
    assert sha(copied_job)==pin['original_GTO_Rust_job_sha256']
    locks,lockmeta=pipeline.lock_list(SPOT,'exp_ip',FLOP)
    assert locks and lockmeta
    report=dict(
        schema='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',
        spot=SPOT,version='exp_ip',flop=FLOP,
        pot_family='SRP',root_pot_bb=5.5,root_remaining_bb=97.5,root_spr=round(97.5/5.5,6),
        preflop_ranges=source['preflop_ranges'],n_NL2_hands=pool['hands'],
        pool_source_sha256=sha(src/'inputs/pool_stats.json'),
        solver_pin=sha(pf/'py/pipeline.py'),solver_ranges_sha256=sha(pf/'py/ranges.py'),
        flop_action_sizes=list(SIZES),flop_size_profile='full',restricted_tree_assumption=False,
        allow_IP_flop_leads=True,turn_sizing_mode='default',
        turn_subgame_sizing={'oop':pipeline.SUB['turn_oop'],'ip':pipeline.SUB['turn_ip']},
        selected_lines=[LINE],flop_line_policy='checked-b100only',
        selected_turn_lines=[TURNLINE],turn_line_policy='xxonly',turns=[TURN],
        flop_parent_mode='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK',
        file_flop=str(copied.relative_to(pf)),file_flop_sha256=sha(copied),
        flop_root_jobfile_sha256=sha(copied_job),
        gto_parent_source_sha256=pin['original_GTO_flop_root_sha256'],
        gto_parent_source_run_id=RUN,
        gto_parent_source_manifest_sha256=pin['original_GTO_manifest_sha256'],
        original_B104_B1_pin_sha256=sha(PIN),
        original_B1_preexisting_EXP_IP_flop_not_relabelled_as_matching_river=True,
        GTO_flop_byte_identical_and_not_recomputed=True,
        NL2_hero_lock_scope='TURN_RIVER_ONLY_FROM_PINNED_GTO_FLOP_PARENT',
        locks=[dict(pat=x['pat'],scope=x.get('scope','PINNED_MEASURED_NL2_SOURCE'),
                 source=x.get('src'),n=x.get('n')) for x in lockmeta],
        unknown_action_frequency_policy=
          'NL2 observed pooled size/street marginals where sampled; assumed/default otherwise. No observed private-hand conditionals.',
        no_generic_certification=True,not_observed_exact_NL2_hero_EV=True,
        cases=[],failures=[],skipped=[],elapsed_seconds=0)
    t0=time.monotonic()
    try:
        pipeline.solve_sub(SPOT,'exp_ip',FLOP,fr,LINE,TURN)
        sub=out/(FLOP+'_'+LINE.replace(' ','')+'_'+TURN+'.json')
        if not sub.is_file():raise FileNotFoundError('Missing genuine Rust downstream NL2 actor-IP subgame')
        d=json.loads(sub.read_text())
        assert d['line0']==LINE and d['turn']==TURN
        assert any(len(x['board'])==10 for x in d['nodes'])
        report['cases'].append(dict(line=LINE,turn=TURN,
             source_path=str(sub.relative_to(pf)),source_sha256=sha(sub),
             real_flop_parent_spr=round((fr['stack']-max(parent['bets']))/parent['pot'],6),
             flop_parent_pot_bb=parent['pot']/100,
             flop_parent_effective_remaining_bb=(fr['stack']-max(parent['bets']))/100,
             true_river_nodes=sum(len(n['board'])==10 for n in d['nodes']),
             source_node_count=len(d['nodes']),
             gto_gap_pct=d['info'].get('gto_expl_pct'),
             hero_gap_pct=d['info'].get('hero_gap_pct'),
             lock_stats=d['info'].get('lock_stats',{}),
             status='TRUE_B1_SHA_PINNED_GTO_FLOP_TURN_RIVER_PARTIAL_NL2_IP_LOCK'))
    except Exception as e:
        report['failures'].append(dict(error=str(e),traceback=traceback.format_exc()[-1700:]))
    report['elapsed_seconds']=round(time.monotonic()-t0,2)
    report['solved_cases']=len(report['cases'])
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(spot=SPOT,flop=FLOP,turn=TURN,flop_line=LINE,
        source_GTO_flop_SHA256=pin['original_GTO_flop_root_sha256'],
        locked_cases=report['solved_cases'],failures=report['failures'],
        elapsed_seconds=report['elapsed_seconds']),ensure_ascii=False),flush=True)
    if report['failures'] or report['solved_cases']!=1:raise SystemExit(1)

if __name__=='__main__':main()
