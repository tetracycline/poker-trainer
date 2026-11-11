#!/usr/bin/env python3
"""全站 QA：部署前必跑。  python3 tools/qa_all.py [-n 500] [--only 名稱] [--shots 50]
每個練習產生 N 題（讀 window.__Q），檢查：
 1 手牌是 HW 會玩的（hwrange.js 核心範圍；翻後 w≥50；要先有動作才到的點只發會走到的牌）
 2 每條街完整行動（翻前→目前街），有尺寸
 3 每個統計都有範圍（位置／行動線／分質地或合併／n／攤牌 n／GTO 對池＋顯著性）
 4 每個按鈕都有快捷鍵（keys.js 的 kbd.kk）
 5 1280×800 不用捲動；手機字較大
 6 剝削規則：池顯著偏離 且 每手 >0.25bb 才偏離，其他照 GTO
 7 牌合法（不重複、手牌不在牌面）
回傳碼 0 = 全部通過。需要 playwright + /usr/bin/google-chrome。"""
import argparse, asyncio, json, os, random, re, socket, subprocess, sys, time, collections, math
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('-n', type=int, default=500); ap.add_argument('--only', default='')
ap.add_argument('--shots', type=int, default=0); ap.add_argument('--shotdir', default='/tmp/qa_shots')
ap.add_argument('--json', default='/tmp/qa_all.json')
ap.add_argument('--data-only', action='store_true', help='Run data checks; explicitly skip all browser/layout/keyboard checks')
A = ap.parse_args()

def js_obj(path, var):
    out = subprocess.run(['node', '-e', f"global.window=global;eval(require('fs').readFileSync({json.dumps(path)},'utf8'));"
                          f"for(const p of {json.dumps(var)})eval(require('fs').readFileSync(p,'utf8'));process.stdout.write(JSON.stringify(window.LD||window.HWR))"],
                         capture_output=True, text=True, cwd=ROOT)
    return json.loads(out.stdout)
HWR = js_obj('hwrange.js', [])
LD = js_obj('learn_data.js', ['reads_data.js'])

R = '23456789TJQKA'
def cards(s):
    if isinstance(s, list): s = ''.join(s)
    return re.findall(r'[2-9TJQKA][shdc]', s or '')
def cls(h):
    c = cards(h)
    if len(c) != 2: return None
    a, b = sorted(c, key=lambda x: -R.index(x[0]))
    return a[0] + b[0] if a[0] == b[0] else a[0] + b[0] + ('s' if a[1] == b[1] else 'o')
def hw_ok(kind, key, c): return c in (HWR.get(kind, {}).get(key) or [])

FAIL = collections.defaultdict(list); COUNT = collections.Counter(); CATS = ['1 範圍', '2 行動線', '3 統計範圍', '4 快捷鍵', '5 版面', '6 剝削規則', '7 牌', '0 錯誤']
def fail(cat, drill, msg):
    FAIL[(cat, drill)].append(msg)

# ---------------- 6: data-level exploit rule ----------------
def evs(t): return [float(x) for x in re.findall(r'(?:EV|每手)\s*\+?([\d.]+)\s*bb', t or '')]
def check_data():
    for r in LD['rules']:
        d = 'ln:' + r['id']
        if r['ans'] != r['gto'] and not r.get('dev'): fail('6 剝削規則', 'ln', f"{d} 答案≠GTO 但 dev=false")
        if r.get('dev'):
            e = evs(r.get('gl', '') + ' ' + r.get('why', ''))
            if r.get('gv') != 'sig' or not e or max(e) <= 0.25: fail('6 剝削規則', 'ln', f"{d} 偏離但 gv={r.get('gv')} ev={e}")
        if not r.get('dev') and re.search(r'剝削[^不]', r.get('why', '')) and '照 GTO' not in r.get('why', ''): fail('6 剝削規則', 'ln', f"{d} 照 GTO 但說明寫剝削")
    for k, t in LD['tb'].items():
        gl = t.get('gl') or ''
        if t.get('gv') == 'sig':
            e = evs(gl)
            if e and max(e) <= 0.25: fail('6 剝削規則', 'tb', f"tb {k} sig 但 EV {e}")
        elif t.get('gv') and '照 GTO' not in gl and 'GTO' not in (t.get('note') or '') and t.get('gv') not in ('nonode',): fail('6 剝削規則', 'tb', f"tb {k} gv={t.get('gv')} 沒寫照 GTO：{gl}")
    for k, t in LD['iso'].items():
        if t.get('gv') and t['gv'] != 'sig' and t.get('gl') and '照 GTO' not in t['gl'] and 'GTO' not in t['gl']: fail('6 剝削規則', 'iso', f"iso {k} gv={t['gv']} 沒寫照 GTO")
    norm = lambda a: '邊緣' if a.startswith('邊緣') else a
    for r in LD['reads']:
        ok = r.get('gvd') == 'sig' and (r.get('gev') or 0) > 0.25
        for h in r['hands']:
            ga = h.get('ga')
            if not ga: continue
            a = norm(h['act']); same = a == ga or a.startswith(ga) or (ga == '繼續' and a in ('跟注', '加注'))
            if not same and not ok: fail('6 剝削規則', 'rd', f"rd {r['id']} {h['g']} {h['act']}≠GTO {ga}，但池 {r.get('gvd')} EV {r.get('gev')}")
        if not r.get('sc'): fail('3 統計範圍', 'rd', f"rd {r['id']} 沒有統計範圍")
        if r.get('gvd') != 'nonode' and not re.search('顯著|照 GTO|近 GTO', r.get('gp', '')): fail('3 統計範圍', 'rd', f"rd {r['id']} 沒寫顯著性")
    # ln examples: HW range + w>=50 baked in
    for r in LD['rules']:
        for e in r.get('ex', []):
            h, b, sp, pot, l, p = e
            c = cards(h); bb = cards(b)
            if len(c) != 2 or len(set(c + bb)) != len(c + bb) or len(bb) not in (3, 4, 5): fail('7 牌', 'ln', f"ln {r['id']} 例子牌不合法 {h} {b}")

def check_defs():
    """每個顯示出來的標籤（牌型、牌面、尺寸、行動線、小字）都要能點開、且在 defs.js 有定義"""
    o = subprocess.run(['node', 'tools/defs_check.js'], capture_output=True, text=True, cwd=ROOT)
    if o.returncode != 0:
        for ln in (o.stderr or o.stdout).strip().splitlines()[:40]:
            fail('6 剝削規則', 'lines:defs', ln)
def check_lines():
    """行動線對照表（lines_data.js）：跟 LD 一致、每列有根據、例子合法且在 HW 範圍、規則卡不再有第二份河牌數據"""
    out = subprocess.run(['node', '-e', "global.window=global;eval(require('fs').readFileSync('lines_data.js','utf8'));eval(require('fs').readFileSync('nl2_rules.js','utf8'));process.stdout.write(JSON.stringify({L:window.NLL,R:window.NL2}))"], capture_output=True, text=True, cwd=ROOT)
    D = json.loads(out.stdout); NLL, NL2 = D['L'], D['R']
    from lines_contract import diff, NODES, street, semantic_errors
    for issue in semantic_errors(NLL): fail('6 剝削規則', 'lines:semantics', issue)
    missing = diff(NLL)
    for m in missing:
        fail('6 剝削規則', 'lines:coverage', '缺預期格子 ' + json.dumps(m, ensure_ascii=False))
    for sp, nodes in NODES.items():
        actual = {r['nd'] for r in NLL['rows'] if r['sp'] == sp}
        if any(street(n) == 'turn' for n in nodes) and not any(street(n) == 'turn' for n in actual):
            fail('6 剝削規則', 'lines:coverage', sp + ' 沒有轉牌列')
        for nd in set(nodes) - actual:
            fail('6 剝削規則', 'lines:coverage', sp + ':' + nd + ' 缺節點')
    # 轉／河（非 mw）只要求「走得到」的牌型有答案；走不到的列不顯示，也不再當空格失敗。翻牌與 mw 仍要七種牌型。
    reach_out = subprocess.run(['node', '-e', "global.window=global;global.globalThis=global;eval(require('fs').readFileSync('nl2_reach.js','utf8'));eval(require('fs').readFileSync('lines_data.js','utf8'));process.stdout.write(JSON.stringify(NL2REACH.build(window.NLL).dump()))"], capture_output=True, text=True, cwd=ROOT)
    if reach_out.returncode != 0:
        fail('6 剝削規則', 'lines:reach', 'nl2_reach.js dump failed: ' + (reach_out.stderr or reach_out.stdout)[:200])
        REACHMAP = {}
    else:
        REACHMAP = json.loads(reach_out.stdout)
    def _ckey(r):
        c = r.get('c') or {}
        return json.dumps(c, sort_keys=True, ensure_ascii=False) if c else '{}'
    for sp, nd in {(r['sp'], r['nd']) for r in NLL['rows']}:
        info = REACHMAP.get(sp + '|' + nd) or {}
        if info.get('usesReach') and not info.get('visible'):
            continue
        rr = [r for r in NLL['rows'] if (r['sp'], r['nd']) == (sp, nd) and not r.get('x')]
        for r0 in rr:
            cl = r0.get('cl') or '全部'
            allowed = set(NLL['hc'])
            if info.get('usesReach'):
                allowed = set(info.get('byC', {}).get(_ckey(r0), []) or info.get('byC', {}).get(json.dumps(r0.get('c') or {}, sort_keys=True), []))
                if not allowed:
                    continue
            for hc in allowed:
                if not any((r.get('cl') or '全部') == cl and hc in r['hc'] for r in rr):
                    fail('6 剝削規則', 'lines:grid', f'{sp}:{nd}:{cl}:{hc} 會顯示空格')
    if NLL.get('mw_grid',{}).get('columns') != [{'hr':'PFR'},{'hr':'CALL'}]:
        fail('6 剝削規則', 'lines:mw-roles', 'MW must have opener and caller columns')
    for r in NLL['rows']:
        if r['sp']=='mw' and r.get('c',{}).get('hr') not in ('PFR','CALL'):
            fail('6 剝削規則', 'lines:mw-roles', r['id']+' lacks hero role')
    from mw_sanity import check as check_mw_sanity
    for issue in check_mw_sanity(NLL)[0]:
        fail('6 剝削規則', 'lines:mw-sanity', issue)
    exact = collections.Counter((r['sp'], r['nd'], hc, json.dumps(r.get('c') or {}, sort_keys=True)) for r in NLL['rows'] for hc in r['hc'])
    for key, n in exact.items():
        if n > 1: fail('6 剝削規則', 'lines:duplicates', str(key))
    if set(NLL['basis']) != {'gto', 'pool', 'gtoa', 'est'}: fail('3 統計範圍', 'lines', 'basis must have exactly gto/pool/gtoa/est')
    for filename in ('lines_data.js', 'nl2.js', 'nl2_rules.js'):
        if '原則' in open(os.path.join(ROOT, filename)).read(): fail('3 統計範圍', 'lines', filename + ' contains unsupported evidence label')
    ldr = {r['id']: r for r in LD['rules']}
    seen = collections.defaultdict(list)
    for r in NLL['rows']:
        d = 'lines:' + r['id']
        if r.get('b') not in ('pool', 'gto', 'gtoa', 'est'):
            fail('3 統計範圍', 'lines', f"{d} 沒有根據")
            continue
        if r['b'] == 'est':   # run 003 pool estimate of the most profitable action (not a closed proof)
            v = r.get('pool_est_run003') or {}
            ns = [int(n.replace(',', '')) for n in re.findall(r'n=([\d,]+)', r.get('ev', ''))]
            dom = r.get('dominance')
            if dom and (not dom.get('by') or any((next((x for x in NLL['rows'] if x['id'] == i), {}).get('a', 'f') == 'f') != (r['a'] == 'f') for i in dom['by'])): fail('6 剝削規則', 'lines', d + ' dominance fix without a matching source row')
            elif dom: pass
            elif r['sp'] == 'mw' or not v or v.get('action') != r['a'] or not r.get('evidence', '').startswith(('run003:', 'run004:')): fail('3 統計範圍', 'lines', d + ' invalid run003/run004 estimate provenance')
            elif not ns or v.get('n', 0) < 40 or max(ns) < 40: fail('3 統計範圍', 'lines', d + ' run003 estimate n<40')
            elif '估算' not in r['why'] or '不是封閉證明' not in r['ev'] or 'GTO 基準' not in r['ev'] or '95% CI' not in r['ev']: fail('3 統計範圍', 'lines', d + ' run003 estimate lacks honest labels / GTO baseline / CI')
            elif not dom and r['a'] not in (v.get('arms') or {}) or any(x['ev_bb'] > v['arms'][r['a']]['ev_bb'] + 1e-9 for x in v['arms'].values()): fail('6 剝削規則', 'lines', d + ' run003 answer is not the best estimated arm')
        if r['b'] == 'gtoa':
            v = r.get('solver', {})
            if r['sp'] != 'mw' or not v.get('samples') or not v.get('freq'):
                fail('3 統計範圍', 'lines', d + ' invalid MW approximation provenance')
            elif r['a'] != max(v['freq'], key=v['freq'].get) or abs(sum(v['freq'].values())-1) > .001:
                fail('6 剝削規則', 'lines', d + ' inconsistent approximation frequency')
        composition = (r['sp']=='mw' and r['nd'] in ('f_vs_bet','t_vs_bet') and r['hc']==['S'] and r.get('evidence','').startswith('mw-composition:') and '勝率檢定只比較跟/棄，加注依原表的池攤牌組成' in r['ev'] and ((r['a']=='r' and r['ok']==['c']) or (r['a']=='c' and r['ok']==['r'])))
        if r.get('evidence','').startswith('mw-composition:') and not composition: fail('3 統計範圍','lines',d+' invalid original composition evidence')
        if r['b'] == 'pool' and not (re.search(r'n=[\d,]+', r['ev']) and POS.search(r['ev']) and (composition or re.search('顯著|不明顯', r['ev']))): fail('3 統計範圍', 'lines', f"{d} 池數據沒 n/位置/顯著性：{r['ev'][:60]}")
        if r.get('src', '').startswith('ld:'):
            L0 = ldr.get(r['src'][3:])
            if not L0: fail('6 剝削規則', 'lines', f"{d} 對不到 LD {r['src']}")
            elif L0['ans'] != r['a'] and not r.get('evidence', '').startswith('legacy:'): fail('6 剝削規則', 'lines', f"{d} 跟行動線題不一致：表 {r['a']} vs LD {L0['ans']}")
        if r.get('evidence', '').startswith('legacy:'):
            gf = ldr[r['src'][3:]].get('gf', {})
            if not gf or r['a'] != max(gf, key=gf.get): fail('6 剝削規則', 'lines', d + ' is not solver majority')
        if r['b'] == 'pool':
            if not re.search(r'95%\s*CI|95%.*信賴', r.get('ev', '')):
                fail('3 統計範圍', 'lines', d + ' lacks 95% CI')
            river_pool = r.get('river_pool') if r['sp'] == 'mw' and r.get('evidence', '').startswith('run8:river:') else None
            if river_pool:
                v = river_pool; n = v['n']; p = v['w']/n*100
                e = 1.96*math.sqrt(max((p/100)*(1-p/100), 1e-9)/n)*100
                expected_action = 'c' if p >= v['need'] else 'f'
                significant = abs(p-v['need']) > e
                expected_ok = [] if significant else ['f' if expected_action == 'c' else 'c']
                if n < 40 or not v.get('closes') or r['nd'] not in ('r_vs_bet', 'r_vs_xr'):
                    fail('3 統計範圍', 'lines', d + ' invalid closing river sample')
                if r['a'] != expected_action or r['ok'] != expected_ok:
                    fail('6 剝削規則', 'lines', d + ' inconsistent river verdict')
                if len(v['ci']) != 2 or any(abs(x-y)>1e-8 for x,y in zip(v['ci'], [p-e,p+e])):
                    fail('3 統計範圍', 'lines', d + ' invalid river CI')
                audit = NLL['mw_grid']['cells'].get(r['nd']+'|'+r['hc'][0], {})
                if n != audit.get('n') or not 0 <= v['w'] <= n or not 0 <= v['need'] <= 100:
                    fail('3 統計範圍', 'lines', d + ' inconsistent river audit')
            realized = r.get('realized') if r['sp'] == 'mw' and r.get('evidence', '').startswith('run7:realized:') else None
            if realized:
                actions = realized.get('actions', {})
                if len(actions) < 2 or any(v['n'] < 40 for v in actions.values()): fail('3 統計範圍', 'lines', d + ' insufficient per-action realized sample')
                if r['a'] != max(actions, key=lambda a: actions[a]['mean']): fail('6 剝削規則', 'lines', d + ' not best observed mean')
                expected_ok = []
                for action, values in actions.items():
                    if action == r['a']: continue
                    best = actions[r['a']]; delta = best['mean'] - values['mean']
                    se = math.sqrt(best['variance']/best['n'] + values['variance']/values['n'])
                    ci = [delta-1.96*se, delta+1.96*se]
                    if any(abs(x-y)>1e-8 for x,y in zip(ci, realized['ci'].get(action, []))) or len(realized['ci'].get(action, [])) != 2: fail('3 統計範圍', 'lines', d + ' invalid realized CI')
                    if ci[0] <= 0: expected_ok.append(action)
                if sorted(r['ok']) != sorted(expected_ok): fail('6 剝削規則', 'lines', d + ' inconsistent alternatives')
            if not realized and not river_pool and (not re.search(r'GTO.*基準|GTO基準', r.get('ev', '')) or re.search(r'無.*GTO.*基準|沒有.*GTO', r.get('ev', ''))):
                fail('3 統計範圍', 'lines', d + ' lacks same-node GTO baseline')
            ns = [int(n.replace(',', '')) for n in re.findall(r'n=([\d,]+)', r['ev'])]
            if not ns or min(ns) < 40 or (not composition and not realized and not river_pool and ('不明顯' in r['ev'] or '不顯著' in r['ev'])): fail('3 統計範圍', 'lines', d + ' lacks significant n>=40 support')
        if r['a'] in r['ok']: fail('6 剝削規則', 'lines', f"{d} 答案也在 ok 裡")
        if not r.get('x'):
            for h in r['hc']: seen[(r['sp'], r['nd'], r.get('cl'), h)].append(r['id'])
        for e in r['eg']:
            c = cards(e['h']); bb = cards(e['b'])
            if len(c) != 2 or len(set(c + bb)) != len(c + bb) or len(bb) not in (3, 4, 5): fail('7 牌', 'lines', f"{d} 例子牌不合法 {e['h']} {e['b']}")
            k, key = e['role']
            if k in ('open', 'call', 'tb', 'c3', 'iso') and not hw_ok(k, key, cls(e['h'])): fail('1 範圍', 'lines', f"{d} 例子 {cls(e['h'])} 不在 HW {k} {key}")
    for k, v in seen.items():
        if len(v) > 1: fail('6 剝削規則', 'lines', f"同一格兩個答案 {k}: {v}")
    if 'river' in NL2: fail('6 剝削規則', 'lines', 'nl2_rules.js 還有第二份河牌數據（NL2.river）')

# ---------------- browser harness ----------------
HARN = r"""
window.__QA = async function(n, ansSel, nextSel, settle){
 const ANSSEL=ansSel, NXTSEL=nextSel;
 const sleep=t=>new Promise(r=>setTimeout(r,t)), out=[];
 const vis=e=>{if(!e.isConnected||e.disabled)return false;const r=e.getBoundingClientRect();if(!r.width||!r.height)return false;const cs=getComputedStyle(e);if(cs.visibility==='hidden'||cs.display==='none')return false;const dd=e.parentElement&&e.parentElement.closest('details:not([open])');return !(dd&&!(e.tagName==='SUMMARY'&&e.parentElement===dd))};
 const CTRL='button,a[href],summary,select,input:not([type=hidden]),textarea,[role=button]';
 const measure=()=>{ if(window.PKKEYS)PKKEYS.render(); const L=window.PKKEYS&&PKKEYS.last(); const cov=new Set();
   if(L)L.list.forEach(x=>{if(x.badge&&x.label)x.els.forEach(e=>cov.add(e))});
   const miss=[...document.querySelectorAll(CTRL)].filter(e=>vis(e)&&!e.closest('#kkhint,#kkhelp,.kk')&&!e.matches('.df[data-df]')&&!cov.has(e)).map(e=>(e.tagName+'.'+(e.className||'')+' '+(e.textContent||'').trim().slice(0,20)));
   return {sh:document.documentElement.scrollHeight, ih:innerHeight, sw:document.documentElement.scrollWidth, iw:innerWidth, miss:miss.slice(0,4), nmiss:miss.length, txt:(document.querySelector('main')||document.body).innerText.slice(0,4000), act:[...new Set([...document.querySelectorAll('.ral,.line,.facing,.pfl')].concat([...document.querySelectorAll('.st')].map(e=>e.parentElement)))].filter(e=>e&&e.offsetParent).map(e=>e.innerText).join('\n'), kb:keyBottom()} };
 const keyBottom=()=>{let b=0;const els=[...document.querySelectorAll(ANSSEL+','+NXTSEL)].filter(vis);
   [...document.querySelectorAll('body *')].forEach(e=>{if(e.children.length<=3&&(e.textContent||"").trim().length<40&&/^\s*[✓✗]/.test(e.textContent||'')&&vis(e))els.push(e)});
   els.forEach(e=>{const r=e.getBoundingClientRect();if(getComputedStyle(e).position!=='fixed'||1)b=Math.max(b,r.bottom+scrollY)});return Math.round(b)};
 let prev=null;
 for(let i=0;i<n;i++){
   let q=null; for(let k=0;k<300;k++){ if(window.__Q&&window.__Q!==prev){q=window.__Q;break} if(window.__QNUDGE&&k%40==39){const nx=[...document.querySelectorAll(nextSel)].filter(vis)[0]; if(nx) nx.click()} await sleep(10) }
   if(!q){out.push({end:1});break}
   prev=q; await sleep(settle); const m1=measure(); let m2=null;
   const ans=[...document.querySelectorAll(ansSel)].filter(vis);
   if(ans.length){ ans[Math.floor(Math.random()*ans.length)].click(); await sleep(settle); m2=measure(); }
   out.push({q:JSON.parse(JSON.stringify(q)), m1, m2});
   if(window.__Q!==prev) continue;
   const nx=[...document.querySelectorAll(nextSel)].filter(vis)[0]; if(nx) nx.click(); else if(window.__QNEXT) window.__QNEXT();
 }
 return out;
}"""
ANS = '[data-a]:not([data-a=next]),[data-qa],#abar .ab[data-k]'
NXT = '[data-next],[data-a=next],[data-qn],[data-dnext],#bNext'

def drills():
    D = []
    pre = ['bb-utg', 'bb-hj', 'bb-co', 'bb-btn', 'bb-sb', 'sb', 'btn', 'open', 'rfi-utg', 'rfi-hj', 'rfi-co', 'rfi-sb', '3bet', 'vs3b', 'vs4b', 'mix', 'real']
    for p in pre: D.append(dict(name='pre:' + p, url=f'index.html#{p}', runs=[('', A.n)]))
    for c in ['', '.f_cbet', '.f_vs_cbet', '.barrel', '.vs_barrel', '.r_barrel', '.r_vs_bet']:
        D.append(dict(name='postflop:all' + c, url=f'postflop/index.html#all{c}', runs=[('', A.n)], settle=40))
    D.append(dict(name='postflop:handx', url='postflop/index.html#handx', runs=[('', A.n)], settle=40))   # 剝削整手
    D.append(dict(name='postflop:handg', url='postflop/index.html#handg', runs=[('', A.n)], settle=40))   # GTO 整手
    grps = ['SRP_IP', 'SRP_BB', '3BP_3bettor', '3BP_caller']
    D.append(dict(name='ln', url='learn.html#ln', runs=[(f"LQ.st.mode='drill';LQ.st.grp='{g}';LQ.st.cat='all';LQ.st.q=null;LQ.draw()", A.n // 4 + 1) for g in grps]))
    D.append(dict(name='rd', url='learn.html#rd', runs=[("LQ.st.rm='drill';LQ.st.rg='all';LQ.st.q=null;LQ.draw()", A.n)]))
    tb = list(LD['tb']); iso = list(LD['iso'])
    D.append(dict(name='tb', url='learn.html#tb', runs=[(f"LQ.st.tb='{k}';LQ.st.q=null;LQ.draw()", A.n // len(tb) + 1) for k in tb]))
    D.append(dict(name='iso', url='learn.html#iso', runs=[(f"LQ.st.iso='{k}';LQ.st.q=null;LQ.draw()", A.n // len(iso) + 1) for k in iso]))
    D.append(dict(name='eq', url='learn.html#eq', runs=[("(document.querySelector('[data-md=quiz],[data-mode=quiz]')||{click(){}}).click()", A.n)], settle=30))
    D.append(dict(name='nl2:river', url='nl2.html#river', runs=[('', A.n)]))
    D.append(dict(name='nl2:drill', url='nl2.html#drill', runs=[(f"document.querySelector('[data-f=\"{k}\"]').click()", A.n // 8 + 1) for k in ('all', 'ipfr', 'bb', 'opfr', 'ipc', '3bp', 'iso', 'mw')]))
    D.append(dict(name='solver:riv', url='solver.html#riv', runs=[('', A.n)]))
    for f in sorted(os.listdir(os.path.join(ROOT, 'review'))):
        if re.match(r'\d{4}-\d\d-\d\d\.html$', f): D.append(dict(name='review:' + f[:-5], url=f'review/{f}#quiz', runs=[('', 100000)], finite=True))
    D.append(dict(name='review:postflop', url='review/postflop.html#quiz', runs=[('', 100000)], finite=True))
    return D
STATIC = ['index.html#home', 'index.html#prac', 'index.html#preflop', 'index.html#leaks', 'index.html#about', 'learn.html#ln?sheet', 'learn.html#rd?sheet',
          'learn.html#eq', 'postflop/index.html#prac', 'postflop/index.html#charts', 'postflop/index.html#about', 'postflop/index.html#handx', 'postflop/index.html#handg', 'solver.html#tool', 'review/index.html', 'review/2026-10-31.html', 'review/2026-11-02.html', 'review/postflop.html', 'nl2.html#card', 'nl2.html#lines', 'review/2026-11-04.html']

POS = re.compile(r'UTG|HJ|CO|BTN|SB|BB')
SIZE_OK = re.compile(r'\d|½|⅓|¼|⅔|¾|不分|全下|最小|all-?in', re.I)
AGG = re.compile(r'(下注|加注|開池|開 |3-bet|4-bet|c-bet|再開槍|領先|donk|probe)', re.I)
def seg_sizes(text):
    bad = []
    for ln in text.split('\n'):
        for seg in re.split(r'→|，|；|、', ln):
            if AGG.search(seg) and not SIZE_OK.search(seg) and not re.search(r'GTO|池 |頻率|%|勝率|範圍|問|練習|你要|該|怎麼', seg): bad.append(seg.strip()[:40])
    return bad

def check_q(d, it):
    q, m1, m2 = it['q'], it['m1'], it.get('m2'); dr = q.get('drill', '?'); nm = d['name']
    tag = f"{q.get('id')} {q.get('hero')} {q.get('board', '')}"
    # 7 cards
    h = cards(q.get('hero')); b = cards(q.get('board')); full = cards(q.get('full')) or b
    if dr not in ('eq',):
        if len(h) != 2: fail('7 牌', nm, f"手牌不是兩張：{tag}")
        if len(set(h + full)) != len(h + full): fail('7 牌', nm, f"牌重複：{tag}")
    # 1 range
    role = q.get('role') or ['pre', '']; c = cls(q.get('hero'))
    if not q.get('real') and role[0] in ('open', 'call', 'tb', 'c3', 'iso') and c and not hw_ok(role[0], role[1], c):
        fail('1 範圍', nm, f"{c} 不在 HW {role[0]} {role[1]}：{tag}")
    if dr in ('postflop', 'hand') and not q.get('pre') and (q.get('w') or 0) < 50: fail('1 範圍', nm, f"w={q.get('w')} <50：{tag}")
    if dr == 'pre' and role[0] != 'pre' and (q.get('reach') or 0) < 50: fail('1 範圍', nm, f"到達率 {q.get('reach')} <50：{tag}")
    if dr == 'hand':
        if q.get('ver') == 'exp' and not q.get('pm') and not q.get('xr'): fail('1 範圍', nm, f"剝削整手出了剝削解走不到的手：{tag}")
        if q.get('ver') != ('exp' if nm.endswith('handx') else 'gto'): fail('6 剝削規則', nm, f"版本不對（{q.get('ver')}）：{tag}")
        if m2:
            t2 = m2['txt']
            if re.search(r'✓ 正確[\s\S]*你選的頻率 0%', t2): fail('6 剝削規則', nm, f"頻率 0% 卻判對：{tag}")
            if '你選的頻率' not in t2: fail('6 剝削規則', nm, f"答案沒寫你選的頻率：{tag}")
            if not re.search(r'依 (剝削 NL2 池|剝削|GTO) 評分', t2): fail('6 剝削規則', nm, f"沒寫依剝削或 GTO 評分：{tag}")
            if q.get('ver') == 'exp':
                if not re.search(r'0\.25|同動作|走不到|不會走到|沒存這個點', t2): fail('6 剝削規則', nm, f"剝削整手沒寫為什麼用剝削/GTO：{tag}")
                if '依 剝削' in t2 and '剝削模型 EV' not in t2: fail('6 剝削規則', nm, f"剝削評分沒列剝削模型 EV：{tag}")
                if '依 剝削' in t2 and not re.search(r'池 [\d.]+%[^\n]*n=[\d,]+|樣本不足', t2): fail('3 統計範圍', nm, f"剝削評分沒列池統計（n）：{tag}")
    if dr == 'solver-riv' and m2 and re.search(r'不會到達這個節點', m2['txt']): fail('1 範圍', nm, f"出了剝削解裡不會走到的手：{tag}")
    if dr == 'solver-riv' and m2 and re.search(r'✓ 正確[^\n]*頻率 0%', m2['txt']): fail('6 剝削規則', nm, f"頻率 0% 卻判對：{tag}")
    if dr == 'solver-riv' and not q.get('hwok'): fail('1 範圍', nm, f"河牌手牌非 HW 核心/到達率低：{tag}")
    # 2 streets
    txt = (m1 or {}).get('txt', '')
    need = ['翻前'] + ['翻牌', '轉牌', '河牌'][:max(0, len(b) - 2) if len(b) >= 3 else 0]
    if dr in ('ln', 'rd'):
        rows = q.get('rows') or []
        if dr == 'rd': need = ['翻前'] + ['翻牌', '轉牌', '河牌'][:q.get('street') or 1]
        for s in need:
            if s not in rows: fail('2 行動線', nm, f"缺 {s}（有 {rows}）：{tag}")
    elif dr in ('postflop', 'hand', 'solver-riv', 'eq', 'nl2lines'):
        need = ['翻前'] if dr == 'eq' else need
        for s in need:
            if s not in txt: fail('2 行動線', nm, f"畫面缺 {s}：{tag}")
    elif dr in ('rvday', 'rvpost'):
        seen = q.get('seen') or []; st = q.get('st')
        for s in (['pre', 'flop', 'turn', 'river'][: ['pre', 'flop', 'turn', 'river'].index(st)] if st in ('pre', 'flop', 'turn', 'river') else []):
            if s not in seen: fail('2 行動線', nm, f"缺 {s} 行動：{tag}")
    if dr not in ('rvday', 'rvpost'):
        for sg in seg_sizes((m1 or {}).get('act', '')): fail('2 行動線', nm, f"動作沒尺寸「{sg}」：{tag}")
    # 3 scope
    for when, m in (('題目', m1), ('答案', m2)):
        if not m: continue
        t = m['txt']
        if re.search(r'(?<![半滿])池\s*\d+%', t):
            if not re.search(r'n\s*=\s*[\d,]+|[\d,]+\s*手|攤牌\s*[\d,]+|攤牌 n', t): fail('3 統計範圍', nm, f"{when}有池統計但沒 n：{tag}")
            if not re.search(r'顯著|照 GTO|可剝削|不明顯|很小|近 GTO|無 GTO 對照|無理論值|只看玩家池', t): fail('3 統計範圍', nm, f"{when}有池統計但沒寫顯著性：{tag}")
            if not POS.search(t): fail('3 統計範圍', nm, f"{when}沒寫位置：{tag}")
    if dr in ('ln', 'rd', 'tb', 'iso') and not (q.get('sc') and POS.search(q.get('sc'))): fail('3 統計範圍', nm, f"沒有範圍行：{tag}")
    if dr == 'ln' and q.get('gl') and not q.get('psc'): fail('3 統計範圍', nm, f"GTO 對池沒範圍：{tag}")
    if dr == 'eq' and not (q.get('n') and q.get('sd') is not None): fail('3 統計範圍', nm, f"勝率卡沒 n/攤牌 n：{tag}")
    # 6 eq advice must be read-only
    for m in (m1, m2):
        if m and dr == 'eq' and re.search(r'多跟注|多棄牌|多下注|少薄價值|多過牌', m['txt']): fail('6 剝削規則', nm, f"勝率頁給了動作建議（沒算 EV）：{tag}")
    # 4 shortcuts, 5 layout (desktop)
    for when, m in (('題目', m1), ('答案', m2)):
        if not m: continue
        if m['nmiss']: fail('4 快捷鍵', nm, f"{when} {m['nmiss']} 個按鈕沒快捷鍵 {m['miss']}")
        if when == '題目' and m['sh'] > m['ih'] + 2: fail('5 版面', nm, f"題目 1280×800 要捲動（{m['sh']}px）：{tag}")
        if when == '答案' and m['kb'] > m['ih'] + 2: fail('5 版面', nm, f"答案（對錯＋按鈕）超出 1280×800（{m['kb']}px）：{tag}")
        if m['sw'] > m['iw'] + 2: fail('5 版面', nm, f"{when} 橫向溢出 {m['sw']}px")

async def goto(pg, url):
    # 本機伺服器偶爾卡住：重試，不讓整輪 QA 掛掉
    for k in range(3):
        try: return await pg.goto(url, timeout=60000)
        except Exception:
            if k == 2: raise
            await pg.wait_for_timeout(2000)


async def run():
    port = (lambda s: (s.bind(('127.0.0.1', 0)), s.getsockname()[1], s.close())[1])(socket.socket())
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8); base = f'http://127.0.0.1:{port}/'
    os.makedirs(A.shotdir, exist_ok=True); shots = []
    try:
        async with async_playwright() as p:
            br = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
            async def page(w, h, mobile=False):
                ctx = await br.new_context(viewport={'width': w, 'height': h}, is_mobile=mobile, has_touch=mobile, device_scale_factor=2 if mobile else 1, service_workers='block')
                pg = await ctx.new_page(); errs = []
                pg.on('pageerror', lambda e: errs.append(str(e)))
                await pg.add_init_script("try{localStorage.clear()}catch(e){}"); return pg, errs, ctx
            for d in drills():
                if A.only and A.only not in d['name']: continue
                pg, errs, ctx = await page(1280, 800)
                await goto(pg, base + d['url']); await pg.wait_for_timeout(1500); await pg.evaluate(HARN)
                tot = 0
                for prep, n in d['runs']:
                    if prep: await pg.evaluate(prep); await pg.wait_for_timeout(50)
                    res = await pg.evaluate(f"__QA({n}, {json.dumps(ANS)}, {json.dumps(NXT)}, {d.get('settle', 15)})")
                    for it in res:
                        if 'q' not in it: continue
                        tot += 1; check_q(d, it)
                        if A.shots and random.random() < A.shots / 9000: shots.append((d['url'], prep, it['q']))
                COUNT[d['name']] = tot
                if tot < (1 if d.get('finite') else A.n): fail('0 錯誤', d['name'], f"只產生 {tot} 題（要 {A.n}）")
                for e in errs[:5]: fail('0 錯誤', d['name'], 'JS 錯誤：' + e[:160])
                # mobile: larger text
                mp, merr, mctx = await page(390, 844, True)
                await goto(mp, base + d['url']); await mp.wait_for_timeout(1500)
                if d['runs'][0][0]: await mp.evaluate(d['runs'][0][0]); await mp.wait_for_timeout(300)
                fs = await mp.evaluate("(()=>{const e=[...document.querySelectorAll('.qs,.eqq,.facing,.ral,.ctx,.line,.qcard,.spotT,.qtxt,#qbox,main p')].find(x=>x.offsetParent&&x.innerText.trim());return e?parseFloat(getComputedStyle(e).fontSize):0})()")
                dfs = await pg.evaluate("(()=>{const e=[...document.querySelectorAll('.qs,.eqq,.facing,.ral,.ctx,.line,.qcard,.spotT,.qtxt,#qbox,main p')].find(x=>x.offsetParent&&x.innerText.trim());return e?parseFloat(getComputedStyle(e).fontSize):0})()")
                mw = await mp.evaluate('[document.documentElement.scrollWidth, innerWidth]')
                if fs < 15 or fs < dfs: fail('5 版面', d['name'], f"手機字 {fs}px（桌機 {dfs}px）")
                if mw[0] > mw[1] + 2: fail('5 版面', d['name'], f"手機橫向溢出 {mw}")
                print(f"{d['name']:<24} {tot:>5} 題", flush=True)
                await ctx.close(); await mctx.close()
            # static pages: shortcuts + overflow + mobile font
            for u in STATIC:
                if A.only and A.only not in u: continue
                pg, errs, ctx = await page(1280, 800); url, _, flag = u.partition('?')
                await goto(pg, base + url); await pg.wait_for_timeout(1500); await pg.evaluate(HARN)
                if flag == 'sheet': await pg.evaluate("LQ.st.mode='sheet';LQ.st.rm='sheet';LQ.draw()"); await pg.wait_for_timeout(200)
                m = await pg.evaluate("(async()=>{const r=await __QA(0,'x','x',1);return null})()")
                mm = await pg.evaluate("""(()=>{PKKEYS&&PKKEYS.render();const L=PKKEYS&&PKKEYS.last(),cov=new Set();if(L)L.list.forEach(x=>{if(x.badge&&x.label)x.els.forEach(e=>cov.add(e))});
                  const CTRL='button,a[href],summary,select,input:not([type=hidden]),textarea,[role=button]';const vis=e=>{if(!e.isConnected||e.disabled)return false;const r=e.getBoundingClientRect();if(!r.width||!r.height)return false;const cs=getComputedStyle(e);if(cs.visibility==='hidden'||cs.display==='none')return false;const dd=e.parentElement&&e.parentElement.closest('details:not([open])');return !(dd&&!(e.tagName==='SUMMARY'&&e.parentElement===dd))};
                  const miss=[...document.querySelectorAll(CTRL)].filter(e=>vis(e)&&!e.closest('#kkhint,#kkhelp,.kk')&&!e.matches('.df[data-df]')&&!cov.has(e)).map(e=>e.tagName+' '+(e.textContent||'').trim().slice(0,20));
                  return {miss:miss.slice(0,5),n:miss.length,sw:document.documentElement.scrollWidth,iw:innerWidth,txt:document.body.innerText.slice(0,20000)}})()""")
                if mm['n']: fail('4 快捷鍵', 'static:' + u, f"{mm['n']} 個按鈕沒快捷鍵 {mm['miss']}")
                if mm['sw'] > mm['iw'] + 2: fail('5 版面', 'static:' + u, f"橫向溢出 {mm['sw']}")
                if re.search(r'(?<![半滿])池\s*\d+%', mm['txt']) and not re.search(r'n\s*=\s*[\d,]+|[\d,]+\s*手|攤牌', mm['txt']): fail('3 統計範圍', 'static:' + u, '有池統計但整頁沒有 n')
                for e in errs[:3]: fail('0 錯誤', 'static:' + u, 'JS 錯誤：' + e[:160])
                COUNT['static:' + u] = 1; await ctx.close()
                print(f"static {u}", flush=True)
            await br.close()
    finally:
        srv.terminate()
    return shots

check_data(); check_lines(); check_defs()
shots = [] if A.data_only else asyncio.run(run())
if A.data_only: print('DATA ONLY: browser drills, layout and keyboard checks SKIPPED')
tot = 0; rep = {}
print('\n==== 結果 ====')
for cat in CATS:
    items = {k[1]: v for k, v in FAIL.items() if k[0] == cat}; n = sum(len(v) for v in items.values()); tot += n
    print(f"{cat}: {n} 失敗")
    for dname, v in items.items():
        print(f"   {dname}: {len(v)}  例：{' ｜ '.join(sorted(set(v))[:3])}")
    rep[cat] = {k: v[:50] for k, v in items.items()}
print(f"題數：{sum(v for k, v in COUNT.items() if not k.startswith('static'))}（{len([k for k in COUNT if not k.startswith('static')])} 個練習）；失敗合計 {tot}")
json.dump(dict(browser_skipped=A.data_only, fail=rep, count=COUNT, shots=shots[:A.shots] if A.shots else []), open(A.json, 'w'), ensure_ascii=False, indent=1)
sys.exit(1 if tot else 0)
