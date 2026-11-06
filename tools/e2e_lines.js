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
  function grids(label) {
    let count = 0;
    for (const cell of app.innerHTML.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)) {
      const value = cell[1].replace(/<[^>]*>/g, '').trim(); count++;
      if (!value || value === '—') failures.push(`${label}: blank grid cell ${count}`);
    }
    if (!count) failures.push(`${label}: no rendered grid cells`);
    return count;
  }
  for (const spot of context.NLL.spots) {
    context.__linesQA.render(spot.id);
    const cells = grids(spot.id), questions = [];
    for (const nd of context.__linesQA.nodesOf(spot.id)) {
      const eligible = context.NLL.rows.filter(r => r.sp === spot.id && r.nd === nd)
        .some(r => (r.eg || []).some(e => {
          const story = context.__linesQA.story(e);
          return story && story.length === context.__linesQA.stOf(nd) + 2;
        }));
      if (!eligible) failures.push(`${spot.id}/${nd}: no complete drill example`);
    }
    for (let street = 0; street < 3; street++) {
      let count = 0;
      if (spot.id === 'mw' && street < 2) {
        context.__linesQA.drill(spot.id, street);
        if (context.__Q) failures.push(`mw/${street}: unsupported question`);
        questions.push(0); continue;
      }
      for (let i = 0; i < 30; i++) {
        context.__linesQA.drill(spot.id, street);
        const q = context.__Q;
        if (!q) { failures.push(`${spot.id}/${street}: no drill question`); break; }
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
