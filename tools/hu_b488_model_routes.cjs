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

const proofs = [
  [85,'bb','ln-bb-r_model-1e6bpc','ln-bb-t_model-1c7tu96','翻前：BTN 開， 你 BB 跟','你過、對手下注、你跟|你過、對手過|','call',null,'x b50 c/x x/',0],
  [112,'ipfr','ln-ipfr-r_model-9eqgjz','ln-ipfr-t_model-xbvh6','翻前： 你 BTN 開 ，BB 跟','對手過、你過|對手過、你過|對手過','check',null,'x x/x x/x',1],
  [177,'3bp','ln-3bp-3b_r_model-1mh38ma','ln-3bp-3b_t_model-1fvksvd','翻前：BTN 開， 你 BB 3-bet ，BTN 跟','你下注、對手跟|你過、對手過|','bet',0.75,'b75 c/x x/',0],
  [256,'3bp','ln-3bp-3c_r_model-cfardb','ln-3bp-3c_t_stab-nk3x7w','翻前： 你 BTN 開 ，BB 3-bet， 你 BTN 跟','對手下注、你跟|對手過、你過|對手過',null,null,'b33 c/x x/x',1],
];
for (const [rank,spot,id,parent,pre,key,act,size,line,seat] of proofs) {
  context.__linesQA.render(spot);
  const nodes=new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
  const model=nodes.get(id), ancestor=nodes.get(parent);
  assert.deepEqual([model.source,model.pre,model.key,model.action],[parent,pre,key,'check']);
  if (act) {
    assert.equal(ancestor.action,act);
    if(size !== null) assert.equal(ancestor.size,size);
  } else {
    // The pre-authored BTN turn table is reached through the same BB 3-bet/BTN-call public history.
    const section=app.innerHTML.split('id="'+parent+'"')[1].split('<div class="sec"')[0].replace(/<[^>]+>/g,' ');
    assert.ok(section.includes('BB 下注 33%'));
    assert.ok(section.includes('你（BTN） 跟'));
  }
  const group=JSON.parse(fs.readFileSync('data/solver_evidence/reverified/rank'+rank+'.json','utf8'));
  assert.deepEqual([group.rank,group.model_id,group.boards.length],[rank,id,3]);
  for(const board of group.boards) {
    assert.deepEqual([board.acting_seat,board.actual_exact_action_line,board.model_assumed_spr],[seat,line,model.facts.spr]);
    assert.ok(Math.abs(board.actual_spr/model.facts.spr-1)<=.05);
  }
}
console.log('B488 all four model routes, native parent roles and 12 public source decisions verified');
