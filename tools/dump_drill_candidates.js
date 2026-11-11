#!/usr/bin/env node
/* 給 tools/build_drill_paths.py：列出每一列的每個例題（含它所在的線、你先前的決定點），JSON 印到 stdout */
const fs = require('fs'), vm = require('vm'), path = require('path');
const root = path.resolve(process.argv[2] || path.join(__dirname, '..'));
const app = { innerHTML: '', querySelectorAll: () => [], addEventListener() {} };
const ctx = { console, __LINES_QA: true, __NL2_NO_EGPATH: true, location: { hash: '#lines' }, scrollTo() {}, addEventListener() {}, document: { querySelector: () => app, querySelectorAll: () => [] } };
ctx.window = ctx; vm.createContext(ctx);
for (const n of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2.js']) vm.runInContext(fs.readFileSync(path.join(root, n), 'utf8'), ctx, { filename: n });
const Q = ctx.__linesQA, L = ctx.NLL, T = Q.TITLES, items = [];
for (const r of L.rows) for (const [i, e] of (r.eg || []).entries()) {
  const ln = T.titleForEg(r.sp, r.nd, e); if (!ln) continue;
  items.push({ id: r.id, i, sp: r.sp, nd: r.nd, st: Q.stOf(r.nd), hc: r.hc, e: { h: e.h, b: e.b, l: e.l, me: e.me }, facts: ln.facts, decs: ln.decisions.map(d => ({ st: d.st, verb: d.verb, need: d.need, nds: d.nds })) });
}
process.stdout.write(JSON.stringify({ items, rows: L.rows.map(r => ({ id: r.id, sp: r.sp, nd: r.nd, hc: r.hc, c: r.c || {}, x: !!r.x, a: r.a })) }));
