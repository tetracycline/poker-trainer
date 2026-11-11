#!/usr/bin/env node
/* 獨立可達性驗證（不使用 nl2_reach.js / nl2_titles.js 的可達性邏輯）。
   做法：執行正式 nl2.js 渲染每個情境，從「畫面上的 HTML」讀出每張表的標題、每一格；
   從標題文字重建完整行動線；對每個顯示的牌型×牌面格，逐一走過這條線上「你」先前的每個決定
   （翻牌、轉牌、本街先前；對手動作照線上假設），到該決定點的資料表查這個牌型的答案（主答案 r.a，
   ≈ 的替代動作不算），必須等於線上要求的動作。牌型會逐街改變：先前那一街用「那一街的牌型」查，
   翻牌→轉牌→河牌 的牌型序列必須真的發得出來（tools/class_trans.json，正式分類器真實發牌）；牌面以
   翻牌質地 → 各街最高張（T 以上／9 以下）追蹤，例外列依條件套用。
   另外反查：走得到卻沒顯示的格（漏格）、走得到卻沒顯示的線（漏表）。
   用法：node tools/reach_verify.js [repoRoot] [--log out.md] [--json out.json] [--quiet]
   結束碼：違規數 > 0 → 1。 */
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const args = process.argv.slice(2);
const opt = k => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const root = path.resolve(args[0] && !args[0].startsWith('--') ? args[0] : path.join(__dirname, '..'));
const LOG = opt('--log'), JSONOUT = opt('--json'), QUIET = args.includes('--quiet');

// ---------- 1. 執行正式渲染器 ----------
function loadRenderer() {
  const app = { innerHTML: '', querySelectorAll: () => [], addEventListener() {} };
  const ctx = { console, __LINES_QA: true, location: { hash: '#lines' }, scrollTo() {}, addEventListener() {},
    document: { querySelector: () => app, querySelectorAll: () => [], getElementById: () => null } };
  ctx.window = ctx; if (args.includes('--nofilter')) ctx.__NL2_NOFILTER = true; vm.createContext(ctx);
  for (const n of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2.js']) {
    const f = path.join(root, n); if (!fs.existsSync(f)) continue;
    let src = fs.readFileSync(f, 'utf8');
    if (n === 'nl2.js' && !src.includes('data-node=')) // 舊版沒有節點標記：只為了讀出節點，補上屬性（不改任何邏輯）
      src = src.replace('return use.map(ln => `<div class="sec"><b class="ttl">', 'return use.map(ln => `<div class="sec" data-node="${sp}/${nd}"><b class="ttl">');
    vm.runInContext(src, ctx, { filename: n });
  }
  return { ctx, app };
}
const { ctx, app } = loadRenderer();
const L = ctx.NLL, Q = ctx.__linesQA;

// ---------- 2. 基本表 ----------
const HCODE = { '兩對+': 'S', '頂對好': 'TPG', '頂對弱': 'TPW', '中小對': 'MID', '強聽': 'DRAW', '強聽未中': 'DRAW', '弱聽': 'WDRAW', '弱聽／高張': 'WDRAW', '空氣': 'AIR' };
const HNAME = { S: '兩對+', TPG: '頂對好', TPW: '頂對弱', MID: '中小對', DRAW: '強聽', WDRAW: '弱聽', AIR: '空氣' };
const STN = ['翻牌', '轉牌', '河牌'];
const TX = ['A_high', 'KQ_high', 'mid_high', 'low', 'paired', 'mono'];
const TXN = { A_high: 'A 高面', KQ_high: 'K/Q 高面', mid_high: 'J/T 高面', low: '9 以下', paired: '成對面', mono: '單色面' };
const streetOfNd = nd => /(^|_)f_/.test(nd) ? 0 : /(^|_)t_/.test(nd) ? 1 : 2;
const pfxOf = nd => (nd.match(/^(3b_|3c_|lmp_|iso_)/) || [''])[0];
const ANS = { x: '過', c: '跟', f: '棄', r: '加注', small: '下注', big: '下注' };
const strip = s => String(s).replace(/<[^>]*>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').trim();
const rowsOf = (sp, nd) => L.rows.filter(r => r.sp === sp && r.nd === nd);

// ---------- 3. 自己的動作正規化（原始例題 → 你/對手＋動作）----------
const VB = { x: '過', c: '跟', f: '棄', b: '下注', r: '加注', a: '全下' };
function rawBits(seg, me) {
  const out = []; let bet = false;
  for (const t of String(seg || '').split(' ').filter(Boolean)) {
    const i = t.indexOf(':'), p = t.slice(0, i), k = t[i + 1], hero = p === me;
    let v = VB[k]; if (k === 'a' && !hero) v = bet ? '加注' : '下注';
    if ('bra'.includes(k)) bet = true;
    out.push((hero ? '你' : '對手') + v);
  }
  return out;
}
function canon(bits) { // 對手棄牌不改變線；連續相同的對手動作合併；對手在你行動前跟別人的注不算
  const a = []; let bet = false;
  for (let b of bits) {
    if (b === '對手超池下注') b = '對手下注';
    if (b === '對手全下') b = bet ? '對手加注' : '對手下注';
    if (/^(你|對手)(下注|加注|全下)/.test(b)) bet = true; if (b === '對手棄') continue; if (a.length && a[a.length - 1] === b && b.startsWith('對手')) continue; a.push(b); }
  return a.filter((b, i) => !(b === '對手跟' && i > 0 && /^對手(下注|加注)/.test(a[i - 1])));
}
// 決定點索引：sp|前綴|街|這個決定之前的完整行動 → 節點
const DEC = new Map();
for (const r of L.rows) for (const e of r.eg || []) {
  const st = streetOfNd(r.nd), segs = String(e.l || '').split('/');
  if (segs.length !== st + 1) continue;
  const key = [r.sp, pfxOf(r.nd), st, segs.map(g => canon(rawBits(g, e.me)).join('、')).join('|')].join('#');
  if (!DEC.has(key)) DEC.set(key, new Set()); DEC.get(key).add(r.nd);
}

// ---------- 4. 讀畫面 ----------
function parseTitle(plain) {
  const parts = plain.split(' → ');
  if (!parts[0].startsWith('翻前：')) return null;
  const pre = parts[0].slice(3), streets = [];
  let question = '';
  for (let i = 1; i < parts.length; i++) {
    const m = parts[i].match(/^(翻牌|轉牌|河牌)：(.*)$/); if (!m) return null;
    let body = m[2];
    if (i === parts.length - 1) {
      const q = body.match(/(?:^|，)(輪到你，下注或過牌？|你要怎麼做？|你先行動，下注或過牌？)$/);
      if (!q) return null; question = q[1]; body = body.slice(0, body.length - q[0].length);
    }
    streets.push(body ? body.split('、') : []);
  }
  return { pre, streets, question };
}
function parseSections(html, sp) {
  const out = [];
  const re = /<div class="sec" data-node="([^"]+)"><b class="ttl">([\s\S]*?)<\/b>([\s\S]*?)<\/div>(?=<div class="sec"|<div class="sec small"|$)/g;
  // 段落內含 <div class="tw">…</div>，用手動切段
  const starts = [...html.matchAll(/<div class="sec" data-node="([^"]+)">/g)].map(m => ({ i: m.index, node: m[1] }));
  for (let k = 0; k < starts.length; k++) {
    const seg = html.slice(starts[k].i, k + 1 < starts.length ? starts[k + 1].i : html.length);
    const tm = seg.match(/<b class="ttl">([\s\S]*?)<\/b>/);
    const titleHtml = tm ? tm[1] : '';
    const face = (seg.match(/<p class="small muted">你面對（例）：([\s\S]*?)<\/p>/) || [])[1] || '';
    const tab = (seg.match(/<table class="rt lt">([\s\S]*?)<\/table>/) || [])[1] || '';
    const trs = [...tab.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map(m => m[1]);
    const cols = trs.length ? [...trs[0].matchAll(/<th[^>]*>([\s\S]*?)<\/th>/g)].slice(1).map(m => strip(m[1])) : [];
    const rows = trs.slice(1).map(tr => {
      const cond = strip((tr.match(/<th class="cl">([\s\S]*?)<\/th>/) || [])[1] || '');
      const cells = [...tr.matchAll(/<td class="([^"]*)">([\s\S]*?)<\/td>/g)].map(m => ({ cls: m[1], text: strip(m[2].replace(/<small[\s\S]*?<\/small>/g, '')), basis: strip((m[2].match(/<small[^>]*>([\s\S]*?)<\/small>/) || [])[1] || '') }));
      return { cond, cells };
    });
    const exm = seg.match(/<span class="lab"><span class="df"[^>]*>例外<\/span><\/span>　([\s\S]*?)<\/p>/);
    const exc = exm ? exm[1].split('；').map(x => { const t = strip(x); const m = t.match(/^(.*)：(.*) → (.*)$/); return m ? { cond: m[1], classes: m[2].split('、'), text: m[3].replace(/(池估|池|GTO|兩人 GTO 近似)$/, '') } : { raw: t }; }) : [];
    const [nsp, nd] = starts[k].node.split('/');
    out.push({ sp: nsp || sp, nd, titleHtml, title: strip(titleHtml), face: strip(face), cols, rows, exc });
  }
  return out;
}

// ---------- 5. 牌面狀態 ----------
// 狀態：翻牌質地 tx，各街最高張 hi[0..2]（T＝T 以上，L＝9 以下）
function states(S) {
  const out = [];
  for (const tx of TX) {
    const hf = ['A_high', 'KQ_high', 'mid_high'].includes(tx) ? ['T'] : tx === 'low' ? ['L'] : ['T', 'L'];
    for (const h0 of hf) for (const h1 of (h0 === 'T' ? ['T'] : ['T', 'L'])) for (const h2 of (h1 === 'T' ? ['T'] : ['T', 'L'])) {
      out.push({ tx, hi: [h0, h1, h2] });
    }
  }
  // 只保留到第 S 街為止不同的組合
  const seen = new Set(); return out.filter(s => { const k = s.tx + s.hi.slice(0, S + 1).join(''); if (seen.has(k)) return false; seen.add(k); return true; });
}
// 線層級條件（三槍、你轉牌過牌、你翻轉都下注、你的翻前角色）
function lineFacts(P) {
  const st = P.streets;
  const firstBetBy = bits => { for (const b of bits) { if (/^對手(下注)/.test(b)) return 'v'; if (/^你(下注|全下)/.test(b)) return 'h'; } return null; };
  const heroBet = bits => bits.some(b => /^你(下注|全下|加注)/.test(b));
  return {
    tb: st.length >= 3 && firstBetBy(st[0]) === 'v' && firstBetBy(st[1]) === 'v' && firstBetBy(st[2]) === 'v',
    checkTurn: st.length >= 3 && st[1].includes('你過') && !heroBet(st[1]),
    betBet: st.length >= 3 && heroBet(st[0]) && heroBet(st[1]),
    // 翻前加注者＝最後一個加注的人：你 3-bet、你加注隔離，或你開池而沒有人 3-bet
    pfr: /你 (\S+ )?3-bet|你 ?(\S+ )?加注隔離/.test(P.pre) || (/(^|，)你 \S+ 開/.test(P.pre) && !/3-bet/.test(P.pre))
  };
}
// 一列的條件 vs 狀態／線：true＝一定符合，'maybe'＝不追蹤的條件（下注尺寸、河牌牌型），false＝不符
function condFit(r, s, street, F) {
  const c = r.c || {}; let maybe = false;
  for (const k of Object.keys(c)) {
    const v = c[k];
    if (k === 'tx') { if (s.tx !== v) return false; }
    else if (k === 'hi') { if (s.hi[street] !== v) return false; }
    else if (k === 'ln') { if (F == null) { maybe = true; continue; } if ((v === 'tb') !== F.tb) return false; }
    else if (k === 'prior') { if (F == null) { maybe = true; continue; } if (v === 'check_turn' && !F.checkTurn) return false; if (v === 'bet_bet' && !F.betBet) return false; }
    else if (k === 'hr') { if (F == null) { maybe = true; continue; } if ((v === 'PFR') !== F.pfr) return false; }
    else maybe = true; // sz, ct
  }
  return maybe ? 'maybe' : true;
}
// 某節點、某牌型、某狀態下，可能的主答案（例外優先）
function answersAt(sp, nd, h, s, street, F) {
  const R = rowsOf(sp, nd).filter(r => r.hc.includes(h));
  const ex = R.filter(r => r.x), base = R.filter(r => !r.x);
  const out = new Set(); let definiteEx = false;
  for (const r of ex) { const f = condFit(r, s, street, F); if (f) { out.add(r.a); if (f === true) definiteEx = true; } }
  if (!definiteEx) for (const r of base) if (condFit(r, s, street, F)) out.add(r.a);
  return out;
}
// 牌型序列表（真實發牌）：質地|各街最高張 → 出現過的 翻轉河 牌型序列
const CTJ = JSON.parse(fs.readFileSync(path.join(__dirname, 'class_trans.json'), 'utf8'));
const LET = { S: 's', TPG: 'g', TPW: 'w', MID: 'm', DRAW: 'd', WDRAW: 'k', AIR: 'a' }, HC = Object.keys(LET);
const SEQ = {};
for (const [k, v] of Object.entries(CTJ)) if (!k.startsWith('_')) SEQ[k] = new Set(v.split(' '));
function seqs(h, s, S) { // 第 0..S 街的牌型（最後一街＝h）
  if (S === 0) return [[h]];
  const out = [];
  for (const a of HC) for (const b of (S === 2 ? HC : [null])) {
    const want = S === 1 ? LET[a] + LET[h] : LET[a] + LET[b] + LET[h];
    const keys = S === 1 ? ['T', 'L'].map(x => s.tx + '|' + s.hi[0] + s.hi[1] + x) : [s.tx + '|' + s.hi.join('')];
    const hit = keys.some(k => SEQ[k] && [...SEQ[k]].some(q => q.startsWith(want)));
    if (hit) out.push(S === 1 ? [a, h] : [a, b, h]);
  }
  return out;
}
const NEED = { 過: ['x'], 下注: ['small', 'big'], 全下: ['big', 'small', 'r'], 跟: ['c'], 加注: ['r'] };


// 反查用：給一條線（各街正規化動作）、一列、一個牌型 → 走不走得到
function decisionsFor(sp, nd, streets) {
  const out = [];
  streets.forEach((bits, i) => bits.forEach((b, j) => {
    if (!b.startsWith('你')) return;
    const prefix = streets.slice(0, i).map(x => x.join('、')).concat([bits.slice(0, j).join('、')]).join('|');
    out.push({ street: i, verb: b.slice(1), need: NEED[b.slice(1)] || [], nodes: [...(DEC.get([sp, pfxOf(nd), i, prefix].join('#')) || [])] });
  }));
  return out;
}
function reachable(sp, nd, streets, F, r, h) {
  const S = streets.length - 1, decs = decisionsFor(sp, nd, streets), rows = rowsOf(sp, nd);
  if (!decs.every(d => d.nodes.length)) return false;
  for (const s of states(S)) {
    if (!condFit(r, s, S, F)) continue;
    if (!r.x && rows.some(x => x.x && x.hc.includes(h) && condFit(x, s, S, F) === true)) continue;
    const ok = (d, c) => d.nodes.some(n => [...answersAt(sp, n, c, s, d.street, F)].some(a => d.need.includes(a)));
    if (seqs(h, s, S).some(q => decs.every(d => ok(d, q[d.street])))) return true;
  }
  return false;
}
// ---------- 6. 驗證每張表 ----------
const report = { tables: [], violations: [], flags: [], counts: {} };
function V(t, kind, msg) { report.violations.push({ table: t.title, node: t.sp + '/' + t.nd, kind, msg }); t.viol.push(kind + '：' + msg); }
function heroSide(pre) { // 翻後順序 SB BB UTG HJ CO BTN
  const PO = ['SB', 'BB', 'UTG', 'HJ', 'CO', 'BTN'];
  const me = (pre.match(/你（?\s?(SB|BB|UTG|HJ|CO|BTN)/) || [])[1];
  const all = [...pre.matchAll(/\b(SB|BB|UTG|HJ|CO|BTN)\b/g)].map(m => m[1]);
  return { me, others: [...new Set(all.filter(p => p !== me))], PO };
}
function describeDecision(sp, nd) { return `${sp}/${nd}`; }

for (const spot of L.spots) {
  Q.render(spot.id);
  const secs = parseSections(app.innerHTML, spot.id);
  const seenTitle = new Set();
  for (const t of secs) {
    t.viol = []; t.checks = []; t.removedCells = [];
    report.tables.push(t);
    if (seenTitle.has(t.title)) V(t, '重複', '同一情境出現兩張標題完全相同的表');
    seenTitle.add(t.title);
    const P = parseTitle(t.title);
    if (!P) { V(t, '標題', '標題無法解析成明確行動線'); continue; }
    t.P = P;
    const S = P.streets.length - 1, st = streetOfNd(t.nd);
    if (S !== st) V(t, '標題', `標題寫到${STN[S]}，但這張表是${STN[st]}的決定`);
    const F = lineFacts(P);
    // (a) 合法動作
    const cur = P.streets[S] || [];
    const facing = cur.length > 0 && /^對手(下注|加注|全下|超池下注)/.test(cur[cur.length - 1]);
    if (facing && t.question !== undefined && P.question !== '你要怎麼做？') V(t, '標題', '面對下注卻問「下注或過牌」');
    if (!facing && P.question === '你要怎麼做？') V(t, '標題', '沒人下注卻問「你要怎麼做？」（應為下注或過牌）');
    const legal = txt => facing ? /^(棄|跟|加注|全下)/.test(txt) : /^(過|下注|全下)/.test(txt);
    // (b) 你的上色
    const hi = [...t.titleHtml.matchAll(/<span class="ha">([\s\S]*?)<\/span>/g)].map(m => strip(m[1]));
    for (const x of hi) if (!/^你/.test(x) && !/^輪到你/.test(x)) V(t, '上色', `金色標到不是你的動作：「${x}」`);
    const plainNoHa = strip(t.titleHtml.replace(/<span class="ha">[\s\S]*?<\/span>/g, ''));
    for (const m of plainNoHa.matchAll(/你[^，、→ ]*/g)) V(t, '上色', `你的動作沒有金色：「${m[0]}」`);
    // (c) 誰先行動
    const side = heroSide(P.pre);
    if (side.me && side.others.length === 1) {
      const ip = side.PO.indexOf(side.me) > side.PO.indexOf(side.others[0]);
      P.streets.forEach((bits, i) => {
        if (!bits.length) { if (ip && i < S) V(t, '順序', `${STN[i]}沒有動作`); if (ip && i === S) V(t, '順序', `你有位置，${STN[i]}卻寫你先行動`); return; }
        const first = bits[0].startsWith('你') ? 'h' : 'v';
        if (ip && first === 'h') V(t, '順序', `你有位置（${side.me}），${STN[i]}卻是你先動`);
        if (!ip && first === 'v') V(t, '順序', `你沒位置（${side.me}），${STN[i]}卻是對手先動`);
      });
    }
    // (d) 例題與標題一致
    checkFace(t, P);
    // (e) 先前決定點
    const decisions = [];
    for (let i = 0; i <= S; i++) {
      const bits = P.streets[i];
      bits.forEach((b, j) => {
        if (!b.startsWith('你')) return;
        const verb = b.slice(1);
        const prefix = P.streets.slice(0, i).map(x => canon(x).join('、')).concat([canon(bits.slice(0, j)).join('、')]).join('|');
        const key = [t.sp, pfxOf(t.nd), i, prefix].join('#');
        const nodes = [...(DEC.get(key) || [])];
        decisions.push({ street: i, verb, prefix, nodes, need: NEED[verb] || [] });
        if (!nodes.length) V(t, '找不到先前決定點', `${STN[i]}「${prefix.split('|').pop() || '（第一個動作）'}」之後你${verb}：資料裡沒有這個決定點，無法確認哪些牌型會這樣打`);
        if (!NEED[verb]) V(t, '標題', `先前動作「${b}」不是合法的決定動作`);
      });
    }
    t.decisions = decisions;
    // (f) 每一格
    const nodeRows = rowsOf(t.sp, t.nd);
    const SS = states(S);
    function checkCell(r, h, label, txt) {
      const lines = [];
      if (txt != null && !legal(txt)) V(t, '不合法動作', `${label}：「${txt}」${facing ? '面對下注不能過牌／下注' : '沒有人下注不能跟／棄／加注'}`);
      // 這列本身的條件
      const witnesses = [];
      const perDec = decisions.map(() => new Map());
      const candDec = decisions.map(() => new Map());
      for (const s of SS) {
        const fit = condFit(r, s, S, F); if (!fit) continue;
        if (!r.x) { // 基本列：此狀態若有一定適用的例外，基本格不代表這個狀態
          const exDef = nodeRows.some(x => x.x && x.hc.includes(h) && condFit(x, s, S, F) === true);
          if (exDef) continue;
        }
        // 每個決定：哪些「當街牌型」的主答案符合線上動作
        const passBy = decisions.map(d => {
          const ok = new Set();
          for (const c of HC) {
            const A = new Set(); for (const nd of d.nodes) for (const a of answersAt(t.sp, nd, c, s, d.street, F)) A.add(a);
            if ([...A].some(a => d.need.includes(a))) ok.add(c);
          }
          return ok;
        });
        const allSeq = seqs(h, s, S);
        const chain = allSeq.find(q => decisions.every((d, di) => passBy[di].has(q[d.street])));
        decisions.forEach((d, di) => { // 給理由：這一街可能是哪些牌型、它們的答案
          for (const q of allSeq) { const c = q[d.street]; const A = new Set(); for (const nd of d.nodes) for (const a of answersAt(t.sp, nd, c, s, d.street, F)) A.add(ANS[a]);
            candDec[di].set(c, new Set([...(candDec[di].get(c) || []), ...A])); }
        });
        decisions.forEach((d, di) => {
          const bk = d.street === 0 ? TXN[s.tx] : (s.hi[d.street] === 'T' ? '最高張 T 以上' : '最高張 9 以下');
          const prev = perDec[di].get(bk) || { A: [], pass: false, cls: new Set() };
          const A = new Set(prev.A); for (const nd of d.nodes) for (const a of answersAt(t.sp, nd, d.street === S ? h : (chain ? chain[d.street] : h), s, d.street, F)) A.add(a);
          perDec[di].set(bk, { A: [...A], pass: prev.pass || !!chain, cls: new Set([...prev.cls, ...(chain ? [chain[d.street]] : [])]) });
        });
        if (chain) witnesses.push({ ...s, chain });
      }
      decisions.forEach((d, di) => {
        const m = perDec[di];
        const parts = [...m.entries()].map(([bk, v]) => `${bk}=${v.A.length ? [...new Set(v.A.map(a => ANS[a]))].join('/') : '（沒有答案）'}${v.pass ? '✓' : '✗'}`);
        const cl = [...new Set([...m.values()].flatMap(v => [...v.cls]))].map(c => HNAME[c]); lines.push(`${HNAME[h]}：${STN[d.street]}「${d.prefix.split('|').pop() || '你先行動'}」→ 線上要你${d.verb}；${cl.length ? '那時牌型可以是 ' + cl.join('／') + '；' : ''}節點 ${d.nodes.join('/') || '（無）'} 答案 ${parts.join('、') || '（此列條件下無牌面）'}`);
      });
      const okAll = witnesses.length > 0 && decisions.every(d => d.nodes.length);
      // 白話理由（給 HW 看）
      let reason = '';
      if (!okAll) {
        const miss = decisions.find(d => !d.nodes.length);
        const anyState = SS.some(s => condFit(r, s, S, F));
        if (miss) reason = `前面「${STN[miss.street]}：${miss.prefix.split('|').pop() || '你先行動'}，你${miss.verb}」這一步，資料裡沒有對應的表，無法確認哪些牌會這樣打`;
        else if (!anyState) reason = '這一列的條件（三槍／你轉牌過牌／你的翻前角色）跟這條線不符';
        else {
          const di = decisions.findIndex((d, i) => ![...candDec[i].entries()].some(([c, A]) => [...A].some(a => d.verb === a || (d.verb === '全下' && /下注|加注/.test(a)))));
          if (di >= 0) {
            const d = decisions[di], cm = candDec[di];
            const desc = [...cm.entries()].map(([c, A]) => `${HNAME[c]}＝${[...A].join('／') || '沒有答案'}`).join('、');
            reason = d.street === S
              ? `${HNAME[h]}在${STN[d.street]}「${d.prefix.split('|').pop() || '你先行動'}」時的答案是「${[...(cm.get(h) || [])].join('／') || '沒有答案'}」，不會${d.verb}，所以走不到這條線`
              : `到${STN[S]}會是${HNAME[h]}的牌，在${STN[d.street]}可能是：${desc || '（發不出來）'}；在${STN[d.street]}「${d.prefix.split('|').pop() || '你先行動'}」時都不會${d.verb}，所以走不到這條線`;
          } else if (perDec.length && [...perDec[0].keys()].length === 0) reason = '這一格代表的牌面都歸例外列';
          else reason = `每一步單獨看都有牌面會這樣打，但沒有同一個牌面能一路走到這一格（翻牌質地／各街最高張前後對不上）`;
        }
        if (!r.x && anyState && !reason.startsWith('前面') && SS.filter(s => condFit(r, s, S, F)).every(s => nodeRows.some(x => x.x && x.hc.includes(h) && condFit(x, s, S, F) === true))) reason = '這一格代表的牌面都由例外列另外列出';
      }
      const wtxt = witnesses.length ? '可走到，例：' + [...new Set(witnesses.map(s => TXN[s.tx] + (S >= 1 ? '／轉牌' + (s.hi[1] === 'T' ? 'T+' : '9-') : '') + (S >= 2 ? '／河牌' + (s.hi[2] === 'T' ? 'T+' : '9-') : '') + (S >= 1 ? '（' + s.chain.map(c => HNAME[c]).join('→') + '）' : '')))].slice(0, 4).join('；') : '走不到';
      if (!decisions.length) lines.push(`${HNAME[h]}：之前沒有你的翻後決定（翻前不分牌型）✓`);
      return { ok: okAll, lines, wtxt, witnesses, reason };
    }
    let nCells = 0;
    for (const row of t.rows) {
      row.cells.forEach((c, ci) => {
        const lab = t.cols[ci], h = HCODE[lab];
        if (/\bna\b/.test(c.cls)) return;
        nCells++;
        const r = nodeRows.find(x => !x.x && (x.cl || '全部') === row.cond && x.hc.includes(h));
        if (!r) { V(t, '資料', `${row.cond}×${lab}：資料裡找不到這一格`); return; }
        const want = ANS[r.a];
        if (!c.text.startsWith(want === '下注' ? '' : want) && !(r.a === 'r' && /^全下/.test(c.text))) V(t, '答案', `${row.cond}×${lab}：畫面「${c.text}」與資料答案 ${r.a} 不一致`);
        const res = checkCell(r, h, `${row.cond}×${lab}`, c.text);
        t.checks.push({ cell: `${row.cond}×${lab}＝${c.text}`, ...res });
        if (!res.ok) V(t, '走不到的格', `${row.cond}×${lab}（${c.text}）：${res.lines.filter(x => /✗|（無）/.test(x)).join('；') || res.wtxt}`);
      });
    }
    for (const e of t.exc) {
      if (e.raw) { V(t, '資料', '例外列無法解析：' + e.raw); continue; }
      for (const lab of e.classes) {
        const h = Object.keys(HNAME).find(k => HNAME[k] === lab) || HCODE[lab];
        const r = nodeRows.find(x => x.x && x.cl === e.cond && x.hc.includes(h));
        if (!r) { V(t, '資料', `例外「${e.cond}」×${lab} 在資料裡找不到`); continue; }
        nCells++;
        const res = checkCell(r, h, `例外 ${e.cond}×${lab}`, e.text);
        t.checks.push({ cell: `例外 ${e.cond}×${lab}＝${e.text}`, ...res });
        if (!res.ok) V(t, '走不到的格', `例外 ${e.cond}×${lab}：${res.lines.filter(x => /✗|（無）/.test(x)).join('；') || res.wtxt}`);
      }
    }
    // (g) 反查漏格：這個節點資料裡每一列 × 每個牌型，走得到卻沒顯示
    const shownBase = new Set(), shownEx = new Set();
    for (const row of t.rows) row.cells.forEach((c, ci) => { if (!/\bna\b/.test(c.cls)) shownBase.add(row.cond + '|' + HCODE[t.cols[ci]]); });
    for (const e of t.exc) for (const lab of (e.classes || [])) shownEx.add(e.cond + '|' + (Object.keys(HNAME).find(k => HNAME[k] === lab) || HCODE[lab]));
    const canonSt = P.streets.map(b => canon(b));
    for (const r of nodeRows) for (const h of r.hc) {
      const k = (r.x ? r.cl : (r.cl || '全部')) + '|' + h;
      if ((r.x ? shownEx : shownBase).has(k)) continue;
      if (reachable(t.sp, t.nd, canonSt, F, r, h)) V(t, '漏格', `${r.x ? '例外 ' : ''}${r.cl || '全部'}×${HNAME[h]}（${ANS[r.a]}）走得到卻沒有顯示`);
    }
    t.key = canonSt.map(b => b.join('、')).join('|');
    t.nCells = nCells;
    if (!nCells) V(t, '空表', '顯示了標題但表裡沒有任何格');
  }
}

// (h) 反查漏表：資料例題裡出現的每條線，有走得到的格卻沒有表
{
  const shown = new Set(report.tables.map(t => t.sp + '/' + t.nd + '#' + t.key));
  const seen = new Set();
  for (const r0 of L.rows) for (const e of r0.eg || []) {
    const st = streetOfNd(r0.nd), segs = String(e.l || '').split('/');
    if (segs.length !== st + 1) continue;
    const streets = segs.map(g => canon(rawBits(g, e.me))), key = streets.map(b => b.join('、')).join('|');
    const pfr = e.me === e.pa, id = r0.sp + '/' + r0.nd + '#' + key;
    if (shown.has(id) || seen.has(id + pfr)) continue; seen.add(id + pfr);
    const F = { ...lineFacts({ streets, pre: '' }), pfr };
    const hits = [];
    for (const r of rowsOf(r0.sp, r0.nd)) for (const h of r.hc) if (reachable(r0.sp, r0.nd, streets, F, r, h)) hits.push(`${r.x ? '例外 ' : ''}${r.cl || '全部'}×${HNAME[h]}`);
    if (hits.length) report.violations.push({ table: key.replace(/\|/g, ' → '), node: r0.sp + '/' + r0.nd, kind: '漏表', msg: `這條線（${['翻牌', '轉牌', '河牌'].slice(0, streets.length).map((x, i) => x + '：' + (streets[i].join('、') || '（無）')).join(' → ')}）有 ${hits.length} 格走得到卻沒有表：${hits.slice(0, 8).join('、')}${hits.length > 8 ? '…' : ''}` });
  }
}
// 轉換表一致：渲染器內建的 CT 必須與 tools/class_trans.json 相同
{
  const src = fs.existsSync(path.join(root, 'nl2_titles.js')) ? fs.readFileSync(path.join(root, 'nl2_titles.js'), 'utf8') : '';
  const m = src.match(/const CT = (\{[^;]*\});/);
  const mine = Object.fromEntries(Object.entries(CTJ).filter(([k]) => !k.startsWith('_')));
  if (!m || JSON.stringify(JSON.parse(m[1])) !== JSON.stringify(mine)) report.violations.push({ table: '-', node: '-', kind: '轉換表', msg: 'nl2_titles.js 內建的牌型轉換表與 tools/class_trans.json 不同（或沒有）' });
}
// 例題（你面對）與標題一致：位置、每街動作、底池
function checkFace(t, P) {
  if (!t.face) { report.flags.push({ table: t.title, msg: '沒有例題' }); return; }
  const parts = t.face.split(' → ');
  const pre = parts[0];
  const meEx = (pre.match(/你（(\w+)）/) || [])[1];
  const meTi = (P.pre.match(/你（?\s?(SB|BB|UTG|HJ|CO|BTN)）?/) || [])[1];
  if (meTi && meEx && meTi !== meEx) V(t, '例題', `標題你是 ${meTi}，例題你是 ${meEx}`);
  const posEx = new Set([...pre.matchAll(/\b(SB|BB|UTG|HJ|CO|BTN)\b/g)].map(m => m[1]));
  const posTi = new Set([...P.pre.matchAll(/\b(SB|BB|UTG|HJ|CO|BTN)\b/g)].map(m => m[1]));
  if (posTi.size && [...posTi].some(p => !posEx.has(p))) V(t, '例題', `標題位置 ${[...posTi].join('、')} 與例題 ${[...posEx].join('、')} 不一致`);
  let pot = parseFloat((pre.match(/底池 ([\d.]+)bb/) || [])[1]);
  for (let i = 1; i < parts.length; i++) {
    const m = parts[i].match(/^(翻牌|轉牌|河牌)(?:：(.*)|，(.*))?$/); if (!m) { V(t, '例題', '例題無法解析：' + parts[i]); return; }
    let body = m[2] || m[3] || '';
    let final = null;
    const fm = body.match(/(?:^|，)(輪到你（底池 ([\d.]+)bb）|你要跟 ([\d.]+)bb（底池 ([\d.]+)bb）)$/);
    if (i === parts.length - 1) { if (!fm) { V(t, '例題', '例題最後一街沒有「輪到你」'); return; } final = fm; body = body.slice(0, body.length - fm[0].length); }
    const acts = body ? body.split('，') : [];
    const bits = [], con = {}; let curBet = 0, bet = false;
    for (const a of acts) {
      const am = a.match(/^(你（\w+）|\w+) (過牌|棄牌|跟 ([\d.]+)bb|下注 (\d+)%（([\d.]+)bb）|加注到 ([\d.]+)bb|全下 ([\d.]+)bb)$/);
      if (!am) { V(t, '例題', '例題動作無法解析：' + a); return; }
      const hero = am[1].startsWith('你'), who = am[1];
      let v;
      if (am[2] === '過牌') v = '過'; else if (am[2] === '棄牌') v = '棄';
      else if (am[3]) { v = '跟'; con[who] = +am[3]; if (Math.abs(+am[3] - curBet) > 0.11) V(t, '例題', `${STN[i - 1]}跟注 ${am[3]}bb 與當前下注 ${curBet}bb 不符`); }
      else if (am[4]) { v = '下注'; const amt = +am[5]; if (Math.abs(amt - pot * am[4] / 100) > pot * 0.005 + 0.11) V(t, '例題', `${STN[i - 1]}下注 ${am[4]}% 應約 ${(pot * am[4] / 100).toFixed(1)}bb，例題寫 ${amt}bb`); curBet = amt; con[who] = amt; bet = true; }
      else if (am[6]) { v = '加注'; curBet = +am[6]; con[who] = +am[6]; bet = true; }
      else { v = hero ? '全下' : (bet ? '加注' : '下注'); curBet = Math.max(curBet, +am[7]); con[who] = +am[7]; bet = true; }
      bits.push((hero ? '你' : '對手') + v);
    }
    const want = canon(P.streets[i - 1] || []).join('、'), got = canon(bits).join('、');
    if (want !== got) V(t, '例題', `${STN[i - 1]}：標題「${want || '（無）'}」≠ 例題「${got || '（無）'}」`);
    const add = Object.values(con).reduce((a, b) => a + b, 0);
    if (final) {
      if (final[2] && Math.abs(+final[2] - pot) > 0.11) V(t, '例題', `例題底池 ${final[2]}bb，依前面動作應為 ${pot.toFixed(1)}bb`);
      const heroCon = Object.entries(con).filter(([w]) => w.startsWith('你')).reduce((a, [, v]) => a + v, 0);
      if (final[3] && Math.abs(+final[3] - (curBet - heroCon)) > 0.11) V(t, '例題', `例題要你跟 ${final[3]}bb，依前面動作應為 ${(curBet - heroCon).toFixed(1)}bb`);
      if (final[4] && Math.abs(+final[4] - (pot + add)) > 0.11) V(t, '例題', `例題底池 ${final[4]}bb，依前面動作應為 ${(pot + add).toFixed(1)}bb`);
    }
    pot = Math.round((pot + add) * 10) / 10;
  }
}

// ---------- 7. 輸出 ----------
const byKind = {};
for (const v of report.violations) byKind[v.kind] = (byKind[v.kind] || 0) + 1;
const nodes = new Set(report.tables.map(t => t.sp + '/' + t.nd));
report.counts = { noExample: report.flags.length, tables: report.tables.length, nodes: nodes.size, cells: report.tables.reduce((a, t) => a + (t.nCells || 0), 0), violations: report.violations.length, byKind };
if (!QUIET) {
  console.log(JSON.stringify(report.counts, null, 1));
  for (const v of report.violations.slice(0, 40)) console.log(`✗ [${v.kind}] ${v.node}｜${v.table}\n    ${v.msg}`);
}
if (LOG) {
  const o = [];
  o.push('# NL2 行動線：逐表、逐格可達性檢查（完整紀錄）', '');
  o.push(`產生：tools/reach_verify.js（獨立驗證，不用 nl2_reach.js）｜表 ${report.counts.tables} 張、節點 ${report.counts.nodes} 個、格 ${report.counts.cells} 格｜違規 ${report.counts.violations}`, '');
  o.push('規則：每一格的牌型，把標題這條線上「你」先前每一個決定（翻牌、轉牌、本街先前）都到該決定點的表查答案；答案必須就是線上寫的動作（只算主答案，≈ 的另一個動作不算）。對手的動作照標題假設。牌型逐街沿用同一標籤（本頁規則）；牌面：翻牌質地 → 轉牌／河牌最高張（T 以上／9 以下），有例外列時照例外。翻前不分牌型，不檢查。', '');
  let cur = '';
  for (const t of report.tables) {
    const spt = L.spots.find(s => s.id === t.sp);
    if (t.sp !== cur) { cur = t.sp; o.push(`## ${spt ? spt.t : t.sp}`, ''); }
    o.push(`### ${t.title}`, '', `節點 ${t.sp}/${t.nd}｜顯示 ${t.nCells || 0} 格｜${t.viol.length ? '✗ ' + t.viol.length + ' 個問題' : '✓ 全部通過'}`, '');
    if (t.face) o.push(`例題：${t.face}`, '');
    if (t.decisions) o.push('你先前的決定：' + (t.decisions.length ? t.decisions.map(d => `${STN[d.street]}「${d.prefix.split('|').pop() || '你先行動'}」→ 你${d.verb}（節點 ${d.nodes.join('/') || '無'}）`).join('；') : '無（這是這條線你第一個翻後決定）'), '');
    for (const c of t.checks) {
      o.push(`- **${c.cell}** ${c.ok ? '✓' : '✗'}　${c.wtxt}`);
      for (const l of c.lines) o.push(`  - ${l}`);
    }
    if (t.viol.length) { o.push('', '問題：'); for (const v of t.viol) o.push(`- ✗ ${v}`); }
    o.push('');
  }
  fs.writeFileSync(LOG, o.join('\n'));
}
if (JSONOUT) fs.writeFileSync(JSONOUT, JSON.stringify({ counts: report.counts, violations: report.violations, tables: report.tables.map(t => ({ sp: t.sp, nd: t.nd, title: t.title, cols: t.cols, rows: t.rows, exc: t.exc, viol: t.viol, nCells: t.nCells, checks: (t.checks || []).map(c => ({ cell: c.cell, ok: c.ok, reason: c.reason })) })) }, null, 1));
process.exitCode = report.violations.length ? 1 : 0;
