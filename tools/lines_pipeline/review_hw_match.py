# HW 的翻後決策 → 對照表（rows.json）有沒有對應的列
import pickle, json, sys, argparse
from collections import Counter, defaultdict
# common classifier is vendored alongside this module
from common import hcls, szb, texture, ctype
from run10_common import classes
ap = argparse.ArgumentParser()
ap.add_argument('--rows', default='/workspace/outputs/poker_lines_v2/results/rows.json')
ap.add_argument('--out', default='/workspace/outputs/poker_lines_v2/results/hw_match.json')
args = ap.parse_args()
P = pickle.load(open('/workspace/outputs/poker/lines1105/hw.pkl', 'rb')); D = json.load(open(args.rows)); ROWS = D['rows']
IDX = defaultdict(list)
for r in ROWS: IDX[(r['sp'], r['nd'])].append(r)
POSO = ['SB', 'BB', 'UTG', 'HJ', 'CO', 'BTN']
GRP = lambda sb: 'le50' if sb in ('s33', 's50') else 'p75' if sb in ('s75', 's100') else 'o150'
def ip(a, b, pos): return POSO.index(pos[a]) > POSO.index(pos[b])
AL = D['al']
def match(sp, nd, c, cond):
    r = match0(sp, nd, c, cond)
    if r: return r
    a = AL.get(sp, {}).get(nd)
    if a:
        cd = dict(cond)
        if a in ('bb', 'ipfr') and nd in ('f_vs_cbet', 'f_cbet') and 'tx' not in cd: pass
        asp, _, and_ = a.partition(':'); r = match0(asp, and_ or nd, c, cd)
        if r: return dict(r, b='alias:' + r['b'])
    return None
def match0(sp, nd, c, cond):
    for r in IDX.get((sp, nd), []):
        if c not in r['hc'] or r.get('x'): continue
        rc = r.get('c') or {}
        if all(cond.get(k) == v for k, v in rc.items()): return r
    return None
tot = 0; cov = 0; BY = Counter(); BYC = Counter(); MISS = Counter(); MATCHED = []
for h in P:
    if 'Hero' not in h['live'] or len(h['board']) < 6 or not h['hero']: continue
    pre = h['acts'][0]; pot = 1.5; contrib = defaultdict(float); contrib[[p for p in h['pos'] if h['pos'][p] == 'SB'][0] if 'SB' in h['pos'].values() else None] = 0.5
    bbp = [p for p in h['pos'] if h['pos'][p] == 'BB']
    if bbp: contrib[bbp[0]] = 1.0
    for (p, v, x, to, ai) in pre:
        if v == 'c': contrib[p] += x
        elif v == 'r': contrib[p] = to
    pot = sum(v for k, v in contrib.items() if k)
    live = list(h['live']); raises = h['raises']; pfr = h['raisers'][-1] if h['raisers'] else None
    allin = {a[0] for a in pre if a[4]}
    hist = {}  # street → list of (player, act)
    for s in (1, 2, 3):
        L = {1: 6, 2: 8, 3: 10}[s]
        if len(h['board']) < L or 'Hero' not in live: break
        bd = h['board'][:L]; acts = h['acts'][s]; nst = len(live); c = classes(h['hero'], bd)[0]
        facing = None; bet_by = None; cur = 0.0; hero_bet = False; hero_raised = False; potst = pot; pending = set(live) - allin
        for i, (p, v, x, to, ai) in enumerate(acts):
            if p == 'Hero':
                tot += 1
                if nst >= 3:
                    sp = 'mw'
                    if facing is None: nd, cond = {1: 'f_bet', 2: 't_bet', 3: 'r_bet'}[s], {'n': '3' if nst == 3 else '4+'}
                    elif facing == 'b': nd, cond = {1: 'f_vs_bet', 2: 't_vs_bet', 3: 'r_vs_bet'}[s], {'by': 'PFR' if bet_by == pfr else 'NON', 'sz': GRP(szb(fx))}
                    else:
                        stem = {1:'f',2:'t',3:'r'}[s]
                        raises_now = sum(a0=='r' for _,a0 in [(q,a0) for q,a0,_,_,_ in acts[:i]])
                        nd = stem + ('_vs_3b' if hero_raised else '_vs_reraise' if hero_bet and raises_now>=2 else '_vs_xr' if hero_bet else '_vs_cold_raise')
                        cond = {}
                    if s == 1 and nd == 'f_vs_bet': cond.pop('sz')
                    if s == 3 and nd == 'r_vs_bet': cond.pop('by')
                    if s != 1 and nd in ('t_bet',): pass
                    if nd == 'r_bet': cond = {}
                    cond['hr'] = 'PFR' if pfr == 'Hero' else 'CALL'
                else:
                    vil = [q for q in live if q != 'Hero'][0]; hip = ip('Hero', vil, h['pos'])
                    if raises == 0: kind = 'LMP'
                    elif raises == 1 and h['limpers']: kind = 'ISO'
                    elif raises == 1: kind = 'SRP'
                    else: kind = '3BP'
                    hp = pfr == 'Hero'
                    if kind == 'LMP': sp = 'iso'
                    elif kind == 'ISO': sp = 'iso'
                    elif kind == 'SRP': sp = ('ipfr' if hip else 'opfr') if hp else ('ipc' if hip else 'bb')
                    else: sp = '3bp'
                    pf = 'pfr' if hp else 'call'
                    prev = hist  # earlier streets
                    hb = lambda st, who: any(q == who and a == 'b' for q, a in prev.get(st, []))
                    xx = lambda st: prev.get(st) is not None and all(a == 'x' for q, a in prev.get(st, []))
                    cond = {'tx': texture(bd[:6])} if s == 1 else {}
                    if hero_raised and facing in ('r','b'): nd = {1: 'f_vs_3b', 2: 't_vs_3b', 3: 'r_vs_3b'}[s]
                    elif facing == 'r' or (facing == 'b' and hero_bet): nd = {1: 'f_vs_xr', 2: 't_vs_xr', 3: 'r_vs_xr'}[s]
                    elif facing == 'b':
                        if s == 1: nd = 'f_vs_cbet' if not hp else 'f_vs_donk'
                        elif s == 2: nd = 't_vs_barrel' if hb(1, vil) else 't_vs_probe'
                        else: nd = 'r_vs_bet'
                        if s == 3:
                            g = GRP(szb(fx)); cond = {'sz': g}
                            if sp in ('bb', 'ipc'): cond['ln'] = 'tb' if hb(1, vil) and hb(2, vil) else 'oth'
                    else:
                        if s == 1:
                            nd = 'f_cbet' if hp else 'f_stab' if hip else 'f_first'
                        elif s == 2:
                            nd = 't_barrel' if hb(1, 'Hero') else ('t_probe' if not hp and not hip else 't_delay') if xx(1) else 't_stab' if hip else 't_first'
                        else:
                            nd = 'r_barrel' if hb(1, 'Hero') and hb(2, 'Hero') else 'r_stab'
                    if sp == '3bp': nd = ('3b_' if hp else '3c_') + (nd if nd != 'r_vs_bet' or hp else 'r_vs_bet2')
                    if sp == '3bp' and nd == '3c_f_stab': cond = {}
                    if sp == 'iso' and kind == 'ISO' and not hp: nd = 'iso_' + nd
                    if sp == 'iso' and kind == 'LMP': nd = ('lmp_f_stab' if hip else 'lmp_f_lead') if (s == 1 and facing is None) else 'lmp_' + nd
                    if sp == '3bp' and nd == '3c_f_vs_cbet' and fx >= 1.0: nd = '3c_f_vs_over'
                    if sp == '3bp' or sp == 'iso': cond.pop('tx', None)
                    if sp == '3bp' and nd == '3c_r_vs_bet2': cond = {'sz': GRP(szb(fx))}
                    if sp == 'iso' and nd == 'r_vs_bet': cond = {'sz': GRP(szb(fx))}
                    if sp == 'opfr' and nd == 'r_vs_bet': cond = {'sz': GRP(szb(fx))}
                if s == 3: cond['ct'] = ctype(bd,3)
                mw_eligible = True
                if sp == 'mw':
                    mw_eligible = True
                r = match(sp, nd, c, cond) if nd not in ('none', 'raise') and mw_eligible else None
                BY[sp] += 1
                if r: cov += 1; BYC[sp] += 1; MATCHED.append((h['id'], s, r['id'], r['b']))
                else: MISS[(sp, nd, c if not IDX.get((sp, nd)) or True else '')] += 1
            if v in ('b', 'r'): pending = set(live) - allin - {p}
            else: pending.discard(p)
            if v == 'b' and facing is None: facing = 'b'; bet_by = p; fx = x / max(potst + cur, 0.1)
            elif v == 'r': facing = 'r'; bet_by = p
            if p == 'Hero' and v in 'br': hero_bet = True
            if p == 'Hero' and v == 'r': hero_raised = True
            if p != 'Hero' and v == 'b': pass
            cur += x if v in 'bc' else (x if v == 'r' else 0)
            if ai: allin.add(p); pending.discard(p)
            if v == 'f' and p in live: live.remove(p)
        hist[s] = [(p, v) for (p, v, x, to, ai) in acts]
        pot = potst + cur
print('decisions', tot, 'covered', cov, f"{cov / tot:.1%}")
for sp in BY: print(f"  {sp:5} {BYC[sp]}/{BY[sp]} {BYC[sp] / BY[sp]:.0%}")
print('direct', sum(1 for *_, b in MATCHED if not b.startswith('alias')), 'alias', sum(1 for *_, b in MATCHED if b.startswith('alias')))
print('basis of matched', Counter(b for *_, b in MATCHED))
spm = Counter()
for (sp, nd, c), v in MISS.items(): spm[(sp, nd)] += v
for k, v in spm.most_common(25): print('miss', k, v)
json.dump(dict(tot=tot, cov=cov, direct=sum(1 for *_, b in MATCHED if not b.startswith('alias')), by={k: [BYC[k], BY[k]] for k in BY}, basis=dict(Counter(b for *_, b in MATCHED)), miss=[[list(k), v] for k, v in spm.most_common(40)], rowhits=dict(Counter(rid for _, _, rid, _ in MATCHED))), open(args.out, 'w'), ensure_ascii=False)
