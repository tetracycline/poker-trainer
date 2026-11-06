"""Publication gate on raw approximation frequencies, including pool baselines."""
from collections import defaultdict

def check(data):
    groups=defaultdict(dict);ip_groups=set()
    for r in data['rows']:
        if r['sp']!='mw': continue
        v=r.get('solver',r.get('baseline',{}))
        if not v.get('freq'): continue
        key=(r['nd'],r.get('c',{}).get('hr'))
        groups[key][r['hc'][0]]=v['freq']
        if any(s.get('player')==1 for s in v.get('samples',[])):ip_groups.add(key)
    issues=[];table=[]
    for (nd,role),g in sorted(groups.items()):
        if not all(c in g for c in ['S','MID','WDRAW','AIR']):
            issues.append(f'{nd}/{role}: missing sanity classes');continue
        agg=lambda c:sum(g[c].get(a,0)for a in ['small','big','r'])
        strong=agg('S');weak=max(agg(c)for c in ['MID','WDRAW','AIR'])
        air=g['AIR'].get('f',0);mid=g['MID'].get('f',0)
        # Strength ordering is required for openers or IP actors, not OOP callers.
        applicable=role=='PFR' or (nd,role) in ip_groups
        if applicable and strong+1e-6<weak:issues.append(f'{nd}/{role}: S aggression {strong:.5f} < weak {weak:.5f}')
        if '_vs_' in nd and air+1e-6<mid:issues.append(f'{nd}/{role}: AIR folds {air:.5f} < MID {mid:.5f}')
        table.append(dict(node=nd,role=role,strength_gate=applicable,S=strong,weak=weak,AIR_fold=air,MID_fold=mid))
    return issues,table
