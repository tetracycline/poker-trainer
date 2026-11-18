#!/usr/bin/env node
/* 行動線跳轉覆蓋檢查：翻／轉每一格非棄牌動作，必須有可點的下一街錨點
   （同一情境、同一條線、同一牌面列若有），或明確標「（無後續表）」。
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
const ok = { linked: 0, noted: 0, fold: 0, na: 0, river: 0 };
function baseId(href) { return String(href || '').replace(BT_RE, ''); }
function addMiss(kind, s, row, cell, detail) {
  misses.push({ kind, sp: s.sp, nd: s.nd, table: s.id, row: row && (row.lab || row.id), text: cell && cell.text, href: cell && cell.href, detail });
}

for (const s of allSecs) {
  for (const row of s.rows) for (const c of row.cells) {
    if (c.na || c.text === '—' || !c.text) { ok.na++; continue; }
    if (s.st >= 2) { ok.river++; continue; }
    if (c.act === 'fold') { ok.fold++; continue; }
    if (c.href && c.note) addMiss('又連又標', s, row, c, '有下一街連結卻仍標「無後續表」');
    if (c.href) {
      const href = c.href, base = baseId(href), hasRow = BT_RE.test(href);
      const tsec = idMap.get(href) || idMap.get(base);
      if (!tsec) { addMiss('錨點不存在', s, row, c, '#' + href); continue; }
      if (tsec.st !== s.st + 1) { addMiss('街次不對', s, row, c, `目標 ${tsec.sp}/${tsec.nd} st=${tsec.st}`); continue; }
      if (tsec.sp !== s.sp) { addMiss('情境不對', s, row, c, `目標 ${tsec.sp}/${tsec.nd}`); continue; }
      if (tsec.pfx !== s.pfx) { addMiss('線前綴不對', s, row, c, `目標 ${tsec.nd} pfx=${tsec.pfx}`); continue; }
      if (hasRow && !idMap.has(href)) { addMiss('牌面列錨點不存在', s, row, c, '#' + href + '（表在，列 id 沒有）'); continue; }
      if (hasRow && row.bt && href.endsWith('-' + row.bt) === false) addMiss('牌面列不對', s, row, c, `從 ${row.bt} 鏈到 ${href}`);
      else ok.linked++;
    } else if (c.note) {
      ok.noted++;
    } else {
      addMiss('沉默無連結', s, row, c, '非棄牌且沒有下一街連結，也沒有「（無後續表）」');
    }
  }
}

const counts = {
  tables: allSecs.length,
  flop: allSecs.filter(s => s.st === 0).length,
  turn: allSecs.filter(s => s.st === 1).length,
  river: allSecs.filter(s => s.st === 2).length,
  linked: ok.linked, noted: ok.noted, fold: ok.fold, na: ok.na, riverCells: ok.river,
  misses: misses.length
};
const byKind = {};
for (const m of misses) byKind[m.kind] = (byKind[m.kind] || 0) + 1;


const BT_ZH = ['9 以下低牌面', 'J/T 高面', 'K/Q 高面', 'A 高面', '成對面', '單色面'];
const HCO = ['S', 'TPG', 'TPW', 'MID', 'DRAW', 'WDRAW', 'AIR'];
const HNAME = { S: '兩對+', TPG: '頂對好', TPW: '頂對弱', MID: '中小對', DRAW: '強聽', WDRAW: '弱聽', AIR: '空氣' };
let reachShown = 0, reachRemoved = 0, reachRemovedCols = 0;
const removedEx = [];
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
          if (removedEx.length < 40) removedEx.push(spot.id + '/' + nd + ' ' + (ln.key || '') + ' ' + zh + '×' + (HNAME[h] || h));
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
  o.push('規則：翻牌、轉牌每一格非棄牌動作，必須連到下一街同一情境、同一條線的表（有牌面列就停在同一列），或明確標「（無後續表）」。棄牌不必有下一步。河牌不再往下連。');
  o.push('');
  o.push('## 計數');
  o.push('');
  o.push(`- 表：${counts.tables}（翻 ${counts.flop}、轉 ${counts.turn}、河 ${counts.river}）`);
  o.push(`- 有下一街連結：${counts.linked}`);
  o.push(`- 標「（無後續表）」：${counts.noted}`);
  o.push(`- 棄牌（不要求連結）：${counts.fold}`);
  o.push(`- 走不到的「—」：${counts.na}`);
  o.push(`- 河牌格（不要求下一步）：${counts.riverCells}`);
  o.push(`- **misses：${counts.misses}**`);
  o.push('');
  o.push('## 行動線可達性（邏輯）');
  o.push('');
  o.push('規則：這一格的牌型，必須能用「你先前每一個決定的主答案」（≈ 不算）走到這條線。牌型可逐街改變（轉牌／河牌才提升的手，用當街牌面分類）。牌面列還要跟「翻牌質地＋各街最高張」一致：最高張仍是 9 以下時，不能寫進 J/T、K/Q、A 高面；最高張已是 T 以上時，不能寫進 9 以下低牌面。');
  o.push('');
  o.push(`- 通過可達性、實際顯示的格：${counts.reachShown}`);
  o.push(`- 資料有列但因走不到而拿掉的格：${counts.reachRemoved}`);
  o.push(`- 因此整欄拿掉的牌型（某一條線上該牌型完全走不到）：${counts.reachRemovedCols}`);
  o.push('- 例：BB 過牌－面對 c-bet 跟注－轉牌先行動，「兩對+」在翻牌的主答案是加注（或先行動時下注），不會以翻牌兩對+ 走進這條線；表上若還有兩對+，只代表轉牌才從頂對／中對等提升上來的手。');
  o.push(`  目前該線兩對+ 顯示 ${counts.tfirstTwoPairCells} 格（提升後的當街兩對+），翻牌就已經是兩對+ 的已排除。`);

  if (Object.keys(byKind).length) {
    o.push('');
    o.push('分類：' + Object.entries(byKind).map(([k, n]) => `${k} ${n}`).join('、'));
  }
  o.push('');
  if (!misses.length) o.push('結論：0 misses。每個會繼續的動作要不是連到正確的下一街錨點，就是標了「（無後續表）」。');
  else {
    o.push('## Misses');
    o.push('');
    for (const m of misses.slice(0, 200)) {
      o.push(`- [${m.kind}] ${m.sp}/${m.nd} ${m.row || ''} 「${m.text}」 ${m.href ? '#' + m.href : ''} — ${m.detail}`);
    }
    if (misses.length > 200) o.push(`- …另有 ${misses.length - 200} 筆`);
  }
  o.push('');
  return o.join('\n');
}

function samplePaths() {
  // Prefer real href chains flop→turn→river, include KQ_high / A_high if present
  const wanted = [];
  const flop = allSecs.filter(s => s.st === 0);
  for (const s of flop) {
    for (const row of s.rows) {
      for (const c of row.cells) {
        if (!c.href) continue;
        const mid = idMap.get(c.href) || idMap.get(baseId(c.href));
        if (!mid || mid.st !== 1) continue;
        const midRow = mid.rows.find(r => r.id === c.href) || mid.rows.find(r => row.bt && r.id.endsWith('-' + row.bt)) || mid.rows[0];
        const nextC = midRow && midRow.cells.find(x => x.href && (idMap.get(x.href) || idMap.get(baseId(x.href)) || {}).st === 2);
        if (!nextC) continue;
        const riv = idMap.get(nextC.href) || idMap.get(baseId(nextC.href));
        wanted.push({
          spot: s.sp, flop: s, flopRow: row.lab, flopAct: c.text.replace(/（無後續表）/, '').trim(), flopHref: c.href,
          turn: mid, turnRow: midRow && midRow.lab, turnAct: nextC.text.replace(/（無後續表）/, '').trim(), turnHref: nextC.href,
          river: riv
        });
      }
    }
  }
  // unique by flop table + flop row + river table, prefer ipfr KQ / A
  const rank = p => (p.spot === 'ipfr' ? 0 : 1) + (p.flopRow && /K\/Q/.test(p.flopRow) ? 0 : 2) + (p.turnRow && /A 高/.test(p.turnRow) ? 0 : 1);
  const seen = new Set(), pick = [];
  for (const p of wanted.sort((a, b) => rank(a) - rank(b))) {
    const k = [p.spot, p.flop.id, p.flopRow, p.turn.id, p.river.id].join('|');
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
  o.push('這是 NL2 行動線對照表。上方按鈕切換翻前情境（例如你開池有位置、BB 防守）。每個情境下面依行動線排表，一條線一張表：先翻牌，再轉牌，再河牌。');
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
  o.push('欄是牌型（兩對+、頂對好…）。走不到或沒答案是「—」。格子只寫動作和「GTO」或「剝削」，下注／加注會標尺寸；面對下注且答案隨尺寸而變時，會寫「面對小注／≥¾／超池」。不要再看到「最高張 9 以下」或「最高張 T 以上」另開成一列，那些已併進上面六列。');
  o.push('');
  o.push('點格子裡的動作（或表上的「→ 下一步」）會跳到下一街同一條線的表，對得到就停在同一種牌面列。後面的表有「↑ 上一步」。棄牌沒有下一步。若資料裡沒有下一街的表，格子會寫「（無後續表）」，不該出現默默沒連結、也沒說明的情況。');
  o.push('');
  o.push('錨點格式：#ln-{情境}-{節點}-{hash}，牌面列再加 -low、-mid_high、-KQ_high、-A_high、-paired、-mono。');
  o.push('');
  o.push('## 十條翻→轉→河樣本路徑');
  o.push('');
  o.push('請實際打開連結，確認會滾到正確的表與列，標題行動線接得上，列名與出發列同類（或轉牌牌面按規則改列，例如 K 高翻牌轉 A 應到 A 高面）。');
  o.push('');
  const paths = samplePaths();
  const ST = ['翻牌', '轉牌', '河牌'];
  paths.forEach((p, i) => {
    o.push(`### ${i + 1}. ${p.spot}　${p.flopRow || ''} → ${p.turnRow || ''} → ${p.river && p.river.title ? '' : ''}${p.turnRow || ''}`);
    o.push('');
    o.push(`- 翻：${p.flop.title}`);
    o.push(`  列「${p.flopRow}」動作「${p.flopAct}」`);
    o.push(`  → https://tetracycline.github.io/poker-trainer/nl2.html#${p.flopHref}`);
    o.push(`- 轉：${p.turn.title}`);
    o.push(`  列「${p.turnRow}」動作「${p.turnAct}」`);
    o.push(`  → https://tetracycline.github.io/poker-trainer/nl2.html#${p.turnHref}`);
    o.push(`- 河：${p.river.title}`);
    o.push(`  → https://tetracycline.github.io/poker-trainer/nl2.html#${p.turnHref.replace(/-(A_high|KQ_high|mid_high|low|paired|mono)$/, '') === p.turnHref ? p.turnHref : p.turnHref}`);
    o.push('');
  });
  if (paths.length < 10) o.push(`（只收集到 ${paths.length} 條完整翻→轉→河路徑。）`);
  o.push('');
  return o.join('\n');
}

const auditText = mdAudit();
const reviewText = mdReview();
const mdPath = opt('--md'), reviewPath = opt('--review'), jsonPath = opt('--json');
if (mdPath) fs.writeFileSync(mdPath, auditText);
if (reviewPath) fs.writeFileSync(reviewPath, reviewText);
if (jsonPath) fs.writeFileSync(jsonPath, JSON.stringify({ counts, byKind, misses: misses.slice(0, 500) }, null, 2));
if (!QUIET) {
  console.log(JSON.stringify(counts));
  if (misses.length) console.log('misses by kind', byKind);
}
if (!mdPath && !QUIET) console.log(auditText);
process.exit(misses.length ? 1 : 0);
