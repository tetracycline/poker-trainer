#!/usr/bin/env node
/* Execute the production renderer; no reimplementation of grids or questions. */
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const root = path.resolve(__dirname, '..');
async function main() {
  const base = process.argv[2];
  const read = async name => {
    if (!base) return fs.readFileSync(path.join(root, name), 'utf8');
    const response = await fetch(new URL(name, base.replace(/\/?$/, '/')));
    if (!response.ok) throw new Error(`${name}: HTTP ${response.status}`);
    return response.text();
  };
  const handlers = {}, app = {innerHTML: '', querySelectorAll: () => [], addEventListener: (event, fn) => { handlers[event] = fn; }};
  const context = { console, __LINES_QA: true, location: {hash:'#lines'}, scrollTo() {}, addEventListener() {}, document: {querySelector: () => app, querySelectorAll: () => []} };
  context.window = context; vm.createContext(context);
  let seed = 1106;
  context.Math = Object.create(Math);
  context.Math.random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296);
  for (const name of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2.js']) vm.runInContext(await read(name), context, {filename: name});
  if (!context.__linesQA) throw new Error('Renderer lacks QA interface (deploy nl2.js with the data)');
  const failures = [], summary = [];
  context.__linesQA.card();
  if (/undefined|NaN/.test(app.innerHTML)) failures.push('rule cards: invalid rendered text');
  function grids(label) { // 預設＋例外摘要：每個節點一行預設、每格都對應到非空動作（零空格）
    let count = 0;
    if (/undefined|NaN/.test(app.innerHTML)) failures.push(`${label}: invalid rendered text`);
    for (const m of app.innerHTML.matchAll(/<p class="sum">([\s\S]*?)<\/p>/g)) {
      count++; const t = m[1].replace(/<[^>]*>/g, '').replace(/.*→/, '').trim();
      if (!t || t === '—') failures.push(`${label}: blank default ${count}`);
    }
    if (!count) failures.push(`${label}: no rendered node summary`);
    return count;
  }
  function cellsOk(sp, nd) {
    const S = context.__linesQA.nodeSum(sp, nd);
    for (const c of S.cells) {
      const lab = String((c.r.L && c.r.L[c.r.a]) || c.r.a || '');
      if (!lab || /undefined|NaN/.test(lab)) failures.push(`${sp}/${nd}: blank cell ${c.k}/${c.h}`);
    }
    const hc = Object.keys(context.NLL.hc);
    for (const k of new Set(S.cells.map(c => c.k))) for (const h of hc)
      if (!S.cells.some(c => c.k === k && c.h === h)) failures.push(`${sp}/${nd}: ${k}/${h} has no answer`);
  }
  for (const spot of context.NLL.spots) {
    context.__linesQA.render(spot.id);
    const cells = grids(spot.id), questions = [];
    for (const nd of context.__linesQA.nodesOf(spot.id)) {
      cellsOk(spot.id, nd);
      const exc = context.NLL.rows.filter(r => r.sp === spot.id && r.nd === nd && context.__linesQA.isExc(r));
      if (!exc.filter(r => !r.noeg).length) continue;   // 全部同一動作，或例外牌型不在你的範圍：不出題（HW 11/10）
      const eligible = exc.some(r => (r.eg || []).some(e => {
          const story = context.__linesQA.story(e);
          return story && story.length === context.__linesQA.stOf(nd) + 2;
        }));
      if (!eligible) failures.push(`${spot.id}/${nd}: no complete drill example for its exceptions`);
    }
    for (let street = 0; street < 3; street++) {
      let count = 0;
      for (let i = 0; i < 30; i++) {
        context.__linesQA.drill(spot.id, street);
        const q = context.__Q;
        if (/undefined|NaN/.test(app.innerHTML)) failures.push(`${spot.id}/${street}: invalid drill text`);
        if (!q) { if (context.__linesQA.pool(spot.id).some(r => context.__linesQA.stOf(r.nd) === street)) failures.push(`${spot.id}/${street}: no drill question`); break; }
        if (!context.__linesQA.isExc(q.row)) failures.push(`${spot.id}/${street}/${q.id}: drill on a non-exception row`);
        const lines = [...app.innerHTML.matchAll(/<p class="line">([\s\S]*?)<\/p>/g)].map(m => m[1].replace(/<[^>]*>/g,''));
        for (const name of ['翻前','翻牌','轉牌','河牌'].slice(0, street + 2)) {
          if (!lines.some(line => line.startsWith(name))) failures.push(`${spot.id}/${street}/${q.id}: missing ${name}`);
        }
        if (context.__linesQA.stOf(q.row.nd) !== street) failures.push(`${spot.id}: wrong decision street`);
        count++;
      }
      questions.push(count);
    }
    summary.push({spot: spot.id, cells, flop: questions[0], turn: questions[1], river: questions[2]});
  }
  let riv = 0, rivCells = 0;
  for (let i = 0; i < 30; i++) {
    context.__linesQA.drill('riv');
    if (!context.__Q) {failures.push('riv: no question'); break;}
    for (const name of ['翻牌','轉牌','河牌']) if (!app.innerHTML.includes(`<p class="line">${name}`)) failures.push(`riv: missing ${name}`);
    context.__linesQA.answer(context.__Q.row.a);
    rivCells += grids('riv');
    riv++;
  }
  summary.push({spot:'riv', cells:rivCells, flop:0, turn:0, river:riv});
  console.table(summary);
  console.log(`${failures.length} failures`);
  if (failures.length) console.error(failures.slice(0, 50).join('\n'));
  process.exitCode = failures.length ? 1 : 0;
}
main().catch(error => {console.error(error); process.exitCode = 1;});
