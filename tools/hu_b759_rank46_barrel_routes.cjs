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
        if (m[2].replace(/≈$/, '') !== label) continue;
        keys.push(key);
      }
    }
  }
  assert.ok(keys.length, source + ' -> ' + target);
  return keys;
}



const spec={
  '199':['ln-iso-lmp_r_model-10l8t7i','下注 ⅓'],
  '200':['ln-iso-lmp_r_model-68efr6','下注 ½'],
  '201':['ln-iso-lmp_r_model-qsgdjf','下注 ¾']
};
const turn='ln-iso-lmp_t_model-17z0wyl', flop='ln-iso-lmp_f_stab-yvzhuw';
const result={};
for(const [rank,[id,label]] of Object.entries(spec)){
 const node=nodes.get(id); assert.equal(node.source,turn);
 const turnKeys=incoming(turn,id,label);
 assert.deepEqual([...turnKeys].sort(),Array.from(node.allowed).sort());
 const river={};
 for(const [key,,html] of cells(id)){
  if(!node.allowed.includes(key))continue;
  river[key]=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
 }
 result[rank]={model_id:id,flop:incoming(flop,turn,'下注 ½'),turn:turnKeys,river,model_spr:node.facts.spr};
}
console.log(JSON.stringify(result));