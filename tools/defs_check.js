#!/usr/bin/env node
/* QA: every label shown in the lines tables and drill answer grids must be tappable and have a definition in defs.js.
   Runs the production nl2.js. Optional arg: base URL to check the live site. */
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const root = path.resolve(__dirname, '..');
async function main() {
  const base = process.argv[2];
  const read = async n => base ? (await fetch(new URL(n, base.replace(/\/?$/, '/')))).text() : fs.readFileSync(path.join(root, n), 'utf8');
  const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
  const ctx = {console, __LINES_QA: true, location: {hash: '#lines'}, scrollTo() {}, addEventListener() {}, document: {querySelector: () => app, querySelectorAll: () => [], getElementById: () => null}};
  ctx.window = ctx; vm.createContext(ctx);
  let seed = 652; ctx.Math = Object.create(Math); ctx.Math.random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296);
  for (const n of ['defs.js', 'lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2.js']) vm.runInContext(await read(n), ctx, {filename: n});
  const D = ctx.NLDEF, F = [], used = new Set(), Q = ctx.__linesQA;
  if (!D || !D.d) { console.log('defs.js missing'); process.exitCode = 1; return; }
  const grouped = new Set(D.groups.flatMap(g => g[1]));
  for (const k of grouped) if (!(D.d[k] || '').trim()) F.push(`definition empty: ${k}`);
  for (const k of Object.keys(D.d)) if (!grouped.has(k)) F.push(`definition not shown in 定義 panel: ${k}`);
  const strip = s => s.replace(/<[^>]*>/g, '').trim();
  function check(label, html) {
    for (const m of html.matchAll(/<th\b[^>]*>([\s\S]*?)<\/th>/g)) {
      const inner = m[1]; if (!strip(inner)) continue;
      const rest = strip(inner.replace(/<span class="df"[^>]*>[\s\S]*?<\/span>/g, '').replace(/・/g, ''));
      if (rest) F.push(`${label}: label without definition tap: ${strip(inner)}`);
    }
    for (const m of html.matchAll(/<small\b([^>]*)>([\s\S]*?)<\/small>/g)) if (!/data-df=/.test(m[1])) F.push(`${label}: tag without definition: ${strip(m[2])}`);
    for (const m of html.matchAll(/data-df="([^"]*)"/g)) { const k = m[1].replace(/&amp;/g, '&'); used.add(k); if (!(D.d[k] || '').trim()) F.push(`${label}: no definition for 「${k}」`); }
    if (/data-f=|<details class="sec defs"/.test(html) && !html.includes('<details class="sec defs"')) F.push(`${label}: 定義 panel missing`);
  }
  for (const s of ctx.NLL.spots) { Q.render(s.id); check('lines ' + s.id, app.innerHTML); if (!app.innerHTML.includes('<details class="sec defs"')) F.push(`lines ${s.id}: 定義 panel missing`); }
  const filters = ['all', 'riv'].concat(ctx.NLL.spots.map(s => s.id)); let nq = 0;
  for (const f of filters) for (let i = 0; i < 30; i++) {
    Q.drill(f); if (!ctx.__Q) { F.push(`drill ${f}: no question`); break; }
    Q.answer(ctx.__Q.row.a); check('drill ' + f, app.innerHTML); nq++;
    if (!app.innerHTML.includes('<details class="sec defs"')) F.push(`drill ${f}: 定義 panel missing in answer`);
  }
  console.log(`labels used ${used.size}: ${[...used].join(' | ')}`);
  console.log(`drill answers checked ${nq}; ${F.length} failures`); if (F.length) console.error([...new Set(F)].slice(0, 40).join('\n'));
  process.exitCode = F.length ? 1 : 0;
}
main().catch(e => { console.error(e); process.exitCode = 1; });
