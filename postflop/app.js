/* 撲克練習・翻後 pf1 — every drill / chart reads data/*.json built from the HU postflop CFR solves. */
(function () {
'use strict';
const $ = s => document.querySelector(s), $$ = s => Array.from(document.querySelectorAll(s));
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const f1 = x => (Math.round(x * 10) / 10).toFixed(1);
const fbb = c => { const v = Math.round(c) / 100; return (Math.round(v * 10) / 10).toString(); };
const fev = c => c == null ? '—' : (c >= 0 ? '+' : '') + (c / 100).toFixed(2);
const RK = '23456789TJQKA', SU = {s: '♠', h: '♥', d: '♦', c: '♣'};
const LS = {get(k, d) { try { const v = localStorage.getItem('pkpf.' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('pkpf.' + k, JSON.stringify(v)); } catch (e) {} }};
// version is shared with the preflop site (raw string in pk8.ver)
let VER = 'exp'; try { const raw = localStorage.getItem('pk8.ver'); if (raw === 'gto' || raw === 'exp') VER = raw; } catch (e) {}
function setVer(v) { VER = v; try { localStorage.setItem('pk8.ver', v); } catch (e) {} }
const VERZH = {exp: '剝削 NL2 池', gto: 'GTO'};
const ST = Object.assign({cnt: 0, q: [], miss: {}, st: {}}, LS.get('st', {}));
const save = () => LS.set('st', ST);
let IDX = null; const CACHE = new Map();
const SPZH = {BTN_BB: 'BTN 開池・BB 跟注', CO_BB: 'CO 開池・BB 跟注', SB_BB: 'SB 開池・BB 跟注', UTG_BB: 'UTG 開池・BB 跟注', HJ_BB: 'HJ 開池・BB 跟注',
  SB3_BTN: 'BTN 開池・SB 3-bet・BTN 跟注', BB3_BTN: 'BTN 開池・BB 3-bet・BTN 跟注'};
const SPSH = {BTN_BB: 'BTN vs BB', CO_BB: 'CO vs BB', SB_BB: 'SB vs BB', UTG_BB: 'UTG vs BB', HJ_BB: 'HJ vs BB', SB3_BTN: '3bet SB vs BTN', BB3_BTN: '3bet BB vs BTN'};
const SPORDER = ['BTN_BB', 'CO_BB', 'SB_BB', 'UTG_BB', 'HJ_BB', 'SB3_BTN', 'BB3_BTN'];
let CATZH = {}, CATST = {};
// ---------- cards & hands ----------
function cardHTML(c, cls) { return `<span class="cd ${c[1]} ${cls || ''}">${c[0] === 'T' ? '10' : c[0]}<i>${SU[c[1]]}</i></span>`; }
const cardTxt = c => (c[0] === 'T' ? '10' : c[0]) + SU[c[1]];
const cards = s => { const o = []; for (let i = 0; i < s.length; i += 2) o.push(s.slice(i, i + 2)); return o; };
function classOf(h) { const a = h.slice(0, 2), b = h.slice(2, 4); let x = RK.indexOf(a[0]), y = RK.indexOf(b[0]); const s = a[1] === b[1]; if (x < y) [x, y] = [y, x]; return x === y ? RK[x] + RK[x] : RK[x] + RK[y] + (s ? 's' : 'o'); }
function gridName(i, j) { const a = 12 - i, b = 12 - j; return a === b ? RK[a] + RK[a] : a > b ? RK[a] + RK[b] + 's' : RK[b] + RK[a] + 'o'; }
const GRID = []; for (let i = 0; i < 13; i++) for (let j = 0; j < 13; j++) GRID.push(gridName(i, j));
// ---------- node helpers ----------
function nh(n) { return n.h.length / 4; }
function combo(n, i) { return n.h.slice(4 * i, 4 * i + 4); }
function row(n, i) { const k = n.a.length; return n.s.slice(i * k, i * k + k); }
function evRow(n, i) { const k = n.a.length; return n.ev.slice(i * k, i * k + k); }
function hidx(n, h) { for (let i = 0; i < nh(n); i++) if (combo(n, i) === h) return i; return -1; }
const AGG = a => a[0] === 'b' || a === 'r' || a === 'a';
// THE grading rule (one function; drill answers, chart cells, combo chips and the consistency test all use it):
// correct = the combo's highest-frequency action, or any action it plays >= 25%.
function okActs(n, i) {
  const s = row(n, i); let m = 0; s.forEach((x, j) => { if (x > s[m]) m = j; });
  return {main: n.a[m], ok: n.a.filter((a, j) => j === m || s[j] >= 25), s};
}
function judge(n, i, a) {
  const o = okActs(n, i), j = n.a.indexOf(a);
  if (j < 0) return 'bad';
  if (o.ok.includes(a)) return (a === o.main || o.s[j] >= 50) ? 'ok' : 'mix';
  if (AGG(a)) { const agg = n.a.reduce((t, x, k) => t + (AGG(x) ? o.s[k] : 0), 0); if (agg >= 50) return 'size'; }
  return 'bad';
}
const GOOD = r => r === 'ok' || r === 'mix';
// ---------- betting line ----------
function spotOf(sp) { return IDX.spots[sp]; }
function seats(sp) { const s = spotOf(sp); return [s.oop, s.ip]; }
function replay(sp, line) {
  // walks the line; returns per-street descriptions + state at the end
  const S = spotOf(sp), P0 = Math.round(S.pot * 100), STK = Math.round(S.stack * 100), names = seats(sp);
  let pot = P0, contrib = 0; const streets = line.split('/').map(x => x ? x.split(' ') : []);
  const out = [];
  streets.forEach((tk, si) => {
    const b = [0, 0], d = [];
    tk.forEach((t, k) => {
      const p = k % 2, mx = Math.max(b[0], b[1]);
      if (t === 'x') d.push(`${names[p]} 過牌`);
      else if (t === 'c') { b[p] = mx; d.push(`${names[p]} 跟注`); }
      else if (t === 'f') d.push(`${names[p]} 棄牌`);
      else if (t[0] === 'b') { const pc = +t.slice(1); b[p] = Math.round(pc / 100 * pot); d.push(`${names[p]} 下注 <b>${pc}%</b>（${fbb(b[p])}bb）`); }
      else if (t === 'r') { b[p] = 3 * mx; d.push(`${names[p]} 加注到 <b>${fbb(b[p])}bb</b>`); }
      else if (t === 'a') { b[p] = STK - contrib; d.push(`${names[p]} <b>全下</b>（${fbb(b[p])}bb）`); }
    });
    out.push(d);
    if (si < streets.length - 1) { pot += b[0] + b[1]; contrib += b[0]; }
  });
  return {out, pot, contrib, STK, P0};
}
function actLabel(sp, n, a, short) {
  const r = replay(sp, n.l), mx = Math.max(n.bt[0], n.bt[1]), my = n.bt[n.p];
  if (a === 'x') return '過牌'; if (a === 'f') return '棄牌';
  if (a === 'c') return short ? '跟注' : `跟注 ${fbb(mx - my)}bb`;
  if (a[0] === 'b') { const pc = +a.slice(1); return short ? `下注 ${pc}%` : `下注 ${pc}%（${fbb(pc / 100 * n.pot)}bb）`; }
  if (a === 'r') return short ? '加注' : `加注到 ${fbb(3 * mx)}bb`;
  if (a === 'a') return short ? '全下' : `全下 ${fbb(r.STK - r.contrib)}bb`;
  return a;
}
function aggIndex(n) { return n.a.filter(AGG); }
function keyOf(n, a) {
  if (a === 'f') return 'F'; if (a === 'x' || a === 'c') return 'C'; if (a === 'a') return 'A';
  const ag = aggIndex(n).filter(x => x !== 'a'); const k = ag.indexOf(a); return k === 0 ? 'R' : String(k + 1);
}
function btnClass(n, a) { if (a === 'f' || a === 'x' || a === 'c' || a === 'a' || a === 'r') return 'k-' + a; const ag = aggIndex(n).filter(x => x !== 'a'); return 'k-b' + Math.min(3, ag.indexOf(a) + 1); }
const COLS = {f: '#26332b', x: '#3b78c4', c: '#3b78c4', a: '#8e44ad', r: '#c9483f'};
function colOf(n, a) { if (COLS[a]) return COLS[a]; const ag = aggIndex(n).filter(x => x !== 'a'); return ['#d9825b', '#c9483f', '#9e2f2a'][Math.min(2, ag.indexOf(a))]; }
const STREETZH = ['翻牌', '轉牌', '河牌'];
function streetOf(n) { return n.l.split('/').length - 1; }
function lineHTML(sp, n) {
  const r = replay(sp, n.l), bd = cards(n.b);
  return r.out.map((d, si) => {
    const bc = si === 0 ? bd.slice(0, 3).sort((x, y) => RK.indexOf(y[0]) - RK.indexOf(x[0])) : [bd[si + 2]];
    const txt = d.length ? d.join(' → ') : '<span class="muted">（輪到你先行動）</span>';
    return `<div><span class="st">${STREETZH[si]} ${bc.map(cardTxt).join('')}</span>${txt}</div>`;
  }).join('');
}
function boardHTML(n) { const bd = cards(n.b); const fl = bd.slice(0, 3).sort((x, y) => RK.indexOf(y[0]) - RK.indexOf(x[0]) || 'shdc'.indexOf(x[1]) - 'shdc'.indexOf(y[1])); bd.splice(0, 3, ...fl); return bd.map((c, k) => (k === 3 ? '<span class="bsep"></span>' : k === 4 ? '<span class="bsep"></span>' : '') + cardHTML(c, k >= 3 && k === bd.length - 1 ? 'new' : '')).join(''); }
// ---------- data ----------
let FFL = null;
function fflate() { return FFL || (FFL = new Promise((ok, no) => { const s = document.createElement('script'); s.src = 'fflate.min.js'; s.onload = () => ok(window.fflate); s.onerror = no; document.head.appendChild(s); })); }
async function gunzipJSON(r) {
  if (typeof DecompressionStream === 'function') return new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).json();
  const buf = new Uint8Array(await r.arrayBuffer()), f = await fflate(); return JSON.parse(f.strFromU8(f.gunzipSync(buf)));
}
async function loadFlop(sp, fl) {
  const k = sp + '/' + fl; if (CACHE.has(k)) return CACHE.get(k);
  const p = fetch(`data/${sp}/${fl}.json.gz`).then(r => { if (!r.ok) throw new Error('http ' + r.status); return gunzipJSON(r); });
  CACHE.set(k, p); try { return await p; } catch (e) { CACHE.delete(k); throw e; }
}
function findNode(F, v, l, b) { return (F.v[v] || []).find(n => n.l === l && n.b === b) || null; }
// ---------- drills ----------
let DRILLS = [], DR = {};
function buildDrills() {
  DRILLS = []; const cats = IDX.cats;
  const has = (sp, c) => Object.keys(spotOf(sp).qcount).some(k => k.endsWith('|' + c));
  DRILLS.push({id: 'all', g: '混練', name: '翻後全部混練', sp: null, cat: null});
  ['f_cbet', 'f_vs_cbet', 'barrel', 'vs_barrel', 'r_barrel', 'r_vs_bet'].forEach(c => DRILLS.push({id: 'all.' + c, g: '混練', name: '全部位置・' + CATZH[c], sp: null, cat: c}));
  SPORDER.filter(sp => IDX.spots[sp]).forEach(sp => {
    DRILLS.push({id: sp, g: SPSH[sp], name: '全部', sp, cat: null});
    cats.forEach(([c]) => { if (has(sp, c)) DRILLS.push({id: sp + '.' + c, g: SPSH[sp], name: CATZH[c], sp, cat: c}); });
  });
  DR = {}; DRILLS.forEach(d => DR[d.id] = d);
}
function candFlops(d) {
  const out = [];
  Object.keys(IDX.spots).forEach(sp => {
    if (d.sp && d.sp !== sp) return;
    IDX.spots[sp].flops.forEach(([fl, c]) => {
      const n = Object.keys(c).filter(k => k.startsWith(VER + '|') && (!d.cat || k === VER + '|' + d.cat)).reduce((t, k) => t + c[k], 0);
      if (n) out.push({sp, fl, w: d.sp ? 1 : (IDX.spots[sp].kind === 'SRP' ? 1 : 0.6) * (sp === 'BTN_BB' ? 1.5 : 1) / IDX.spots[sp].flops.length});
    });
  });
  return out;
}
function pick(arr, wf) { let t = 0; const ws = arr.map(x => { const w = Math.max(0, wf(x)); t += w; return w; }); if (t <= 0) return null; let r = Math.random() * t; for (let i = 0; i < arr.length; i++) { r -= ws[i]; if (r <= 0 && ws[i] > 0) return arr[i]; } return arr[arr.length - 1]; }
const qkey = (sp, fl, l, b, h) => [sp, fl, l, b, h].join('|');
const MIN_PR_Q = 0.002;
function unrel(n, i) { if (!n.u && !n.uc) return false; if (!n._u) n._u = new Set([...(n.u || []), ...(n.uc || [])]); return n._u.has(i); }
function conflict(n, i) { return !!(n.uc && n.uc.includes(i)); }
// hero hand must be in the CURRENT preflop range (pf_data v8-1031x); solves used older ranges -> per-class multiplier, 0 = no longer reaches here
function pfa(sp, n, i) { const t = IDX && IDX.pfadj && IDX.pfadj[sp + '|' + VER + '|' + n.p]; if (!t) return 1; if (!IDX._pfi) { IDX._pfi = {}; IDX.pfnames.forEach((x, k) => IDX._pfi[x] = k); } return t[IDX._pfi[classOf(combo(n, i))]]; }
function handWeight(n, i, mk) {
  const w = n.w[i]; if (w < 10 || unrel(n, i)) return 0;
  const s = row(n, i), mx = Math.max(...s);
  const miss = ST.miss[mk(i)] || 0;
  return w * (0.3 + 3 * (1 - mx / 100)) * Math.min(7, 1 + 2 * miss);
}
let PAGE = 'all', Q = null, ANS = null, SES = {n: 0, ok: 0}, LASTDRILL = LS.get('last', 'all'), BUSY = false;
let GEN = 0;
async function nextQ() {
  const g = ++GEN, stale = () => g !== GEN || !$('#qbox');  // newer navigation wins; never write into a page that is gone
  try {
    const d = DR[PAGE], prev = Q; Q = null; ANS = null; let q = null; renderBar();  // no answering a stale question while the next one loads
    // due reviews first
    const di = ST.q.findIndex(x => x.due <= ST.cnt && (!d.sp || d.sp === x.sp) && (!d.cat || d.cat === x.c) && !(prev && prev.key === x.key));
    if (di >= 0) {
      const it = ST.q.splice(di, 1)[0]; save();
      try { const F = await loadFlop(it.sp, it.fl), n = findNode(F, VER, it.l, it.b), i = n ? hidx(n, it.h) : -1; if (n && i >= 0 && n.w[i] >= 5 && !unrel(n, i) && pfa(it.sp, n, i) > 0) q = {sp: it.sp, fl: it.fl, F, n, i, review: it.stage || 1}; } catch (e) {}
    }
    for (let tries = 0; !q && tries < 6; tries++) {
      const cf = pick(candFlops(d), x => x.w); if (!cf) break;
      const F = await loadFlop(cf.sp, cf.fl);
      const nodes = (F.v[VER] || []).filter(n => !d.cat || n.c === d.cat);
      const n = pick(nodes, x => (x.pr < MIN_PR_Q ? 0 : Math.sqrt(x.pr)) * (x.c === 'vs_raise' && d.cat !== 'vs_raise' ? 0.3 : 1)); if (!n) continue;
      const mk = i => qkey(cf.sp, cf.fl, n.l, n.b, combo(n, i));
      const idx = []; for (let i = 0; i < nh(n); i++) idx.push(i);
      const i = pick(idx, k => (prev && prev.n === n && prev.i === k) ? 0 : handWeight(n, k, mk) * pfa(cf.sp, n, k)); if (i == null) continue;
      q = {sp: cf.sp, fl: cf.fl, F, n, i};
    }
    if (stale()) return;
    if (!q) { $('#qbox').innerHTML = '<div class="qcard">這個項目在目前版本沒有題目。</div>'; return; }
    q.h = combo(q.n, q.i); q.key = qkey(q.sp, q.fl, q.n.l, q.n.b, q.h); Q = q; renderDrill();
  } catch (e) { if (!stale()) $('#qbox').innerHTML = `<div class="qcard">載入失敗：${esc(e.message)}</div>`; console.warn(e); }
}
function answer(a) {
  if (!Q || ANS) return; const n = Q.n; if (!n.a.includes(a)) return;
  const res = judge(n, Q.i, a), good = GOOD(res), k = Q.key;
  ANS = {a, res, ver: VER}; SES.n++; if (good) SES.ok++; ST.cnt++;
  const sk = PAGE, s = ST.st[sk] = ST.st[sk] || {n: 0, ok: 0}; s.n++; if (good) s.ok++;
  const item = {sp: Q.sp, fl: Q.fl, l: n.l, b: n.b, h: Q.h, c: n.c, key: k};
  if (!good) { ST.miss[k] = Math.min(5, (ST.miss[k] || 0) + 1); ST.q = ST.q.filter(x => x.key !== k); ST.q.push(Object.assign(item, {due: ST.cnt + 3, stage: 1})); }
  else if (Q.review === 1) { ST.q.push(Object.assign(item, {due: ST.cnt + 8, stage: 2})); ST.miss[k] = Math.max(0, (ST.miss[k] || 0) - 1); }
  else if (ST.miss[k]) { ST.miss[k] = Math.max(0, ST.miss[k] - 1); if (!ST.miss[k]) delete ST.miss[k]; }
  if (ST.q.length > 80) ST.q = ST.q.slice(-80);
  const mk = Object.keys(ST.miss); if (mk.length > 400) mk.slice(0, mk.length - 400).forEach(x => delete ST.miss[x]);
  save(); renderAnswer(); renderBar(); renderStat();
}
// ---------- rendering ----------
function verSeg() { return `<div class="seg ver" role="group" aria-label="版本"><button class="segb ${VER === 'exp' ? 'on' : ''}" data-ver="exp">剝削 NL2 池</button><button class="segb ${VER === 'gto' ? 'on' : ''}" data-ver="gto">GTO</button></div>`; }
function drillNav() {
  let h = `<details class="dpick" ${window.innerWidth >= 900 ? 'open' : ''}><summary>練習項目：<b>${DR[PAGE].g}・${DR[PAGE].name}</b><span class="muted small">（點這裡換）</span></summary><div class="dnav">`; let g = '';
  DRILLS.forEach(d => { if (d.g !== g) { if (g) h += '</div>'; g = d.g; h += `<div class="dg"><span class="dgl">${g}</span>`; } h += `<a class="chip sm ${d.id === PAGE ? 'on' : ''}" href="#${d.id}" data-go="${d.id}">${d.name}</a>`; });
  return h + '</div></div></details>';
}
function renderStat() { const el = $('#stat'); if (!el) return; const s = ST.st[PAGE] || {n: 0, ok: 0}; el.innerHTML = `本次 <b>${SES.ok}/${SES.n}</b>・這組累計 <b>${s.n ? Math.round(100 * s.ok / s.n) : 0}%</b>（${s.n}）・待複習 <b>${ST.q.length}</b>`; }
function renderDrillShell() {
  $('#main').innerHTML = `<div class="pg">${drillNav()}<div class="row ctl">${verSeg()}<span class="stat" id="stat"></span></div><div id="qbox"><div class="loading">載入中…</div></div><div id="ans"></div></div>`;
  bindCommon(); renderStat();
}
function heroDesc(sp, n) {
  const nm = seats(sp), me = nm[n.p], S = spotOf(sp), pfr = S.pfr === n.p;
  return `你是 <b>${me}</b>（${n.p === 1 ? '有位置' : '無位置'}・${pfr ? '翻前加注者' : '翻前跟注者'}）`;
}
function potLine(sp, n) { const r = replay(sp, n.l); const left = r.STK - r.contrib - n.bt[n.p]; return `底池 <b>${fbb(n.pot)}bb</b>・你剩 ${fbb(left)}bb`; }
function renderDrill() {
  const q = Q, n = q.n;
  const tags = [`<span class="tag">${SPZH[q.sp]}</span>`, `<span class="tag">${CATZH[n.c]}</span>`, `<span class="tag v-${VER}">${VERZH[VER]}</span>`];
  if (q.review) tags.push('<span class="tag rv">複習：上次答錯</span>');
  $('#qbox').innerHTML = `<div class="qcard"><div class="tags">${tags.join('')}</div>
    <p class="ctx">${heroDesc(q.sp, n)}・${spotOf(q.sp).kind === 'SRP' ? '單次加注底池' : '3-bet 底池'}・100bb</p>
    <div class="board">${boardHTML(n)}</div>
    <div class="line">${lineHTML(q.sp, n)}</div>
    <div class="pinfo">${potLine(q.sp, n)}</div>
    <div class="hand">${cards(q.h).map(c => cardHTML(c)).join('')}<span class="hcls">${classOf(q.h)}</span></div>
    <p class="muted small qhint">你要怎麼做？${n.a.map(a => `<kbd>${keyOf(n, a)}</kbd> ${actLabel(q.sp, n, a, true)}`).join('　')}</p></div>`;
  ANS = null; $('#ans').innerHTML = ''; renderBar();
}
function evTable(sp, n, i, chosen) {
  const o = okActs(n, i), ev = evRow(n, i), best = Math.max(...ev);
  return `<table class="evt"><tr><th>動作</th><th>頻率</th><th>EV（bb）</th><th>差距</th></tr>${n.a.map((a, j) => {
    const d = (ev[j] - best) / 100;
    return `<tr class="${a === chosen ? 'me' : ''} ${o.ok.includes(a) ? 'okr' : ''}"><td><i class="dot" style="background:${colOf(n, a)}"></i>${esc(actLabel(sp, n, a))}${a === chosen ? ' ← 你' : ''}</td><td><span class="fb"><span style="width:${o.s[j]}%;background:${colOf(n, a)}"></span></span>${o.s[j]}%</td><td>${fev(ev[j])}</td><td>${d > -0.005 ? '最佳' : d.toFixed(2)}</td></tr>`;
  }).join('')}</table>`;
}
function wilson(p, n) { const z = 1.96, d = 1 + z * z / n, c = (p + z * z / (2 * n)) / d, h = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return [c - h, c + h]; }
function lockTxt(L) {
  const parts = [];
  if (L.bet != null) parts.push(`下注 ${f1(100 * L.bet)}%`);
  if (L.fold != null) parts.push(`棄牌 ${f1(100 * L.fold)}%`);
  if (L.raise_ != null) parts.push(`加注 ${f1(100 * L.raise_)}%`);
  const p = L.bet != null ? L.bet : L.fold, ci = p != null && L.n ? wilson(p, L.n) : null;
  return `${parts.join('、')}（n=${(L.n || 0).toLocaleString()}${ci ? `，95% CI ${f1(100 * ci[0])}–${f1(100 * ci[1])}%` : ''}）<span class="muted">［${esc(L.src || '')}］</span>`;
}
function poolNote(sp, n) {
  if (!n.nx) return '<p class="muted small">剝削版：這個決策之後的對手節點沒有足夠的 NL2 樣本（n&lt;500），對手照均衡解應對。</p>';
  const nm = seats(sp)[1 - n.p];
  return `<div class="lk"><p class="muted small">剝削版把 ${nm} 鎖成 NL2 池實際頻率（樣本只計 HU 底池；攤牌資料有偏差，只影響牌力排序、不影響頻率）：</p><ul>${Object.keys(n.nx).map(a => `<li>你${esc(actLabel(sp, n, a, true))}之後，${nm}：${lockTxt(n.nx[a])}</li>`).join('')}</ul></div>`;
}
function classAgg(n) {
  const k = n.a.length, A = {};
  for (let i = 0; i < nh(n); i++) {
    const c = classOf(combo(n, i)), w = n.w[i]; const x = A[c] = A[c] || {w: 0, n: 0, s: new Array(k).fill(0), idx: []};
    x.w += w; x.n++; x.idx.push(i); row(n, i).forEach((v, j) => x.s[j] += v * w);
  }
  Object.values(A).forEach(x => { x.s = x.s.map(v => x.w ? v / x.w : 0); x.r = x.w / x.n; });
  return A;
}
function gridHTML(sp, n, hl) {
  const A = classAgg(n); let h = '<div class="grid">';
  GRID.forEach(nm => {
    const x = A[nm];
    const segs = !x ? '' : n.a.map((a, j) => x.s[j] > 0.5 ? `<i style="width:${x.s[j]}%;background:${colOf(n, a)}"></i>` : '').join('');
    const cls = ['gc', !x ? 'out' : x.r < 35 ? 'low' : '', nm === hl ? 'hl' : ''].join(' ');
    h += `<button class="${cls}" data-h="${nm}"><span class="bars">${segs}</span><b>${nm}</b></button>`;
  });
  return h + '</div>';
}
function legendHTML(sp, n) { return `<div class="legend">${n.a.map((a, j) => `<span><i style="background:${colOf(n, a)}"></i>${esc(actLabel(sp, n, a, true))} ${f1(n.f[j])}%</span>`).join('')}<span class="muted">格子＝該牌型各花色組合依到達率加權；淡＝少到達</span></div>`; }
function combosHTML(sp, n, cls, me) {
  const A = classAgg(n), x = A[cls];
  if (!x) return `<b>${cls}</b>：這個牌型不會走到這裡（或被公共牌擋住）。`;
  return `<div class="row sp"><b>${cls}</b><span class="muted small">${x.n} 個組合</span></div><div class="combos">${x.idx.map(i => {
    const o = okActs(n, i), h = combo(n, i);
    return `<span class="cmb ${h === me ? 'me' : ''}" data-i="${i}">${cards(h).map(cardTxt).join('')} <b>${esc(actLabel(sp, n, o.main, true))}</b> ${n.a.map((a, j) => o.s[j] ? `${o.s[j]}` : '').filter(Boolean).length > 1 ? '(' + n.a.map((a, j) => o.s[j] ? actLabel(sp, n, a, true) + ' ' + o.s[j] + '%' : '').filter(Boolean).join('/') + ')' : ''}<span class="muted"> 權重${n.w[i]}${conflict(n, i) ? '・*不同尺寸間矛盾，不出題' : unrel(n, i) ? '・*未收斂，不出題' : ''}</span></span>`;
  }).join('')}</div><p class="muted small">點組合看 EV。</p><div class="cev"></div>`;
}
function bindGrid(sp, n, me) {
  $$('#main .grid .gc').forEach(b => b.onclick = () => {
    $$('#main .grid .gc.sel').forEach(x => x.classList.remove('sel')); b.classList.add('sel');
    const d = b.closest('.sec').querySelector('.cdet'); if (!d) return; d.innerHTML = combosHTML(sp, n, b.dataset.h, me);
    d.querySelectorAll('.cmb').forEach(c => c.onclick = () => { d.querySelector('.cev').innerHTML = `<p class="small"><b>${cards(combo(n, +c.dataset.i)).map(cardTxt).join('')}</b>・勝率 ${n.eq[+c.dataset.i]}%</p>` + evTable(sp, n, +c.dataset.i); });
  });
}
function renderAnswer() {
  const q = Q, n = q.n, a = ANS.a, v = ANS.ver, o = okActs(n, q.i);
  const head = {ok: '✓ 正確', mix: '✓ 正確（混合）', size: '✗ 方向對，尺寸不對', bad: '✗ 錯誤'}[ANS.res];
  const mainTxt = o.ok.map(x => actLabel(q.sp, n, x, true) + ' ' + o.s[n.a.indexOf(x)] + '%').join(' / ');
  let h = `<div class="sec res ${ANS.res}"><div class="rh">${head}</div><div>你選 <b>${esc(actLabel(q.sp, n, a, true))}</b>；${VERZH[v]}解在這手 ${cards(q.h).map(cardTxt).join('')}：<b>${esc(mainTxt)}</b>${ANS.res === 'mix' ? '（低頻但 ≥25%，算對）' : ''}</div></div>`;
  h += `<div class="sec">${evTable(q.sp, n, q.i, a)}<p class="muted small">勝率（對手此刻範圍）${n.eq[q.i]}%。EV＝從這個決策起，這手牌最後從底池拿回的期望籌碼（bb，已扣 5% 抽水、上限 10bb；棄牌＝0）。頻率 ≥25% 的動作都算正確；下注方向對但尺寸 &lt;25% 記為錯（尺寸不對）。</p>`;
  if (n.a.includes('c')) { const call = Math.max(...n.bt) - n.bt[n.p]; h += `<p class="muted small">底池賠率：補 ${fbb(call)}bb 去贏 ${fbb(n.pot)}bb，需要約 ${f1(100 * call / (n.pot + call))}% 勝率（未扣抽水、未計之後的街）。</p>`; }
  const ov = v === 'exp' ? 'gto' : 'exp', on = findNode(q.F, ov, n.l, n.b), oi = on ? hidx(on, q.h) : -1;
  if (on && oi >= 0) { const oo = okActs(on, oi); h += `<p class="muted small">${VERZH[ov]}版：${oo.ok.map(x => actLabel(q.sp, on, x, true) + ' ' + oo.s[on.a.indexOf(x)] + '%').join(' / ')}</p>`; }
  else h += `<p class="muted small">${VERZH[ov]}版：那個版本的解不會走到這條線（尺寸或範圍不同），或這手牌不在範圍內。</p>`;
  if (v === 'exp') h += poolNote(q.sp, n);
  h += `</div><div class="sec"><div class="row sp"><b>${CATZH[n.c]}・${VERZH[v]}</b><span class="muted small">整個範圍：${n.a.map((x, j) => esc(actLabel(q.sp, n, x, true)) + ' ' + f1(n.f[j]) + '%').join('・')}</span></div>${gridHTML(q.sp, n, classOf(q.h))}${legendHTML(q.sp, n)}<div class="cdet"></div></div>`;
  $('#ans').innerHTML = h; bindGrid(q.sp, n, q.h);
  const d = $('#ans .cdet'); if (d) { d.innerHTML = combosHTML(q.sp, n, classOf(q.h), q.h); d.querySelectorAll('.cmb').forEach(c => c.onclick = () => { d.querySelector('.cev').innerHTML = `<p class="small"><b>${cards(combo(n, +c.dataset.i)).map(cardTxt).join('')}</b>・勝率 ${n.eq[+c.dataset.i]}%</p>` + evTable(q.sp, n, +c.dataset.i); }); }
}
function renderBar() {
  const bar = $('#abar'); if (!bar) return;
  if (!DR[PAGE] || !Q) { bar.innerHTML = ''; bar.classList.add('hide'); document.body.classList.remove('hasbar'); return; }
  bar.classList.remove('hide'); document.body.classList.add('hasbar');
  const n = Q.n;
  if (!ANS) {
    bar.innerHTML = n.a.map(a => { const L = actLabel(Q.sp, n, a), m = L.match(/^(.*?)(（.*）| [\d.]+bb)?$/); return `<button class="ab ${btnClass(n, a)}" data-a="${a}"><kbd>${keyOf(n, a)}</kbd> ${esc(actLabel(Q.sp, n, a, true))}${m && m[2] ? `<small>${esc(m[2].replace(/[（）]/g, ''))}</small>` : ''}</button>`; }).join('');
  } else {
    bar.innerHTML = `<span class="abr ${ANS.res}">${{ok: '✓ 正確', mix: '✓ 混合', size: '✗ 尺寸', bad: '✗ 錯誤'}[ANS.res]}</span><button class="ab nx" data-next="1">下一題 <kbd>Space</kbd></button>`;
  }
  bar.querySelectorAll('[data-a]').forEach(b => b.onclick = () => answer(b.dataset.a));
  bar.querySelectorAll('[data-next]').forEach(b => b.onclick = () => { nextQ(); window.scrollTo(0, 0); });
}
// ---------- page: charts ----------
let CGEN = 0;
async function renderCharts() {
  const g = ++CGEN;
  const C = Object.assign({sp: 'BTN_BB', fl: null, k: 0}, LS.get('cs', {}));
  if (!IDX.spots[C.sp]) C.sp = Object.keys(IDX.spots)[0];
  const fls = IDX.spots[C.sp].flops.map(x => x[0]); if (!fls.includes(C.fl)) C.fl = fls[0];
  $('#main').innerHTML = `<div class="pg"><div class="row ctl">${verSeg()}</div><div class="flt"><span class="dgl">情境</span>${SPORDER.filter(s => IDX.spots[s]).map(s => `<button class="chip sm ${s === C.sp ? 'on' : ''}" data-csp="${s}">${SPSH[s]}</button>`).join('')}</div>
    <div class="flt"><span class="dgl">翻牌</span><select id="cfl">${fls.map(f => `<option ${f === C.fl ? 'selected' : ''}>${f}</option>`).join('')}</select><span class="dgl">決策點</span><select id="cnd"></select></div><div id="cbox"><div class="loading">載入中…</div></div></div>`;
  bindCommon(); renderBar();
  $$('[data-csp]').forEach(b => b.onclick = () => { C.sp = b.dataset.csp; C.fl = null; C.k = 0; LS.set('cs', C); renderCharts(); });
  $('#cfl').onchange = e => { C.fl = e.target.value; C.k = 0; LS.set('cs', C); renderCharts(); };
  let F; try { F = await loadFlop(C.sp, C.fl); } catch (e) { if (g === CGEN && $('#cbox')) $('#cbox').innerHTML = '載入失敗'; return; }
  if (g !== CGEN || !$('#cbox')) return;
  const nodes = F.v[VER] || []; if (C.k >= nodes.length) C.k = 0;
  $('#cnd').innerHTML = nodes.map((n, k) => `<option value="${k}" ${k === C.k ? 'selected' : ''}>${STREETZH[streetOf(n)]}${streetOf(n) ? ' ' + cards(n.b).slice(3).map(cardTxt).join('') : ''}・${seats(C.sp)[n.p]}・${CATZH[n.c]}・${n.l || '（開始）'}</option>`).join('');
  $('#cnd').onchange = e => { C.k = +e.target.value; LS.set('cs', C); renderCharts(); };
  const n = nodes[C.k]; if (!n) { $('#cbox').innerHTML = '沒有資料'; return; }
  const info = F.info[VER === 'gto' ? 'gto' : (n.p === 1 ? 'exp_ip' : 'exp_oop')] || {};
  $('#cbox').innerHTML = `<div class="sec"><div class="board">${boardHTML(n)}</div><div class="line">${lineHTML(C.sp, n)}</div><div class="pinfo">${potLine(C.sp, n)}・${seats(C.sp)[n.p]} 行動・這條線出現機率 ${f1(100 * n.pr)}%</div>
    ${gridHTML(C.sp, n, null)}${legendHTML(C.sp, n)}<div class="cdet"></div>
    <p class="muted small">收斂：${VER === 'gto' ? `可剝削度 ${f1(info.gto_expl_pct || 0)}% 底池` : `英雄最佳回應差距 ${f1(info.hero_gap_pct || 0)}% 底池（對手已鎖池頻率）`}</p>${VER === 'exp' ? poolNote(C.sp, n) : ''}</div>`;
  bindGrid(C.sp, n, null);
}
// ---------- page: about ----------
function renderAbout() {
  const sm = IDX.summary || {};
  $('#main').innerHTML = `<div class="pg"><div class="sec"><h3>翻後練習怎麼來的</h3>
  <ul><li>引擎：HU 翻後 CFR（DCFR），翻牌→轉牌→河牌全樹，5% 抽水、上限 10bb，有效籌碼 100bb。</li>
  <li>起手範圍：直接取自 v8 翻前解（GTO 版用 GTO 範圍；剝削版用你的剝削範圍 vs NL2 池的實際範圍）。</li>
  <li>翻牌樹：翻前加注者下注 33%／75%，加注 3 倍或全下；轉牌 66%、河牌 75%（粗樹，用來求翻牌策略）。</li>
  <li>轉牌細解：主要 c-bet 線與過牌過牌線，每個翻牌取 3 張轉牌重解：轉牌 50%／100%，河牌 50%／100%／全下。</li>
  <li>剝削版：把對手鎖成 NL2 池頻率（n≥500 的節點），再解你的最佳回應；對手下注時的尺寸比例也照 NL2 池的尺寸分佈；樣本太少的節點對手照均衡應對。</li>
  <li>不出題的組合：很少走到的線（出現機率 &lt;0.2%）不出題；solver 最高頻動作比它自己算出的最佳 EV 動作少 0.25bb 以上（且超過底池 5%）的組合，代表該處未完全收斂，在表中標「*未收斂」，也不出題。同一決策點面對較大下注反而比面對較小下注多繼續 ≥50 個百分點的組合（不同尺寸間矛盾），標「*不同尺寸間矛盾」，也不出題。</li>
  <li>評分：這個組合最高頻的動作，或任何 ≥25% 的動作都算對；下注方向對但尺寸 &lt;25% 記為「尺寸不對」（算錯）。答錯的題目 3 題後再出、答對後 8 題再複習一次。</li>
  <li>題目抽樣：翻牌依實際出現機率等權抽樣（${Object.values(IDX.spots).reduce((t, s) => t + s.flops.length, 0)} 個代表翻牌），線依出現機率開根號加權，手牌依到達率和難度（混合策略）加權。</li></ul>
  ${sm.html || ''}
  <p class="muted small">限制：只解 HU 底池；下注尺寸是抽象化的（實戰尺寸會不同）；轉牌/河牌只取樣部分牌；NL2 池的翻後統計來自攤牌與行動紀錄，攤牌牌力資料有偏差。</p></div></div>`;
  bindCommon(); renderBar();
}
// ---------- routing ----------
const TOP = [['prac', '練習'], ['charts', '翻後表'], ['about', '說明']];
function go(id, push) {
  if (id === 'prac') id = LASTDRILL;
  if (!DR[id] && !['charts', 'about'].includes(id)) id = 'all';
  PAGE = id; Q = null; ANS = null;
  const top = DR[id] ? 'prac' : id;
  $$('#topnav .topb').forEach(b => b.classList.toggle('on', b.dataset.top === top));
  if (location.hash !== '#' + id) history.replaceState(null, '', location.pathname + location.search + '#' + id);
  if (DR[id]) { LASTDRILL = id; LS.set('last', id); renderDrillShell(); nextQ(); }
  else { renderBar(); if (id === 'charts') renderCharts(); else renderAbout(); }
  if (push !== false) window.scrollTo(0, 0);
}
function bindCommon() {
  $$('#main [data-ver]').forEach(b => b.onclick = () => { setVer(b.dataset.ver); if (DR[PAGE]) { renderDrillShell(); nextQ(); } else go(PAGE, false); });
  $$('#main [data-go]').forEach(a => a.onclick = e => { e.preventDefault(); go(a.dataset.go); });
}
async function boot() {
  try { IDX = await fetch('data/index.json').then(r => r.json()); } catch (e) { $('#main').innerHTML = '<div class="loading">資料載入失敗</div>'; return; }
  IDX.cats.forEach(([k, zh, st]) => { CATZH[k] = zh; CATST[k] = st; });
  buildDrills();
  $('#topnav').innerHTML = TOP.map(([k, t]) => `<button class="topb" data-top="${k}">${t}</button>`).join('').replace('<button class="topb" data-top="about">', '<a class="topb" href="../solver.html" style="text-decoration:none;text-align:center">河牌解算器</a><button class="topb" data-top="about">');
  $$('#topnav .topb[data-top]').forEach(b => b.onclick = () => go(b.dataset.top));
  document.addEventListener('keydown', e => {
    if (!DR[PAGE] || !Q || e.metaKey || e.ctrlKey || e.altKey) return; if (e.target && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
    const k = e.key.toUpperCase();
    if (!ANS) { const a = Q.n.a.find(x => keyOf(Q.n, x) === k); if (a) { e.preventDefault(); answer(a); } }
    else if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); nextQ(); window.scrollTo(0, 0); }
  });
  window.addEventListener('hashchange', () => { const id = location.hash.slice(1); if (id && id !== PAGE) go(id); });
  go(location.hash.slice(1) || 'prac', false);
}
// test hooks
window.PP = {okActs, judge, keyOf, classAgg, loadFlop, findNode, hidx, combo, row, version: () => VER, page: () => PAGE, drills: () => DRILLS,
  q: () => Q && {sp: Q.sp, fl: Q.fl, l: Q.n.l, b: Q.n.b, h: Q.h, i: Q.i}, ans: () => ANS, answer, go, nextQ,
  async ask(sp, fl, l, b, h) { GEN++; const F = await loadFlop(sp, fl), n = findNode(F, VER, l, b), i = hidx(n, h); Q = {sp, fl, F, n, i, h, key: qkey(sp, fl, l, b, h)}; ANS = null; renderDrill(); }};
boot();
})();
