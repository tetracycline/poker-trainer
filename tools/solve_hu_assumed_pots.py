#!/usr/bin/env python3
"""Genuine postflop CFR on explicitly assumed NL2 100bb ISO/LMP profiles.

NOT CERT for live NL2: 169-class starting weights were selected BEFORE this
solve. Real postflop actions/SPR/CFR outputs are hashes and not generalized
across different pot families, histories, or assumed source ranges.
"""
import argparse
import hashlib
import importlib
import json
import pathlib
import sys
import time
import traceback

ROOT=pathlib.Path(__file__).resolve().parent
RULES={
 'ISO_BTN_CO':dict(pot=9.5,stack=96.0,oop='CO',ip='BTN',kind='ISO',pfr='ip',
    description='CO limp(1bb), BTN iso to 4bb, CO calls; SB 0.5bb+BB 1bb dead',
    ip_policy='isolation top 22% with suited broadways, medium pairs and selected suited connectors',
    oop_policy='CO limp/call 28% broadways, small pairs and suited connectors'),
 'LMP_CO_BB':dict(pot=2.5,stack=99.0,oop='BB',ip='CO',kind='LMP',pfr='ip',
    description='CO open-limp(1bb), SB dead 0.5bb, BB checks(1bb)',
    ip_policy='CO limp 35% pairs, suited hands and offsuit broadways',
    oop_policy='BB checks with any otherwise-unraised 2-card hand'),
}
RANKS='23456789TJQKA'
def is_adjacent(a,b):return abs(RANKS.index(a)-RANKS.index(b))<=2

def w_iso_ip(n):
    if len(n)==2: return 1.0 if RANKS.index(n[0])>=5 else 0.25
    h,l,s=n[0],n[1],n[2];ri=RANKS.index(h);li=RANKS.index(l)
    if s=='s':
        if h=='A' and li>=5:return 1.0
        if h in 'KQJ' and li>=7:return 1.0
        if is_adjacent(h,l) and li>=5:return 0.5
        if h=='A':return 0.5
        return 0.0
    if h=='A' and li>=9:return 1.0
    if h in 'KQ' and li>=9:return 0.75
    return 0.0

def w_iso_oop(n):
    if len(n)==2: return 1.0 if RANKS.index(n[0])<=9 else 0.35
    h,l,s=n[0],n[1],n[2];li=RANKS.index(l)
    if s=='s':
        if h=='A':return 0.9
        if h in 'KQJ' and li>=5:return 0.85
        if is_adjacent(h,l) and li>=2:return 0.75
        return 0.2
    if h=='A' and li>=5:return 0.75
    if h=='K' and li>=8:return 0.7
    if h=='Q' and li>=8:return 0.5
    return 0.0

def w_lmp_ip(n):
    if len(n)==2:return 1.0
    h,l,s=n[0],n[1],n[2];li=RANKS.index(l)
    if s=='s':return 1.0 if h in 'AKQJ' or is_adjacent(h,l) else 0.45
    if h=='A':return 0.9 if li>=3 else 0.4
    if h in 'KQJ' and li>=5:return 0.6
    return 0.0

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for buf in iter(lambda:f.read(1024*1024),b''):h.update(buf)
    return h.hexdigest()

def main():
    q=argparse.ArgumentParser()
    q.add_argument('--solver-root',type=pathlib.Path,required=True)
    q.add_argument('--spot',choices=list(RULES),required=True)
    q.add_argument('--flop-start',type=int,default=0)
    q.add_argument('--turn-count',type=int,default=1)
    q.add_argument('--manifest',type=pathlib.Path,required=True)
    a=q.parse_args()
    pf=a.solver_root.resolve()/'postflop'
    if not (pf/'pfdriver/target/release/pfdriver').exists():raise SystemExit('Real CFR engine not built')
    sys.path.insert(0,str(pf/'py'))
    ranges=importlib.import_module('ranges')
    job=importlib.import_module('job')
    pipeline=importlib.import_module('pipeline')
    src=RULES[a.spot]
    rprof={k:v for k,v in src.items() if k in ('pot','stack','oop','ip','pfr')}
    rprof['kind']='SRP'  # underlying tree shape; NOT a declaration that the pot is SRP
    ranges.SPOTS[a.spot]=rprof
    pipeline.SPOTS[a.spot]=rprof
    pipeline.NFLOP[a.spot]=6
    pipeline.OFFS[a.spot]=0.41 if a.spot.startswith('ISO') else 0.71
    policy=(w_iso_oop,w_iso_ip) if a.spot.startswith('ISO') else (lambda n:1.0,w_lmp_ip)
    w0=[float(policy[0](n)) for n in ranges.NAMES]
    w1=[float(policy[1](n)) for n in ranges.NAMES]
    if not sum(w0) or not sum(w1):raise ValueError('Range empty')
    # job.make_job looks up ranges() from the module global dictionary.
    job.ranges=lambda spot,ver:(w0,w1) if spot==a.spot and ver=='gto' else ranges.ranges(spot,ver)
    flop=pipeline.flops_for(a.spot)[a.flop_start]
    turns=pipeline.turns_for(flop)[:a.turn_count]
    if not turns:raise ValueError('No turn cards')
    report=dict(schema='HU_ASSUMED_RANGES_ACTUAL_CFR_V1',spot=a.spot,kind=src['kind'],
      preflop_history=src['description'],range_assumption=src,
      effective_stack_bb=100.0,starting_pot_bb=src['pot'],starting_remaining_bb=src['stack'],
      root_spr=round(src['stack']/src['pot'],5),
      oop_169_class_weights=dict(zip(ranges.NAMES,w0)),ip_169_class_weights=dict(zip(ranges.NAMES,w1)),
      source_range_sha256=sha(pf/'py/ranges.py'),source_driver_sha256=sha(pf/'pfdriver/src/main.rs'),
      source_pipeline_sha256=sha(pf/'py/pipeline.py'),flop=flop,turns=turns,
      version='gto',cases=[],failures=[],not_CERT_or_EST_for_NL2=True)
    t0=time.monotonic()
    try:
        fr=pipeline.solve_flop(a.spot,'gto',flop)
        main=pipeline.main_line(fr,a.spot)
        for line in list(dict.fromkeys((main,'x x'))):
            for turn in turns:
                parent=next((n for n in fr['nodes'] if n['line']==line+'/' and n['board'][-2:]==turn),None)
                if parent is None or not parent.get('wr') or any(sum(max(0,float(x)) for x in side)<=1e-4 for side in parent['wr']):
                    report['cases'].append(dict(line=line,turn=turn,status='EMPTY_REACH_EXCLUDED'))
                    continue
                pipeline.solve_sub(a.spot,'gto',flop,fr,line,turn)
                sub=pf/'out'/a.spot/'gto'/f"{flop}_{line.replace(' ','')}_{turn}.json"
                if not sub.exists():raise FileNotFoundError(sub)
                raw=json.loads(sub.read_text())
                report['cases'].append(dict(line=line,turn=turn,status='GENUINE_CFR_RAW_NOT_PUBLISHED',
                    raw_path=str(sub.relative_to(pf)),raw_sha256=sha(sub),
                    node_count=len(raw['nodes']),gto_exploitability_pct=raw['info'].get('gto_expl_pct'),
                    parent_pot_bb=parent['pot']/100,
                    parent_stack_bb=(fr['stack']-max(parent['bets']))/100,
                    parent_spr=round((fr['stack']-max(parent['bets']))/parent['pot'],6)))
    except Exception as e:
        report['failures'].append(dict(error=str(e),trace=traceback.format_exc()[-1600:]))
    report['elapsed_seconds']=round(time.monotonic()-t0,2)
    report['solved_cases']=sum(x['status']=='GENUINE_CFR_RAW_NOT_PUBLISHED' for x in report['cases'])
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:report[k] for k in ('spot','flop','solved_cases','failures','root_spr')},ensure_ascii=False))
    if report['failures']:raise SystemExit(1)
if __name__=='__main__': main()