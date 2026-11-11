// Shared reachability for NL2 later-street tables: which hand classes can
// arrive at a turn/river node from parent answers (same labels, chained).
// mw is never filtered. Flop nodes are computed internally for chaining only.
(function (root) {
  const HANDS = ['S', 'TPG', 'TPW', 'MID', 'DRAW', 'WDRAW', 'AIR'];
  const EDGES = [
    { child: 'f_vs_xr', parents: ['f_cbet', 'f_stab', 'f_first', 'f_lead', 'f_bet'], via: 'bet' },
    { child: 'f_vs_3b', parents: ['f_vs_cbet', 'f_vs_donk', 'f_vs_bet', 'f_vs_over'], via: 'raise' },
    { child: 't_barrel', parents: ['f_cbet', 'f_stab', 'f_first', 'f_lead', 'f_bet'], via: 'bet' },
    { child: 't_delay', parents: ['f_cbet', 'f_stab', 'f_first', 'f_lead', 'f_bet'], via: 'check' },
    { child: 't_probe', parents: ['f_cbet', 'f_stab', 'f_first', 'f_lead', 'f_bet'], via: 'check' },
    { child: 't_first', parents: ['f_first', 'f_lead', 'f_bet', 'f_cbet'], via: 'check' },
    { child: 't_stab', parents: ['f_stab', 'f_cbet', 'f_first', 'f_lead', 'f_bet'], via: 'check' },
    { child: 't_stab', parents: ['f_vs_cbet', 'f_vs_donk', 'f_vs_bet', 'f_vs_over'], via: 'call', tag: 'after-call' },
    { child: 't_first', parents: ['f_vs_cbet', 'f_vs_donk', 'f_vs_bet', 'f_vs_over'], via: 'call', tag: 'after-call' },
    { child: 't_probe', parents: ['f_vs_cbet', 'f_vs_donk', 'f_vs_bet', 'f_vs_over'], via: 'call', tag: 'after-call' },
    { child: 't_vs_barrel', parents: ['f_vs_cbet', 'f_vs_donk', 'f_vs_bet', 'f_vs_over'], via: 'call' },
    { child: 't_vs_bet', parents: ['f_vs_bet', 'f_vs_cbet', 'f_vs_donk', 'f_vs_over'], via: 'call' },
    { child: 't_vs_probe', parents: ['f_cbet', 'f_stab', 'f_first', 'f_lead', 'f_bet'], via: 'check' },
    { child: 't_bet', parents: ['f_bet', 'f_cbet', 'f_stab', 'f_first', 'f_lead'], via: 'check' },
    { child: 't_bet', parents: ['f_vs_bet', 'f_vs_cbet', 'f_vs_donk'], via: 'call', tag: 'after-call' },
    { child: 't_vs_xr', parents: ['t_barrel', 't_delay', 't_probe', 't_stab', 't_first', 't_bet'], via: 'bet' },
    { child: 't_vs_3b', parents: ['t_vs_barrel', 't_vs_probe', 't_vs_bet'], via: 'raise' },
    { child: 'r_barrel', parents: ['t_barrel', 't_delay', 't_probe', 't_stab', 't_first', 't_bet'], via: 'bet' },
    { child: 'r_stab', parents: ['t_barrel', 't_delay', 't_probe', 't_stab', 't_first', 't_bet'], via: 'check' },
    { child: 'r_bet', parents: ['t_bet', 't_first', 't_probe', 't_stab', 't_barrel', 't_delay'], via: 'check' },
    { child: 'r_bet', parents: ['t_vs_bet', 't_vs_barrel', 't_vs_probe'], via: 'call', tag: 'after-call' },
    { child: 'r_vs_bet', parents: ['t_vs_barrel', 't_vs_probe', 't_vs_bet'], via: 'call', line: 'tb' },
    { child: 'r_vs_bet', parents: ['t_barrel', 't_delay', 't_probe', 't_stab', 't_first', 't_bet'], via: 'check', line: 'oth' },
    { child: 'r_vs_bet', parents: ['t_vs_barrel', 't_vs_probe', 't_vs_bet'], via: 'call' },
    { child: 'r_vs_bet', parents: ['t_barrel', 't_delay', 't_probe', 't_stab', 't_first', 't_bet'], via: 'check' },
    { child: 'r_vs_bet2', parents: ['t_vs_barrel', 't_vs_probe'], via: 'call' },
    { child: 'r_vs_bet2', parents: ['t_delay', 't_stab', 't_first', 't_probe', 't_barrel'], via: 'check' },
    { child: 'r_vs_xr', parents: ['r_barrel', 'r_stab', 'r_bet'], via: 'bet' },
    { child: 'r_vs_3b', parents: ['r_vs_bet', 'r_vs_bet2'], via: 'raise' }
  ];

  function streetOf(nd) {
    return /(^|_)f_/.test(nd) ? 0 : /(^|_)t_/.test(nd) ? 1 : 2;
  }
  function splitNd(nd) {
    for (const p of ['3b_', '3c_', 'lmp_', 'iso_']) {
      if (nd.startsWith(p)) return { pfx: p, kind: nd.slice(p.length) };
    }
    return { pfx: '', kind: nd };
  }
  function usesReach(sp, nd) { return sp !== 'mw' && streetOf(nd) >= 1; }
  function acts(r) { return new Set([r.a, ...(r.ok || [])]); }
  function continues(r, via) {
    const A = acts(r);
    if (via === 'call') return A.has('c');
    if (via === 'raise') return A.has('r');
    if (via === 'check') return A.has('x');
    if (via === 'bet') return A.has('small') || A.has('big');
    return false;
  }
  function lineOf(r) {
    if (r && r.c && r.c.ln) return r.c.ln;
    const cl = (r && r.cl) || '';
    if (/不是三槍/.test(cl)) return 'oth';
    if (/三槍/.test(cl)) return 'tb';
    return null;
  }
  function priorOf(r) { return (r && r.c && r.c.prior) || null; }
  function pathOkForRow(edge, r) {
    const ln = lineOf(r), prior = priorOf(r);
    if (edge.line === 'tb' && ln && ln !== 'tb') return false;
    if (edge.line === 'oth' && ln && ln !== 'oth') return false;
    if (prior === 'bet_bet' && edge.via === 'check') return false;
    if (prior === 'check_turn' && edge.via !== 'check') return false;
    return true;
  }
  function condKey(r) {
    const c = r.c || {};
    const keys = Object.keys(c).sort();
    return keys.length ? JSON.stringify(c, keys) : '{}';
  }
  function reasonMatchesRow(reason, r) {
    const ln = lineOf(r), prior = priorOf(r);
    if (ln === 'tb' && reason.via !== 'call') return false;
    if (ln === 'oth' && reason.via === 'call' && !reason.tag) return false;
    if (prior === 'bet_bet' && reason.via === 'check') return false;
    if (prior === 'check_turn' && reason.via !== 'check') return false;
    return true;
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
    function parentsFor(rec) {
      const out = [];
      for (const e of EDGES.filter(x => x.child === rec.kind)) {
        for (const pk of e.parents) {
          const hit = nodeIndex.get(rec.sp + '|' + rec.pfx + pk);
          if (hit) out.push({ edge: e, parent: hit.rec, rows: hit.rows });
        }
      }
      return out;
    }
    const reach = {};
    for (const rec of nodeList) {
      const reasons = {};
      for (const h of HANDS) reasons[h] = [];
      if (!parentsFor(rec).length) {
        const rows = nodeIndex.get(rec.key).rows;
        for (const h of HANDS) if (rows.some(r => r.hc.includes(h))) {
          reasons[h].push({ via: 'root', parentNd: '', tag: '', line: '' });
        }
      }
      reach[rec.key] = reasons;
    }
    let changed = true, guard = 0;
    while (changed && guard++ < 20) {
      changed = false;
      for (const rec of nodeList) {
        for (const { edge, parent, rows } of parentsFor(rec)) {
          for (const h of HANDS) {
            if (!reach[parent.key][h].length) continue;
            if (!rows.some(r => r.hc.includes(h) && continues(r, edge.via))) continue;
            const already = reach[rec.key][h].some(x =>
              x.parentNd === parent.nd && x.via === edge.via && x.line === (edge.line || '') && x.tag === (edge.tag || ''));
            if (already) continue;
            reach[rec.key][h].push({ via: edge.via, line: edge.line || '', tag: edge.tag || '', parentNd: parent.nd });
            changed = true;
          }
        }
      }
    }
    function classReached(sp, nd, h, row) {
      if (!usesReach(sp, nd)) return true;
      const rec = nodeIndex.get(sp + '|' + nd);
      if (!rec) return true;
      const rs = reach[rec.rec.key][h] || [];
      if (!rs.length) return false;
      if (!row) return true;
      return rs.some(reason => reasonMatchesRow(reason, row));
    }
    function reachedHands(sp, nd, row) {
      return HANDS.filter(h => classReached(sp, nd, h, row));
    }
    function visible(sp, nd) {
      if (!usesReach(sp, nd)) return true;
      const hit = nodeIndex.get(sp + '|' + nd);
      if (!hit) return false;
      return hit.rows.some(r => r.hc.some(h => classReached(sp, nd, h, r)));
    }
    function dump() {
      const out = {};
      for (const rec of nodeList) {
        const byC = {};
        for (const r of nodeIndex.get(rec.key).rows) {
          if (r.x) continue;
          const k = condKey(r);
          if (!byC[k]) byC[k] = [];
          for (const h of r.hc) if (classReached(rec.sp, rec.nd, h, r) && !byC[k].includes(h)) byC[k].push(h);
        }
        out[rec.key] = { visible: visible(rec.sp, rec.nd), usesReach: usesReach(rec.sp, rec.nd), st: rec.st, byC };
      }
      return out;
    }
    return { classReached, reachedHands, visible, usesReach, dump, HANDS };
  }

  root.NL2REACH = { build, usesReach, streetOf, HANDS };
})(typeof window !== 'undefined' ? window : globalThis);
