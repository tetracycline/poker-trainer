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
  const ag = aggIndex(n).filter(x => x !== 'a'); const k = ag.indexOf(a); return k === 0 ? 'R' : k === 1 ? 'B' : 'N';
}
function btnClass(n, a) { if (a === 'f' || a === 'x' || a === 'c' || a === 'a' || a === 'r') return 'k-' + a; const ag = aggIndex(n).filter(x => x !== 'a'); return 'k-b' + Math.min(3, ag.indexOf(a) + 1); }
const COLS = {f: '#26332b', x: '#3b78c4', c: '#3b78c4', a: '#8e44ad', r: '#c9483f'};
function colOf(n, a) { if (COLS[a]) return COLS[a]; const ag = aggIndex(n).filter(x => x !== 'a'); return ['#d9825b', '#c9483f', '#9e2f2a'][Math.min(2, ag.indexOf(a))]; }
const STREETZH = ['翻牌', '轉牌', '河牌'];
function streetOf(n) { return n.l.split('/').length - 1; }
function lineHTML(sp, n) {
  const r = replay(sp, n.l), bd = cards(n.b);
  return `<div><span class="st">翻前</span>${pfLine(sp)}</div>` + r.out.map((d, si) => {
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
// HW 實際會玩：翻前核心範圍（hwrange.js）＋這條線至少 50% 會走到這裡
function hwRole(sp, p) { const S = spotOf(sp), me = p ? S.ip : S.oop, op = p ? S.oop : S.ip;
  if (S.kind === 'SRP') return S.pfr === p ? ['open', me] : ['call', op + 'open>' + me];
  return S.pfr === p ? ['tb', op + 'open>' + me] : ['c3', me + 'open>' + op + '3b']; }
function hwOK(sp, n, i) { if (!window.HWR) return true; const r = hwRole(sp, n.p); return HWR.ok(r[0], r[1], classOf(combo(n, i))); }
function pfLine(sp) { const S = spotOf(sp);
  if (S.kind === 'SRP') { const o = S.pfr ? S.ip : S.oop, c = S.pfr ? S.oop : S.ip, sz = o === 'SB' ? 3 : 2.5; return `${o} 開 <b>${sz}bb</b> → ${c} 跟注`; }
  const ag = S.pfr ? S.ip : S.oop, o = S.pfr ? S.oop : S.ip, to = (100 - S.stack); return `${o} 開 <b>2.5bb</b> → ${ag} 3-bet 到 <b>${to}bb</b> → ${o} 跟注`; }
function handWeight(n, i, mk) {
  const w = n.w[i]; if (w < 50 || unrel(n, i)) return 0;
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
      try { const F = await loadFlop(it.sp, it.fl), n = findNode(F, VER, it.l, it.b), i = n ? hidx(n, it.h) : -1; if (n && i >= 0 && n.w[i] >= 50 && !unrel(n, i) && pfa(it.sp, n, i) > 0 && hwOK(it.sp, n, i)) q = {sp: it.sp, fl: it.fl, F, n, i, review: it.stage || 1}; } catch (e) {}
    }
    for (let tries = 0; !q && tries < 12; tries++) {
      const cf = pick(candFlops(d), x => x.w); if (!cf) break;
      const F = await loadFlop(cf.sp, cf.fl);
      const nodes = (F.v[VER] || []).filter(n => !d.cat || n.c === d.cat);
      const n = pick(nodes, x => (x.pr < MIN_PR_Q ? 0 : Math.sqrt(x.pr)) * (x.c === 'vs_raise' && d.cat !== 'vs_raise' ? 0.3 : 1)); if (!n) continue;
      const mk = i => qkey(cf.sp, cf.fl, n.l, n.b, combo(n, i));
      const idx = []; for (let i = 0; i < nh(n); i++) idx.push(i);
      const i = pick(idx, k => (prev && prev.n === n && prev.i === k) ? 0 : handWeight(n, k, mk) * pfa(cf.sp, n, k) * (hwOK(cf.sp, n, k) ? 1 : 0)); if (i == null) continue;
      q = {sp: cf.sp, fl: cf.fl, F, n, i};
    }
    if (stale()) return;
    if (!q) { $('#qbox').innerHTML = '<div class="qcard">這個項目在目前版本沒有題目。</div>'; return; }
    q.h = combo(q.n, q.i); q.key = qkey(q.sp, q.fl, q.n.l, q.n.b, q.h); Q = q; renderDrill();
  } catch (e) { if (!stale()) $('#qbox').innerHTML = `<div class="qcard">載入失敗：${esc(e.message)}</div>`; console.warn(e); }
}
// 剝削規則：剝削版的主動作比 GTO 主動作多賺 >0.25bb 才照剝削版，否則照 GTO
function gateExp(q) {
  const n = q.n, i = q.i; if (VER !== 'exp') return {use: VER};
  const on = findNode(q.F, 'gto', n.l, n.b), oi = on ? hidx(on, q.h) : -1; if (!on || oi < 0) return {use: 'exp', why: 'nogto'};
  const em = okActs(n, i).main, gm = okActs(on, oi).main; if (em === gm || !n.a.includes(gm) || !on.a.includes(em) && false) return {use: 'exp', gain: 0, on, oi};
  const ev = evRow(n, i), gain = (ev[n.a.indexOf(em)] - ev[n.a.indexOf(gm)]) / 100;
  return gain > 0.25 ? {use: 'exp', gain, on, oi} : {use: 'gto', gain, on, oi};
}
function answer(a) {
  if (!Q || ANS) return; const n = Q.n; if (!n.a.includes(a)) return;
  const gt = gateExp(Q), res = gt.use === 'gto' ? judge(gt.on, gt.oi, a) : judge(n, Q.i, a), good = GOOD(res), k = Q.key;
  ANS = {a, res, ver: gt.use === 'gto' ? 'gto' : VER, gn: gt.use === 'gto' ? gt.on : null, gi: gt.oi, gain: gt.gain}; SES.n++; if (good) SES.ok++; ST.cnt++;
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
  const dpk = window.__dpk; window.__dpk = false;
  let h = `<details class="dpick" ${dpk ? 'open' : ''}><summary>練習項目：<b>${DR[PAGE].g}・${DR[PAGE].name}</b><span class="muted small">（點這裡換）</span></summary><div class="dnav">`; let g = '';
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
  const R = hwRole(q.sp, n.p); window.__Q = {drill: 'postflop', id: PAGE, hero: q.h, board: n.b, role: R, line: n.l, w: n.w[q.i], streets: 1 + streetOf(n), ver: VER};
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
  const q = ANS.gn ? Object.assign({}, Q, {n: ANS.gn, i: ANS.gi}) : Q, n = q.n, a = ANS.a, v = ANS.ver, o = okActs(n, q.i);
  const head = {ok: '✓ 正確', mix: '✓ 正確（混合）', size: '✗ 方向對，尺寸不對', bad: '✗ 錯誤'}[ANS.res];
  const mainTxt = o.ok.map(x => actLabel(q.sp, n, x, true) + ' ' + o.s[n.a.indexOf(x)] + '%').join(' / ');
  let h = `<div class="sec res ${ANS.res}"><div class="rh">${head}</div><div>你選 <b>${esc(actLabel(q.sp, n, a, true))}</b>；${VERZH[v]}解在這手 ${cards(q.h).map(cardTxt).join('')}：<b>${esc(mainTxt)}</b>${ANS.res === 'mix' ? '（低頻但 ≥25%，算對）' : ''}</div></div>`;
  h += `<div class="sec">${evTable(q.sp, n, q.i, a)}<p class="muted small">勝率（對手此刻範圍）${n.eq[q.i]}%。EV＝從這個決策起，這手牌最後從底池拿回的期望籌碼（bb，已扣 5% 抽水、上限 10bb；棄牌＝0）。頻率 ≥25% 的動作都算正確；下注方向對但尺寸 &lt;25% 記為錯（尺寸不對）。</p>`;
  if (n.a.includes('c')) { const call = Math.max(...n.bt) - n.bt[n.p]; h += `<p class="muted small">底池賠率：補 ${fbb(call)}bb 去贏 ${fbb(n.pot)}bb，需要約 ${f1(100 * call / (n.pot + call))}% 勝率（未扣抽水、未計之後的街）。</p>`; }
  const ov = v === 'exp' ? 'gto' : 'exp', on = findNode(q.F, ov, n.l, n.b), oi = on ? hidx(on, q.h) : -1;
  if (on && oi >= 0) { const oo = okActs(on, oi); h += `<p class="muted small">${VERZH[ov]}版：${oo.ok.map(x => actLabel(q.sp, on, x, true) + ' ' + oo.s[on.a.indexOf(x)] + '%').join(' / ')}</p>`; }
  else h += `<p class="muted small">${VERZH[ov]}版：那個版本的解不會走到這條線（尺寸或範圍不同），或這手牌不在範圍內。</p>`;
  if (ANS.gn) h += `<p class="small"><b>照 GTO</b>：剝削版的打法只多賺 ${ANS.gain.toFixed(2)}bb ≤ 0.25bb／手 → 這題以 GTO 評分。</p>`;
  else if (VER === 'exp' && ANS.gain > 0.25) h += `<p class="small"><b>用剝削版</b>：比 GTO 打法多賺 ${ANS.gain.toFixed(2)}bb > 0.25bb／手（鎖定的池頻率 n≥500）。</p>`;
  if (v === 'exp') h += poolNote(q.sp, n);
  h += `</div><div class="sec"><div class="row sp"><b>${CATZH[n.c]}・${VERZH[v]}</b><span class="muted small">整個範圍：${n.a.map((x, j) => esc(actLabel(q.sp, n, x, true)) + ' ' + f1(n.f[j]) + '%').join('・')}</span></div>${gridHTML(q.sp, n, classOf(q.h))}${legendHTML(q.sp, n)}<div class="cdet"></div></div>`;
  $('#ans').innerHTML = h; bindGrid(q.sp, n, q.h);
  const d = $('#ans .cdet'); if (d) { d.innerHTML = combosHTML(q.sp, n, classOf(q.h), q.h); d.querySelectorAll('.cmb').forEach(c => c.onclick = () => { d.querySelector('.cev').innerHTML = `<p class="small"><b>${cards(combo(n, +c.dataset.i)).map(cardTxt).join('')}</b>・勝率 ${n.eq[+c.dataset.i]}%</p>` + evTable(q.sp, n, +c.dataset.i); }); }
}
function renderBar() {
  const bar = $('#abar'); if (!bar) return;
  if (PAGE === 'hand') { bar.classList.remove('hide'); document.body.classList.add('hasbar'); hBar(bar); return; }
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
// ---------- page: 整手（翻牌一路打到開牌） ----------
// 你：從 HW 實際會玩的範圍發牌；對手：池頻率（n≥500 且和 GTO 有顯著差）否則照 GTO；每個決策當場評分（剝削版多賺 >0.25bb 才照剝削版）。
let H = null, HGEN = 0;
const HZH = ['高牌', '一對', '兩對', '三條', '順子', '同花', '葫蘆', '四條', '同花順'];
function hEval(cs) {
  const r = cs.map(c => RK.indexOf(c[0])), cnt = Array(13).fill(0), bs = {}; r.forEach(x => cnt[x]++);
  cs.forEach((c, k) => (bs[c[1]] = bs[c[1]] || []).push(r[k]));
  const sHi = rs => { const S = new Set(rs); if (S.has(12)) S.add(-1); for (let h = 12; h >= 3; h--) { let ok = true; for (let k = 0; k < 5; k++) if (!S.has(h - k)) { ok = false; break; } if (ok) return h; } return -1; };
  for (const s in bs) if (bs[s].length >= 5) { const h = sHi(bs[s]); if (h >= 0) return [8, h]; }
  const g = []; for (let x = 12; x >= 0; x--) if (cnt[x]) g.push([cnt[x], x]); g.sort((a, b) => b[0] - a[0] || b[1] - a[1]);
  const rest = skip => r.filter(x => !skip.includes(x)).sort((a, b) => b - a);
  if (g[0][0] === 4) return [7, g[0][1], rest([g[0][1]])[0]];
  if (g[0][0] === 3 && g[1] && g[1][0] >= 2) return [6, g[0][1], g[1][1]];
  for (const s in bs) if (bs[s].length >= 5) return [5, ...bs[s].sort((a, b) => b - a).slice(0, 5)];
  const st = sHi(r); if (st >= 0) return [4, st];
  if (g[0][0] === 3) return [3, g[0][1], ...rest([g[0][1]]).slice(0, 2)];
  if (g[0][0] === 2 && g[1] && g[1][0] === 2) return [2, g[0][1], g[1][1], rest([g[0][1], g[1][1]])[0]];
  if (g[0][0] === 2) return [1, g[0][1], ...rest([g[0][1]]).slice(0, 3)];
  return [0, ...rest([]).slice(0, 5)];
}
const hCmp = (a, b) => { for (let k = 0; k < Math.max(a.length, b.length); k++) { const d = (a[k] || 0) - (b[k] || 0); if (d) return d; } return 0; };
function hState(sp, line) {
  const S = spotOf(sp), STK = Math.round(S.stack * 100), sts = line.split('/'); let pot = Math.round(S.pot * 100), con = 0, b = [0, 0];
  sts.forEach((s, si) => { b = [0, 0]; (s ? s.split(' ') : []).forEach((t, k) => { const p = k % 2, mx = Math.max(b[0], b[1]);
    if (t === 'c') b[p] = mx; else if (t[0] === 'b') b[p] = Math.round(+t.slice(1) / 100 * pot); else if (t === 'r') b[p] = Math.min(3 * mx, STK - con); else if (t === 'a') b[p] = STK - con; });
    if (si < sts.length - 1) { pot += b[0] + b[1]; con += Math.max(b[0], b[1]); b = [0, 0]; } });
  return {pot, b, con, STK, tot: pot + b[0] + b[1], left: [STK - con - b[0], STK - con - b[1]]};
}
const hToks = l => { const s = l.split('/'); const t = s[s.length - 1]; return t ? t.split(' ') : []; };
const hClosed = tk => tk.length >= 2 && (tk[tk.length - 1] === 'c' || (tk.length === 2 && tk[0] === 'x' && tk[1] === 'x'));
const hAdd = (l, a) => l + (hToks(l).length ? ' ' : '') + a;
const hNodes = () => (H.F.v.gto || []).concat(H.F.v.exp || []);
function hHas(l, b) { return hNodes().some(n => n.l === l && n.b === b); }
// 這個動作之後，解裡還有沒有後續（下一個決策點或下一條街）
function hCont(l, b) {
  const tk = hToks(l); if (tk[tk.length - 1] === 'f') return true;
  if (hClosed(tk)) { if (l.split('/').length === 3) return true; const st = hState(H.sp, l); if (Math.min(...st.left) <= 0) return true;
    return hNodes().some(n => n.l.startsWith(l + '/') && n.b.length === b.length + 2 && n.b.startsWith(b)); }
  return hHas(l, b);
}
function hLock(l) {
  if (VER !== 'exp') return null; const inf = H.F.info[H.hp === 0 ? 'exp_oop' : 'exp_ip']; if (!inf || !inf.locks) return null;
  return inf.locks.find(L => { try { return new RegExp(L.pat).test(l); } catch (e) { return false; } }) || null;
}
function hPick(ws) { const t = ws.reduce((a, b) => a + b, 0); if (t <= 0) return -1; let r = Math.random() * t; for (let k = 0; k < ws.length; k++) { r -= ws[k]; if (r <= 0) return k; } return ws.length - 1; }
const pc = x => f1(100 * x) + '%';
// 對手動作：池（n≥500 且 GTO 落在 95% 信賴區間外）→ 照池；否則照 GTO
function hVillain() {
  const l = H.line, n = findNode(H.F, 'gto', l, H.b), who = seats(H.sp)[1 - H.hp];
  if (!n) return hVillainNoNode(l, who);
  const facing = n.a.includes('f'), gf = n.a.map((a, j) => n.f[j] / 100), agg = n.a.map(AGG);
  let w = gf.slice(), src = 'GTO（GTO 模式）';
  const L = hLock(l);
  if (VER === 'exp') {
    if (!L) src = '池樣本不足（n<500）→ 照 GTO';
    else {
      const gA = gf.reduce((t, x, j) => t + (agg[j] ? x : 0), 0), gF = facing ? gf[n.a.indexOf('f')] : 0;
      const pv = facing ? L.fold : L.bet, gv = facing ? gF : gA, ci = pv != null ? wilson(pv, L.n) : null;
      const stat = `${facing ? '棄牌' : '下注'} 池 ${pv != null ? pc(pv) : '—'} vs GTO ${pc(gv)}（n=${L.n.toLocaleString()}${ci ? `，95% ${pc(ci[0])}–${pc(ci[1])}` : ''}；${esc(L.src)}）`;
      const sig = ci && (gv < ci[0] || gv > ci[1]);
      if (sig) {
        if (facing) { const pr = L.raise_ != null ? L.raise_ : gA, pcall = Math.max(0, 1 - pv - pr);
          const gC = gf.reduce((t, x, j) => t + (n.a[j] === 'c' ? x : 0), 0);
          w = n.a.map((a, j) => a === 'f' ? pv : agg[j] ? (gA ? pr * gf[j] / gA : 0) : (gC ? pcall * gf[j] / gC : pcall)); }
        else w = n.a.map((a, j) => agg[j] ? (gA ? pv * gf[j] / gA : 0) : 1 - pv);
        src = stat + ' → 顯著，照池抽';
      } else src = stat + ' → 不顯著 → 照 GTO';
    }
  }
  // 只抽解裡有後續的動作
  const ok = n.a.map(a => hCont(hAdd(l, a), H.b)); let w2 = w.map((x, j) => ok[j] ? x : 0), cut = false;
  if (w2.some(x => x > 0) && w2.some((x, j) => !ok[j] && w[j] > 0.005)) cut = true; else if (!w2.some(x => x > 0)) w2 = w;
  const j = hPick(w2); const a = n.a[j];
  H.vn.push({n, a});
  return {a, txt: `${who} ${actLabel(H.sp, n, a)}`, src: src + (cut ? '（解裡沒後續的動作不抽）' : '')};
}
// 解沒存他這個點：剝削版有池鎖（你上一個動作之後的 NL2 頻率）就照池；否則只能走解裡有的後續線
function hVillainNoNode(l, who) {
  const tk = hToks(l), S = hState(H.sp, l), facing = S.b[1 - H.hp] < Math.max(...S.b);
  const cand = facing ? ['f', 'c', 'r', 'a'] : ['x', 'b33', 'b50', 'b75', 'b100', 'a'];
  const ok = cand.filter(a => a === 'f' || hCont(hAdd(l, a), H.b)); if (!ok.filter(a => a !== 'f').length) return null;
  const hn = H.prev, L = hn && hn.nx && hn.nx[H.prevA];
  let w = ok.map(() => 1), src = '解沒存他這個點的頻率 → 在解裡有後續的線中平均抽（不代表真實頻率）';
  if (L && L.n) {
    const pv = facing ? L.fold : L.bet;
    if (pv != null) { const ci = wilson(pv, L.n), ag = ok.filter(a => AGG(a)).length || 1;
      w = ok.map(a => facing ? (a === 'f' ? pv : AGG(a) ? (L.raise_ || 0) / ag : Math.max(0, 1 - pv - (L.raise_ || 0))) : (AGG(a) ? pv / ag : 1 - pv));
      src = `${facing ? '棄牌' : '下注'} 池 ${pc(pv)}（n=${L.n.toLocaleString()}，95% ${pc(ci[0])}–${pc(ci[1])}；${esc(L.src || '')}）→ 無 GTO 對照（解沒存 GTO 這點）→ 照池抽`; }
  }
  else if (facing) { const bet = Math.max(...S.b) - S.b[1 - H.hp], al = bet / (S.tot + bet), cn = ok.filter(a => a !== 'f').length;
    w = ok.map(a => a === 'f' ? al : (1 - al) / cn); src = `解沒存他這點的頻率、也無池樣本 → 用最低防守頻率（棄 ${pc(al)}），其餘平均分到解裡有後續的線（不代表真實頻率）`; }
  if (!w.some(x => x > 0)) w = ok.map(() => 1);
  const j = hPick(w); if (j < 0) return null; const a = ok[j];
  const fake = {a: ok, bt: S.b, pot: S.pot, l}; let t;
  if (a === 'x') t = '過牌'; else if (a === 'f') t = '棄牌'; else if (a === 'c') t = `跟注 ${fbb(Math.max(...S.b) - S.b[1 - H.hp])}bb`; else if (a[0] === 'b') t = `下注 ${a.slice(1)}%（${fbb(+a.slice(1) / 100 * S.pot)}bb）`; else if (a === 'r') t = `加注到 ${fbb(3 * Math.max(...S.b))}bb`; else t = `全下 ${fbb(S.left[1 - H.hp])}bb`;
  return {a, txt: `${who} ${t}`, src};
}
async function hDeal() {
  for (let tries = 0; tries < 40; tries++) {
    const cf = pick(candFlops({}), x => x.w); if (!cf) return null;
    let F; try { F = await loadFlop(cf.sp, cf.fl); } catch (e) { continue; }
    const hp = Math.random() < 0.5 ? 0 : 1;
    const n0 = (F.v[VER] || []).concat(F.v.gto || []).find(n => n.p === hp && n.l.split('/').length === 1); if (!n0) continue;
    const idx = []; for (let i = 0; i < nh(n0); i++) idx.push(i);
    const i = pick(idx, k => (n0.w[k] >= 50 && !unrel(n0, k) && hwOK(cf.sp, n0, k) ? n0.w[k] * pfa(cf.sp, n0, k) : 0)); if (i == null) continue;
    const b0 = n0.b.slice(0, 6);
    return {sp: cf.sp, fl: cf.fl, F, hp, h: combo(n0, i), w0: n0.w[i], b: b0, line: '', log: [[]], dec: [], vn: [], off: false, end: null, cur: null};
  }
  return null;
}
async function hNew() {
  const g = ++HGEN; H = null; renderBar();
  const d = await hDeal();
  if (g !== HGEN || !$('#hbox')) return;
  if (!d) { $('#hbox').innerHTML = '<div class="qcard">發牌失敗，再按一次。</div>'; return; }
  H = d; hRun();
}
function hLog(t, src) { H.log[H.log.length - 1].push({t, src}); }
function hRun() {
  for (let guard = 0; guard < 40; guard++) {
    const tk = hToks(H.line), last = tk[tk.length - 1], st = H.line.split('/').length - 1;
    if (last === 'f') { H.end = {fold: (tk.length - 1) % 2}; break; }
    const S = hState(H.sp, H.line);
    if (hClosed(tk)) {
      if (st === 2) { H.end = {sd: 1}; break; }
      const allin = Math.min(...S.left) <= 0;
      const used = cards(H.h).concat(cards(H.b));
      let nb = [...new Set(hNodes().filter(n => n.l.startsWith(H.line + '/') && n.b.length === H.b.length + 2 && n.b.startsWith(H.b)).map(n => n.b))].filter(b => !used.includes(b.slice(-2)));
      if (allin || H.off || !nb.length) { if (!allin && !H.off) { H.off = true; H.why = 'card@' + H.line; hLog('（解只存主要的線；之後自動過牌/跟注到開牌，不評分）', ''); }
        const dk = []; for (const r of RK) for (const s of 'shdc') if (!used.includes(r + s)) dk.push(r + s); nb = [H.b + dk[Math.floor(Math.random() * dk.length)]]; }
      H.b = nb[Math.floor(Math.random() * nb.length)]; H.line += '/'; H.log.push([]);
      if (allin) continue;
      continue;
    }
    const p = tk.length % 2;
    if (Math.min(...S.left) <= 0 && tk.length === 0) { H.line = hAdd(H.line, 'x'); H.line = hAdd(H.line, 'x'); continue; }
    if (H.off) { const mx = Math.max(...S.b), a = S.b[p] < mx ? 'c' : 'x'; hLog(`${seats(H.sp)[p]} ${a === 'c' ? '跟注' : '過牌'}`, '解外：自動'); H.line = hAdd(H.line, a); continue; }
    if (!H.line && !hHas('', H.b)) { hLog(`${seats(H.sp)[0]}${H.hp === 0 ? '（你）' : ''} 過牌`, '解設定：翻牌由 ' + seats(H.sp)[0] + ' 先過牌（不出題）'); H.line = 'x'; continue; }
    if (p === H.hp) {
      let n = findNode(H.F, VER, H.line, H.b), i = n ? hidx(n, H.h) : -1;
      if (i < 0) { n = findNode(H.F, VER === 'exp' ? 'gto' : 'exp', H.line, H.b); i = n ? hidx(n, H.h) : -1; }
      if (!n || i < 0) { H.off = true; H.why = (n ? 'hand' : 'node') + '@' + H.line; hLog('（你這手在這條線上解裡沒有；之後自動到開牌，不評分）', ''); continue; }
      H.cur = {n, i, fb: n !== findNode(H.F, VER, H.line, H.b)}; break;
    }
    const v = hVillain(); if (!v) { H.off = true; H.why = 'vil@' + H.line; continue; }
    hLog(v.txt, v.src); H.line = hAdd(H.line, v.a);
  }
  if (H.end) hFinish(); hRender();
}
function hAnswer(a) {
  if (!H || !H.cur || H.cur.ans) return; const {n, i} = H.cur; if (!n.a.includes(a)) return;
  const q = {F: H.F, n, i, h: H.h}, gt = VER === 'exp' && !H.cur.fb ? gateExp(q) : {use: H.cur.fb ? 'gto' : VER, on: n, oi: i};
  const gn = gt.use === 'gto' && gt.on ? gt.on : n, gi = gt.use === 'gto' && gt.on ? gt.oi : i;
  const res = judge(gn, gi, a), ev = evRow(gn, gi), j = gn.a.indexOf(a), best = Math.max(...ev), loss = j >= 0 ? (best - ev[j]) / 100 : null, o = okActs(gn, gi);
  const vz = gt.use === 'gto' ? 'GTO' : VERZH[VER];
  const why = VER === 'exp' ? (H.cur.fb ? '剝削解沒存這個點 → 照 GTO' : gt.use === 'gto' ? `剝削打法只多賺 ${(gt.gain || 0).toFixed(2)}bb ≤ 0.25 → 照 GTO` : gt.gain > 0.25 ? `剝削多賺 ${gt.gain.toFixed(2)}bb > 0.25 → 用剝削解` : '剝削解和 GTO 同動作') : 'GTO';
  H.cur.ans = {a, res, loss, best: o.ok.map(x => actLabel(H.sp, gn, x, true) + ' ' + o.s[gn.a.indexOf(x)] + '%').join(' / '), vz, why, st: streetOf(n)};
  H.dec.push(Object.assign({l: H.line, al: actLabel(H.sp, n, a, true)}, H.cur.ans));
  hLog(`${seats(H.sp)[H.hp]}（你）${actLabel(H.sp, n, a)}`, '');
  H.prev = n; H.prevA = a; H.line = hAdd(H.line, a); hRender();
}
function hNext() { if (!H) return hNew(); if (H.end && !H.cur) return hNew(); if (H.cur && H.cur.ans) { H.cur = null; hRun(); } }
function hFinish() {
  const used = cards(H.h).concat(cards(H.b)), vp = 1 - H.hp;
  // 對手的牌：他的範圍 × 他這手每個動作的 GTO 機率，抽一手
  const first = H.vn.length ? H.vn[0].n : (H.F.v.gto || []).find(n => n.p === vp);
  let vh = null;
  if (first) { const ws = []; for (let k = 0; k < nh(first); k++) { const c = combo(first, k), cc = cards(c); if (cc.some(x => used.includes(x))) { ws.push(0); continue; }
      let w = first.w[k] * pfa(H.sp, first, k); for (const {n, a} of H.vn) { const ii = hidx(n, c); w *= ii < 0 ? 0 : row(n, ii)[n.a.indexOf(a)] / 100; } ws.push(w); }
    const k = hPick(ws); if (k >= 0) vh = combo(first, k); }
  H.vh = vh; const S = hState(H.sp, H.line);
  while (H.end.sd && cards(H.b).length < 5) { const u = used.concat(vh ? cards(vh) : []); const dk = []; for (const r of RK) for (const s of 'shdc') if (!u.includes(r + s) && !cards(H.b).includes(r + s)) dk.push(r + s); H.b += dk[Math.floor(Math.random() * dk.length)]; }
  if (H.end.fold != null) { H.end.win = H.end.fold === H.hp ? -1 : 1; H.end.pot = S.tot; return; }
  const me = hEval(cards(H.h).concat(cards(H.b))), op = vh ? hEval(cards(vh).concat(cards(H.b))) : null, c = op ? hCmp(me, op) : 0;
  Object.assign(H.end, {me, op, win: c > 0 ? 1 : c < 0 ? -1 : 0, pot: S.tot});
}
function hBoard() { const bd = cards(H.b); const fl = bd.slice(0, 3).sort((x, y) => RK.indexOf(y[0]) - RK.indexOf(x[0])); bd.splice(0, 3, ...fl); return bd.map((c, k) => (k === 3 || k === 4 ? '<span class="bsep"></span>' : '') + cardHTML(c)).join(''); }
function hLine() {
  const bd = cards(H.b); const fl = bd.slice(0, 3).sort((x, y) => RK.indexOf(y[0]) - RK.indexOf(x[0]));
  return `<div><span class="st">翻前</span>${pfLine(H.sp)}</div>` + H.log.map((L, si) => {
    const bc = si === 0 ? fl : [bd[si + 2]]; if (!bc[0]) return '';
    const t = L.length ? L.map(x => x.t.replace(/(\d+)%/, '<b>$1%</b>')).join(' → ') : '<span class="muted">（輪到你先行動）</span>';
    return `<div><span class="st">${STREETZH[si]} ${bc.map(cardTxt).join('')}</span>${t}</div>`; }).join('');
}
function hSrc() { const v = H.log.flat().filter(x => x.src); return v.length ? `<details class="hsrc"><summary class="small muted">對手動作依據（${v.length}）</summary><ul class="small">${v.map(x => `<li><b>${x.t}</b>：${x.src}</li>`).join('')}</ul></details>` : ''; }
function hRender() {
  const box = $('#hbox'); if (!box || !H) return;
  const S = hState(H.sp, H.line), me = seats(H.sp)[H.hp], spk = spotOf(H.sp).kind === 'SRP' ? '單次加注' : '3-bet 底池';
  let h = `<div class="qcard"><div class="tags"><span class="tag">${SPZH[H.sp]}</span><span class="tag v-${VER}">${VERZH[VER]}</span><span class="tag">你是 ${me}（${H.hp ? '有位置' : '沒位置'}）</span></div>
    <div class="board">${hBoard()}</div><div class="line">${hLine()}</div>${hSrc()}
    <div class="pinfo">底池 <b>${fbb(S.tot)}bb</b>・你剩 ${fbb(S.left[H.hp])}bb・他剩 ${fbb(S.left[1 - H.hp])}bb・${spk}・100bb</div>
    <div class="hand">${cards(H.h).map(c => cardHTML(c)).join('')}<span class="hcls">${classOf(H.h)}</span></div>`;
  if (H.cur && !H.cur.ans) h += `<p class="muted small qhint">你要怎麼做？${H.cur.n.a.map(a => `<kbd>${keyOf(H.cur.n, a)}</kbd> ${actLabel(H.sp, H.cur.n, a, true)}`).join('　')}</p>`;
  h += '</div>';
  const A = H.cur && H.cur.ans;
  let r = '';
  if (A) r += `<div class="sec res ${A.res}"><div class="rh">${{ok: '✓ 正確', mix: '✓ 正確（混合）', size: '✗ 尺寸不對', bad: '✗ 錯誤'}[A.res]}${A.loss != null ? `<span class="small">　EV 少 ${A.loss.toFixed(2)}bb</span>` : ''}</div><div class="small">${A.vz}：<b>${esc(A.best)}</b>・${esc(A.why)}</div></div>`;
  if (H.end) {
    const E = H.end, vh = H.vh, vs = seats(H.sp)[1 - H.hp];
    const res = E.win > 0 ? `你贏 ${fbb(E.pot)}bb 底池` : E.win < 0 ? `${vs} 贏 ${fbb(E.pot)}bb 底池` : '平分底池';
    const how = E.fold != null ? (E.fold === H.hp ? '你棄牌' : `${vs} 棄牌`) : `開牌：你 ${HZH[E.me[0]]}${E.op ? ` vs ${vs} ${HZH[E.op[0]]}` : ''}`;
    const tl = H.dec.reduce((t, d) => t + (d.loss || 0), 0), okn = H.dec.filter(d => GOOD(d.res)).length;
    r += `<div class="sec hend"><div class="rh">${how}・${res}</div>
      <div class="small">${vs} 的牌：${vh ? `<b>${cards(vh).map(cardTxt).join('')}</b>（依他的範圍＋他每個動作的 GTO 機率抽樣）` : '—'}</div>
      <div class="small">你的決策 ${okn}/${H.dec.length} 對・EV 共少 <b>${tl.toFixed(2)}bb</b></div>
      <ol class="small hdl">${H.dec.map(d => `<li>${STREETZH[d.st]}：你 ${esc(d.al)} ${GOOD(d.res) ? '✓' : '✗'}・最佳 ${esc(d.best)}・少 ${(d.loss || 0).toFixed(2)}bb</li>`).join('')}</ol></div>`;
  }
  box.innerHTML = h; $('#ans').innerHTML = r; renderBar();
  if (H.cur && !H.cur.ans) window.__Q = {drill: 'hand', id: 'hand', hero: H.h, board: H.b, role: hwRole(H.sp, H.hp), line: H.line, w: H.w0, streets: 1 + streetOf(H.cur.n), ver: VER, sp: H.sp};
}
function hBar(bar) {
  if (H && H.cur && !H.cur.ans) { const n = H.cur.n;
    bar.innerHTML = n.a.map(a => { const L = actLabel(H.sp, n, a), m = L.match(/^(.*?)(（.*）| [\d.]+bb)?$/); return `<button class="ab ${btnClass(n, a)}" data-a="${a}"><kbd>${keyOf(n, a)}</kbd> ${esc(actLabel(H.sp, n, a, true))}${m && m[2] ? `<small>${esc(m[2].replace(/[（）]/g, ''))}</small>` : ''}</button>`; }).join('');
    bar.querySelectorAll('[data-a]').forEach(b => b.onclick = () => hAnswer(b.dataset.a)); return; }
  const A = H && H.cur && H.cur.ans, end = H && H.end && (!H.cur || A);
  bar.innerHTML = `${A ? `<span class="abr ${A.res}">${{ok: '✓ 正確', mix: '✓ 混合', size: '✗ 尺寸', bad: '✗ 錯誤'}[A.res]}</span>` : ''}<button class="ab nx" data-next="1">${H && !H.end ? '繼續' : '下一手'} <kbd>Space</kbd></button>`;
  bar.querySelectorAll('[data-next]').forEach(b => b.onclick = () => { hNext(); });
}
function renderHand() {
  $('#main').innerHTML = `<div class="pg"><div class="row ctl">${verSeg()}<span class="muted small">整手：翻牌一路打到開牌・你的牌只發 HW 會玩的範圍</span></div><div id="hbox"><div class="loading">發牌中…</div></div><div id="ans"></div></div>`;
  bindCommon(); hNew();
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
const TOP = [['prac', '練習'], ['hand', '整手'], ['charts', '翻後表'], ['about', '說明']];
function go(id, push) {
  if (id === 'prac') id = LASTDRILL;
  if (!DR[id] && !['charts', 'about', 'hand'].includes(id)) id = 'all';
  PAGE = id; Q = null; ANS = null;
  const top = DR[id] ? 'prac' : id;
  $$('#topnav .topb').forEach(b => b.classList.toggle('on', b.dataset.top === top));
  if (location.hash !== '#' + id) history.replaceState(null, '', location.pathname + location.search + '#' + id);
  if (DR[id]) { LASTDRILL = id; LS.set('last', id); renderDrillShell(); nextQ(); }
  else if (id === 'hand') renderHand(); else { renderBar(); if (id === 'charts') renderCharts(); else renderAbout(); }
  if (push !== false) window.scrollTo(0, 0);
}
function bindCommon() {
  $$('#main [data-ver]').forEach(b => b.onclick = () => { setVer(b.dataset.ver); if (PAGE === 'hand') { renderHand(); return; } if (DR[PAGE]) { renderDrillShell(); nextQ(); } else go(PAGE, false); });
  $$('#main [data-go]').forEach(a => a.onclick = e => { e.preventDefault(); window.__dpk = e.detail === 0 && !!a.closest('details.dpick[open]'); go(a.dataset.go); });
}
async function boot() {
  try { IDX = await fetch('data/index.json').then(r => r.json()); } catch (e) { $('#main').innerHTML = '<div class="loading">資料載入失敗</div>'; return; }
  IDX.cats.forEach(([k, zh, st]) => { CATZH[k] = zh; CATST[k] = st; });
  buildDrills();
  $('#topnav').innerHTML = TOP.map(([k, t]) => `<button class="topb" data-top="${k}">${t}</button>`).join('').replace('<button class="topb" data-top="about">', '<a class="topb" href="../solver.html" style="text-decoration:none;text-align:center">河牌解算器</a><button class="topb" data-top="about">');
  $$('#topnav .topb[data-top]').forEach(b => b.onclick = () => go(b.dataset.top));
  document.addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return; if (e.target && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
    const k = e.key.toUpperCase();
    if (PAGE === 'hand') { if (H && H.cur && !H.cur.ans) { const a = H.cur.n.a.find(x => keyOf(H.cur.n, x) === k); if (a) { e.preventDefault(); hAnswer(a); } } else if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); hNext(); } return; }
    if (!DR[PAGE] || !Q) return;
    if (!ANS) { const a = Q.n.a.find(x => keyOf(Q.n, x) === k); if (a) { e.preventDefault(); answer(a); } }
    else if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); nextQ(); window.scrollTo(0, 0); }
  });
  window.addEventListener('hashchange', () => { const id = location.hash.slice(1); if (id && id !== PAGE) go(id); });
  go(location.hash.slice(1) || 'prac', false);
}
window.__H = () => H; if (location.hash === '#hand') window.__QNUDGE = 1;
// test hooks
window.PP = {okActs, judge, keyOf, classAgg, loadFlop, findNode, hidx, combo, row, version: () => VER, page: () => PAGE, drills: () => DRILLS,
  q: () => Q && {sp: Q.sp, fl: Q.fl, l: Q.n.l, b: Q.n.b, h: Q.h, i: Q.i}, ans: () => ANS, answer, go, nextQ,
  async ask(sp, fl, l, b, h) { GEN++; const F = await loadFlop(sp, fl), n = findNode(F, VER, l, b), i = hidx(n, h); Q = {sp, fl, F, n, i, h, key: qkey(sp, fl, l, b, h)}; ANS = null; renderDrill(); }};
boot();
})();
