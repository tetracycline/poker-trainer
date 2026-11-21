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
// 當街牌面（與翻牌同一套列、同一優先序；/workspace/poker_r005/btx.py）。JS street：0＝翻牌、1＝轉牌、2＝河牌。
const BT_ROWS = [['low', '9 以下低牌面'], ['mid_high', 'J/T 高面'], ['KQ_high', 'K/Q 高面'], ['A_high', 'A 高面'], ['paired', '成對面'], ['mono', '單色面']];
const BT_ZH = Object.fromEntries(BT_ROWS);
const BT_KEYS = BT_ROWS.map(x => x[0]);
const _BT_RISE = {A_high: ['A_high', 'paired', 'mono'], KQ_high: ['A_high', 'KQ_high', 'paired', 'mono'], mid_high: ['A_high', 'KQ_high', 'mid_high', 'paired', 'mono'], low: BT_KEYS, paired: ['paired', 'mono'], mono: ['mono']};
function textureNow(bstr, k) { // k＝JS street；看前 3+k 張公牌
  const n = 3 + k, b = String(bstr || ''), cs = [];
  for (let i = 0; i < 2 * n && i < b.length; i += 2) cs.push(b.slice(i, i + 2));
  if (cs.length !== n) return null;
  const RV = '23456789TJQKA', suits = cs.map(c => c[1]), rs = cs.map(c => RV.indexOf(c[0]) + 2);
  const sc = {}; for (const s of suits) sc[s] = (sc[s] || 0) + 1;
  if (Math.max(...Object.values(sc)) >= 3) return 'mono';
  if (new Set(rs).size < rs.length) return 'paired';
  const m = Math.max(...rs);
  return m === 14 ? 'A_high' : m >= 12 ? 'KQ_high' : m >= 10 ? 'mid_high' : 'low';
}
function possibleBt(flopTx, street) { return street <= 0 ? [flopTx] : (_BT_RISE[flopTx] || BT_KEYS); }
function splitCl(cl) {
  const k = cl || '全部';
  for (const [, zh] of BT_ROWS) {
    if (k === zh) return {grp: '', tx: zh};
    if (k.endsWith('・' + zh)) return {grp: k.slice(0, -(zh.length + 1)), tx: zh};
  }
  return {grp: k === '全部' ? '' : k, tx: k === '全部' ? '全部' : null};
}
function isCtRow(r) { return (r.c && r.c.ct) || (r.rn && r.rn.k === 'ct'); }
function isHiSplitEx(r) { return /(^|・)最高張 (9 以下|T 以上)$/.test(r.cl || ''); }
function btTitle(nd, r, e) {
  const st = stOf(nd); if (!st) return '';
  const key = (r && r.c && r.c.bt) || (e && textureNow(e.b, st));
  if (!key || !BT_ZH[key]) return '';
  return `<b class="ro">｜${st === 1 ? '轉牌' : '河牌'}：${dfs(BT_ZH[key])}</b>`;
}
const RNK = {cert: 'CERT', est: '', gtoe: '', gto: '', fb: '沿用', ct: ''};
function nTxt(r) { // 格子小字：根據＋樣本數（池 n／解算牌面數）
  const n = r.rn; if (!n) return '';
  if (n.k === 'est' || n.k === 'gtoe' || n.k === 'cert') return ` n${n.p}`;
  if (n.k === 'gto') return ` ${n.g}盤`;
  if (n.k === 'fb') return '';
  return '';
}
const cellSmall = r => r.rofb ? `<small class="df" data-df="沿用">沿用 n${r.rn.p}·${r.rn.g}盤</small>` : `<small class="df" data-df="${BS[r.b]}">${BS[r.b]}${nTxt(r)}</small>`;
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
const STD_SZ = [[1/3, '⅓'], [1/2, '½'], [2/3, '⅔'], [3/4, '¾'], [1, '1'], [1.5, '1½']];
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
  if (p.or) return '下注 ' + p.or.map(x => ({'3/4':'¾','1.5':'1½'}[x] || x)).join('或');
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
const ND_PFX = ['3b_', '3c_', 'lmp_', 'iso_'];
const ndPfx = nd => ND_PFX.find(p => nd.startsWith(p)) || '';
const VERB_OF = {x: '過', small: '下注', big: '下注', c: '跟', r: '加注'};
const STN_NAV = ['翻牌', '轉牌', '河牌'];
function lid(sp, nd, key, bt) {
  const s = sp + '\t' + nd + '\t' + (key || '');
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return 'ln-' + sp + '-' + nd + '-' + (h >>> 0).toString(36) + (bt ? '-' + bt : '');
}
function keyForLid(ln) {
  return ((ln && ln.pf) ? ln.pf + '##' : '') + (ln ? (ln.key || '') : '');
}
function catItem(sp, nd, ln) {
  return {sp, nd, pfx: ndPfx(nd), st: stOf(nd), key: ln ? (ln.key || '') : '', pf: (ln && ln.pf) || '', ln, id: lid(sp, nd, keyForLid(ln))};
}
function pfOk(a, b) {
  if (!a || !b) return true;
  if (!a.pf || !b.pf) return true;
  return a.pf === b.pf;
}
const CATC = new Map();
function lineCatalog(sp) {
  if (CATC.has(sp)) return CATC.get(sp);
  const out = [];
  for (const nd of nodesOf(sp)) {
    if (!nodeVisible(sp, nd)) continue;
    const lns = lineList(sp, nd).length ? lineList(sp, nd) : [null];
    for (const ln of lns) out.push(catItem(sp, nd, ln));
  }
  CATC.set(sp, out);
  return out;
}
function facingOk(face) { return !/你/.test(face || ''); }
function isThrough(x) {
  const face = ((x && x.key) || '').split('|').pop() || '';
  return !face || face === '對手過' || (/(^|、)對手過$/.test(face) && !/下注|加注/.test(face));
}
function nextEntries(cat, item, verb) {
  if (!verb || !cat || !item) return [];
  const segs0 = (item.key || '').split('|');
  const last = segs0[segs0.length - 1] || '';
  const withHero = last ? last + '、你' + verb : '你' + verb;
  const afterHero = (done) => {
    if (done === withHero) return [];
    if (!done.startsWith(withHero + '、')) return null;
    return done.slice(withHero.length + 1).split('、').filter(Boolean);
  };
  const oppOnly = (bits, kinds) => bits && bits.every(b => kinds.includes(b));
  const rank = face => !face ? 0 : face === '對手過' ? 1 : face === '對手下注' ? 2 : 3;
  const found = [];
  for (const x of cat) {
    if (x.pfx !== item.pfx || x.id === item.id || !pfOk(item, x)) continue;
    const segs = (x.key || '').split('|');
    if (x.st === item.st && segs.length === segs0.length
        && segs.slice(0, -1).join('|') === segs0.slice(0, -1).join('|')) {
      const rest = afterHero(segs[segs.length - 1] || '');
      if (verb === '過' && rest && rest.length) {
        const i = rest.findIndex(b => b === '對手下注' || b === '對手超池下注');
        if (i >= 0 && oppOnly(rest.slice(0, i), ['對手過']) && oppOnly(rest.slice(i + 1), ['對手跟'])) found.push(x);
      }
      else if ((verb === '下注' || verb === '加注' || verb === '超池下注') && rest && rest.length && rest[rest.length - 1] === '對手加注' && oppOnly(rest.slice(0, -1), ['對手跟', '對手過'])) found.push(x);
    } else if (item.st < 2 && x.st === item.st + 1 && segs.length === item.st + 2
        && segs.slice(0, -1).slice(0, segs0.length - 1).join('|') === segs0.slice(0, -1).join('|')
        && facingOk(segs[segs.length - 1])) {
      const bits = afterHero(segs.slice(0, -1)[segs.slice(0, -1).length - 1] || '');
      if (bits === null) continue;
      if (verb === '跟' && oppOnly(bits, ['對手跟'])) found.push(x);
      else if (verb === '過' && oppOnly(bits, ['對手過'])) found.push(x);
      else if ((verb === '下注' || verb === '加注' || verb === '超池下注') && bits.length && oppOnly(bits, ['對手跟'])) found.push(x);
    }
  }
  const seen = new Set();
  return found.sort((a, b) => (b.st - a.st) || rank((a.key || '').split('|').pop()) - rank((b.key || '').split('|').pop()) || a.nd.localeCompare(b.nd))
    .filter(x => seen.has(x.id) ? false : (seen.add(x.id), true));
}
function prevEntry(cat, item) {
  if (!cat || !item) return null;
  const segs = (item.key || '').split('|');
  const last = segs[segs.length - 1] || '';
  const m = last.match(/^(?:(.*)、)?你(過|超池下注|下注|跟|加注)(?:、對手.*)?$/);
  if (m && /你(過|超池下注|下注|跟|加注)/.test(last)) {
    const prevFace = m[1] || '';
    const want = segs.slice(0, -1).concat([prevFace]).join('|');
    for (const x of cat) {
      if (x.st !== item.st || x.pfx !== item.pfx || x.id === item.id || !pfOk(item, x)) continue;
      if ((x.key || '') === want) return x;
    }
  }
  if (item.st < 1) return null;
  const completed = segs.slice(0, -1);
  for (const x of cat) {
    if (x.st !== item.st - 1 || x.pfx !== item.pfx || !pfOk(item, x)) continue;
    const ps = (x.key || '').split('|');
    if (ps.length !== item.st) continue;
    if (ps.slice(0, -1).join('|') !== completed.slice(0, -1).join('|')) continue;
    const xFace = ps[ps.length - 1] || '';
    const curDone = completed[completed.length - 1] || '';
    const need = xFace ? xFace + '、你' : '你';
    if (curDone === xFace || curDone.startsWith(need)) return x;
  }
  return null;
}
function nextLab(x) {
  const kind = x.nd.replace(/^(3b_|3c_|lmp_|iso_)/, '').replace(/^[ftr]_/, '');
  const km = {barrel: '繼續下注', delay: '延遲 c-bet', stab: '先行動', first: '先行動', probe: '試探下注',
    vs_probe: '面對試探', vs_barrel: '面對繼續下注', vs_cbet: '面對 c-bet', vs_bet: '面對下注', vs_bet2: '面對下注',
    vs_xr: '被加注', vs_donk: '面對領打', vs_over: '面對超池下注', cbet: 'c-bet', bet: '下注或過牌', lead: '領打'};
  return STN_NAV[x.st] + (km[kind] ? '・' + km[kind] : '');
}
function hrefOf(x, bt) { return x ? x.id + (bt ? '-' + bt : '') : ''; }
function secLab(x) {
  const face = ((x && x.key) || '').split('|').pop() || '';
  const kind = (x && x.nd) || '';
  if (/vs_xr|vs_3b/.test(kind) || /對手加注/.test(face)) return '若被加注';
  if (/over/.test(kind) || /超池/.test(face)) return '若面對超池';
  return '若面對下注';
}
function branchLab(x, item, verb) {
  if (x && item && x.st === item.st + 1) {
    const face = ((x.key || '').split('|').pop() || '');
    if (/超池/.test(face) || /over/.test(x.nd || '')) return '下一街面對超池';
    if (/下注/.test(face) || /vs_bet|vs_probe|vs_donk|vs_barrel|vs_cbet/.test(x.nd || '')) return '下一街面對下注';
    if (verb === '過') return '若對手過';
    if (verb === '跟') return '下一街';
    return '若對手跟注';
  }
  return secLab(x);
}
// 延伸表（沒有例題的後續線，nl2_titles.js 按需產生）：id → {item, parent}；存 localStorage 讓重新整理也找得到
const EXTI = new Map();
const EXT_LS = 'nl2ext1';
function extSave(x, parent) {
  try { const m = JSON.parse(localStorage.getItem(EXT_LS) || '{}'); if (!m[x.id]) { m[x.id] = [x.sp, x.nd, x.pf || '', x.key || '', parent ? parent.id : '']; const ks = Object.keys(m); if (ks.length > 3000) delete m[ks[0]]; localStorage.setItem(EXT_LS, JSON.stringify(m)); } } catch (e) {}
}
function extGet(id) {
  if (EXTI.has(id)) return EXTI.get(id);
  try { const v = JSON.parse(localStorage.getItem(EXT_LS) || '{}')[id]; if (!v || !TITLES || !TITLES.lineByKey) return null;
    const ln = TITLES.lineByKey(v[0], v[1], v[2], v[3]); if (!ln || !ln.visible) return null;
    const x = catItem(v[0], v[1], ln); if (x.id !== id) return null;
    const rec = { item: x, parentId: v[4] }; EXTI.set(id, rec); return rec; } catch (e) { return null; }
}
function allNext(cat, item, verb) {
  const nx = nextEntries(cat, item, verb).slice();
  if (TITLES && TITLES.follow && item && item.ln && verb) for (const f of TITLES.follow(item.sp, item.nd, item.ln, verb)) {
    const x = catItem(item.sp, f.nd, f.line);
    if (nx.some(y => y.id === x.id)) continue;
    nx.push(x);
    if (f.line.syn && !EXTI.has(x.id)) { EXTI.set(x.id, { item: x, parentId: item.id }); extSave(x, item); }
  }
  const rank = face => !face ? 0 : face === '對手過' ? 1 : face === '對手下注' ? 2 : 3;
  return nx.sort((a, b) => (b.st - a.st) || rank((a.key || '').split('|').pop()) - rank((b.key || '').split('|').pop()) || a.nd.localeCompare(b.nd));
}
function nextLinks(cat, item, a, bt) {
  const verb = VERB_OF[a] || (a === 'big' || a === 'small' ? '下注' : '');
  const nx = allNext(cat, item, verb);
  const through = nx.filter(x => x.st === item.st + 1 && isThrough(x));
  const nextOther = nx.filter(x => x.st === item.st + 1 && !through.includes(x));
  const same = nx.filter(x => x.st === item.st);
  const ordered = through.concat(nextOther, same);
  return {
    href: through[0] ? hrefOf(through[0], bt) : (nextOther[0] ? hrefOf(nextOther[0], bt) : ''),
    extras: ordered.map(x => ({ href: hrefOf(x, bt), lab: branchLab(x, item, verb) })),
    all: nx
  };
}
function hrefNext(cat, item, a, bt) {
  return nextLinks(cat, item, a, bt).href;
}
function basisOf(r) { return r.b === 'est' ? '剝削' : 'GTO'; }
function faceTag(cl) {
  const parts = String(cl || '').split('・');
  for (const g of parts) {
    if (/^≤½|^≤1\/2/.test(g)) return '小注';
    if (/^≤⅓|^≤1\/3/.test(g)) return '≤⅓';
    if (/¾|3\/4/.test(g)) return '≥¾';
    if (/超池/.test(g)) return '超池';
    if (/任何尺寸/.test(g)) return '任何尺寸';
  }
  return '';
}
function actText(a, r) {
  let lab = short(a, r);
  if (a === 'r') {
    const p = potFromLab(rawLab(a, r));
    if (p && p.allin) lab = '加注 全下';
    else if (lab === '全下') lab = '加注 全下';
    else if (!/^加注/.test(lab)) lab = '加注';
  }
  return lab;
}
function shownOf(r) { return (TITLES && TITLES.topAct) ? TITLES.topAct(r) : { a: r.a, mix: !!(r.ok && r.ok.length) }; }
function clsAct(a) {
  if (a === 'b33' || a === 'b50' || a === 'b66' || a === 'small') return 'small';
  if (a === 'b75' || a === 'b100' || a === 'b150' || a === 'big') return 'big';
  return a;
}
function gtoMass(freq) {
  const mass = {};
  for (const [k, v] of Object.entries(freq || {})) {
    const a = clsAct(k), n = Number(v);
    if (a && n > 0) mass[a] = (mass[a] || 0) + n;
  }
  return mass;
}
function lowConf(r) {
  if (!r) return false;
  const freq = (r.solver && (r.solver.exact_freqs || r.solver.freq)) || {};
  const boards = Number(r.solver && r.solver.boards);
  const src = String((r.solver && r.solver.src) || '');
  const rnG = r.rn && Number(r.rn.g);
  const crude = src.includes('parent mix') || (Number.isFinite(boards) && boards >= 0 && boards < 3) || (Number.isFinite(rnG) && rnG >= 0 && rnG < 3);
  if (r.b !== 'est') return !!crude && (src.includes('parent mix') || boards === 0 || boards === 1 || rnG === 0 || rnG === 1);
  const ev = String(r.ev || '');
  const n = Number((ev.match(/n=(\d+)/) || [])[1] || 0);
  const samples = (r.solver && r.solver.samples || []).length;
  const a = clsAct(shownOf(r).a);
  const mass = gtoMass(freq);
  const f = Number(mass[a] || 0);
  const best = Object.entries(mass).sort((x, y) => y[1] - x[1])[0];
  if (n && n < 20) return true;
  if (samples && samples < 3 && n && n < 200) return true;
  if (Object.keys(mass).length && f < 0.15) return true;
  if (best && a && clsAct(best[0]) !== a) return true;
  if (crude && (boards < 3 || rnG < 3 || src.includes('parent mix'))) return true;
  return false;
}
function cellMain(r, nd) {
  const sh = shownOf(r);
  const act = actText(sh.a, r), face = isVs(nd) ? faceTag(r.cl) : '';
  return (face ? '面對' + face + ' ' : '') + act + (sh.mix ? '≈' : '');
}
function cellInner(r, nd, href, extras) {
  const main = cellMain(r, nd), b = basisOf(r);
  const act = `<span class="act">${esc(main)}</span>`;
  const sec = (extras || []).map(x => `<a class="jmp sub" href="#${x.href}">${esc(x.lab)}→</a>`).join('');
  const lo = lowConf(r) ? '<small class="lo" title="樣本少或與 GTO 頻率差很多">低把握</small>' : '';
  return `<div class="cell">${act}<small class="df" data-df="${esc(b)}">${esc(b)}</small>${sec}${lo}</div>`;
}
function navHtml(cat, item) {
  if (!cat || !item) return '';
  const bits = [];
  const ext = EXTI.get(item.id);
  const prev = prevEntry(cat, item) || (ext && ext.parentId ? { id: ext.parentId } : null);
  if (prev) bits.push(`<a class="jmp" href="#${prev.id}">↑ 上一步</a>`);
  const seen = new Set();
  for (const v of ['下注', '過', '跟', '加注']) for (const x of nextEntries(cat, item, v)) {
    if (seen.has(x.id)) continue; seen.add(x.id);
    bits.push(`<a class="jmp" href="#${x.id}">→ ${esc(nextLab(x))}</a>`);
  }
  return bits.length ? `<p class="navln">${bits.join('　')}</p>` : '';
}
const nodeVisible = (sp, nd) => TITLES ? TITLES.nodeVisible(sp, nd) : (!REACH.usesReach || !REACH.usesReach(sp, nd) || REACH.visible(sp, nd));
const rowReached = (r, h, line) => TITLES ? TITLES.rowReached(r, h, line) : (!REACH.usesReach(r.sp, r.nd) || REACH.classReached(r.sp, r.nd, h, r));
function gridHtml(sp, nd, me, line, ro, cat) {
  const lines = line ? [line] : (lineList(sp, nd).length ? lineList(sp, nd) : [null]);
  return lines.map(ln => gridOne(sp, nd, me, ln, ro, cat)).join('');
}
function gridMw(sp, nd, me, line, cat) {
  const reached = (r, h) => rowReached(r, h, line);
  const R = L.rows.filter(r => r.sp === sp && r.nd === nd), base = R.filter(r => !r.x);
  const ex = R.filter(r => r.x && !isHiSplitEx(r) && (!me || r.id === me.id) && r.hc.some(h => reached(r, h)));
  const conds = [];
  base.forEach(r => { const k = r.cl || '全部'; if (!conds.includes(k)) conds.push(k); });
  const cols = HCO.filter(h => base.some(r => r.hc.includes(h) && reached(r, h)));
  const condsShown = conds.filter(k => cols.some(h => {
    const r = base.find(r => (r.cl || '全部') === k && r.hc.includes(h));
    return r && reached(r, h);
  }));
  if (!cols.length || !condsShown.length) return '';
  const item = (cat && line) ? catItem(sp, nd, line) : null;
  const cell = (k, h) => {
    const r = base.find(r => (r.cl || '全部') === k && r.hc.includes(h));
    if (!r || !reached(r, h)) return '<td class="na">—</td>';
    const sh = shownOf(r);
    const nl = (item && !/全下/.test(actText(sh.a, r))) ? nextLinks(cat, item, sh.a) : { href: '', extras: [] };
    return `<td class="${ACL(sh.a)}${me && me.id === r.id ? ' me' : ''}">${cellInner(r, nd, nl.href, nl.extras)}</td>`;
  };
  let html = `<div class="tw"><table class="rt lt"><tr><th></th>${cols.map(c => `<th>${dfs(hlabel(c, nd))}</th>`).join('')}</tr>` +
    condsShown.map(k => `<tr data-cl="${esc(k)}"><th class="cl">${dfl(k)}</th>${cols.map(c => cell(k, c)).join('')}</tr>`).join('') + '</table></div>';
  if (ex.length) html += `<p class="small"><span class="lab">${dfs('例外')}</span>　${ex.map(r => `<span class="${me && me.id === r.id ? 'mex' : ''}">${dfl(r.cl)}：${r.hc.filter(c => reached(r, c)).map(c => hlabel(c, r.nd)).join('、')} → <b>${esc(cellMain(r, nd))}</b><small class="df" data-df="${esc(basisOf(r))}">${esc(basisOf(r))}</small></span>`).join('；')}</p>`;
  return html;
}
function gridOne(sp, nd, me, line, ro, cat) {
  const reached = (r, h) => rowReached(r, h, line);
  const R = L.rows.filter(r => r.sp === sp && r.nd === nd);
  const base = R.filter(r => !r.x && !isCtRow(r));
  const ex = R.filter(r => (r.x || isCtRow(r)) && !isHiSplitEx(r) && (!me || r.id === me.id) && r.hc.some(h => reached(r, h)));
  const groups = [];
  const seenG = new Set();
  if (sp === 'mw') groups.push('');
  else {
    for (const r of base) {
      const g = splitCl(r.cl).grp;
      if (!seenG.has(g)) { seenG.add(g); groups.push(g); }
    }
  }
  if (!groups.length) groups.push('');
  const mwHr = (sp === 'mw' && line && line.facts) ? (line.facts.pfr ? 'PFR' : 'CALL') : null;
  const findR = (grp, zh, h) => {
    if (mwHr) {
      return base.find(r => r.hc.includes(h) && r.c && r.c.hr === mwHr)
        || base.find(r => r.hc.includes(h) && r.cl === (mwHr === 'PFR' ? '你是開池者' : '你是跟注者'));
    }
    const want = grp ? grp + '・' + zh : zh;
    const hit = base.find(r => (r.cl || '全部') === want && r.hc.includes(h));
    if (hit) return hit;
    return base.find(r => r.hc.includes(h) && !(r.c && r.c.bt) && (
      (r.cl || '全部') === '全部' && !grp ||
      (grp && (r.cl || '') === grp) ||
      (r.rn && r.rn.k === 'cert' && (!grp || (r.cl || '') === grp || (r.cl || '全部') === '全部'))
    ));
  };
  const cols = HCO.filter(h => groups.some(g => BT_ROWS.some(([, zh]) => { const r = findR(g, zh, h); return r && reached(r, h); })));
  const groupsShown = groups.filter(g => cols.some(h => BT_ROWS.some(([, zh]) => { const r = findR(g, zh, h); return r && reached(r, h); })));
  if (!cols.length || !groupsShown.length) return '';
  const item = (cat && line) ? catItem(sp, nd, line) : null;
  const btOf = zh => (BT_ROWS.find(([, z]) => z === zh) || [''])[0];
  const cell = (g, zh, h) => {
    const r = findR(g, zh, h);
    if (!r || !reached(r, h)) return '<td class="na">—</td>';
    const sh = shownOf(r);
    const nl = (item && !/全下/.test(actText(sh.a, r))) ? nextLinks(cat, item, sh.a, btOf(zh)) : { href: '', extras: [] }; // 全下：沒有後續決定
    return `<td class="${ACL(sh.a)}${me && me.id === r.id ? ' me' : ''}">${cellInner(r, nd, nl.href, nl.extras)}</td>`;
  };
  const head = `<tr><th></th>${cols.map(c => `<th>${dfs(hlabel(c, nd))}</th>`).join('')}</tr>`;
  let body = '';
  for (let i = 0; i < groupsShown.length; i++) {
    const g = groupsShown[i];
    if (groupsShown.length > 1 || g) body += `<tr class="grp"><th class="cl" colspan="${1 + cols.length}">${dfl(g || '全部')}</th></tr>`;
    if (i === 0 || groupsShown.length > 1) body += (i === 0 ? '' : head);
    body += BT_ROWS.map(([, zh]) => `<tr data-cl="${esc(g ? g + '・' + zh : zh)}"${item && i === 0 && btOf(zh) ? ` id="${item.id}-${btOf(zh)}"` : ''}><th class="cl">${dfl(zh)}</th>${cols.map(c => cell(g, zh, c)).join('')}</tr>`).join('');
  }
  let html = `<div class="tw"><table class="rt lt">${head}${body}</table></div>`;
  if (ex.length) html += `<p class="small"><span class="lab">${dfs('例外')}</span>　${ex.map(r => `<span class="${me && me.id === r.id ? 'mex' : ''}">${dfl(r.cl)}：${r.hc.filter(c => reached(r, c)).map(c => hlabel(c, r.nd)).join('、')} → <b>${esc(cellMain(r, nd))}</b><small class="df" data-df="${esc(basisOf(r))}">${esc(basisOf(r))}</small></span>`).join('；')}</p>`;
  return html;
}
function faceHtml(sp, nd, line, ro) { // 這個節點你面對什麼：例題的完整行動線（翻前＋先前各街＋這街）
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
      const cs = x => stOf(nd) ? ' ' + pretty(x.cards) : ''; // 轉牌／河牌：例題寫出每街實際發的牌
      const prev = s.slice(1, -1).map(x => `${x.st}${cs(x)}：${esc(x.txt)}`).join(' → ');
      return `<p class="small muted">你面對（例）：${esc(s[0])} → ${prev ? prev + ' → ' : ''}${l.st}${cs(l)}${l.txt ? '：' + esc(l.txt) : ''}，${face}</p>`; } }
  return '';
}
function dataHtml(sp, nd, line, ro) {
  return `<ul class="dl">${L.rows.filter(r => r.sp === sp && r.nd === nd && r.hc.some(h => rowReached(r, h, line))).map(r => `<li class="small">${r.rofb ? '沿用・' : ''}${r.x ? '例外・' : ''}${esc(r.cl || '全部')}・${r.hc.map(c => hlabel(c, r.nd)).join('、')}：<b>${esc(alab(r.a, r))}</b>${r.ok.length ? '（' + r.ok.map(a => alab(a, r)).join('、') + ' 也可以）' : ''}。${esc(r.why)}<br><span class="muted">${BS[r.b]}｜${esc(r.ev)}${r.hw ? `｜你打過 ${r.hw} 次` : ''}</span></li>`).join('')}</ul>`;
}
let LS = {sp: 'bb', data: false};
function lines() {
  window.__Q = null; const sp = LS.sp, S = L.spots.find(s => s.id === sp), cv = L.cov;
  const al = L.al[sp] || {}, aln = L.aln[sp];
  const alias = Object.keys(al).map(nd => { const [s2, n2] = al[nd].includes(':') ? al[nd].split(':') : [al[nd], nd];
    return `${esc(nodeLabel(sp, nd))} → 照「${esc(L.spots.find(s => s.id === s2).t)}」的「${esc(nodeLabel(s2, n2))}」`; });
  app.innerHTML = `<div class="sec"><b class="h">NL2 行動線對照表</b><p class="small muted">${esc(L.scope)}<br>${esc(L.bias)}${cv ? `<br>你 10/28–11/4 的 ${f0(cv.tot)} 個翻後決定，${pc(cv.cov, cv.tot)} 落在這張表（皆為直接對應；未對應的決策不計入覆蓋）。` : ''}</p>
  <p class="small">怎麼看：標題是這條線從翻前到這一街的行動，<span class="ha">金色粗體</span>是你的動作。一格＝你的動作。走不到的線、牌型不列。<b>≈</b>＝打平（另一個動作也可以）。小字＝根據：池＝玩家池數據（樣本與比較見數據）、GTO＝本機解算器（範圍、代表牌面與設定見數據）。近似＝GTO 近似（兩人 solver），把多人壓縮為最強對手分布；限制見數據。尺寸：格子只標 1/3、1/2、2/3、3/4、1、1.5 或全下（最接近的底池比例）。GTO 照解算樹靠這幾檔（⅔ 也在這組裡）；池估是牌池實際下注均值再靠檔，不是精確到 1%。格子只寫動作和「GTO」或「剝削」（剝削＝牌池估算比 GTO 更賺，不是封閉證明），不列樣本數或頻率。下注、加注會標尺寸（⅓、½、⅔、¾、1、1½ 或全下）。面對下注時，若資料有尺寸分檔，格子會寫門檻（例：面對小注 跟、面對 ≥¾ 棄）；翻牌／轉牌資料沒有分檔時不另造門檻。點動作或「→ 下一步」會跳到同一街的後續表（過→面對下注、下注／加注→被加注）或下一街同一條線的表，對得到就停在同一種牌面列；多人會對在同一條翻前線。後面的表有「↑ 上一步」。棄牌沒有下一步。同一條行動線一張表。橫列固定、跟翻牌同一套，順序是：9 以下低牌面、J/T 高面、K/Q 高面、A 高面、成對面、單色面；欄是牌型。走不到或沒答案是「—」。轉牌、河牌依做決定時的當街牌面歸列（例：K 高翻牌轉 A，算 A 高面；轉出對子，算成對面；同花完成，算單色面）。順子完成、補聽，以及舊的「最高張 9 以下／T 以上」分半，都併入這六列，不另開列。優先序與翻牌相同：單色（3 張以上同花）＞成對＞最高張。格子裡動作、根據（GTO 或剝削）、以及每個「若…」連結各佔一行、置中。下注或加注之後，連「若對手跟注→」（下一街同一條線，你先行動或對手過牌）、「下一街面對下注→」（跟注後對手在下一街先下注，這不是同一街的面對下注），以及「若被加注→」（同一街被加注）。過牌之後，連「若對手過→」（過完進下一街）和「若面對下注→」或「若面對超池→」（同一街對手先下注）。跟注之後若有下一街表，標「下一街→」。已下注的格子不會再標同一街的「若面對下注」。棄牌、全下、河牌已結束的格子不再標「（無後續表）」。有例題的線先列在頁面上；沒有例題的後續線，點連結時才產生「延伸表」（放在頁面最下面，答案取自同一節點的策略列；翻後策略列不分翻前位置），所以跟注、過牌、下注、加注之後都連得到下一步。只有資料裡根本沒有那個決定點時才沒有連結。全下之後沒有後續。樣本很少或剝削動作與 GTO 頻率差很多的格子會標「低把握」。詳細樣本與頻率在「顯示每格的數據」。多人近似每街「下注 1/2」、加注只含全下，面對加注的答案僅適用此尺寸。牌型：頂對好＝超對或頂對 J 以上踢腳；頂對弱＝頂對 T 以下踢腳；中小對含比頂對小的口袋對；強聽＝同花聽、兩頭順；弱聽＝卡順或兩張高牌。</p>
  ${L.notes ? `<details class="small muted"><summary>依據與解算設定註解</summary>${L.notes.map((n, i) => `<p>${i + 1}. ${esc(n)}</p>`).join('')}</details>` : ''}
  <div class="chips">${L.spots.map(s => `<button class="chip${s.id === sp ? ' on' : ''}" data-sp="${s.id}">${esc(s.t.split('（')[0])}</button>`).join('')}</div>
  <button class="btn tg" data-tg="1">${LS.data ? '收起數據' : '顯示每格的數據'}</button>　<a class="btn" href="#drill">練習這張表 →</a></div>` + defsHtml(false) + `
  <div class="sec"><b class="h">${esc(S.t)}</b><span class="ev">${esc(S.sub)}</span>${cv && cv.by[sp] ? `<span class="ev">你 ${cv.by[sp][0]}/${cv.by[sp][1]} 個決定在表上</span>` : ''}</div>` +
  (function(){ const cat = lineCatalog(sp);
  return nodesOf(sp).filter(nd => nodeVisible(sp, nd)).flatMap(nd => {
    const use = lineList(sp, nd).length ? lineList(sp, nd) : [null];
    return use.map(ln => { const g = gridHtml(sp, nd, null, ln, null, cat); if (!g) return '';
      const item = catItem(sp, nd, ln);
      return `<div class="sec" data-node="${sp}/${nd}" id="${item.id}"><b class="ttl">${ln ? ln.titleHtml : esc(nodeLabel(sp, nd))}</b>${navHtml(cat, item)}${faceHtml(sp, nd, ln)}${g}${LS.data ? dataHtml(sp, nd, ln) : ''}</div>`; });
  }).join(''); })() + '<div id="extwrap"></div>' +
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
  return { tx, hi, ct, sz, bt: textureNow(b, k), ln: F.tb ? 'tb' : 'oth', prior: [F.checkTurn && 'check_turn', F.betBet && 'bet_bet'].filter(Boolean), hr: F.pfr ? 'PFR' : 'CALL' };
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
  <div id="qbox" class="sec"><p class="qs">${esc(sp.t.split('（')[0])}｜<span class="ttl">${(TITLES && TITLES.titleForEg(r.sp, r.nd, e) || {}).titleHtml || esc(nodeLabel(r.sp, r.nd))}</span>${btTitle(r.nd, r, e)}。你的牌 ${pretty(h)}，你要怎麼做？</p>
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
  <p class="small"><b class="ttl">${(TITLES && TITLES.titleForEg(r.sp, r.nd, q.e) || {}).titleHtml || esc(nodeLabel(r.sp, r.nd))}</b>${btTitle(r.nd, r, q.e)}（框起來的是這題）</p>${gridHtml(r.sp, r.nd, r, TITLES && TITLES.titleForEg(r.sp, r.nd, q.e))}<p class="small"><a href="#lines" data-go="${r.sp}">看完整對照表</a></p></div>${defsHtml(false)}`;
}
function clsName(q) { return q.row.hc.map(h => stOf(q.row.nd) === 2 && ['DRAW', 'WDRAW'].includes(h) ? hlabel(h, q.row.nd) : L.hc[h]).join('／'); }
// ---------- 路由 ----------
const TABS = ['card', 'lines', 'drill', 'river'];
function hashInfo() {
  const h = (location.hash || '#card').slice(1);
  const m = h.match(/^ln-(\w+)-([\w]+)-([a-z0-9]+)(?:-(A_high|KQ_high|mid_high|low|paired|mono))?$/);
  if (m) return {tab: 'lines', sp: m[1], table: 'ln-' + m[1] + '-' + m[2] + '-' + m[3], id: h, row: m[4] || ''};
  if (h === 'lines') return {tab: 'lines'};
  if (h === 'card' || h === '') return {tab: 'card'};
  if (h === 'drill' || h === 'river') return {tab: h};
  return {tab: 'card'};
}
function extHtml(id) { // 延伸表的整段 HTML（被連到時才產生）
  const rec = extGet(id); if (!rec) return '';
  const x = rec.item, cat = lineCatalog(x.sp);
  const g = gridHtml(x.sp, x.nd, null, x.ln, null, cat); if (!g) return '';
  return `<div class="sec ext" data-node="${x.sp}/${x.nd}" id="${x.id}"><b class="ttl">${x.ln.titleHtml}</b>${navHtml(cat, x)}<p class="small muted">延伸表：這條線在資料裡沒有實際例題，答案取自同一節點的策略列（翻後策略列不分翻前位置）。</p>${g}${LS.data ? dataHtml(x.sp, x.nd, x.ln) : ''}</div>`;
}
function goAnchor(info) {
  if (!info || !info.id || !document.getElementById) return;
  if (!document.getElementById(info.table)) {
    const rec = extGet(info.table), wrap = document.getElementById('extwrap');
    if (rec && wrap && rec.item.sp === LS.sp) wrap.insertAdjacentHTML('beforeend', extHtml(info.table));
  }
  const el = document.getElementById(info.id) || document.getElementById(info.table);
  if (el) el.scrollIntoView({block: 'start', behavior: 'smooth'});
}
function route() {
  const info = hashInfo(), tab = info.tab;
  document.querySelectorAll('.topb').forEach(e => e.classList.toggle('on', e.dataset.t === tab));
  if (info.sp && info.sp !== LS.sp) LS.sp = info.sp;
  const stay = tab === 'lines' && LS.view === 'lines' && app.querySelector && app.querySelector('[data-node]');
  if (!stay) {
    if (tab === 'card') card();
    else if (tab === 'lines') lines();
    else drill(tab === 'river' ? 'riv' : (DF === 'riv' ? 'all' : DF));
  }
  LS.view = tab === 'lines' ? 'lines' : tab;
  if (info.id) { if (typeof requestAnimationFrame === 'function') requestAnimationFrame(() => goAnchor(info)); else goAnchor(info); }
  else if (!stay) window.scrollTo(0, 0);
}
window.__QNEXT = () => drill();
app.addEventListener('click', e => {
  const t = e.target;
  const df = t.closest('[data-df]'); if (df) { showDef(df.dataset.df); return; }
  if (t.closest('[data-next]')) { drill(); return; }
  const f = t.closest('[data-f]'); if (f) { drill(f.dataset.f); return; }
  const sp = t.closest('[data-sp]'); if (sp) {
    LS.sp = sp.dataset.sp;
    if (location.hash && String(location.hash).startsWith('#ln-')) location.hash = 'lines';
    lines();
    return;
  }
  if (t.closest('[data-tg]')) { LS.data = !LS.data; lines(); return; }
  const go = t.closest('[data-go]'); if (go) LS.sp = go.dataset.go;
});
if (window.__LINES_QA) window.__linesQA = { tableOnly, egCond, egInException, egOk,
  answer: a => lanswer(a, {classList: {add() {}}}),
  render: sp => { LS.sp = sp; lines(); }, pool, card, DEF, defsHtml, drill, gridHtml, story, nodesOf, stOf, nodeVisible, rowReached, REACH, TITLES, lineList,
  lineCatalog, nextEntries, prevEntry, nextLinks, allNext, extHtml, extGet, EXTI, catItem, lid, keyForLid, shownOf, VERB_OF, isThrough, branchLab, facingOk
};
window.addEventListener('hashchange', route); route();
})();
