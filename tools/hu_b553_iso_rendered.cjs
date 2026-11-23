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
    const section=app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];
    const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+t+'">([\\s\\S]*?)</tr>'))[1];
    const actions={};
    for(const [i,cell] of [...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].entries()){
      if(!visible.includes(handClasses[i])) continue;
      const a=cell[1].match(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/);
      assert.ok(a);
      const label=a[2].replace(/≈$/,'');
      actions[handClasses[i]]={'過':'x','下注 ⅓':'b33','下注 ½':'b50','下注 ¾':'b75','下注 1':'b100'}[label];
      assert.ok(actions[handClasses[i]],label);
    }
    output[rank][t]={flop:linkedHands(target.source,id,t,bet),actions};
  }
}
console.log(JSON.stringify(output));
