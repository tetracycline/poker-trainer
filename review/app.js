/* 覆盤 — session review pages. Preflop answers read window.PF (same pf_data.js + same grading rule as the v8 trainer). */
(function () {
'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const fbb = x => String(Math.round(x * 100) / 100);
const fev = c => c == null ? '—' : (c / 100 >= 0 ? '+' : '') + (c / 100).toFixed(2);
const sg = x => (x > 0 ? '+' : '') + x;
const SU = {h: '♥', d: '♦', c: '♣', s: '♠'};
const cardHTML = c => `<span class="cd ${c[1]}">${c[0] === 'T' ? '10' : c[0]}<i>${SU[c[1]]}</i></span>`;
const LS = {get(k, d) { try { const v = localStorage.getItem('pk8.' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('pk8.' + k, JSON.stringify(v)); } catch (e) {} }};
let VER = 'exp'; try { const r = localStorage.getItem('pk8.ver'); if (r === 'gto' || r === 'exp') VER = r; } catch (e) {}
const VERZH = {exp: '穩健剝削', gto: 'GTO'};
const PAGE = document.body.dataset.page;
$('#topnav').innerHTML = PAGE === 'day' ? '<a class="topb" href="index.html" style="text-decoration:none;text-align:center">← 覆盤列表</a>' : '';
if (PAGE !== 'day') $('#topnav').style.display = 'none';

// ---------------- index page ----------------
if (PAGE === 'index') {
  const L = window.RVI || [];
  $('#app').innerHTML = `<div class="rvh">覆盤</div><p class="muted small">每場打完的檢討：結論、數據、三大弱點、最貴的手（測驗）、翻前錯題練習。最新的在最上面。</p>` +
    (L.length ? L.map(r => `<a class="rvcard" href="${esc(r.date)}.html"><div class="row sp"><b>${esc(r.date)}</b><span class="tag">${r.hands} 手</span></div>
      <div style="margin:4px 0">${esc(r.title)}</div>
      <div class="small">結果 <b>${sg(r.net_bb)}bb（${sg(r.bb100)} bb/100）</b>${r.adj_bb100 != null ? `・運氣調整後 約 ${sg(r.adj_bb100)} bb/100` : ''}</div>
      <div class="small muted">${(r.top || []).map(esc).join('<br>')}</div>
      <div class="tags" style="margin-top:6px"><span class="tag rv">最貴的手 ${r.n_costly} 題</span><span class="tag rv">翻前錯題 ${r.n_drill} 題</span></div></a>`).join('')
      : '<p>還沒有覆盤。</p>');
  return;
}

// ---------------- day page ----------------
const PF = window.PF, RV = window.RV, IX = {}; PF.names.forEach((n, i) => IX[n] = i);
const SEATS = ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB'];
const ZH = {fold: '棄牌', call: '跟注', open: '開池加注', '3bet': '3-bet', '4bet': '4-bet', jam: '全下'};
const COL = {fold: '#26332b', call: '#3b78c4', open: '#2e9e5a', '3bet': '#c9483f', '4bet': '#c9483f', jam: '#8e44ad'};
const node = n => PF.nodes[n];
function cell(n, v, h) { const d = PF.nodes[n][v], i = IX[h]; return {s: d.s[i], ev: d.ev ? d.ev[i] : null}; }
// same grading rule as ../app.js: correct = highest-frequency action, or any action played >= 25%
function okActs(n, v, h) { const acts = node(n).acts, s = cell(n, v, h).s; let m = 0; s.forEach((x, j) => { if (x > s[m]) m = j; }); return {main: acts[m], ok: acts.filter((a, j) => j === m || s[j] >= 25), s}; }
function judge(n, v, h, a) { const o = okActs(n, v, h), j = node(n).acts.indexOf(a); if (!o.ok.includes(a)) return 'bad'; return (a === o.main || o.s[j] >= 50) ? 'ok' : 'mix'; }
function parse(n) { let m;
  if ((m = n.match(/^(\w+?)rfi$/))) return {fam: 'rfi', hero: m[1]};
  if ((m = n.match(/^(\w+?)open>(\w+?)3b>4b>jam$/))) return {fam: 'vsjam', hero: m[1], op: m[1], y: m[2]};
  if ((m = n.match(/^(\w+?)open>(\w+?)3b>4b$/))) return {fam: 'vs4b', hero: m[2], op: m[1], y: m[2]};
  if ((m = n.match(/^(\w+?)open>(\w+?)3b$/))) return {fam: 'vs3b', hero: m[1], op: m[1], y: m[2]};
  if ((m = n.match(/^(\w+?)open>(\w+)$/))) return {fam: m[2] === 'BB' ? 'bbdef' : m[2] === 'SB' ? 'sbdef' : 'ipdef', hero: m[2], op: m[1], y: m[2]};
  return {fam: '?'}; }
function title(n) { const p = parse(n);
  switch (p.fam) { case 'rfi': return `${p.hero} 開池（前面全部棄牌）`; case 'bbdef': case 'sbdef': case 'ipdef': return `${p.hero} 面對 ${p.op} 開池`;
    case 'vs3b': return `${p.hero} 開池後面對 ${p.y} 的 3-bet`; case 'vs4b': return `${p.hero} 3-bet 後面對 ${p.op} 的 4-bet`; case 'vsjam': return `${p.hero} 4-bet 後面對 ${p.y} 全下`; }
  return n; }
function actLabel(n, a) { const m = node(n);
  if (a === 'fold') return '棄牌'; if (a === 'call') return `跟注（補 ${fbb(m.tocall)}bb）`; if (a === 'open') return `加注到 ${fbb(m.to.open)}bb`; if (a === 'jam') return '全下 100bb';
  return `${ZH[a]} 到 ${fbb(m.to[a])}bb`; }
function drillOf(n) { const p = parse(n);
  if (p.fam === 'rfi') return {UTG: 'rfi-utg', HJ: 'rfi-hj', CO: 'rfi-co', BTN: 'btn', SB: 'rfi-sb'}[p.hero];
  if (p.fam === 'bbdef') return 'bb-' + p.op.toLowerCase(); if (p.fam === 'sbdef') return 'sb'; if (p.fam === 'ipdef') return '3bet';
  return p.fam === 'vs3b' ? 'vs3b' : 'vs4b'; }
function treeCtx(n) { const p = parse(n), m = node(n);
  if (p.fam === 'rfi') return `解算器樹：你在 ${p.hero} 前面全棄，開池 ${fbb(m.to.open)}bb。`;
  return `解算器樹（標準尺寸）：底池 ${fbb(m.pot)}bb，跟注要補 ${fbb(m.tocall)}bb。`; }

// ---- hand replay ----
const STZ = {pre: '翻牌前', flop: '翻牌', turn: '轉牌', river: '河牌'};
const BN = {pre: 0, flop: 3, turn: 4, river: 5};
const who = p => p === 'Hero' ? '你' : p;
function aTxt(a) { const [, , k, x, ai] = a;
  if (k === 'fold') return '棄牌'; if (k === 'check') return a[0] === 'pre' && a[1] !== 'BB' ? '補盲 1（過牌）' : '過牌';
  if (ai) return k === 'call' ? `跟注 ${fbb(x)}（全下）` : `全下 ${fbb(x)}`;
  return k === 'call' ? `跟注 ${fbb(x)}` : k === 'bet' ? `下注 ${fbb(x)}` : `加注到 ${fbb(x)}`; }
function logHTML(h, upto, reveal) {
  const end = reveal ? h.acts.length : upto; let html = '', st = null;
  for (let i = 0; i < end; i++) { const a = h.acts[i];
    if (a[0] !== st) { st = a[0]; html += `<div class="st">${STZ[st]}${BN[st] ? '　' + h.board.slice(0, BN[st]).map(cardHTML).join('') .replace(/class="cd/g, 'style="width:34px;height:46px;font-size:18px" class="cd') : ''}　<span class="muted">底池 ${fbb(h.pots[i])}bb</span></div>`; }
    html += `<span class="a ${a[1] === 'Hero' ? 'me' : ''}">${esc(who(a[1]))} ${aTxt(a)}</span>`; }
  if (!reveal) { const a = h.acts[upto];
    if (a[0] !== st) html += `<div class="st">${STZ[a[0]]}　<span class="muted">底池 ${fbb(h.pots[upto])}bb</span></div>`;
    html += `<span class="a q">你 ？</span>`; }
  return `<div class="alog">${html}</div>`; }
function boardAt(h, upto) { const st = h.acts[upto][0]; return h.board.slice(0, BN[st]); }

// ---- quiz state ----
const KEY = 'rv.' + RV.date;
const S = Object.assign({ci: 0, cans: {}, q: null, right: 0, wrong: 0, seen: 0}, LS.get(KEY, {}));
if (!Array.isArray(S.q)) S.q = RV.drill.map((_, i) => i);
const save = () => LS.set(KEY, S);
let TAB = 'costly', CUR = null; // CUR = {item, ans}

function itemHead(it) {
  const h = it.hand, up = it.at, b = boardAt(h, up);
  const tags = it.kind === 'pre'
    ? `<span class="tag v-${VER}">翻前・solver（${VERZH[VER]}）</span><span class="tag">${esc(title(it.node))}</span>`
    : `<span class="tag np">非 solver（翻後解算器未涵蓋），依原則判斷</span>`;
  return `<div class="tags">${tags}<span class="tag">${esc(h.id)}</span></div>
    <div class="hand">${h.cards.map(cardHTML).join('')}<span class="hcls">${esc(it.h || '')}</span><span class="muted">你在 <b>${h.pos}</b>・籌碼 ${h.stack}bb・${h.players.length} 人桌</span></div>
    ${b.length ? `<div class="bd">${b.map(cardHTML).join('')}</div>` : ''}
    ${logHTML(h, up, false)}
    <div class="small">輪到你：底池 <b>${fbb(h.pots[up])}bb</b>${h.tocall[up] > 0 ? `，要跟 <b>${fbb(h.tocall[up])}bb</b>` : ''}。</div>
    ${it.kind === 'pre' ? `<div class="small muted">${treeCtx(it.node)}實戰尺寸不同時，以樹上最接近的局面評分。</div>` : ''}`;
}
function optsHTML(it) {
  if (it.kind === 'pre') { const m = node(it.node); return `<div class="opts">${m.acts.map(a => `<button class="ab k-${a}" data-a="${a}">${esc(actLabel(it.node, a))}</button>`).join('')}</div>`; }
  return `<div class="opts">${it.opts.map(([k, t]) => `<button class="ab k-${k}" data-a="${k}">${esc(t)}</button>`).join('')}</div>`;
}
function grade(it, a) { return it.kind === 'pre' ? judge(it.node, VER, it.h, a) : (it.ok.includes(a) ? 'ok' : 'bad'); }
function evTable(it, a) { const n = it.node, m = node(n), c = cell(n, VER, it.h), o = okActs(n, VER, it.h), best = c.ev ? Math.max(...c.ev) : null;
  return `<table class="evt"><tr><th>動作</th><th>頻率</th><th>EV（bb）</th><th>差距</th></tr>${m.acts.map((x, j) => { const d = c.ev ? (c.ev[j] - best) / 100 : null;
    return `<tr class="${x === a ? 'me' : ''} ${o.ok.includes(x) ? 'okr' : ''}"><td><i class="dot" style="background:${COL[x]}"></i>${esc(actLabel(n, x))}${x === a ? ' ← 你選' : ''}${x === it.you ? ' ・實戰' : ''}</td><td><span class="fb"><span style="width:${c.s[j]}%;background:${COL[x]}"></span></span>${c.s[j]}%</td><td>${fev(c.ev ? c.ev[j] : null)}</td><td>${d == null ? '—' : d > -0.005 ? '最佳' : d.toFixed(2)}</td></tr>`; }).join('')}</table>`; }
function revealHTML(it, a) {
  const r = grade(it, a), h = it.hand, lbl = x => it.kind === 'pre' ? ZH[x] : (it.opts.find(o => o[0] === x) || [x, x])[1];
  let ans, why = it.why || '';
  if (it.kind === 'pre') { const o = okActs(it.node, VER, it.h);
    ans = `${VERZH[VER]}：<b>${o.ok.map(x => ZH[x]).join(' 或 ')}</b>（主要 ${ZH[o.main]}）`;
    if (!why) why = `${it.h} 在「${title(it.node)}」：${VERZH[VER]}主要 ${ZH[o.main]}。`;
    if (o.ok.includes(it.you)) why += `　<span class="muted">註：照 ${VERZH[VER]} 你實戰的 ${ZH[it.you]} 也算對（這題是依剝削版挑的）。</span>`;
  } else ans = `建議：<b>${it.ok.map(lbl).join(' 或 ')}</b>`;
  const sd = Object.entries(h.shows || {}).filter(([p]) => p !== 'Hero').map(([p, c]) => `${esc(p)} 亮 ${c.map(cardHTML).join('')}`).join('　');
  return `<div class="res ${r}"><div class="rh">${r === 'bad' ? '✗ 不對' : r === 'mix' ? '✓ 混合（可以）' : '✓ 正確'}</div>
    <div>你選：${esc(lbl(a))}　｜　你實戰：<b>${esc(lbl(it.you))}</b>${it.loss ? `（比最佳少約 ${it.loss}bb）` : ''}</div>
    <div>${ans}</div><div class="small" style="margin-top:6px">${why}</div></div>
    ${it.kind === 'pre' ? evTable(it, a) + `<div style="margin-top:6px"><a class="chip sm" href="../index.html#${drillOf(it.node)}">到翻前練習：${esc(title(it.node))} →</a></div>` : ''}
    <details style="margin-top:8px"><summary>這手後來怎麼了（完整動作、亮牌、結果）</summary>
      ${h.board.length ? `<div class="bd">${h.board.map(cardHTML).join('')}</div>` : ''}${logHTML(h, 0, true)}
      ${sd ? `<div class="small">攤牌：${sd}</div>` : ''}<div class="small">你這手：<b>${sg(h.net)}bb</b></div></details>`;
}
function render() {
  const nC = RV.costly.length, nD = RV.drill.length;
  let body = '';
  if (TAB === 'costly') {
    const i = Math.min(S.ci, nC - 1), it = RV.costly[i], a = S.cans[i];
    body = `<div class="row sp"><span class="prog">最貴的手 第 ${i + 1} / ${nC} 題</span><span><button class="btn sm" data-nav="-1" ${i ? '' : 'disabled'}>← 上一題</button> <button class="btn sm" data-nav="1" ${i < nC - 1 ? '' : 'disabled'}>下一題 →</button></span></div>
      <div class="qcard" id="qc">${itemHead(it)}${a ? revealHTML(it, a) + '<button class="btn sm" data-redo="1" style="margin-top:8px">重答這題</button>' : optsHTML(it)}</div>`;
    CUR = {it, mode: 'costly', i};
  } else {
    if (!S.q.length) { body = `<div class="qcard"><div class="rh big">全部答對 🎉</div><p>答對 ${S.right}、答錯 ${S.wrong}（答錯的題會排回後面再考）。</p><button class="btn" data-reset="1">重新開始</button></div>`; CUR = null; }
    else { const k = S.q[0], it = RV.drill[k];
      body = `<div class="row sp"><span class="prog">剩 ${S.q.length} / ${nD} 題・答對 ${S.right}・答錯 ${S.wrong}</span><button class="btn sm" data-reset="1">重來</button></div>
        <div class="qcard" id="qc">${itemHead(it)}${CUR && CUR.mode === 'drill' && CUR.k === k && CUR.a ? revealHTML(it, CUR.a) + '<button class="btn" data-dnext="1" style="margin-top:8px">下一題 →</button>' : optsHTML(it)}</div>`;
      if (!(CUR && CUR.mode === 'drill' && CUR.k === k)) CUR = {it, mode: 'drill', k}; }
  }
  $('#quiz').innerHTML = `<div class="row ctl"><span class="seg"><button class="segb ${TAB === 'costly' ? 'on' : ''}" data-tab="costly">最貴的手（${nC}）</button><button class="segb ${TAB === 'drill' ? 'on' : ''}" data-tab="drill">翻前錯題練習（${nD}）</button></span></div>` + body;
}
function answer(a) {
  if (!CUR) return;
  if (CUR.mode === 'costly') { S.cans[CUR.i] = a; save(); render(); return; }
  if (CUR.a) return; CUR.a = a; CUR.r = grade(CUR.it, a); S.seen++;
  if (CUR.r === 'bad') S.wrong++; else S.right++;
  save(); render();
}
// spaced repetition: a wrong item goes back 3 places in the queue, a right one leaves it
function dnext() { if (!CUR || !CUR.a) return; const k = S.q.shift();
  if (CUR.r === 'bad') S.q.splice(Math.min(3, S.q.length), 0, k);
  CUR = null; save(); render(); }

const R = RV.result;
$('#app').innerHTML = `<div class="row sp"><div class="rvh">覆盤 ${esc(RV.date)}</div><div class="seg ver" role="group" aria-label="版本"><button class="segb ${VER === 'exp' ? 'on' : ''}" data-ver="exp">穩健剝削</button><button class="segb ${VER === 'gto' ? 'on' : ''}" data-ver="gto">GTO</button></div></div>
  <div class="muted small">${esc(RV.title)}・${esc(RV.session)}</div>
  <div class="sec"><b>結論</b><div class="kpi" style="margin:8px 0">
    <div><span class="muted">實際結果</span><b>${sg(R.net_bb)}bb</b><span class="muted">${sg(R.bb100)} bb/100（±${R.se_bb100}）</span></div>
    <div><span class="muted">運氣調整後</span><b>約 ${sg(R.adj_bb100)} bb/100</b><span class="muted">全下運氣約 ${sg(R.luck_bb)}bb</span></div>
    <div><span class="muted">翻前可量化損失</span><b>−${RV.loss_total}bb</b><span class="muted">${RV.n_decisions} 個翻前決定、錯 ${RV.n_bad} 個</span></div></div>
    <ul>${RV.conclusion.map(x => `<li>${x}</li>`).join('')}</ul></div>
  <div class="sec"><b>數據 vs 目標</b><div class="tw"><table class="t st" style="margin-top:6px"><tr><th>項目</th><th>今天</th><th>累計</th><th>目標</th></tr>
    ${RV.stats.map(r => `<tr><td>${esc(r[0])}</td><td class="${r[4] || ''}">${esc(r[1])}</td><td>${esc(r[2])}</td><td>${esc(r[3])}</td></tr>`).join('')}</table></div>
    <div class="small muted" style="margin-top:6px">${esc(RV.stats_note)}</div></div>
  <div class="sec"><b>三大弱點與修正</b>${RV.leaks.map(l => `<div style="margin-top:10px"><b>${esc(l.t)}</b><div class="small">${esc(l.p)}</div><div class="note" style="margin-top:4px">修正：${esc(l.fix)}</div>
    <div class="tags" style="margin-top:6px">${l.go.map(([d, t]) => `<a class="chip sm" href="../index.html#${esc(d)}">練：${esc(t)} →</a>`).join('')}</div></div>`).join('')}</div>
  <div class="sec"><b>翻後</b><ul>${RV.post_notes.map(x => `<li class="small">${x}</li>`).join('')}</ul></div>
  <div class="sec" id="quizsec"><b>測驗</b><div class="small muted">先看到你當時的位置、手牌和動作，選完才揭曉你實戰怎麼打、solver／剝削答案和原因。翻前用跟翻前練習一樣的評分（最高頻率或 ≥25% 都算對）；錯題練習答錯會排回去再考。</div><div id="quiz"></div></div>`;
render();
document.addEventListener('click', e => {
  const t = e.target.closest('button'); if (!t) return;
  if (t.dataset.ver) { VER = t.dataset.ver; try { localStorage.setItem('pk8.ver', VER); } catch (x) {} document.querySelectorAll('.ver .segb').forEach(b => b.classList.toggle('on', b.dataset.ver === VER)); render(); }
  else if (t.dataset.tab) { TAB = t.dataset.tab; CUR = null; render(); }
  else if (t.dataset.nav) { S.ci = Math.max(0, Math.min(RV.costly.length - 1, S.ci + +t.dataset.nav)); save(); render(); }
  else if (t.dataset.a) answer(t.dataset.a);
  else if (t.dataset.dnext) dnext();
  else if (t.dataset.redo) { delete S.cans[S.ci]; save(); render(); }
  else if (t.dataset.reset) { if (TAB === 'drill') { S.q = RV.drill.map((_, i) => i); S.right = S.wrong = S.seen = 0; } CUR = null; save(); render(); }
});
})();
