#!/usr/bin/env python3
"""Compile the exact HU river backlog into solvable and blocked jobs.

The root SPR is informational. Node SPR requires the precise betting history.
Never certify GTO (CERT) or mapped EST from a texture alone.
"""
import argparse
import collections
import json
import pathlib
import re

# Existing poker-solver/postflop/py/ranges.py exact preflop profiles.
PROFILES = {
    'BTN_BB': (5.5, 97.5), 'CO_BB': (5.5, 97.5),
    'SB_BB': (6.0, 97.0), 'BB3_BTN': (20.5, 90.0),
    'SB3_BTN': (21.0, 90.0),
    # From poker-solver/preflop/pfsolve.py: UTG opens 2.5, CO calls, blinds 1.5.
    'UTG_CO': (6.5, 97.5),
    # CO opens 2.5, BTN 3-bets IP to 7.5; CO calls, blinds 1.5.
    'CO3_BTN': (16.5, 92.5),
}

def pot_family(pre):
    if '溜入' in pre:
        return 'ISO' if '加注隔離' in pre else 'LMP'
    return '3BP' if '3-bet' in pre else 'SRP'

def spot(pre, family):
    pre = re.sub(r'\s+', ' ', pre)
    if family == 'SRP':
        if 'BTN 開' in pre and 'BB 跟' in pre: return 'BTN_BB'
        if 'CO 開' in pre and 'BB 跟' in pre: return 'CO_BB'
        if 'SB 開' in pre and 'BB 跟' in pre: return 'SB_BB'
        if 'UTG 開' in pre and 'CO 跟' in pre: return 'UTG_CO'
    if family == '3BP':
        if 'BTN 開' in pre and 'BB 3-bet' in pre: return 'BB3_BTN'
        if 'BTN 開' in pre and 'SB 3-bet' in pre: return 'SB3_BTN'
        if 'CO 開' in pre and 'BTN 3-bet' in pre: return 'CO3_BTN'
    return None

def build(audit):
    counts = audit['counts']
    cells = audit['unresolvedCells']
    if len(cells) != counts['noRiver'] or len(cells) != len(set(c['id'] for c in cells)):
        raise ValueError('Incomplete or duplicate per-cell gap ledger')
    if counts['continuing'] != counts['reachRiver'] + counts['noRiver']:
        raise ValueError('Coverage does not reconcile')
    groups = collections.OrderedDict()
    full = []
    for c in cells:
        pre = c['preflop']
        fam = pot_family(pre)
        sp = spot(pre, fam)
        rootpot, rootstack = PROFILES[sp] if sp else (None, None)
        c = dict(c, pot_family=fam, solver_spot=sp,
                 root_pot_bb=rootpot, root_stack_bb=rootstack,
                 root_spr=round(rootstack/rootpot, 5) if sp else None,
                 node_pot_bb=None, node_stack_bb=None, node_spr=None,
                 exact_bet_sizes_verified=False, combo_reach_verified=False,
                 certificate=None, estimate_source=None)
        full.append(c)
        at = c.get('blockedAt') or {}
        key = (fam,sp,pre,c['nd'],str(c.get('history')),c['action'],
               at.get('nd'),c['breakReason'])
        if key not in groups:
            groups[key] = dict(group_id=f'G{len(groups)+1:03}',pot_family=fam,
                solver_spot=sp,preflop=pre,nd=c['nd'],
                action_history=c.get('history'),action=c['action'],
                blocked_nd=at.get('nd'),break_reason=c['breakReason'],
                root_pot_bb=rootpot,root_stack_bb=rootstack,
                root_spr=round(rootstack/rootpot,5) if sp else None,
                node_spr=None,required_next_action_sizes=None,
                status='NEEDS_LINE_SPECIFIC_SOLVE' if sp else 'BLOCKED_PREFLOP_RANGE',
                count=0,cell_ids=[])
        groups[key]['count'] += 1
        groups[key]['cell_ids'].append(c['id'])
    fam=collections.Counter(c['pot_family'] for c in full)
    sp=collections.Counter(c['solver_spot'] or 'NO_EXACT_PROFILE' for c in full)
    reasons=collections.Counter(c['breakReason'] for c in full)
    out=dict(schema='NL2_HU_RIVER_GAP_QUEUE_V1',
      provenance_policy='CERT: identical positions, preflop weighted ranges, exact postflop bets, river board, node pot, remaining stack, full combo reach and converged CFR; EST additionally requires same family and node SPR and explicit source identity. Cross-family or unknown node SPR mapping forbidden.',
      summary=dict(continuing=counts['continuing'],river=counts['reachRiver'],missing=len(full),
        percentage=counts['riverShare'],groups=len(groups),
        has_starting_profile=sum(c['solver_spot'] is not None for c in full),
        missing_exact_preflop_profile=sum(c['solver_spot'] is None for c in full),
        by_family=dict(fam),by_solver_spot=dict(sp),by_break_reason=dict(reasons),
        newly_certified=0,newly_estimated=0),
      groups=list(groups.values()),cells=full)
    assert sum(x['count'] for x in out['groups'])==len(full)
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--audit',required=True,type=pathlib.Path)
    p.add_argument('--out',required=True,type=pathlib.Path)
    a=p.parse_args()
    out=build(json.loads(a.audit.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(out['summary'],ensure_ascii=False))
if __name__=='__main__':main()
