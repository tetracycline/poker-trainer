#!/usr/bin/env python3
"""Assess a paired medium-pot-bet CFR experiment; do not publish by default.

A 50% size is a confirmed candidate only if an eligible *hero* combo reaches
that action and meets both 40%-absolute and 70%-of-top-frequency thresholds.
One representative flop cannot establish cross-texture NL2 action policy.
"""
import argparse
import hashlib
import json
import pathlib

def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def score(raw, profile, version):
    nodes=raw['nodes']
    node=next((n for n in nodes if n.get('line')=='x' and 'b33' in n.get('acts',[])),None)
    if not node: raise ValueError('No IP cbet after OOP check in real CFR')
    hero=1 if version=='exp_ip' else 0 if version=='exp_oop' else None
    actor=node['player']; nh=len(raw['hands'][actor]); wt=node['w'][actor]
    if len(wt)!=nh or len(node['strat'])!=len(node['acts'])*nh:
        raise ValueError('Malformed authentic CFR node dimensions')
    tot=sum(max(0,float(x)) for x in wt)
    if tot<=0: raise ValueError('No real combo reach')
    out={}
    for aidx,a in enumerate(node['acts']):
        mass=0.;candidates=[]
        for idx in range(nh):
            w=max(0,float(wt[idx]))
            if w<=1e-4: continue
            f=[max(0,float(node['strat'][i*nh+idx])) for i in range(len(node['acts']))]
            den=sum(f)
            if den<=0:continue
            q=[x/den for x in f]
            mass+=w*q[aidx]
            if q[aidx]>=.4-1e-7 and q[aidx]>=.7*max(q)-1e-7:
                candidates.append(raw['hands'][actor][idx])
        out[a]=dict(reach_weighted_pct=round(100*mass/tot,4),
                    eligible_combo_count=len(candidates),
                    eligible_combos=candidates[:30])
    return dict(profile=profile,version=version,actor=actor,
        actor_role=('hero' if hero==actor else 'villain' if hero is not None else 'equilibrium'),
        available_actions=node['acts'],
        actions=out,
        flop=raw['flop'],node_board=node['board'],
        node_pot_units=node['pot'],
        node_remaining_stack_units=raw['stack']-max(node['bets']),
        node_spr=round((raw['stack']-max(node['bets']))/node['pot'],6),
        gto_exploitability_pct=raw['info'].get('gto_expl_pct'),
        hero_gap_pct=raw['info'].get('hero_gap_pct'))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--folder',required=True,type=pathlib.Path)
    p.add_argument('--out',required=True,type=pathlib.Path)
    a=p.parse_args()
    comparison=json.loads((a.folder/'comparison.json').read_text())
    records={}
    for rec in comparison['results']:
        raw=pathlib.Path(rec['raw_file'])
        # Raw file may be stored in the named output folder, without CI parent.
        path=a.folder/raw.name
        if not path.is_file():raise FileNotFoundError(path)
        if sha256(path)!=rec['sha256']:
            raise ValueError('Solver sha256 mismatch '+path.name)
        r=score(json.loads(path.read_text()),rec['profile'],comparison['version'])
        r['sha256']=rec['sha256']
        records[rec['profile']]=r
    baseline=records['baseline'];medium=records['medium_added']
    c=medium['actions'].get('b50',{})
    is_hero=medium['actor_role']!='villain'
    enough=c.get('eligible_combo_count',0)>0
    report=dict(schema='NL2_DEPOLARIZED_CFR_GATE_V1',
       spot=comparison['spot'],version=comparison['version'],
       flop=comparison['flop'],baseline=baseline,medium_added=medium,
       hero_b50_eligible=bool(is_hero and enough),
       action_publish_allowed=False,
       reasoning='A single flop, even with eligible hero combos, cannot establish robust medium-bet NL2 cell rules across all texture/SPR/history contexts.',
       source_comparison=comparison['comparison'])
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(spot=report['spot'],version=report['version'],
      b50_frequency_pct=c.get('reach_weighted_pct'),
      b50_combo_count=c.get('eligible_combo_count'),
      actor=medium['actor_role'],publish=False)))
if __name__=='__main__':main()
