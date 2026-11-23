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

context.__linesQA.render('ipc');
const model=context.__HU_MODEL_LAST.nodes.find(n=>n.id==='ln-ipc-t_model-1cla93g');
assert.deepEqual([model.pre,model.source,model.action,model.key],[
  '翻前：UTG 開， 你 CO 跟','ln-ipc-f_vs_cbet-m5gxt4','call','對手下注、你跟|對手過'
]);
if(process.argv.includes('--check-low-call')) {
  for(const t of ['low','KQ_high']) for(const column of [0,1,2]) {
    assert.ok(model.allowed.includes(t+':'+column), 'Missing the actual one-pair flop calling cell');
  }
}
const {root,pot,spr}=model.facts;
assert.deepEqual([root.spot,root.pot,root.stack,pot,spr],['UTG_CO',6.5,97.5,13,7]);
const actualBet=(pot-root.pot)/2;
assert.equal(actualBet/root.pot,.5);
const result=JSON.parse(fs.readFileSync('data/nl2_hu_b489_rank79_attempts.json'));
const group=result.model;
assert.deepEqual([group.rank,group.model_id,group.spot,group.actor,group.line],[79,model.id,'UTG_CO','CO_IP','b50 c/x']);
for(const board of group.boards){
  assert.deepEqual([board.acting_seat,board.actual_exact_action_line,board.actual_pot_bb,board.actual_effective_stack_bb],
                   [1,group.line,pot,root.stack-actualBet]);
  assert.ok(Math.abs(board.actual_spr/spr-1)<=.05);
}
console.log('Verified exact CO-IP call versus 50%, native checked turn and named-board solver stacks.');
