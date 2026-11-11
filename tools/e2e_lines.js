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
  for (const name of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2.js']) vm.runInContext(await read(name), context, {filename: name});
  if (!context.__linesQA) throw new Error('Renderer lacks QA interface (deploy nl2.js with the data)');
  const failures = [], summary = [];
  context.__linesQA.card();
  if (/undefined|NaN/.test(app.innerHTML)) failures.push('rule cards: invalid rendered text');
  function grids(label) { // 9b695d6 格狀表：走得到的格子不可空白；轉／河不可出現走不到的牌型
    let count = 0;
    if (/undefined|NaN/.test(app.innerHTML)) failures.push(`${label}: invalid rendered text`);
    if (/所有牌型|其餘牌型|class="leg"|class="diff"/.test(app.innerHTML)) failures.push(`${label}: compact-table leftover`);
    if (/先前行動見例題|全部前面行動線|逐題列出翻前|翻前角色見情境/.test(app.innerHTML)) failures.push(`${label}: vague node title leftover`);
    const plain = app.innerHTML.replace(/<[^>]+>/g, '');
    if (label==='bb' && !/你過、對手過/.test(plain)) failures.push('bb: t_probe-style title missing 你過、對手過');
    for (const cell of app.innerHTML.matchAll(/<td\b([^>]*)>([\s\S]*?)<\/td>/g)) {
      const value = cell[2].replace(/<[^>]*>/g, '').trim(); count++;
      const isNa = /\bna\b/.test(cell[1]);
      if (isNa) continue; // 走不到的條件×牌型
      if (!value || value === '—') failures.push(`${label}: blank grid cell ${count}`);
      if (/約|牌池均值|\d+%/.test(value)) failures.push(`${label}: oversized or raw-percent cell ${count}: ${value}`);
    }
    if (!count) failures.push(`${label}: no rendered grid cells`);
    return count;
  }
  function cellsOk(sp, nd) {
    if (!context.__linesQA.nodeVisible(sp, nd)) {
      if (context.__linesQA.gridHtml(sp, nd)) failures.push(`${sp}/${nd}: omitted node still rendered a table`);
      return;
    }
    const html = context.__linesQA.gridHtml(sp, nd);
    if (!html || !/<table class="rt lt">/.test(html)) failures.push(`${sp}/${nd}: missing table`);
    if (/所有牌型|其餘牌型|class="leg"|class="diff"/.test(html)) failures.push(`${sp}/${nd}: compact-table leftover`);
    const rows = context.NLL.rows.filter(r => r.sp === sp && r.nd === nd && !r.x);
    for (const r of rows) for (const h of r.hc) {
      const reached = context.__linesQA.rowReached(r, h);
      const lab = hlabel(h, nd);
      const shown = html.includes(lab) && !new RegExp('class="na"[^>]*>—</td>').test('');
      if (reached) {
        const labTxt = String((r.L && r.L[r.a]) || r.a || '');
        if (!labTxt || /undefined|NaN/.test(labTxt)) failures.push(`${sp}/${nd}: blank cell ${(r.cl||'全部')}/${h}`);
      }
    }
    if (html.includes('>空氣<') && !rows.some(r => r.hc.includes('AIR') && r.hc.some(h => h==='AIR' && context.__linesQA.rowReached(r, 'AIR'))))
      failures.push(`${sp}/${nd}: rendered 空氣 but it is unreachable`);
  }
  const hlabel = (h, nd) => context.__linesQA.stOf(nd) === 2 ? ({DRAW: '強聽未中', WDRAW: '弱聽／高張'}[h] || context.NLL.hc[h] || h) : (context.NLL.hc[h] || h);
  // 固定回歸：延遲搶池整節點應省略；BB 面對第二槍不應再列空氣
  context.__linesQA.render('ipc');
  if (context.__linesQA.nodeVisible('ipc', 't_delay')) failures.push('ipc/t_delay should be omitted (no hand checks flop stab)');
  if (context.__linesQA.gridHtml('ipc', 't_delay')) failures.push('ipc/t_delay table still rendered');
  context.__linesQA.render('bb');
  const bbHtml = context.__linesQA.gridHtml('bb', 't_vs_barrel') || '';
  if (/空氣/.test(bbHtml)) failures.push('bb/t_vs_barrel rendered 空氣');
  for (const spot of context.NLL.spots) {
    context.__linesQA.render(spot.id);
    const cells = grids(spot.id), questions = [];
    for (const nd of context.__linesQA.nodesOf(spot.id)) {
      if (!context.__linesQA.nodeVisible(spot.id, nd)) continue;
      cellsOk(spot.id, nd);
      const eligible = context.NLL.rows.filter(r => r.sp === spot.id && r.nd === nd && context.__linesQA.rowReached && r.hc.some(h => context.__linesQA.rowReached(r, h)))
        .some(r => (r.eg || []).some(e => {
          const story = context.__linesQA.story(e);
          return story && story.length === context.__linesQA.stOf(nd) + 2;
        }));
      const tOnly = context.__linesQA.tableOnly && context.__linesQA.tableOnly(spot.id, nd);
      if (tOnly && context.__linesQA.pool(spot.id).some(r => r.nd === nd)) failures.push(`${spot.id}/${nd}: table-only line leaked into drill pool`);
      if (!eligible && !tOnly) failures.push(`${spot.id}/${nd}: no complete drill example`);
    }
    for (let street = 0; street < 3; street++) {
      let count = 0;
      for (let i = 0; i < 30; i++) {
        context.__linesQA.drill(spot.id, street);
        const q = context.__Q;
        if (/undefined|NaN/.test(app.innerHTML)) failures.push(`${spot.id}/${street}: invalid drill text`);
        if (!q) { if (context.__linesQA.pool(spot.id).some(r => context.__linesQA.stOf(r.nd) === street)) failures.push(`${spot.id}/${street}: no drill question`); break; }
        if (!q.row.hc.some(h => context.__linesQA.rowReached(q.row, h))) failures.push(`${spot.id}/${street}/${q.id}: drill on an unreachable row`);
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
