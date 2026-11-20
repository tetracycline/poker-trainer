#!/usr/bin/env python3
"""Real HU Rust CFR for disclosed 100bb ISO / limp ranges against measured
NL2 aggregate *facing-bet* frequencies.

This is NOT a model-cell CERT. HU_facing_bet is pot/street-marginal,
not matched action-history samples and NOT observed per-combo frequencies.
Source stats and any unlocked nodes are recorded explicitly.
"""
import argparse, hashlib, importlib, json, pathlib, re, sys, time, traceback

ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from solve_hu_assumed_pots import RULES,w_iso_oop,w_iso_ip,w_lmp_ip,sha

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--solver-root',required=True,type=pathlib.Path)
    p.add_argument('--spot',required=True,choices=['ISO_BTN_CO','LMP_CO_BB'])
    p.add_argument('--flop',default='Ks7h2d')
    p.add_argument('--version',required=True,choices=['exp_ip','exp_oop'])
    p.add_argument('--turn-count',type=int,default=1)
    p.add_argument('--manifest',required=True,type=pathlib.Path)
    a=p.parse_args()
    if a.turn_count not in (1,2,3):p.error('turn-count must be 1..3')
    cards=[a.flop[k:k+2] for k in (0,2,4)]
    if len(a.flop)!=6 or len(set(cards))!=3 or any(not re.fullmatch('[23456789TJQKA][cdhs]',x) for x in cards):
        p.error('Invalid flop')
    root=a.solver_root.resolve();pf=root/'postflop'
    if not (pf/'pfdriver/target/release/pfdriver').is_file():raise SystemExit('Missing compiled authentic Rust driver')
    sys.path.insert(0,str(pf/'py'))
    ranges=importlib.import_module('ranges')
    pipeline=importlib.import_module('pipeline')
    job=importlib.import_module('job')
    pool=json.loads((root/'inputs/pool_stats.json').read_text())['NL2']
    rule=RULES[a.spot]
    config={k:v for k,v in rule.items() if k in ('oop','ip','pot','stack','pfr')}
    config['kind']='SRP'  # engine's action-tree abstraction only; source pot type recorded separately
    ranges.SPOTS[a.spot]=config
    pipeline.SPOTS[a.spot]=config
    orig_range_fn=job.ranges
    handpair=(w_iso_oop,w_iso_ip) if a.spot.startswith('ISO') else (lambda n:1.0,w_lmp_ip)
    ranges2=([float(fn(n)) for n in ranges.NAMES] for fn in handpair)
    oop_weights,ip_weights=list(ranges2)
    job.ranges=lambda spot,version:(oop_weights,ip_weights) if spot==a.spot else orig_range_fn(spot,version)
    proxy_family='SRP' if a.spot.startswith('ISO') else 'limped'
    # Source observations condition on street and pot family only; this is
    # an explicit aggregate proxy for ISO and not a direct ISO-vs-BTN sample.
    assumptions=[]
    for street in (1,2,3):
        facing=pool['HU_facing_bet'][str(street)]
        side=facing['by_pot'][proxy_family]
        against_raise=facing['bettor_vs_raise']
        for kind,stat in [('facing_bet',side),('facing_raise',against_raise)]:
            if int(stat['n'])<500:continue
            last=r'b\d+' if kind=='facing_bet' else 'r'
            pat=r'^(?:[^/]*/){'+str(street-1)+r'}[^/]*'+last+r'$'
            assumptions.append(dict(pat=pat,fold=stat['fold']/100,raise_=stat['raise']/100,
               src='NL2.HU_facing_bet[%s].%s%s'%(street,'by_pot.'+proxy_family if kind=='facing_bet' else 'bettor_vs_raise',''),
               n=int(stat['n']),street=street,scope='ACTUAL_AGGREGATE_NOT_HISTORY_OR_COMBO_CONDITIONAL',
               is_ISO_proxy=bool(a.spot.startswith('ISO'))))
    def model_locks(spot,version,board):
        if version=='gto':return [],[]
        from locks import driver_locks
        return driver_locks(assumptions),assumptions
    pipeline.lock_list=model_locks
    orig_make=pipeline.make_job
    def strict_make(*args,**kw):
        kw['rank']=0.5
        kw['target']=min(float(kw.get('target',0.5)),0.5)
        kw['iters']=2200
        return orig_make(*args,**kw)
    pipeline.make_job=strict_make
    out=pf/'out'/a.spot/a.version
    out.mkdir(parents=True,exist_ok=True)
    manifest=dict(schema='HU_ASSUMED_NL2_AGGREGATE_LOCKED_CFR_V1',
      spot=a.spot,version=a.version,flop=a.flop,turns=pipeline.turns_for(a.flop)[:a.turn_count],
      actual_pool_source='poker-solver/inputs/pool_stats.json',pool_sha256=sha(root/'inputs/pool_stats.json'),
      preflop_assumptions=rule,100bb_initial_stack=True,
      root_pot_bb=rule['pot'],root_stack_bb=rule['stack'],root_spr=round(rule['stack']/rule['pot'],6),
      oop_class_weights=dict(zip(ranges.NAMES,oop_weights)),
      ip_class_weights=dict(zip(ranges.NAMES,ip_weights)),
      matched_aggregate_lock_patterns=assumptions,
      unobserved_combo_assignment='Engine sorts opponents by its own GTO strategy, not observed NL2 hole cards.',
      completely_locked=False,not_certified_generic_model=True,
      pool_data_limitations='Pot-family and street-level marginals; not exact ISO postflop history, and no observed combo-specific frequencies.',
      results=[],failures=[],excluded_zero_reach=[],source_driver_sha256=sha(pf/'pfdriver/src/main.rs'),
      source_engine_sha='9d1509fe5077d019825f833eed04b16d342dfda1')
    t0=time.monotonic()
    try:
        fr=pipeline.solve_flop(a.spot,a.version,a.flop)
        lines=list(dict.fromkeys((pipeline.main_line(fr,a.spot),'x x')))
        for line in lines:
            for turn in manifest['turns']:
                parent=next((n for n in fr['nodes'] if n['line']==line+'/' and n['board'][-2:]==turn),None)
                if parent is None or not parent.get('wr') or any(
                  sum(max(0.,float(v)) for v in side)<=1e-4 for side in parent['wr']):
                    manifest['excluded_zero_reach'].append(dict(line=line,turn=turn))
                    continue
                pipeline.solve_sub(a.spot,a.version,a.flop,fr,line,turn)
                sub=out/(a.flop+'_'+line.replace(' ','')+'_'+turn+'.json')
                if not sub.is_file():raise ValueError('Missing turn/river source '+str(sub))
                d=json.loads(sub.read_text())
                lockstats=d['info'].get('lock_stats',{})
                hero=1 if a.version=='exp_ip' else 0
                base=d['info'].get('ev_gto_vs_pool')
                optimized=d['info'].get('ev_exploit')
                delta=(optimized[hero]-base[hero])/100. if base and optimized else None
                manifest['results'].append(dict(line=line,turn=turn,flop=a.flop,
                  subgame_path=str(sub.relative_to(pf)),subgame_sha256=sha(sub),
                  parent_pot_bb=parent['pot']/100,
                  parent_effective_remaining_bb=(fr['stack']-max(parent['bets']))/100,
                  parent_spr=round((fr['stack']-max(parent['bets']))/parent['pot'],6),
                  raw_node_count=len(d['nodes']),river_node_count=sum(len(n['board'])==10 for n in d['nodes']),
                  gto_gap_pct=d['info'].get('gto_expl_pct'),
                  hero_gap_pct=d['info'].get('hero_gap_pct'),
                  matched_patterns=len(lockstats),lock_stats=lockstats,
                  partial_pool_locked_hero_gain_bb=delta,
                  output_status='REAL_CFR_WITH_COARSE_POOL_MARGINAL_LOCKS_NOT_A_GENERIC_NL2_CERT'))
    except Exception as exc:
        manifest['failures'].append({'error':str(exc),'trace':traceback.format_exc()[-2400:]})
    manifest['elapsed_sec']=round(time.monotonic()-t0,2)
    manifest['solved_cases']=len(manifest['results'])
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'spot':a.spot,'version':a.version,'solved_cases':manifest['solved_cases'],
      'excluded':len(manifest['excluded_zero_reach']),'errors':manifest['failures'],
      'source_pool_stats':len(assumptions),'elapsed_sec':manifest['elapsed_sec']}))
    if manifest['failures']:raise SystemExit(1)
if __name__=='__main__':main()
