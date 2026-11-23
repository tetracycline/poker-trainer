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
const turn = 'ln-iso-lmp_t_barrel-mtwej3';
const river = 'ln-iso-lmp_r_model-pjewx6';
const model = nodes.get(river);
assert.equal(model.source, turn);
assert.equal(model.pre, '翻前：CO 溜入， 你 BB 過');
assert.equal(model.flopBetPct, 50);
assert.deepEqual([model.facts.pot,model.facts.stack,model.facts.spr],[5,97.75,19.55]);
const result = {};
for (const texture of textures) {
  const final = cells(river,texture).flatMap((cell,i)=>{
    if (!model.allowed.includes(texture+':'+i)) return [];
    const label=cell.split('<small')[0].replace(/<[^>]*>/g,'').trim();
    assert.match(label,/^過(?:≈|$)/);
    return [classes[i]];
  });
  result[texture] = {flop:links(flop,turn,texture,'下注 ½'),turn:links(turn,river,texture,'過'),river:final};
}
console.log(JSON.stringify(result));
