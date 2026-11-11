#!/usr/bin/env python3
"""練習題例題的真實牌路檢查 → nl2_drillpath.js（window.NL2_EGBAD：{列 id: [不能出題的例題序號]}）
每個例題用正式分類器 run10_common.classes 算出它在翻牌／轉牌／河牌的實際牌型，
（1）到這一街的牌型必須在這一格；（2）這一格的條件（翻牌質地、最高張、河牌牌型、下注尺寸、線）要符合實際牌面；
（3）這條線上你先前每個決定：用「那一街的實際牌型＋實際牌面」查表（例外列優先），主答案必須就是例題的動作。
任何一項不符 → 這個例題不出題（表格不受影響、答案不變）。用法：python3 tools/build_drill_paths.py [repoRoot]"""
import sys, os, json, subprocess, collections
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(H)
sys.path[:0] = [os.path.join(H, 'lines_pipeline'), '/workspace/outputs/poker/lines1105', '/workspace/outputs/poker_solver/read_v1']
from run10_common import classes
from common import texture, ctype
D = json.loads(subprocess.check_output(['node', os.path.join(H, 'dump_drill_candidates.js'), ROOT]))
by = collections.defaultdict(list)
for r in D['rows']: by[(r['sp'], r['nd'])].append(r)
RK = '23456789TJQKA'; ST = ['翻牌', '轉牌', '河牌']
HN = {'S': '兩對+', 'TPG': '頂對好', 'TPW': '頂對弱', 'MID': '中小對', 'DRAW': '強聽', 'WDRAW': '弱聽', 'AIR': '空氣'}
def hi(b, k): return 'T' if max(RK.index(b[i]) for i in range(0, 2 * (3 + k), 2)) >= RK.index('T') else 'L'
def szb(x): return 'le50' if x <= 0.60 else 'p75' if x <= 1.15 else 'o150'
def fits(r, e, k, F, segs):
    b = e['b']
    for key, v in r['c'].items():
        if key == 'tx' and texture(b[:6]) != v: return False
        if key == 'hi' and hi(b, k) != v: return False
        if key == 'ct' and (k == 0 or ctype(b, k + 1) != v): return False
        if key == 'sz':
            last = [t for t in segs[k].split(' ') if t and t.split(':')[0] != e['me'] and t.split(':')[1][:1] in 'bra']
            if last and last[-1].split(':')[1][:1] == 'b' and szb(float(last[-1].split(':')[1][1:])) != v: return False
        if key == 'ln' and (v == 'tb') != F['tb']: return False
        if key == 'prior' and ((v == 'check_turn' and not F['checkTurn']) or (v == 'bet_bet' and not F['betBet'])): return False
        if key == 'hr' and (v == 'PFR') != F['pfr']: return False
    return True
def answer(sp, nd, h, e, k, F, segs):
    R = [r for r in by[(sp, nd)] if h in r['hc']]
    ex = [r for r in R if r['x'] and fits(r, e, k, F, segs)]
    if ex: return ex[0]
    base = [r for r in R if not r['x'] and fits(r, e, k, F, segs)]
    return base[0] if base else None
bad, why = [], collections.Counter()
for it in D['items']:
    e, st, F = it['e'], it['st'], it['facts']; segs = e['l'].split('/')
    r0 = next(r for r in by[(it['sp'], it['nd'])] if r['id'] == it['id'])
    if len(e['b']) < 2 * (3 + st): bad.append((it, '牌面張數不足')); continue
    cls = [classes(e['h'], e['b'][:2 * (3 + k)])[0] for k in range(st + 1)]
    if cls[st] not in it['hc']: bad.append((it, f'實際牌型是{HN[cls[st]]}，不在這一格')); continue
    if not fits(r0, e, st, F, segs): bad.append((it, '實際牌面／尺寸不符這一格的條件')); continue
    if not r0['x']:
        a = answer(it['sp'], it['nd'], cls[st], e, st, F, segs)
        if a and a['x'] and a['a'] != r0['a']: bad.append((it, '實際牌面屬於例外列，正解不同')); continue
    msg = None
    for d in it['decs']:
        h = cls[d['st']]; got = [answer(it['sp'], nd, h, e, d['st'], F, segs) for nd in d['nds']]
        if not any(a and a['a'] in d['need'] for a in got):
            msg = f"{ST[d['st']]}實際是{HN[h]}，表上不會{d['verb']}"; break
    if msg: bad.append((it, msg))
for it, m in bad: why[m.split('，')[0] if '實際是' not in m else '前面的動作不是表上答案'] += 1
keys = collections.defaultdict(set)
for it, _ in bad: keys[it['id']].add(it['i'])
keys = {k: sorted(v) for k, v in sorted(keys.items())}
with open(os.path.join(ROOT, 'nl2_drillpath.js'), 'w', encoding='utf8') as f:
    f.write('// 產生：tools/build_drill_paths.py（正式分類器逐街算例題的實際牌型）。這些例題的牌路跟表上答案對不上，不拿來出題。\n')
    f.write('window.NL2_EGBAD = ' + json.dumps(keys, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(f"例題 {len(D['items'])}，不出題 {sum(len(v) for v in keys.values())}", dict(why))
