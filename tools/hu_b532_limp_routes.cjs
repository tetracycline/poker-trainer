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
const targets = {27:'ln-iso-lmp_r_model-1aov4pd',29:'ln-iso-lmp_r_model-gifggm'};
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
  const target=nodes.get(id), parent=nodes.get(target.source);
  assert.equal(target.pre,'翻前：CO 溜入， 你 BB 過');
  const bet='下注 ½', next=rank==='27'?'下注 ⅓':'下注 ¾';
  output[rank]={};
  for(const texture of new Set(target.allowed.map(k=>k.split(':')[0]))){
    output[rank][texture]=[linkedHands(parent.source,parent.id,texture,bet),linkedHands(parent.id,id,texture,next),
      target.allowed.filter(k=>k.startsWith(texture+':')).map(k=>handClasses[Number(k.split(':')[1])])];
  }
}
console.log(JSON.stringify(output));
