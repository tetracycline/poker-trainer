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
  for (const n of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2.js']) {
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
function actOf(text) {
  if (/棄/.test(text)) return 'fold';
  if (/跟/.test(text)) return 'call';
  if (/加注|全下/.test(text)) return 'raise';
  if (/過/.test(text)) return 'check';
  if (/下注/.test(text)) return 'bet';
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
        const href = (tm[2].match(/href="#([^"]+)"/) || [])[1] || '';
        const note = /（無後續表）/.test(tm[2]) || /（無後續表）/.test(text);
        cells.push({ na, text, href, note, act: actOf(text) });
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
const ok = { linked: 0, noted: 0, fold: 0, na: 0 };
function baseId(href) { return String(href || '').replace(BT_RE, ''); }
function addMiss(kind, s, row, cell, detail) {
  misses.push({ kind, sp: s.sp, nd: s.nd, table: s.id, row: row && (row.lab || row.id), text: cell && cell.text, href: cell && cell.href, detail });
}
function verbOfAct(act) {
  return act === 'call' ? '跟' : act === 'raise' ? '加注' : act === 'check' ? '過' : act === 'bet' ? '下注' : '';
}
function preOf(title) {
  const m = String(title || '').match(/翻前：([^→]+)/);
  return m ? m[1].replace(/\s+/g, ' ').trim() : '';
}

if (typeof Q.lineCatalog !== 'function' || typeof Q.nextEntries !== 'function' || typeof Q.prevEntry !== 'function')
  throw new Error('QA 沒有 lineCatalog/nextEntries/prevEntry（應掛在 __linesQA）');

const cats = {};
function catOf(sp) { return cats[sp] || (cats[sp] = Q.lineCatalog(sp)); }
const itemById = new Map();
for (const spot of L.spots) {
  for (const it of catOf(spot.id)) if (it && it.id) itemById.set(it.id, it);
}

for (const s of allSecs) {
  const item = itemById.get(s.id);
  const cat = catOf(s.sp);
  for (const row of s.rows) for (const c of row.cells) {
    if (c.na || c.text === '—' || !c.text) { ok.na++; continue; }
    if (c.act === 'fold') { ok.fold++; continue; }
    const verb = verbOfAct(c.act);
    const nx = (item && verb) ? Q.nextEntries(cat, item, verb) : [];
    if (c.href && c.note) addMiss('又連又標', s, row, c, '有連結卻仍標「無後續表」');
    if (c.note && !c.href) {
      if (nx.length) addMiss('假無後續表', s, row, c, '資料裡有同一街或下一街表：' + nx.map(x => x.nd).join(','));
      else ok.noted++;
      continue;
    }
    if (c.href) {
      const href = c.href, base = baseId(href), hasRow = BT_RE.test(href);
      const tsec = idMap.get(href) || idMap.get(base);
      if (!tsec) { addMiss('錨點不存在', s, row, c, '#' + href); continue; }
      if (tsec.st !== s.st && tsec.st !== s.st + 1) { addMiss('街次不對', s, row, c, '目標 ' + tsec.sp + '/' + tsec.nd + ' st=' + tsec.st); continue; }
      if (tsec.sp !== s.sp) { addMiss('情境不對', s, row, c, '目標 ' + tsec.sp + '/' + tsec.nd); continue; }
      if (tsec.pfx !== s.pfx) addMiss('線前綴不對', s, row, c, '目標 ' + tsec.nd + ' pfx=' + tsec.pfx);
      const tItem = itemById.get(tsec.id);
      if (s.sp === 'mw' && item && tItem && item.pf && tItem.pf && item.pf !== tItem.pf)
        addMiss('翻前線不對', s, row, c, '從「' + String(item.pf).replace(/\t/g, ' ') + '」鏈到「' + String(tItem.pf).replace(/\t/g, ' ') + '」');
      if (hasRow) {
        const hasBt = tsec.rows.some(r => r.id === href) || idMap.has(href);
        if (!hasBt) { addMiss('牌面列錨點不存在', s, row, c, '#' + href + '（表在，列 id 沒有）'); continue; }
      }
      if (hasRow && row.bt && href.endsWith('-' + row.bt) === false) addMiss('牌面列不對', s, row, c, '從 ' + row.bt + ' 鏈到 ' + href);
      else ok.linked++;
    } else {
      addMiss('沉默無連結', s, row, c, '非棄牌且沒有連結，也沒有「（無後續表）」');
    }
  }
}

const inbound = new Set();
for (const s of allSecs) {
  for (const h of (s.navHrefs || [])) inbound.add(baseId(h));
  for (const row of s.rows) for (const c of row.cells) if (c.href) inbound.add(baseId(c.href));
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

const counts = {
  tables: allSecs.length,
  flop: allSecs.filter(s => s.st === 0).length,
  turn: allSecs.filter(s => s.st === 1).length,
  river: allSecs.filter(s => s.st === 2).length,
  linked: ok.linked, noted: ok.noted, fold: ok.fold, na: ok.na,
  misses: misses.length
};
const byKind = {};
for (const m of misses) byKind[m.kind] = (byKind[m.kind] || 0) + 1;

const HCO = ['S', 'TPG', 'TPW', 'MID', 'DRAW', 'WDRAW', 'AIR'];
const HNAME = { S: '兩對+', TPG: '頂對好', TPW: '頂對弱', MID: '中小對', DRAW: '強聽', WDRAW: '弱聽', AIR: '空氣' };
let reachShown = 0, reachRemoved = 0, reachRemovedCols = 0;
const tfirstS = { shown: 0, cells: [] };
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
        if (Q.rowReached(r, h, ln)) {
          reachShown++;
          shownH.add(h);
          if (spot.id === 'bb' && nd === 't_first' && h === 'S') { tfirstS.shown++; tfirstS.cells.push(zh); }
        } else {
          reachRemoved++;
        }
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
  o.push('規則：每一格非棄牌動作，必須連到同一街後續表或下一街同一情境、同一條線的表（有牌面列就停在同一列），或明確標「（無後續表）」且資料裡確實沒有後續表。棄牌不必有下一步。每張有上一步的表必須有「↑ 上一步」，且非根表必須有入口連結。橫列順序固定為 9 以下低牌面、J/T 高面、K/Q 高面、A 高面、成對面、單色面。多人連結必須落在同一條翻前線。');
  o.push('');
  o.push('## 計數');
  o.push('');
  o.push('- 表：' + counts.tables + '（翻 ' + counts.flop + '、轉 ' + counts.turn + '、河 ' + counts.river + '）');
  o.push('- 有後續連結（含同一街）：' + counts.linked);
  o.push('- 標「（無後續表）」且確為終點：' + counts.noted);
  o.push('- 棄牌（不要求連結）：' + counts.fold);
  o.push('- 走不到的「—」：' + counts.na);
  o.push('- **misses：' + counts.misses + '**');
  o.push('');
  o.push('## 行動線可達性（邏輯）');
  o.push('');
  o.push('規則：這一格的牌型，必須能用「你先前每一個決定」走到這條線。混合策略：頻率差很多時只跟最高頻率的動作；行動 a 走進這條線 iff f(a) 為最高，或 f(a)≥40% 且 f(a)≥70%×最高頻率。沒有頻率時用主答案；有 ≈ 且無頻率時兩個動作都算。兩對／頂對以上變成空氣／弱聽的極稀有轉壞不算。「最高張 9 以下／T 以上」例外列已併入六列，不擋基本格。牌型可逐街改變（轉牌／河牌才提升的手，用當街牌面分類）。牌面列還要跟「翻牌質地＋各街最高張」一致：最高張仍是 9 以下時，不能寫進 J/T、K/Q、A 高面；最高張已是 T 以上時，不能寫進 9 以下低牌面。');
  o.push('');
  o.push('- 通過可達性、實際顯示的格：' + counts.reachShown);
  o.push('- 資料有列但因走不到而拿掉的格：' + counts.reachRemoved);
  o.push('- 因此整欄拿掉的牌型（某一條線上該牌型完全走不到）：' + counts.reachRemovedCols);
  o.push('- 例：BB 過牌－面對 c-bet 跟注－轉牌先行動。翻牌兩對+ 若幾乎都加注，不會以翻牌兩對+ 走進這條線；表上若還有兩對+，只代表轉牌才從頂對／中對等提升上來的手，或翻牌頻率接近混合、跟注也算走進。');
  o.push('  目前該線兩對+ 顯示 ' + counts.tfirstTwoPairCells + ' 格。');
  if (Object.keys(byKind).length) {
    o.push('');
    o.push('分類：' + Object.entries(byKind).map(([k, n]) => k + ' ' + n).join('、'));
  }
  o.push('');
  if (!misses.length) o.push('結論：0 misses。每個會繼續的動作要不是連到正確的同一街／下一街錨點，就是標了真正的「（無後續表）」；每張非根表有入口與上一步；列序正確。');
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

function firstHref(sec, rowBt, pred) {
  if (!sec) return null;
  for (const row of sec.rows) {
    if (rowBt && row.bt !== rowBt) continue;
    for (const c of row.cells) if (c.href) {
      const t = secByHref(c.href);
      if (pred && !pred(t, c, row)) continue;
      return { href: c.href, act: c.text, row: row.lab, bt: row.bt, id: row.id, target: t };
    }
  }
  return null;
}
function toTurn(t) { return t && t.st === 1; }
function toRiver(t) { return t && t.st === 2; }
function secByHref(href) { return href ? (idMap.get(href) || idMap.get(baseId(href))) : null; }
function rowId(sec, bt) {
  if (!sec) return '';
  const r = sec.rows.find(x => x.bt === bt);
  return r && r.id ? r.id : (sec.id + (bt ? '-' + bt : ''));
}
function viaNav(sec, wantSt) {
  if (!sec) return null;
  for (const h of (sec.navHrefs || [])) {
    const t = secByHref(h);
    if (t && t.st === wantSt) return t;
  }
  return null;
}

function samplePaths() {
  const out = [];
  function push(rec) { if (rec && rec.flop && rec.turn) out.push(rec); }
  function chain(spotPref, flopBt, turnBt, riverBt, tag) {
    const flops = allSecs.filter(s => s.st === 0 && (!spotPref || s.sp === spotPref));
    for (const flop of flops) {
      const cell = firstHref(flop, flopBt, toTurn) || firstHref(flop, flopBt) || firstHref(flop, null, toTurn) || firstHref(flop, null);
      if (!cell || !cell.href) continue;
      const turn = secByHref(cell.href);
      if (!turn || turn.st < 1) continue;
      const tCell = firstHref(turn, turnBt, toRiver) || firstHref(turn, null, toRiver) || firstHref(turn, turnBt) || firstHref(turn, null);
      const rSec = (tCell && tCell.target && tCell.target.st === 2 && tCell.target) || viaNav(turn, 2);
      if (!rSec || rSec.st !== 2) continue;
      push({
        tag: tag, spot: flop.sp,
        flop: flop, flopRow: ((flop.rows.find(r => r.bt === flopBt) || {}).lab) || cell.row, flopAct: cell.act,
        flopHref: rowId(turn, flopBt || cell.bt),
        turn: turn, turnRow: ((turn.rows.find(r => r.bt === (turnBt || flopBt)) || {}).lab) || (tCell && tCell.row) || '',
        turnAct: (tCell && tCell.act) || '',
        turnHref: rSec && rSec.st === 2 ? rowId(rSec, turnBt || flopBt) : rowId(turn, turnBt || flopBt),
        river: rSec && rSec.st === 2 ? rSec : null,
        riverRow: rSec && rSec.st === 2 ? (((rSec.rows.find(r => r.bt === (riverBt || turnBt || flopBt)) || {}).lab) || '') : '',
        riverHref: rSec && rSec.st === 2 ? rowId(rSec, riverBt || turnBt || flopBt) : ''
      });
      if (out.filter(x => x.tag === tag).length >= 1) return;
    }
  }
  function boardChange(spot, flopBt, turnBt, riverBt, tag) {
    const flop = allSecs.find(s => s.sp === spot && s.st === 0 && firstHref(s, flopBt, toTurn));
    if (!flop) return;
    const cell = firstHref(flop, flopBt, toTurn);
    const turn = cell && (cell.target || secByHref(cell.href));
    if (!turn || turn.st !== 1) return;
    const tCell = firstHref(turn, turnBt) || firstHref(turn, flopBt) || firstHref(turn, null);
    const rSec = (tCell && tCell.target && tCell.target.st === 2 && tCell.target) || viaNav(turn, 2);
    push({
      tag: tag, spot: spot,
      flop: flop, flopRow: ((flop.rows.find(r => r.bt === flopBt) || {}).lab), flopAct: cell.act,
      flopHref: rowId(turn, flopBt),
      turn: turn, turnRow: ((turn.rows.find(r => r.bt === turnBt) || {}).lab), turnAct: (tCell && tCell.act) || '',
      turnHref: rowId(turn, turnBt),
      river: rSec && rSec.st === 2 ? rSec : null,
      riverRow: rSec && rSec.st === 2 ? (((rSec.rows.find(r => r.bt === riverBt) || rSec.rows.find(r => r.bt === turnBt) || {}).lab) || '') : '',
      riverHref: rSec && rSec.st === 2 ? rowId(rSec, riverBt) : '',
      note: tag
    });
  }
  chain('ipfr', 'KQ_high', 'KQ_high', 'KQ_high', '同質地 K/Q');
  chain('ipfr', 'A_high', 'A_high', 'A_high', '同質地 A');
  chain('bb', 'KQ_high', 'KQ_high', 'KQ_high', 'BB 同質地 K/Q');
  boardChange('ipfr', 'KQ_high', 'A_high', 'A_high', 'K72→A（K/Q 高面轉 A，改讀 A 高面）');
  boardChange('ipfr', 'KQ_high', 'paired', 'paired', 'K72→7（K/Q 高面轉成對，改讀成對面）');
  boardChange('ipfr', 'low', 'mid_high', 'mid_high', '862→T（9 以下低牌面轉 T，改讀 J/T 高面）');
  boardChange('bb', 'KQ_high', 'A_high', 'A_high', 'BB K72→A');
  boardChange('ipfr', 'KQ_high', 'mono', 'mono', 'K 高翻牌轉同花完成，改讀單色面');
  chain('bb', 'low', 'low', 'low', 'BB 低牌面同質地');
  chain('ipfr', 'paired', 'paired', 'paired', '成對面同質地');
  const ffirst = allSecs.find(s => s.sp === 'bb' && s.nd === 'f_first');
  if (ffirst) {
    let cell = null, row = null;
    for (const r of ffirst.rows) {
      const c = r.cells.find(x => x.act === 'check' && x.href);
      if (c) { cell = c; row = r; break; }
    }
    const nxt = cell && secByHref(cell.href);
    if (nxt) {
      const tCell = firstHref(nxt, row && row.bt) || firstHref(nxt, null);
      const turn = tCell && tCell.href ? secByHref(tCell.href) : null;
      const rCell = turn && (firstHref(turn, row && row.bt) || firstHref(turn, null));
      const river = rCell && rCell.href ? secByHref(rCell.href) : null;
      const rSec = (turn && turn.st === 2) ? turn : (river && river.st === 2 ? river : null);
      push({
        tag: 'BB 翻牌過→同一街面對 c-bet→轉→河',
        spot: 'bb',
        flop: ffirst, flopRow: row && row.lab, flopAct: cell && cell.text, flopHref: cell && cell.href,
        turn: nxt, turnRow: ((nxt.rows.find(r => row && r.bt === row.bt) || {}).lab), turnAct: (tCell && tCell.act) || '',
        turnHref: (tCell && tCell.href) || nxt.id,
        river: rSec, riverRow: rSec ? (((rSec.rows.find(r => row && r.bt === row.bt) || {}).lab) || '') : '',
        riverHref: (rCell && rCell.href) || (rSec && rSec.id) || '',
        note: '第一步是同一街 f_vs_cbet，不是下一街'
      });
    }
  }
  const seen = new Set(), pick = [];
  for (const p of out) {
    const k = [p.tag, p.spot, p.flop && p.flop.id, p.turn && p.turn.id, p.river && p.river.id, p.flopHref, p.turnHref].join('|');
    if (seen.has(k)) continue;
    seen.add(k);
    pick.push(p);
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
  o.push('這是 NL2 行動線對照表。上方按鈕切換翻前情境（例如你開池有位置、BB 防守）。每個情境下面依行動線排表，一條線一張表：先翻牌，再轉牌，再河牌。同一街若還有「面對下注／被加注」的表，格子會連過去。');
  o.push('');
  o.push('每張表的標題是這條線從翻前到這一街的行動，金色粗體是「你」的動作。表的橫列固定六列，順序是：');
  o.push('');
  o.push('1. 9 以下低牌面');
  o.push('2. J/T 高面');
  o.push('3. K/Q 高面');
  o.push('4. A 高面');
  o.push('5. 成對面');
  o.push('6. 單色面');
  o.push('');
  o.push('欄是牌型（兩對+、頂對好…）。走不到或沒答案是「—」。格子只寫動作和「GTO」或「剝削」，下注／加注會標尺寸；面對下注且資料有尺寸分檔時，會寫「面對小注／≥¾／超池」。不要再看到「最高張 9 以下」或「最高張 T 以上」另開成一列，那些已併進上面六列。');
  o.push('');
  o.push('點格子裡的動作（或表上的「→ 下一步」）會跳到同一街後續表或下一街同一條線的表，對得到就停在同一種牌面列。轉牌牌面若改變（K 高翻牌轉 A、轉出對子、同花完成），請改讀下一張表對應的新列，不要停在出發列。多人必須對在同一條翻前線。後面的表有「↑ 上一步」。棄牌沒有下一步。若資料裡沒有同一街或下一街的表，格子會寫「（無後續表）」，不該出現默默沒連結、也沒說明的情況，也不該在還有後續表時寫這個標示。');
  o.push('');
  o.push('錨點格式：#ln-{情境}-{節點}-{hash}，牌面列再加 -low、-mid_high、-KQ_high、-A_high、-paired、-mono。');
  o.push('');
  o.push('## 十條翻→轉→河樣本路徑（含牌面改變）');
  o.push('');
  o.push('請實際打開連結，確認會滾到正確的表與列，標題行動線接得上。同質地路徑的列名應與出發列相同；標了「K72→A」等的路徑，轉牌／河牌應讀新列。');
  o.push('');
  const paths = samplePaths();
  paths.forEach((p, i) => {
    o.push('### ' + (i + 1) + '. ' + (p.tag || p.spot));
    o.push('');
    o.push('- 翻牌：' + p.flop.title);
    o.push('  列「' + (p.flopRow || '') + '」動作「' + (p.flopAct || '') + '」');
    if (p.flopHref) o.push('  → https://tetracycline.github.io/poker-trainer/nl2.html#' + p.flopHref);
    if (p.turn) {
      o.push('- 轉牌：' + p.turn.title);
      o.push('  列「' + (p.turnRow || '') + '」動作「' + (p.turnAct || '') + '」');
      if (p.turnHref) o.push('  → https://tetracycline.github.io/poker-trainer/nl2.html#' + p.turnHref);
    }
    if (p.river) {
      o.push('- 河牌：' + p.river.title);
      o.push('  列「' + (p.riverRow || '') + '」');
      if (p.riverHref) o.push('  → https://tetracycline.github.io/poker-trainer/nl2.html#' + p.riverHref);
    } else {
      o.push('- 河牌：這條樣本在轉牌之後沒有收集到河牌表（請仍檢查轉牌「↑ 上一步」與後續連法）。');
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
if (jsonPath) fs.writeFileSync(jsonPath, JSON.stringify({ counts, byKind, misses: misses }, null, 2));
if (!QUIET) {
  console.log(JSON.stringify(counts));
  if (misses.length) console.log('misses by kind', byKind);
}
if (!mdPath && !QUIET) console.log(auditText);
process.exit(misses.length ? 1 : 0);
