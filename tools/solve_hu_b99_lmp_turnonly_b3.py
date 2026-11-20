#!/usr/bin/env python3
"""B99: authentic NL2 OOP partial turn/river lock, *no flop solve*.

B98 SHA-frozen full-size ORIGINAL B3 LMP GTO flop/root/range is copied
byte-for-byte from run 44666294821. Only the downstream 8s8h3d / turn 5s
x-x / x-x turn continuation is solved via pinned Rust CFR. Pool frequencies
are aggregate marginals, not observed conditional private-hole-card policies.
"""
import argparse,hashlib,json,pathlib,shutil,sys,time,traceback
from solve_hu_multiboard_100bb import make_fallbacks,sha,SIZES
from solve_hu_assumed_pots import RULES,w_lmp_ip

R=pathlib.Path('data')
PIN=R/'nl2_hu_b98_lmp_8s8h3d_gto_parent_pin.json'
B3=R/'solver_evidence/NL2_MULTIBOARD_B3.index.json'
SPOT='LMP_CO_BB';FLOP='8s8h3d';TURN='5s';LINE='x x'
RUN=44666294821

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--solver-root',required=True,type=pathlib.Path)
    parser.add_argument('--gto-artifact-root',required=True,type=pathlib.Path)
    parser.add_argument('--manifest',required=True,type=pathlib.Path)
    args=parser.parse_args()
    pin=json.loads(PIN.read_text())
    idx=json.loads(B3.read_text())
    assert pin['schema']=='NL2_HU_B98_LMP_B3_8S8H3D_FROZEN_PARENT_V1'
    assert pin['result']=='PASS_GTO_ROOT_PIN'
    assert pin['source_run_id']==idx['run_id']==RUN
    assert pin['source_archive_gzip_sha256']==idx['gzip_sha256']
    assert pin['frozen_rank_targets']==[77,78]
    assert pin['GTO_verified_river_OOP_actor_nodes']>0
    assert (pin['public_flop'],pin['turn'],pin['flop_line'],pin['turn_line'])==(FLOP,TURN,LINE,LINE)
    artifact=args.gto_artifact_root.resolve()
    rootfile=artifact/'solver/postflop'/pin['original_GTO_file_relative_path']
    jobfile=rootfile.with_suffix('.job.json')
    manifest=artifact/f'evidence/{SPOT}-gto-{FLOP}.json'
    assert all(x.is_file() for x in (rootfile,jobfile,manifest))
    assert sha(rootfile)==pin['original_GTO_flop_sha256']
    assert sha(jobfile)==pin['original_GTO_flop_job_sha256']
    assert sha(manifest)==pin['original_manifest_sha256']
    source=json.loads(manifest.read_text())
    fr=json.loads(rootfile.read_text());original_job=json.loads(jobfile.read_text())
    assert source['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
    assert (source['spot'],source['version'],source['flop'])==(SPOT,'gto',FLOP)
    assert source['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
    assert len(source['preflop_ranges']['oop_169'])==169
    assert len(source['preflop_ranges']['ip_169'])==169
    assert source['no_generic_certification'] and not source['failures']
    assert (source['root_pot_bb'],source['root_remaining_bb'])==(2.5,99)
    assert (fr['flop'],fr['pot'],fr['stack'])==(FLOP,250,9900)
    assert (original_job['pot'],original_job['stack'])==(250,9900)
    assert original_job.get('hero') is None and not original_job.get('locks')
    assert abs(original_job['rake_rate']-.05)<1e-8 and original_job['rake_cap']==1000
    assert all(n in original_job.get('flop_oop','') for n in SIZES)
    assert all(n in original_job.get('flop_ip','') for n in SIZES)
    assert TURN in fr.get('turns',[])
    parent=[n for n in fr['nodes'] if n['line']==LINE+'/' and n['board'][-2:]==TURN]
    assert len(parent)==1
    parent=parent[0]
    assert all(any(float(w)>1e-4 for w in seat) for seat in parent['wr'])
    src=args.solver_root.resolve()
    pf=src/'postflop'
    assert (pf/'pfdriver/target/release/pfdriver').is_file(), 'Real pinned Rust driver binary absent'
    sys.path.insert(0,str(pf/'py'))
    import pipeline,ranges,job
    base={k:RULES[SPOT][k] for k in ('pot','stack','oop','ip','pfr')}
    base['kind']='SRP'
    assert base['pot']==2.5 and base['stack']==99
    ranges.SPOTS[SPOT]=base
    pipeline.SPOTS[SPOT]=base
    weights=([1.0 for _ in ranges.NAMES],[float(w_lmp_ip(x)) for x in ranges.NAMES])
    assert len(weights[0])==len(weights[1])==169
    old_ranges=job.ranges
    job.ranges=lambda spot,version:weights if spot==SPOT else old_ranges(spot,version)
    original_locks=pipeline.lock_list
    pool=json.loads((src/'inputs/pool_stats.json').read_text())['NL2']
    assert sha(src/'inputs/pool_stats.json')==source['pool_source_sha256']
    pipeline.lock_list=lambda spot,ver,flop:make_fallbacks(spot,ver,pool,original_locks,flop)
    before_make=pipeline.make_job
    def sized(*pos,**kwargs):
        kwargs['target']=.5;kwargs['rank']=.5;kwargs['iters']=1700
        j=before_make(*pos,**kwargs)
        j['flop_oop']=','.join(SIZES)
        j['flop_ip']=','.join(SIZES)
        j['flop_raise']='3x,a'
        return j
    pipeline.make_job=sized
    pipeline.TURN_LINES=[LINE]
    actual_turns=pipeline.turns_for(FLOP)
    assert actual_turns and actual_turns[0]==TURN
    out=pf/'out'/SPOT/'exp_oop'
    out.mkdir(parents=True,exist_ok=True)
    copy=out/(FLOP+'_multiboard.json')
    copyjob=copy.with_suffix('.job.json')
    shutil.copy2(rootfile,copy)
    shutil.copy2(jobfile,copyjob)
    assert sha(copy)==pin['original_GTO_flop_sha256']
    assert sha(copyjob)==pin['original_GTO_flop_job_sha256']
    locks,lockmeta=pipeline.lock_list(SPOT,'exp_oop',FLOP)
    assert locks and lockmeta, 'Frozen NL2 pool provides no marginal/assumed opponent locks'
    report=dict(
       schema='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',
       spot=SPOT,version='exp_oop',flop=FLOP,
       pot_family='LMP',root_pot_bb=2.5,root_remaining_bb=99.,root_spr=39.6,
       preflop_ranges=source['preflop_ranges'],n_NL2_hands=pool['hands'],
       pool_source_sha256=sha(src/'inputs/pool_stats.json'),
       solver_pin=sha(pf/'py/pipeline.py'),solver_ranges_sha256=sha(pf/'py/ranges.py'),
       flop_action_sizes=list(SIZES),flop_size_profile='full',restricted_tree_assumption=False,
       allow_OOP_flop_leads=True,turn_sizing_mode='default',
       turn_subgame_sizing={'oop':pipeline.SUB['turn_oop'],'ip':pipeline.SUB['turn_ip']},
       selected_lines=[LINE],flop_line_policy='checkcheck',
       selected_turn_lines=[LINE],turn_line_policy='xxonly',turns=[TURN],
       flop_parent_mode='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK',
       file_flop=str(copy.relative_to(pf)),file_flop_sha256=sha(copy),
       flop_root_jobfile_sha256=sha(copyjob),
       gto_parent_source_sha256=pin['original_GTO_flop_sha256'],
       gto_parent_source_run_id=RUN,
       gto_parent_source_manifest_sha256=pin['original_manifest_sha256'],
       original_immutable_B3_B98_pin_sha256=sha(PIN),
       original_B3_unchanged_GTO_flop_parent=True,
       NL2_hero_lock_scope='TURN_RIVER_ONLY_WITH_FIXED_GTO_FLOP_REACH',
       root_GTO_169class_preflop_assumed_not_measured=True,
       locks=[dict(pat=z['pat'],scope=z.get('scope','PINNED_MEASURED_NL2_SOURCE'),
                   source=z.get('src'),n=z.get('n')) for z in lockmeta],
       unknown_action_frequency_policy=
         'NL2 pooled street/bet-size marginals only; unknown exact private hand conditions labeled ASSUMED',
       no_generic_certification=True,not_observed_exact_NL2_hero_EV=True,
       cases=[],failures=[],skipped=[],elapsed_seconds=0)
    t0=time.monotonic()
    try:
        pipeline.solve_sub(SPOT,'exp_oop',FLOP,fr,LINE,TURN)
        sub=out/(FLOP+'_'+LINE.replace(' ','')+'_'+TURN+'.json')
        if not sub.is_file():
            raise FileNotFoundError('Authentic pinned Rust downstream turn/river subgame missing')
        solved=json.loads(sub.read_text())
        assert solved['line0']==LINE and solved['turn']==TURN
        assert any(len(n['board'])==10 for n in solved['nodes'])
        report['cases'].append(dict(line=LINE,turn=TURN,
           source_path=str(sub.relative_to(pf)),source_sha256=sha(sub),
           real_flop_parent_spr=round((fr['stack']-max(parent['bets']))/parent['pot'],6),
           flop_parent_pot_bb=parent['pot']/100,
           flop_parent_effective_remaining_bb=(fr['stack']-max(parent['bets']))/100,
           true_river_nodes=sum(len(n['board'])==10 for n in solved['nodes']),
           source_node_count=len(solved['nodes']),
           gto_gap_pct=solved['info'].get('gto_expl_pct'),
           hero_gap_pct=solved['info'].get('hero_gap_pct'),
           lock_stats=solved['info'].get('lock_stats',{}),
           status='NL2_TURN_ONLY_PARTIAL_LOCK_FROM_IMMUTABLE_LMP_GTO_FLOP_PARENT'))
    except Exception as err:
        report['failures'].append(dict(error=str(err),traceback=traceback.format_exc()[-2000:]))
    report['elapsed_seconds']=round(time.monotonic()-t0,2)
    report['solved_cases']=len(report['cases'])
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(run=RUN,spot=SPOT,flop=FLOP,turn=TURN,
        cases=report['solved_cases'],failures=report['failures'],
        elapsed_seconds=report['elapsed_seconds'],
        original_flop_parent_SHA256=pin['original_GTO_flop_sha256']),ensure_ascii=False),flush=True)
    if report['failures'] or report['solved_cases']!=1:raise SystemExit(1)

if __name__=='__main__':main()
