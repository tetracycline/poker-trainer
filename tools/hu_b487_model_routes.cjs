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
const nodes=new Map(context.__HU_MODEL_LAST.nodes.map(m=>[m.id,m]));
const turn=nodes.get('ln-bb-t_model-cge9jz'),river=nodes.get('ln-bb-r_model-123cy01');
const parent='ln-bb-f_vs_cbet-m7k2cp',pre='翻前：CO 開， 你 BB 跟';
assert.deepEqual([turn.pre,turn.source,turn.action,turn.key], [pre,parent,'call','你過、對手下注、你跟|']);
assert.deepEqual([river.pre,river.source,river.action,river.key],[pre,turn.id,'check','你過、對手下注、你跟|你過、對手過|']);
const data=JSON.parse(fs.readFileSync('data/nl2_hu_b487_cobb_reach.json'));
for(const row of Object.values(data.models)){
  const m=nodes.get(row.model_id);
  assert.equal(m.facts.spr,8.364);
  for(const b of row.boards){
    assert.deepEqual([b.acting_seat,b.actual_pot_bb,b.actual_effective_stack_bb,b.actual_exact_action_line],[0,11,94.75,row.line]);
    assert.ok(Math.abs(b.actual_spr/m.facts.spr-1)<=.05);
  }
}
console.log('B487 exact BB role, native parent and checked turn verified');
