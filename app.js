/* 撲克練習 v8 — every chart / drill / table / lesson reads window.PF (pf_data.js, built from the solver). */
(function () {
'use strict';
const PF = window.PF, N = PF.names, IX = {}; N.forEach((n, i) => IX[n] = i);
const RK = '23456789TJQKA', SEATS = ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB'];
const NC = N.map(n => n.length === 2 ? 6 : n[2] === 's' ? 4 : 12);
const $ = s => document.querySelector(s), $$ = s => Array.from(document.querySelectorAll(s));
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const f1 = x => (Math.round(x * 10) / 10).toFixed(1);
const fbb = x => { const v = Math.round(x * 100) / 100; return String(v); };
const fev = c => c == null ? '—' : (c / 100 >= 0 ? '+' : '') + (c / 100).toFixed(2);
// ---------- storage ----------
const LS = {get(k, d) { try { const v = localStorage.getItem('pk8.' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('pk8.' + k, JSON.stringify(v)); } catch (e) {} }};
let VER = LS.get('ver', 'exp'); if (VER !== 'gto' && VER !== 'exp') VER = 'exp';
// pk8.ver is stored as raw string too so solver.html (iframe) can share it
try { const raw = localStorage.getItem('pk8.ver'); if (raw === 'gto' || raw === 'exp') VER = raw; } catch (e) {}
function setVer(v) { VER = v; try { localStorage.setItem('pk8.ver', v); } catch (e) {} }
const VERZH = {exp: '穩健剝削', gto: 'GTO'};
const ST = Object.assign({cnt: 0, q: [], miss: {}, st: {}, flt: {}}, LS.get('st', {}));
const save = () => LS.set('st', ST);
// ---------- solver data helpers ----------
const ZH = {fold: '棄牌', call: '跟注', open: '開池加注', '3bet': '3-bet', '4bet': '4-bet', jam: '全下'};
const KEY = {fold: 'F', call: 'C', open: 'R', '3bet': 'R', '4bet': 'R', jam: 'R'};
const COL = {fold: '#26332b', call: '#3b78c4', open: '#2e9e5a', '3bet': '#c9483f', '4bet': '#c9483f', jam: '#8e44ad'};
function node(n) { return PF.nodes[n]; }
function cell(n, v, h) { const d = PF.nodes[n][v], i = IX[h]; return {s: d.s[i], r: d.r[i], ev: d.ev ? d.ev[i] : null, fl: d.fl[i] || null}; }
// THE grading rule (one function; chart cells, drill answers and tests all use it):
// correct = highest-frequency action, or any action the chart plays >= 25%.
function okActs(n, v, h) {
  const acts = node(n).acts, s = cell(n, v, h).s; let m = 0;
  s.forEach((x, j) => { if (x > s[m]) m = j; });
  return {main: acts[m], ok: acts.filter((a, j) => j === m || s[j] >= 25), s};
}
function judge(n, v, h, a) {
  const o = okActs(n, v, h), j = node(n).acts.indexOf(a);
  if (!o.ok.includes(a)) return 'bad';
  return (a === o.main || o.s[j] >= 50) ? 'ok' : 'mix';
}
// ---------- node descriptions ----------
function parse(n) {
  let m;
  if ((m = n.match(/^(\w+?)rfi$/))) return {fam: 'rfi', hero: m[1]};
  if ((m = n.match(/^(\w+?)open>(\w+?)3b>4b>jam$/))) return {fam: 'vsjam', hero: m[1], op: m[1], y: m[2]};
  if ((m = n.match(/^(\w+?)open>(\w+?)3b>4b$/))) return {fam: 'vs4b', hero: m[2], op: m[1], y: m[2]};
  if ((m = n.match(/^(\w+?)open>(\w+?)3b$/))) return {fam: 'vs3b', hero: m[1], op: m[1], y: m[2]};
  if ((m = n.match(/^(\w+?)open>(\w+)$/))) return {fam: m[2] === 'BB' ? 'bbdef' : m[2] === 'SB' ? 'sbdef' : 'ipdef', hero: m[2], op: m[1], y: m[2]};
  return {fam: '?', hero: '?'};
}
function between(a, b) { const i = SEATS.indexOf(a), j = SEATS.indexOf(b); return SEATS.slice(i + 1, j); }
function after(a) { return SEATS.slice(SEATS.indexOf(a) + 1); }
function sizes(p) {
  const o = node(p.op + 'rfi') ? node(p.op + 'rfi').to.open : 2.5;
  const n1 = node(p.op + 'open>' + p.y), n2 = node(p.op + 'open>' + p.y + '3b');
  return {o, t3: n1 ? n1.to['3bet'] : null, t4: n2 ? n2.to['4bet'] : null};
}
function title(n) {
  const p = parse(n);
  switch (p.fam) {
    case 'rfi': return `${p.hero} 開池（前面全部棄牌）`;
    case 'bbdef': case 'sbdef': case 'ipdef': return `${p.hero} 面對 ${p.op} 開池`;
    case 'vs3b': return `${p.hero} 開池後面對 ${p.y} 的 3-bet`;
    case 'vs4b': return `${p.hero} 3-bet 後面對 ${p.op} 的 4-bet`;
    case 'vsjam': return `${p.hero} 4-bet 後面對 ${p.y} 全下`;
  }
  return n;
}
function short(n) {
  const p = parse(n);
  if (p.fam === 'rfi') return p.hero;
  if (['bbdef', 'sbdef', 'ipdef'].includes(p.fam)) return (p.fam === 'ipdef' ? p.hero + ' ' : '') + 'vs ' + p.op;
  return p.op + ' vs ' + p.y;
}
function ctx(n) {
  const p = parse(n), m = node(n), z = sizes(p), pot = `底池 <b>${fbb(m.pot)}bb</b>`;
  const call = `跟注要再補 <b>${fbb(m.tocall)}bb</b>`;
  switch (p.fam) {
    case 'rfi': return `你在 <b>${p.hero}</b>，前面全部棄牌。` + (p.hero === 'SB' ? '只剩 BB。' : `後面還有 ${after(p.hero).join('、')}。`) + `開池尺寸 ${fbb(m.to.open)}bb。`;
    case 'bbdef': case 'sbdef': case 'ipdef': { const bw = between(p.op, p.hero);
      return `<b>${p.op}</b> 開到 <b>${fbb(z.o)}bb</b>${bw.length ? '，' + bw.join('、') + ' 棄牌' : ''}。你在 <b>${p.hero}</b>` + (p.hero === 'BB' ? '' : `，後面還有 ${after(p.hero).join('、')}`) + `。${pot}，${call}。`; }
    case 'vs3b': return `你在 <b>${p.op}</b> 開到 ${fbb(z.o)}bb，<b>${p.y} 3-bet 到 ${fbb(z.t3)}bb</b>，其他人棄牌。${pot}，${call}。`;
    case 'vs4b': return `<b>${p.op}</b> 開到 ${fbb(z.o)}bb，你在 <b>${p.y}</b> 3-bet 到 ${fbb(z.t3)}bb，<b>${p.op} 4-bet 到 ${fbb(z.t4)}bb</b>。${pot}，${call}。`;
    case 'vsjam': return `你在 <b>${p.op}</b> 開池，${p.y} 3-bet 到 ${fbb(z.t3)}bb，你 4-bet 到 ${fbb(z.t4)}bb，<b>${p.y} 全下 100bb</b>。${pot}，${call}。`;
  }
  return '';
}
function actLabel(n, a) {
  const m = node(n);
  if (a === 'fold') return '棄牌';
  if (a === 'call') return `跟注（補 ${fbb(m.tocall)}bb）`;
  if (a === 'open') return `加注到 ${fbb(m.to.open)}bb`;
  if (a === 'jam') return '全下 100bb';
  return `${ZH[a]} 到 ${fbb(m.to[a])}bb`;
}
function actShort(a) { return a === 'open' ? '加注' : ZH[a]; }
// ---------- drills ----------
const ALL = Object.keys(PF.nodes);
const byFam = f => ALL.filter(n => parse(n).fam === f);
const DRILLS = [
  {id: 'bb-utg', g: 'BB 防守', name: 'BB 對 UTG', nodes: ['UTGopen>BB']},
  {id: 'bb-hj', g: 'BB 防守', name: 'BB 對 HJ', nodes: ['HJopen>BB']},
  {id: 'bb-co', g: 'BB 防守', name: 'BB 對 CO', nodes: ['COopen>BB']},
  {id: 'bb-btn', g: 'BB 防守', name: 'BB 對 BTN', nodes: ['BTNopen>BB']},
  {id: 'bb-sb', g: 'BB 防守', name: 'BB 對 SB', nodes: ['SBopen>BB']},
  {id: 'rfi-utg', g: '開池', name: 'UTG 開池', nodes: ['UTGrfi']},
  {id: 'rfi-hj', g: '開池', name: 'HJ 開池', nodes: ['HJrfi']},
  {id: 'rfi-co', g: '開池', name: 'CO 開池', nodes: ['COrfi']},
  {id: 'btn', g: '開池', name: 'BTN 開池', nodes: ['BTNrfi']},
  {id: 'rfi-sb', g: '開池', name: 'SB 開池', nodes: ['SBrfi']},
  {id: 'open', g: '開池', name: '開池混練', nodes: byFam('rfi')},
  {id: 'sb', g: '面對開池', name: 'SB 面對開池', nodes: byFam('sbdef')},
  {id: '3bet', g: '面對開池', name: '有位置面對開池', nodes: byFam('ipdef')},
  {id: 'vs3b', g: '3-bet 之後', name: '開池後面對 3-bet', nodes: byFam('vs3b')},
  {id: 'vs4b', g: '3-bet 之後', name: '面對 4-bet／全下', nodes: byFam('vs4b').concat(byFam('vsjam'))},
  {id: 'mix', g: '綜合', name: '翻前全部混練', nodes: ALL},
  {id: 'real', g: '綜合', name: '我的實戰手牌', nodes: []}
];
const DR = {}; DRILLS.forEach(d => DR[d.id] = d);
const FAMW = {bbdef: 3, rfi: 2, sbdef: 1.2, ipdef: 1.2, vs3b: 1, vs4b: 0.5, vsjam: 0.4};
// real hands from the 10/29 session (preflop only; postflop / limp / cash-out questions were deleted in v8)
const REAL = [
  {id: 'HD3112537453', n: 'SBopen>BB', c: ['Jd', 'Ts'], you: 'fold', note: '實戰 SB 開 2bb；解算器的 SB 開池是 3bb。'},
  {id: 'HD3112503075', n: 'COopen>BB', c: ['Ad', '6c'], you: 'fold'},
  {id: 'HD3112297836', n: 'BTNopen>BB', c: ['Tc', '9h'], you: 'fold'},
  {id: 'HD3112500262', n: 'COopen>BB', c: ['9s', '8h'], you: 'fold', note: '實戰 CO 開 2bb（更小，更該防守）；解算器用 2.5bb。'},
  {id: 'HD3112497897', n: 'HJopen>SB', c: ['Ks', 'Qh'], you: 'fold', note: '實戰 HJ 開 2bb；解算器用 2.5bb。'},
  {id: 'HD3112538067', n: 'BTNopen>SB', c: ['Jh', '8h'], you: 'call'},
  {id: 'HD3112261094', n: 'COrfi', c: ['4s', '4c'], you: 'fold'},
  {id: 'HD3112500958', n: 'COrfi', c: ['Ad', '6d'], you: 'fold'},
  {id: 'HD3112243181', n: 'BTNrfi', c: ['Kh', '6h'], you: 'fold'},
  {id: 'HD3112474230', n: 'BTNrfi', c: ['Qd', '6d'], you: 'fold'},
  {id: 'HD3112498023', n: 'BTNrfi', c: ['Ks', '9c'], you: 'fold'},
  {id: 'HD3112499491', n: 'COopen>BTN', c: ['Ah', '4h'], you: 'call', note: '實戰 CO 開 2bb；解算器用 2.5bb。'},
  {id: 'HD3112475126', n: 'UTGopen>BTN', c: ['Kh', 'Js'], you: 'call'}
];
REAL.forEach(r => { r.h = classOf(r.c[0], r.c[1]); });
function classOf(a, b) { let x = RK.indexOf(a[0]), y = RK.indexOf(b[0]); const s = a[1] === b[1]; if (x < y) [x, y] = [y, x]; return x === y ? RK[x] + RK[x] : RK[x] + RK[y] + (s ? 's' : 'o'); }
function randCards(h) {
  const S = 'shdc', r = () => S[Math.floor(Math.random() * 4)];
  let a = r(), b = r();
  if (h.length === 2 || h[2] === 'o') while (b === a) b = r(); else b = a;
  return [h[0] + a, h[1] + b];
}
function gridName(i, j) { const a = 12 - i, b = 12 - j; return a === b ? RK[a] + RK[a] : a > b ? RK[a] + RK[b] + 's' : RK[b] + RK[a] + 'o'; }
const GRID = []; for (let i = 0; i < 13; i++) for (let j = 0; j < 13; j++) GRID.push(gridName(i, j));
const POS = {}; GRID.forEach((h, k) => POS[h] = [Math.floor(k / 13), k % 13]);
function neighbours(h) { const [i, j] = POS[h], out = []; [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([a, b]) => { const x = i + a, y = j + b; if (x >= 0 && x < 13 && y >= 0 && y < 13) out.push(GRID[x * 13 + y]); }); return out; }
function drillNodes(d) {
  if (d.id === 'real') return [...new Set(REAL.map(r => r.n))];
  const f = ST.flt[d.id]; return (f && d.nodes.includes(f)) ? [f] : d.nodes;
}
function eligible(n, v, h) { return cell(n, v, h).r >= 25; }
function handWeight(n, v, h) {
  const c = cell(n, v, h); if (c.r < 25) return 0;
  const o = okActs(n, v, h), mx = Math.max(...c.s);
  const border = neighbours(h).some(x => cell(n, v, x).r >= 5 && okActs(n, v, x).main !== o.main);
  let w = NC[IX[h]] * c.r / 100 * (0.25 + 3 * (1 - mx / 100) + (border ? 1.5 : 0) + (c.fl ? 0.5 : 0));
  const miss = ST.miss[n + '|' + h] || 0; return w * Math.min(7, 1 + 2 * miss);
}
function pick(arr, wf) { let t = 0; const ws = arr.map(x => { const w = Math.max(0, wf(x)); t += w; return w; }); if (t <= 0) return null; let r = Math.random() * t; for (let i = 0; i < arr.length; i++) { r -= ws[i]; if (r <= 0 && ws[i] > 0) return arr[i]; } return arr[arr.length - 1]; }
// ---------- state ----------
let PAGE = 'bb-btn', Q = null, ANS = null, SES = {n: 0, ok: 0}, LASTDRILL = LS.get('last', 'bb-btn'), REALI = 0;
function nextQ() {
  const d = DR[PAGE]; ANS = null; const nodes = drillNodes(d);
  let q = null;
  if (d.id === 'real') { const r = REAL[REALI % REAL.length]; REALI++; q = {d: d.id, n: r.n, h: r.h, c: r.c, real: r}; }
  else {
    const due = ST.q.findIndex(x => x.due <= ST.cnt && nodes.includes(x.n) && eligible(x.n, VER, x.h) && !(Q && Q.n === x.n && Q.h === x.h));
    if (due >= 0) { const it = ST.q.splice(due, 1)[0]; q = {d: d.id, n: it.n, h: it.h, c: randCards(it.h), review: it.stage || 1}; save(); }
    else {
      const n = pick(nodes, x => (d.id === 'mix' || d.nodes.length > 1 ? (FAMW[parse(x).fam] || 1) : 1) * (N.some(h => eligible(x, VER, h)) ? 1 : 0));
      const h = pick(N, x => (Q && Q.h === x && Q.n === n) ? 0 : handWeight(n, VER, x));
      q = {d: d.id, n, h, c: randCards(h)};
    }
  }
  Q = q; renderDrill();
}
function answer(a) {
  if (!Q || ANS) return; if (!node(Q.n).acts.includes(a)) return;
  const res = judge(Q.n, VER, Q.h, a), good = res !== 'bad', k = Q.n + '|' + Q.h;
  ANS = {a, res, ver: VER}; SES.n++; if (good) SES.ok++; ST.cnt++;
  const s = ST.st[Q.d] = ST.st[Q.d] || {n: 0, ok: 0}; s.n++; if (good) s.ok++;
  if (Q.d !== 'real') {
    if (!good) { ST.miss[k] = Math.min(5, (ST.miss[k] || 0) + 1); ST.q = ST.q.filter(x => !(x.n === Q.n && x.h === Q.h)); ST.q.push({n: Q.n, h: Q.h, due: ST.cnt + 3, stage: 1}); }
    else if (Q.review === 1) { ST.q.push({n: Q.n, h: Q.h, due: ST.cnt + 8, stage: 2}); ST.miss[k] = Math.max(0, (ST.miss[k] || 0) - 1); }
    else if (ST.miss[k]) { ST.miss[k] = Math.max(0, ST.miss[k] - 1); if (!ST.miss[k]) delete ST.miss[k]; }
    if (ST.q.length > 60) ST.q = ST.q.slice(-60);
  }
  save(); renderAnswer(); renderBar(); renderStat();
}
// ---------- rendering pieces ----------
const SU = {s: '♠', h: '♥', d: '♦', c: '♣'};
function cardHTML(c) { return `<span class="cd ${c[1]}">${c[0] === 'T' ? '10' : c[0]}<i>${SU[c[1]]}</i></span>`; }
function verSeg() { return `<div class="seg ver" role="group" aria-label="版本"><button class="segb ${VER === 'exp' ? 'on' : ''}" data-ver="exp">穩健剝削</button><button class="segb ${VER === 'gto' ? 'on' : ''}" data-ver="gto">GTO</button></div>`; }
function gridHTML(n, v, hl) {
  const acts = node(n).acts; let h = '<div class="grid">';
  GRID.forEach(nm => {
    const c = cell(n, v, nm), o = okActs(n, v, nm);
    const segs = c.r < 5 ? '' : acts.map((a, j) => c.s[j] ? `<i style="width:${c.s[j]}%;background:${COL[a]}"></i>` : '').join('');
    const cls = ['gc', c.r < 5 ? 'out' : c.r < 50 ? 'low' : '', nm === hl ? 'hl' : '', c.fl ? 'f-' + c.fl[0] : ''].join(' ');
    h += `<button class="${cls}" data-h="${nm}" data-main="${o.main}" data-ok="${o.ok.join(',')}" data-r="${c.r}"><span class="bars">${segs}</span><b>${nm}</b>${c.fl ? `<em>${c.fl[0] === 'mix' ? '≈' : '*'}</em>` : ''}</button>`;
  });
  return h + '</div>';
}
function legendHTML(n, v) {
  const m = node(n), f = m[v].freq;
  return `<div class="legend">${m.acts.map(a => `<span><i style="background:${COL[a]}"></i>${actShort(a)} ${f1(f[a])}%</span>`).join('')}<span class="muted">≈ 平滑成混合　* EV 修正　淡＝少到達</span></div>`;
}
function freqLine(n, v) { const m = node(n), f = m[v].freq; return m.acts.map(a => `${actShort(a)} ${f1(f[a])}%`).join('・') + (m.acts.includes('call') ? `（繼續 ${f1(100 - f.fold)}%）` : ''); }
function evTable(n, v, h, chosen) {
  const m = node(n), c = cell(n, v, h), o = okActs(n, v, h);
  const best = c.ev ? Math.max(...c.ev) : null;
  return `<table class="evt"><tr><th>動作</th><th>頻率</th><th>EV（bb）</th><th>差距</th></tr>${m.acts.map((a, j) => {
    const d = c.ev ? (c.ev[j] - best) / 100 : null;
    return `<tr class="${a === chosen ? 'me' : ''} ${o.ok.includes(a) ? 'okr' : ''}"><td><i class="dot" style="background:${COL[a]}"></i>${esc(actLabel(n, a))}${a === chosen ? ' ← 你' : ''}</td><td><span class="fb"><span style="width:${c.s[j]}%;background:${COL[a]}"></span></span>${c.s[j]}%</td><td>${fev(c.ev ? c.ev[j] : null)}</td><td>${d == null ? '—' : d > -0.005 ? '最佳' : d.toFixed(2)}</td></tr>`;
  }).join('')}</table>`;
}
function flagNote(n, v, h) {
  const c = cell(n, v, h); if (!c.fl) return '';
  const acts = node(n).acts, orig = c.fl[1].map((x, j) => x ? actShort(acts[j]) + ' ' + x + '%' : '').filter(Boolean).join('、');
  if (c.fl[0] === 'mix') return `<p class="note">≈ 這格解算器原始輸出是「${orig}」。它和相鄰手牌的 EV 差不到 0.25bb，原樣顯示會在表上留下不合理的「洞」，所以平滑成和鄰格一致的頻率。題目照這張表評分。</p>`;
  return `<p class="note">* 這格解算器原始輸出是「${orig}」，但那個動作的 EV 明顯較差（沒收斂好的罕見節點），所以改成顯示 EV 最高的動作。</p>`;
}
function poolNote(n) {
  const p = parse(n), out = [];
  const add = (k, lead) => { const x = PF.pool[k]; if (!x) return; out.push(`${lead}：${Object.keys(x.t).map(a => actShort(a) + ' ' + f1(x.t[a]) + '%').join('、')}（n=${x.n.toLocaleString()}）`); };
  if (p.fam === 'rfi') { ['BB', 'SB', 'BTN', 'CO'].filter(y => after(p.hero).includes(y)).slice(0, 2).forEach(y => add(p.hero + 'open>' + y, `NL2 池的 ${y} 面對 ${p.hero} 開池`)); }
  else if (['bbdef', 'sbdef', 'ipdef'].includes(p.fam)) { add(p.op + 'rfi', `NL2 池的 ${p.op} 開池`); add(p.op + 'open>' + p.y + '3b', `池的 ${p.op} 面對 3-bet`); }
  else if (p.fam === 'vs3b') { add(p.op + 'open>' + p.y, `池的 ${p.y} 面對 ${p.op} 開池`); add(p.op + 'open>' + p.y + '3b>4b', `池的 ${p.y} 面對 4-bet`); }
  else if (p.fam === 'vs4b') add(p.op + 'open>' + p.y + '3b', `池的 ${p.op} 面對 3-bet`);
  else if (p.fam === 'vsjam') add(p.op + 'open>' + p.y + '3b>4b', `池的 ${p.y} 面對 4-bet`);
  const W = (PF.build.audit && PF.build.audit.why || {})[n];
  const lead = p.fam === 'rfi' ? '穩健剝削版開池範圍：用 9 種情境（對手比較會防守、會因你開寬而少棄牌、你翻後打得比模型差等）檢驗，只留大多數情境都賺的牌。' : '穩健剝削版：只在 NL2 池明顯偏離 GTO 的地方調整（差 5 個百分點以上，或差 2 點以上且相對差 25% 以上），其他地方對手當 GTO；而且一手牌要比照 GTO 打多賺 0.25bb 以上才改，否則照 GTO。';
  return (out.length || W) ? `<p class="muted small">${lead}${W ? '<br>' + W : ''}${out.length ? '<br>池的實際頻率：' + out.join('；') + '。' : ''}</p>` : '';
}
// ---------- page: drill ----------
function drillNav() {
  const dpk = window.__dpk; window.__dpk = false;
  let h = `<details class="dpick" ${dpk ? 'open' : ''}><summary>練習項目：<b>${DR[PAGE].g}・${DR[PAGE].name}</b><span class="muted small">（點這裡換）</span></summary><div class="dnav">`; let g = '';
  DRILLS.forEach(d => { if (d.g !== g) { if (g) h += '</div>'; g = d.g; h += `<div class="dg"><span class="dgl">${g}</span>`; } h += `<a class="chip ${d.id === PAGE ? 'on' : ''}" href="#${d.id}" data-go="${d.id}">${d.name}</a>`; });
  h += '</div></div></details>';
  const d = DR[PAGE];
  if (d.nodes.length > 1) { const f = ST.flt[d.id] || ''; h += `<div class="flt"><span class="dgl">只練</span><button class="chip sm ${!f ? 'on' : ''}" data-flt="">全部</button>${d.nodes.map(n => `<button class="chip sm ${f === n ? 'on' : ''}" data-flt="${n}">${short(n)}</button>`).join('')}</div>`; }
  return h;
}
function renderDrillShell() {
  $('#main').innerHTML = `<div class="pg">${drillNav()}<div class="row ctl">${verSeg()}<span class="stat" id="stat"></span></div><div id="qbox"></div><div id="ans"></div></div>`;
  bindCommon(); renderStat();
}
function renderStat() { const el = $('#stat'); if (!el) return; const s = ST.st[PAGE] || {n: 0, ok: 0}; el.innerHTML = `本次 <b>${SES.ok}/${SES.n}</b>・這組累計 <b>${s.n ? Math.round(100 * s.ok / s.n) : 0}%</b>（${s.n}）・待複習 <b>${ST.q.length}</b>`; }
function renderDrill() {
  const q = Q, m = node(q.n);
  const tags = [`<span class="tag">${title(q.n)}</span>`, `<span class="tag v-${VER}">${VERZH[VER]}</span>`];
  if (q.review) tags.push('<span class="tag rv">複習：上次答錯</span>');
  if (q.real) tags.push(`<span class="tag">實戰 ${q.real.id}</span>`);
  $('#qbox').innerHTML = `<div class="qcard"><div class="tags">${tags.join('')}</div><p class="ctx">${ctx(q.n)}</p>
    ${q.real && q.real.note ? `<p class="muted small">${q.real.note}</p>` : ''}
    <div class="hand">${q.c.map(cardHTML).join('')}<span class="hcls">${q.h}</span></div>
    <p class="muted small qhint">你要怎麼做？${m.acts.map(a => `<kbd>${KEY[a]}</kbd> ${actShort(a)}`).join('　')}</p></div>`;
  $('#ans').innerHTML = ''; renderBar();
}
function renderAnswer() {
  const q = Q, a = ANS.a, v = ANS.ver, o = okActs(q.n, v, q.h), m = node(q.n);
  const head = ANS.res === 'ok' ? '✓ 正確' : ANS.res === 'mix' ? '✓ 正確（混合）' : '✗ 錯誤';
  const mainTxt = o.ok.map(x => actShort(x) + ' ' + o.s[m.acts.indexOf(x)] + '%').join(' / ');
  const ov = v === 'exp' ? 'gto' : 'exp', oo = okActs(q.n, ov, q.h), oc = cell(q.n, ov, q.h);
  let h = `<div class="sec res ${ANS.res}"><div class="rh">${head}</div><div>你選 <b>${actShort(a)}</b>；${VERZH[v]}表上這手 ${q.h}：<b>${mainTxt}</b>${ANS.res === 'mix' ? '（低頻但在表內，算對）' : ''}</div></div>`;
  h += `<div class="sec">${evTable(q.n, v, q.h, a)}<p class="muted small">EV＝這手牌從發牌算起的整手結果（bb，已扣抽水），所以棄牌的 EV 就是已經投入的籌碼（例如 BB 棄牌＝−1）。頻率 ≥25% 的動作都算正確。</p>`;
  if (m.acts.includes('call')) { const need = m.tocall / (m.pot + m.tocall) * 100; h += `<p class="muted small">底池賠率：補 ${fbb(m.tocall)}bb 去贏 ${fbb(m.pot)}bb，需要約 ${f1(need)}% 勝率（還要扣抽水、考慮位置與翻後實現）。</p>`; }
  h += flagNote(q.n, v, q.h);
  h += `<p class="muted small">${VERZH[ov]}版：${oc.r < 5 ? '這手牌在那個版本不會走到這裡。' : oo.ok.map(x => actShort(x) + ' ' + oo.s[m.acts.indexOf(x)] + '%').join(' / ')}</p>`;
  if (v === 'exp') h += poolNote(q.n);
  if (q.real) h += `<p class="muted small">你當時：${actShort(q.real.you)}。</p>`;
  h += `</div><div class="sec"><div class="row sp"><b>${title(q.n)}・${VERZH[v]}</b><span class="muted small">${freqLine(q.n, v)}</span></div>${gridHTML(q.n, v, q.h)}${legendHTML(q.n, v)}<div id="cdet" class="cdet"></div></div>`;
  $('#ans').innerHTML = h; bindGrid(q.n, v);
}
function renderBar() {
  const bar = $('#abar'); if (!bar) return;
  if (!DR[PAGE] || !Q) { bar.innerHTML = ''; bar.classList.add('hide'); document.body.classList.remove('hasbar'); return; }
  bar.classList.remove('hide'); document.body.classList.add('hasbar');
  const m = node(Q.n);
  if (!ANS) {
    const order = ['fold', 'call', 'open', '3bet', '4bet', 'jam'].filter(a => m.acts.includes(a));
    bar.innerHTML = order.map(a => `<button class="ab k-${a}" data-a="${a}"><kbd>${KEY[a]}</kbd> ${esc(a === 'fold' ? '棄牌' : a === 'call' ? '跟注 ' + fbb(m.tocall) : a === 'jam' ? '全下' : actShort(a) + ' ' + fbb(m.to[a]))}</button>`).join('');
  } else {
    bar.innerHTML = `<span class="abr ${ANS.res}">${ANS.res === 'bad' ? '✗ 錯誤' : ANS.res === 'mix' ? '✓ 混合' : '✓ 正確'}</span><button class="ab nx" data-next="1">下一題 <kbd>Space</kbd></button>`;
  }
  bar.querySelectorAll('[data-a]').forEach(b => b.onclick = () => answer(b.dataset.a));
  bar.querySelectorAll('[data-next]').forEach(b => b.onclick = () => { nextQ(); window.scrollTo(0, 0); });
}
function cellDetail(n, v, h) {
  const c = cell(n, v, h);
  if (c.r < 5) return `<b>${h}</b>：這手牌在${VERZH[v]}裡幾乎不會走到這個決策（到達率 ${c.r}%）。`;
  return `<div class="row sp"><b>${h}</b><span class="muted small">到達率 ${c.r}%</span></div>${evTable(n, v, h)}${flagNote(n, v, h)}`;
}
function bindGrid(n, v) {
  $$('.grid .gc').forEach(b => b.onclick = () => { $$('.grid .gc.sel').forEach(x => x.classList.remove('sel')); b.classList.add('sel'); const d = b.closest('.sec').querySelector('.cdet'); if (d) d.innerHTML = cellDetail(n, v, b.dataset.h); });
}
// ---------- page: charts ----------
const CG = [['rfi', '開池'], ['bbdef', 'BB 防守'], ['sbdef', 'SB 面對開池'], ['ipdef', '有位置面對開池'], ['vs3b', '面對 3-bet'], ['vs4b', '面對 4-bet'], ['vsjam', '面對全下']];
const DRILL_OF = n => { const p = parse(n); if (p.fam === 'bbdef') return 'bb-' + p.op.toLowerCase(); if (p.fam === 'rfi') return p.hero === 'BTN' ? 'btn' : 'rfi-' + p.hero.toLowerCase(); return {sbdef: 'sb', ipdef: '3bet', vs3b: 'vs3b', vs4b: 'vs4b', vsjam: 'vs4b'}[p.fam]; };
function renderCharts() {
  let g = LS.get('cg', 'bbdef'); if (!CG.some(x => x[0] === g)) g = 'bbdef';
  const list = byFam(g); let n = LS.get('cn', ''); if (!list.includes(n)) n = list.includes('BTNopen>BB') ? 'BTNopen>BB' : list[0];
  const m = node(n), ov = VER === 'exp' ? 'gto' : 'exp', nfl = Object.keys(m[VER].fl).length;
  const nr = m.norake ? m.acts.map(a => `${actShort(a)} ${f1(m.norake[a])}%`).join('・') : '';
  $('#main').innerHTML = `<div class="pg"><div class="dnav"><div class="dg">${CG.map(([k, t]) => `<button class="chip ${k === g ? 'on' : ''}" data-cg="${k}">${t}</button>`).join('')}</div></div>
   <div class="flt">${list.map(x => `<button class="chip sm ${x === n ? 'on' : ''}" data-cn="${x}">${short(x)}</button>`).join('')}</div>
   <div class="row ctl">${verSeg()}<a class="btn" href="#${DRILL_OF(n)}" data-go="${DRILL_OF(n)}" data-pre="${n}">練習這個 →</a></div>
   <div class="sec"><div class="row sp"><b>${title(n)}・${VERZH[VER]}</b></div><p class="ctx small">${ctx(n)}</p>
   <p class="small"><b>${freqLine(n, VER)}</b></p>${gridHTML(n, VER, null)}${legendHTML(n, VER)}<div class="cdet" id="cdet"><span class="muted small">點任一格看頻率和每個動作的 EV。</span></div>
   <p class="muted small">對照　${VERZH[ov]}：${freqLine(n, ov)}${nr ? '　｜　GTO 無抽水：' + nr : ''}</p>
   ${nfl ? `<p class="muted small">這張表有 ${nfl} 格經過顯示修正（≈ 平滑 / * EV 修正），點格子可看原始值。</p>` : ''}${VER === 'exp' ? poolNote(n) : ''}</div></div>`;
  bindCommon(); bindGrid(n, VER);
  $$('[data-cg]').forEach(b => b.onclick = () => { LS.set('cg', b.dataset.cg); renderCharts(); });
  $$('[data-cn]').forEach(b => b.onclick = () => { LS.set('cn', b.dataset.cn); renderCharts(); });
}
// ---------- page: solver (iframe) ----------
function renderSolver() {
  const src = (window.PK_SOLVER_URL || 'solver.html') + '#riv';
  $('#main').innerHTML = `<iframe id="solverf" class="solverf" src="${src}" title="解算器"></iframe>`;
}
// ---------- page: leaks (lesson; numbers computed from PF) ----------
function F(n, v, a) { return node(n)[v].freq[a]; }
function cont(n, v) { return 100 - F(n, v, 'fold'); }
function renderLeaks() {
  const v = VER, ov = v === 'exp' ? 'gto' : 'exp';
  const row = (lbl, you, sol, go) => `<div class="lrow"><div class="ll"><b>${lbl}</b>${go ? `<a class="btn sm" href="#${go}" data-go="${go}">練習 →</a>` : ''}</div><div class="lv"><span class="muted">你</span>${you}</div><div class="lv"><span class="muted">解算器</span><b>${sol}</b></div></div>`;
  const bb = ['BTN', 'SB', 'CO'].map(x => `vs ${x} ${f1(cont(x + 'open>BB', v))}%`).join('、');
  const steal = ['CO', 'BTN', 'SB'].map(x => `${x} ${f1(F(x + 'rfi', v, 'open'))}%`).join('、');
  const b3 = `BB vs BTN ${f1(F('BTNopen>BB', v, '3bet'))}%、BTN vs CO ${f1(F('COopen>BTN', v, '3bet'))}%、SB vs BTN ${f1(F('BTNopen>SB', v, '3bet'))}%`;
  const shifts = [['BTNrfi', 'open', 'BTN 開池'], ['SBrfi', 'open', 'SB 開池'], ['BTNopen>BB3b', 'fold', 'BTN 面對 BB 3-bet 棄牌'], ['BTNopen>BB3b', '4bet', 'BTN 面對 BB 3-bet 4-bet'], ['SBopen>BB3b', 'call', 'SB 面對 BB 3-bet 跟注'], ['COopen>BB3b', '4bet', 'CO 面對 BB 3-bet 4-bet'], ['UTGopen>BB3b', 'call', 'UTG 面對 BB 3-bet 跟注'], ['BTNopen>SB', '3bet', 'SB 對 BTN 3-bet'], ['COopen>BTN', '3bet', 'BTN 對 CO 3-bet（已改回 GTO）']];
  const RVL = window.RVI || [], rv0 = RVL[0];
  const rvSec = rv0 ? `<div class="sec"><b>最新覆盤：${esc(rv0.date)}（${rv0.hands} 手）</b><p class="small">結果 ${rv0.net_bb > 0 ? '+' : ''}${rv0.net_bb}bb（${rv0.bb100 > 0 ? '+' : ''}${rv0.bb100} bb/100）${rv0.adj_bb100 != null ? `，運氣調整後約 ${rv0.adj_bb100 > 0 ? '+' : ''}${rv0.adj_bb100} bb/100` : ''}。<br>${(rv0.top || []).map(esc).join('<br>')}</p>
   <div class="row"><a class="btn" href="review/${esc(rv0.date)}.html">打開覆盤（最貴的手 ${rv0.n_costly} 題、翻前錯題 ${rv0.n_drill} 題）</a><a class="btn" href="review/index.html">全部覆盤</a></div></div>` : '';
  $('#main').innerHTML = `<div class="pg"><div class="row ctl">${verSeg()}</div>${rvSec}
  <div class="sec"><b>你的數據（938 手，10/29 匯入）對照解算器（${VERZH[v]}）</b><p class="muted small">右欄數字直接從翻前表計算，和練習題同一份資料。樣本很小，信賴區間寫在括號裡。</p>
  <div class="lt">
  ${row('BB 面對偷盲防守', '20%（12/61，12–31%）', bb, 'bb-btn')}
  ${row('SB 面對偷盲棄牌', '84%（49/58，73–92%）', `vs BTN ${f1(F('BTNopen>SB', v, 'fold'))}%、vs CO ${f1(F('COopen>SB', v, 'fold'))}%`, 'sb')}
  ${row('偷盲（CO/BTN/SB 開池）', '23%（52/229，18–29%）', steal, 'open')}
  ${row('3-bet', '4%（14/344，2–7%）', b3, '3bet')}
  ${row('面對 3-bet 棄牌', '50%（6/12，25–75%）', `BTN vs BB ${f1(F('BTNopen>BB3b', v, 'fold'))}%、CO vs BTN ${f1(F('COopen>BTN3b', v, 'fold'))}%`, 'vs3b')}
  ${row('VPIP / PFR', '18% / 14%', '—', null)}</div></div>
  <div class="sec"><b>1. BB 防守太少（最確定的漏洞）</b><p>你只防守 20%，連信賴區間上限 31% 都遠低於解算器（${bb}）。BB 已經投入 1bb，面對 BTN 2.5bb 只要補 1.5bb 去爭 4bb 的底池，大量同花牌、連張、帶 A 的牌都該跟。先把 BB 對 BTN、BB 對 SB 練到 90% 以上。</p>
   <div class="row"><a class="btn" href="#bb-btn" data-go="bb-btn">BB 對 BTN</a><a class="btn" href="#bb-sb" data-go="bb-sb">BB 對 SB</a><a class="btn" href="#bb-co" data-go="bb-co">BB 對 CO</a></div></div>
  <div class="sec"><b>2. 偷盲太少</b><p>你從 CO–SB 只開 23%；解算器：${steal}。${v === 'exp' ? 'NL2 池的盲注棄牌太多，所以穩健剝削版的 BTN、SB 開得比 GTO 寬；但比純剝削解收斂，只留各種情境都賺的牌（CO 以前反而比 GTO 略緊）。' : ''}</p><div class="row"><a class="btn" href="#btn" data-go="btn">BTN 開池</a><a class="btn" href="#rfi-sb" data-go="rfi-sb">SB 開池</a><a class="btn" href="#rfi-co" data-go="rfi-co">CO 開池</a></div></div>
  <div class="sec"><b>3. SB 面對開池棄牌太多、3-bet 太少</b><p>你在 SB 棄牌 84%；解算器 vs BTN 棄牌 ${f1(F('BTNopen>SB', v, 'fold'))}%，3-bet ${f1(F('BTNopen>SB', v, '3bet'))}%、平跟 ${f1(F('BTNopen>SB', v, 'call'))}%。</p><div class="row"><a class="btn" href="#sb" data-go="sb">SB 面對開池</a><a class="btn" href="#3bet" data-go="3bet">有位置面對開池</a></div></div>
  <div class="sec"><b>4. 面對 3-bet</b><p>你棄牌 50%（只有 12 次，樣本太小）。${v === 'exp' ? `NL2 池的 BB 對 BTN 3-bet 比 GTO 少（${f1(PF.pool['BTNopen>BB'].t['3bet'])}% vs GTO ${f1(F('BTNopen>BB', 'gto', '3bet'))}%），而且池子面對 4-bet 只棄 ${f1(PF.pool['BTNopen>BB3b>4b'].t.fold)}%（GTO 約 ${f1(F('BTNopen>BB3b>4b', 'gto', 'fold'))}%），4-bet 詐唬不划算。所以剝削版 BTN 面對 BB 3-bet 棄 ${f1(F('BTNopen>BB3b', 'exp', 'fold'))}%（GTO ${f1(F('BTNopen>BB3b', 'gto', 'fold'))}%）、4-bet ${f1(F('BTNopen>BB3b', 'exp', '4bet'))}%（GTO ${f1(F('BTNopen>BB3b', 'gto', '4bet'))}%）：A5s–A3s、KQ 這類原本 4-bet 詐唬的牌改跟注，JJ、TT 改 4-bet 拿價值。對 3-bet 稍微多棄一點，但不是大幅多棄。` : `GTO 下 BTN 面對 BB 3-bet 棄牌 ${f1(F('BTNopen>BB3b', 'gto', 'fold'))}%。`}</p><div class="row"><a class="btn" href="#vs3b" data-go="vs3b">開池後面對 3-bet</a></div></div>
  <div class="sec"><b>剝削版和 GTO 差最多的地方</b><table class="t"><tr><th>情況</th><th>GTO</th><th>剝削</th></tr>${shifts.map(([n, a, t]) => `<tr><td>${t}</td><td>${f1(F(n, 'gto', a))}%</td><td>${f1(F(n, 'exp', a))}%</td></tr>`).join('')}</table>
   <p class="muted small">模型收益（bb/100，對 NL2 池）：${Object.keys(PF.heroes).map(s => `${s} +${f1(PF.heroes[s].gain)}`).join('、')}。</p></div>
  <div class="sec"><b>實戰手牌</b><p>10/29 那場的 13 手翻前決策，已依解算器重新出題（翻後、limp、EV Cashout 題目已刪除，因為解算器沒有涵蓋）。</p><a class="btn" href="#real" data-go="real">開始練實戰手牌</a></div>
  <div class="sec"><b>翻牌面對 c-bet 棄牌 59%（10/17）</b><p class="muted">翻前解算器不含翻牌，所以這項沒有對應的翻前表；河牌防守可以到「解算器」分頁練。</p><a class="btn" href="#solver" data-go="solver">解算器</a></div></div>`;
  bindCommon();
}
// ---------- page: about ----------
function renderAbout() {
  const B = PF.build, P = PF.params, pl = Object.keys(PF.pool);
  const ns = pl.map(k => PF.pool[k].n), nmin = Math.min(...ns), nmax = Math.max(...ns);
  $('#main').innerHTML = `<div class="pg">
  <div class="sec"><b>資料從哪裡來（v8）</b><p>網站上每一張翻前表、每一題、答題後的表格和「我的弱點」數字，都來自同一份檔案 <code>pf_data.js</code>（版本 ${PF.ver}）。它由解算器輸出直接產生，沒有手寫範圍。</p>
  <ul><li><b>GTO</b>：6 人桌 100bb、NL2 抽水（5%、上限 10bb、沒有翻牌不抽），DCFR ${P.iters} 次迭代，NashConv ${P.nashconv_mbb} mbb/手；65 個決策點 × 169 手牌。</li>
  <li><b>穩健剝削</b>（練習預設）：用 ${P.hands_pool.toLocaleString()} 手 NL2 資料（${pl.length} 個節點，每節點 n=${nmin.toLocaleString()}–${nmax.toLocaleString()}）。只有池子明顯偏離 GTO 的 ${(PF.build.audit || {}).pool_material ? PF.build.audit.pool_material.length : '?'} 個節點照池的頻率（手牌組成仍照 GTO 的形狀），其他節點對手當 GTO；你的每手牌只有比照 GTO 打多賺 0.25bb 以上才改，否則照 GTO（${PF.ver} 檢查後，${Object.keys(PF.nodes).filter(k => !k.endsWith('rfi')).length} 個非開池節點裡 ${(PF.build.audit || {}).n_gto || '?'} 個完全照 GTO）。主要的剝削：池子面對 4-bet 只棄約 31%（GTO 約 63–72%）→ 少 4-bet 詐唬、多拿價值；池子面對 3-bet 棄得比 GTO 少 → 3-bet 少詐唬、多跟注。每個決策點的答案表下面都有這一格為什麼不同。</li>
  <li><b>開池範圍（穩健版，${PF.ver}）</b>：純剝削解只對「池子剛好是模型那樣」最好，會開到 BTN 60%、SB 84%。我們再用 9 種合理情境重算每手牌開池的 EV（對手防守的牌像 GTO、少棄一半、會因你開寬而調整、你翻後打折 5%，以及組合）。UTG／HJ／CO 只開至少 7 種情境都賺的牌，BTN／SB 只開 9 種都賺的牌：UTG ${f1(PF.nodes.UTGrfi.exp.freq.open)}%、HJ ${f1(PF.nodes.HJrfi.exp.freq.open)}%、CO ${f1(PF.nodes.COrfi.exp.freq.open)}%、BTN ${f1(PF.nodes.BTNrfi.exp.freq.open)}%、SB ${f1(PF.nodes.SBrfi.exp.freq.open)}%。開池題答案表的 EV 欄用其中偏悲觀的那一種情境（對手防守像 GTO、會調整、你翻後打折 5%）。如果池子真的跟模型一樣，這樣每 100 手約少賺 0.2–0.3bb；對手一調整就反過來多賺。</li>
  <li><b>尺寸</b>：開池 2.5bb（SB 3bb）；有位置 3-bet 3 倍、盲注 3-bet 4 倍（BB 對 SB 3 倍）；4-bet 2.2 倍；之後全下。</li>
  <li><b>簡化</b>：只算兩人對抗：沒有擠壓（squeeze）、多人跟注和 limp。翻後用勝率實現模型估算。</li></ul></div>
  <div class="sec"><b>評分規則（全站同一個函式）</b><p>答案＝表上頻率最高的動作；任何頻率 ≥25% 的動作也算對（顯示「正確（混合）」）。題目只從到達率 ≥25% 的手牌出，邊界牌和混合牌出現得比較多，答錯的牌約 3 題後重出、對了再約 8 題後確認一次。</p></div>
  <div class="sec"><b>顯示修正（為什麼有 ≈ 和 *）</b><ul>
  <li><b>* EV 修正</b>：某動作頻率 ≥5% 卻比最佳動作差 0.25bb 以上，或最高頻動作比最佳差 0.10bb 以上（沒收斂的罕見節點），改顯示最佳動作。GTO ${B.counts.gto.evfix} 格、剝削 ${B.counts.exp.evfix} 格。</li>
  <li><b>≈ 平滑</b>：同一條踢腳鏈（A2s→AKs…）或對子鏈上，較弱的牌繼續（不棄牌）的頻率不能比較強的牌高超過 ${B.thr_pp} 個百分點；高牌鏈上不能有比兩側都低 ${B.thr_pp} 點以上的「洞」。違反時，只在相關格子 EV 差 ≤${B.tol_bb}bb（接近無差異）時才把它們平滑成混合頻率。GTO ${B.counts.gto.mix} 格、剝削 ${B.counts.exp.mix} 格；保留未修的違規 ${B.kept} 處。</li>
  <li>修正後的頻率、整體百分比都重新計算，表和題目永遠一致。</li></ul></div>
  <div class="sec"><b>v8 刪除了什麼</b><p>舊版手寫的「簡化／非 solver」範圍表、100 條小測、100 條課程、節點卡片、尺寸題、翻後與 limp 實戰題全部移除（它們和解算器不一致，例如舊題 BB 對最小加注 K6o 的答案和表不同）。舊網址會自動導到對應的新頁。</p></div>
  <div class="sec"><b>快捷鍵</b><p>每個按鈕上的小方塊就是它的鍵（全站同一套）：<b>1–9</b> 依畫面順序選答案（也可用 <b>F</b> 棄牌／<b>C</b> 跟注・過牌／<b>R</b> 加注・下注・3-bet／<b>A</b> 全下）、<b>空白</b>或 <b>Enter</b> 下一題、<b>⌫</b> 或 <b>Esc</b> 退一步、<b>← →</b> 換分頁、<b>字母</b> 換那一排的選項（<b>⇧</b> 反向）、<b>⇧1–6</b> 主選單、<b>H</b> 或 <b>?</b> 看全部快捷鍵。手機用畫面下方的按鈕。</p><button class="btn" id="rst">清除練習紀錄</button></div></div>`;
  bindCommon(); $('#rst').onclick = () => { if (!confirm('清除所有練習紀錄？')) return; ST.cnt = 0; ST.q = []; ST.miss = {}; ST.st = {}; save(); SES = {n: 0, ok: 0}; };
}
// ---------- page: home (全站首頁：5 個大按鈕) ----------
function renderHome() {
  const H = [['index.html#prac', '翻前', '開池・防守・3-bet 練習＋範圍表'], ['postflop/index.html#prac', '翻後', '翻牌到河牌練習・河牌解算器'],
    ['learn.html#tb', '剝削', '對 NL2 池怎麼打：3-bet・Iso・行動線・讀牌'], ['learn.html#eq', '對手範圍', '他走這條線，你的牌還有多少勝率'], ['review/index.html', '覆盤', '每天的實戰手牌檢討']];
  $('#main').innerHTML = `<div class="home">${H.map(([h, t, d]) => `<a class="hb" href="${h}"><b>${t}</b><span>${d}</span></a>`).join('')}
  <div class="hm">更多：<a href="#leaks">我的弱點</a>・<a href="#real">我的實戰手牌</a>・<a href="solver.html#tool">自己解河牌</a>・<a href="#about">說明</a></div></div>`;
}
// ---------- routing ----------
const ALIAS = {size: 'open', value: 'solver', nodes: 'mix', quiz: 'mix', course: 'leaks', chak: 'about', pool: 'about', plan: 'about', river: 'solver', charts: 'preflop', prac: null};
const TOP = [['prac', '練習'], ['preflop', '範圍表'], ['leaks', '我的弱點'], ['about', '說明']];
function resolve(id) { if (id in ALIAS) id = ALIAS[id] || LASTDRILL; if (DR[id] || ['home', 'preflop', 'solver', 'leaks', 'about'].includes(id)) return id; return null; }
function go(id, push) {
  id = resolve(id) || LASTDRILL;
  if (id === 'solver') { location.replace('solver.html'); return; }
  if (window.PKNAV) PKNAV.set(id === 'home' ? 'home' : 'pre');
  PAGE = id; Q = null; ANS = null;
  document.body.dataset.page = id; document.body.classList.toggle('solverpg', id === 'solver');
  const top = DR[id] ? 'prac' : id;
  $$('#topnav .topb').forEach(b => b.classList.toggle('on', b.dataset.top === top));
  if (location.hash !== '#' + id) history.replaceState(null, '', location.pathname + location.search.replace(/([?&])p=[^&#]*&?/, '$1').replace(/[?&]$/, '') + '#' + id);
  if (DR[id]) { LASTDRILL = id; LS.set('last', id); renderDrillShell(); nextQ(); }
  else if (id === 'home') renderHome();
  else { renderBar(); if (id === 'preflop') renderCharts(); else if (id === 'solver') renderSolver(); else if (id === 'leaks') renderLeaks(); else renderAbout(); }
  if (push !== false) window.scrollTo(0, 0);
}
function bindCommon() {
  $$('#main [data-ver]').forEach(b => b.onclick = () => { setVer(b.dataset.ver); if (DR[PAGE]) { renderDrillShell(); nextQ(); } else go(PAGE, false); });
  $$('#main [data-go]').forEach(a => a.onclick = e => { e.preventDefault(); window.__dpk = e.detail === 0 && !!a.closest('details.dpick[open]'); if (a.dataset.pre) { const d = DR[a.dataset.go]; if (d && d.nodes.length > 1) { ST.flt[d.id] = a.dataset.pre; save(); } } go(a.dataset.go); });
  $$('#main [data-flt]').forEach(b => b.onclick = () => { ST.flt[PAGE] = b.dataset.flt; save(); renderDrillShell(); nextQ(); });
}
function boot() {
  $('#topnav').innerHTML = TOP.map(([k, t]) => `<button class="topb" data-top="${k}">${t}</button>`).join('');
  $$('#topnav .topb[data-top]').forEach(b => b.onclick = () => go(b.dataset.top === 'prac' ? LASTDRILL : b.dataset.top));
  document.addEventListener('keydown', e => {
    if (!DR[PAGE] || !Q || e.metaKey || e.ctrlKey || e.altKey) return; if (e.target && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
    const k = e.key.toUpperCase(), m = node(Q.n);
    if (!ANS && (k === 'F' || k === 'C' || k === 'R')) { const a = m.acts.find(x => KEY[x] === k); if (a) { e.preventDefault(); answer(a); } }
    else if (ANS && (e.key === ' ' || e.key === 'Enter')) { e.preventDefault(); nextQ(); window.scrollTo(0, 0); }
  });
  window.addEventListener('hashchange', () => { const id = location.hash.slice(1); if (id && id !== PAGE) go(id); });
  window.addEventListener('storage', e => { if (e.key === 'pk8.ver' && (e.newValue === 'gto' || e.newValue === 'exp')) VER = e.newValue; });
  const hp = location.hash.slice(1), qp = (/[?&]p=([^&#]+)/.exec(location.search) || [])[1];
  go(hp || (qp ? decodeURIComponent(qp) : '') || 'home', false);
}
// test hooks (read-only helpers + forcing a question)
window.PK = {okActs, judge, DRILLS, REAL, parse, drillNodes, cell, version: () => VER, page: () => PAGE, q: () => Q && {n: Q.n, h: Q.h, d: Q.d},
  ask(n, h) { Q = {d: PAGE, n, h, c: randCards(h)}; ANS = null; renderDrill(); }, answer, go};
boot();
})();
