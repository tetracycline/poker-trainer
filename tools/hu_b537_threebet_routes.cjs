const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
const context = {
  console, __LINES_QA: true, location: {hash: '#lines'}, scrollTo() {}, addEventListener() {},
  document: {querySelector: () => app, querySelectorAll: () => [], getElementById: () => null}
};
context.window = context;
vm.createContext(context);
for (const file of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js']) {
  vm.runInContext(fs.readFileSync(file,'utf8'), context, {filename: file});
}
context.__linesQA.render('3bp');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const handClasses = ['TPG','TPW','MID','DRAW','WDRAW'];
function linkedHands(from, to, texture, label) {
  const section = app.innerHTML.split('id="'+from+'"')[1].split('<div class="sec"')[0];
  const row = section.match(new RegExp('<tr[^>]+id="'+from+'-'+texture+'">([\\s\\S]*?)</tr>'))[1];
  const result = [];
  for(const [i,cell] of [...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].entries()){
    for(const match of cell[1].matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)){
      if(match[1]===to+'-'+texture){
        assert.equal(match[2].replace(/≈$/,''),label); result.push(handClasses[i]);
      }
    }
  }
  assert.ok(result.length);
  return [...new Set(result)];
}
const turn='ln-3bp-3c_t_model-1oebhk7';
const parent='ln-3bp-3c_f_first-1w56d75';
const ids={131:turn,244:'ln-3bp-3c_r_model-knstxa',261:'ln-3bp-3c_r_model-7xkisp'};
const out={};
for(const [rank,id] of Object.entries(ids)){
  const model=nodes.get(id);
  assert.equal(model.pre,'翻前： 你 CO 開 ，BTN 3-bet， 你 CO 跟');
  assert.equal(model.source,rank==='131'?parent:turn);
  const visible=model.allowed.filter(k=>k.startsWith('low:')).map(k=>handClasses[Number(k.split(':')[1])]);
  const flop=linkedHands(parent,turn,'low','過');
  out[rank]=rank==='131'?[flop,visible]:[flop,linkedHands(turn,id,'low',rank==='244'?'下注 ½':'過'),visible];
}
console.log(JSON.stringify(out));
