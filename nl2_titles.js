// NL2 節點標題：寫成明確行動線；同一節點若有多條先前線就拆表。
// 逐線、逐格：線上你先前每個決定都到該決定點查主答案，走不到的格／線／節點不顯示（見 build 內說明）。
// 獨立驗證：tools/reach_verify.js（從畫面讀表，不用這裡的程式）。
(function (root) {
  const HANDS = ['S', 'TPG', 'TPW', 'MID', 'DRAW', 'WDRAW', 'AIR'];
  const STN = ['翻牌', '轉牌', '河牌'];
  const PFX = ['3b_', '3c_', 'lmp_', 'iso_'];

  function esc(s) {
    return String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }
  function ha(s) { return `<span class="ha">${esc(s)}</span>`; }
  function streetOf(nd) { return /(^|_)f_/.test(nd) ? 0 : /(^|_)t_/.test(nd) ? 1 : 2; }
  function splitNd(nd) {
    for (const p of PFX) if (nd.startsWith(p)) return { pfx: p, kind: nd.slice(p.length) };
    return { pfx: '', kind: nd };
  }
  function bareKind(kind) { return String(kind || '').replace(/^[ftr]_/, ''); }
  function verb(a) {
    return { x: '過', c: '跟', f: '棄', b: '下注', r: '加注', a: '全下' }[String(a || '')[0]] || a;
  }
  function actsOfSeg(seg, me) {
    return String(seg || '').split(' ').filter(Boolean).map(tok => {
      const i = tok.indexOf(':'), p = tok.slice(0, i), a = tok.slice(i + 1);
      return { hero: p === me, pos: p, k: a[0], verb: verb(a) };
    });
  }
  // 一街的動作 → 你／對手＋動作（照實寫；只做三件事：對手棄牌不寫、連續相同的對手動作併成一次、
  // 對手在你行動前跟別的對手的注不寫）。對手全下：本街已有人下注 → 對手加注；沒有 → 對手下注（表不分尺寸）。
  function canonSeg(acts) {
    const a = []; let bet = false;
    for (const x of acts) {
      if (!x.hero && x.verb === '棄') continue;
      const v = (!x.hero && x.verb === '全下') ? (bet ? '加注' : '下注') : x.verb;
      if (/下注|加注|全下/.test(x.verb)) bet = true;
      const bit = (x.hero ? '你' : '對手') + v;
      if (a.length && a[a.length - 1] === bit && !x.hero) continue;
      a.push(bit);
    }
    return a.filter((b, i) => !(b === '對手跟' && i > 0 && /^對手(下注|加注|全下)/.test(a[i - 1])));
  }
  // 線的識別：各街（到本街為止）已發生的動作，以「|」分街，位置固定（空的街也保留）
  function lineKeyFromEg(e, st) {
    const segs = String(e.l || '').split('/');
    const parts = [];
    for (let i = 0; i <= st; i++) parts.push(canonSeg(actsOfSeg(segs[i], e.me)).join('、'));
    return parts.join('|');
  }
  function segsFromKey(key) { return key ? key.split('|') : []; }

  const PRE_ORDER = ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB'];
  function preflopTokens(e) {
    if (!e) return [{ h: false, t: '翻前已完成' }];
    const me = e.me, t = e.t, pa = e.pa, pc = (e.pc || []).filter(Boolean);
    const nm = p => p || '對手';
    const out = [];
    if (t === '3BP') {
      const opener = pc[0], three = pa;
      const cold = pc.slice(1).filter(p => p !== three && p !== opener);
      out.push({ h: opener === me, t: opener === me ? `你 ${nm(opener)} 開` : `${nm(opener)} 開` });
      out.push({ h: three === me, t: three === me ? '你 3-bet' : `${nm(three)} 3-bet` });
      for (const p of cold) out.push({ h: p === me, t: p === me ? `你 ${p} 跟` : `${p} 跟` }); // 多人：冷跟 3-bet 的人
      if (three === me) out.push({ h: false, t: `${nm(opener)} 跟` });
      else if (opener === me) out.push({ h: true, t: `你 ${nm(me)} 跟` });
      else if (!cold.includes(me)) out.push({ h: false, t: `${nm(opener)} 跟` });
      else out.push({ h: false, t: `${nm(opener)} 跟` });
      return out;
    }
    if (t === 'ISO') {
      const iso = pa, limp = pc[0];
      out.push({ h: limp === me, t: limp === me ? `你 ${nm(limp)} 溜入` : `${nm(limp)} 溜入` });
      out.push({ h: iso === me, t: iso === me ? '你加注隔離' : `${nm(iso)} 加注隔離` });
      out.push({ h: me !== iso, t: (me !== iso) ? `你 ${nm(me)} 跟` : `${nm(limp)} 跟` });
      return out;
    }
    if (t === 'LMP' || !pa) { // 溜入底池：逐人寫；你的部分才上金色
      let seq = [];
      if (e.pretext) {
        for (const x of String(e.pretext).split('，')) {
          const m = x.match(/^(你（(\w+)）|(\w+)) (跟注|過牌|加注|棄牌)/);
          if (!m || m[4] === '棄牌') continue;
          const p = m[2] || m[3];
          seq.push({ p, v: m[4] === '過牌' ? '過' : m[4] === '加注' ? '加注' : '溜入' });
        }
      }
      if (!seq.length) seq = pc.slice().sort((x, y) => PRE_ORDER.indexOf(x) - PRE_ORDER.indexOf(y)).map(p => ({ p, v: p === 'BB' ? '過' : '溜入' }));
      for (const x of seq) out.push({ h: x.p === me, t: x.p === me ? `你 ${x.p} ${x.v}` : `${x.p} ${x.v}` });
      return out;
    }
    // SRP / default
    const opener = pa, callers = pc.filter(p => p !== opener);
    out.push({ h: opener === me, t: opener === me ? `你 ${nm(opener)} 開` : `${nm(opener)} 開` });
    if (callers.length > 1) {
      const others = callers.filter(p => p !== me);
      if (callers.includes(me)) {
        if (others.length) out.push({ h: false, t: others.map(nm).join('、') + ' 跟' });
        out.push({ h: true, t: `你 ${nm(me)} 跟` });
      } else {
        out.push({ h: false, t: callers.map(nm).join('、') + ' 跟' });
      }
    } else if (callers.length === 1) {
      const c = callers[0];
      out.push({ h: c === me, t: c === me ? `你 ${nm(c)} 跟` : `${nm(c)} 跟` });
    }
    return out;
  }

  function questionFor(kind, curSeg) { // 照本街實際狀態問：面對下注／加注 → 你要怎麼做；否則下注或過牌
    const bits = String(curSeg || '').split('、').filter(Boolean);
    if (bits.length && /^對手(下注|加注|全下|超池下注)/.test(bits[bits.length - 1])) return '你要怎麼做？';
    if (bits.length) return '輪到你，下注或過牌？';
    return '你先行動，下注或過牌？';
  }

  function buildTitle(preToks, segs, kind, st) {
    const parts = [];
    const prePlain = preToks.map(x => x.t).join('，');
    const preHtml = preToks.map(x => x.h ? ha(x.t) : esc(x.t)).join('，');
    parts.push({ plain: '翻前：' + prePlain, html: '翻前：' + preHtml });
    for (let i = 0; i <= st; i++) {
      const name = STN[i];
      let seg = segs[i] || '';
      if (i === st && bareKind(kind) === 'vs_over') seg = seg.replace(/對手下注$/, '對手超池下注'); // 跟一般面對下注的表分開
      if (i < st) {
        // 已完成的街
        if (!seg) continue;
        const html = seg.split('、').map(bit => bit.startsWith('你') ? ha(bit) : esc(bit)).join('、');
        parts.push({ plain: name + '：' + seg, html: name + '：' + html });
      } else {
        const q = questionFor(kind, seg);
        let plain, html;
        if (seg) {
          const htmlSeg = seg.split('、').map(bit => bit.startsWith('你') ? ha(bit) : esc(bit)).join('、');
          plain = name + '：' + seg + '，' + q;
          html = name + '：' + htmlSeg + '，' + ha(q);
        } else {
          plain = name + '：' + q;
          html = name + '：' + ha(q);
        }
        parts.push({ plain, html });
      }
    }
    return { titleText: parts.map(p => p.plain).join(' → '), titleHtml: parts.map(p => p.html).join(' → ') };
  }

  function mostCommon(arr) {
    const m = new Map();
    for (const x of arr) m.set(x, (m.get(x) || 0) + 1);
    return [...m.entries()].sort((a, b) => b[1] - a[1])[0];
  }

  // ---------- 可達性（逐線、逐格）----------
  // 一個牌型 × 一列條件，能不能走到這條線：這條線上你先前的每一個決定（翻牌、轉牌、本街先前），
  // 到「那個決定點」的表查這個牌型的主答案（≈ 的替代動作不算），必須就是線上寫的動作。
  // 牌型逐街沿用同一標籤；牌面狀態＝翻牌質地＋各街最高張（T 以上／9 以下），例外列照條件優先。
  const TXS = ['A_high', 'KQ_high', 'mid_high', 'low', 'paired', 'mono'];
  const NEED = { 過: ['x'], 下注: ['small', 'big'], 全下: ['big', 'small', 'r'], 跟: ['c'], 加注: ['r'] };
  function boardStates(S) {
    const out = [], seen = new Set();
    for (const tx of TXS) {
      const h0s = ['A_high', 'KQ_high', 'mid_high'].includes(tx) ? ['T'] : tx === 'low' ? ['L'] : ['T', 'L'];
      for (const h0 of h0s) for (const h1 of (h0 === 'T' ? ['T'] : ['T', 'L'])) for (const h2 of (h1 === 'T' ? ['T'] : ['T', 'L'])) {
        const hi = [h0, h1, h2], k = tx + hi.slice(0, S + 1).join('');
        if (!seen.has(k)) { seen.add(k); out.push({ tx, hi }); }
      }
    }
    return out;
  }
  function lineFacts(segs, preToks) {
    const bits = i => (segs[i] || '').split('、').filter(Boolean);
    const firstBet = i => { for (const b of bits(i)) { if (/^對手(下注|全下)/.test(b)) return 'v'; if (/^你(下注|全下)/.test(b)) return 'h'; } return ''; };
    const heroAgg = i => bits(i).some(b => /^你(下注|全下|加注)/.test(b));
    return {
      tb: segs.length >= 3 && firstBet(0) === 'v' && firstBet(1) === 'v' && firstBet(2) === 'v',
      checkTurn: segs.length >= 3 && bits(1).includes('你過') && !heroAgg(1),
      betBet: segs.length >= 3 && heroAgg(0) && heroAgg(1),
      // 翻前加注者（資料的「你是開池者」）＝最後加注的人：你 3-bet／你加注隔離，或你開池且沒人 3-bet
      pfr: preToks.some(x => x.h && /3-bet|加注隔離/.test(x.t)) || (preToks.some(x => x.h && /開$/.test(x.t)) && !preToks.some(x => /3-bet/.test(x.t)))
    };
  }
  // 列條件是否符合：true 一定符合；'maybe' 有不追蹤的條件（下注尺寸、河牌牌型）；false 不符
  function rowFits(r, s, street, F) {
    let maybe = false;
    for (const [k, v] of Object.entries(r.c || {})) {
      if (k === 'tx') { if (s.tx !== v) return false; }
      else if (k === 'hi') { if (s.hi[street] !== v) return false; }
      else if (k === 'ln') { if ((v === 'tb') !== F.tb) return false; }
      else if (k === 'prior') { if ((v === 'check_turn' && !F.checkTurn) || (v === 'bet_bet' && !F.betBet)) return false; }
      else if (k === 'hr') { if ((v === 'PFR') !== F.pfr) return false; }
      else maybe = true;
    }
    return maybe ? 'maybe' : true;
  }

  function build(L) {
    const nodeIndex = new Map();
    const nodeList = [];
    for (const r of L.rows) {
      const key = r.sp + '|' + r.nd;
      if (!nodeIndex.has(key)) {
        const { pfx, kind } = splitNd(r.nd);
        const rec = { sp: r.sp, nd: r.nd, pfx, kind, st: streetOf(r.nd), key };
        nodeIndex.set(key, { rec, rows: [] });
        nodeList.push(rec);
      }
      nodeIndex.get(key).rows.push(r);
    }
    const rowsOf = (sp, nd) => (nodeIndex.get(sp + '|' + nd) || { rows: [] }).rows;
    // 決定點：情境＋前綴＋街＋這個決定之前的完整行動（來自各節點例題）→ 節點
    const DECI = new Map();
    for (const rec of nodeList) for (const r of nodeIndex.get(rec.key).rows) for (const e of (r.eg || [])) {
      if (String(e.l || '').split('/').length !== rec.st + 1) continue;
      const k = [rec.sp, rec.pfx, rec.st, lineKeyFromEg(e, rec.st)].join('#');
      if (!DECI.has(k)) DECI.set(k, new Set());
      DECI.get(k).add(rec.nd);
    }
    function decisionsOf(rec, key) {
      const segs = segsFromKey(key), out = [];
      for (let i = 0; i <= rec.st; i++) {
        const bits = (segs[i] || '').split('、').filter(Boolean);
        bits.forEach((b, j) => {
          if (!b.startsWith('你')) return;
          const prefix = segs.slice(0, i).concat([bits.slice(0, j).join('、')]).join('|');
          const nds = [...(DECI.get([rec.sp, rec.pfx, i, prefix].join('#')) || [])];
          out.push({ st: i, verb: b.slice(1), need: NEED[b.slice(1)] || [], nds, prefix });
        });
      }
      return out;
    }
    function primary(sp, nd, h, s, street, F) {
      const R = rowsOf(sp, nd).filter(r => r.hc.includes(h));
      const out = new Set(); let sure = false;
      for (const r of R) if (r.x) { const f = rowFits(r, s, street, F); if (f) { out.add(r.a); if (f === true) sure = true; } }
      if (!sure) for (const r of R) if (!r.x && rowFits(r, s, street, F)) out.add(r.a);
      return out;
    }

    const lineMap = new Map();
    const removed = [];
    for (const rec of nodeList) {
      const rows = nodeIndex.get(rec.key).rows;
      const buckets = new Map();
      for (const r of rows) for (const e of (r.eg || [])) {
        if (String(e.l || '').split('/').length !== rec.st + 1) continue;
        const key = lineKeyFromEg(e, rec.st);
        if (!buckets.has(key)) buckets.set(key, { key, egs: [], er: [] });
        buckets.get(key).egs.push(e); buckets.get(key).er.push({ e, r });
      }
      if (!buckets.size) { const k0 = Array(rec.st + 1).fill('').join('|'); buckets.set(k0, { key: k0, egs: [], er: [] }); }
      const lines = [];
      for (const b of buckets.values()) {
        const sig = e => JSON.stringify({ t: e.t, me: e.me, pa: e.pa, pc: e.pc, pretext: e.pretext || '' });
        const top = (mostCommon(b.egs.map(sig)) || [])[0];
        const eObj = top ? b.egs.find(e => sig(e) === top) : null;
        const segs = segsFromKey(b.key);
        const preToks = preflopTokens(eObj || guessPre(rec));
        const titles = buildTitle(preToks, segs, rec.kind, rec.st);
        const F = lineFacts(segs, preToks);
        const decs = decisionsOf(rec, b.key);
        const states = boardStates(rec.st);
        const cache = new Map();
        function rowOk(r, h) {
          if (r.sp !== rec.sp || r.nd !== rec.nd || !r.hc.includes(h)) return false;
          const ck = r.id + '|' + h;
          if (cache.has(ck)) return cache.get(ck);
          if (root.__NL2_NOFILTER) return true; // 只給 QA（tools/reach_verify.js --nofilter）看「不過濾會出現什麼」
          let ok = false;
          if (decs.every(d => d.nds.length)) {
            for (const s of states) {
              if (!rowFits(r, s, rec.st, F)) continue;
              if (!r.x && rows.some(x => x.x && x.hc.includes(h) && rowFits(x, s, rec.st, F) === true)) continue; // 這個牌面由例外列代表
              if (decs.every(d => d.nds.some(nd => [...primary(rec.sp, nd, h, s, d.st, F)].some(a => d.need.includes(a))))) { ok = true; break; }
            }
          }
          cache.set(ck, ok);
          return ok;
        }
        const hands = HANDS.filter(h => rows.some(r => !r.x && rowOk(r, h)));
        // 標題翻前位置改用「走得到的格」的例題（例題才對得上標題）；翻前角色不同就不換
        let eUse = eObj, tUse = titles;
        const egR = b.er.filter(x => x.r.hc.some(h => rowOk(x.r, h))).map(x => x.e);
        const top2 = (mostCommon(egR.map(sig)) || [])[0];
        if (top2 && top2 !== (eObj && sig(eObj))) {
          const e2 = egR.find(e => sig(e) === top2), p2 = preflopTokens(e2);
          if (lineFacts(segs, p2).pfr === F.pfr) { eUse = e2; tUse = buildTitle(p2, segs, rec.kind, rec.st); }
        }
        const visible = hands.length > 0;
        if (!visible) {
          const miss = decs.filter(d => !d.nds.length);
          removed.push({ sp: rec.sp, nd: rec.nd, line: tUse.titleText, key: b.key,
            reason: miss.length ? miss.map(d => `${STN[d.st]}「${d.prefix.split('|').pop() || '你先行動'}」之後你${d.verb}：資料裡沒有這個決定點`).join('；')
              : '沒有任何牌型照前面各街的答案會走到這條線' });
        }
        lines.push({ id: rec.sp + '/' + rec.nd + '#' + lines.length, key: b.key, eg: eUse, facts: F, decisions: decs,
          titleText: tUse.titleText, titleHtml: tUse.titleHtml, nEg: b.egs.length, hands, visible, rowOk });
      }
      lineMap.set(rec.key, lines);
    }

    function guessPre(rec) {
      for (const r of L.rows) if (r.sp === rec.sp && (r.eg || [])[0]) return r.eg[0];
      return { t: 'SRP', me: rec.sp === 'bb' ? 'BB' : 'BTN', pa: 'BTN', pc: ['BB'] };
    }
    function lines(sp, nd) { return (lineMap.get(sp + '|' + nd) || []).filter(ln => ln.visible); }
    function nodeVisible(sp, nd) { return lines(sp, nd).length > 0; }
    function rowReached(r, h, line) {
      if (line) return line.visible && line.rowOk(r, h);
      return lines(r.sp, r.nd).some(ln => ln.rowOk(r, h));
    }
    function titleForEg(sp, nd, e) { // 只回傳這個例題自己的線（不再退回第一條）
      const rec = nodeIndex.get(sp + '|' + nd);
      if (!rec) return null;
      const k = lineKeyFromEg(e, rec.rec.st);
      return lines(sp, nd).find(ln => ln.key === k) || null;
    }
    function dump() {
      const out = {};
      for (const rec of nodeList) {
        const ls = lineMap.get(rec.key) || [];
        out[rec.key] = { visible: nodeVisible(rec.sp, rec.nd), st: rec.st, nLines: ls.filter(l => l.visible).length, nDropped: ls.filter(l => !l.visible).length,
          lines: ls.filter(l => l.visible).map(l => ({ key: l.key, hands: l.hands })) };
      }
      return out;
    }
    function audit() {
      const all = [];
      let nSplit = 0, nTables = 0, nOmittedNodes = 0;
      for (const rec of nodeList) {
        const ls = lineMap.get(rec.key) || [];
        const shown = ls.filter(l => l.visible), dropped = ls.filter(l => !l.visible);
        if (shown.length > 1) nSplit++;
        nTables += shown.length;
        if (!shown.length) nOmittedNodes++;
        all.push({ sp: rec.sp, nd: rec.nd, st: rec.st,
          old: (L.node_labels && L.node_labels[rec.sp] && L.node_labels[rec.sp][rec.nd]) || (L.nd && L.nd[rec.nd]) || rec.nd,
          shown: shown.map(l => ({ title: l.titleText, key: l.key, hands: l.hands.slice(), nEg: l.nEg })),
          dropped: dropped.map(l => ({ title: l.titleText, key: l.key, reason: (removed.find(x => x.sp === rec.sp && x.nd === rec.nd && x.key === l.key) || {}).reason })),
          split: shown.length > 1, nShown: shown.length, nDropped: dropped.length });
      }
      return { all, removed, unsure: [], nNodes: nodeList.length, nSplit, nTables, nOmittedNodes };
    }
    return { lines, nodeVisible, rowReached, titleForEg, lineKeyFromEg, dump, audit, HANDS };
  }

  root.NL2TITLES = { build, lineKeyFromEg, streetOf, splitNd };
})(typeof window !== 'undefined' ? window : globalThis);
