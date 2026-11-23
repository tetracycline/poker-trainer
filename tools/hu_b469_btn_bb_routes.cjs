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
context.__linesQA.render('bb');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n => [n.id, n]));
const parent = nodes.get('ln-bb-t_model-1n6d5u3');
assert.equal(parent.action, 'check');
assert.equal(parent.key, '你過、對手過|');
for (const [id, size, spr] of [['ln-bb-r_model-16s8tm3',0.75,6.791],['ln-bb-r_model-rb27ni',0.333,10.436]]) {
  const target = nodes.get(id);
  assert.equal(target.source,parent.id);
  assert.equal(target.action,'bet');
  assert.equal(target.size,size);
  assert.equal(target.facts.spr,spr);
  assert.equal(target.key,'你過、對手過|你下注、對手跟|');
}
console.log('BB 75% and 33% exact parent and river routes verified');
