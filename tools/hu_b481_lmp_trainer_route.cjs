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
context.__linesQA.render('iso');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(node => [node.id, node]));

const parent = nodes.get('ln-iso-lmp_t_model-19hfq8v');
const river = nodes.get('ln-iso-lmp_r_model-1aov4pd');
const pre = '翻前：CO 溜入， 你 BB 過';
assert.deepEqual([parent.pre,parent.action,parent.size,parent.key,parent.facts.pot,parent.facts.stack,parent.facts.spr],
  [pre,'bet',.50,'你下注、對手跟|',5,97.75,19.55]);
assert.deepEqual([river.pre,river.source,river.action,river.size,river.st,river.key,river.facts.pot,river.facts.stack,river.facts.spr],
  [pre,parent.id,'bet',.333,2,'你下注、對手跟|你下注、對手跟|',8.333,96.083,11.53]);
assert.deepEqual([river.facts.root.family,river.facts.root.spot,river.facts.root.pot,river.facts.root.stack],
  ['LMP','ASSUMED_LMP',2.5,99]);
process.stdout.write(JSON.stringify({source_model_id:parent.id, enabled_texture_handclass_cells:Array.from(river.allowed),
  generic_trainer_cells_certified:[], claim:'NAMED_ACTION_LINE_EXAMPLES_ONLY'}));
