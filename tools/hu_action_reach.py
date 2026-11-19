#!/usr/bin/env python3
"""Per-combo proof of solver action reach and low-frequency branch pruning.

No NL2 decision or link is published here. Cert/EST require full action,
position, pot/stack/SPR and range lineage beyond this report.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
ABS_SECONDARY = 0.40
REL_SECONDARY = 0.70
MIN_REACH = 1e-4

def choose(actions, frequencies):
    if not actions or len(actions) != len(frequencies):
        raise ValueError('action/frequency count mismatch')
    if any(not math.isfinite(x) or x < 0 for x in frequencies):
        raise ValueError('invalid CFR frequency')
    total = sum(frequencies)
    if total <= 0: raise ValueError('zero-frequency hand')
    q = [x / total for x in frequencies]
    hi = max(range(len(q)), key=lambda i:q[i])
    return [hi] + [i for i in range(len(q)) if i != hi and
                     q[i] >= ABS_SECONDARY-1e-7 and
                     q[i] >= REL_SECONDARY*q[hi]-1e-7]

def audit(raw, origin, sha256, source_run=None):
    hands,nodes = raw['hands'],raw['nodes']
    if len(hands) != 2: raise ValueError('Only authentic HU CFR JSON is accepted')
    info=raw.get('info',{})
    gap,hero_gap=info.get('gto_expl_pct'),info.get('hero_gap_pct')
    converged=gap is not None and math.isfinite(float(gap)) and float(gap)<=0.5+1e-6
    if hero_gap is not None: converged=converged and float(hero_gap)<=0.5+1e-6
    totals=dict(nodes=0,combos_reachable=0,combos_unreachable=0,
                forced_single=0,near_mixed=0,discarded_secondary=0)
    records=[]
    for n in nodes:
        p=n['player']
        if p not in (0,1): raise ValueError('Non-HU actor')
        acts=n['acts'];nh=len(hands[p]);strat=n['strat'];w=n['w'][p]
        if len(w)!=nh or len(strat)!=nh*len(acts):
            raise ValueError('invalid CFR node dimensions: '+str(n.get('line')))
        branches={a:dict(combo_count=0,reach_mass=0.) for a in acts}
        combos=[];active=0
        for h,combo in enumerate(hands[p]):
            wt=float(w[h])
            if wt <= MIN_REACH:
                totals['combos_unreachable']+=1
                continue
            fq=[float(strat[i*nh+h]) for i in range(len(acts))]
            selected=choose(acts,fq)
            den=sum(fq)
            totals['combos_reachable']+=1;active+=1
            totals['near_mixed' if len(selected)>1 else 'forced_single']+=1
            totals['discarded_secondary']+=len(acts)-len(selected)
            for i in selected:
                branches[acts[i]]['combo_count']+=1
                branches[acts[i]]['reach_mass']+=wt*fq[i]/den
            combos.append(dict(combo=combo,actions=[acts[i] for i in selected],
                frequencies={acts[i]:round(fq[i]/den,5) for i in selected}))
        totals['nodes']+=int(active>0)
        records.append(dict(line=n['line'],board=n['board'],pot=n['pot'],bets=n['bets'],
          remaining_effective_stack_units=max(0,raw['stack']-max(n['bets'])),
          node_spr=round(max(0,raw['stack']-max(n['bets']))/n['pot'],6) if n['pot']>0 else None,
          actor=p,action_labels=acts,reachable_combos=active,
          branches=branches,combos=combos))
    return dict(schema='HU_CFR_REACH_V1',source=origin,source_sha256=sha256,
      source_run=source_run,source_flop=raw.get('flop'),source_turn=raw.get('turn'),
      source_flop_line=raw.get('line0'),
      source_root_pot_units=raw.get('pot'),source_root_stack_units=raw.get('stack'),
      gto_exploitability_pct=gap,hero_gap_pct=hero_gap,converged_for_cert=converged,
      rules=dict(always_allow_highest_action=True,secondary_absolute_min=ABS_SECONDARY,
        secondary_relative_to_highest_min=REL_SECONDARY,min_combo_reach=MIN_REACH),
      summary=totals,nodes=records)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--raw',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--run-id')
    a=p.parse_args()
    data=a.raw.read_bytes()
    obj=audit(json.loads(data),str(a.raw),hashlib.sha256(data).hexdigest(),a.run_id)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps(dict(source=str(a.raw),sha256=obj['source_sha256'],
      converged=obj['converged_for_cert'],**obj['summary'])))
if __name__=='__main__':main()
