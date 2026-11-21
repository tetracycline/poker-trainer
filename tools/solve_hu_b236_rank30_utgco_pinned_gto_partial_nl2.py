#!/usr/bin/env python3
"""B236: SHA-pinned real UTG_CO preflop-CFR + original GTO flop,
genuine Rust downstream NL2 actor-OOP turn/river partial lock.
Use one of THREE preregistered actual flops. Never infer a per-hole-card
NL2 conditional from street/size marginals or upgrade generic textures.
"""
import argparse,hashlib,json,pathlib,shutil,sys,time,traceback
from solve_hu_multiboard_100bb import make_fallbacks,sha,SIZES
from solve_hu_missing_branches import EXTRA_SPOTS
from hu_sequential_cfr_reach import game_reach
D=pathlib.Path(__file__).resolve().parents[1]/'data'
SPOT='UTG_CO';LINE='b50 c';MID='ln-opfr-t_model-1hmsxaw'
PINS={
 '4s4h2d':('B233',44894288118),
 '7s5h3d':('B234',44894366667),
 'KsQh4d':('B235',44894369547),
}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--flop',required=True,choices=PINS)
    ap.add_argument('--solver-root',required=True,type=pathlib.Path)
    ap.add_argument('--gto-artifact-root',required=True,type=pathlib.Path)
    ap.add_argument('--manifest',required=True,type=pathlib.Path)
    a=ap.parse_args()
    flop=a.flop;batch,original_run=PINS[flop]
    pinpath=D/f'nl2_hu_{batch.lower()}_rank30_utgco_{flop}_gto_parent_pin.json'
    idxpath=D/f'solver_evidence/NL2_MULTIBOARD_{batch}_R30_{flop.upper()}_GTO.index.json'
    assert pinpath.is_file() and idxpath.is_file()
    pin=json.loads(pinpath.read_text());idx=json.loads(idxpath.read_text())
    assert (pin['source_run_id'],idx['run_id'])==(original_run,original_run)
    assert (pin['spot'],pin['flop'],pin['flop_line'],pin['turn_line'])==(SPOT,flop,LINE,'')
    assert (pin['target_rank'],pin['model_id'])==(30,MID)
    assert pin['preflop_CFR_pinned_not_observed_NL2_private_card'] is True
    assert pin['original_full_100bb_utgco_gto_source_pinned'] is True
    assert pin['target_exact_actor_OOP_turn_nodes']>0 and pin['target_exact_actor_OOP_turn_strict_combos']>0
    assert idx['exact_target_actor_OOP_turn_nodes']>0 and idx['exact_target_actor_OOP_turn_strict_combos']>0
    assert (idx['verified_cases'],idx['gto_cases'],idx['locked_cases'])==(1,1,0)
    assert idx['original_parent_GTO_root_SHA256']==pin['original_gto_root_sha256']
    assert idx['original_parent_GTO_job_SHA256']==pin['original_gto_job_sha256']
    assert idx['original_parent_GTO_manifest_SHA256']==pin['original_gto_manifest_sha256']
    artifact=a.gto_artifact_root.resolve()
    original_manifest=artifact/f'evidence/{SPOT}-gto-{flop}.json'
    root=artifact/f'solver/postflop/out/{SPOT}/gto/{flop}_multiboard.json'
    jobfile=root.with_suffix('.job.json')
    assert all(p.is_file() for p in (original_manifest,root,jobfile))
    assert sha(original_manifest)==pin['original_gto_manifest_sha256']
    assert sha(root)==pin['original_gto_root_sha256']
    assert sha(jobfile)==pin['original_gto_job_sha256']
    manifest=json.loads(original_manifest.read_text())
    fr=json.loads(root.read_text());rootjob=json.loads(jobfile.read_text())
    assert (manifest['spot'],manifest['version'],manifest['flop'])==(SPOT,'gto',flop)
    assert manifest['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    assert manifest['selected_lines']==[LINE] and manifest['turns']==[pin['turn']]
    assert manifest['preflop_ranges']['full_sha256']
    assert (manifest['root_pot_bb'],manifest['root_remaining_bb'])==(6.5,97.5)
    assert (fr['flop'],fr['pot'],fr['stack'])==(flop,650,9750)
    assert (rootjob['pot'],rootjob['stack'],rootjob['rake_rate'],rootjob['rake_cap'])==(650,9750,.05,1000)
    assert rootjob.get('hero') is None and not rootjob.get('locks')
    assert fr['info'].get('gto_expl_pct') is not None and float(fr['info']['gto_expl_pct'])<=.5
    assert all(z in rootjob['flop_oop'] for z in SIZES)
    parent=[n for n in fr['nodes'] if n['line']==LINE+'/' and n['board'][-2:]==pin['turn']]
    assert len(parent)==1 and all(any(float(w)>1e-4 for w in seat) for seat in parent[0]['wr'])
    src=a.solver_root.resolve();pf=src/'postflop'
    assert (pf/'pfdriver/target/release/pfdriver').is_file()
    assert sha(src/'v8_build/build/pf_data.json')==manifest['preflop_ranges']['full_sha256']
    assert sha(src/'inputs/pool_stats.json')==manifest['pool_source_sha256']
    sys.path.insert(0,str(pf/'py'))
    import pipeline,ranges,job
    config=EXTRA_SPOTS[SPOT]
    ranges.SPOTS[SPOT]=config;pipeline.SPOTS[SPOT]=config
    pool=json.loads((src/'inputs/pool_stats.json').read_text())['NL2']
    original_locks=pipeline.lock_list
    pipeline.lock_list=lambda s,v,f:make_fallbacks(s,v,pool,original_locks,f)
    old_make=pipeline.make_job
    def make(*pos,**kwargs):
        kwargs['target']=.5;kwargs['rank']=.5;kwargs['iters']=1700
        j=old_make(*pos,**kwargs)
        j['flop_oop']=','.join(SIZES);j['flop_ip']=','.join(SIZES)
        j['flop_raise']='3x,a'
        return j
    pipeline.make_job=make
    pipeline.TURN_LINES=['x x']
    assert pipeline.turns_for(flop)[0]==pin['turn']
    out=pf/'out'/SPOT/'exp_oop'
    out.mkdir(parents=True,exist_ok=True)
    clone=out/(flop+'_multiboard.json')
    clonejob=clone.with_suffix('.job.json')
    shutil.copy2(root,clone);shutil.copy2(jobfile,clonejob)
    assert sha(clone)==pin['original_gto_root_sha256']
    assert sha(clonejob)==pin['original_gto_job_sha256']
    actual_locks,locks_meta=pipeline.lock_list(SPOT,'exp_oop',flop)
    assert actual_locks and locks_meta
    report=dict(schema='NL2_HU_B236_TRUE_PINNED_UTG_CO_GTO_FLOP_PARTIAL_NL2_OOP_V1',
        target_rank=30,model_id=MID,spot=SPOT,flop=flop,turn=pin['turn'],
        flop_line=LINE,exact_target_line=LINE+'/',version='exp_oop',
        original_GTO_source_batch=batch,original_GTO_source_run_id=original_run,
        original_GTO_flop_root_sha256=pin['original_gto_root_sha256'],
        original_GTO_job_sha256=pin['original_gto_job_sha256'],
        original_GTO_manifest_sha256=pin['original_gto_manifest_sha256'],
        original_GTO_pin_sha256=sha(pinpath),
        source_preflop='PINNED_POKER_SOLVER_PREFLOP_CFR',
        no_observed_private_card_NL2_rates=True,
        original_GTO_flop_unchanged=True,
        original_GTO_flop_full_sizing_not_reoptimized=True,
        partially_locked_turn_river_only=True,
        locks=[dict(pat=z['pat'],source_scope=z.get('scope'),n=z.get('n'),
               source=z.get('src')) for z in locks_meta],
        genuine_GTO_parent_actor_turn_strict_combos=pin['target_exact_actor_OOP_turn_strict_combos'],
        cases=[],failures=[],elapsed_seconds=None,no_generic_CERT_upgrade=True,
        PR2_Draft_NEVER_MERGE=True)
    start=time.monotonic()
    try:
        pipeline.solve_sub(SPOT,'exp_oop',flop,fr,LINE,pin['turn'])
        sub=out/(flop+'_'+LINE.replace(' ','')+'_'+pin['turn']+'.json')
        sjob=sub.with_suffix('.job.json')
        if not sub.is_file() or not sjob.is_file():
            raise FileNotFoundError('Original Rust B236 actor-OOP turn+river source absent')
        raw=json.loads(sub.read_text());sj=json.loads(sjob.read_text())
        assert raw['line0']==LINE and raw['turn']==pin['turn']
        assert sj['hero']==0 and sj.get('locks')
        assert (sj['pot'],sj['rake_rate'],sj['rake_cap'])==(parent[0]['pot'],.05,1000)
        assert any(len(n['board'])==8 for n in raw['nodes'])
        assert any(len(n['board'])==10 for n in raw['nodes'])
        seq,stats=game_reach(fr,raw)
        selected=[]
        for n in raw['nodes']:
            if n['line']!=LINE+'/' or n['player']!=0 or len(n['board'])!=8:continue
            q=seq['|'.join((n['board'],n['line'],'0'))]
            if q['count']<=0:continue
            spr=(raw['stack']-max(n['bets']))/n['pot']
            selected.append(dict(public_board=n['board'],strict_combos=q['count'],
                actual_spr=spr,relative_spr_error_pct=100*abs(spr-7.25)/7.25,
                permitted_actions=n['acts']))
        report['cases'].append(dict(
            flop=flop,turn=pin['turn'],exact_action_line=LINE+'/',
            original_Rust_exp_subgame_path=str(sub.relative_to(pf)),
            source_sha256=sha(sub),original_exp_job_sha256=sha(sjob),
            hero_actor_OOP_turn_nodes=len(selected),
            strictly_reachable_actor_turn_combos=sum(n['strict_combos'] for n in selected),
            model_SPR_eligible_actor_turn_combos=sum(n['strict_combos'] for n in selected
                if n['relative_spr_error_pct']<=5),
            actual_turn_nodes=selected,
            source_node_count=len(raw['nodes']),true_river_nodes=sum(len(n['board'])==10 for n in raw['nodes']),
            lock_stats=raw['info'].get('lock_stats',{}),
            hero_gap_pct=raw['info'].get('hero_gap_pct'),
            GTO_flop_exploitability_pct=fr['info'].get('gto_expl_pct'),
            sequential_gate_stats=dict(stats)))
    except Exception as e:
        report['failures'].append(dict(error=str(e),traceback=traceback.format_exc()[-2000:]))
    report['elapsed_seconds']=round(time.monotonic()-start,2)
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(batch='B236',flop=flop,locked_cases=len(report['cases']),
        strict_actor_combos=report['cases'][0]['model_SPR_eligible_actor_turn_combos'] if report['cases'] else None,
        failures=report['failures'],elapsed=report['elapsed_seconds'])),flush=True)
    if report['failures'] or len(report['cases'])!=1:raise SystemExit(1)
if __name__=='__main__':main()
