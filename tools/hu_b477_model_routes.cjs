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
  vm.runInContext(fs.readFileSync(file, 'utf8'), context, { filename: file });
}

const proof = JSON.parse(fs.readFileSync('data/nl2_hu_b477_raw_river_pairs.json', 'utf8')).models;
const parents = {
  116: ['iso', 'ln-iso-lmp_t_stab-12vmlhl', 'bet', 0.5, 'b33 c/x b50 c/x'],
  200: ['iso', 'ln-iso-lmp_t_model-17z0wyl', 'bet', 0.5, 'x b50 c/x b50 c/x'],
  213: ['ipc', 'ln-ipc-t_model-1cla93g', 'check', null, 'b50 c/x x/x'],
  232: ['3bp', 'ln-3bp-3b_t_first-rkfnto', 'check', null, 'x b33 c/x x/'],
  237: ['ipc', 'ln-ipc-t_model-1cla93g', 'bet', 0.5, 'b50 c/x b50 c/x'],
};
for (const [rank, [spot, parentId, action, size, line]] of Object.entries(parents)) {
  context.__linesQA.render(spot);
  const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(row => [row.id, row]));
  const result = proof[rank], model = nodes.get(result.model_id);
  assert.deepEqual([model.source, model.action, result.exact_line], [parentId, action, line]);
  if (size !== null) assert.equal(model.size, size);
  if (rank === '200') {
    const parent = nodes.get(parentId);
    assert.deepEqual([parent.source, parent.action, parent.size], ['ln-iso-lmp_f_stab-yvzhuw', 'bet', 0.5]);
  }
  if (rank === '116' || rank === '232') {
    const text = app.innerHTML.split('id="'+parentId+'"')[1].split('<div class="sec"')[0].replace(/<[^>]+>/g, ' ');
    assert.ok(text.includes('下注 33%'));
    assert.ok(text.includes(rank === '116' ? '底池 2.5bb' : '底池 21bb'));
  }
}
console.log('B477 trainer source roles and generated action sizes verified');
