#!/usr/bin/env node
/* Per-node review checklist (production renderer; local files or live base URL).
   (1) action line: complete example story (preflop + every prior street + this street) for the node and every drilled row
   (2) poker sense: dominance (a stronger made class never folds where a weaker one continues), two pair+ never folds to a non-all-in bet
   (3) sizes: every bet label carries an explicit % (or ½/1 pot) between 20% and 200%
   (4) no redundant class lists: one default line + only differing classes
   (5) evidence label on the default and on every exception */
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const root = path.resolve(__dirname, '..');
(async () => {
  const base = process.argv[2] || '';
  const read = async n => base ? (await (await fetch(new URL(n, base.replace(/\/?$/, '/')))).text()) : fs.readFileSync(path.join(root, n), 'utf8');
  const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
  const ctx = {console, __LINES_QA: true, location: {hash: '#lines'}, scrollTo() {}, addEventListener() {}, document: {querySelector: () => app, querySelectorAll: () => []}};
  ctx.window = ctx; vm.createContext(ctx);
  for (const n of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2.js']) vm.runInContext(await read(n), ctx, {filename: n});
  const Q = ctx.__linesQA, L = ctx.NLL, ORD = ['S', 'TPG', 'TPW', 'MID', 'AIR'];
  const isVs = nd => /_vs_|_over/.test(nd), allin = r => (r.eg || []).some(e => /:a/.test(e.l.split('/').pop()));
  const pct = l => /½ 池/.test(l) ? 50 : /⅔ 池/.test(l) ? 67 : /¾ 池/.test(l) ? 75 : /1 池/.test(l) ? 100 : (+(String(l).match(/(\d+)%/) || [])[1] || null);
  const out = [];
  for (const sp of L.spots) {
    Q.render(sp.id); const html = app.innerHTML, secs = html.split('<div class="sec"><b>').slice(1);
    Q.nodesOf(sp.id).forEach((nd, i) => {
      const sec = secs[i] || '', S = Q.nodeSum(sp.id, nd), rows = L.rows.filter(r => r.sp === sp.id && r.nd === nd), issues = {1: [], 2: [], 3: [], 4: [], 5: []};
      const need = Q.stOf(nd) + 2;
      if (!/你面對（例）：翻前：/.test(sec)) issues[1].push('no full example line');
      rows.filter(Q.isExc).filter(r => !r.noeg).forEach(r => { if (!(r.eg || []).some(e => { const s = Q.story(e); return s && s.length === need; })) issues[1].push(`${r.id}: no complete example`); });
      if (isVs(nd)) for (const k of new Set(S.cells.map(c => c.k))) {
        const cs = S.cells.filter(c => c.k === k), get = h => cs.find(c => c.h === h);
        for (let a = 0; a < ORD.length; a++) for (let b = a + 1; b < ORD.length; b++) {
          const A = get(ORD[a]), B = get(ORD[b]);
          if (A && B && A.r.a === 'f' && (B.r.a === 'c' || (B.r.a === 'r' && ORD[b] !== 'AIR'))) issues[2].push(`${k}: ${ORD[a]} folds but weaker ${ORD[b]} ${B.r.a} (${A.r.id} vs ${B.r.id})`);
        }
        const s2 = get('S'); if (s2 && s2.r.a === 'f' && !allin(s2.r)) issues[2].push(`${k}: two pair+ folds to a non-all-in bet (${s2.r.id})`);
      }
      for (const r of rows) for (const a of [r.a, ...r.ok]) if (a === 'small' || a === 'big') {
        const l = (r.L && r.L[a]) || ''; const v = pct(l);
        if (!l && !/^3bp|^iso/.test('')) issues[3].push(`${r.id}: ${a} uses the default label (solver tree size)`);
        else if (l !== '全下' && (!v || v < 20 || v > (/lmp_/.test(nd) ? 300 : 200))) issues[3].push(`${r.id}: size label "${l}"`);
      }
      const sum = sec.match(/<p class="sum">[\s\S]*?<\/p>/g) || [];
      if (sum.length !== 1) issues[4].push(`summary lines ${sum.length}`);
      if (/<table/.test(sec)) issues[4].push('still renders a class grid');
      for (const l of S.lines) if (!l.own && l.groups.some(g => new Set(g.cs.map(c => c.h)).size === new Set(l.all.map(c => c.h)).size)) issues[4].push(`${l.k}: exception lists every class`);
      const li = sec.match(/<li[\s\S]*?<\/li>/g) || [];
      if (!/<small class="df"/.test(sum[0] || '')) issues[5].push('default without evidence label');
      li.forEach(x => { if (!/<small class="df"/.test(x)) issues[5].push('exception without evidence label: ' + x.replace(/<[^>]*>/g, '').slice(0, 40)); });
      out.push({n: out.length + 1, sp: sp.id, nd, label: (L.node_labels[sp.id] || {})[nd] || L.nd[nd], exceptions: rows.filter(Q.isExc).length, drill_rows: Q.pool(sp.id).filter(r => r.nd === nd).length, issues});
    });
  }
  fs.writeFileSync(process.argv[3] || '/dev/stdout', JSON.stringify(out, null, 1));
  const cnt = k => out.filter(o => o.issues[k].length).length;
  console.error(`${out.length} nodes; nodes with issues: (1) ${cnt(1)} (2) ${cnt(2)} (3) ${cnt(3)} (4) ${cnt(4)} (5) ${cnt(5)}`);
})();
