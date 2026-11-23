const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = { innerHTML: '', querySelectorAll: () => [], addEventListener() {} };
const context = {
  console, __LINES_QA: true, location: { hash: '#lines' }, scrollTo() {}, addEventListener() {},
  document: { querySelector: () => app, querySelectorAll: () => [], getElementById: () => null }
};
context.window = context;
vm.createContext(context);
for (const file of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js']) {
  vm.runInContext(fs.readFileSync(file, 'utf8'), context, {filename: file});
}
context.__linesQA.render('bb');
const models = new Map(context.__HU_MODEL_LAST.nodes.map(n => [n.id, n]));
const classes = ['TPG', 'TPW', 'MID', 'DRAW', 'WDRAW'];
const textures = ['low', 'mid_high', 'KQ_high', 'A_high', 'paired', 'mono'];
const output = {};
for (const [rank, id, lead] of [[73,'ln-bb-r_model-150oewe','下注 1']]) {
  const model = models.get(id);
  assert.equal(model.facts.root.spot, 'BTN_BB');
  const stages=['ln-bb-f_vs_cbet-cdkvuf',model.source,model.id];
  assert.equal(model.source,'ln-bb-t_first-tplilt');
  const route = [];
  for (const [stage, source] of stages.entries()) {
    const rows = {};
    const section = app.innerHTML.split('id="' + source + '"')[1].split('<div class="sec"')[0];
    for (const t of textures) {
      const row = section.match(new RegExp('<tr[^>]+id="' + source + '-' + t + '">([\\s\\S]*?)</tr>'));
      assert.ok(row, source);
      rows[t] = {};
      for (const [column, cell] of [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].entries()) {
        if (stage < 2) {
          for (const m of cell[1].matchAll(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/g)) {
            if (m[1] === stages[stage + 1] + '-' + t) {
              const label = m[2].replace(/≈$/, '');
              assert.equal(label,stage===0?'跟':lead);
              rows[t][classes[column]] = label;
            }
          }
        } else if (model.allowed.includes(t + ':' + column)) {
          const label = cell[1].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g, '').replaceAll('≈', '').trim();
          assert.equal(label,'過');
          rows[t][classes[column]] = label;
        }
      }
    }
    route.push(rows);
  }
  output[rank] = {id, spr: model.facts.spr, stages: route};
}
console.log(JSON.stringify(output));
