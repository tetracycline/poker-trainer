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



const id='ln-iso-lmp_r_model-p8a79',turn='ln-iso-lmp_t_model-17z0wyl',flop='ln-iso-lmp_f_stab-yvzhuw';
const node=nodes.get(id);
assert.equal(node.source,turn);
assert.equal(nodes.get(turn).source,flop);
assert.deepEqual([node.facts.root.spot,node.facts.pot,node.facts.stack,node.facts.spr], ['ASSUMED_LMP',5,97.75,19.55]);
const flopKeys=incoming(flop,turn,'下注 ½');
const turnKeys=incoming(turn,id,'過');
assert.deepEqual([...turnKeys].sort(),Array.from(node.allowed).sort());
const river={};
for(const [key,,html] of cells(id)){
  if (!node.allowed.includes(key)) continue;
  const label=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
  assert.equal(label,'過');
  river[key]=label;
}
console.log(JSON.stringify({model_id:id,flop_source:flop,turn_source:turn,flop:flopKeys,turn:turnKeys,river,actor:1,line:'x b50 c/x x/x',model_spr:19.55}));
