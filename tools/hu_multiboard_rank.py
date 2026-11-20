#!/usr/bin/env python3
"""Frozen NL2 frequency-first selection of 392 abstract training MODEL tables.

Ranking is a reproducible estimate from *actual* NL2 aggregate observations.
The corpus does not contain joint conditional rates for every complete history,
so unobserved conditional actions are explicit model assumptions, never data.
Selection is before inspecting a solver's per-board performance.

Data: poker-solver/inputs/pool_stats.json pinned commit
abe310c3aad02dd4a7c77fb2831801fd490cf51b, 2,334,487 NL2 hands.

All high-priority nodes remain APPROX until each obtains at least 3 distinct
correctly matched AUTHENTIC GTO solves with exact board, action, actor, SPR,
combo reach, and conditional stage provenance.
"""
import argparse, collections, hashlib, json, math, pathlib

FLOP_ACTIONS={'下注':'bet','過':'check','跟':'call','加注':'raise','超池下注':'overbet',
              '加注全下':'jam','全下':'jam','棄':'fold'}
FIRST_POS=['BTN_BB','CO_BB','SB_BB','UTG_CO']
THREE_POS=['BB3_BTN','SB3_BTN','CO3_BTN']
SPOT_W={
 'SRP':{}, '3BP':{},'ISO':{'ISO_BTN_CO':1.0},'LMP':{'LMP_CO_BB':1.0}
}

def observed_root_weights(p):
    b=p['bb_defend_by_opener']
    a={
      'BTN_BB':b['BTN']['n']*b['BTN']['defend']/100,
      'CO_BB':b['CO']['n']*b['CO']['defend']/100,
      'SB_BB':b['SB']['n']*b['SB']['defend']/100,
      'UTG_CO':p['preflop']['CO']['vs_open']['UTG']['n']*p['preflop']['CO']['vs_open']['UTG']['call']/100
    }
    tot=sum(a.values())
    SPOT_W['SRP'].update({k:v/tot for k,v in a.items()})
    # Position weights use directly observed BB/SB vs BTN 3-bet opportunities,
    # while CO3_BTN has an assumed 0.2 share because exact CO-BTN3 flop pot
    # frequency was not separated by the NL2 corpus.
    bb=p['preflop']['BB']['vs_open']['BTN'];sb=p['preflop']['SB']['vs_open']['BTN']
    prof={'BB3_BTN':bb['n']*bb['3bet']/100,'SB3_BTN':sb['n']*sb['3bet']/100,
          'CO3_BTN':p['preflop']['BTN']['vs_open']['CO']['n']*
                         p['preflop']['BTN']['vs_open']['CO']['3bet']/100}
    z=sum(prof.values())
    SPOT_W['3BP'].update({k:v/z for k,v in prof.items()})
    return {'SRP':a,'3BP':prof}

def tokenize(text):
    out=[]
    for part in text.split('、'):
        value=part.strip()
        if not value:continue
        role='hero' if value.startswith('你') else 'villain' if value.startswith('對手') else 'unknown'
        if role=='unknown':continue
        value=value[1:] if role=='hero' else value[2:]
        out.append((role,FLOP_ACTIONS.get(value,'other')))
    return out

def clamp(v):
    return max(0.015,min(0.94,float(v)))

def action_probability(p,kind,spot,actor,act,stage,history):
    # Prefer real NL2 PFR_IP/OOP decision and response stats whenever matchable.
    PFR_IP=spot in ('BTN_BB','CO_BB','CO3_BTN','ISO_BTN_CO','LMP_CO_BB')
    # In true two-handed flop tree: PFR IP if BTN/CO open vs BB, ISO BTN, LMP CO; CO3_BTN is PFR IP.
    # SB_BB/BB3_BTN/SB3_BTN/UTG_CO are OOP PFR.
    pfr='IP' if PFR_IP else 'OOP'
    ph=p['postflop_HU']
    family=kind if kind in ('SRP','3BP') else 'SRP'
    core=ph[family+'_PFR_'+pfr]
    # Training line position hero seat depends on the original table.
    # Here branch frequencies are a PFR-centric benchmark, not fake hand observations.
    prev=[x for x in history if x[1] not in ('check','fold')]
    facing='raise' if prev and prev[-1][1]=='raise' else 'bet' if prev and prev[-1][1] in ('bet','overbet') else None
    if stage==0 and not prev and act in ('bet','check'):
        cb=core['cbet']['pct']/100
        return clamp(cb if act=='bet' else 1-cb),f'{family}_PFR_{pfr}.cbet(n={core["cbet"]["n"]})'
    if act in ('call','raise','fold') and facing:
        sample=core['vs_cbet_raise_resp'] if facing=='raise' else core['vs_cbet']
        if stage>0:
            sample=core['vs_turn_barrel'] if stage==1 else core['vs_river_barrel']
        base=sample['call' if act=='call' else act]/100
        return clamp(base),f'{family}_PFR_{pfr}.vs{"_turn" if stage==1 else "_river" if stage==2 else ""}_bet(n={sample["n"]})'
    if act in ('bet','overbet'):
        if act=='overbet':return 0.04,'ASSUMED_OVERBET_BRANCH_4PCT'
        key='turn_barrel' if stage==1 else 'river_barrel' if stage==2 else 'cbet'
        sample=core[key]
        return clamp(sample['pct']/100),f'{family}_PFR_{pfr}.{key}(n={sample["n"]})'
    if act=='check':
        key='turn_barrel' if stage==1 else 'river_barrel' if stage==2 else 'cbet'
        sample=core[key]
        return clamp(1-sample['pct']/100),f'complement_{family}_PFR_{pfr}.{key}(n={sample["n"]})'
    if act=='raise':
        sample=p['HU_facing_bet'][str(stage+1)]['by_pot']['limped' if kind in ('ISO','LMP') else kind]
        return clamp(sample['raise']/100),f'HU_facing_bet[{stage+1}].by_pot.{kind} (n={sample["n"]})'
    if act=='call':
        sample=p['HU_facing_bet'][str(stage+1)]['by_pot']['limped' if kind in ('ISO','LMP') else kind]
        return clamp(sample['call']/100),f'HU_facing_bet[{stage+1}].by_pot.{kind} (n={sample["n"]})'
    if act=='jam':return 0.02,'ASSUMED_JAM_2PCT'
    return 0.1,'ASSUMED_OTHER_UNKNOWN_10PCT'

def ranking(queue,pool,cutoff):
    p=pool['NL2'];n=int(p['hands'])
    weights=observed_root_weights(p)
    # HU appearance base rates are the observed pot-level NL2 distribution;
    # by-pet family normalized share is not the unique hand count.
    pot_share=p['pot_level'];root={}
    root['SRP']=pot_share['SRP']/100
    root['3BP']=pot_share['3BP']/100
    # ISO subset is not a separate measured pot label, reserve explicitly assumed 25%.
    root['ISO']=pot_share['limped']/100*0.25
    root['LMP']=pot_share['limped']/100*0.75
    scored=[]
    for x in queue['records']:
        family=x['family'];spot=x['solver_profile'];segments=x['abstract_action_history'].split('|')
        base=root[family]*SPOT_W[family].get(spot,0)
        if base<=0:raise ValueError('Missing starting profile '+spot)
        trace=[]
        prob=1.0
        for st,segment in enumerate(segments):
            history=[]
            # For the current street, actions at this initial time are only
            # opportunity setup, not a completed new bet branch.
            for role,action in tokenize(segment):
                v,label=action_probability(p,family,spot,role,action,st,history)
                prob*=v
                history.append((role,action))
                trace.append({'street':st,'actor':role,'action':action,
                    'probability':round(v,6),'source':label})
        if len(segments)==3 and len(segments[1])<2:prob*=0.9  # explicit stage survival
        # Avoid using number of preprogrammed texture/hand cells as empirical weight.
        score=base*prob
        scored.append(dict(model_id=x['model_id'],family=family,spot=spot,
          street=x['street'],abstract_history=x['abstract_action_history'],
          estimated_NL2_hand_opportunity_fraction=round(score,10),
          relative_base_appearance=round(base,8),
          source_trace=trace,approx_spr=x['approx_spr'],root_spr=x['root_spr'],
          represented_class_texture_count=x['represented_class_texture_count']))
    scored.sort(key=lambda x:(-x['estimated_NL2_hand_opportunity_fraction'],x['model_id']))
    cutoff=min(cutoff,len(scored))
    limit=scored[cutoff-1]['estimated_NL2_hand_opportunity_fraction']
    top_ids=set(x['model_id'] for x in scored[:cutoff])
    for rank,x in enumerate(scored,1):
        x['rank_by_empirically_grounded_frequency_proxy']=rank
        x['high_frequency_priority']=x['model_id'] in top_ids
        x['status']='APPROX_PENDING_EXACT_MULTIBOARD_EVIDENCE'
    return dict(schema='NL2_MULTIBOARD_PREREG_RANK_V1',
      source='tetracycline/poker-solver/inputs/pool_stats.json',
      source_sha256=hashlib.sha256(json.dumps(pool,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
      source_hands=n,
      endpoint='392 generic NL2 HU model nodes (not 392 exact-board CFR games)',
      empirical_base={'pot_level_pct':pot_share,
          'bb_defend_by_opener':p['bb_defend_by_opener'],
          'limper_vs_raise':p['limper_vs_raise'],
          'family_root_pct':{k:round(v*100,3) for k,v in root.items()},
          'spot_appearance_proxy_inputs':weights,
          'per_spot_relative_weights':SPOT_W},
      disclosed_assumptions=['ISO family proxy = 25% of observed limped pot frequency; LMP = 75%, because exact ISO postflop type not identified',
        'Postflop stage-specific cbet/barrel/fold/call aggregate probabilities are marginals, NOT observed multi-street action-history joint frequencies',
        'PFR vs caller handclass likelihoods are not inferred; each abstract MODEL is an opportunity, not a unique observed hand count',
        'Fallback conditional probabilities are labeled ASSUMED in every node source_trace',
        'High frequency only means preregistered rank top-N among 392; all need independent exact cards and real source GTO before CERT-MULTIBOARD'],
      cutoff={'method':'TOP_N_BY_NL2_EMPIRICAL_ANCHORED_OPPORTUNITY_PROXY',
              'N':cutoff,'fraction_of_model_nodes':round(cutoff/len(scored),6),
              'min_priority_score':limit,
              'selection_does_not_consider_solver_result_or_profit':True},
      summary={'models':len(scored),'high_frequency_priority':cutoff,
               'low_priority_approx':len(scored)-cutoff,
               'top_by_family':dict(collections.Counter(x['family'] for x in scored[:cutoff]))},
      nodes:scored)

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--queue',required=True,type=pathlib.Path)
    a.add_argument('--pool',required=True,type=pathlib.Path)
    a.add_argument('--out',required=True,type=pathlib.Path)
    a.add_argument('--cutoff',type=int,default=24)
    q=a.parse_args()
    obj=ranking(json.loads(q.queue.read_text()),json.loads(q.pool.read_text()),q.cutoff)
    q.out.parent.mkdir(parents=True,exist_ok=True)
    q.out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'summary':obj['summary'],'cutoff':obj['cutoff'],
       'top':[{k:x[k] for k in ('model_id','family','spot','street','estimated_NL2_hand_opportunity_fraction','abstract_history','approx_spr')}
            for x in obj['nodes'][:30]]},ensure_ascii=False))
if __name__=='__main__':main()
