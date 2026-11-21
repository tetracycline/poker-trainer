#!/usr/bin/env python3
"""Independently check real Rust CFR outputs for frozen but *assumed* 100bb ranges.

The audit establishes authentic CFR under its documented ISO/LMP assumptions.
It does NOT certify any rendered NL2 model cell, true pool population range, or
texture-equivalent transfer to another pot / action history.
"""
import argparse
import hashlib
import json
import pathlib
import zipfile

EXPECTED = {'ISO_BTN_CO': (9.5, 96.0), 'LMP_CO_BB': (2.5, 99.0)}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def audit_zip(p):
    with zipfile.ZipFile(p) as z:
        names=z.namelist()
        found=[s for s in names if s.startswith('evidence/') and s.endswith('.json')]
        if len(found)!=1:raise ValueError(f'expected exactly one evidence manifest, found {found}')
        report=json.loads(z.read(found[0]))
        spot=report['spot']
        if spot not in EXPECTED:raise ValueError(f'Unapproved assumed source spot: {spot}')
        pot,stack=EXPECTED[spot]
        if abs(report['starting_pot_bb']-pot)>1e-6 or abs(report['starting_remaining_bb']-stack)>1e-6:
            raise ValueError('Starting pot/stack changed')
        if abs(report['root_spr']-stack/pot)>1e-4:
            raise ValueError('Incorrect root SPR')
        if report['not_CERT_or_EST_for_NL2'] is not True or report['version']!='gto':
            raise ValueError('Provenance label does not prohibit false CERT')
        for player in ('oop','ip'):
            weights=report[f'{player}_169_class_weights']
            if len(weights)!=169 or sum(weights.values())<=0 or any(not 0<=x<=1 for x in weights.values()):
                raise ValueError('Invalid assumed starting range weights')
        if report['failures']:raise ValueError('CFR job reported failure')
        base=f'solver/postflop/out/{spot}/gto/'
        flop=report['flop']
        fr=json.loads(z.read(base+f'{flop}.json'))
        job=json.loads(z.read(base+f'{flop}.job.json'))
        if job.get('pot')!=round(pot*100) or job.get('stack')!=round(stack*100):
            raise ValueError('Actual engine job diverges from frozen root pot and stack')
        if abs(job.get('rake_rate',0)-0.05)>1e-6 or job.get('rake_cap')!=1000.0:
            raise ValueError('Actual rake not source-controlled')
        if fr['flop']!=flop or fr['pot']!=round(pot*100) or fr['stack']!=round(stack*100):
            raise ValueError('Root engine output diverges from input')
        for player,name in (('oop',0),('ip',1)):
            formatted=job[player]
            for hand,weight in report[f'{player}_169_class_weights'].items():
                if weight>=0.005 and not any(token.startswith(hand+':') for token in formatted.split(',')):
                    raise ValueError('Job missing expected weighted hand')
        solved=[]
        for case in report['cases']:
            if case['status']!='GENUINE_CFR_RAW_NOT_PUBLISHED':
                raise ValueError('Pilot did not produce required authentic case')
            rawkey='solver/postflop/'+case['raw_path']
            raw=z.read(rawkey)
            if sha(raw)!=case['raw_sha256']:
                raise ValueError('Raw CFR file failed SHA-256 manifest')
            d=json.loads(raw)
            if d['flop']!=flop or d['line0']!=case['line'] or d['turn']!=case['turn']:
                raise ValueError('Raw CFR runout/action history does not match manifest')
            parent=next((n for n in fr['nodes'] if n['line']==case['line']+'/' and n['board'][-2:]==case['turn']),None)
            if parent is None:raise ValueError('No parent with exact flop/turn action lineage')
            pp=parent['pot']/100
            ps=(fr['stack']-max(parent['bets']))/100
            if abs(pp-case['parent_pot_bb'])>1e-5 or abs(ps-case['parent_stack_bb'])>1e-5:
                raise ValueError('Parent pot/effective stack mismatch')
            if abs(ps/pp-case['parent_spr'])>1e-4:
                raise ValueError('Parent SPR mismatch')
            gap=d['info'].get('gto_expl_pct')
            if gap is None or gap>0.50:raise ValueError('CFR non-converged (>0.5% exploitability)')
            river=[x for x in d['nodes'] if len(x['board'])==10]
            if not river:raise ValueError('Turn subgame lacks an extracted 5-card river node')
            for n in d['nodes']:
                if n['pot']<=0 or d['stack']<0:raise ValueError('Nonpositive pot or negative stack')
                rem=d['stack']-max(n['bets'])
                if rem < -1e-5: raise ValueError('Subgame bets exceed stack')
                spr=rem/n['pot']
                if not 0<=spr<=stack/pot+1e-4:raise ValueError('Node SPR out of bounds')
                if len(n['strat'])!=len(n['acts'])*len(d['hands'][n['player']]):
                    raise ValueError('Invalid genuine combo-by-action strategy dimensions')
            solved.append(dict(flop=flop,turn=case['turn'],line=case['line'],source_sha256=case['raw_sha256'],
                               gto_exploitability_pct=gap,parent_spr=case['parent_spr'],
                               subgame_nodes=len(d['nodes']),river_nodes=len(river)))
        return dict(spot=spot,kind=report['kind'],starting_pot_bb=pot,starting_remaining_bb=stack,
                    root_spr=report['root_spr'],flop=flop,source=found[0],source_zip_sha256=sha(p.read_bytes()),
                    verified_subgames=len(solved),subgames=solved,not_nl2_certified=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--zip',required=True,type=pathlib.Path,nargs='+')
    p.add_argument('--out',required=True,type=pathlib.Path)
    a=p.parse_args()
    x=[audit_zip(p) for p in a.zip]
    if len(x)!=2 or {z['spot'] for z in x}!=set(EXPECTED):raise ValueError('Must have both distinct ISO and LMP source artifacts')
    r={'schema':'NL2_ASSUMED_CFR_AUTHENTICITY_V1','cases':x,
       'total_subgames':sum(z['verified_subgames'] for z in x),
       'all_solver_CFR_under_assumed_profiles':True,'new_cert_nl2_table_cells':0,
       'new_est_nl2_table_cells':0,'model_navigation_is_not_GTO_certification':True}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cases':{z['spot']:z['verified_subgames'] for z in x},'total':r['total_subgames'],
                      'new_CERTest':0},ensure_ascii=False))
if __name__=='__main__':main()