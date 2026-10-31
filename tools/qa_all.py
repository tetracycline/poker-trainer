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
import argparse, asyncio, json, os, random, re, socket, subprocess, sys, time, collections
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('-n', type=int, default=500); ap.add_argument('--only', default='')
ap.add_argument('--shots', type=int, default=0); ap.add_argument('--shotdir', default='/tmp/qa_shots')
ap.add_argument('--json', default='/tmp/qa_all.json')
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

# ---------------- browser harness ----------------
HARN = r"""
window.__QA = async function(n, ansSel, nextSel, settle){
 const ANSSEL=ansSel, NXTSEL=nextSel;
 const sleep=t=>new Promise(r=>setTimeout(r,t)), out=[];
 const vis=e=>{if(!e.isConnected||e.disabled)return false;const r=e.getBoundingClientRect();if(!r.width||!r.height)return false;const cs=getComputedStyle(e);if(cs.visibility==='hidden'||cs.display==='none')return false;const dd=e.parentElement&&e.parentElement.closest('details:not([open])');return !(dd&&!(e.tagName==='SUMMARY'&&e.parentElement===dd))};
 const CTRL='button,a[href],summary,select,input:not([type=hidden]),textarea,[role=button]';
 const measure=()=>{ if(window.PKKEYS)PKKEYS.render(); const L=window.PKKEYS&&PKKEYS.last(); const cov=new Set();
   if(L)L.list.forEach(x=>{if(x.badge&&x.label)x.els.forEach(e=>cov.add(e))});
   const miss=[...document.querySelectorAll(CTRL)].filter(e=>vis(e)&&!e.closest('#kkhint,#kkhelp,.kk')&&!cov.has(e)).map(e=>(e.tagName+'.'+(e.className||'')+' '+(e.textContent||'').trim().slice(0,20)));
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
    D.append(dict(name='solver:riv', url='solver.html#riv', runs=[('', A.n)]))
    for f in sorted(os.listdir(os.path.join(ROOT, 'review'))):
        if re.match(r'\d{4}-\d\d-\d\d\.html$', f): D.append(dict(name='review:' + f[:-5], url=f'review/{f}#quiz', runs=[('', 100000)], finite=True))
    D.append(dict(name='review:postflop', url='review/postflop.html#quiz', runs=[('', 100000)], finite=True))
    return D
STATIC = ['index.html#home', 'index.html#prac', 'index.html#preflop', 'index.html#leaks', 'index.html#about', 'learn.html#ln?sheet', 'learn.html#rd?sheet',
          'learn.html#eq', 'postflop/index.html#prac', 'postflop/index.html#charts', 'postflop/index.html#about', 'postflop/index.html#handx', 'postflop/index.html#handg', 'solver.html#tool', 'review/index.html', 'review/2026-10-31.html', 'review/postflop.html']

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
    elif dr in ('postflop', 'hand', 'solver-riv', 'eq'):
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
                await pg.goto(base + d['url']); await pg.wait_for_timeout(1500); await pg.evaluate(HARN)
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
                await mp.goto(base + d['url']); await mp.wait_for_timeout(1500)
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
                await pg.goto(base + url); await pg.wait_for_timeout(1500); await pg.evaluate(HARN)
                if flag == 'sheet': await pg.evaluate("LQ.st.mode='sheet';LQ.st.rm='sheet';LQ.draw()"); await pg.wait_for_timeout(200)
                m = await pg.evaluate("(async()=>{const r=await __QA(0,'x','x',1);return null})()")
                mm = await pg.evaluate("""(()=>{PKKEYS&&PKKEYS.render();const L=PKKEYS&&PKKEYS.last(),cov=new Set();if(L)L.list.forEach(x=>{if(x.badge&&x.label)x.els.forEach(e=>cov.add(e))});
                  const CTRL='button,a[href],summary,select,input:not([type=hidden]),textarea,[role=button]';const vis=e=>{if(!e.isConnected||e.disabled)return false;const r=e.getBoundingClientRect();if(!r.width||!r.height)return false;const cs=getComputedStyle(e);if(cs.visibility==='hidden'||cs.display==='none')return false;const dd=e.parentElement&&e.parentElement.closest('details:not([open])');return !(dd&&!(e.tagName==='SUMMARY'&&e.parentElement===dd))};
                  const miss=[...document.querySelectorAll(CTRL)].filter(e=>vis(e)&&!e.closest('#kkhint,#kkhelp,.kk')&&!cov.has(e)).map(e=>e.tagName+' '+(e.textContent||'').trim().slice(0,20));
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

check_data()
shots = asyncio.run(run())
tot = 0; rep = {}
print('\n==== 結果 ====')
for cat in CATS:
    items = {k[1]: v for k, v in FAIL.items() if k[0] == cat}; n = sum(len(v) for v in items.values()); tot += n
    print(f"{cat}: {n} 失敗")
    for dname, v in items.items():
        print(f"   {dname}: {len(v)}  例：{' ｜ '.join(sorted(set(v))[:3])}")
    rep[cat] = {k: v[:50] for k, v in items.items()}
print(f"題數：{sum(v for k, v in COUNT.items() if not k.startswith('static'))}（{len([k for k in COUNT if not k.startswith('static')])} 個練習）；失敗合計 {tot}")
json.dump(dict(fail=rep, count=COUNT, shots=shots[:A.shots] if A.shots else []), open(A.json, 'w'), ensure_ascii=False, indent=1)
sys.exit(1 if tot else 0)
