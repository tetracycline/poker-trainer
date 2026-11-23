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

context.__linesQA.render('iso');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const model=nodes.get('ln-iso-lmp_r_model-gifggm');
const textures=['low','mid_high','KQ_high','A_high','paired','mono'];
function cells(id) {
  const section=app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];
  return textures.flatMap(texture=>{
    const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));
    assert.ok(row,id);
    return [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map((cell,i)=>[texture+':'+i,texture,cell[1]]);
  });
}
function incoming(target,label) {
  const keys=[];
  for (const [key,texture,html] of cells(target.source)){
    for(const m of html.matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)) {
      if(m[1]===target.id+'-'+texture){assert.equal(m[2].replace(/≈$/,''),label);keys.push(key);}
    }
  }
  assert.deepEqual([...new Set(keys)].sort(),Array.from(target.allowed).sort());
  return keys;
}
const parent=nodes.get(model.source);
const flop=incoming(parent,'下注 ½'),turn=incoming(model,'下注 ¾'),river={};
for(const [key,,html] of cells(model.id)){
  const primary=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
  if(primary!=='—')river[key]=primary;
}
assert.deepEqual(Object.keys(river).sort(),Array.from(model.allowed).sort());
assert.deepEqual(turn,['mono:0']);
assert.ok(['mono:0','mono:1','mono:3','mono:4'].every(k=>flop.includes(k)));
assert.equal(model.pre,'翻前：CO 溜入， 你 BB 過');
assert.equal(model.facts.root.spot,'ASSUMED_LMP');
assert.equal(model.facts.spr,7.52);
console.log(JSON.stringify({flop,turn,river}));
