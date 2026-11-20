#!/usr/bin/env python3
"""B108 genuine IP NL2 partial turn-river lock from original B2 GTO root.

Original run 44666290556 failed as a WHOLE due an unrelated SB3_BTN job;
CO_BB Js9h4d original GTO was individually verified (B2_PARTIAL).
This script copies the full 100bb GTO flop root+job byte-for-byte, then
solves ONLY turn Ts (x-b100-call) and river with authentic pinned Rust CFR,
using observed NL2 aggregate marginals and explicitly assumed defaults.
Never infer observed per-private-card NL2 behavior.
"""
import argparse,json,pathlib,shutil,sys,time,traceback
from solve_hu_multiboard_100bb import make_fallbacks,sha,SIZES

R=pathlib.Path(__file__).resolve().parents[1]/'data'
PIN=R/'nl2_hu_b107_co_js9h4d_b2_gto_parent_pin.json'
INDEX=R/'solver_evidence/NL2_MULTIBOARD_B2_PARTIAL.index.json'
SPOT='CO_BB';FLOP='Js9h4d';TURN='Ts'
LINE='x b33 c';TURNLINE='x b100 c';RUN=44666290556

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--solver-root',type=pathlib.Path,required=True)
    parser.add_argument('--gto-artifact-root',type=pathlib.Path,required=True)
    parser.add_argument('--manifest',type=pathlib.Path,required=True)
    args=parser.parse_args()
    pinned=json.loads(PIN.read_text())
    idx=json.loads(INDEX.read_text())
    assert pinned['schema']=='NL2_HU_B107_CO_B2_JS9H4D_GTO_PARENT_V1'
    assert pinned['result']=='PASS_INDIVIDUALLY_VERIFIED_B2_GTO_ARTIFACT'
    assert pinned['original_source_run_id']==idx['run_id']==RUN
    assert pinned['B2_PARTIAL_source_archive_SHA256']==idx['gzip_sha256']
    assert pinned['full_B2_workflow_failed_unrelated_job'] is True
    assert pinned['B2_failed_SB3_BTN_GTO_job_explicitly_excluded'] is True
    assert pinned['frozen_targets']==[215,220]
    assert (pinned['public_flop'],pinned['turn'],pinned['flop_line'],pinned['turn_line'])==(
        FLOP,TURN,LINE,TURNLINE)
    assert pinned['original_GTO_positive_strict_IP_actor_node_count']>0
    original=args.gto_artifact_root.resolve()
    manifest=original/'evidence/CO_BB-gto-Js9h4d.json'
    root=original/'solver/postflop'/pinned['original_GTO_flop_relative_path']
    rootjob=root.with_suffix('.job.json')
    assert all(x.is_file() for x in (manifest,root,rootjob))
    assert sha(manifest)==pinned['original_manifest_SHA256']
    assert sha(root)==pinned['original_GTO_flop_SHA256']
    assert sha(rootjob)==pinned['original_GTO_job_SHA256']
    source=json.loads(manifest.read_text())
    fr=json.loads(root.read_text());jobroot=json.loads(rootjob.read_text())
    assert source['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
    assert (source['spot'],source['version'],source['flop'])==(SPOT,'gto',FLOP)
    assert source['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    assert source['no_generic_certification'] is True and not source['failures']
    assert (source['root_pot_bb'],source['root_remaining_bb'])==(5.5,97.5)
    assert (fr['flop'],fr['pot'],fr['stack'])==(FLOP,550,9750)
    assert (jobroot['pot'],jobroot['stack'])==(550,9750)
    assert jobroot.get('hero') is None and not jobroot.get('locks')
    assert jobroot['rake_rate']==0.05 and jobroot['rake_cap']==1000
    assert all(x in jobroot.get('flop_oop','') for x in SIZES)
    assert all(x in jobroot.get('flop_ip','') for x in SIZES)
    assert TURN in fr.get('turns',[])
    parents=[n for n in fr['nodes'] if n['line']==LINE+'/' and n['board'][-2:]==TURN]
    assert len(parents)==1
    parent=parents[0]
    assert all(any(float(w)>1e-4 for w in ws) for ws in parent['wr'])
    src=args.solver_root.resolve()
    pf=src/'postflop'
    assert (pf/'pfdriver/target/release/pfdriver').is_file()
    sys.path.insert(0,str(pf/'py'))
    import pipeline
    prof=pipeline.SPOTS[SPOT]
    assert abs(prof['pot']-5.5)<1e-8 and abs(prof['stack']-97.5)<1e-8
    pool=json.loads((src/'inputs/pool_stats.json').read_text())['NL2']
    assert sha(src/'inputs/pool_stats.json')==source['pool_source_sha256']
    assert sha(src/'v8_build/build/pf_data.json')==source['preflop_ranges']['full_sha256']
    original_locks=pipeline.lock_list
    pipeline.lock_list=lambda s,v,f:make_fallbacks(s,v,pool,original_locks,f)
    raw_make=pipeline.make_job
    def make(*pos,**kwargs):
        kwargs['target']=.5
        kwargs['rank']=.5
        kwargs['iters']=1700
        j=raw_make(*pos,**kwargs)
        j['flop_oop']=','.join(SIZES)
        j['flop_ip']=','.join(SIZES)
        j['flop_raise']='3x,a'
        return j
    pipeline.make_job=make
    pipeline.TURN_LINES=[TURNLINE]
    assert pipeline.turns_for(FLOP)[0]==TURN
    out=pf/'out'/SPOT/'exp_ip'
    out.mkdir(parents=True,exist_ok=True)
    rootCopy=out/(FLOP+'_multiboard.json')
    rootCopyJob=rootCopy.with_suffix('.job.json')
    shutil.copy2(root,rootCopy)
    shutil.copy2(rootjob,rootCopyJob)
    assert sha(rootCopy)==pinned['original_GTO_flop_SHA256']
    assert sha(rootCopyJob)==pinned['original_GTO_job_SHA256']
    locks,lockmeta=pipeline.lock_list(SPOT,'exp_ip',FLOP)
    assert locks and lockmeta, 'No true source or explicit assumed NL2 partial lock config'
    report=dict(
        schema='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',
        spot=SPOT,version='exp_ip',flop=FLOP,
        pot_family='SRP',root_pot_bb=5.5,root_remaining_bb=97.5,
        root_spr=round(97.5/5.5,6),
        preflop_ranges=source['preflop_ranges'],n_NL2_hands=pool['hands'],
        pool_source_sha256=sha(src/'inputs/pool_stats.json'),
        solver_pin=sha(pf/'py/pipeline.py'),solver_ranges_sha256=sha(pf/'py/ranges.py'),
        flop_action_sizes=list(SIZES),flop_size_profile='full',
        restricted_tree_assumption=False,allow_OOP_flop_leads=True,
        turn_sizing_mode='default',
        turn_subgame_sizing={'oop':pipeline.SUB['turn_oop'],'ip':pipeline.SUB['turn_ip']},
        selected_lines=[LINE],flop_line_policy='checked-b33only',
        selected_turn_lines=[TURNLINE],turn_line_policy='xb100only',turns=[TURN],
        flop_parent_mode='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK',
        file_flop=str(rootCopy.relative_to(pf)),file_flop_sha256=sha(rootCopy),
        flop_root_jobfile_sha256=sha(rootCopyJob),
        gto_parent_source_sha256=pinned['original_GTO_flop_SHA256'],
        gto_parent_source_run_id=RUN,
        gto_parent_source_manifest_sha256=pinned['original_manifest_SHA256'],
        original_B107_individually_verified_GTO_pin_sha256=sha(PIN),
        whole_B2_workflow_failed_but_parent_GTO_individually_verified=True,
        excluded_B2_unrelated_failed_SB3_source=True,
        original_B2_GTO_flop_byte_identical_not_recomputed=True,
        NL2_hero_lock_scope='TURN_RIVER_ONLY_FROM_PINNED_ORIGINAL_B2_GTO',
        locks=[dict(pat=x['pat'],scope=x.get('scope','PINNED_MEASURED_NL2_SOURCE'),
                source=x.get('src'),n=x.get('n')) for x in lockmeta],
        unknown_action_frequency_policy=
            'Only observed NL2 pooled size/street marginal where present, explicit assumed defaults otherwise; no observed private-hand conditional.',
        no_generic_certification=True,not_observed_exact_NL2_hero_EV=True,
        cases=[],failures=[],skipped=[],elapsed_seconds=0)
    t0=time.monotonic()
    try:
        pipeline.solve_sub(SPOT,'exp_ip',FLOP,fr,LINE,TURN)
        sub=out/(FLOP+'_'+LINE.replace(' ','')+'_'+TURN+'.json')
        if not sub.is_file():raise FileNotFoundError('Authentic Rust IP turn+river subgame missing')
        d=json.loads(sub.read_text())
        assert d['line0']==LINE and d['turn']==TURN
        assert any(len(n['board'])==10 for n in d['nodes'])
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
          status='B2_PINNED_ORIGINAL_FULL_GTO_FLOP_GENUINE_TURN_RIVER_NL2_IP_MARGINAL_LOCK'))
    except Exception as err:
        report['failures'].append(dict(error=str(err),traceback=traceback.format_exc()[-1950:]))
    report['elapsed_seconds']=round(time.monotonic()-t0,2)
    report['solved_cases']=len(report['cases'])
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(spot=SPOT,flop=FLOP,turn=TURN,flop_line=LINE,
        turn_line=TURNLINE,locked_cases=report['solved_cases'],
        failures=report['failures'],elapsed_seconds=report['elapsed_seconds'],
        original_flop_SHA256=pinned['original_GTO_flop_SHA256']),ensure_ascii=False),flush=True)
    if report['failures'] or report['solved_cases']!=1:raise SystemExit(1)

if __name__=='__main__':main()
