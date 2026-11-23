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
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const model = nodes.get('ln-ipc-r_model-6ntgm7'), parent = nodes.get(model.source);
assert.equal(parent.id,'ln-ipc-t_model-1cla93g');
assert.equal(parent.source,'ln-ipc-f_vs_cbet-m5gxt4');
assert.equal(model.pre,'翻前：UTG 開， 你 CO 跟');
assert.equal(model.key,'對手下注、你跟|對手過、你過|對手過');
assert.deepEqual([model.facts.root.spot,model.facts.root.pot,model.facts.root.stack,parent.facts.pot,model.facts.pot,model.facts.spr],['UTG_CO',6.5,97.5,13,13,7]);
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
const flop=incoming(parent,'跟'),turn=incoming(model,'過'),river={};
for(const [key,,html] of cells(model.id)){
  const main=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
  if(main!=='—'){assert.equal(main,'過');river[key]='x';}
}
assert.deepEqual(Object.keys(river).sort(),Array.from(model.allowed).sort());
console.log(JSON.stringify({flop,turn,river}));
