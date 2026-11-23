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

context.__linesQA.render('opfr');
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

const results={};
for(const [rank,id] of Object.entries({149:'ln-opfr-r_model-142idcm'})){
 const model=nodes.get(id);const parent=nodes.get(model.source);
 assert.deepEqual([model.facts.root.spot, model.facts.root.pot, model.facts.root.stack, model.facts.spr], ['UTG_CO', 6.5, 97.5, 15]);
 assert.equal(parent.id,'ln-opfr-t_model-1ocorr7');
 assert.equal(parent.source,'ln-opfr-f_cbet-1ihx52e');
 const flop=incoming(parent,'過'),turn=incoming(model,'過'),river={};
 for(const [k,t,h] of cells(model.id)){
  const a=h.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
  if(a!=='—')river[k]=a;
 }
 results[rank]={flop,turn,river};
}
console.log(JSON.stringify(results));
