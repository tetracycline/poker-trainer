"""Independent decision/grid contract. Never infer expected nodes from surviving rows.

River draw labels mean unpaired missed draws, classified on the turn. An OOP
opener facing a flop bet has checked first (the historical UI calls it donk).
"""
import itertools
import json
from pathlib import Path

HANDS = ['S', 'TPG', 'TPW', 'MID', 'DRAW', 'WDRAW', 'AIR']
TEXTURES = ['A_high', 'KQ_high', 'mid_high', 'low', 'paired', 'mono']
NODES = {
 'ipfr': 'f_cbet f_vs_donk f_vs_xr t_barrel t_delay t_vs_probe t_vs_xr r_barrel r_stab r_vs_bet r_vs_xr',
 'opfr': 'f_cbet f_vs_donk f_vs_xr t_barrel t_delay t_vs_probe t_vs_xr r_barrel r_stab r_vs_bet r_vs_xr',
 'bb': 'f_first f_vs_cbet f_vs_xr t_first t_probe t_vs_barrel t_vs_xr r_stab r_vs_bet r_vs_xr',
 'ipc': 'f_stab f_vs_cbet f_vs_xr t_delay t_vs_barrel t_vs_xr r_stab r_vs_bet r_vs_xr',
 '3bp': '3b_f_cbet 3b_f_vs_donk 3b_f_vs_xr 3b_t_barrel 3b_t_delay 3b_t_vs_probe 3b_t_vs_xr 3b_r_barrel 3b_r_stab 3b_r_vs_bet 3b_r_vs_xr 3c_f_first 3c_f_stab 3c_f_vs_cbet 3c_f_vs_over 3c_f_vs_xr 3c_t_first 3c_t_probe 3c_t_delay 3c_t_vs_barrel 3c_t_vs_xr 3c_r_stab 3c_r_vs_bet2 3c_r_vs_xr',
 'iso': 'f_cbet f_vs_donk f_vs_xr t_barrel t_delay t_vs_probe t_vs_xr r_barrel r_stab r_vs_bet r_vs_xr f_stab f_lead lmp_f_vs_cbet lmp_f_vs_xr lmp_t_first lmp_t_probe lmp_t_delay lmp_t_vs_barrel lmp_t_vs_xr lmp_r_stab lmp_r_vs_bet lmp_r_vs_xr',
 'mw': 'f_bet f_vs_bet f_vs_xr t_bet t_vs_bet t_vs_xr r_bet r_vs_bet r_vs_xr',
}
NODES = {s: n.split() for s, n in NODES.items()}
NODES['iso'] += ['lmp_f_first', 'lmp_f_stab']
# The initiative can change after a check/call or a caller's stab.
NODES['ipfr'] += ['t_stab', 't_vs_barrel']
NODES['opfr'] += ['t_first', 't_vs_barrel']
NODES['bb'] += ['t_barrel', 't_vs_probe', 'r_barrel']
NODES['ipc'] += ['t_barrel', 't_stab', 't_vs_probe', 'r_barrel']
NODES['3bp'] += ['3b_t_first', '3b_t_stab', '3b_t_vs_barrel', '3c_t_barrel', '3c_t_stab', '3c_t_vs_probe', '3c_r_barrel']
NODES['iso'] += ['t_first', 't_stab', 't_vs_barrel', 'lmp_t_barrel', 'lmp_t_stab', 'lmp_t_vs_probe', 'lmp_r_barrel']

# Explicit corrected pot-type vocabulary. Pure ISO caller decisions were formerly
# misnamed lmp; retain LMP decisions only when independently supported.
NODES['iso'] = [n for n in NODES['iso'] if n not in ('f_stab','f_lead','lmp_f_first')]
NODES['iso'] += ['lmp_f_lead'] + ['iso_'+n[4:] for n in NODES['iso'] if n.startswith('lmp_') and n not in ('lmp_r_barrel','lmp_f_lead')]
NODES['iso'] += ['iso_f_first','iso_r_vs_3b','iso_t_vs_3b','lmp_r_vs_3b','lmp_t_vs_3b']

def street(nd):
    return 'flop' if nd.startswith('f_') or '_f_' in nd else 'turn' if nd.startswith('t_') or '_t_' in nd else 'river'

def conditions(sp, nd):
    if sp == 'mw': return [{'hr':'PFR'},{'hr':'CALL'}]
    if nd.endswith('r_vs_bet') or nd.endswith('r_vs_bet2'):
        return [dict(sz=z, **({'ln': l} if sp in ('bb', 'ipc') else {})) for z, l in itertools.product(['le50', 'p75', 'o150'], ['tb', 'oth'] if sp in ('bb', 'ipc') else [''])]
    if street(nd) == 'flop' and sp in ('ipfr', 'opfr', 'bb', 'ipc') and nd not in ('f_first', 'f_stab'):
        return [dict(tx=t) for t in TEXTURES]
    return [{}]

def expected(data):
    """Contract plus every actual column, so UI-added conditions cannot escape QA."""
    for sp, nodes in NODES.items():
        for nd in sorted(set(nodes) | {r['nd'] for r in data['rows'] if r['sp'] == sp}):
            conds = conditions(sp, nd)
            conds += [r.get('c') or {} for r in data['rows'] if r['sp'] == sp and r['nd'] == nd and not r.get('x')]
            unique = {json.dumps(c, sort_keys=True): c for c in conds}
            for c in unique.values():
                for hc in HANDS: yield sp, nd, hc, c

def diff(data):
    missing = []
    for sp, nd, hc, c in expected(data):
        if not any(r['sp'] == sp and r['nd'] == nd and hc in r['hc'] and not r.get('x') and all(c.get(k) == v for k, v in (r.get('c') or {}).items()) for r in data['rows']):
            missing.append(dict(sp=sp, nd=nd, hc=hc, c=c))
    return missing

if __name__ == '__main__':
    import sys
    d = json.load(open(sys.argv[1]))
    json.dump(diff(d), sys.stdout, ensure_ascii=False, indent=2)
    print()

# Semantic invariants are independent of recommended poker actions.
POSITION_ORDER = ['SB', 'BB', 'UTG', 'HJ', 'CO', 'BTN']
def semantic_errors(data):
    errors=[]
    def err(r,msg): errors.append(r.get('id',r.get('nd','?'))+': '+msg)
    for r in data['rows']:
        nd,sp=r['nd'],r['sp']
        label=data.get('node_labels',{}).get(sp,{}).get(nd,'')
        if not label: err(r,'missing per-spot label')
        for field in ('why','ev','cl'):
            if any(x in str(r.get(field,'')) for x in ('undefined','NaN')): err(r,'invalid rendered text')
        if any(x in label for x in ('undefined','NaN')):err(r,'invalid label')
        if (sp=='ipc' or nd.startswith(('3c_','lmp_','iso_'))) and '延遲 c-bet' in label:err(r,'caller c-bet label')
        for sample in r.get('solver',{}).get('samples',[]):
            if sp in ('ipfr','ipc','opfr','bb') and sample.get('player') is not None and sample['player'] != (1 if sp in ('ipfr','ipc') else 0):err(r,'strategy IP/OOP role')
            from pathlib import Path
            source=Path(sample.get('original_source',sample.get('path',sample.get('source','')))).name
            if nd.startswith('lmp_') and not source.startswith('limp_'):err(r,'LMP strategy source')
            if nd.startswith('iso_') and not source.startswith('iso_'):err(r,'ISO strategy source')
        for e in r.get('eg',[]):
            if nd.startswith('lmp_') and e['t']!='LMP':err(r,'LMP namespace pot type')
            if nd.startswith('iso_') and e['t']!='ISO':err(r,'ISO namespace pot type')
            positions=[p for p in [e['pa']]+e['pc'] if p]
            if e['me'] not in positions:err(r,'hero absent');continue
            ip=POSITION_ORDER.index(e['me'])==max(POSITION_ORDER.index(p) for p in positions)
            if sp in ('ipfr','opfr','bb','ipc'):
                if e['t']!='SRP':err(r,'SRP spot pot type')
                if (e['me']==e['pa']) != (sp in ('ipfr','opfr')):err(r,'opener/caller role')
                if ip != (sp in ('ipfr','ipc')):err(r,'IP/OOP spot')
            if sp=='bb' and e['me'] not in ('SB','BB'):err(r,'blind defender position')
            if nd.startswith(('3b_','3c_')) and (e['t']!='3BP' or (e['me']==e['pa']) != nd.startswith('3b_')):err(r,'3bet role')
            if '本街你先過牌' in label and not any(tk==e['me']+':x' for tk in e['l'].split('/')[-1].split()):err(r,'claimed current-street check absent')
            if '你有位置，對手先行動' in label and not ip:err(r,'label first actor IP')
            if '你沒位置先行動' in label and e['me'] != min(positions,key=POSITION_ORDER.index):err(r,'label first actor OOP')
    return errors
