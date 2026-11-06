#!/usr/bin/env python3
"""Build the shared NL2 table/drills using only local solver GTO and supported pool evidence.
The v2 evidence gate reads /workspace/outputs/poker_lines_v2/results/solved.json,
rejects unsupported/insignificant recommendations, and records every old row disposition.
Reproduce: python3 /workspace/outputs/poker_lines_v2/solve_rules.py; python3 tools/build_lines.py.
"""
import json, math, os, re, subprocess, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST = '/workspace/outputs/poker/lines1105'
random.seed(11)
def js(path, var):
    o = subprocess.run(['node', '-e', f"global.window=global;for(const p of {json.dumps(path)})eval(require('fs').readFileSync(p,'utf8'));process.stdout.write(JSON.stringify({var}))"], capture_output=True, text=True, cwd=ROOT)
    return json.loads(o.stdout)
LD = js(['learn_data.js', 'reads_data.js'], 'window.LD'); HWR = js(['hwrange.js'], 'window.HWR')
RV = json.load(open(f'{ST}/river.json')); FT = json.load(open(f'{ST}/fturn.json'))['F']; MW = json.load(open(f'{ST}/mw.json')); ISO = json.load(open(f'{ST}/iso.json'))
EG = json.load(open(f'{ST}/eg.json')); EGM = json.load(open(f'{ST}/eg_mw.json'))
HC = {'S': '兩對以上（含三條）', 'TPG': '超對／頂對好踢（J 以上）', 'TPW': '頂對弱踢', 'MID': '中小對', 'DRAW': '強聽牌（同花聽、兩頭順）', 'WDRAW': '弱聽牌／兩張高牌', 'AIR': '空氣'}
LDH = {'strong': 'S', 'top_good': 'TPG', 'top_weak': 'TPW', 'mid_low': 'MID', 'draw': 'DRAW', 'weak_draw': 'WDRAW', 'air': 'AIR'}
TX = {'A_high': 'A 高面', 'KQ_high': 'K/Q 高面', 'mid_high': 'J–9 高面', 'low': '8 以下低牌面', 'paired': '成對面', 'mono': '單色面'}
CT = {'str4': '單張成順（再一張牌就成順）', 'flush': '同花第三張', 'pair': '公牌成對', 'blank': '空白', 'over': '高張', 'str3': '兩張成順'}
SZ = {'le50': '≤½ 池', 'p75': '¾–1 池', 'o150': '超池（1.5 池）', 'all': '任何尺寸（到 1 池）'}
f0 = lambda x: f"{x:,}"
pc = lambda a, b: round(100 * a / b) if b else 0
def ci(p, n): return 1.96 * math.sqrt(max(p * (1 - p), 1e-9) / n) * 100
def need_of(g, ns):  # 跟注需要的勝率 b/(1+2b)，依尺寸組內各桶的 n 加權
    W = {'s33': 0.33, 's50': 0.5, 's75': 0.75, 's100': 1.0, 's150': 1.5}
    tot = sum(ns.values()) or 1
    return 100 * sum(ns[k] * W[k] / (1 + 2 * W[k]) for k in ns) / tot
GB = {'le50': ['s33', 's50'], 'p75': ['s75', 's100'], 'o150': ['s150']}
GB3 = ['le50', 'p75', 'o150']
GBA = dict(GB, all=['s33', 's50', 's75', 's100'])
def rvW(spot, line, g, ct, c):  # 河牌跟注者勝率（line='*' 或某條線；ct 牌型或 '*'）
    w = n = 0; ns = {}
    for sb in GBA[g]:
        v = RV['W'].get(f"{spot}|{line}|{sb}|{ct}|{c}")
        if v: w += v[0]; n += v[1]
        f = RV['F'].get(f"{spot}|{line}|{sb}|{ct}") or RV['F'].get(f"{spot}|{line}|{sb}|*")
        ns[sb] = (f or [0, 1])[1]
    return w, n, need_of(g, ns)
def rvW_oth(spot, tbl, g, c):  # 「不是三槍」的線＝全部 − 三槍
    w1, n1, nd = rvW(spot, '*', g, '*', c); w2, n2, _ = rvW(spot, tbl, g, '*', c)
    return w1 - w2, n1 - n2, nd
def verdict(w, n, need, cls_a=('c', 'f')):
    p = w / n; e = ci(p, n); p *= 100
    if p - need > e: return cls_a[0], [], 'sig', p, e
    if need - p > e: return cls_a[1], [], 'sig', p, e
    return (cls_a[0] if p >= need else cls_a[1]), [cls_a[1] if p >= need else cls_a[0]], 'ns', p, e
POSV = {'SRP_PFRbets_IP': ('UTG/HJ/CO/BTN 開池', 'BB/SB 跟（沒位置）'), 'SRP_CALLERbets_OOP': ('你開池（有位置）', 'BB/SB 跟注後先下注'),
        'SRP_PFRbets_OOP': ('前位開池（UTG/HJ/CO/SB，沒位置）', '後位跟（HJ/CO/BTN/BB，有位置）'), 'SRP_CALLERbets_IP': ('你開池（UTG/HJ/CO/SB，沒位置）', '後位跟注者（HJ/CO/BTN/BB）下注'),
        '3BP_PFRbets_IP': ('3-bet 的人（有位置）', '你跟 3-bet'), '3BP_PFRbets_OOP': ('SB/BB 3-bet（沒位置）', '你 BTN/CO 跟 3-bet'),
        'ISO_CALLERbets_OOP': ('你隔離加注（HJ/CO/BTN/SB/BB）', 'limp 的人（UTG–SB）跟注後先下注')}
ROWS = []; SPOTS = []
def row(sp, nd, hc, a, ok, why, b, ev, cond=None, ex=False, eg=None, src=None, L=None):
    if b == 'pool' and not re.search(r'UTG|HJ|CO|BTN|SB|BB', ev): ev = ev.replace('玩家池：', '玩家池（全部位置 UTG–BB 合併）：', 1)
    r = dict(sp=sp, nd=nd, hc=hc if isinstance(hc, list) else [hc], a=a, ok=ok or [], why=why, b=b, ev=ev, eg=eg or [])
    if cond: r['c'] = cond
    if ex: r['x'] = 1
    if src: r['src'] = src
    if L: r['L'] = L
    ROWS.append(r); return r
# ------------- 1. 沿用 LD.rules（行動線題）-------------
LDMAP = {'SRP_IP': 'ipfr', 'SRP_BB': 'bb', '3BP_3bettor': '3bet', '3BP_caller': '3call'}
CATN = {'f_cbet': 'f_cbet', 'barrel': 't_barrel', 'delay': 't_delay', 'r_barrel': 'r_barrel', 'r_stab': 'r_stab', 'vs_probe': 't_vs_probe', 'r_vs_bet': 'r_vs_bet',
        'f_vs_cbet': 'f_vs_cbet', 'vs_barrel': 't_vs_barrel', 'probe': 't_probe'}
SPM = {'BTN_BB': ['BB', 'BTN', 1, 'SRP', 5.5, 97.5], 'CO_BB': ['BB', 'CO', 1, 'SRP', 5.5, 97.5], 'HJ_BB': ['BB', 'HJ', 1, 'SRP', 5.5, 97.5], 'UTG_BB': ['BB', 'UTG', 1, 'SRP', 5.5, 97.5],
       'SB_BB': ['SB', 'BB', 0, 'SRP', 6, 97], 'SB3_BTN': ['SB', 'BTN', 0, '3BP', 21, 90], 'BB3_BTN': ['BB', 'BTN', 0, '3BP', 20.5, 90]}
def ld_eg(e):
    h, b, sp, pot, l, p = e; oop, ip, pfr, kind, P0, stk = SPM[sp]; pos = [oop, ip]
    S = l.split('/') if l else ['']; out = []
    for st in S:
        tk = st.split(' ') if st else []
        out.append(' '.join(f"{pos[k % 2]}:{t if t[0] != 'b' else 'b' + str(int(t[1:]) / 100)}" + ('3' if t == 'r' else '') for k, t in enumerate(tk)))
    me = pos[p]; o = pos[pfr] if kind == 'SRP' else pos[1 - pfr]; c3 = pos[pfr] if kind == '3BP' else None
    pre = (f"{o}|open" if kind == 'SRP' else f"{o}|open|{c3}|3b")
    return dict(h=h, b=b, l='/'.join(out), me=me, pre=pre, pos=pos, pot=P0, stk=stk)
for r in LD['rules']:
    sp = LDMAP[r['group']]; cat = r['cat']
    nd = CATN.get(cat) or (('f_vs_xr' if r['street'] == 'flop' else 't_vs_xr') if cat == 'vs_raise' else cat)
    if sp in ('3bet', '3call'): sp = '3bp'; nd = ('3b_' if r['group'] == '3BP_3bettor' else '3c_') + nd
    b = 'pool' if r.get('dev') else 'gto'
    ev = (r.get('psc') or '') + ('｜' if r.get('psc') and r.get('gl') else '') + (r.get('gl') or '')
    cond = {'tx': r['tx']} if r.get('tx') else None
    row(sp, nd, LDH[r['hc']], r['ans'], r.get('ok'), r['why'], b, ev, cond, eg=[ld_eg(e) for e in r['ex']], src='ld:' + r['id'])
# ------------- 2. 河牌面對下注：依尺寸（玩家池跟注後攤牌勝率）-------------
CLS5 = ['S', 'TPG', 'TPW', 'MID', 'AIR']
def eg_rv(spot, lg, g, ct, c, me_role):
    L = EG.get(f"RV|{spot}|{lg}|{g}|{ct}|{c}") or []
    return [dict(e, me=e['me']) for e in L[:30]]
def river_rows(sp, nd, spot, tbl, lab, linesplit=True):
    who = POSV[spot]
    lines = [('tb', tbl, '三槍（翻、轉、河都下注）'), ('oth', None, '不是三槍（前面有一街過牌）')] if linesplit else [('*', '*', '全部行動線')]
    for lg, L, lz in lines:
        for g in GB3:
            for c in CLS5:
                cc = [c] + (['WDRAW'] if c == 'AIR' else [])
                def get(lg2):
                    if lg2 == 'oth': w, n, need = rvW_oth(spot, tbl, g, c)
                    else: w, n, need = rvW(spot, tbl if lg2 == 'tb' else '*', g, '*', c)
                    if c == 'AIR':
                        w2, n2, _ = (rvW_oth(spot, tbl, g, 'WDRAW') if lg2 == 'oth' else rvW(spot, tbl if lg2 == 'tb' else '*', g, '*', 'WDRAW')); w += w2; n += n2
                    return w, n, need
                w, n, need = get(lg); fb = ''
                if n < 40 and lg != '*':
                    fb = f"（{lz.split('（')[0]}樣本只有 n={n}，改用全部行動線）"; w, n, need = get('*')
                if n < 40:
                    if g == 'o150' and c in ('TPG', 'TPW', 'MID'):
                        row(sp, nd, c, 'f', ['c'], '超池樣本不夠（n<40）：照規則卡，一對面對超池預設棄', 'rule', f"玩家池：{who[0]}・{who[1]}｜{lab}｜{lz}｜河牌超池｜{HC[c]}跟注只有 n={n}，樣本不足，不下結論；原則：超池需要 38% 勝率", dict(sz=g, ln=lg) if lg != '*' else dict(sz=g), eg=eg_rv(spot, '*', g, '*', c, None))
                    continue
                a, ok, sig, p, e = verdict(w, n, need)
                pol = ''
                if sig == 'ns' and c == 'AIR': a, ok = 'f', ['c']  # 沒成牌、差距在誤差內：預設棄
                if sig == 'ns' and g == 'o150' and c in ('TPG', 'TPW', 'MID') and a == 'c': a, ok, pol = 'f', ['c'], '；超池一對預設棄'
                why = f"跟注後攤牌勝率 {p:.0f}%，需要 {need:.0f}% → " + ('跟' if a == 'c' else '棄') + ('' if sig == 'sig' else f'（差距在誤差內，跟或棄都可以{pol}）')
                ev = f"玩家池：{who[0]}・{who[1]}｜{lab}｜{lz}{fb}｜河牌 {SZ[g]}｜{HC[c]}跟注 n={f0(n)}：勝率 {p:.0f}%±{e:.0f}（需要 {need:.0f}%）→ {'顯著' if sig == 'sig' else '不明顯'}"
                row(sp, nd, cc, a, ok, why, 'pool', ev, dict(sz=g, ln=lg) if lg != '*' else dict(sz=g), eg=eg_rv(spot, '*' if fb else lg, g, '*', c, None) or eg_rv(spot, '*', g, '*', c, None))
        # 例外：河牌牌型
    for ct in ('str4', 'flush'):
        for c in ('TPG', 'TPW', 'MID'):
            G = [g for g in ('le50', 'p75') if rvW(spot, '*', g, ct, c)[1] >= 40]
            if not G and rvW(spot, '*', 'all', ct, c)[1] >= 40: G = ['all']
            for g in G:
                w, n, need = rvW(spot, '*', g, ct, c)
                a, ok, sig, p, e = verdict(w, n, need)
                base = [x for x in ROWS if x['sp'] == sp and x['nd'] == nd and c in x['hc'] and not x.get('x') and x.get('c', {}).get('sz') in ((g,) if g != 'all' else ('le50', 'p75'))]
                if base and all(x['a'] == a for x in base): continue  # 跟一般規則一樣就不列
                why = f"河牌{CT[ct]}：{HC[c]}跟注後勝率 {p:.0f}%，需要 {need:.0f}% → " + ('跟' if a == 'c' else '棄') + ('' if sig == 'sig' else '（差距在誤差內）')
                ev = f"玩家池：{who[0]}・{who[1]}｜{lab}｜全部行動線｜河牌是{CT[ct]}、{SZ[g]}｜{HC[c]}跟注 n={f0(n)}：勝率 {p:.0f}%±{e:.0f}（需要 {need:.0f}%）→ {'顯著' if sig == 'sig' else '不明顯'}"
                row(sp, nd, c, a, ok, why, 'pool', ev, dict(sz=g, ct=ct), ex=True, eg=eg_rv(spot, '*', g, ct, c, None))
river_rows('bb', 'r_vs_bet', 'SRP_PFRbets_IP', 'Cx Ab Cc/Cx Ab Cc', '單加注底池・單挑・有效 ≥40bb')
river_rows('ipfr', 'r_vs_bet', 'SRP_CALLERbets_OOP', None, '單加注底池・單挑・有效 ≥40bb', linesplit=False)
river_rows('ipc', 'r_vs_bet', 'SRP_PFRbets_OOP', 'Ab Cc/Ab Cc', '單加注底池・單挑・有效 ≥40bb')
river_rows('opfr', 'r_vs_bet', 'SRP_CALLERbets_IP', None, '單加注底池・單挑・有效 ≥40bb', linesplit=False)
river_rows('3bp', '3c_r_vs_bet2', '3BP_PFRbets_OOP', 'Ab Cc/Ab Cc', '3-bet 底池・單挑', linesplit=False)
river_rows('iso', 'r_vs_bet', 'ISO_CALLERbets_OOP', None, '隔離底池（limp 後你加注）・單挑', linesplit=False)
# 舊的 LD r_vs_bet（≤½ 或 >½ 單一尺寸）被上面依尺寸的列取代：只留在 learn.html 題目裡，這裡移除，避免兩套
ROWS[:] = [r for r in ROWS if not (r.get('src', '').startswith('ld:') and '|r_vs_bet|' in r['src'])]
# ------------- 3. 河牌你下注被加注 -------------
def rr_rows(sp, t, rpos, lab, need=26):
    for c in ['S', 'TPG', 'TPW', 'MID']:
        v = FT.get(f"RR|{t}|{rpos}|*|callerwin|{c}")
        if not v or v[2] < 40: continue
        a, ok, sig, p, e = verdict(v[0], v[2], need)
        if sig == 'ns': a, ok = 'f', ['c']  # 差距在誤差內：照規則卡「一對被加注就棄」
        tot = FT.get(f"RR|{t}|{rpos}|*")
        why = f"被加注後跟注的攤牌勝率 {p:.0f}%，需要約 {need}% → " + ('跟' if a == 'c' else '棄') + ('' if sig == 'sig' else '（差距在誤差內，照規則卡預設棄，跟也可以）')
        ev = f"玩家池：{lab}｜河牌你下注、對手加注（約 3 倍）｜{HC[c]}跟注 n={f0(v[2])}：勝率 {p:.0f}%±{e:.0f}（需要 {need}%：⅔ 池下注被加到 3 倍）→ {'顯著' if sig == 'sig' else '不明顯'}" + (f"｜加注總數 n={f0(tot[2])}，對手攤牌時兩對以上占多數" if tot else '')
        row(sp, 'r_vs_xr', c, a, ok, why, 'pool', ev, eg=(EG.get(f"RR|{t}|{rpos}|*|{c}") or [])[:30])
    row(sp, 'r_vs_xr', ['DRAW', 'WDRAW', 'AIR'], 'f', [], '河牌沒成牌，被加注只能棄', 'rule', '原則（沒成牌不可能跟）')
rr_rows('ipfr', 'SRP', 'raiserOOP', '你開池有位置・BB/SB 跟（單挑）')
rr_rows('bb', 'SRP', 'raiserIP', '你在 BB/SB・開池者有位置（單挑）')
rr_rows('opfr', 'SRP', 'raiserIP', '你開池沒位置（UTG/HJ/CO/SB）・後位跟（單挑）')
# ------------- 4. 沒位置 c-bet（依牌面：空氣用棄牌率決定）-------------
def be(x): return 100 * x / (1 + x)
for tx in TX:
    v = FT.get(f"F|SRP|cbet|OOP|{tx}|s33"); v2 = FT.get(f"F|SRP|cbet|OOP|{tx}|s50")
    p = pc(v[0], v[2]); e = ci(v[0] / v[2], v[2]); bb = be(0.33)
    a = 'small' if p - e > bb else 'x'
    why = f"沒位置 33% c-bet 對手棄 {p}%（保本 {bb:.0f}%）→ " + ('小注詐唬賺' if a == 'small' else '詐唬不賺，過牌')
    ev = f"玩家池：前位/SB 開池（沒位置）・後位/BB 跟（單挑）｜翻牌 c-bet 33%｜{TX[tx]}｜n={f0(v[2])}：棄 {p}%±{e:.0f}（保本 {bb:.0f}%）→ {'顯著' if abs(p - bb) > e else '不明顯'}（頻率統計，不需攤牌）"
    row('opfr', 'f_cbet', ['WDRAW', 'AIR'], a, ['x'] if a == 'small' else [], why, 'pool', ev, {'tx': tx}, eg=(EG.get(f"F1|SRP|AOOP|{tx}|AIR") or [])[:15] + (EG.get(f"F1|SRP|AOOP|{tx}|WDRAW") or [])[:15])
    for c, a2, w in [('S', 'big', '價值：大注'), ('TPG', 'small', '價值：小注（沒位置控池）'), ('TPW', 'x', '中等牌沒位置：過牌（跟注小注）'), ('MID', 'x', '有攤牌價值：過牌'), ('DRAW', 'small', '半詐唬：小注')]:
        row('opfr', 'f_cbet', c, a2, ['x'] if c in ('TPG', 'DRAW') else (['small'] if c == 'TPW' else []), w, 'rule', 'GTO 原則（這個點網站沒有解算器解；只有棄牌率數據）', {'tx': tx}, eg=(EG.get(f"F1|SRP|AOOP|{tx}|{c}") or [])[:25])
# ------------- 5. 隔離／limp 底池（單挑）-------------
for who, lab, k in [('AIP', '你隔離加注、有位置，翻牌對手過牌', 'ISO|AIP'), ('CIP', '你在後面 limp／過牌、單挑有位置，翻牌對手過牌', 'LMP|CIP')]:
    v = ISO.get(f"{k}|s33|*") or ISO.get(f"{k.split('|')[0]}|{who}|s33|*")
    p = pc(v[0], v[1]); e = ci(v[0] / v[1], v[1]); bb = be(0.33)
    nd = 'f_cbet' if who == 'AIP' else 'f_stab'
    t = k.split('|')[0]
    ev = f"玩家池：{'BTN/CO/HJ 隔離加注 vs limp 的人' if who == 'AIP' else 'limp 底池・單挑・BTN/CO/SB/BB 有位置的一方'}｜翻牌對手過牌、你下注 33%｜n={f0(v[1])}：棄 {p}%±{e:.0f}（保本 {bb:.0f}%）→ 顯著（頻率統計，不需攤牌）"
    row('iso', nd, ['WDRAW', 'AIR', 'DRAW'], 'small', [], f"對手棄 {p}%，保本只要 {bb:.0f}% → 任何牌小注都賺", 'pool', ev, eg=[e2 for c in ('AIR', 'WDRAW', 'DRAW') for tx in TX for e2 in (EG.get(f"F1|{t}|{who}|{tx}|{c}") or [])[:5]][:30])
    row('iso', nd, ['S', 'TPG', 'TPW', 'MID'], 'small', ['big'] if who == 'AIP' else ['x'], '有牌也小注：對手很少加注、很多會跟', 'rule', 'GTO 原則（隔離底池沒有解算器解）', eg=[e2 for c in ('S', 'TPG', 'TPW', 'MID') for tx in TX for e2 in (EG.get(f"F1|{t}|{who}|{tx}|{c}") or [])[:5]][:30])
# limp 底池沒位置先行動：½ 池領先
v = ISO.get('LMP|AOOP|s50|*'); v1 = ISO.get('LMP|AOOP|s33|*'); p = pc(v[0], v[1]); e = ci(v[0] / v[1], v[1]); p1 = pc(v1[0], v1[1])
ev = f"玩家池：limp 底池・單挑・沒位置的一方（SB/BB）翻牌先下注｜½ 池 n={f0(v[1])}：棄 {p}%±{e:.0f}（保本 33%）→ 顯著；33% 池 n={f0(v1[1])}：棄 {p1}%（保本 25%）→ 不賺（頻率統計，不需攤牌）"
LH = {'small': '下注 ½ 池'}
row('iso', 'f_lead', ['DRAW', 'WDRAW', 'AIR'], 'small', [], f"½ 池下注對手棄 {p}%，保本 33% → 任何牌都下注 ½ 池（33% 只棄 {p1}%，不要下小）", 'pool', ev, L=LH, eg=[e2 for c in ('AIR', 'WDRAW', 'DRAW') for tx in TX for e2 in (EG.get(f"F1|LMP|AOOP|{tx}|{c}") or [])[:5]][:30])
row('iso', 'f_lead', ['S', 'TPG', 'TPW', 'MID'], 'small', ['x'], '有牌也下注 ½ 池：對手很多會跟', 'rule', '原則（limp 底池沒有解算器解）', L=LH, eg=[e2 for c in ('S', 'TPG', 'TPW', 'MID') for tx in TX for e2 in (EG.get(f"F1|LMP|AOOP|{tx}|{c}") or [])[:5]][:30])
# 有位置跟注、開池者翻牌過牌給你
v = FT.get('F|SRP|stab|IP|*|s33'); p = pc(v[0], v[2]); e = ci(v[0] / v[2], v[2])
ev = f"玩家池：前位開池・你有位置跟注（單挑）｜翻牌開池者過牌、你下注 33%｜n={f0(v[2])}：棄 {p}%±{e:.0f}（保本 25%）→ 顯著（頻率統計，不需攤牌）"
row('ipc', 'f_stab', ['WDRAW', 'AIR'], 'small', ['x'], f"開池者過牌後你下 33%，對手棄 {p}%（保本 25%）→ 小注偷", 'pool', ev, eg=(EG.get("F1|SRP|CIP|*|AIR") or [])[:15] + (EG.get("F1|SRP|CIP|*|WDRAW") or [])[:15])
for c, a2, ok2, w in (('S', 'big', ['small'], '價值：大注'), ('TPG', 'small', ['big'], '價值：小注'), ('TPW', 'small', ['x'], '頂對弱踢：小注或過牌'), ('MID', 'x', ['small'], '有攤牌價值：過牌'), ('DRAW', 'small', ['x'], '半詐唬：小注')):
    row('ipc', 'f_stab', c, a2, ok2, w, 'rule', 'GTO 原則（這個點網站沒有解算器解；只有棄牌率數據）', eg=[e2 for tx in TX for e2 in (EG.get(f"F1|SRP|CIP|{tx}|{c}") or [])[:5]][:30])
# BB 先行動
row('bb', 'f_first', ['S', 'TPG', 'TPW', 'MID', 'DRAW', 'WDRAW', 'AIR'], 'x', [], '翻牌先過牌給開池者：BB 直接先下注（donk）的 GTO 頻率很低，等他 c-bet 再決定', 'rule', 'GTO 原則（BB 對有位置的開池者幾乎都過牌）')
row('bb', 't_first', ['S', 'TPG', 'TPW', 'MID', 'DRAW', 'WDRAW', 'AIR'], 'x', [], '翻牌跟注後，轉牌先過牌給開池者（他下注再決定）', 'rule', 'GTO 原則（跟注者轉牌先下注的頻率很低）')
row('3bp', '3c_f_first', ['S', 'TPG', 'TPW', 'MID', 'DRAW', 'WDRAW', 'AIR'], 'x', [], '你跟 3-bet 又沒位置：翻牌先過牌給 3-bet 的人', 'rule', 'GTO 原則（跟注者先下注的頻率很低）')
row('3bp', '3c_t_first', ['S', 'TPG', 'TPW', 'MID', 'DRAW', 'WDRAW', 'AIR'], 'x', [], '翻牌跟注後，轉牌先過牌給 3-bet 的人', 'rule', 'GTO 原則（跟注者轉牌先下注的頻率很低）')
# 讀牌（池攤牌組成＋勝率模型）：donk、隔離底池、3-bet 底池
RDMAP = {'ip_donk': ('ipfr', 'f_vs_donk'), 'iso_donk': ('iso', 'f_vs_donk'), 'iso_xr': ('iso', 'f_vs_xr'), '3c_over': ('3bp', '3c_f_vs_over'), '3b_raised': ('3bp', '3b_f_vs_xr')}
GMAP = {'S': ['S'], 'M': ['TPG'], 'W': ['TPW', 'MID'], 'D': ['DRAW'], 'A': ['WDRAW', 'AIR']}
AMAP = {'加注': 'r', '跟注': 'c', '棄牌': 'f', '邊緣': 'c'}
for rd in LD['reads']:
    if rd['id'] not in RDMAP: continue
    sp, nd = RDMAP[rd['id']]
    for h in rd['hands']:
        a = AMAP.get(h['act'][:2]);
        if not a: continue
        ok = ['f'] if h['act'].startswith('邊緣') else []
        ev = f"{rd['sc']}｜n={f0(rd['n'])}・攤牌 {f0(rd['nsd'])}｜{rd.get('gp', '')}｜{h['zh']}對池範圍勝率約 {h['eq']}%（攤牌樣本，有偏差）"
        row(sp, nd, GMAP[h['g']], a, ok, rd['why'], 'read', ev, src='rd:' + rd['id'])
# ------------- 6. 多人底池（3 人以上）-------------
def mwF(s, t, nk, who, sb): return MW['F'].get(f"B|{s}|{t}|{nk}|{who}|{sb}|*")
for nk in ('3', '4+'):
    v = mwF(1, 'SRP', nk, 'PFR', 's50'); v2 = mwF(1, 'SRP', nk, 'PFR', 's75')
    p = pc(v[0], v[1]); p2 = pc(v2[0], v2[1])
    ev = f"玩家池：單加注底池、翻牌 {nk} 人（開池者先下注）｜½ 池全部棄牌 {p}%（n={f0(v[1])}，保本 33%）、¾ 池 {p2}%（n={f0(v2[1])}，保本 43%）→ 顯著（頻率統計，不需攤牌）"
    row('mw', 'f_bet', ['WDRAW', 'AIR'], 'x', [], f"{nk} 人底池下注幾乎不會讓所有人棄（½ 池只 {p}%）→ 不詐唬", 'pool', ev, {'n': nk}, eg=[e for tx in TX for e in (EGM.get(f"MF|{nk}|PFR|{tx}|AIR") or [])[:5]][:30])
    row('mw', 'f_bet', ['DRAW'], 'x', ['small'], '聽牌不要靠棄牌率：過牌，有人下注再跟', 'rule', f'原則＋池（{nk} 人底池全部棄牌率低）', {'n': nk}, eg=[e for tx in TX for e in (EGM.get(f"MF|{nk}|PFR|{tx}|DRAW") or [])[:5]][:30])
    row('mw', 'f_bet', ['TPW', 'MID'], 'x', [], '中等牌在多人底池過牌：下注只會被更好的牌跟', 'rule', '原則（多人底池沒有解算器解）', {'n': nk}, eg=[e for tx in TX for c in ('TPW', 'MID') for e in (EGM.get(f"MF|{nk}|PFR|{tx}|{c}") or [])[:5]][:30])
    row('mw', 'f_bet', ['S', 'TPG'], 'big', ['small'], '強牌下注收價值：多人底池跟注的人多', 'rule', ev.replace('→ 顯著', '→ 顯著：下注一定有人跟'), {'n': nk}, eg=[e for tx in TX for c in ('S', 'TPG') for e in (EGM.get(f"MF|{nk}|PFR|{tx}|{c}") or [])[:5]][:30])
# 多人底池面對翻牌下注：下注者攤牌組成（有偏差）
for who, lz in (('PFR', '開池者 c-bet'), ('NON', '其他人先下注（donk/領先）')):
    cm = MW['COMP'].get(f"FC|{who}|s75") or {}; n = sum(cm.values())
    sh = {k: pc(v, n) for k, v in cm.items()}
    ev = f"玩家池：多人底池（3 人以上）翻牌{lz} ¾ 池｜攤牌 n={f0(n)}：兩對以上 {sh.get('S', 0)}%、超對/頂對好踢 {sh.get('TPG', 0)}%、頂對弱踢 {sh.get('TPW', 0)}%、中小對 {sh.get('MID', 0)}%、空氣 {sh.get('AIR', 0)}%（攤牌樣本，有偏差）"
    row('mw', 'f_vs_bet', ['S'], 'r', ['c'], '兩對以上加注收價值', 'read', ev, {'by': who})
    row('mw', 'f_vs_bet', ['TPG'], 'c', [], '頂對好踢跟', 'read', ev, {'by': who})
    row('mw', 'f_vs_bet', ['TPW'], 'c' if who == 'NON' else 'f', ['f'] if who == 'NON' else ['c'], ('非開池者先下注：範圍很寬，頂對弱踢跟' if who == 'NON' else '開池者在多人池 c-bet 大注：超對/頂對好踢就占 ' + str(sh.get('TPG', 0)) + '% → 頂對弱踢棄'), 'read', ev, {'by': who})
    row('mw', 'f_vs_bet', ['MID', 'WDRAW', 'AIR'], 'f', [], '多人底池中小對、弱聽牌、空氣面對下注棄', 'read', ev, {'by': who})
    row('mw', 'f_vs_bet', ['DRAW'], 'c', [], '強聽牌跟（多人底池賠率好）', 'rule', '原則（多人底池沒有解算器解）', {'by': who})
for r in ROWS:
    if r['sp'] == 'mw' and r['nd'] == 'f_vs_bet' and not r['eg']:
        r['eg'] = [e for c in r['hc'] for g in ('p75', 'le50') for e in (EGM.get(f"MFV|3|{r['c']['by']}|{g}|{c}") or [])[:10]][:30]
# 多人底池河牌面對下注（河牌還有 3 人以上）
for g in GB:
    for c in ['S', 'TPG', 'TPW', 'MID', 'AIR']:
        w = n = 0; ns = {}
        for sb in GB[g]:
            v = MW['W'].get(f"RW|MW|*|{sb}|{c}");
            if v: w += v[0]; n += v[1]; ns[sb] = v[1]
        if n < 40: continue
        need = need_of(g, ns) + 3  # 後面還有人：多留 3% 的餘裕
        a, ok, sig, p, e = verdict(w, n, need)
        ev = f"玩家池：河牌還有 3 人以上、第一個下注 {SZ[g]}｜{HC[c]}跟注 n={f0(n)}：攤牌贏全部人 {p:.0f}%±{e:.0f}（需要約 {need:.0f}%，含後面還有人的餘裕）→ {'顯著' if sig == 'sig' else '不明顯'}"
        row('mw', 'r_vs_bet', [c] + (['WDRAW'] if c == 'AIR' else []), a, ok, f"勝率 {p:.0f}%，需要約 {need:.0f}% → " + ('跟' if a == 'c' else '棄') + ('' if sig == 'sig' else '（差距在誤差內）'), 'pool', ev, {'sz': g}, eg=(EGM.get(f"MRV|{g}|{c}") or [])[:30])
# 多人底池轉牌（轉牌還有 3 人以上）
MW2 = json.load(open(f'{ST}/mw2.json')); EGT = MW2['EG']
for nk in ('3', '4+'):
    v = MW['F'].get(f"B|2|SRP|{nk}|PFR|s50|*"); v2 = MW['F'].get(f"B|2|SRP|{nk}|NON|s50|*")
    p, p2, n1, n2 = pc(v[0], v[1]), pc(v2[0], v2[1]), v[1] // 2, v2[1] // 2
    ev = f"玩家池：單加注底池、轉牌還有 {nk} 人、第一個下注 ½ 池｜全部棄牌：開池者下注 {p}%（n={f0(n1)}）、其他人下注 {p2}%（n={f0(n2)}），保本 33% → 顯著（頻率統計，不需攤牌）"
    row('mw', 't_bet', ['WDRAW', 'AIR'], 'x', [], f"轉牌 {nk} 人下注全部棄只有 {max(p, p2)}% 以下 → 不詐唬", 'pool', ev, {'n': nk}, eg=(EGT.get(f"MT|{nk}|AIR") or [])[:15] + (EGT.get(f"MT|{nk}|WDRAW") or [])[:15])
    row('mw', 't_bet', ['DRAW'], 'x', ['small'], '聽牌不要靠棄牌率：過牌，有人下注再看賠率', 'rule', f'原則＋池（{nk} 人底池全部棄牌率低）', {'n': nk}, eg=(EGT.get(f"MT|{nk}|DRAW") or [])[:30])
    row('mw', 't_bet', ['TPW', 'MID'], 'x', [], '中等牌在多人底池過牌：下注只會被更好的牌跟', 'rule', '原則（多人底池沒有解算器解）', {'n': nk}, eg=(EGT.get(f"MT|{nk}|TPW") or [])[:15] + (EGT.get(f"MT|{nk}|MID") or [])[:15])
    row('mw', 't_bet', ['S', 'TPG'], 'big', ['small'], '強牌下注收價值：多人底池跟注的人多', 'rule', '原則（多人底池沒有解算器解）', {'n': nk}, eg=(EGT.get(f"MT|{nk}|S") or [])[:15] + (EGT.get(f"MT|{nk}|TPG") or [])[:15])
TVA = {  # (who, grp) → 每種牌的動作（依下注者攤牌組成）
 ('PFR', 'le50'): dict(S=('r', ['c']), TPG=('c', []), TPW=('c', ['f']), MID=('f', ['c']), DRAW=('c', []), WDRAW=('f', []), AIR=('f', [])),
 ('PFR', 'p75'): dict(S=('r', ['c']), TPG=('c', ['f']), TPW=('f', ['c']), MID=('f', []), DRAW=('c', ['f']), WDRAW=('f', []), AIR=('f', [])),
 ('PFR', 'o150'): dict(S=('c', ['r']), TPG=('f', ['c']), TPW=('f', []), MID=('f', []), DRAW=('f', ['c']), WDRAW=('f', []), AIR=('f', [])),
 ('NON', 'le50'): dict(S=('r', ['c']), TPG=('c', []), TPW=('c', []), MID=('f', ['c']), DRAW=('c', []), WDRAW=('f', []), AIR=('f', [])),
 ('NON', 'p75'): dict(S=('r', ['c']), TPG=('c', ['f']), TPW=('f', ['c']), MID=('f', []), DRAW=('c', ['f']), WDRAW=('f', []), AIR=('f', [])),
 ('NON', 'o150'): dict(S=('c', ['r']), TPG=('f', ['c']), TPW=('f', []), MID=('f', []), DRAW=('f', ['c']), WDRAW=('f', []), AIR=('f', [])),
}
for (who, g), AM in TVA.items():
    cm = MW2['COMP'].get(f"TC|{who}|{g}") or {}; n = sum(cm.values()); sh = {k: pc(v, n) for k, v in cm.items()}
    ev = f"玩家池：多人底池（轉牌 3 人以上）{'開池者' if who == 'PFR' else '其他人'}先下注 {SZ[g]}｜攤牌 n={f0(n)}：兩對以上 {sh.get('S', 0)}%、超對/頂對好踢 {sh.get('TPG', 0)}%、頂對弱踢 {sh.get('TPW', 0)}%、中小對 {sh.get('MID', 0)}%、聽牌 {sh.get('DRAW', 0)}%、弱聽/空氣 {sh.get('WDRAW', 0) + sh.get('AIR', 0)}%（攤牌樣本，有偏差）"
    for c, (a2, ok2) in AM.items():
        better = sh.get('S', 0) + (sh.get('TPG', 0) if c in ('TPW', 'MID') else 0) + (sh.get('TPW', 0) if c == 'MID' else 0)
        why = {'S': '兩對以上：加注收價值' if a2 == 'r' else '超池下注者兩對以上很多：跟就好', 'DRAW': '強聽牌：' + ('賠率夠，跟' if a2 == 'c' else '超池賠率不夠，棄'),
               'WDRAW': '弱聽牌多人底池面對下注棄', 'AIR': '空氣棄'}.get(c) or f"下注者攤牌時比你好的牌約 {better}% → " + ('跟' if a2 == 'c' else '棄')
        row('mw', 't_vs_bet', c, a2, ok2, why, 'read' if c not in ('WDRAW', 'AIR', 'DRAW') else 'rule', ev, {'by': who, 'sz': g}, eg=(EGT.get(f"MTV|{who}|{g}|{c}") or [])[:30])
for c, a2, ok2, w in (('S', 'big', ['small'], '多人河牌強牌下注收價值'), ('TPG', 'small', ['x'], '頂對好踢多人河牌小注收價值'), ('TPW', 'x', [], '頂對弱踢多人河牌過牌：被跟多半是更好的牌'), ('MID', 'x', [], '中小對過牌攤牌')):
    row('mw', 'r_bet', c, a2, ok2, w, 'rule', '原則（多人底池沒有解算器解）', eg=(EGT.get(f"MR|{c}") or [])[:30])
v = MW['F'].get('B|3|*|*|*|*|*')
row('mw', 'r_bet', ['WDRAW', 'AIR', 'DRAW'], 'x', [], f"多人河牌下注全部棄只有 {pc(v[0], v[1])}% → 不詐唬", 'pool', f"玩家池：河牌還有 3 人以上、第一個下注｜n={f0(v[1])}：全部棄牌 {pc(v[0], v[1])}%（任何尺寸的保本都 ≥25%）→ 顯著（頻率統計，不需攤牌）")
# ------------- 修正：LD 與新數據衝突 -------------
# （learn_data.js 的 SRP_IP|r_vs_bet|ALL|mid_low 已在同一個 commit 改成跟注；見 tools/qa_all.py 檢查）
# ------------- 節點、位置說明 -------------
SPN = [
 ('ipfr', '你開池、有位置（BTN/CO/HJ 開，BB/SB 跟）', '單挑・單加注底池'),
 ('bb', '你在 BB 跟注（對手開池、有位置）', '單挑・單加注底池'),
 ('opfr', '你開池、沒位置（SB 開或前位開、後位跟）', '單挑・單加注底池'),
 ('ipc', '你有位置跟注（冷跟開池）', '單挑・單加注底池；翻前照表少冷跟'),
 ('3bp', '3-bet 底池', '單挑'),
 ('iso', 'limp／隔離底池', '單挑'),
 ('mw', '多人底池（翻牌 3 人以上）', '3 人以上'),
]
NDN = {'f_cbet': '翻牌：對手過牌給你（c-bet）', 'f_vs_xr': '翻牌：你下注被過牌加注', 'f_vs_donk': '翻牌：對手直接先下注（donk）', 't_barrel': '轉牌：翻牌下注被跟，再開一槍？',
       't_delay': '轉牌：翻牌過牌過牌（延遲 c-bet）', 't_vs_probe': '轉牌：翻牌你過牌，對手先下注', 't_vs_xr': '轉牌：你下注被加注', 'r_barrel': '河牌：翻、轉都下注被跟，第三槍？',
       'r_stab': '河牌：轉牌（或翻轉）都過牌', 'r_vs_bet': '河牌：對手下注，跟或棄', 'r_vs_xr': '河牌：你下注被加注', 'f_vs_cbet': '翻牌：面對 c-bet', 't_vs_barrel': '轉牌：面對第二槍',
       't_probe': '轉牌：翻牌對手過牌，你先下注？', 'f_stab': '翻牌：對手過牌給你（你不是開池者）', 'f_bet': '翻牌：輪到你下注（沒人下注）', 'f_vs_bet': '翻牌：面對下注', 'r_bet': '河牌：輪到你、沒人下注', 't_bet': '轉牌：輪到你、沒人下注', 'f_lead': '翻牌：limp 底池你沒位置先行動', 'f_first': '翻牌：你先行動', 't_first': '轉牌：翻牌跟注後你先行動', '3c_f_first': '翻牌：你跟 3-bet、先行動', '3c_t_first': '轉牌：你跟 3-bet、翻牌跟注後先行動', '3c_f_stab': '翻牌：你跟 3-bet、對手過牌給你', '3c_r_stab': '河牌：你跟 3-bet、對手過牌給你', 't_vs_bet': '轉牌：面對下注',
       '3b_f_cbet': '翻牌：你 3-bet、c-bet？', '3b_t_barrel': '轉牌：你 3-bet、再開一槍？', '3b_r_barrel': '河牌：你 3-bet、第三槍？', '3b_f_vs_xr': '翻牌：你 3-bet c-bet 被加注',
       '3c_f_vs_cbet': '翻牌：你跟 3-bet、面對 c-bet', '3c_t_vs_barrel': '轉牌：你跟 3-bet、面對第二槍', '3c_r_vs_bet2': '河牌：你跟 3-bet、對手下注', '3c_f_vs_over': '翻牌：你跟 3-bet、對手超池/全下'}
NDST = lambda nd: 'flop' if '_f_' in '_' + nd or nd.startswith('f_') else 'turn' if '_t_' in '_' + nd or nd.startswith('t_') else 'river'
CH = lambda nd: ['f', 'c', 'r'] if 'vs' in nd else ['x', 'small', 'big']
for r in ROWS:
    r['hc'] = [h for h in HC if h in r['hc']]
# 例子只留合法（兩張手牌＋3–5 張牌面、不重複）
def cards(s): return re.findall(r'[2-9TJQKA][shdc]', s or '')
for r in ROWS:
    good = []
    for e in r['eg']:
        h, b = cards(e['h']), cards(e['b'])
        if len(h) == 2 and len(b) in (3, 4, 5) and len(set(h + b)) == len(h + b): good.append(e)
    r['eg'] = good
# 例子統一格式：{h,b,me,t,pa,pc[],pot,stk,l,role}；l 的每個動作是「位置:動作」（b0.5＝下注半池；r＝加注）
RK = '23456789TJQKA'
def hlab(h):
    c = cards(h); a, b2 = sorted(c, key=lambda x: -RK.index(x[0]))
    return a[0] + b2[0] if a[0] == b2[0] else a[0] + b2[0] + ('s' if a[1] == b2[1] else 'o')
def norm(e, sp):
    if 'pre' in e:  # LD
        pr = e['pre'].split('|'); t = 'SRP' if len(pr) == 2 else '3BP'
        pa = pr[0] if t == 'SRP' else pr[2]; pcs = [x for x in e['pos'] if x != pa]
        return dict(h=e['h'], b=e['b'], me=e['me'], t=t, pa=pa, pc=pcs, pot=e['pot'], stk=e['stk'], l=e['l'])
    if 'pfr' in e:  # 多人
        live = e['live']; t = e['t']; pfr = e['pfr']
        if t == 'LMP': pot = len(live) + (0 if 'SB' in live else 0.5) - (0 if 'BB' in live else 0); pa = None; pcs = list(live)
        else:
            pot = 2.5 * len(live) + (0.5 if 'SB' not in live else 0) + (1 if 'BB' not in live else 0); pa = pfr; pcs = [x for x in live if x != pfr]
        return dict(h=e['h'], b=e['b'], me=e['me'], t=t, pa=pa, pc=pcs, pot=round(pot, 1), stk=e['stk'], l=e['l'], mw=1)
    mp = {'A': e['pa'], 'C': e['pc']}
    l = '/'.join(' '.join((mp.get(tk.split(':')[0], tk.split(':')[0]) + ':' + tk.split(':')[1]) for tk in st.split(' ') if tk) for st in e['l'].split('/'))
    return dict(h=e['h'], b=e['b'], me=mp.get(e['me'], e['me']), t=e['t'], pa=e['pa'], pc=[e['pc']], pot=e['pot'], stk=e['stk'], l=l)
def role(e):
    me, pa, t = e['me'], e['pa'], e['t']
    if t == 'LMP' or pa is None: return ['post', '']
    if t == 'ISO': return ['iso', f"{e['pc'][0]}>{pa}"] if me == pa else ['post', '']
    if t == 'SRP': return ['open', pa] if me == pa else ['call', f"{pa}open>{me}"]
    if t == '3BP':
        op = e['pc'][0] if me == pa else me
        return ['tb', f"{op}open>{pa}"] if me == pa else ['c3', f"{op}open>{pa}3b"]
    return ['post', '']
def inrange(e):
    k, key = e['role']
    if k == 'post': return True
    return hlab(e['h']) in (HWR.get(k, {}).get(key) or [])
NIN = 0
for r in ROWS:
    L = []
    for e in r['eg']:
        e2 = norm(e, r['sp']); e2['role'] = role(e2)
        if e2['me'] not in [e2['pa']] + e2['pc']: continue
        if inrange(e2): L.append(e2)
        else: NIN += 1
    random.shuffle(L); r['eg'] = L[:6]
print('examples dropped (not in HW range):', NIN)
# 精簡規則（口訣）：同一節點、同一條件，把答案一樣的牌型合併
def cond_lab(c):
    if not c: return ''
    p = []
    if c.get('tx'): p.append(TX[c['tx']])
    if c.get('ln') == 'tb': p.append('三槍')
    if c.get('ln') == 'oth': p.append('不是三槍')
    if c.get('sz'): p.append(SZ[c['sz']])
    if c.get('ct'): p.append('河牌' + CT[c['ct']])
    if c.get('n'): p.append(c['n'] + ' 人')
    if c.get('by'): p.append('開池者下注' if c['by'] == 'PFR' else '其他人先下注')
    return '・'.join(p)
# Evidence gate runs after example normalization, before assigning new IDs.
import sys
sys.path.insert(0, '/workspace/outputs/poker_lines_v2')
from evidence_policy import apply
ROWS[:] = apply(ROWS, LD)
AL = {}; ALN = {}  # Cross-spot advice had no shared evidence; aliases removed.
for i, r in enumerate(ROWS): r['id'] = f"{r['sp']}.{r['nd']}.{i}"; r['cl'] = cond_lab(r.get('c'))
COV = None
# Coverage and row hits are recomputed below against the final rows.
out = dict(ver='lines-1105', built='2026-11-05',
  scope='玩家池：GG NL2（$0.01/$0.02）6-max，2024-10 至 2025-05，724 檔原始手牌；單挑 50.5 萬手、多人底池 57.1 萬手到翻牌，有效籌碼 ≥40bb。你：10/28–11/4 共 6,717 手。',
  bias='棄牌率是所有手牌的頻率，沒有偏差。河牌「跟注後勝率」：河牌跟注一定攤牌，所以偏差最小。翻牌、轉牌的「攤牌組成」只算有攤牌的手，偏向中了牌的手，只當參考。',
  basis={'pool': '玩家池數據（n≥40；勝率檢定／原表攤牌組成與偏差見每列）', 'gto': '本機解算器（範圍、代表牌面與樹設定見每列；不跨位置套用）'},
  hc=HC, tx=TX, al=AL, aln=ALN, spots=[dict(id=a, t=b, sub=c) for a, b, c in SPN], nd=NDN, rows=ROWS, cov=COV)
from polish_text import polish
out['notes'] = polish(ROWS)
from run6_apply import apply as apply_run6
apply_run6(out, cond_lab)
from run7_apply import apply as apply_run7
apply_run7(out, cond_lab)
from run8_apply import apply as apply_run8
apply_run8(out, cond_lab, verdict)
# Labels for newly enumerated decisions share the same street vocabulary.
NDN['t_stab'] = '轉牌：翻牌跟注後，對手過牌給你'
NDN['f_vs_donk'] = '翻牌：面對跟注者下注（領打或過牌後下注）'
NDN['f_vs_xr'] = '翻牌：你下注後被加注'
for r in ROWS:
    if r['nd'] not in NDN:
        nd = r['nd']
        base = re.sub(r'^(?:3[bc]_|lmp_)', '', nd)
        NDN[nd] = ('溜入底池・' if nd.startswith('lmp_') else '再加注底池・' if nd.startswith('3') else '') + NDN.get(base, base)
# Recompute HW matches against final IDs; source lines1105 stays read-only.
json.dump(out, open('/workspace/outputs/poker_lines_v2/results/rows.json', 'w'), ensure_ascii=False)
subprocess.run([sys.executable, '/workspace/outputs/poker_lines_v2/review_hw_match.py'], check=True)
COV = json.load(open('/workspace/outputs/poker_lines_v2/results/hw_match.json'))
out['cov'] = COV
for r in ROWS: r['hw'] = COV['rowhits'].get(r['id'], 0)
open(os.path.join(ROOT, 'lines_data.js'), 'w').write('// 自動產生：python3 tools/build_lines.py（不要手改）\nwindow.NLL=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
json.dump(out, open('/workspace/outputs/poker_lines_v2/results/rows.json', 'w'), ensure_ascii=False)
from collections import Counter
print('rows', len(ROWS), Counter(r['sp'] for r in ROWS), Counter(r['b'] for r in ROWS), 'no-eg', sum(1 for r in ROWS if not r['eg']))
