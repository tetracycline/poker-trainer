(function(){
const R = window.NL2, L = window.NLL, H = window.HWR, $ = s => document.querySelector(s), app = $('#app');
const RK = '23456789TJQKA', SU = {s: '♠', h: '♥', d: '♦', c: '♣'};
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const cd = c => `<span class="cd ${c[1] === 'h' ? 'r' : c[1] === 'd' ? 'd' : c[1] === 'c' ? 'c' : ''}">${c[0] === 'T' ? '10' : c[0]}${SU[c[1]]}</span>`;
const pretty = cs => cs.map(c => (c[0] === 'T' ? '10' : c[0]) + SU[c[1]]).join('');
const nodeLabel = (sp, nd) => (L.node_labels?.[sp]?.[nd] || L.nd[nd] || nd);
// ---------- 規則卡 ----------
function card() {
  window.__Q = null;
  app.innerHTML = `<div class="sec"><b class="h">NL2 規則卡（${esc(R.ver)}）</b><p class="small muted">${esc(R.scope)}<br>${esc(R.bias)}<br>每條規則：觀察＝你的手牌；數據＝玩家池（括號是 n 和誤差）；規則＝要做什麼；最後是練習的地方。翻前的規則跟網站翻前表一致；翻後的每個動作都在「行動線對照表」（同一份數據，練習也從那裡出題）。</p></div>` +
   R.rules.map(r => r.auto ? Object.assign({}, r, {data: r.data.concat(autoData(r.auto))}) : r).map((r, i) => `<div class="sec"><b class="h">${i + 1}. ${esc(r.t)}</b><span class="ev">${esc(r.ev)}</span>
   <p><span class="lab">觀察</span>　${esc(r.obs)}</p><div><span class="lab">數據</span><ul>${r.data.map(d => `<li class="small">${esc(d)}</li>`).join('')}</ul></div>
   <p><span class="lab">規則</span>　<b>${esc(r.rule)}</b></p><div>${r.go.map(([h, t]) => `<a class="btn" href="${h}">${esc(t)}</a>`).join('')}</div></div>`).join('') +
   `<div class="sec small muted">覆盤：<a href="review/2026-11-04.html">11/4 覆盤＋11/5 大數據診斷</a></div>`;
}
function autoData(a) { // 規則卡的數字直接從對照表讀，不另存一份
  const [sp, nd] = a.split(':'), R = L.rows.filter(r => r.sp === sp && r.nd === nd && !r.x && r.c && r.c.sz), out = [];
  [...new Set(R.map(r => r.cl))].forEach(k => { const rr = R.filter(r => r.cl === k && r.hc.some(h => ['S', 'TPG', 'TPW', 'MID'].includes(h)));
    if (!rr.length) return;
    const buckets = {le50: [0.33, 0.5], p75: [0.75, 1], o150: [1.5], all: [0.33, 0.5, 0.75, 1]};
    const sizes = buckets[rr[0].c.sz];
    if (!sizes) throw new Error('Unknown bet size bucket');
    const odds = sizes.map(bet => Math.round(100 * bet / (1 + 2 * bet)));
    const nd0 = odds.length > 1 ? `${odds[0]}–${odds[odds.length - 1]}` : odds[0];
    out.push(`${k}（需要 ${nd0}%）：` + rr.map(r => { const m = r.why.match(/勝率 (\d+)%/), n = r.ev.match(/n=([\d,]+)/);
      return `${HS[r.hc[0]]} ${m ? m[1] + '%' : '樣本不足'}${n ? `（n=${n[1]}）` : ''} ${short(r.a, r)}${r.ok.length ? '≈' : ''}`; }).join('、')); });
  return out;
}
// ---------- 行動線對照表（資料：lines_data.js，表和練習用同一份）----------
const HS = {S: '兩對+', TPG: '頂對好', TPW: '頂對弱', MID: '中小對', DRAW: '強聽', WDRAW: '弱聽', AIR: '空氣'};
const HCO = ['S', 'TPG', 'TPW', 'MID', 'DRAW', 'WDRAW', 'AIR'];
const BS = {pool: '池', gto: 'GTO', gtoa: '兩人 GTO 近似', est: '池估'};
const stOf = nd => /(^|_)f_/.test(nd) ? 0 : /(^|_)t_/.test(nd) ? 1 : 2;
const hlabel = (h, nd) => stOf(nd) === 2 ? ({DRAW: '強聽未中', WDRAW: '弱聽／高張'}[h] || HS[h]) : HS[h];
// 定義（defs.js）：每個標籤都可以點開看定義
const DEF = (window.NLDEF || {d: {}, groups: []});
const dfs = t => `<span class="df" data-df="${esc(t)}" role="button" tabindex="0">${esc(t)}</span>`;
const dfl = k => String(k).split('・').map(dfs).join('・');
function defsHtml(open) {
  return `<details class="sec defs"${open ? ' open' : ''}><summary><b>定義</b>：手牌類型、牌面、尺寸、小字（也可以直接點表格上的字）</summary>` +
    DEF.groups.map(([g, ks]) => `<p class="small"><span class="lab">${esc(g)}</span></p><dl class="small">${ks.map(k => `<dt>${esc(k)}</dt><dd>${esc(DEF.d[k] || '')}</dd>`).join('')}</dl>`).join('') + '</details>';
}
function showDef(k) {
  let b = document.getElementById('dfp');
  if (!b) { b = document.createElement('div'); b.id = 'dfp'; document.body.appendChild(b); b.addEventListener('click', () => b.classList.remove('on')); }
  b.innerHTML = `<b>${esc(k)}</b>　${esc(DEF.d[k] || '（沒有定義）')}<span class="muted small">　點一下關閉</span>`; b.classList.add('on');
}
const isVs = nd => /_vs_|_over/.test(nd);
const CHO = (nd, sp) => (sp === 'mw' && isVs(nd)) ? ['f', 'c', 'r'] : /r_vs_xr/.test(nd) ? ['f', 'c'] : isVs(nd) ? ['f', 'c', 'r'] : ['x', 'small', 'big'];
const STD_SZ = [[1/3, '1/3'], [1/2, '1/2'], [3/4, '3/4'], [1, '1'], [1.5, '1.5']];
const nearestSz = p => STD_SZ.reduce((b, z) => Math.abs(z[0] - p) < Math.abs(b[0] - p) ? z : b)[1];
function potFromLab(lab) { // 從原始標籤讀底池比例；全下維持全下；「或超池」保留兩檔標準尺寸
  if (!lab) return null;
  const t = String(lab).replace(/（[^）]*）|\([^)]*\)/g, '');
  if (/全下/.test(t) && !/\d\s*%|池/.test(t.replace(/全下/g, ''))) return { allin: true };
  if (/或超池/.test(t)) return { or: ['3/4', '1.5'] };
  const FR = { '⅓': 1/3, '½': 1/2, '⅔': 2/3, '¾': 3/4 };
  for (const ch in FR) if (t.includes(ch)) return { pot: FR[ch] };
  let m = t.match(/(\d+)\s*\/\s*(\d+)/);
  if (m) return { pot: +m[1] / +m[2] };
  m = t.match(/(\d+(?:\.\d+)?)\s*%/);
  if (m) return { pot: +m[1] / 100 };
  m = t.match(/下注\s*(?:約\s*)?(\d+(?:\.\d+)?)\s*池/);
  if (m) return { pot: +m[1] };
  return null;
}
function fmtLab(lab) {
  const p = potFromLab(lab);
  if (!p) return lab;
  if (p.allin) return '全下';
  if (p.or) return '下注 ' + p.or.join('或');
  return '下注 ' + nearestSz(p.pot);
}
function rawLab(a, r) {
  if (r && r.L && r.L[a]) return r.L[a];
  const s = stOf(r ? r.nd : '');
  return {x: '過牌', f: '棄牌', c: '跟注', r: '加注'}[a] || (a === 'small' ? (s ? '下注 ½ 池' : '下注 33%') : (s ? '下注 1 池' : '下注 75%'));
}
function alab(a, r) { return fmtLab(rawLab(a, r)); }
const short = (a, r) => alab(a, r).replace('棄牌', '棄').replace('跟注', '跟').replace('過牌', '過');
const ACL = a => a === 'c' ? 'c' : a === 'f' ? 'f' : a === 'x' ? 'x' : 'b';
function nodesOf(sp) {
  const o = []; L.rows.forEach(r => { if (r.sp === sp && !o.includes(r.nd)) o.push(r.nd); });
  return o.sort((a, b) => stOf(a) - stOf(b));
}
// 表格版型照 9b695d6；標題寫成明確行動線，多條先前線就拆表。走不到的線／牌型不列。
const REACH = (window.NL2REACH && window.NL2REACH.build(L)) || { usesReach: () => false, classReached: () => true, visible: () => true };
const TITLES = (window.NL2TITLES && window.NL2TITLES.build(L)) || null;
const lineList = (sp, nd) => TITLES ? TITLES.lines(sp, nd) : [];
const nodeVisible = (sp, nd) => TITLES ? TITLES.nodeVisible(sp, nd) : (!REACH.usesReach || !REACH.usesReach(sp, nd) || REACH.visible(sp, nd));
const rowReached = (r, h, line) => TITLES ? TITLES.rowReached(r, h, line) : (!REACH.usesReach(r.sp, r.nd) || REACH.classReached(r.sp, r.nd, h, r));
function gridHtml(sp, nd, me, line) {
  const lines = line ? [line] : (lineList(sp, nd).length ? lineList(sp, nd) : [null]);
  return lines.map(ln => gridOne(sp, nd, me, ln)).join('');
}
function gridOne(sp, nd, me, line) {
  const reached = (r, h) => rowReached(r, h, line);
  const R = L.rows.filter(r => r.sp === sp && r.nd === nd), base = R.filter(r => !r.x);
  const ex = R.filter(r => r.x && (!me || r.id === me.id) && r.hc.some(h => reached(r, h)));
  const conds = [];
  base.forEach(r => { const k = r.cl || '全部'; if (!conds.includes(k)) conds.push(k); });
  const cols = HCO.filter(h => base.some(r => r.hc.includes(h) && reached(r, h)));
  const condsShown = conds.filter(k => cols.some(h => {
    const r = base.find(r => (r.cl || '全部') === k && r.hc.includes(h));
    return r && reached(r, h);
  }));
  if (!cols.length || !condsShown.length) return '';
  const cell = (k, h) => {
    const r = base.find(r => (r.cl || '全部') === k && r.hc.includes(h));
    if (!r || !reached(r, h)) return '<td class="na">—</td>';
    return `<td class="${ACL(r.a)}${me && me.id === r.id ? ' me' : ''}">${short(r.a, r)}${r.ok.length ? '≈' : ''}<small class="df" data-df="${BS[r.b]}">${BS[r.b]}</small></td>`;
  };
  let h = `<div class="tw"><table class="rt lt"><tr><th></th>${cols.map(c => `<th>${dfs(hlabel(c, nd))}</th>`).join('')}</tr>` +
    condsShown.map(k => `<tr><th class="cl">${dfl(k)}</th>${cols.map(c => cell(k, c)).join('')}</tr>`).join('') + '</table></div>';
  if (ex.length) h += `<p class="small"><span class="lab">${dfs('例外')}</span>　${ex.map(r => `<span class="${me && me.id === r.id ? 'mex' : ''}">${dfl(r.cl)}：${r.hc.filter(c => reached(r, c)).map(c => hlabel(c, r.nd)).join('、')} → <b>${short(r.a, r)}</b>${r.ok.length ? '≈' : ''}<small class="df" data-df="${BS[r.b]}">${BS[r.b]}</small></span>`).join('；')}</p>`;
  return h;
}
function faceHtml(sp, nd, line) { // 這個節點你面對什麼：例題的完整行動線（翻前＋先前各街＋這街）
  // 例題只用來顯示行動線（位置、尺寸、底池），不顯示手牌，所以同一條線的任何例題都可以
  const ex = L.rows.filter(r => r.sp === sp && r.nd === nd && r.eg && r.eg.length && (line || r.hc.some(h => rowReached(r, h, line))));
  const sig = e => e ? [e.t, e.me, e.pa, (e.pc || []).join(','), e.pretext || ''].join('|') : '';
  const cand = []; // 例題必須跟標題同一條線、同一組翻前位置
  for (const r of ex) for (const e of r.eg) if (!line || !TITLES || TITLES.lineKeyFromEg(e, stOf(nd)) === line.key) cand.push(e);
  if (line && line.eg) cand.sort((a, b) => (sig(b) === sig(line.eg)) - (sig(a) === sig(line.eg)));
  for (const r of [0]) {
    for (const e of cand) {
      if (line && line.eg && sig(e) !== sig(line.eg)) continue;
      const s = story(e); if (!s || s.length !== stOf(nd) + 2) continue; const l = s[s.length - 1];
      const face = isVs(nd) ? `你要跟 ${r1(s.facing)}bb（底池 ${s.pot}bb）` : `輪到你（底池 ${l.pot}bb）`;
      const prev = s.slice(1, -1).map(x => `${x.st}：${esc(x.txt)}`).join(' → ');
      return `<p class="small muted">你面對（例）：${esc(s[0])} → ${prev ? prev + ' → ' : ''}${l.st}${l.txt ? '：' + esc(l.txt) : ''}，${face}</p>`; } }
  return '';
}
function dataHtml(sp, nd, line) {
  return `<ul class="dl">${L.rows.filter(r => r.sp === sp && r.nd === nd && r.hc.some(h => rowReached(r, h, line))).map(r => `<li class="small">${r.x ? '例外・' : ''}${esc(r.cl || '全部')}・${r.hc.map(c => hlabel(c, r.nd)).join('、')}：<b>${esc(alab(r.a, r))}</b>${r.ok.length ? '（' + r.ok.map(a => alab(a, r)).join('、') + ' 也可以）' : ''}。${esc(r.why)}<br><span class="muted">${BS[r.b]}｜${esc(r.ev)}${r.hw ? `｜你打過 ${r.hw} 次` : ''}</span></li>`).join('')}</ul>`;
}
let LS = {sp: 'bb', data: false};
function lines() {
  window.__Q = null; const sp = LS.sp, S = L.spots.find(s => s.id === sp), cv = L.cov;
  const al = L.al[sp] || {}, aln = L.aln[sp];
  const alias = Object.keys(al).map(nd => { const [s2, n2] = al[nd].includes(':') ? al[nd].split(':') : [al[nd], nd];
    return `${esc(nodeLabel(sp, nd))} → 照「${esc(L.spots.find(s => s.id === s2).t)}」的「${esc(nodeLabel(s2, n2))}」`; });
  app.innerHTML = `<div class="sec"><b class="h">NL2 行動線對照表</b><p class="small muted">${esc(L.scope)}<br>${esc(L.bias)}${cv ? `<br>你 10/28–11/4 的 ${f0(cv.tot)} 個翻後決定，${pc(cv.cov, cv.tot)} 落在這張表（皆為直接對應；未對應的決策不計入覆蓋）。` : ''}</p>
  <p class="small">怎麼看：標題是這條線從翻前到這一街的行動，<span class="ha">金色粗體</span>是你的動作。一格＝你的動作。走不到的線、牌型不列。<b>≈</b>＝打平（另一個動作也可以）。小字＝根據：池＝玩家池數據（樣本與比較見數據）、GTO＝本機解算器（範圍、代表牌面與設定見數據）。近似＝GTO 近似（兩人 solver），把多人壓縮為最強對手分布；限制見數據。尺寸：格子只標 1/3、1/2、3/4、1、1.5 或全下（最接近的底池比例）。GTO 照解算樹靠這幾檔；池估是牌池實際下注均值再靠檔，不是精確到 1%。點「池估」可看說明。多人近似每街「下注 1/2」、加注只含全下，面對加注的答案僅適用此尺寸。牌型：頂對好＝超對或頂對 J 以上踢腳；頂對弱＝頂對 T 以下踢腳；中小對含比頂對小的口袋對；強聽＝同花聽、兩頭順；弱聽＝卡順或兩張高牌。</p>
  ${L.notes ? `<details class="small muted"><summary>依據與解算設定註解</summary>${L.notes.map((n, i) => `<p>${i + 1}. ${esc(n)}</p>`).join('')}</details>` : ''}
  <div class="chips">${L.spots.map(s => `<button class="chip${s.id === sp ? ' on' : ''}" data-sp="${s.id}">${esc(s.t.split('（')[0])}</button>`).join('')}</div>
  <button class="btn tg" data-tg="1">${LS.data ? '收起數據' : '顯示每格的數據'}</button>　<a class="btn" href="#drill">練習這張表 →</a></div>` + defsHtml(false) + `
  <div class="sec"><b class="h">${esc(S.t)}</b><span class="ev">${esc(S.sub)}</span>${cv && cv.by[sp] ? `<span class="ev">你 ${cv.by[sp][0]}/${cv.by[sp][1]} 個決定在表上</span>` : ''}</div>` +
  nodesOf(sp).filter(nd => nodeVisible(sp, nd)).flatMap(nd => {
    const use = lineList(sp, nd).length ? lineList(sp, nd) : [null];
    return use.map(ln => `<div class="sec" data-node="${sp}/${nd}"><b class="ttl">${ln ? ln.titleHtml : esc(nodeLabel(sp, nd))}</b>${faceHtml(sp, nd, ln)}${gridHtml(sp, nd, null, ln)}${LS.data ? dataHtml(sp, nd, ln) : ''}</div>`);
  }).join('') +
  (alias.length ? `<div class="sec small"><span class="lab">其他點</span>　${aln ? esc(aln) + '。' : ''}沒有自己的數據，照下面的表：<ul>${alias.map(a => `<li>${a}</li>`).join('')}</ul></div>` : '');
}
const f0 = x => Number(x).toLocaleString('en-US'), pc = (a, b) => Math.round(a / b * 1000) / 10 + '%';
// 例子 → 畫面上的行動線
const PO = ['SB', 'BB', 'UTG', 'HJ', 'CO', 'BTN'], STN = ['翻牌', '轉牌', '河牌'];
const cs2 = s => s.match(/../g) || [];
const r1 = x => Math.round(x * 10) / 10;
function story(e) {
  const me = e.me, nm = p => p === me ? `你（${p}）` : p, live = [e.pa].concat(e.pc).filter(Boolean);
  const dead = (live.includes('SB') ? 0 : 0.5) + (live.includes('BB') ? 0 : 1);
  let pre;
  if (e.pretext) pre = e.pretext;
  else if (e.t === 'SRP') pre = `${nm(e.pa)} 開池 ${r1((e.pot - dead) / live.length)}bb，${e.pc.map(nm).join('、')} 跟`;
  else if (e.t === '3BP') pre = `${nm(e.pc[0])} 開池 2.5bb，${nm(e.pa)} 3-bet 到 ${r1((e.pot - dead) / 2)}bb，${nm(e.pc[0])} 跟`;
  else if (e.t === 'ISO') pre = `${nm(e.pc[0])} limp，${nm(e.pa)} 加注到 ${r1((e.pot - dead) / 2)}bb，${nm(e.pc[0])} 跟`;
  else pre = `${e.pc.filter(p => p !== 'BB').map(nm).join('、')} limp${e.pc.includes('BB') ? '，' + nm('BB') + ' 過牌' : ''}`;
  const out = [`翻前：${pre}（底池 ${r1(e.pot)}bb）`], b = cs2(e.b), segs = e.l.split('/');
  if (b.length !== segs.length + 2) return null;
  let P = e.pot, alive = PO.filter(p => live.includes(p)); const spent = {};
  for (let s = 0; s < segs.length; s++) {
    const tk = segs[s].split(' ').filter(Boolean), con = {}, ac = [], need = new Set(); let cur = 0, idx = 0, last = s === segs.length - 1;
    const order = alive.slice();
    for (const t of tk) {
      const [p, a] = t.split(':'); if (!order.includes(p)) return null;
      const k = a[0], x = parseFloat(a.slice(1));
      if (k === 'x') ac.push(`${nm(p)} 過牌`);
      else if (k === 'f') { ac.push(`${nm(p)} 棄牌`); alive = alive.filter(q => q !== p); }
      else if (k === 'c') { ac.push(`${nm(p)} 跟 ${r1(cur)}bb`); con[p] = cur; }
      else if (k === 'b') { cur = r1(P * x); con[p] = cur; ac.push(`${nm(p)} 下注 ${Math.round(x * 100)}%（${cur}bb）`); }
      else if (k === 'a') { const to = r1(Math.max(cur, (e.stk || 100) - (spent[p] || 0))); cur = to; con[p] = to; ac.push(`${nm(p)} 全下 ${to}bb`); }
      else if (k === 'r') { const to = r1(cur * (x || 3)); cur = to; con[p] = to; ac.push(`${nm(p)} 加注到 ${to}bb`); }
      else return null;
    }
    if (!last && tk.length === 0) return null;
    if (last && !alive.includes(me)) return null;
    const pot0 = P; P = r1(P + Object.values(con).reduce((a, c) => a + c, 0)); for (const p in con) spent[p] = (spent[p] || 0) + con[p];
    const cards = s === 0 ? b.slice(0, 3) : [b[s + 2]];
    out.push({st: STN[s], cards, txt: ac.length ? ac.join('，') : '', pot: last ? pot0 : null, cur: last ? cur : 0, mine: con[me] || 0});
    if (last) { out.facing = cur - (con[me] || 0); out.pot = P; }
  }
  return out;
}
// ---------- 練習（同一份表）----------
let LQ = null, ln = 0, DF = 'all';
const FL = () => [['all', '全部']].concat(L.spots.map(s => [s.id, s.t.split('（')[0]])).concat([['riv', '河牌一對：跟或棄']]);
// 題目只用「走得到這條線」的例題：例題自己的線要顯示，而且這一列的牌型在那條線上走得到
// 例題的實際牌面若落在同牌型的例外列（例：轉牌最高張 9 以下），這題的正解是例外列的答案，不能用基本列出題
const EGRK = '23456789TJQKA';
function egCond(e, k, ln) { // 例題在第 k 街的條件值
  const b = String(e.b || ''), cs = []; for (let i = 0; i < b.length; i += 2) cs.push(b.slice(i, i + 2));
  const fl = cs.slice(0, 3), rk = c => EGRK.indexOf(c[0]), seen = cs.slice(0, 3 + k);
  const suits = new Set(fl.map(c => c[1])), ranks = fl.map(rk);
  const tx = suits.size === 1 ? 'mono' : new Set(ranks).size < 3 ? 'paired' : Math.max(...ranks) === 12 ? 'A_high' : Math.max(...ranks) >= 10 ? 'KQ_high' : Math.max(...ranks) >= 8 ? 'mid_high' : 'low';
  const hi = seen.length ? (Math.max(...seen.map(rk)) >= 8 ? 'T' : 'L') : null;
  let ct = null;
  if (k >= 1 && cs[2 + k]) {
    const pre = cs.slice(0, 2 + k), c = cs[2 + k], pr = pre.map(x => rk(x) + 2), r0 = rk(c) + 2;
    const win = rs => { const st = new Set(rs); if (st.has(14)) st.add(1); let m = 0; for (let lo = 1; lo <= 10; lo++) { let n = 0; for (let x = lo; x < lo + 5; x++) if (st.has(x)) n++; m = Math.max(m, n); } return m; };
    const w0 = win(pr), w1 = win(pr.concat([r0]));
    ct = pr.includes(r0) ? 'pair' : pre.filter(x => x[1] === c[1]).length >= 2 ? 'flush' : (w1 >= 4 && w0 < 4) ? 'str4' : (w1 >= 3 && w0 < 3) ? 'str3' : r0 > Math.max(...pr) ? 'over' : 'blank';
  }
  const seg = String(e.l || '').split('/')[k] || '', bets = seg.split(' ').filter(t => t && !t.startsWith(e.me + ':') && /:b/.test(t)).map(t => parseFloat(t.split(':b')[1]));
  const last = seg.split(' ').filter(t => t && !t.startsWith(e.me + ':') && /:[bra]/.test(t)).pop() || '';
  const sz = /:b/.test(last) ? (bets[bets.length - 1] <= 0.6 ? 'le50' : bets[bets.length - 1] <= 1.15 ? 'p75' : 'o150') : null;
  const F = (ln && ln.facts) || {};
  return { tx, hi, ct, sz, ln: F.tb ? 'tb' : 'oth', prior: [F.checkTurn && 'check_turn', F.betBet && 'bet_bet'].filter(Boolean), hr: F.pfr ? 'PFR' : 'CALL' };
}
function egInException(r, e, ln) {
  if (r.x) return false;
  const k = stOf(r.nd), v = egCond(e, k, ln);
  return L.rows.some(x => x.x && x.sp === r.sp && x.nd === r.nd && x.hc.some(h => r.hc.includes(h)) && x.a !== r.a &&
    Object.entries(x.c || {}).every(([key, want]) => key === 'prior' ? v.prior.includes(want) : (v[key] == null ? true : v[key] === want))); // 算不出的條件（全下尺寸）保守當作符合
}
// 例題的實際牌路（tools/build_drill_paths.py 用正式分類器逐街算）跟表上答案對不上的，不出題
const egPathBad = (r, e) => !window.__NL2_NO_EGPATH && !!(window.NL2_EGBAD && (window.NL2_EGBAD[r.id] || []).includes(r.eg.indexOf(e)));
const egOk = (r, e) => { if (!TITLES) return true; if (egPathBad(r, e)) return false; const ln = TITLES.titleForEg(r.sp, r.nd, e); return !!ln && r.hc.some(h => rowReached(r, h, ln)) && !egInException(r, e, ln); };
// 只列表、不出題的線：這條線走得到的格沒有完整例題手牌（HW 2026-11-11 同意保留表格、不進練習）
const TABLE_ONLY = new Set(['mw/r_vs_xr']);
const tableOnly = (sp, nd) => TABLE_ONLY.has(sp + '/' + nd);
function pool(f) {
  return L.rows.filter(r => r.eg && r.eg.length && !tableOnly(r.sp, r.nd) && nodeVisible(r.sp, r.nd) && r.hc.some(h => rowReached(r, h)) && r.eg.some(e => egOk(r, e)) && (f === 'all' || (f === 'riv' ? (/r_vs_bet/.test(r.nd) && r.sp !== 'mw' && r.hc.some(h => ['TPG', 'TPW', 'MID'].includes(h))) : r.sp === f)));
}
function newLQ(f, street) {
  const P = pool(f).filter(r => street === undefined || stOf(r.nd) === street);
  if (!P.length) return null;
  for (let t = 0; t < 200; t++) {
    const r = P[Math.floor(Math.random() * P.length)], egs = r.eg.filter(e => egOk(r, e)), e = egs[Math.floor(Math.random() * egs.length)], s = e && story(e);
    if (!s) continue;
    if (s.length !== stOf(r.nd) + 2) continue;
    if (f === 'riv' && !['TPG', 'TPW', 'MID'].some(h => r.hc.includes(h))) continue;
    const h = cs2(e.h), b = cs2(e.b);
    return {id: r.id + '#' + r.eg.indexOf(e), drill: 'nl2lines', hero: h.join(' '), board: b.join(' '), full: b.join(' '), role: e.role, row: r, e, s};
  }
  return null;
}

function drill(f, street) {
  window.__Q = null;
  DF = f || DF; const q = LQ = newLQ(DF, street);
  if (!q) { app.innerHTML = '<div class="sec">這個分類沒有題目。</div>'; return; }
  const r = q.row, e = q.e, s = q.s, h = cs2(e.h), b = cs2(e.b), sp = L.spots.find(x => x.id === r.sp);
  const lst = s[s.length - 1], vs = isVs(r.nd);
  const ask = vs ? `輪到你：要跟 ${r1(s.facing)}bb（底池 ${s.pot}bb）` : `輪到你（底池 ${lst.pot}bb）`;
  app.innerHTML = `<div class="chips">${FL().map(([k, t]) => `<button class="chip${k === DF ? ' on' : ''}" data-f="${k}">${esc(t)}</button>`).join('')}</div>
  <div id="qbox" class="sec"><p class="qs">${esc(sp.t.split('（')[0])}｜<span class="ttl">${(TITLES && TITLES.titleForEg(r.sp, r.nd, e) || {}).titleHtml || esc(nodeLabel(r.sp, r.nd))}</span>。你的牌 ${pretty(h)}，你要怎麼做？</p>
  <div class="cards">${h.map(cd).join('')}　${b.map(cd).join('')}</div>
  <p class="line">${esc(s[0])}</p>${s.slice(1).map((x, i) => `<p class="line">${x.st} ${pretty(x.cards)}：${esc(x.txt)}${i === s.length - 2 ? (x.txt ? '，' : '') + esc(ask) : ''}</p>`).join('')}
  <div class="abar">${CHO(r.nd, r.sp).map(a => `<button class="ab" data-a="${a}">${esc(alab(a, r))}${a === 'c' ? ' ' + r1(s.facing) + 'bb' : ''}</button>`).join('')}</div></div><div id="ans"></div>`;
  window.__Q = q;
  app.querySelectorAll('.ab').forEach(el => el.onclick = () => lanswer(el.dataset.a, el));
}
function lanswer(a, el) {
  const q = LQ; if (!q || q.done) return; q.done = 1; const r = q.row, good = a === r.a, alt = r.ok.includes(a);
  app.querySelectorAll('.ab').forEach(x => { if (x.dataset.a === r.a || r.ok.includes(x.dataset.a)) x.classList.add('good'); });
  el.classList.add('pick');
  const res = good ? '✓ 正確' : alt ? '✓ 也可以（打平）' : '✗ 不對';
  $('#ans').innerHTML = `<div class="sec"><p class="res ${good || alt ? 'ok' : 'no'}">${res}：${esc(alab(r.a, r))}${r.ok.length ? `（${r.ok.map(x => alab(x, r)).join('、')} 也可以）` : ''}</p><button class="nx" data-next>下一題 →</button>
  <p class="small">這手是<b>${esc(clsName(q))}</b>，表上：${esc(r.cl || '全部牌面')} → <b>${esc(alab(r.a, r))}</b>。${esc(r.why)}</p>
  <p class="small muted">${esc(L.basis[r.b])}｜${esc(r.ev)}</p>
  <p class="small"><b class="ttl">${(TITLES && TITLES.titleForEg(r.sp, r.nd, q.e) || {}).titleHtml || esc(nodeLabel(r.sp, r.nd))}</b>（框起來的是這題）</p>${gridHtml(r.sp, r.nd, r, TITLES && TITLES.titleForEg(r.sp, r.nd, q.e))}<p class="small"><a href="#lines" data-go="${r.sp}">看完整對照表</a></p></div>${defsHtml(false)}`;
}
function clsName(q) { return q.row.hc.map(h => stOf(q.row.nd) === 2 && ['DRAW', 'WDRAW'].includes(h) ? hlabel(h, q.row.nd) : L.hc[h]).join('／'); }
// ---------- 路由 ----------
const TABS = ['card', 'lines', 'drill', 'river'];
function route() { let t = (location.hash || '#card').slice(1); if (!TABS.includes(t)) t = 'card';
  document.querySelectorAll('.topb').forEach(e => e.classList.toggle('on', e.dataset.t === t));
  if (t === 'card') card(); else if (t === 'lines') lines(); else drill(t === 'river' ? 'riv' : (DF === 'riv' ? 'all' : DF)); window.scrollTo(0, 0); }
window.__QNEXT = () => drill();
app.addEventListener('click', e => {
  const t = e.target;
  const df = t.closest('[data-df]'); if (df) { showDef(df.dataset.df); return; }
  if (t.closest('[data-next]')) { drill(); return; }
  const f = t.closest('[data-f]'); if (f) { drill(f.dataset.f); return; }
  const sp = t.closest('[data-sp]'); if (sp) { LS.sp = sp.dataset.sp; lines(); return; }
  if (t.closest('[data-tg]')) { LS.data = !LS.data; lines(); return; }
  const go = t.closest('[data-go]'); if (go) LS.sp = go.dataset.go;
});
if (window.__LINES_QA) window.__linesQA = { tableOnly, egCond, egInException, egOk,
  answer: a => lanswer(a, {classList: {add() {}}}),
  render: sp => { LS.sp = sp; lines(); }, pool, card, DEF, defsHtml, drill, gridHtml, story, nodesOf, stOf, nodeVisible, rowReached, REACH, TITLES, lineList
};
window.addEventListener('hashchange', route); route();
})();
