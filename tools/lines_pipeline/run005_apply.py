"""Run 005 apply: split every non-MW turn/river row of lines_data.js into runout-category rows (RULE.md deploy rule).
Usage: python3 apply5.py DECISIONS005.json RUNLABEL   (writes /workspace/repos/poker-trainer/lines_data.js in place, keeps header)"""
import json, re, sys, subprocess, collections, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rcat import rcat, CATS
import os
ROOT = Path(os.environ.get('R5ROOT', str(Path(__file__).resolve().parents[2])))
js = (ROOT / 'lines_data.js').read_text(); hdr = js.split('\n', 1)[0]
N = json.loads(subprocess.run(['node', '-e', "global.window={};eval(require('fs').readFileSync('lines_data.js','utf8'));process.stdout.write(JSON.stringify(window.NLL))"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
D = {d['row_id']: d for d in json.load(open(sys.argv[1]))['decisions']}; RUN = sys.argv[2]
UNS = {u['id']: u for u in json.load(open('/workspace/poker_r005/unsplit.json'))}
LAB = {'x': '過牌', 'small': '小注', 'big': '大注', 'f': '棄牌', 'c': '跟注', 'r': '加注'}
CN = {'over': '高張落下（A/K 或新最大牌）', 'pair': '公牌成對', 'flush': '同花完成', 'straight': '順子完成', 'draw': '補聽牌', 'brick': '空白牌'}
def isvs(nd): return bool(re.search(r'_vs_|_over', nd))
def cho(nd, sp): return ['f', 'c'] if re.search(r'r_vs_xr', nd) else ['f', 'c', 'r'] if isvs(nd) else ['x', 'small', 'big']
def stv(nd): return 2 if re.search(r'(^|_)t_', nd) else 3
def pct(x): return f'{round(x * 100)}%'
def fq(m): return '／'.join(f'{LAB.get(a, a)} {p * 100:.1f}%' for a, p in sorted(m.items(), key=lambda kv: -kv[1]))
st = collections.Counter(); out = []; per = collections.Counter(); kinds = collections.Counter()
for r in N['rows']:
    if r['sp'] == 'mw' or not re.search(r'(^|_)[tr]_', r['nd']): out.append(r); continue
    s = stv(r['nd']); STN = '轉牌' if s == 2 else '河牌'
    if r['id'] in UNS:
        u = UNS[r['id']]
        if u['why'] == 'CERT':   # run-002 certified pool answer holds in every category (shown in every category table)
            r['rn'] = dict(k='cert', p=int(next(iter(re.findall(r'n=([\d,]+)', r.get('ev', '')) or ['0'])).replace(',', '')))
            kinds['cert'] += 1
        else:                    # ct row: already runout-specific -> only in its category table
            r['c'] = dict(r['c'], ro=u['ro']); r['rn'] = dict(k='ct'); kinds['ct'] += 1
        out.append(r); continue
    for cat in CATS[s]:
        d = D[r['id'] + '~' + cat]; n = int(d.get('n_matched') or 0); nb = d.get('solver_boards') or 0
        x = {k: copy.deepcopy(v) for k, v in r.items() if k not in ('solver', 'pool_est_run003', 'hw', 'dominance')}
        x['id'] = r['id'] + '~' + cat; x['c'] = dict(r.get('c') or {}, ro=cat); x['parent'] = r['id']
        x['eg'] = [e for e in (r.get('eg') or []) if len(e.get('b', '')) >= 2 * (2 + s) and rcat(e['b'], s) == cat]
        if not x['eg'] and r.get('eg'): x['eg'] = []
        x.pop('noeg', None)
        sv = r.get('solver') or {}
        g = d['gto_primary']; mix = d.get('gto_mix') or {}; cat_mix = str(d.get('pi_src', '')).startswith('solver.samples')
        x['solver'] = dict(freq=mix, src=d.get('pi_src'), boards=nb, parent_freq=sv.get('freq'), provenance=sv.get('provenance') or sv.get('aggregation'))
        legal = [a for a in cho(r['nd'], r['sp']) if a in mix]
        A = {k: v for k, v in (d.get('arms') or {}).items() if k in legal}
        pm = d.get('mean_pot_bb') or 0
        mdl = '河牌精算' if s == 3 else '翻/轉牌近似（勝率×底池，未計後續街）'
        L0 = {k: v for k, v in (r.get('L') or {}).items() if '牌池均值' not in v}
        if d['label'] == 'EST' and A:
            best = max(A, key=lambda k: (A[k]['ev'], k == g)); dev = best != g and A[best]['ev'] > d['ev_ref']
            arms = '、'.join(f"{LAB[k]} {v['ev'] * pm:+.2f}bb（n={int(v['n']) if v['n'] < 10**8 else n}）" for k, v in sorted(A.items(), key=lambda kv: -kv[1]['ev']))
            ci = d.get('dEV_ci_bb') or [float('nan')] * 2; pg = d.get('p_best_gt_primary')
            gsrc = f'這類落牌 {nb} 個解算牌面' if cat_mix else '未分落牌的同格 solver（這類落牌解算牌面不足 5 個）'
            ev = (f"牌池估算 run 005 落牌分類（{RUN}；預登錄 RULE.md）｜最賺動作估算，不是封閉證明｜{STN}落牌：{CN[cat]}；同節點牌池決策 n={n}"
                  f"｜模型：{mdl}｜各動作 EV：{arms}｜95% CI {ci[0]:+.2f}～{ci[1]:+.2f}｜GTO 基準（{gsrc}）：{json.dumps({k: round(v, 3) for k, v in mix.items()}, ensure_ascii=False)}")
            if dev:
                a = best; resp = A[a]
                ex = f"，池對此注棄牌 {resp['fold'] * 100:.0f}%" if a in ('small', 'big', 'r') and 'fold' in resp else ''
                x.update(a=a, b='est', ok=([g] if g in legal and (pg is None or pg < 0.9) else []),
                         why=f"{STN}{CN[cat]}：牌池估算最賺（{mdl}，非封閉證明）{ex}：{LAB[a]} {A[a]['ev'] * pm:+.2f}bb vs GTO {LAB.get(g, g)}{'混合' if d.get('ref_kind') == 'GTO_MIX' else ''} {d['ev_ref'] * pm:+.2f}bb（n={n}）",
                         ev=ev, evidence=f'run005:{RUN}:{x["id"]}:{a}',
                         pool_est_run003=dict(action=a, gto_primary=g, n=n, run='005', dEV_ci_bb=ci, mean_pot_bb=pm,
                                              arms={k: dict(ev_bb=v['ev'] * pm, n=(int(v['n']) if v['n'] < 10**8 else None)) for k, v in A.items()}))
                Ln = dict(L0)
                for gg in ('small', 'big'):
                    if gg in A and A[gg].get('size'): Ln[gg] = f"下注約 {pct(A[gg]['size'])} 池（牌池均值）"
                x['L'] = Ln; x['rn'] = dict(k='est', p=n, g=nb); kinds['est'] += 1
            else:
                ok = [k for k, v in mix.items() if k != g and v >= .3 and k in legal]
                x.update(a=g, b='gto', ok=ok, why=f"{STN}{CN[cat]}：牌池估算（{mdl}）：GTO {LAB.get(g, g)} 仍最賺（n={n}）；GTO：{fq(mix)}",
                         ev=ev, evidence=f'run005:{RUN}:{x["id"]}:{g}', L=L0)
                x['rn'] = dict(k='gtoe', p=n, g=nb); kinds['est_agree'] += 1
        elif cat_mix:
            ok = [k for k, v in mix.items() if k != g and v >= .3 and k in legal]
            x.update(a=g, b='gto', ok=ok, why=f"{STN}{CN[cat]}：牌池樣本不足（{d['reason']}，n={n}），照這類落牌的 GTO：{fq(mix)}",
                     ev=f"本機解算器（同格 run10／重算樣本），只取{STN}落牌屬「{CN[cat]}」的 {nb} 個解算牌面重新加權（同來源同牌面按到達質量、各牌面等權）；頻率：{fq(mix)}｜run 005 牌池 n={n}（{RUN}）｜未分落牌的同格頻率：{fq(sv.get('freq') or {})}",
                     evidence=f'run005:{RUN}:{x["id"]}:gto', L=L0)
            x['rn'] = dict(k='gto', p=n, g=nb); kinds['gto'] += 1
        else:
            x['why'] = f"{STN}{CN[cat]}：這類落牌牌池 {n} 手（<40 或無法估）、解算牌面 {nb} 個（<5），沿用未分落牌的答案。原依據：" + r.get('why', '')
            x['ev'] = f"沿用未分落牌（run 005 {RUN}：這類落牌牌池 {n} 手、解算牌面 {nb} 個）｜" + r.get('ev', '')
            if r.get('pool_est_run003'): x['pool_est_run003'] = r['pool_est_run003']
            if r.get('dominance'): x['dominance'] = r['dominance']
            x['rofb'] = 1; x['rn'] = dict(k='fb', p=n, g=nb); kinds['fallback'] += 1
        per[(s, cat, x['rn']['k'])] += 1
        out.append(x)
N['rows'] = out
N['ro'] = {'over': '高張落下（A/K 或新最大牌）', 'pair': '公牌成對', 'flush': '同花完成', 'straight': '順子完成', 'draw': '補聽牌', 'brick': '空白牌'}
N.setdefault('notes', []).append(f'run 005（{RUN}，2026-11-18）：轉牌、河牌每個節點按這一街新發的那張牌分類（高張落下（A/K 或新最大牌）、公牌成對、同花完成、順子完成、補聽牌〔轉牌〕、空白牌），每類一張表、各自估算：牌池 n≥40 有估算用池估最賺動作；否則用這類落牌的解算牌面（≥5 個）GTO；兩者都沒有就沿用未分答案（標「沿用」）。牌型仍按當街牌面逐街重算。')
(ROOT / 'lines_data.js').write_text(hdr + '\nwindow.NLL=' + json.dumps(N, ensure_ascii=False, separators=(',', ':')) + ';\n')
json.dump(dict(kinds=kinds, per={'|'.join(map(str, k)): v for k, v in sorted(per.items())}, rows=len(out)), open('/workspace/poker_r005/apply_stats.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), dict(kinds))
