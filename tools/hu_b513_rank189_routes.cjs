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

context.__linesQA.render('3bp');
context.__linesQA.render('ipc');
const rows = context.__HU_MODEL_LAST.nodes;
const a = rows.find(r => r.id==='ln-ipc-r_model-1ua8hb7');
const b = rows.find(r => r.id==='ln-ipc-r_model-i19djk');
const parent = rows.find(r => r.id===b.source);
assert.deepEqual([a.facts.root.spot,a.facts.root.pot,a.facts.root.stack,a.action,a.size,a.facts.pot],['SB_BB',6,97,'bet',1,30]);
assert.deepEqual(Array.from(a.allowed), ['A_high:3','A_high:4','mono:3','mono:4']);
assert.equal(a.source,'ln-ipc-t_barrel-igavs2');
const turnPot = a.facts.pot/(1+2*a.size);
assert.ok(Math.abs((turnPot/a.facts.root.pot-1)/2-1/3)<1e-6);
assert.deepEqual([parent.size,parent.facts.pot,b.size,b.facts.pot],[1,18,.333,30]);
console.log('Verified rank189 33%/100% and rank191 100%/33% are distinct native routes.');
