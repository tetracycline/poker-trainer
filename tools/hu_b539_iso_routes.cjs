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
context.__linesQA.render('iso');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const targets = {124:'ln-iso-t_model-1gjwm8f',125:'ln-iso-t_model-szsdgn'};
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
const output={};
for(const [rank,id] of Object.entries(targets)){
  const target=nodes.get(id);
  assert.equal(target.pre,'翻前：CO 溜入， 你 BTN 加注隔離 ，CO 跟');
  assert.equal(target.source,'ln-iso-f_cbet-hd3ik2');
  assert.deepEqual([target.facts.root.pot,target.facts.root.stack],[9.5,96]);
  const bet=rank==='124'?'下注 ½':'下注 ⅓';
  output[rank]={};
  for(const t of new Set(target.allowed.map(k=>k.split(':')[0]))){
    const visible=target.allowed.filter(k=>k.startsWith(t+':')).map(k=>handClasses[Number(k.split(':')[1])]);
    output[rank][t]=[linkedHands(target.source,id,t,bet),visible];
  }
}
console.log(JSON.stringify(output));
