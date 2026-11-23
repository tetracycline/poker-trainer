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
const flop='ln-iso-lmp_f_lead-aqcv9i';
const classes=['TPG','TPW','MID','DRAW','WDRAW'];
const textures=['low','mid_high','KQ_high','A_high','paired','mono'];
const outcome={};
function cells(id, texture){
  const section=app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];
  const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));
  assert.ok(row);
  return [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
}
function links(id,to,texture,expected){
  const found=[];
  for(const [column,cell] of cells(id,texture).entries()){
    for(const m of cell.matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)){
      if(m[1]!==to+'-'+texture)continue;
      assert.equal(m[2].replace(/≈$/,''),expected);
      found.push(classes[column]);
    }
  }
  return [...new Set(found)];
}
{
  const turn='ln-iso-lmp_t_model-19hfq8v';
  const river='ln-iso-lmp_r_model-1aov4pd';
  const model=nodes.get(river);
  assert.equal(model.source,turn);
  assert.equal(model.pre,'翻前：CO 溜入， 你 BB 過');
  const result={};
  for(const texture of textures){
    const final=[];
    for(const [column,cell] of cells(river,texture).entries()){
      if(!model.allowed.includes(texture+':'+column))continue;
      const label=cell.split('<small')[0].replace(/<[^>]*>/g,'').trim();
      assert.match(label,/^過(?:≈|$)/);
      final.push(classes[column]);
    }
    result[texture]=[links(flop,turn,texture,'下注 ½'),links(turn,river,texture,'下注 ⅓'),final];
  }
  outcome[27]={flop,turn,river,by_texture:result};
}
assert.deepEqual(outcome[27].by_texture.low,[['TPG','TPW','DRAW','WDRAW'],['TPW'],['TPW']]);
console.log(JSON.stringify(outcome));
