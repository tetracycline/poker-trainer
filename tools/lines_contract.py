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
