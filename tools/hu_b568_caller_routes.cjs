const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
const context = {
  console, __LINES_QA: true, location: {hash: '#lines'}, scrollTo() {}, addEventListener() {},
  document: {querySelector: () => app, querySelectorAll: () => [], getElementById: () => null}
};
context.window = context;
vm.createContext(context);
for (const file of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js']) {
  vm.runInContext(fs.readFileSync(file,'utf8'), context, {filename: file});
}
context.__linesQA.render('ipc');
const river = 'ln-ipc-r_model-1a3ai9a';
const turn = 'ln-ipc-t_vs_barrel-yf121k';
const flop = 'ln-ipc-f_vs_cbet-1axpfmj';
const model = context.__HU_MODEL_LAST.nodes.find(row => row.id === river);
assert.equal(model.source, turn);
assert.equal(model.key, '對手下注、你跟|對手下注、你跟|對手過');

const route = {flop: {}, turn: {}, river: {}};
for (const [street, sectionId] of Object.entries({flop, turn, river})) {
  const section = app.innerHTML.split('id="' + sectionId + '"')[1].split('<div class="sec"')[0];
  const rows = section.matchAll(/<tr data-cl="[^"]*" id="([^"]+)">([\s\S]*?)<\/tr>/g);
  for (const [, rowId, row] of rows) {
    const texture = rowId.slice(sectionId.length + 1);
    const cells = [...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)];
    for (const [column, cell] of cells.entries()) {
      const html = cell[1];
      const key = texture + ':' + column;
      if (street === 'river') {
        const label = html.split('<')[0].trim().replace(/≈$/, '');
        if (label !== '—') {
          assert.ok(['過', '下注 ½', '下注 ¾'].includes(label), label);
          route.river[key] = label;
        }
        continue;
      }
      const links = [...html.matchAll(/<a class="jmp( sub)?" href="#([^"]+)">([^<]*)<\/a>/g)];
      // The alternate flop link follows the opponent's barrel. The primary turn
      // link follows a BB call and the opponent's check on the river.
      const hasLink = street === 'flop'
        ? links.some(([, sub, to]) => sub && to === turn + '-' + texture)
        : links.some(([, sub, to]) => !sub && to === river + '-' + texture);
      if (hasLink) {
        assert.equal(links[0][3].replace(/≈$/, ''), '跟');
        route[street][key] = 'c';
      }
    }
  }
}
assert.deepEqual(Object.keys(route.turn).sort(), [...model.allowed].sort());
assert.deepEqual(Object.keys(route.river).sort(), [...model.allowed].sort());
route.model = {pot_bb: model.facts.pot, effective_stack_bb: model.facts.stack, spr: model.facts.spr};
assert.deepEqual(route.model, {pot_bb: 22.5, effective_stack_bb: 82.5, spr: 3.667});
console.log(JSON.stringify(route));
