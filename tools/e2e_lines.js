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
  for (const name of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2.js']) vm.runInContext(await read(name), context, {filename: name});
  if (!context.__linesQA) throw new Error('Renderer lacks QA interface (deploy nl2.js with the data)');
  const failures = [], summary = [];
  context.__linesQA.card();
  if (/undefined|NaN/.test(app.innerHTML)) failures.push('rule cards: invalid rendered text');
  function grids(label) { // 每節點一張表；動作格不可空白；轉／河不可出現走不到的牌型
    let count = 0;
    if (/undefined|NaN/.test(app.innerHTML)) failures.push(`${label}: invalid rendered text`);
    if (/class="sum"|class="exl"/.test(app.innerHTML)) failures.push(`${label}: leftover default/exception prose`);
    for (const tbl of app.innerHTML.matchAll(/<table class="rt lt">([\s\S]*?)<\/table>/g)) {
      count++;
      for (const cell of tbl[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)) {
        const value = cell[1].replace(/<[^>]*>/g, '').trim();
        if (!value || value === '—') failures.push(`${label}: blank grid cell`);
      }
    }
    if (!count && label !== 'riv') failures.push(`${label}: no rendered table`);
    return count;
  }
  function cellsOk(sp, nd) {
    if (!context.__linesQA.nodeVisible(sp, nd)) {
      if (new RegExp(nd.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).test(app.innerHTML) && context.__linesQA.gridHtml(sp, nd))
        failures.push(`${sp}/${nd}: omitted node still rendered a table`);
      return;
    }
    const S = context.__linesQA.nodeSum(sp, nd);
    for (const c of S.cells) {
      const lab = String((c.r.L && c.r.L[c.r.a]) || c.r.a || '');
      if (!lab || /undefined|NaN/.test(lab)) failures.push(`${sp}/${nd}: blank cell ${c.k}/${c.h}`);
      if (!context.__linesQA.rowReached(c.r, c.h)) failures.push(`${sp}/${nd}: unreachable cell shown ${c.k}/${c.h}`);
    }
    // 只要求「走得到」的牌型有答案（轉／河非 mw）；翻牌與 mw 仍是全套牌型
    const shown = new Set(S.cells.map(c => c.k + '|' + c.h));
    for (const c of S.cells) if (!shown.has(c.k + '|' + c.h)) failures.push(`${sp}/${nd}: ${c.k}/${c.h} has no answer`);
  }
  // 固定回歸：延遲搶池整節點應省略；BB 面對第二槍不應再列空氣
  context.__linesQA.render('ipc');
  if (context.__linesQA.nodeVisible('ipc', 't_delay')) failures.push('ipc/t_delay should be omitted (no hand checks flop stab)');
  if (/t_delay/.test(app.innerHTML) && context.__linesQA.gridHtml('ipc', 't_delay')) failures.push('ipc/t_delay table still rendered');
  context.__linesQA.render('bb');
  const bbAir = context.__linesQA.nodeSum('bb', 't_vs_barrel').cells.some(c => c.h === 'AIR');
  if (bbAir) failures.push('bb/t_vs_barrel still has an air row');
  if (/空氣/.test(context.__linesQA.gridHtml('bb', 't_vs_barrel') || '')) failures.push('bb/t_vs_barrel rendered 空氣');
  for (const spot of context.NLL.spots) {
    context.__linesQA.render(spot.id);
    const cells = grids(spot.id), questions = [];
    for (const nd of context.__linesQA.nodesOf(spot.id)) {
      if (!context.__linesQA.nodeVisible(spot.id, nd)) continue;
      cellsOk(spot.id, nd);
      const exc = context.NLL.rows.filter(r => r.sp === spot.id && r.nd === nd && context.__linesQA.isExc(r) && r.hc.some(h => context.__linesQA.rowReached(r, h)));
      if (!exc.filter(r => !r.noeg).length) continue;   // 全部同一動作，或例外走不到：不出題
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
