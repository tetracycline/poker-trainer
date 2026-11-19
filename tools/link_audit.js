#!/usr/bin/env node
/* 行動線跳轉覆蓋檢查：每一格非棄牌須連到同一街或下一街，或「（無後續表）」且為真終點；
   非根表要有入口與上一步；列序固定六列；多人須對同一翻前線。
   用法：node tools/link_audit.js [--md out.md] [--review out.md] [--json out.json] [--quiet]
   結束碼：misses > 0 → 1。 */
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const args = process.argv.slice(2);
const opt = k => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const root = path.resolve(args[0] && !args[0].startsWith('--') ? args[0] : path.join(__dirname, '..'));
const QUIET = args.includes('--quiet');
const BT = '(A_high|KQ_high|mid_high|low|paired|mono)';
const BT_RE = new RegExp('-' + BT + '$');
const ND_PFX = ['3b_', '3c_', 'lmp_', 'iso_'];

function loadRenderer() {
  const app = { innerHTML: '', querySelectorAll: () => [], addEventListener() {} };
  const ctx = { console, __LINES_QA: true, location: { hash: '#lines' }, scrollTo() {}, addEventListener() {},
    document: { querySelector: () => app, querySelectorAll: () => [], getElementById: () => null } };
  ctx.window = ctx; vm.createContext(ctx);
  for (const n of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js']) {
    const f = path.join(root, n); if (!fs.existsSync(f)) continue;
    vm.runInContext(fs.readFileSync(f, 'utf8'), ctx, { filename: n });
  }
  if (!ctx.__linesQA) throw new Error('no QA interface');
  return { ctx, app };
}
function stOf(nd) {
  const k = String(nd || '').replace(/^(3b_|3c_|lmp_|iso_)/, '');
  return k.startsWith('r_') ? 2 : k.startsWith('t_') ? 1 : 0;
}
function ndPfx(nd) { return ND_PFX.find(p => String(nd).startsWith(p)) || ''; }
function strip(t) { return String(t || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim(); }
function actOf(text) { // classify PRIMARY action, never secondary navigation text
  const t=String(text||'').trim();
  if (/^棄/.test(t)) return 'fold';
  if (/^全下|^加注\s*全下/.test(t)) return 'allin';
  if (/^跟/.test(t)) return 'call';
  if (/^加注/.test(t)) return 'raise';
  if (/^過/.test(t)) return 'check';
  if (/^下注/.test(t)) return 'bet';
  return '?';
}
function parseSecs(html) {
  const parts = html.split(/<div class="sec"/).slice(1), secs = [];
  for (const p of parts) {
    const node = (p.match(/data-node="([^"]+)"/) || [])[1];
    const id = (p.match(/\bid="([^"]+)"/) || [])[1];
    if (!node) continue;
    const [sp, nd] = node.split('/');
    const title = strip((p.match(/<b class="ttl">([\s\S]*?)<\/b>/) || [])[1] || '');
    const nav = (p.match(/<p class="navln">([\s\S]*?)<\/p>/) || [])[1] || '';
    const navHrefs = [...nav.matchAll(/href="#([^"]+)"/g)].map(x => x[1]);
    const rows = [];
    for (const tr of p.matchAll(/<tr\b([^>]*)>([\s\S]*?)<\/tr>/g)) {
      const attr = tr[1] || '', body = tr[2] || '';
      if (/\bgrp\b/.test(attr) || /colspan=/.test(body)) continue;
      if (!/<td/.test(body)) continue;
      const lab = strip((body.match(/<th[^>]*>([\s\S]*?)<\/th>/) || [])[1] || '');
      const rid = (attr.match(/\bid="([^"]+)"/) || [])[1] || '';
      const bt = (rid.match(BT_RE) || [])[1] || '';
      const cells = [];
      for (const tm of body.matchAll(/<td\b([^>]*)>([\s\S]*?)<\/td>/g)) {
        const na = /\bna\b/.test(tm[1]);
        const text = strip(tm[2]);
        const href = (tm[2].match(/<a class="jmp" href="#([^"]+)"/) || [])[1] || '';
        const extras = [...tm[2].matchAll(/<a class="jmp sub" href="#([^"]+)"/g)].map(x => x[1]);
        const note = /（無後續表）/.test(tm[2]) || /（無後續表）/.test(text);
        const primary = strip((tm[2].match(/<a class="jmp" href="#[^"]+">([\s\S]*?)<\/a>/)||[])[1] ||
          tm[2].split(/<a class="jmp sub"|<small\b/)[0]);
        cells.push({ na, text, href, extras, note, primary, act: actOf(primary) });
      }
      rows.push({ lab, id: rid, bt, cells });
    }
    secs.push({ sp, nd, id, title, navHrefs, rows, st: stOf(nd), pfx: ndPfx(nd) });
  }
  return secs;
}

const { ctx, app } = loadRenderer();
const L = ctx.NLL, Q = ctx.__linesQA;
const allSecs = [], idMap = new Map();
for (const spot of L.spots) {
  Q.render(spot.id);
  for (const s of parseSecs(app.innerHTML)) {
    allSecs.push(s);
    if (s.id) idMap.set(s.id, s);
    for (const r of s.rows) if (r.id) idMap.set(r.id, s);
  }
}

const misses = [];
const ok = { linked: 0, noted: 0, fold: 0, allin: 0, na: 0, sub: 0 };
function baseId(href) { return String(href || '').replace(BT_RE, ''); }
function addMiss(kind, s, row, cell, detail) {
  misses.push({ kind, sp: s.sp, nd: s.nd, table: s.id, row: row && (row.lab || row.id), text: cell && cell.text, href: cell && cell.href, detail });
}
function preOf(title) {
  const m = String(title || '').match(/翻前：([^→]+)/);
  return m ? m[1].replace(/\s+/g, ' ').trim() : '';
}
function isThroughFace(href, tsec) {
  if (!tsec) return false;
  const item = itemById.get(tsec.id);
  const face = item ? ((item.key || '').split('|').pop() || '') : '';
  return !face || face === '對手過' || (/(^|、)對手過$/.test(face) && !/下注|加注/.test(face));
}

if (typeof Q.lineCatalog !== 'function' || typeof Q.nextEntries !== 'function')
  throw new Error('QA 沒有 lineCatalog/nextEntries');

const cats = {};
function catOf(sp) { return cats[sp] || (cats[sp] = Q.lineCatalog(sp)); }
const itemById = new Map();
for (const spot of L.spots) {
  for (const it of catOf(spot.id)) if (it && it.id) itemById.set(it.id, it);
}

const missingNext = new Map(); // key -> {sp,nd,key,verb,title,n}
function addMissing(s, verb, n) {
  const item = itemById.get(s.id);
  const k = s.sp + '/' + s.nd + ' ' + JSON.stringify(item && item.key) + ' ' + verb;
  if (!missingNext.has(k)) missingNext.set(k, { sp: s.sp, nd: s.nd, key: item && item.key, verb, title: s.title, n: 0 });
  missingNext.get(k).n += n;
}

for (const s of allSecs) {
  const item = itemById.get(s.id);
  for (const row of s.rows) for (const c of row.cells) {
    if (c.na || c.text === '—' || !c.text) { ok.na++; continue; }
    if (c.act === 'fold') { ok.fold++; continue; }
    if (c.act === 'allin') { ok.allin++; continue; }
    const hrefs = [];
    // parse from original? we only stored first href. Need all hrefs!
    // We'll re-parse below if needed. For now c.href is first.
    if (c.href) {
      const href = c.href, base = baseId(href);
      const tsec = idMap.get(href) || idMap.get(base);
      if (!tsec) { addMiss('錨點不存在', s, row, c, '#' + href); continue; }
      if (tsec.sp !== s.sp) addMiss('情境不對', s, row, c, '目標 ' + tsec.sp + '/' + tsec.nd);
      if (tsec.pfx !== s.pfx) addMiss('線前綴不對', s, row, c, '目標 ' + tsec.nd);
      if (preOf(s.title) && preOf(tsec.title) && preOf(s.title) !== preOf(tsec.title))
        addMiss('翻前線不對', s, row, c, '從「' + preOf(s.title) + '」鏈到「' + preOf(tsec.title) + '」');
      const verb = c.act === 'bet' || c.act === 'raise' ? (c.act === 'raise' ? '加注' : '下注') : c.act === 'check' ? '過' : c.act === 'call' ? '跟' : '';
      const nx = (item && verb && Q.nextEntries) ? Q.nextEntries(catOf(s.sp), item, verb) : [];
      const through = nx.filter(x => x.st === s.st + 1 && (typeof Q.isThrough === 'function' ? Q.isThrough(x) : isThroughFace(href, { id: x.id, key: x.key })));
      if (through.length && tsec.st === s.st) addMiss('主連結不是下一街', s, row, c, '有下一街表 ' + through[0].nd + ' 卻連到同一街 ' + tsec.nd);
      else if (tsec.st !== s.st && tsec.st !== s.st + 1) addMiss('街次不對', s, row, c, '目標 ' + tsec.nd + ' st=' + tsec.st);
      else ok.linked++;
      if (s.st < 2 && !through.length && c.act !== 'fold') addMissing(s, verb || c.act, 1);
    } else if (s.st < 2) {
      const verb = c.act === 'bet' ? '下注' : c.act === 'raise' ? '加注' : c.act === 'check' ? '過' : c.act === 'call' ? '跟' : '';
      const nx = (item && verb) ? Q.nextEntries(catOf(s.sp), item, verb) : [];
      const through = nx.filter(x => x.st === s.st + 1 && (typeof Q.isThrough === 'function' ? Q.isThrough(x) : true));
      if (through.length) addMiss('沉默無連結', s, row, c, '有下一街 ' + through.map(x => x.nd).join(',') + ' 卻沒主連結');
      else addMissing(s, verb || c.act, 1);
    }
  }
}

const inbound = new Set();
for (const s of allSecs) {
  for (const h of (s.navHrefs || [])) inbound.add(baseId(h));
  for (const row of s.rows) for (const c of row.cells) {
    if (c.href) inbound.add(baseId(c.href));
    for (const h of (c.extras || [])) inbound.add(baseId(h));
  }
}
const BT_ZH = ['9 以下低牌面', 'J/T 高面', 'K/Q 高面', 'A 高面', '成對面', '單色面'];
for (const s of allSecs) {
  const item = itemById.get(s.id);
  const prev = item ? Q.prevEntry(catOf(s.sp), item) : null;
  const hasPrevLink = (s.navHrefs || []).some(h => prev && baseId(h) === prev.id);
  if (prev && !hasPrevLink) addMiss('缺上一步', s, null, null, '應連到 #' + prev.id);
  if (prev && !inbound.has(s.id)) addMiss('無入口', s, null, null, '沒有任何格子或導覽連到此表');
  const labs = s.rows.map(r => r.lab).filter(l => BT_ZH.includes(l));
  if (labs.length) {
    if (labs.length % 6 !== 0) addMiss('列序', s, null, null, '牌面列數 ' + labs.length + '，不是 6 的倍數');
    for (let i = 0; i < labs.length; i++) {
      if (labs[i] !== BT_ZH[i % 6]) { addMiss('列序', s, null, null, '第 ' + (i + 1) + ' 列是「' + labs[i] + '」，應為「' + BT_ZH[i % 6] + '」'); break; }
    }
  }
}

// River reach via PRIMARY links on the rendered page
function walkRiverFrom(cell, s) {
  if (!cell || !cell.href) return { ok: false, at: s };
  let href = cell.href, cur = s, guard = 0;
  while (cur && cur.st < 2 && guard++ < 6) {
    const nxt = idMap.get(href) || idMap.get(baseId(href));
    if (!nxt || nxt.st !== cur.st + 1) return { ok: false, at: cur };
    cur = nxt;
    if (cur.st === 2) return { ok: true, at: cur };
    const bt = (href.match(BT_RE) || [])[1];
    const row = (bt && cur.rows.find(r => r.bt === bt)) || cur.rows[0];
    if (!row) return { ok: false, at: cur };
    const nextCell = row.cells.find(c => c.href && c.act !== 'fold') || row.cells.find(c => c.href);
    if (!nextCell || !nextCell.href) return { ok: false, at: cur };
    href = nextCell.href;
  }
  return { ok: !!(cur && cur.st === 2), at: cur };
}

let cont = 0, reachR = 0, noR = 0;
// Immutable cell-level gap evidence. Never infer reach from a texture-only match.
const unresolvedCells = [];
function recordRiverGap(s, row, c, ri, ci, reason, at, chain) {
  const item = itemById.get(s.id);
  unresolvedCells.push({
    id: [s.id, row.id || ri, ci].join('::'), sp: s.sp, nd: s.nd,
    stage: s.st, table: s.id, row: row.id, rowIndex: ri,
    boardTexture: row.bt, column: ci, action: c.act, text: c.text,
    href: c.href || null, title: s.title,
    preflop: s.title.split('→')[0].trim(), history: item && item.key,
    breakReason: reason, blockedAt: at && { sp: at.sp, nd: at.nd, table: at.id },
    linkChain: chain || [s.id], evidence: 'UNSOLVED'
  });
}
const noREx = new Map();
for (const s of allSecs.filter(x => x.st < 2)) {
  for (const [ri, row] of s.rows.entries()) for (const [ci, c] of row.cells.entries()) {
    if (c.na || c.act === 'fold' || c.act === 'allin' || !c.text || c.text === '—') continue;
    if (!c.href && s.st < 2) { cont++; noR++;
      recordRiverGap(s, row, c, ri, ci, 'NO_PRIMARY_LINK', s, [s.id]); 
      const k = s.sp + '/' + s.nd + ' ' + (itemById.get(s.id) || {}).key + ' ' + c.act;
      if (!noREx.has(k)) noREx.set(k, { title: s.title, n: 0, why: '格子沒有下一街主連結' });
      noREx.get(k).n++;
      continue;
    }
    if (!c.href) continue;
    const tsec = idMap.get(c.href) || idMap.get(baseId(c.href));
    if (!tsec || tsec.st !== s.st + 1) continue; // only count cells whose primary is next street
    cont++;
    const w = walkRiverFrom(c, s);
    if (w.ok) reachR++;
    else {
      noR++;
      recordRiverGap(s, row, c, ri, ci,
        w.at && w.at.st === 1 ? 'NO_TURN_TO_RIVER_LINK' : 'NOT_NEXT_STREET',
        w.at, [s.id, w.at && w.at.id].filter(Boolean));
      const item = itemById.get(s.id);
      const k = s.sp + '/' + s.nd + ' ' + JSON.stringify(item && item.key) + ' ' + c.act;
      if (!noREx.has(k)) noREx.set(k, { title: s.title, n: 0, why: w.at ? ('走到 ' + w.at.sp + '/' + w.at.nd + ' 之後沒有河牌主連結') : '中斷' });
      noREx.get(k).n++;
    }
  }
}

if (unresolvedCells.length !== noR || noR + reachR !== cont)
  throw new Error('Cell-level river-gap ledger not aligned with the coverage denominator');
const counts = {
  tables: allSecs.length,
  flop: allSecs.filter(s => s.st === 0).length,
  turn: allSecs.filter(s => s.st === 1).length,
  river: allSecs.filter(s => s.st === 2).length,
  linked: ok.linked, fold: ok.fold, allin: ok.allin, na: ok.na,
  misses: misses.length,
  continuing: cont, reachRiver: reachR, noRiver: noR,
  riverShare: cont ? Math.round(reachR / cont * 1000) / 10 : 0
};
const byKind = {};
for (const m of misses) byKind[m.kind] = (byKind[m.kind] || 0) + 1;

const HCO = ['S', 'TPG', 'TPW', 'MID', 'DRAW', 'WDRAW', 'AIR'];
const HNAME = { S: '兩對+', TPG: '頂對好', TPW: '頂對弱', MID: '中小對', DRAW: '強聽', WDRAW: '弱聽', AIR: '空氣' };
let reachShown = 0, reachRemoved = 0, reachRemovedCols = 0;
const tfirstS = { shown: 0 };
for (const spot of L.spots) {
  if (spot.id === 'mw') continue;
  for (const nd of Q.nodesOf(spot.id)) {
    if (!Q.nodeVisible(spot.id, nd)) continue;
    const lns = Q.TITLES.lines(spot.id, nd);
    for (const ln of lns) {
      const shownH = new Set(), dataH = new Set();
      for (const h of HCO) for (const zh of BT_ZH) {
        const r = L.rows.find(x => x.sp === spot.id && x.nd === nd && !x.x && x.hc.includes(h) && (x.cl === zh || String(x.cl || '').endsWith('・' + zh)));
        if (!r) continue;
        dataH.add(h);
        if (Q.rowReached(r, h, ln)) { reachShown++; shownH.add(h); if (spot.id === 'bb' && nd === 't_first' && h === 'S') tfirstS.shown++; }
        else reachRemoved++;
      }
      for (const h of dataH) if (!shownH.has(h)) reachRemovedCols++;
    }
  }
}
counts.reachShown = reachShown;
counts.reachRemoved = reachRemoved;
counts.reachRemovedCols = reachRemovedCols;
counts.tfirstTwoPairCells = tfirstS.shown;

function mdAudit() {
  const o = [];
  o.push('# NL2 行動線跳轉覆蓋檢查');
  o.push('');
  o.push('檢查對象：https://tetracycline.github.io/poker-trainer/nl2.html#lines');
  o.push('規則：格子的主連結必須是「這一步被跟或過完之後」的下一街同一情境、同一條翻前線；同一街被加注／面對下注走小連結。棄牌不必有連結。不把缺下一街的格子標成終點。列序固定六列。');
  o.push('');
  o.push('## 計數');
  o.push('');
  o.push('- 表：' + counts.tables + '（翻 ' + counts.flop + '、轉 ' + counts.turn + '、河 ' + counts.river + '）');
  o.push('- 有主連結且通過檢查：' + counts.linked);
  o.push('- 棄牌：' + counts.fold);
  o.push('- 走不到的「—」：' + counts.na);
  o.push('- **misses：' + counts.misses + '**');
  o.push('');
  o.push('## 走到河牌的比例（沿主連結）');
  o.push('');
  o.push('- 翻／轉會繼續且主連結指向下一街的格子：' + counts.continuing);
  o.push('- 沿主連結走到河牌表：' + counts.reachRiver + '（' + counts.riverShare + '%）');
  o.push('- 走不到河牌：' + counts.noRiver);
  o.push('');
  if (missingNext.size || noREx.size) {
    o.push('### 資料裡沒有「被跟／過完」下一街表的節點（不是終點，只是缺表）');
    o.push('');
    const rows = [...missingNext.values()].sort((a, b) => b.n - a.n);
    for (const r of rows.slice(0, 80)) {
      o.push('- ' + r.sp + '/' + r.nd + ' key=' + JSON.stringify(r.key) + ' 動作「' + r.verb + '」：缺下一街表（' + r.n + ' 格）。' + (r.title ? '表題：' + r.title : ''));
    }
    if (rows.length > 80) o.push('- …另有 ' + (rows.length - 80) + ' 種節點');
    o.push('');
  }
  o.push('## 行動線可達性（邏輯）');
  o.push('');
  o.push('混合策略：f(a) 為最高，或 f(a)≥40% 且 f(a)≥70%×最高頻率。頻率鍵保留實際尺寸（b33/b50/b66/b75/b100/b150），比對時再歸成小注／大注。');
  o.push('');
  o.push('- 通過可達性、實際顯示的格：' + counts.reachShown);
  o.push('- 資料有列但因走不到而拿掉的格：' + counts.reachRemoved);
  o.push('- 因此整欄拿掉的牌型：' + counts.reachRemovedCols);
  o.push('  目前 BB 轉牌先行動兩對+ 顯示 ' + counts.tfirstTwoPairCells + ' 格（轉牌才提升）。');
  if (Object.keys(byKind).length) {
    o.push('');
    o.push('分類：' + Object.entries(byKind).map(([k, n]) => k + ' ' + n).join('、'));
  }
  o.push('');
  if (!misses.length) o.push('結論：0 misses。主連結指向下一街、翻前線一致、列序正確。走不到河牌的格子列在上面的缺表清單，不當成終點。');
  else {
    o.push('## Misses');
    o.push('');
    for (const m of misses.slice(0, 200)) {
      o.push('- [' + m.kind + '] ' + m.sp + '/' + m.nd + ' ' + (m.row || '') + ' 「' + (m.text || '') + '」 ' + (m.href ? '#' + m.href : '') + ' — ' + m.detail);
    }
    if (misses.length > 200) o.push('- …另有 ' + (misses.length - 200) + ' 筆');
  }
  o.push('');
  return o.join('\n');
}

function actLabel(text) {
  return String(text || '').replace(/若[^\s]*→/g, '').replace(/低把握/g, '').replace(/\bGTO\b|剝削/g, '').replace(/\s+/g, ' ').trim();
}
function firstPrimary(sec, rowBt, pred) {
  if (!sec) return null;
  for (const row of sec.rows) {
    if (rowBt && row.bt !== rowBt) continue;
    for (const c of row.cells) {
      if (!c.href || c.act === 'fold') continue;
      const t = idMap.get(c.href) || idMap.get(baseId(c.href));
      if (pred && !pred(t, c, row)) continue;
      return { href: c.href, act: c.text, row: row.lab, bt: row.bt, target: t, cell: c };
    }
  }
  return null;
}
function toNext(t, from) { return t && from && t.st === from.st + 1; }
function rowId(sec, bt) {
  if (!sec) return '';
  const r = sec.rows.find(x => x.bt === bt);
  return r && r.id ? r.id : (sec.id + (bt ? '-' + bt : ''));
}

function samplePaths() {
  const out = [];
  function push(rec) { if (rec && rec.flop && rec.turn && rec.river) out.push(rec); }
  function chain(spot, flopBt, tag) {
    const flops = allSecs.filter(s => s.st === 0 && s.sp === spot);
    for (const flop of flops) {
      const cell = firstPrimary(flop, flopBt, t => t && t.st === 1) || firstPrimary(flop, null, t => t && t.st === 1);
      if (!cell || !cell.target || cell.target.st !== 1) continue;
      const turn = cell.target;
      const tCell = firstPrimary(turn, flopBt, t => t && t.st === 2) || firstPrimary(turn, cell.bt, t => t && t.st === 2) || firstPrimary(turn, null, t => t && t.st === 2);
      if (!tCell || !tCell.target || tCell.target.st !== 2) continue;
      const river = tCell.target;
      push({
        tag: tag, spot: spot,
        flop: flop, flopRow: (flop.rows.find(r => r.bt === (flopBt || cell.bt)) || {}).lab || cell.row, flopAct: actLabel(cell.act), flopHref: cell.href,
        flopStart: rowId(flop, flopBt || cell.bt),
        turn: turn, turnRow: (turn.rows.find(r => r.bt === (tCell.bt || flopBt)) || {}).lab || tCell.row, turnAct: tCell.act, turnHref: tCell.href,
        turnStart: rowId(turn, tCell.bt || flopBt || cell.bt),
        river: river, riverRow: (river.rows.find(r => r.bt === (tCell.bt || flopBt)) || {}).lab || '', riverHref: rowId(river, tCell.bt || flopBt)
      });
      return;
    }
  }
  function boardChange(spot, flopBt, turnBt, tag) {
    const flops = allSecs.filter(s => s.st === 0 && s.sp === spot);
    for (const flop of flops) {
      const cell = firstPrimary(flop, flopBt, t => t && t.st === 1);
      if (!cell || !cell.target || cell.target.st !== 1) continue;
      const turn = cell.target;
      const tRow = turn.rows.find(r => r.bt === turnBt);
      if (!tRow) continue;
      const tCell = tRow.cells.find(c => c.href && c.act !== 'fold');
      const river = tCell ? (idMap.get(tCell.href) || idMap.get(baseId(tCell.href))) : null;
      push({
        tag: tag, spot: spot, note: tag,
        flop: flop, flopRow: (flop.rows.find(r => r.bt === flopBt) || {}).lab, flopAct: cell.act, flopHref: cell.href,
        flopStart: rowId(flop, flopBt),
        turn: turn, turnRow: tRow.lab, turnAct: tCell ? tCell.text : '', turnHref: tCell ? tCell.href : rowId(turn, turnBt),
        turnStart: rowId(turn, turnBt),
        river: river && river.st === 2 ? river : null,
        riverRow: river && river.st === 2 ? ((river.rows.find(r => r.bt === turnBt) || {}).lab || '') : '',
        riverHref: river && river.st === 2 ? (tCell && BT_RE.test(tCell.href) ? tCell.href : rowId(river, turnBt)) : ''
      });
      return;
    }
  }
  chain('ipfr', 'KQ_high', '同質地 K/Q');
  chain('ipfr', 'A_high', '同質地 A');
  chain('bb', 'KQ_high', 'BB 同質地 K/Q');
  boardChange('ipfr', 'KQ_high', 'A_high', 'K72→A（K/Q 高面轉 A，改讀 A 高面）');
  boardChange('ipfr', 'KQ_high', 'paired', 'K72→7（K/Q 高面轉成對，改讀成對面）');
  boardChange('ipfr', 'low', 'mid_high', '862→T（9 以下低牌面轉 T，改讀 J/T 高面）');
  boardChange('bb', 'KQ_high', 'A_high', 'BB K72→A');
  boardChange('ipfr', 'KQ_high', 'mono', 'K 高翻牌轉同花完成，改讀單色面');
  chain('bb', 'low', 'BB 低牌面同質地');
  chain('ipfr', 'paired', '成對面同質地');
  const seen = new Set(), pick = [];
  for (const p of out) {
    const k = [p.tag, p.flop && p.flop.id, p.turn && p.turn.id, p.river && p.river.id, p.flopHref, p.turnHref].join('|');
    if (seen.has(k)) continue;
    seen.add(k); pick.push(p);
    if (pick.length >= 10) break;
  }
  return pick;
}

function mdReview() {
  const o = [];
  o.push('# NL2 行動線頁面說明（給外部檢查）');
  o.push('');
  o.push('頁面：https://tetracycline.github.io/poker-trainer/nl2.html#lines');
  o.push('');
  o.push('## 結構');
  o.push('');
  o.push('這是 NL2 行動線對照表。格子的主連結（動作本身）是「這一步被跟或過完之後」的下一街表，對得到就停在同一種牌面列。同一街若還有「被加注／面對下注」的表，格子旁邊有小連結「若被加注→」「若面對下注→」。後面的表有「↑ 上一步」。多人必須對在同一條翻前線。轉牌牌面若改變（K 高翻牌轉 A、轉出對子、同花完成），請改讀下一張表對應的新列。');
  o.push('');
  o.push('橫列固定六列，順序是：9 以下低牌面、J/T 高面、K/Q 高面、A 高面、成對面、單色面。');
  o.push('');
  o.push('## 十條翻→轉→河樣本路徑（從實際渲染頁沿主連結收集，含牌面改變）');
  o.push('');
  const paths = samplePaths();
  paths.forEach((p, i) => {
    o.push('### ' + (i + 1) + '. ' + (p.tag || p.spot));
    o.push('');
    o.push('- 翻牌表：' + p.flop.title);
    o.push('  打開：https://tetracycline.github.io/poker-trainer/nl2.html#' + (p.flopStart || p.flop.id));
    o.push('  列「' + (p.flopRow || '') + '」動作「' + actLabel(p.flopAct || '') + '」');
    if (p.flopHref) o.push('  主連結（被跟或過完後的轉牌）→ https://tetracycline.github.io/poker-trainer/nl2.html#' + p.flopHref);
    if (p.turn) {
      o.push('- 轉牌表：' + p.turn.title);
      o.push('  打開：https://tetracycline.github.io/poker-trainer/nl2.html#' + (p.turnStart || p.turn.id));
      o.push('  列「' + (p.turnRow || '') + '」動作「' + actLabel(p.turnAct || '') + '」');
      if (p.turnHref) o.push('  主連結（被跟或過完後的河牌）→ https://tetracycline.github.io/poker-trainer/nl2.html#' + p.turnHref);
    }
    if (p.river) {
      o.push('- 河牌表：' + p.river.title);
      o.push('  打開：https://tetracycline.github.io/poker-trainer/nl2.html#' + (p.riverHref || p.river.id));
      o.push('  列「' + (p.riverRow || '') + '」');
    } else {
      o.push('- 河牌：這條樣本的轉牌主連結在資料裡沒有「被跟／過完」的河牌表（見 LINK_AUDIT 缺表清單）。');
    }
    if (p.note) o.push('- 說明：' + p.note);
    o.push('');
  });
  if (paths.length < 10) o.push('（只收集到 ' + paths.length + ' 條樣本路徑。）');
  o.push('');
  return o.join('\n');
}

const auditText = mdAudit();
const reviewText = mdReview();
const mdPath = opt('--md'), reviewPath = opt('--review'), jsonPath = opt('--json');
if (mdPath) fs.writeFileSync(mdPath, auditText);
if (reviewPath) fs.writeFileSync(reviewPath, reviewText);
if (jsonPath) fs.writeFileSync(jsonPath, JSON.stringify({ counts, byKind, misses: misses, missingNext: [...missingNext.values()].sort((a,b)=>b.n-a.n), noRiverExamples: [...noREx.values()].sort((a,b)=>b.n-a.n),
  unresolvedCells }, null, 2));
if (!QUIET) {
  console.log(JSON.stringify(counts));
  if (misses.length) console.log('misses by kind', byKind);
}
if (!mdPath && !QUIET) console.log(auditText);
process.exit(misses.length ? 1 : 0);