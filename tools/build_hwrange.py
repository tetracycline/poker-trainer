#!/usr/bin/env python3
"""HW 實際會玩的範圍（核心）→ hwrange.js（window.HWR）。
規則：網站建議範圍（pf_data exp）中頻率 ≥50% 的牌型，依該動作 EV 排序，只取前段，
使組合數接近 HW 實戰頻率（/workspace/poker/hw_stats_cumulative.json；檔案不在時用內建值）。
所有發牌（翻前有前置動作的節點、翻後、行動線、讀牌）都只從這裡發。"""
import json, os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(R, 'pf_data.js')).read()
PF = json.loads(s[s.index('{'):s.rindex('}') + 1])
N = PF['names']; NODES = PF['nodes']
def nc(h): return 6 if len(h) == 2 else 4 if h[2] == 's' else 12
# HW 實戰頻率（%）；cumulative 檔有就讀
HW = {'open': {'UTG': 15, 'HJ': 17, 'CO': 18, 'BTN': 31, 'SB': 33}, 'bb_def': 27.3, 'sb_def': 10.9, 'tb': 3.4}
try:
    c = json.load(open('/workspace/poker/hw_stats_cumulative.json'))['cumulative']
    HW['bb_def'] = c['BB_defend_vs_steal']['pct']; HW['sb_def'] = 100 - c['SB_fold_vs_steal']['pct']
    for p, k in (('CO', 'Steal_CO'), ('BTN', 'Steal_BTN'), ('SB', 'Steal_SB')):
        if k in c: HW['open'][p] = max(HW['open'][p], c[k]['pct'])
except Exception as e:
    print('stats file not read, defaults:', e)
def core(node, act, target_pct=None, frac=None, ver='exp'):
    n = NODES[node]; j = n['acts'].index(act); v = n[ver]
    jf = n['acts'].index('fold') if 'fold' in n['acts'] else None
    cand = [i for i in range(169) if v['s'][i][j] >= 50 and v['r'][i] >= 50]
    ev = lambda i: (v['ev'][i][j] - (v['ev'][i][jf] if jf is not None else 0)) if v.get('ev') and v['ev'][i] else v['s'][i][j]
    cand.sort(key=lambda i: -ev(i))
    tot = sum(nc(N[i]) for i in cand)
    goal = tot if target_pct is None and frac is None else min(tot, target_pct * 13.26 if target_pct is not None else tot * frac)
    out, t = [], 0
    for i in cand:
        if t >= goal - 1e-9: break
        out.append(N[i]); t += nc(N[i])
    return out, round(t / 13.26, 1), round(tot / 13.26, 1)
H = {'open': {}, 'call': {}, 'tb': {}, 'c3': {}, 'iso': {}, 'meta': {}}
site_def_btn = None
for p in ('UTG', 'HJ', 'CO', 'BTN', 'SB'):
    o, a, b = core(p + 'rfi', 'open', HW['open'][p]); H['open'][p] = o; H['meta']['open ' + p] = [a, b]
for k, n in NODES.items():
    m = re.fullmatch(r'(UTG|HJ|CO|BTN|SB)open>(HJ|CO|BTN|SB|BB)', k)
    if m:
        hero = m.group(2)
        f = 0.6 if hero == 'BB' else 0.4 if hero == 'SB' else 0.6   # 只留 EV 最高的前段：BB 防守 27% vs 網站 46%；SB 只防 11%
        if 'call' in n['acts']:
            o, a, b = core(k, 'call', frac=f); H['call'][k] = o; H['meta']['call ' + k] = [a, b]
        if '3bet' in n['acts']:
            o, a, b = core(k, '3bet', frac=0.45); H['tb'][k] = o; H['meta']['3bet ' + k] = [a, b]   # HW 3-bet 3.4%，網站約 8–12%
    m = re.fullmatch(r'(UTG|HJ|CO|BTN|SB)open>(HJ|CO|BTN|SB|BB)3b', k)
    if m and 'call' in n['acts']:
        o, a, b = core(k, 'call'); op = set(H['open'][m.group(1)]); H['c3'][k] = [h for h in o if h in op]; H['meta']['c3 ' + k] = [a, b]
s2 = open(os.path.join(R, 'learn_data.js')).read(); LD = json.loads(s2[s2.index('{'):s2.rindex('}') + 1])
for k, t in LD['iso'].items(): H['iso'][k] = t['core']
H['hw'] = HW
open(os.path.join(R, 'hwrange.js'), 'w').write('// 由 tools/build_hwrange.py 產生：HW 實際會玩的核心範圍（頻率≥50%＋依 HW 實戰頻率收緊）\nwindow.HWR=' + json.dumps(H, separators=(',', ':')) + ';\n'
  "(function(H){H.ok=function(kind,key,h){const L=H[kind]&&H[kind][key];return !!(L&&L.indexOf(h)>=0)};})(window.HWR);\n")
if __name__ == '__main__':
    for k, v in H['meta'].items():
        if k.startswith('open') or 'BTNopen' in k: print(k, v)
    print('BTN open', ' '.join(H['open']['BTN']))
    print('J2s' in H['open']['BTN'])
