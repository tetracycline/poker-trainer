#!/usr/bin/env node
/* Render every node with the production renderer (local files or a live base URL) and print plain text, one block per node. */
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const root = path.resolve(__dirname, '..');
(async () => {
  const base = process.argv[2];
  const read = async n => base ? (await (await fetch(new URL(n, base.replace(/\/?$/, '/')))).text()) : fs.readFileSync(path.join(root, n), 'utf8');
  const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
  const ctx = {console, __LINES_QA: true, location: {hash: '#lines'}, scrollTo() {}, addEventListener() {}, document: {querySelector: () => app, querySelectorAll: () => []}};
  ctx.window = ctx; vm.createContext(ctx);
  for (const n of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2.js']) vm.runInContext(await read(n), ctx, {filename: n});
  const out = [];
  for (const sp of ctx.NLL.spots) {
    ctx.__linesQA.render(sp.id);
    const secs = app.innerHTML.split('<div class="sec"><b>').slice(1);
    for (const s of secs) out.push({sp: sp.id, text: s.replace(/<\/(p|li|b)>/g, m => m === '</b>' ? '' : '\n').replace(/<[^>]*>/g, '').replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&amp;/g, '&').replace(/\n+/g, '\n').trim()});
  }
  fs.writeFileSync(process.argv[3] || '/dev/stdout', out.map((o, i) => `### ${i + 1} [${o.sp}] ${o.text}`).join('\n\n') + '\n');
  console.error(out.length, 'nodes');
})();
