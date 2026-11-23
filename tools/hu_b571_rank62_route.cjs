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

context.__linesQA.render('ipfr');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const model=nodes.get('ln-ipfr-t_model-snfiz2');
assert.equal(model.source,'ln-ipfr-f_cbet-3kh71s');
assert.equal(model.key,'對手過、你下注、對手跟|對手過');
assert.deepEqual([model.facts.root.spot,model.facts.root.pot,model.facts.root.stack,model.facts.pot,model.facts.spr],['CO_BB',5.5,97.5,13.75,6.791]);
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
const flop=incoming(model,'下注 ¾'),turn={};
const tokens={'過':'x','下注 ⅓':'b33','下注 ½':'b50','下注 ¾':'b75','下注 1':'b100','全下':'a'};
for(const [key,,html] of cells(model.id)){
  const primary=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
  if(primary!=='—'){assert.ok(tokens[primary], primary);turn[key]=primary;}
}
assert.deepEqual(Object.keys(turn).sort(),Array.from(model.allowed).sort());
console.log(JSON.stringify({flop,turn}));
