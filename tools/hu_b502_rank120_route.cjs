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
const model=context.__HU_MODEL_LAST.nodes.find(n=>n.id==='ln-3bp-3b_t_model-n5cvfv');
assert.deepEqual([model.pre,model.source,model.action,model.key],
  ['翻前：BTN 開， 你 BB 3-bet ，BTN 跟','ln-3bp-3b_f_cbet-ke0pam','check','你過、對手過|']);
assert.deepEqual([model.facts.root.spot,model.facts.pot,model.facts.stack,model.facts.spr],
  ['BB3_BTN',20.5,90,4.39]);
const report=JSON.parse(fs.readFileSync('data/nl2_hu_b502_rank120_attempts.json'));
assert.equal(report.model_id,model.id);
const seen=new Set();
for(const row of report.attempts){
  assert.equal(row.gto.line,'x x/');assert.equal(row.gto.acting_seat,0);
  assert.equal(row.gto.spot,'BB3_BTN');assert.ok(row.gto.strict_legal_combos>0);
  if(row.status==='BOTH_POSITIVE'){
    assert.ok(row.exp_oop.strict_legal_combos>0 && row.exp_oop.compatible_hole_card_pairs>=row.exp_oop.strict_legal_combos);
    assert.ok(row.exp_oop.source_actions.includes('b50'));seen.add(row.flop);
  }
}
const result='data/solver_evidence/reverified/rank120.json';
assert.equal(fs.existsSync(result),seen.size>=3);
if(seen.size>=3){
  const group=JSON.parse(fs.readFileSync(result));
  assert.equal(group.boards.length,seen.size);
  for(const b of group.boards){
    assert.ok(seen.has(b.flop));assert.deepEqual([b.actual_pot_bb,b.actual_effective_stack_bb],[20.5,90]);
  }
}
console.log('Verified rank120 BB checked turn and '+seen.size+' positive paired flops.');
