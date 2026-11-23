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
context.__linesQA.render('opfr');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(node => [node.id, node]));
const gate = JSON.parse(fs.readFileSync('data/nl2_hu_b467_rank97_147_verified_river_nodes.json', 'utf8'));
const parent = nodes.get('ln-opfr-t_model-qx9t0u');
assert.equal(parent.action, 'bet');
assert.equal(parent.size, 1);
assert.equal(parent.key, '你下注、對手跟|');
for (const [id, group] of Object.entries(gate.models)) {
  const model = nodes.get(id);
  assert.equal(model.source, parent.id);
  assert.equal(model.st, 2);
  assert.equal(model.action, group.rank === 97 ? 'bet' : 'check');
  if (model.action === 'bet') assert.equal(model.size, 0.5);
  assert.equal(model.key, group.rank === 97 ? '你下注、對手跟|你下注、對手跟|' : '你下注、對手跟|你過、對手過|');
  for (const board of group.boards) {
    assert.equal(model.facts.spr, board.model_assumed_spr);
    assert.equal(board.actual_exact_action_line, group.rank === 97 ? 'b100 c/b50 c/' : 'b100 c/x x/');
  }
}
console.log('B467 trainer action sizes, position and SPR verified');
