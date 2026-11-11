// NL2 節點標題：寫成明確行動線；同一節點若有多條先前線就拆表。
// 逐線由親節點「實際答案」（牌型 × 牌面條件）往下追，走不到的線／列／節點不顯示。
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
  function normSeg(acts) {
    const parts = [];
    for (const a of acts) {
      if (!a.hero && a.verb === '棄') continue; // 對手棄牌不改變這條線
      const v = (!a.hero && a.verb === '全下') ? '加注' : a.verb;
      const bit = (a.hero ? '你' : '對手') + v;
      if (parts.length && parts[parts.length - 1] === bit && !a.hero) continue; // 連續的對手過／跟併成一次
      parts.push(bit);
    }
    return parts.join('、');
  }
  // 線的識別：已完成各街＋本街已發生的動作（不含尺寸）
  function semanticSeg(seg) {
    if (!seg) return '';
    const bits = seg.split('、').filter(Boolean);
    const you = bits.filter(b => b.startsWith('你'));
    const vBet = bits.find(b => /^對手(下注|加注)/.test(b));
    const youBet = you.find(b => /下注|全下/.test(b));
    const youRaise = you.find(b => b === '你加注');
    const youCall = you.find(b => b === '你跟');
    const youCheck = you.includes('你過') || you.find(b => b === '你過');
    const villFirst = bits[0] && bits[0].startsWith('對手');
    if (vBet && (youCall || youRaise)) {
      return (youCheck && bits.indexOf('你過') < bits.indexOf(vBet) ? '你過、' : '') + vBet + '、' + (youRaise || youCall) + (youRaise && bits.includes('對手跟') ? '、對手跟' : '');
    }
    if (youBet) {
      const after = [];
      if (bits.includes('對手跟')) after.push('對手跟');
      if (bits.includes('對手加注')) after.push('對手加注');
      if (youCall && bits.includes('對手加注')) after.push('你跟');
      return (villFirst && bits[0] === '對手過' ? '對手過、' : '') + youBet + (after.length ? '、' + after.join('、') : '');
    }
    if (vBet && !youCall && !youRaise && !youBet) {
      return (bits[0] === '你過' ? '你過、' : '') + vBet; // 本街你已過、對手下注，等你回應
    }
    if (youCheck) return villFirst ? '對手過、你過' : (bits.some(b => b === '對手過') ? '你過、對手過' : '你過');
    if (bits.length && bits.every(b => b === '對手過')) return '對手過';
    return seg;
  }
  function lineKeyFromEg(e, st) {
    const segs = String(e.l || '').split('/');
    const parts = [];
    for (let i = 0; i <= st && i < segs.length; i++) {
      const acts = actsOfSeg(segs[i], e.me);
      if (!acts.length) continue;
      const n = semanticSeg(normSeg(acts));
      if (n) parts.push(n);
    }
    return parts.join('|');
  }
  function segsFromKey(key) { return key ? key.split('|') : []; }

  function lastHeroK(segText) {
    const m = [...String(segText || '').matchAll(/你(過|跟|棄|下注|加注|全下)/g)];
    if (!m.length) return null;
    return { 過: 'x', 跟: 'c', 棄: 'f', 下注: 'b', 加注: 'r', 全下: 'a' }[m[m.length - 1][1]];
  }
  function viaOfK(k) {
    if (k === 'x') return 'check';
    if (k === 'c') return 'call';
    if (k === 'r') return 'raise';
    if (k === 'b' || k === 'a') return 'bet';
    return null;
  }
  // 這一段完成的街，對應哪種親節點（kind）
  function kindsForSeg(segText) {
    const s = segText || '';
    if (/你跟|你加注/.test(s) && /對手下注|對手加注/.test(s)) {
      return ['vs_cbet', 'vs_donk', 'vs_bet', 'vs_over', 'vs_barrel', 'vs_probe', 'vs_xr'];
    }
    if (/你下注|你全下/.test(s)) {
      return ['cbet', 'stab', 'first', 'lead', 'bet', 'barrel', 'delay', 'probe'];
    }
    if (/你過/.test(s)) {
      return ['cbet', 'stab', 'first', 'lead', 'bet', 'barrel', 'delay', 'probe'];
    }
    return [];
  }

  function actsSet(r) { return new Set([r.a, ...(r.ok || [])]); }
  function viaMatch(r, via) {
    const A = actsSet(r);
    if (via === 'call') return A.has('c');
    if (via === 'raise') return A.has('r');
    if (via === 'check') return A.has('x');
    if (via === 'bet') return A.has('small') || A.has('big');
    return false;
  }
  function txBucket(cl, c) {
    const s = cl || '';
    if (/A 高面|K\/Q 高面|J\/T 高面|最高張 T 以上/.test(s)) return 'high';
    if (/9 以下|最高張 9 以下/.test(s)) return 'low';
    if (/成對面/.test(s)) return 'pair';
    if (/單色面/.test(s)) return 'mono';
    if (c && c.hi === 'T') return 'high';
    if (c && c.hi === 'L') return 'low';
    if (c && c.tx) {
      if (/A_high|KQ|JT|high/i.test(c.tx)) return 'high';
      if (/low|9/i.test(c.tx)) return 'low';
      if (/pair/i.test(c.tx)) return 'pair';
      if (/mono|flush|tone/i.test(c.tx)) return 'mono';
    }
    return 'all';
  }
  function txCompat(parentB, childB) {
    if (childB === 'all' || parentB === 'all') return true;
    if (childB === parentB) return true;
    if ((parentB === 'pair' || parentB === 'mono') && (childB === 'high' || childB === 'low')) return 'unsure';
    if ((childB === 'pair' || childB === 'mono') && (parentB === 'high' || parentB === 'low')) return 'unsure';
    return false;
  }

  function preflopTokens(e) {
    if (!e) return [{ h: false, t: '翻前已完成' }];
    const me = e.me, t = e.t, pa = e.pa, pc = (e.pc || []).filter(Boolean);
    const nm = p => p || '對手';
    const out = [];
    if (t === '3BP') {
      const opener = pc[0], three = pa;
      out.push({ h: opener === me, t: opener === me ? `你 ${nm(opener)} 開` : `${nm(opener)} 開` });
      out.push({ h: three === me, t: three === me ? '你 3-bet' : `${nm(three)} 3-bet` });
      if (three === me) out.push({ h: false, t: `${nm(opener)} 跟` });
      else out.push({ h: true, t: `你 ${nm(me)} 跟` });
      return out;
    }
    if (t === 'ISO') {
      const iso = pa, limp = pc[0];
      out.push({ h: limp === me, t: limp === me ? `你 ${nm(limp)} 溜入` : `${nm(limp)} 溜入` });
      out.push({ h: iso === me, t: iso === me ? '你加注隔離' : `${nm(iso)} 加注隔離` });
      out.push({ h: limp === me || (me !== iso), t: (me !== iso) ? `你 ${nm(me)} 跟` : `${nm(limp)} 跟` });
      return out;
    }
    if (t === 'LMP' || !pa) {
      if (e.pretext) {
        const short = String(e.pretext).replace(/UTG 棄牌，/g, '').replace(/棄牌，/g, '棄，');
        const clipped = short.length > 36 ? '溜入底池，你（' + me + '）' : short;
        return [{ h: true, t: clipped.indexOf('你') >= 0 ? clipped : `溜入底池，你（${me}）` }];
      }
      return [{ h: true, t: `溜入底池，你（${me}）` }];
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

  function questionFor(kind, curSeg) {
    if (/vs_3b/.test(kind)) return '你要怎麼做？';
    if (/vs_xr/.test(kind)) return '你要怎麼做？';
    if (/vs_/.test(kind)) return '你要怎麼做？';
    if (curSeg && /對手過/.test(curSeg) && !/你(?:過|跟|下注|加注|全下)/.test(curSeg.split('對手過').pop() || '')) {
      return '輪到你，下注或過牌？';
    }
    if (curSeg && curSeg.length) return '輪到你，下注或過牌？';
    return '你先行動，下注或過牌？';
  }

  function buildTitle(preToks, segs, kind, st) {
    const parts = [];
    const prePlain = preToks.map(x => x.t).join('，');
    const preHtml = preToks.map(x => x.h ? ha(x.t) : esc(x.t)).join('，');
    parts.push({ plain: '翻前：' + prePlain, html: '翻前：' + preHtml });
    for (let i = 0; i <= st; i++) {
      const name = STN[i];
      const seg = segs[i] || '';
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

  function build(L) {
    const nodeIndex = new Map();
    const nodeList = [];
    const unsure = [];
    const unsureSeen = new Set();
    function noteUnsure(sp, nd, reason, extra) {
      const id = sp + '|' + nd + '|' + reason + '|' + (extra || '');
      if (unsureSeen.has(id)) return;
      unsureSeen.add(id);
      unsure.push({ sp, nd, reason, extra: extra || '' });
    }
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
    function rowsOf(sp, nd) {
      const hit = nodeIndex.get(sp + '|' + nd);
      return hit ? hit.rows : [];
    }
    function existingKinds(sp, pfx, st) {
      return nodeList.filter(n => n.sp === sp && n.pfx === pfx && n.st === st);
    }
    // 親節點答案：某牌型在相容牌面是否走出 via
    function canDo(sp, parentNd, h, via, childRow) {
      const rows = rowsOf(sp, parentNd);
      if (!rows.length) return false;
      const childB = txBucket(childRow && childRow.cl, childRow && childRow.c);
      let unsureHit = false, ok = false;
      const base = rows.filter(r => !r.x && r.hc.includes(h));
      const ex = rows.filter(r => r.x && r.hc.includes(h));
      const packs = (ex.length ? ex : []).concat(base);
      for (const r of packs) {
        if (!viaMatch(r, via)) continue;
        const cmp = txCompat(txBucket(r.cl, r.c), childB);
        if (cmp === 'unsure') { unsureHit = true; ok = true; }
        else if (cmp) ok = true;
      }
      if (unsureHit) noteUnsure(sp, parentNd, '牌面條件無法與子節點一一對應（成對面／單色面 vs 最高張），暫當走得到', '');
      return ok;
    }

    // 這條已完成的街，這個牌型能否走出來
    function streetReachable(sp, pfx, st, segText, h, childRow) {
      const k = lastHeroK(segText);
      const via = viaOfK(k);
      if (!via) {
        // 本段沒有你的動作（例如只有對手過、等你行動）——不檢查已完成動作
        return true;
      }
      const kinds = kindsForSeg(segText);
      const parents = existingKinds(sp, pfx, st).filter(n => kinds.includes(bareKind(n.kind)));
      if (!parents.length) {
        // 這個情境沒有對應的親節點（例如只有面對 c-bet、沒有「你先行動」表）
        // 若是翻牌且線從「面對下注」開始，視為翻前可到達的根線。
        if (st === 0) return true;
        return false;
      }
      return parents.some(n => canDo(sp, n.nd, h, via, childRow));
    }

    // 某牌型 × 子列條件，能否走到這條明確線（追到本節點之前的已完成街）
    function classReachesLine(rec, lineKey, h, childRow) {
      const segs = segsFromKey(lineKey);
      // 已完成的街：0 .. st-1；本街已發生的「你已經做過的動作」（例如你下注後被加注）也要能從親節點對上
      for (let i = 0; i < rec.st; i++) {
        const seg = segs[i] || '';
        if (!streetReachable(rec.sp, rec.pfx, i, seg, h, childRow)) return false;
      }
      // 同街衍生（你下注被加注、你加注被再加注）：檢查本街已發生的你的動作
      if (/vs_xr|vs_3b/.test(rec.kind)) {
        const cur = segs[rec.st] || '';
        const k = lastHeroK(cur);
        const via = rec.kind.indexOf('vs_3b') >= 0 ? 'raise' : 'bet';
        // 若標題還沒把「你下注／你加注」寫進本街（key 可能只有先前街），仍用 kind 要求
        const needVia = viaOfK(k) || via;
        const parentKinds = rec.kind.indexOf('vs_3b') >= 0
          ? ['vs_cbet', 'vs_donk', 'vs_bet', 'vs_over', 'vs_barrel', 'vs_probe']
          : ['cbet', 'stab', 'first', 'lead', 'bet', 'barrel', 'delay', 'probe'];
        const parents = existingKinds(rec.sp, rec.pfx, rec.st).filter(n => parentKinds.includes(bareKind(n.kind)));
        if (parents.length && !parents.some(n => canDo(rec.sp, n.nd, h, needVia, childRow))) return false;
        if (!parents.length && rec.st > 0) return false;
      }
      return true;
    }

    // 收集每個節點的明確線（來自例子；沒例子則一條空先前線）
    const lineMap = new Map(); // sp|nd -> lines
    const removed = [];

    for (const rec of nodeList) {
      const rows = nodeIndex.get(rec.key).rows;
      const buckets = new Map();
      for (const r of rows) {
        for (const e of (r.eg || [])) {
          const key = lineKeyFromEg(e, rec.st);
          const ln = (r.c && r.c.ln) || '';
          const prior = (r.c && r.c.prior) || '';
          if (!buckets.has(key)) buckets.set(key, { key, lns: new Set(), priors: new Set(), egs: [], rows: new Set(), pres: [] });
          const b = buckets.get(key);
          if (ln) b.lns.add(ln);
          if (prior) b.priors.add(prior);
          b.egs.push({ e, r });
          b.rows.add(r);
          b.pres.push(e);
        }
      }
      // 沒有例子的列：若已有線就掛上去；否則合成一條
      if (!buckets.size) {
        buckets.set('', { key: '', lns: new Set(), priors: new Set(), egs: [], rows: new Set(rows), pres: [] });
      }
      // 把沒例子、但 ln/prior 對得上的列掛到已有的線
      for (const r of rows) {
        const ln = (r.c && r.c.ln) || '', prior = (r.c && r.c.prior) || '';
        if (!ln && !prior) {
          for (const b of buckets.values()) b.rows.add(r);
          continue;
        }
        let hung = false;
        for (const b of buckets.values()) {
          const lnOk = !b.lns.size || !ln || b.lns.has(ln);
          const prOk = !b.priors.size || !prior || b.priors.has(prior);
          // 三槍線 = 兩條街都跟了下注；不是三槍 = 其他
          const looksTb = /你跟/.test(b.key) && (b.key.match(/你跟/g) || []).length >= 2;
          const looksOth = !looksTb;
          const lnMatch = !ln || (ln === 'tb' && looksTb) || (ln === 'oth' && looksOth) || b.lns.has(ln);
          if (lnMatch && prOk) { b.rows.add(r); hung = true; }
        }
        if (!hung) for (const b of buckets.values()) b.rows.add(r); // 答案仍複製到各線，牌型再靠 rowOk 過濾
      }

      const lines = [];
      for (const [id, b] of buckets) {
        const ePick = (mostCommon(b.pres.map(e => JSON.stringify({ t: e.t, me: e.me, pa: e.pa, pc: e.pc, pretext: e.pretext || '', l: e.l }))) || [])[0];
        const eObj = ePick ? b.pres.find(e => JSON.stringify({ t: e.t, me: e.me, pa: e.pa, pc: e.pc, pretext: e.pretext || '', l: e.l }) === ePick) : b.pres[0];
        const segs = segsFromKey(b.key);
        const preToks = preflopTokens(eObj || guessPre(rec));
        const titles = buildTitle(preToks, segs, rec.kind, rec.st);
        // 每個牌型、每一列條件是否走得到這條線
        function lineLn() {
          if (b.lns && b.lns.size === 1) return [...b.lns][0];
          const looksTb = /你跟/.test(b.key) && (b.key.match(/你跟/g) || []).length >= 2;
          if (b.lns && b.lns.has('tb') && looksTb) return 'tb';
          if (b.lns && b.lns.has('oth') && !looksTb) return 'oth';
          return '';
        }
        function linePrior() { return (b.priors && b.priors.size === 1) ? [...b.priors][0] : ''; }
        const thisLn = lineLn(), thisPrior = linePrior();
        function rowOk(r, h) {
          if (!r.hc.includes(h)) return false;
          if (thisLn && r.c && r.c.ln && r.c.ln !== thisLn) return false;
          if (thisPrior && r.c && r.c.prior && r.c.prior !== thisPrior) return false;
          return classReachesLine(rec, b.key, h, r);
        }
        const reached = [];
        for (const r of b.rows) {
          for (const h of r.hc) if (rowOk(r, h) && !reached.includes(h)) reached.push(h);
        }
        // 也檢查節點全部列（答案複製到拆開的表）：以走得到的牌型為準
        const reachedAll = [];
        for (const r of rows) {
          for (const h of r.hc) {
            if (thisLn && r.c && r.c.ln && r.c.ln !== thisLn) continue;
            if (thisPrior && r.c && r.c.prior && r.c.prior !== thisPrior) continue;
            if (classReachesLine(rec, b.key, h, r) && !reachedAll.includes(h)) reachedAll.push(h);
          }
        }
        const hands = reachedAll.length ? reachedAll : reached;
        const whyDrop = [];
        if (!hands.length) {
          // 為什麼走不到
          if (rec.st >= 1) {
            const segs0 = segsFromKey(b.key);
            const need = [];
            for (let i = 0; i < rec.st; i++) {
              const hk = lastHeroK(segs0[i] || '');
              if (hk) need.push(STN[i] + ' 需要你' + verb(hk) + '（' + (segs0[i] || '（空）') + '）');
            }
            whyDrop.push(need.length ? need.join('；') : '上游沒有能走出這條線的牌型');
            // 親節點完全沒有人做該動作？
            for (let i = 0; i < rec.st; i++) {
              const seg = segs0[i] || '';
              const hk = lastHeroK(seg);
              const via = viaOfK(hk);
              if (!via) continue;
              const kinds = kindsForSeg(seg);
              const parents = existingKinds(rec.sp, rec.pfx, i).filter(n => kinds.includes(bareKind(n.kind)));
              if (parents.length && parents.every(n => !HANDS.some(hh => canDo(rec.sp, n.nd, hh, via, null)))) {
                whyDrop.push('親節點 ' + parents.map(p => p.nd).join('/') + ' 沒有任何牌型會' + (via === 'check' ? '過牌' : via === 'call' ? '跟注' : via === 'bet' ? '下注' : '加注') + '（線卻假設有）');
              }
              if (!parents.length && rec.st > 0 && via) {
                whyDrop.push('找不到對應的 ' + STN[i] + ' 親節點（' + kinds.join('/') + '）');
              }
            }
          } else {
            whyDrop.push('這條翻牌線沒有走得到的牌型');
          }
        }
        const visible = hands.length > 0;
        if (!visible) {
          removed.push({
            sp: rec.sp, nd: rec.nd, line: titles.titleText, key: b.key,
            reason: whyDrop.join('。') || '沒有牌型走得到這條線'
          });
        }
        lines.push({
          id: rec.sp + '/' + rec.nd + '#' + lines.length,
          key: b.key, ln: thisLn, prior: thisPrior,
          titleText: titles.titleText, titleHtml: titles.titleHtml,
          nEg: b.egs.length, hands, visible,
          rowOk, rows: [...b.rows]
        });
      }
      lineMap.set(rec.key, lines);
    }

    function guessPre(rec) {
      // 從同情境任何例子湊翻前
      for (const r of L.rows) if (r.sp === rec.sp && (r.eg || [])[0]) return r.eg[0];
      return { t: 'SRP', me: rec.sp === 'bb' ? 'BB' : rec.sp === 'ipfr' ? 'BTN' : 'BTN', pa: 'BTN', pc: ['BB'] };
    }

    function lines(sp, nd) {
      return (lineMap.get(sp + '|' + nd) || []).filter(ln => ln.visible);
    }
    function nodeVisible(sp, nd) {
      return lines(sp, nd).length > 0;
    }
    function rowReached(r, h, line) {
      const all = lineMap.get(r.sp + '|' + r.nd) || [];
      if (line) return line.visible && line.rowOk(r, h);
      return all.some(ln => ln.visible && ln.rowOk(r, h));
    }
    function titleForEg(sp, nd, e) {
      const rec = nodeIndex.get(sp + '|' + nd);
      if (!rec) return null;
      const k = lineKeyFromEg(e, rec.rec.st);
      const ls = lines(sp, nd);
      return ls.find(ln => ln.key === k) || ls[0] || null;
    }
    function dump() {
      const out = {};
      for (const rec of nodeList) {
        const vis = nodeVisible(rec.sp, rec.nd);
        const ls = lineMap.get(rec.key) || [];
        const byC = {};
        for (const r of nodeIndex.get(rec.key).rows) {
          if (r.x) continue;
          const ck = JSON.stringify(r.c || {}, Object.keys(r.c || {}).sort());
          if (!byC[ck]) byC[ck] = [];
          for (const h of r.hc) if (rowReached(r, h) && !byC[ck].includes(h)) byC[ck].push(h);
        }
        out[rec.key] = {
          visible: vis,
          usesReach: true,
          st: rec.st,
          byC,
          nLines: ls.filter(l => l.visible).length,
          nDropped: ls.filter(l => !l.visible).length
        };
      }
      return out;
    }
    function audit() {
      const all = [];
      let nSplit = 0, nTables = 0, nOmittedNodes = 0;
      for (const rec of nodeList) {
        const ls = lineMap.get(rec.key) || [];
        const shown = ls.filter(l => l.visible);
        const dropped = ls.filter(l => !l.visible);
        if (shown.length > 1) nSplit++;
        nTables += shown.length;
        if (!shown.length) nOmittedNodes++;
        all.push({
          sp: rec.sp, nd: rec.nd, st: rec.st,
          old: (L.node_labels && L.node_labels[rec.sp] && L.node_labels[rec.sp][rec.nd]) || (L.nd && L.nd[rec.nd]) || rec.nd,
          shown: shown.map(l => ({ title: l.titleText, key: l.key, hands: l.hands.slice(), nEg: l.nEg, ln: l.ln, prior: l.prior })),
          dropped: dropped.map(l => ({ title: l.titleText, key: l.key, reason: (removed.find(x => x.sp === rec.sp && x.nd === rec.nd && x.key === l.key) || {}).reason })),
          split: shown.length > 1, nShown: shown.length, nDropped: dropped.length
        });
      }
      return { all, removed, unsure, nNodes: nodeList.length, nSplit, nTables, nOmittedNodes };
    }
    return { lines, nodeVisible, rowReached, titleForEg, lineKeyFromEg, dump, audit, HANDS };
  }

  root.NL2TITLES = { build, lineKeyFromEg, streetOf, splitNd };
})(typeof window !== 'undefined' ? window : globalThis);
