"""Run 004 apply (2026-11-10): (1) honest bet-size labels, (2) texture-half splits from run 004 (RULE.md deploy rule).
Usage: python3 tools/lines_pipeline/run004_apply.py DECISIONS003.json [DECISIONS004_DIR RUNID]
Writes lines_data.js in place (keeps the generated header)."""
import json, re, subprocess, sys, glob, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
js = (ROOT / 'lines_data.js').read_text()
hdr, body = js.split('\n', 1)
N = json.loads(subprocess.run(['node', '-e', "global.window={};eval(require('fs').readFileSync('lines_data.js','utf8'));process.stdout.write(JSON.stringify(window.NLL))"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
D3 = {d['row_id']: d for d in json.load(open(sys.argv[1]))['decisions']}
st = collections.Counter()
def pct(x): return f'{round(x * 100)}%'
def size_labels(r, dec):
    L = dict(r.get('L') or {})
    for k, v in list(L.items()):
        if '樣本組平均' in v: L[k] = v.replace('（樣本組平均）', '（牌池均值）'); st['relabel_pool_mean'] += 1
    if r['b'] == 'est' and dec:
        for g in ('small', 'big'):
            a = (dec.get('arms') or {}).get(g)
            if a and a.get('size'): L[g] = f"下注約 {pct(a['size'])} 池（牌池均值）"; st['est_size_' + g] += 1
    sv = r.get('solver') or {}; ex = sv.get('exact_freqs') or {}; fq = sv.get('freq') or {}
    if r['b'] in ('gto', 'pool'):
        for g in ('small', 'big'):
            if g in L: continue
            ks = [k for k in ex if re.fullmatch(r'b\d+', k)]
            if 'small' in fq and 'big' in fq:
                ks = [k for k in ks if (int(k[1:]) <= 60) == (g == 'small')]
            elif g not in fq: ks = []
            if ks:
                k = max(ks, key=lambda k: ex[k]); n = int(k[1:])
                L[g] = '下注 ½ 池' if n == 50 else '下注 1 池' if n == 100 else f'下注 {n}% 池'; st['gto_exact_' + g] += 1
    if L: r['L'] = L
for r in N['rows']:
    size_labels(r, D3.get(r['id']))
# ---- run 004 texture halves ----
if len(sys.argv) > 3:
    ddir, runid = sys.argv[2], sys.argv[3]
    D4 = [d for f in sorted(glob.glob(ddir + '/**/decisions004.json', recursive=True)) for d in json.load(open(f))['decisions']]
    by = collections.defaultdict(dict)
    for d in D4: by[d['base_id']][d['half']] = d
    rows = {r['id']: r for r in N['rows']}
    HL = {'T': '最高張 T 以上', 'L': '最高張 9 以下'}
    RV = '23456789TJQKA'
    def half_of(bd, street): b = bd[:2 * (2 + street)]; return 'T' if max(RV.index(b[i]) for i in range(0, len(b), 2)) >= 8 else 'L'
    stv = lambda nd: 1 if re.search(r'(^|_)f_', nd) else 2 if re.search(r'(^|_)t_', nd) else 3
    LAB = {'x': '過牌', 'small': '小注', 'big': '大注', 'f': '棄牌', 'c': '跟注', 'r': '加注'}
    new = []
    for bid, hh in by.items():
        if set(hh) != {'T', 'L'}: st['half_missing'] += 1; continue
        ans = {h: (d['action'] if d['label'] == 'EST' else d['gto_primary']) for h, d in hh.items()}
        if ans['T'] == ans['L']: st['halves_agree'] += 1; continue
        # amendment (disclosed): a half with no pool estimate AND no per-half solver freqs only repeats the base GTO mix,
        # so it carries no texture evidence -> such a pair is not a texture split; keep the run-003 row.
        if any(d['label'] != 'EST' and str(d.get('pi_src', '')).startswith('base') for d in hh.values()): st['split_skipped_fallback_half'] += 1; continue
        r = rows[bid]; s = stv(r['nd'])
        others = [x['a'] for x in N['rows'] if x['sp'] == r['sp'] and x['nd'] == r['nd'] and not x.get('x') and x['id'] != bid]
        dflt = collections.Counter(others).most_common(1)[0][0] if others else None
        nT, nL = hh['T']['n_matched'], hh['L']['n_matched']
        keep = 'T' if ans['T'] == dflt and ans['L'] != dflt else 'L' if ans['L'] == dflt and ans['T'] != dflt else ('T' if nT >= nL else 'L')
        oth = 'L' if keep == 'T' else 'T'
        def mk(row, h, d):
            a = ans[h]; dev = d['label'] == 'EST' and d['reason'] == 'EST_DEVIATION'
            pm = d.get('mean_pot_bb') or 0; A = d.get('arms') or {}
            arms = '、'.join(f"{LAB[k]} {v['ev']*pm:+.2f}bb（n={int(v['n']) if v['n'] < 10**8 else d['n_matched']}）" for k, v in sorted(A.items(), key=lambda kv: -kv[1]['ev']))
            ci = d.get('dEV_ci_bb') or [float('nan')] * 2
            mdl = '河牌精算' if s == 3 else '翻/轉牌近似（勝率×底池，未計後續街）'
            if d['label'] == 'EST':
                why = (f"{HL[h]}：牌池估算最賺（{mdl}，非封閉證明）：{LAB[a]} {A[a]['ev']*pm:+.2f}bb vs GTO {LAB.get(d['gto_primary'])}{'混合' if d.get('ref_kind')=='GTO_MIX' else ''} {d['ev_ref']*pm:+.2f}bb（n={d['n_matched']}）"
                       if dev else f"{HL[h]}：牌池估算（{mdl}）：GTO {LAB.get(a)} 仍最賺（n={d['n_matched']}）")
                ev = (f"牌池估算 run 004 牌面高低分半（GitHub Actions {runid}；預登錄 RULE.md）｜最賺動作估算，不是封閉證明｜{HL[h]}；同節點牌池決策 n={d['n_matched']}"
                      f"｜模型：{mdl}｜各動作 EV：{arms}｜95% CI {ci[0]:+.2f}～{ci[1]:+.2f}｜GTO 基準（{d['pi_src']}）：{json.dumps({k: round(v, 3) for k, v in (d['gto_mix'] or {}).items()}, ensure_ascii=False)}")
                b = 'est' if dev else 'gto'
            else:
                why = f"{HL[h]}：牌池樣本不足（{d['reason']}），照這半邊的 GTO {LAB.get(a)}"
                ev = f"GTO（{d['pi_src']}）：{json.dumps({k: round(v, 3) for k, v in (d['gto_mix'] or {}).items()}, ensure_ascii=False)}｜run 004（{runid}）牌池 n={d['n_matched']}"
                b = 'gto'
            row = dict(row, a=a, b=b, ok=[], why=why, ev=ev, evidence=f'run004:{runid}:{d["row_id"]}:{a}', hi=h,
                       eg=[e for e in row['eg'] if half_of(e['b'], s) == h] or row['eg'][:0])
            if b == 'est':
                row['pool_est_run003'] = dict(action=a, gto_primary=d['gto_primary'], n=d['n_matched'], run='004', dEV_ci_bb=ci,
                    arms={k: dict(ev_bb=v['ev'] * pm, n=(int(v['n']) if v['n'] < 10**8 else None)) for k, v in A.items()})
            else:
                row.pop('pool_est_run003', None)
                row['L'] = {k: v for k, v in (row.get('L') or {}).items() if '牌池均值' not in v}   # GTO answer -> solver tree size, set below
            size_labels(row, d)
            return row
        base = mk(r, keep, hh[keep]); base['c'] = dict(r.get('c') or {}); base['cl'] = r.get('cl', '')
        base['why'] = base['why'].replace(HL[keep] + '：', f'（{HL[oth]}另列例外）{HL[keep]}：', 1)
        xr = mk(r, oth, hh[oth]); xr['id'] = bid + '@' + oth; xr['x'] = 1; xr['c'] = dict(r.get('c') or {}, hi=oth)
        xr['cl'] = ((r.get('cl') + '・') if r.get('cl') else '') + HL[oth]
        rows[bid].clear(); rows[bid].update(base); new.append(xr); st['split'] += 1
    N['rows'].extend(new)
    N.setdefault('notes', []).append(f'run 004（GitHub Actions {runid}）：沒有分牌面的列，按這街牌面最高張 T 以上／9 以下各估一次；兩半最賺動作不同時，另一半列為例外（{st["split"]} 列）。')
# ---- solver-tree sizes for GTO/pool rows that still use the generic label: read the actual tree node of the first sample ----
_tree = {}
def tree_acts(path, line):
    if path not in _tree:
        try: _tree[path] = {n.get('line'): n.get('acts') for n in json.load(open(path))['nodes'] if isinstance(n, dict)}
        except Exception: _tree[path] = {}
    return _tree[path].get(line)
for r in N['rows']:
    if r['sp'] == 'mw' or r['b'] not in ('gto', 'pool'): continue
    sv = r.get('solver') or {}; fq = sv.get('freq') or {}; L = dict(r.get('L') or {})
    need = [g for g in ('small', 'big') if g in [r['a']] + r['ok'] and g not in L]
    if not need: continue
    acts = None
    for smp in sv.get('samples') or []:
        pth = smp.get('original_source') or smp.get('path') or smp.get('source')
        if pth and smp.get('line') is not None: acts = tree_acts(pth, smp['line'])
        if acts: break
    if not acts:   # documented default tree (notes: flop 33/75, turn/river 50/100)
        fl = bool(re.search(r'(^|_)f_', r['nd']))
        for g in need: L[g] = ('下注 33% 池' if g == 'small' else '下注 75% 池') if fl else ('下注 ½ 池' if g == 'small' else '下注 1 池'); st['tree_size_default_' + g] += 1
        r['L'] = L; continue
    bets = sorted([a for a in acts if re.fullmatch(r'b\d+', a)], key=lambda a: int(a[1:])); ai = 'a' in acts
    for g in need:
        if 'small' in fq and 'big' in fq: cand = bets[:1] if g == 'small' else (bets[1:] or (['a'] if ai else []))
        else: cand = bets[-1:] or (['a'] if ai else [])
        if not cand:
            fl = bool(re.search(r'(^|_)f_', r['nd'])); L[g] = ('下注 33% 池' if g == 'small' else '下注 75% 池') if fl else ('下注 ½ 池' if g == 'small' else '下注 1 池'); st['tree_size_default_' + g] += 1; continue
        k = cand[-1] if g == 'big' else cand[0]
        L[g] = '全下' if k == 'a' else ('下注 ½ 池' if k == 'b50' else '下注 1 池' if k == 'b100' else f'下注 {k[1:]}% 池'); st['tree_size_' + g] += 1
    r['L'] = L
# ---- dominance: in a facing node, a stronger made class never folds where a weaker one continues (same bet, equity >= ) ----
ORD = ['S', 'TPG', 'TPW', 'MID', 'AIR']
def weak(r):
    if r.get('ok'): return True
    if r['b'] == 'est':
        ci = (r.get('pool_est_run003') or {}).get('dEV_ci_bb') or [0, 0]
        return not (ci[0] > 0)
    fq = (r.get('solver') or {}).get('freq') or {}
    return bool(fq) and max(fq.values()) < 0.6
dom_log = []
for (sp, nd) in sorted({(r['sp'], r['nd']) for r in N['rows']}):
    if sp == 'mw' or not re.search(r'_vs_|_over', nd): continue
    base = [r for r in N['rows'] if r['sp'] == sp and r['nd'] == nd and not r.get('x')]
    for cl in sorted({r.get('cl') or '' for r in base}):
        cells = []
        for h in ORD:
            rr = [r for r in base if (r.get('cl') or '') == cl and h in r['hc']]
            if rr: cells.append((h, rr[0]))
        cont = [c[1]['a'] == 'c' or (c[1]['a'] == 'r' and c[0] != 'AIR') for c in cells]   # an AIR raise is a bluff, not a showdown continue
        if any(c[0] == 'AIR' and c[1]['a'] == 'r' for c in cells): cells = [c for c in cells if c[0] != 'AIR']; cont = cont[:len(cells)]
        air_call = any(h == 'AIR' and r['a'] == 'c' for h, r in cells)
        if all(cont[i] or not any(cont[i + 1:]) for i in range(len(cont))): continue
        best = None
        for t in range(len(cells) + 1):
            cost = sum((1 if weak(r) else 2) for i, (h, r) in enumerate(cells) if cont[i] != (i < t))
            if best is None or cost < best[0] or (cost == best[0] and (t < best[1] if air_call else t > best[1])): best = (cost, t)
        t = best[1]
        for i, (h, r) in enumerate(cells):
            want = i < t
            if cont[i] == want: continue
            by = [x for j, (hh, x) in enumerate(cells) if cont[j] == want and ((j > i) if want else (j < i))]
            old = r['a']; r['a'] = 'c' if want else 'f'; r['ok'] = []
            src = by[0] if by else None
            if src is not None: r['b'] = src['b']
            if r['b'] == 'est' and src is not None: r['pool_est_run003'] = dict(src.get('pool_est_run003') or {}, dominance_of=r['id'])
            names = '、'.join(N['hc'][x['hc'][0]] for x in by) or '其他牌型'
            r['why'] = (f"單調修正：同一個下注，{N['hc'][h]}的勝率不低於{names}，而{names}{'繼續' if want else '棄牌'}，所以{N['hc'][h]}" + ('不該棄牌 → 跟注' if want else '也不該跟 → 棄牌') + f"（原答案 {old}；根據同格 {src['id'] if src else '—'}）。" + r['why'])
            r['dominance'] = dict(old=old, new=r['a'], by=[x['id'] for x in by]); r['evidence'] = 'dominance:' + (src['id'] if src else '') + ':' + r['a']
            st['dominance_fix'] += 1; dom_log.append((r['id'], old, r['a']))
# ---- rows with no complete drill example: reuse a same-node, same-condition example line/board and deal a hero hand of
#      the row's class from HW's range for that role (classifier = run10_common.classes; QA checks the HW range) ----
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run10_common import classes as _classes
HWR = json.loads(subprocess.run(['node', '-e', "global.window=global;eval(require('fs').readFileSync('hwrange.js','utf8'));process.stdout.write(JSON.stringify(window.HWR))"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
RK = '23456789TJQKA'; DECK = [r + x for r in RK for x in 'shdc']
def _cls(h):
    a, b = sorted([h[:2], h[2:]], key=lambda x: -RK.index(x[0]))
    return a[0] + b[0] if a[0] == b[0] else a[0] + b[0] + ('s' if a[1] == b[1] else 'o')
def _stv(nd): return 0 if re.search(r'(^|_)f_', nd) else 1 if re.search(r'(^|_)t_', nd) else 2
def _complete(e, nd): k = _stv(nd); return len(e['b']) == 2 * (3 + k) and len(e['l'].split('/')) == k + 1
def _half(bd): return 'T' if max(RK.index(bd[i]) for i in range(0, len(bd), 2)) >= 8 else 'L'
import itertools, hashlib
from common import texture as _texture, ctype as _ctype
def _szb(x): return 's33' if x <= 0.40 else 's50' if x <= 0.60 else 's75' if x <= 0.85 else 's100' if x <= 1.15 else 's150'
_SZG = {'le50': ('s33', 's50'), 'p75': ('s75', 's100'), 'o150': ('s150',)}
def _eg_ok(c, e, nd):
    """Same filters as the pool matcher (worker filt) evaluated on an example's board/line."""
    segs = [[t.split(':') for t in sg.split()] for sg in e['l'].split('/')]; me = e['me']; cur = segs[-1]
    if 'tx' in c and _texture(e['b']) != c['tx']: return False
    if 'ct' in c and (len(e['b']) < 10 or _ctype(e['b'], 3) != c['ct']): return False
    if 'hi' in c and _half(e['b']) != c['hi']: return False
    if 'sz' in c:
        vb = [a for p, a in cur if p != me and a[0] in 'br']
        if not vb or vb[-1][0] != 'b' or _szb(float(vb[-1][1:])) not in _SZG[c['sz']]: return False
    if 'ln' in c:
        tb = all(any(p != me and a[0] == 'b' for p, a in sg) for sg in segs[:3]) and len(segs) >= 3
        if (c['ln'] == 'tb') != tb: return False
    if 'prior' in c:
        t2 = [a for p, a in (segs[1] if len(segs) > 1 else []) if p == me]; f1 = [a for p, a in segs[0] if p == me]
        if c['prior'] == 'check_turn' and not (t2 and all(a == 'x' for a in t2)): return False
        if c['prior'] == 'bet_bet' and not (any(a[0] in 'br' for a in t2) and any(a[0] in 'br' for a in f1)): return False
    return True
for r in N['rows']:
    if r['sp'] == 'mw' or any(_complete(e, r['nd']) for e in r.get('eg') or []): continue
    cands = []
    for o in N['rows']:
        if o is r or o['sp'] != r['sp'] or o['nd'] != r['nd']: continue
        for e in o.get('eg') or []:
            if _complete(e, r['nd']) and not e.get('synth') and _eg_ok(r.get('c') or {}, e, r['nd']): cands.append(e)
    seen = set(); got = []
    for e in cands:
        key = (e['b'], e['l'], e['me'], json.dumps(e['role']))
        if key in seen: continue
        seen.add(key); kind, rk = e['role']; ok = set(HWR.get(kind, {}).get(rk) or []) if kind in ('open', 'call', 'tb', 'c3', 'iso') else None
        bd = [e['b'][i:i + 2] for i in range(0, len(e['b']), 2)]
        combos = sorted((x + y for x, y in itertools.combinations([c for c in DECK if c not in bd], 2)), key=lambda h: hashlib.md5((r['id'] + h).encode()).hexdigest())
        for h in combos:
            if (ok is None or _cls(h) in ok) and _classes(h, e['b']) == [r['hc'][0]]:
                got.append(dict(e, h=h, synth=1)); break
        if len(got) >= 3: break
    if got: r['eg'] = got; st['synth_examples_rows'] += 1
    else: st['synth_examples_none'] += 1; dom_log.append((r['id'], 'no_example', '')); r['noeg'] = '你的範圍在這條線的牌面上拿不到這類牌，不出題'
json.dump(dom_log, open('/workspace/poker_r004/dominance_log.json', 'w'))
(ROOT / 'lines_data.js').write_text(hdr + '\nwindow.NLL=' + json.dumps(N, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(dict(st))
