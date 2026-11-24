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

context.__linesQA.render('3bp');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const textures=['low','mid_high','KQ_high','A_high','paired','mono'];
function cells(id) {
  const section=app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];
  return textures.flatMap(texture=>{
    const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));
    assert.ok(row,id);
    return [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map((cell,i)=>[texture+':'+i,texture,cell[1]]);
  });
}
function incoming(source, target, label) {
  const keys = [];
  for (const [key, texture, html] of cells(source)) {
    for (const m of html.matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)) {
      if (m[1] === target + '-' + texture) {
        assert.equal(m[2].replace(/≈$/, ''), label);
        keys.push(key);
      }
    }
  }
  assert.ok(keys.length, source + ' -> ' + target);
  return keys;
}
const id='ln-3bp-3c_r_model-13bw264',parent='ln-3bp-3c_t_model-owdwy',root='ln-3bp-3c_f_vs_cbet-1pj8rrc',model=nodes.get(id);
assert.ok(model && model.source===parent && nodes.get(parent).source===root);
assert.deepEqual([model.facts.root.spot,model.facts.pot,model.facts.stack,model.facts.spr],['BB3_BTN',34.04,83.23,2.445]);
const flop=incoming(root,parent,'跟'),turn=incoming(parent,id,'過'),river={};
assert.deepEqual([...new Set(turn)].sort(),Array.from(model.allowed).sort());
for(const [key,texture,html] of cells(id)){
 if(!model.allowed.includes(key))continue;
 river[key]=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
}
assert.deepEqual(Array.from([model.facts.root.pot,model.facts.root.stack]),[20.5,90]);
assert.deepEqual(Object.values(river),Object.values(river).map(()=> '過'));
console.log(JSON.stringify({id,parent,root,flop,turn,river,root_fact:model.facts.root,actual:[34.04,83.23,2.445]}));
