// Read amounts from the same generated nodes the training interface uses.
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
const context = {
  console, __LINES_QA: true, location: {hash: '#lines'}, scrollTo() {}, addEventListener() {},
  document: {querySelector: () => app, querySelectorAll: () => [], getElementById: () => null},
};
context.window = context;
vm.createContext(context);
for (const file of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js']) {
  vm.runInContext(fs.readFileSync(file, 'utf8'), context, {filename: file});
}
context.__linesQA.render('ipfr');
const models = new Map(context.__HU_MODEL_LAST.nodes.map(node => [node.id, node]));
const expected = [
  ['ln-ipfr-r_model-h0c7q7', 0.5, 0.5],
  ['ln-ipfr-r_model-7kv23r', 0.333, 0.75],
];
for (const [id, flopSize, turnSize] of expected) {
  const river = models.get(id);
  const turn = models.get(river.source);
  assert.equal(turn.source, 'ln-ipfr-f_cbet-3kh71s');
  assert.deepEqual([turn.action, turn.size, river.action, river.size], ['bet', flopSize, 'bet', turnSize]);
  assert.equal(river.key, '對手過、你下注、對手跟|對手過、你下注、對手跟|對手過');
}

assert.deepEqual(Array.from(models.get('ln-ipfr-r_model-h0c7q7').allowed), ['mono:3']);
