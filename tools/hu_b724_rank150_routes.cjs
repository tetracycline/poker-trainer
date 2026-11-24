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
        assert.equal(m[2].replace(/≈$/, ''), label);
        keys.push(key);
      }
    }
  }
  assert.ok(keys.length, source + ' -> ' + target);
  return keys;
}



const id='ln-iso-lmp_r_model-4ys53a',turn='ln-iso-lmp_t_barrel-1idlo52',flop='ln-iso-lmp_f_stab-yvzhuw';
const node=nodes.get(id);
assert.equal(node.source,turn);
const flopKeys=[];
for(const [key,texture,html] of cells(flop)) {
  for(const jump of html.matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)) {
    if(jump[1]===turn+'-'+texture && jump[2].replace(/≈$/,'')==='下注 ⅓') flopKeys.push(key);
  }
}
assert.deepEqual(flopKeys,['mid_high:3','paired:3']);
const turnKeys=incoming(turn,id,'過');
assert.deepEqual(turnKeys,['mid_high:1','mid_high:2','paired:2','paired:3','paired:4']);
assert.deepEqual(turnKeys,Array.from(node.allowed));
const river={};
for(const [key,,html] of cells(id)) {
  if(!node.allowed.includes(key))continue;
  river[key]=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
  assert.equal(river[key],'過');
}
assert.deepEqual([node.facts.root.spot,node.facts.root.pot,node.facts.root.stack],['ASSUMED_LMP',2.5,99]);
assert.deepEqual([node.facts.pot,node.facts.stack,node.facts.spr],[4.167,98.167,23.558]);
console.log(JSON.stringify({model_id:id,flop_source:flop,turn_source:turn,actor:1,line:'x b33 c/x x/x',
  flop:flopKeys,turn:turnKeys,river,model_price:[4.167,98.167,23.558],native_price:[416,9817]}));
