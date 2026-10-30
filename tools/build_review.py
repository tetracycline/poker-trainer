#!/usr/bin/env python3
"""Build one 覆盤 (session review) page for the poker trainer.

Usage:
  python3 tools/build_review.py --hands /path/to/<day>/hands.json --config /path/to/review_config.json [--repo .]

Inputs (kept OFF the public site):
  hands.json   output of analyze.py (GG / Natural8 parser) for one session
  config.json  day text: result, conclusion, stats rows, leaks, costly-hand picks (see tools/README_review.md)
Single source of truth for answers: <repo>/pf_data.js (same file the v8 trainer uses).
Outputs (public):
  review/data/<date>.js   window.RV = {...}  (sanitised: positions only, no screen names, no raw text)
  review/<date>.html      page shell
  review/data/index.js    window.RVI = [...] list of all reviews (newest first)
"""
import argparse, hashlib, json, os, re, sys

RK = '23456789TJQKA'
def lab(c):
    a, b = c.split(); x, y = RK.index(a[0]), RK.index(b[0]); s = a[1] == b[1]
    if x < y: x, y = y, x
    return RK[x] * 2 if x == y else RK[x] + RK[y] + ('s' if s else 'o')

def load_pf(repo):
    t = open(os.path.join(repo, 'pf_data.js'), encoding='utf-8').read()
    return json.loads(t[t.index('{'):t.rindex('}') + 1])

def ok_acts(PF, n, v, h):
    nd = PF['nodes'][n]; s = nd[v]['s'][PF['names'].index(h)]; m = max(range(len(s)), key=lambda j: s[j])
    return nd['acts'][m], [nd['acts'][j] for j in range(len(s)) if j == m or s[j] >= 25]

def pre_decisions(H, PF):
    """Map each hero preflop decision onto a v8 tree node (clean heads-up lines only)."""
    out = []
    amap = {'folds': 'fold', 'calls': 'call'}
    for h in H:
        pre = [a for a in h['actions'] if a[0] == 'pre']; pos = h['allpos']; hp = h['pos']
        raises, callers, node, nh = [], 0, None, 0
        for k, (st, p, act, amt, ai) in enumerate(pre):
            if p == 'Hero':
                cand = None
                if nh == 0:
                    if not raises and callers == 0 and hp != 'BB' and act in ('raises', 'folds'):
                        cand = (f'{hp}rfi', 'open' if act == 'raises' else 'fold')
                    elif len(raises) == 1 and callers == 0:
                        cand = (f"{pos.get(raises[0][0])}open>{hp}", {'raises': '3bet'}.get(act, amap.get(act)))
                elif nh == 1 and node and node[0].endswith('rfi') and node[1] == 'open' and len(raises) == 2 and callers == 0:
                    cand = (f"{hp}open>{pos.get(raises[1][0])}3b", {'raises': '4bet'}.get(act, amap.get(act)))
                elif nh == 1 and node and node[1] == '3bet' and len(raises) == 3 and callers == 0:
                    cand = (node[0] + '3b>4b', {'raises': 'jam'}.get(act, amap.get(act)))
                node = None
                if cand and cand[0] in PF['nodes'] and cand[1] in PF['nodes'][cand[0]]['acts']:
                    node = cand; n = PF['nodes'][cand[0]]; i = PF['names'].index(lab(h['hero_cards']))
                    ev = n['exp']['ev'][i]; best = max(ev); ch = ev[n['acts'].index(cand[1])]
                    main, ok = ok_acts(PF, cand[0], 'exp', lab(h['hero_cards']))
                    out.append(dict(id=h['id'], node=cand[0], act=cand[1], hand=lab(h['hero_cards']), cards=h['hero_cards'].split(),
                                    k=k, loss=round((best - ch) / 100, 2), bad=cand[1] not in ok, main=main))
                nh += 1
            if act == 'raises': raises.append((p, amt))
            elif act == 'calls': callers += 1
    return out

ZACT = {'folds': 'fold', 'checks': 'check', 'calls': 'call', 'bets': 'bet', 'raises': 'raise'}
def replay(h, bb):
    """Sanitised replay: players -> position labels, hero -> 'Hero'; amounts in bb."""
    pos = h['allpos']; who = lambda p: 'Hero' if p == 'Hero' else pos.get(p, '?')
    acts = [[a[0], who(a[1]), ZACT[a[2]], round(a[3] / bb, 2), bool(a[4])] for a in h['actions']]
    # pot before each action + amount hero must add (blinds; a non-BB player who checks preflop posted 1bb)
    put = {}; st0 = None; pots = []; tocall = []; tot = 0.0
    for a in acts:
        if a[0] != st0:
            st0 = a[0]; tot += sum(put.values()); put = {}
            if st0 == 'pre':
                for p, q in pos.items():
                    if q == 'SB': put['SB'] = 0.5
                    if q == 'BB': put['BB'] = 1.0
                for b in acts:
                    if b[0] == 'pre' and b[2] == 'check' and b[1] != 'BB': put[b[1]] = 1.0
        pots.append(round(tot + sum(put.values()), 2)); tocall.append(round(max(put.values(), default=0) - put.get(a[1], 0), 2))
        if a[2] == 'raise': put[a[1]] = a[3]
        elif a[2] in ('call', 'bet'): put[a[1]] = put.get(a[1], 0) + a[3]
    shows = {who(p): c.split() for p, c in (h.get('shows') or {}).items()}
    order = ['SB', 'BB', 'UTG', 'HJ', 'CO', 'BTN']
    return dict(id=h['id'], pos=h['pos'], cards=h['hero_cards'].split(), board=h['board'].split() if h['board'] else [],
                stack=round(h['hero_stack'] / bb, 1), players=sorted(set(pos.values()), key=lambda x: order.index(x) if x in order else 9),
                acts=acts, pots=pots, tocall=tocall, net=round(h['net'] / bb, 1), shows=shows, pot=round(h.get('pot', 0) / bb, 1))

def dec_index(rp, dec, pre_k=None):
    if dec == 'pre': return pre_k
    st, k = dec['st'], dec['k']; c = 0
    for i, a in enumerate(rp['acts']):
        if a[0] == st and a[1] == 'Hero':
            if c == k: return i
            c += 1
    raise SystemExit(f"decision {dec} not found in {rp['id']}")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--hands', required=True); ap.add_argument('--config', required=True)
    ap.add_argument('--repo', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument('--min-loss', type=float, default=0.0, help='drill = hero actions the site grading marks wrong (exploit), with EV loss >= this')
    A = ap.parse_args()
    PF = load_pf(A.repo); C = json.load(open(A.config, encoding='utf-8'))
    J = json.load(open(A.hands, encoding='utf-8')); H = J['hands']; S = J['summary']; byid = {h['id']: h for h in H}
    bb = H[0]['bb']; date = C['date']
    D = pre_decisions(H, PF); dmap = {(d['id']): d for d in D}
    pre_by = {}
    for d in D: pre_by.setdefault(d['id'], []).append(d)
    # drill: every preflop decision the site's own grading (exploit) marks wrong
    drill = []
    for d in sorted([d for d in D if d['bad'] and d['loss'] >= A.min_loss], key=lambda d: -d['loss']):
        rp = replay(byid[d['id']], bb); drill.append(dict(kind='pre', node=d['node'], h=d['hand'], you=d['act'], loss=d['loss'], at=d['k'], hand=rp))
    # costly hands quiz
    costly = []
    for c in C.get('costly', []):
        h = byid[c['id']]; rp = replay(h, bb)
        if c['dec'] == 'pre':
            ds = pre_by.get(c['id'], [])
            if not ds: raise SystemExit(f"{c['id']}: no preflop decision maps to the v8 tree")
            d = ds[c['pre_n']] if 'pre_n' in c else next((x for x in ds if x['bad']), ds[0])
            if not d['bad']: print(f"WARN {c['id']}: hero action {d['act']} is not graded wrong at {d['node']}", file=sys.stderr)
            costly.append(dict(kind='pre', node=d['node'], h=d['hand'], you=d['act'], loss=d['loss'], at=d['k'], hand=rp, why=c.get('why', '')))
        else:
            i = dec_index(rp, c['dec']); you = rp['acts'][i][2]
            yk = c.get('you') or {'fold': 'fold', 'call': 'call', 'check': 'check', 'raise': 'raise', 'bet': 'bet'}.get(you)
            if c['dec']['st'] != 'pre' and rp['acts'][i][4]: yk = c.get('you') or 'jam'
            if yk not in [o[0] for o in c['opts']]: yk = c.get('you', yk)
            costly.append(dict(kind='post', at=i, opts=c['opts'], ok=c['ok'], you=yk, hand=rp, why=c.get('why', '')))
    # privacy check: no screen names left anywhere
    names = set(p for h in H for p in h['allpos'] if p != 'Hero')
    RV = dict(date=date, title=C['title'], session=C.get('session', ''), result=C['result'], conclusion=C['conclusion'], stats=C['stats'],
              stats_note=C.get('stats_note', ''), leaks=C['leaks'], post_notes=C.get('post_notes', []), costly=costly, drill=drill,
              hands=S['hands'], pf_ver='v8', n_decisions=len(D), n_bad=len(drill), loss_total=round(sum(d['loss'] for d in D), 1))
    blob = json.dumps(RV, ensure_ascii=False, separators=(',', ':'))
    leak = [n for n in names if n in blob]
    if leak: raise SystemExit(f'privacy check failed: {leak[:5]}')
    rd = os.path.join(A.repo, 'review'); os.makedirs(os.path.join(rd, 'data'), exist_ok=True)
    open(os.path.join(rd, 'data', f'{date}.js'), 'w', encoding='utf-8').write('window.RV=' + blob + ';\n')
    tpl = open(os.path.join(rd, 'day.tpl.html'), encoding='utf-8').read()
    open(os.path.join(rd, f'{date}.html'), 'w', encoding='utf-8').write(tpl.replace('{{DATE}}', date).replace('{{TITLE}}', C['title']).replace('data/' + date + '.js?v=1', 'data/' + date + '.js?v=' + hashlib.md5(blob.encode()).hexdigest()[:8]))
    # index (newest first)
    ip = os.path.join(rd, 'data', 'index.js'); L = []
    if os.path.exists(ip):
        t = open(ip, encoding='utf-8').read(); L = json.loads(t[t.index('['):t.rindex(']') + 1])
    L = [x for x in L if x['date'] != date] + [dict(date=date, title=C['title'], hands=S['hands'], net_bb=C['result']['net_bb'], bb100=C['result']['bb100'],
              adj_bb100=C['result'].get('adj_bb100'), n_costly=len(costly), n_drill=len(drill), top=[l['t'] for l in C['leaks']][:3])]
    L.sort(key=lambda x: x['date'], reverse=True)
    open(ip, 'w', encoding='utf-8').write('window.RVI=' + json.dumps(L, ensure_ascii=False, indent=0) + ';\n')
    ix = os.path.join(rd, 'index.html'); s = open(ix, encoding='utf-8').read()
    open(ix, 'w', encoding='utf-8').write(re.sub(r'data/index\.js\?v=[\w-]+', 'data/index.js?v=' + L[0]['date'], s))
    rx = os.path.join(A.repo, 'index.html'); s = open(rx, encoding='utf-8').read()
    open(rx, 'w', encoding='utf-8').write(re.sub(r'review/data/index\.js\?v=[\w-]+', 'review/data/index.js?v=' + L[0]['date'], s))
    print(f'{date}: {len(D)} preflop decisions mapped, drill {len(drill)}, costly {len(costly)}, EV loss {RV["loss_total"]}bb -> review/{date}.html')

if __name__ == '__main__':
    main()
